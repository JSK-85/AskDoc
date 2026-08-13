from sentence_transformers import SentenceTransformer
import os

EMBED_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

# Lazy-loaded inside the worker process to avoid SIGSEGV when Celery forks.
_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document chunks. Returns list of 384-dim vectors."""
    embeddings = _get_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single user query. Uses same model as ingestion."""
    return _get_model().encode([text], convert_to_numpy=True)[0].tolist()
