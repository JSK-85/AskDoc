from ingestion.embedder import embed_query
from retrieval.faiss_store import search
import os

TOP_K = int(os.getenv('TOP_K', 6))


def retrieve(question: str, doc_id: int | None = None) -> list[dict]:
    """Embed the question and retrieve top-k relevant chunks."""
    q_vec = embed_query(question)
    return search(q_vec, top_k=TOP_K, doc_id_filter=doc_id)
