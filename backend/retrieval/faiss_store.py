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
_meta = None  # Will be a dict mapping string ID to metadata dict
_next_id = 1
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


def _get_index() -> tuple[faiss.Index, dict]:
    global _index, _meta, _index_mtime, _next_id

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
        
        # Migration: If old IndexFlatIP is loaded (which returns -1 for IDMap check) 
        # or if meta is a list instead of a dict, we rebuild into IDMap
        if isinstance(_meta, list):
            logger.info("Migrating old IndexFlatIP list format to IndexIDMap dict format...")
            old_index = _index
            old_meta_list = _meta
            
            _index = faiss.IndexIDMap(faiss.IndexFlatIP(DIM))
            _meta = {}
            _next_id = 1
            
            if old_index.ntotal > 0:
                vectors = np.zeros((old_index.ntotal, DIM), dtype='float32')
                ids = np.zeros(old_index.ntotal, dtype='int64')
                for i in range(old_index.ntotal):
                    vectors[i] = old_index.reconstruct(i)
                    ids[i] = _next_id
                    _meta[str(_next_id)] = old_meta_list[i]
                    _next_id += 1
                _index.add_with_ids(vectors, ids)
                
            # Save migrated index immediately
            faiss.write_index(_index, INDEX_PATH)
            with open(META_PATH, 'w') as f:
                json.dump(_meta, f)
        else:
            # It's already the new format, find highest ID
            highest_id = max([int(k) for k in _meta.keys()] + [0])
            _next_id = highest_id + 1
            
        _index_mtime = os.path.getmtime(INDEX_PATH)
    else:
        # IDMap wrapper around FlatIP for O(1) deletions
        _index = faiss.IndexIDMap(faiss.IndexFlatIP(DIM))
        _meta = {}
        _next_id = 1
        _index_mtime = 0
    return _index, _meta


def upsert_chunks(vectors: list[list[float]], metadatas: list[dict]):
    """Append new vectors + metadata under an exclusive write lock."""
    global _next_id
    with faiss_lock(write=True):
        index, meta = _get_index()
        n = len(vectors)
        if n == 0:
            return
            
        arr = np.array(vectors, dtype='float32')
        faiss.normalize_L2(arr)
        
        # Generate sequential IDs
        ids = np.arange(_next_id, _next_id + n, dtype='int64')
        index.add_with_ids(arr, ids)
        
        for i in range(n):
            meta[str(ids[i])] = metadatas[i]
            
        _next_id += n

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
            str_idx = str(idx)
            if str_idx not in meta:
                continue
            m = meta[str_idx]
            if doc_id_filter and m['doc_id'] != doc_id_filter:
                continue
            results.append({**m, 'score': float(score)})
            if len(results) == top_k:
                break
        return results


def delete_document_chunks(doc_id: int) -> int:
    """Delete all chunks belonging to doc_id in O(1) time using remove_ids."""
    with faiss_lock(write=True):
        index, meta = _get_index()
        if index.ntotal == 0:
            return 0

        # Find IDs belonging to this document
        ids_to_remove = []
        for k, m in meta.items():
            if m['doc_id'] == doc_id:
                ids_to_remove.append(int(k))
                
        if not ids_to_remove:
            return 0
            
        # O(1) remove from FAISS IDMap
        arr_ids = np.array(ids_to_remove, dtype='int64')
        index.remove_ids(arr_ids)
        
        # O(1) remove from dict metadata
        for id_val in ids_to_remove:
            del meta[str(id_val)]

        # Persist
        faiss.write_index(index, INDEX_PATH)
        with open(META_PATH, 'w') as f:
            json.dump(meta, f)

        # Update in-memory cache mtime
        global _index_mtime
        _index_mtime = os.path.getmtime(INDEX_PATH)

        logger.info(f'[faiss] Deleted {len(ids_to_remove)} chunks for doc_id={doc_id}')
        return len(ids_to_remove)
