"""Tests for the FAISS store module."""
import os
import sys
import json
import tempfile
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_upsert_and_search():
    """Upsert 5 dummy vectors. Search with a known vector — assert top result has highest similarity."""
    # Use temp paths to avoid polluting real data
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['FAISS_INDEX_PATH'] = os.path.join(tmpdir, 'test_index.bin')
        os.environ['FAISS_META_PATH'] = os.path.join(tmpdir, 'test_meta.json')
        os.environ['EMBEDDING_DIM'] = '384'

        # Re-import to pick up new env vars
        import importlib
        import retrieval.faiss_store as fs
        importlib.reload(fs)

        # Create 5 dummy vectors
        np.random.seed(42)
        vectors = np.random.randn(5, 384).astype('float32').tolist()
        metadatas = [
            {'doc_id': 1, 'text': f'chunk {i}', 'page': 1, 'chunk_index': i}
            for i in range(5)
        ]

        fs.upsert_chunks(vectors, metadatas)

        # Search with the first vector — should find itself as top result
        results = fs.search(vectors[0], top_k=3)
        assert len(results) > 0, "Should return at least one result"
        assert results[0]['chunk_index'] == 0, "Top result should be the query vector itself"


def test_doc_id_filter():
    """Upsert chunks for doc_id=1 and doc_id=2, search with filter=1, assert only doc_id=1 results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['FAISS_INDEX_PATH'] = os.path.join(tmpdir, 'test_index.bin')
        os.environ['FAISS_META_PATH'] = os.path.join(tmpdir, 'test_meta.json')
        os.environ['EMBEDDING_DIM'] = '384'

        import importlib
        import retrieval.faiss_store as fs
        importlib.reload(fs)

        np.random.seed(123)
        # Doc 1: 3 chunks
        v1 = np.random.randn(3, 384).astype('float32').tolist()
        m1 = [{'doc_id': 1, 'text': f'doc1 chunk {i}', 'page': 1, 'chunk_index': i} for i in range(3)]

        # Doc 2: 3 chunks
        v2 = np.random.randn(3, 384).astype('float32').tolist()
        m2 = [{'doc_id': 2, 'text': f'doc2 chunk {i}', 'page': 1, 'chunk_index': i} for i in range(3)]

        fs.upsert_chunks(v1, m1)
        fs.upsert_chunks(v2, m2)

        # Search with filter for doc_id=1
        results = fs.search(v1[0], top_k=6, doc_id_filter=1)
        for r in results:
            assert r['doc_id'] == 1, f"Expected doc_id=1, got {r['doc_id']}"


if __name__ == '__main__':
    test_upsert_and_search()
    test_doc_id_filter()
    print("All FAISS store tests passed!")
