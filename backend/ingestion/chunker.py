from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 800))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 150))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=['\n\n', '\n', '. ', '? ', '! ', ' ', ''],
    keep_separator=True
)


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Input: [{text, page}]  Output: [{text, page, chunk_index}]"""
    result = []
    idx = 0
    for page in pages:
        splits = splitter.split_text(page['text'])
        for s in splits:
            result.append({'text': s, 'page': page['page'], 'chunk_index': idx})
            idx += 1
    return result
