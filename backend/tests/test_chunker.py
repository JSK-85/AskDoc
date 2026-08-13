"""Tests for the chunker module."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.chunker import chunk_pages, CHUNK_SIZE, CHUNK_OVERLAP


def test_no_chunk_exceeds_max_size():
    """Chunk a 3000-character string and assert no chunk exceeds CHUNK_SIZE + CHUNK_OVERLAP."""
    long_text = "This is a test sentence. " * 150  # ~3750 chars
    pages = [{'text': long_text, 'page': 1}]
    chunks = chunk_pages(pages)

    for c in chunks:
        assert len(c['text']) <= CHUNK_SIZE + CHUNK_OVERLAP, \
            f"Chunk exceeds max size: {len(c['text'])} > {CHUNK_SIZE + CHUNK_OVERLAP}"


def test_overlap_works():
    """Assert consecutive chunks share overlapping text."""
    long_text = "Word " * 600  # 3000 chars
    pages = [{'text': long_text, 'page': 1}]
    chunks = chunk_pages(pages)

    if len(chunks) >= 2:
        for i in range(len(chunks) - 1):
            curr_end = chunks[i]['text'][-50:]
            next_start = chunks[i + 1]['text'][:CHUNK_OVERLAP + 50]
            # At least some overlap should exist
            assert any(
                curr_end[j:j+10] in next_start
                for j in range(len(curr_end) - 10)
            ), "Consecutive chunks should share overlapping text"


def test_preserves_page_number():
    """Assert chunk_pages preserves page_number correctly for multi-page input."""
    pages = [
        {'text': 'Page one content. ' * 50, 'page': 1},
        {'text': 'Page two content. ' * 50, 'page': 2},
        {'text': 'Page three content. ' * 50, 'page': 3},
    ]
    chunks = chunk_pages(pages)

    page_numbers_seen = set(c['page'] for c in chunks)
    assert 1 in page_numbers_seen
    assert 2 in page_numbers_seen
    assert 3 in page_numbers_seen


def test_chunk_index_sequential():
    """Assert chunk_index is sequential across all chunks."""
    pages = [
        {'text': 'Content A. ' * 100, 'page': 1},
        {'text': 'Content B. ' * 100, 'page': 2},
    ]
    chunks = chunk_pages(pages)

    for i, c in enumerate(chunks):
        assert c['chunk_index'] == i, f"Expected chunk_index {i}, got {c['chunk_index']}"


if __name__ == '__main__':
    test_no_chunk_exceeds_max_size()
    test_overlap_works()
    test_preserves_page_number()
    test_chunk_index_sequential()
    print("All chunker tests passed!")
