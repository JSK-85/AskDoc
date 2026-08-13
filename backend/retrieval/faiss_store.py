"""FAISS vector store with file-based persistence.

Provides thread-safe and process-safe access via fcntl file locking.
Note: fcntl is Linux/macOS only. For Windows development, use WSL
or replace fcntl with the `filelock` PyPI package.
"""
import faiss
import json
import os
import numpy as np
import fcntl
import threading
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DIM = int(os.getenv('EMBEDDING_DIM', 384))
INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'data/faiss_index.bin')
META_PATH = os.getenv('FAISS_META_PATH', 'data/faiss_meta.json')
LOCK_PATH = 'data/faiss.lock'

os.makedirs('data', exist_ok=True)

_index = None
_meta = None
_index_mtime = 0
_lock = threading.Lock()


@contextmanager
def faiss_lock(write: bool = False):
    """Acquire a thread-safe and process-safe lock using fcntl and threading.Lock.

    Note: fcntl is POSIX-only (Linux / macOS). If you need Windows support,
    replace with the `filelock` package from PyPI.
    """
    with _lock:
        lock_mode = fcntl.LOCK_EX if write else fcntl.LOCK_SH
        with open(LOCK_PATH, 'a+') as f:
            try:
                fcntl.flock(f, lock_mode)
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


def _get_index() -> tuple[faiss.Index, list[dict]]:
    global _index, _meta, _index_mtime

    current_mtime = 0
    if os.path.exists(INDEX_PATH):
        current_mtime = os.path.getmtime(INDEX_PATH)

    # Return cached memory index if file has not changed on disk
    if _index is not None and _meta is not None and current_mtime == _index_mtime:
        return _index, _meta

    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        _index = faiss.read_index(INDEX_PATH)
        with open(META_PATH) as f:
            _meta = json.load(f)
        _index_mtime = current_mtime
    else:
        # Inner product on L2-normalized vectors = cosine similarity
        _index = faiss.IndexFlatIP(DIM)
        _meta = []
        _index_mtime = 0
    return _index, _meta


def upsert_chunks(vectors: list[list[float]], metadatas: list[dict]):
    """Append new vectors + metadata under an exclusive write lock."""
    with faiss_lock(write=True):
        index, meta = _get_index()
        arr = np.array(vectors, dtype='float32')
        faiss.normalize_L2(arr)  # Normalize for cosine similarity
        index.add(arr)
        meta.extend(metadatas)

        faiss.write_index(index, INDEX_PATH)
        with open(META_PATH, 'w') as f:
            json.dump(meta, f)

        # Update global cache validation mtime
        global _index_mtime
        _index_mtime = os.path.getmtime(INDEX_PATH)


def search(query_vector: list[float], top_k: int = 6,
           doc_id_filter: int | None = None) -> list[dict]:
    """Retrieve top-k chunks under a shared read lock."""
    with faiss_lock(write=False):
        index, meta = _get_index()
        if index.ntotal == 0:
            return []
        arr = np.array([query_vector], dtype='float32')
        faiss.normalize_L2(arr)
        scores, indices = index.search(arr, top_k * 3)  # fetch more, then filter

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            m = meta[idx]
            if doc_id_filter and m['doc_id'] != doc_id_filter:
                continue
            results.append({**m, 'score': float(score)})
            if len(results) == top_k:
                break
        return results


def delete_document_chunks(doc_id: int) -> int:
    """Delete all chunks belonging to doc_id by rebuilding the index.

    Uses a rebuild approach for correctness: collects all remaining vectors
    and metadata, then creates a fresh index. This avoids subtle
    metadata-to-vector misalignment issues that can occur with in-place
    removal on IndexFlat.
    """
    with faiss_lock(write=True):
        index, meta = _get_index()
        if index.ntotal == 0:
            return 0

        # Separate keep vs. remove
        keep_indices = [i for i, m in enumerate(meta) if m['doc_id'] != doc_id]
        removed_count = index.ntotal - len(keep_indices)

        if removed_count == 0:
            return 0

        if len(keep_indices) == 0:
            # All vectors belonged to this doc — reset to empty
            new_index = faiss.IndexFlatIP(DIM)
            new_meta = []
        else:
            # Reconstruct remaining vectors from the old index
            remaining_vectors = np.zeros((len(keep_indices), DIM), dtype='float32')
            for new_pos, old_pos in enumerate(keep_indices):
                remaining_vectors[new_pos] = index.reconstruct(old_pos)

            new_index = faiss.IndexFlatIP(DIM)
            new_index.add(remaining_vectors)
            new_meta = [meta[i] for i in keep_indices]

        # Persist
        faiss.write_index(new_index, INDEX_PATH)
        with open(META_PATH, 'w') as f:
            json.dump(new_meta, f)

        # Update in-memory cache
        global _index, _meta, _index_mtime
        _index = new_index
        _meta = new_meta
        _index_mtime = os.path.getmtime(INDEX_PATH)

        logger.info(f'[faiss] Deleted {removed_count} chunks for doc_id={doc_id}')
        return removed_count
