"""Query endpoints: synchronous, streaming, history, and feedback."""
import asyncio
import json
import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import verify_api_key, RateLimit
from db.database import get_db, AsyncSessionLocal
from db.models import QueryLog, Document
from generation.llm_client import generate_answer_async, generate_answer_stream_async
from generation.prompt_builder import build_prompt
from ingestion.embedder import embed_query
from retrieval.faiss_store import search
from retrieval.query_rewriter import rewrite_query

logger = logging.getLogger(__name__)

router = APIRouter()

TOP_K = int(os.getenv('TOP_K', 6))


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    doc_id: int | None = None


class Source(BaseModel):
    page: int
    excerpt: str
    doc_id: int


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    latency_ms: int


@router.post('/query', response_model=QueryResponse)
async def query(
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key),
    __=Depends(RateLimit(limit=5, window=60))
):
    t0 = time.time()

    # 1. Rewrite question for better retrieval (expands with synonyms)
    search_query = await asyncio.to_thread(rewrite_query, req.question)

    # 2. Embed the expanded search query
    q_vec = await asyncio.to_thread(embed_query, search_query)

    # 3. Retrieve top-k chunks from FAISS (offloaded to thread)
    chunks = await asyncio.to_thread(search, q_vec, top_k=TOP_K, doc_id_filter=req.doc_id)

    # 4. Fetch document summary for global context
    doc_summary = None
    target_doc_id = req.doc_id
    if not target_doc_id and chunks:
        # Infer doc_id from retrieved chunks when querying all documents
        target_doc_id = chunks[0].get('doc_id')
    if target_doc_id:
        doc = await db.get(Document, target_doc_id)
        if doc:
            doc_summary = doc.summary

    # 5. Build grounded prompt with summary + chunks
    prompt = build_prompt(req.question, chunks, summary=doc_summary)

    # 6. Generate answer via Gemini (async call)
    answer = await generate_answer_async(prompt)

    # 7. Format sources
    sources = [
        Source(page=c['page'], excerpt=c['text'][:200], doc_id=c['doc_id'])
        for c in chunks
    ]

    latency = int((time.time() - t0) * 1000)

    # 8. Save query log to DB
    log = QueryLog(
        question=req.question,
        answer=answer,
        latency_ms=latency
    )
    db.add(log)
    await db.commit()

    return QueryResponse(
        answer=answer,
        sources=sources,
        latency_ms=latency
    )


@router.post('/query/stream')
async def query_stream(
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key),
    __=Depends(RateLimit(limit=5, window=60))
):
    t0 = time.time()

    # 1. Rewrite question for better retrieval
    search_query = await asyncio.to_thread(rewrite_query, req.question)

    # 2. Embed and retrieve chunks
    q_vec = await asyncio.to_thread(embed_query, search_query)
    chunks = await asyncio.to_thread(search, q_vec, top_k=TOP_K, doc_id_filter=req.doc_id)

    # 3. Fetch document summary for global context
    doc_summary = None
    target_doc_id = req.doc_id
    if not target_doc_id and chunks:
        target_doc_id = chunks[0].get('doc_id')
    if target_doc_id:
        doc = await db.get(Document, target_doc_id)
        if doc:
            doc_summary = doc.summary

    # 4. Build grounded prompt with summary + chunks
    prompt = build_prompt(req.question, chunks, summary=doc_summary)

    # Format sources to send immediately
    sources = [
        {
            'page': c['page'],
            'excerpt': c['text'][:200],
            'doc_id': c['doc_id']
        } for c in chunks
    ]
    sources_json = json.dumps(sources)

    # Capture question for logging inside the generator
    question_text = req.question

    async def event_generator():
        # First, send retrieved sources immediately
        yield f"event: sources\ndata: {sources_json}\n\n"

        full_response = []
        try:
            # Stream character delta chunks as they arrive from Gemini API
            async for chunk in generate_answer_stream_async(prompt):
                if chunk.text:
                    full_response.append(chunk.text)
                    chunk_data = json.dumps({'text': chunk.text})
                    yield f"event: delta\ndata: {chunk_data}\n\n"
        except Exception as e:
            error_data = json.dumps({'error': str(e)})
            yield f"event: error\ndata: {error_data}\n\n"
            return

        full_answer = ''.join(full_response)
        latency = int((time.time() - t0) * 1000)

        # Log query to database using an independent session
        # (the request-scoped session may have been closed by now)
        try:
            async with AsyncSessionLocal() as log_session:
                log = QueryLog(
                    question=question_text,
                    answer=full_answer,
                    latency_ms=latency
                )
                log_session.add(log)
                await log_session.commit()
        except Exception as e:
            logger.warning(f'[query/stream] Failed to save query log: {e}')

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@router.get('/queries')
async def list_queries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
):
    result = await db.execute(
        select(QueryLog)
        .order_by(QueryLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    return [{
        'id': l.id,
        'question': l.question,
        'answer': l.answer,
        'latency_ms': l.latency_ms,
        'created_at': l.created_at.isoformat(),
        'feedback': l.feedback
    } for l in logs]


class FeedbackRequest(BaseModel):
    feedback: str  # 'thumbs_up' or 'thumbs_down'


@router.post('/queries/{log_id}/feedback')
async def submit_feedback(
    log_id: int,
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
):
    if req.feedback not in ('thumbs_up', 'thumbs_down'):
        raise HTTPException(400, "Feedback must be either 'thumbs_up' or 'thumbs_down'")

    log = await db.get(QueryLog, log_id)
    if not log:
        raise HTTPException(404, 'Query log not found')

    log.feedback = req.feedback
    await db.commit()
    return {'status': 'success', 'message': 'Feedback recorded successfully'}
