import pdfplumber
import logging

logger = logging.getLogger(__name__)


def load_pdf(path: str) -> list[dict]:
    """Returns [{text: str, page: int}, ...]. Page is 1-indexed."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(layout=True)
            if not text or not text.strip():
                logger.warning(f'Page {i+1} returned no text — possibly scanned. Skipping.')
                continue
            pages.append({'text': text.strip(), 'page': i + 1})
    return pages


def load_txt(path: str) -> list[dict]:
    """Plain text files treated as a single page."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    return [{'text': text, 'page': 1}]
