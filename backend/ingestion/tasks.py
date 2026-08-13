"""Celery tasks for document ingestion pipeline."""
from celery import Celery
from ingestion.loader import load_pdf, load_txt
from ingestion.chunker import chunk_pages
from ingestion.embedder import embed_documents
from generation.summarizer import generate_document_summary
from retrieval.faiss_store import upsert_chunks
from db.database import get_sync_session
from db.models import Document, Chunk, DocStatus
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

celery_app = Celery('rag', broker=os.getenv('CELERY_BROKER_URL'))
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND')


@celery_app.task(bind=True)
def ingest_document(self, doc_id: int, file_path: str, file_type: str):
    with get_sync_session() as session:
        doc = session.get(Document, doc_id)
        doc.status = DocStatus.INGESTING
        session.commit()

        try:
            # 1. Parse document
            pages = load_pdf(file_path) if file_type == 'pdf' else load_txt(file_path)
            logger.info(f'[ingest] doc_id={doc_id} parsed {len(pages)} pages')

            # 2. Generate comprehensive document summary via Gemini
            try:
                summary = generate_document_summary(pages, filename=doc.filename or '')
                doc.summary = summary
                session.commit()
                logger.info(f'[ingest] doc_id={doc_id} summary generated ({len(summary)} chars)')
            except Exception as e:
                logger.warning(f'[ingest] doc_id={doc_id} summary generation failed: {e}')
                # Non-fatal: continue ingestion without summary

            # 3. Chunk
            chunks = chunk_pages(pages)
            logger.info(f'[ingest] doc_id={doc_id} produced {len(chunks)} chunks')

            # 4. Embed
            texts = [c['text'] for c in chunks]
            vectors = embed_documents(texts)

            # 5. Build metadata and DB records
            metadatas = []
            db_chunks = []
            for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
                metadatas.append({
                    'doc_id': doc_id,
                    'text': chunk['text'],
                    'page': chunk['page'],
                    'chunk_index': chunk['chunk_index']
                })
                db_chunks.append(Chunk(
                    document_id=doc_id,
                    faiss_idx=0,  # updated below after we know the base index
                    chunk_index=chunk['chunk_index'],
                    page_number=chunk['page'],
                    text=chunk['text']
                ))

            # 6. Upsert to FAISS + JSON sidecar
            upsert_chunks(vectors, metadatas)

            # 7. Save to Postgres
            session.add_all(db_chunks)
            doc.total_chunks = len(db_chunks)
            doc.status = DocStatus.DONE
            session.commit()

            logger.info(f'[ingest] doc_id={doc_id} completed successfully')

        except Exception as e:
            doc.status = DocStatus.FAILED
            session.commit()
            logger.error(f'[ingest] doc_id={doc_id} failed: {e}')

            # Clean up the uploaded file on failure to prevent orphans
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f'[ingest] Cleaned up orphaned file: {file_path}')
                except OSError as cleanup_err:
                    logger.warning(f'[ingest] Failed to clean up file: {cleanup_err}')

            raise self.retry(exc=e, countdown=30, max_retries=2)
