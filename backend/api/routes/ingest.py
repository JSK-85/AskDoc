"""Document ingestion, listing, rename, pin, delete endpoints."""
import asyncio
import os
import re
import uuid

import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import verify_api_key
from db.database import get_db
from db.models import Document, DocStatus
from ingestion.tasks import ingest_document
from retrieval.faiss_store import delete_document_chunks

router = APIRouter()

# Persistent upload directory (survives ingestion so we can serve PDFs later)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {'application/pdf': 'pdf', 'text/plain': 'txt'}
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_SIZE_MB', 50)) * 1024 * 1024


def _sanitize_filename(name: str) -> str:
    """Strip unsafe characters from user-supplied filename for display."""
    # Remove anything that isn't alphanumeric, space, dash, underscore, or dot
    safe = re.sub(r'[^\w\s\-.]', '', name)
    return safe.strip() or 'unnamed'


@router.post('/ingest', status_code=202)
async def ingest(file: UploadFile = File(...),
                 db: AsyncSession = Depends(get_db),
                 _=Depends(verify_api_key)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, 'Only PDF and TXT files are supported')

    # Read file with size limit
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            413,
            f'File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.',
        )

    file_type = ALLOWED_TYPES[file.content_type]
    safe_name = f'{uuid.uuid4()}.{file_type}'
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    display_name = _sanitize_filename(file.filename or 'unnamed')
    doc = Document(filename=display_name, status=DocStatus.PENDING, file_path=file_path)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    ingest_document.delay(doc.id, file_path, file_type)

    return {
        'doc_id': doc.id,
        'status': 'pending',
        'message': 'Ingestion started. Poll /api/v1/status/{doc_id} for progress.'
    }


@router.get('/status/{doc_id}')
async def get_status(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, 'Document not found')
    return {
        'doc_id': doc.id,
        'filename': doc.filename,
        'status': doc.status,
        'total_chunks': doc.total_chunks
    }


@router.get('/documents')
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document)
        .order_by(
            case((Document.pinned == True, 0), else_=1),  # noqa: E712
            Document.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )
    docs = result.scalars().all()
    return [{
        'doc_id': d.id,
        'filename': d.filename,
        'status': d.status,
        'total_chunks': d.total_chunks,
        'pinned': d.pinned,
    } for d in docs]


# --- File serving ---

@router.get('/documents/{doc_id}/file')
async def get_document_file(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the original uploaded file for in-browser PDF viewing."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, 'Document not found')
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(404, 'Original file not available')

    # Determine media type
    ext = os.path.splitext(doc.file_path)[1].lower()
    media_type = 'application/pdf' if ext == '.pdf' else 'text/plain'

    return FileResponse(
        path=doc.file_path,
        media_type=media_type,
        filename=doc.filename,
        headers={'Content-Disposition': 'inline'},
    )


# --- Rename ---

class RenameBody(BaseModel):
    filename: str


@router.patch('/documents/{doc_id}')
async def rename_document(
    doc_id: int,
    body: RenameBody,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, 'Document not found')

    new_name = _sanitize_filename(body.filename)
    if not new_name:
        raise HTTPException(400, 'Filename cannot be empty')

    doc.filename = new_name
    await db.commit()
    return {'doc_id': doc.id, 'filename': doc.filename}


# --- Pin / Unpin ---

@router.patch('/documents/{doc_id}/pin')
async def toggle_pin_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, 'Document not found')

    doc.pinned = not doc.pinned
    await db.commit()
    return {'doc_id': doc.id, 'pinned': doc.pinned}


# --- Delete ---

@router.delete('/documents/{doc_id}')
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, 'Document not found')

    # Delete FAISS chunks in a thread to keep FastAPI completely non-blocking
    deleted_faiss_count = await asyncio.to_thread(delete_document_chunks, doc_id)

    # Delete the stored file from disk
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass  # best-effort cleanup

    # Delete from DB (SQLAlchemy cascades delete to chunks table)
    await db.delete(doc)
    await db.commit()

    return {
        'doc_id': doc_id,
        'status': 'deleted',
        'message': f'Document and {deleted_faiss_count} chunks successfully deleted.'
    }
