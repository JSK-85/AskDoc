"""Generate a comprehensive document summary using Gemini.

Two-strategy approach:
  1. KNOWN WORKS: Ask Gemini if it recognizes the document (by title + sample text).
     If yes, leverage Gemini's training data for a detailed summary — fast, free,
     no rate-limit issues, and far more comprehensive than parsing.
  2. PERSONAL DOCS: For unrecognized documents, sample key pages (beginning, middle,
     end) and build a summary from those excerpts — stays within rate limits.
"""
import google.generativeai as genai
import logging
import re

from generation.gemini_config import get_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RECOGNITION_PROMPT = '''I have a document with the following title and opening text.
Is this a well-known published book, article, report, or other publicly available work?

Title: {title}

Opening text (first ~2000 chars):
{sample}

Respond with EXACTLY one of:
- "KNOWN: [Full Title] by [Author]" if you recognize it
- "UNKNOWN" if you do not recognize it or it appears to be a private/personal document

Nothing else.'''

KNOWN_WORK_PROMPT = '''You are a meticulous literary analyst. Provide an EXHAUSTIVE, COMPREHENSIVE
summary of the book "{title}" that would allow someone to answer ANY question about it.

Your summary MUST include ALL of the following:

1. **PROTAGONIST / MAIN CHARACTER**: Full name, occupation, background, central role.

2. **EVERY NAMED CHARACTER**: List ALL named characters. For each: full name, nationality/background,
   role (protagonist, antagonist, ally, villain, etc.), relationships to other characters,
   and what happens to them. Include aliases, fake names, and cover identities.

3. **ANTAGONISTS & VILLAINS**: Names, nationalities, organizations, motivations, actions.

4. **COMPLETE PLOT SUMMARY**: Detailed chronological summary from beginning to end.
   Every major event, twist, conflict, betrayal, kidnapping, death, rescue, deception.
   WHO did WHAT to WHOM, WHERE, and WHY.

5. **KEY RELATIONSHIPS**: Family ties, alliances, betrayals, romantic relationships, deceptions.

6. **ALIASES & FAKE NAMES**: Any character who uses a fake name, alias, cover identity, pseudonym.

7. **ORGANIZATIONS & GROUPS**: Named groups, agencies, factions, with their roles.

8. **LOCATIONS & SETTINGS**: Countries, cities, buildings, safe houses.

9. **THEMES & MOTIVES**: What drives each character, major themes of the work.

Write at least 3000 words. Be EXHAUSTIVE. A reader should be able to answer ANY question
about this book from your summary alone — including twisted or indirect questions like
"what was [character]'s fake name" or "who kidnapped [person]".'''

PERSONAL_DOC_PROMPT = '''You are a meticulous document analyst. Read the text excerpts below
and produce the most comprehensive summary you can.

Your summary MUST include ALL of the following (where applicable):

1. **Main Subject / Protagonist**: Who or what is this document primarily about?
2. **All Named People/Entities**: List every named person, org, or entity with their roles.
3. **Key Events & Actions**: What happened? WHO did WHAT to WHOM and WHY?
4. **Relationships**: Connections between people, organizations, etc.
5. **Locations**: Where do events take place?
6. **Themes & Purpose**: What is this document about at a high level?

Be as detailed as possible with the available excerpts.

---
DOCUMENT EXCERPTS:
'''


def _call_gemini(prompt: str, max_tokens: int = 8192, temperature: float = 0.1,
                 max_retries: int = 3) -> str:
    """Call Gemini with automatic retry on rate limit (429) errors."""
    model = get_model()

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                # Parse retry delay from error message
                match = re.search(r'retry in (\d+\.?\d*)', error_str, re.IGNORECASE)
                wait = float(match.group(1)) + 5 if match else 65
                logger.warning(
                    f'[summarizer] Rate limited (attempt {attempt+1}/{max_retries}), '
                    f'waiting {wait:.0f}s...'
                )
                # Raise a Celery-friendly retry instead of blocking the worker
                raise
            else:
                raise

    raise RuntimeError(f'Gemini rate limit exceeded after {max_retries} retries')


def generate_document_summary(pages: list[dict], filename: str = '') -> str:
    """Generate a comprehensive summary using the best available strategy.

    Strategy 1: Check if Gemini recognizes the document as a known work.
                If yes, use Gemini's training knowledge for a detailed summary.
    Strategy 2: For personal/unknown docs, sample key pages and summarize.

    Args:
        pages: List of {'text': str, 'page': int} from the document loader.
        filename: Original filename for recognition hints.

    Returns:
        A detailed summary string.
    """
    logger.info(f'[summarizer] Starting summary for "{filename}" ({len(pages)} pages)')

    # Strategy 1: Try to recognize as a known work
    known_summary = _try_known_work(pages, filename)
    if known_summary:
        return known_summary

    # Strategy 2: Summarize from sampled pages (personal/unknown docs)
    logger.info('[summarizer] Document not recognized — using excerpt-based summary')
    return _summarize_personal_doc(pages)


def _try_known_work(pages: list[dict], filename: str) -> str | None:
    """Check if this is a known published work and get a summary from Gemini's knowledge."""
    # Get sample text from first few pages
    sample_text = '\n'.join(p['text'] for p in pages[:5])[:2000]
    title = filename or 'Unknown'

    try:
        # Step 1: Ask Gemini if it recognizes the work
        result = _call_gemini(
            RECOGNITION_PROMPT.format(title=title, sample=sample_text),
            max_tokens=100,
            temperature=0.0
        ).strip()
        logger.info(f'[summarizer] Recognition result: {result}')

        if not result.startswith('KNOWN:'):
            return None

        # Step 2: Get comprehensive summary from Gemini's knowledge
        recognized_title = result.replace('KNOWN:', '').strip()
        logger.info(f'[summarizer] Recognized as: {recognized_title}')

        summary = _call_gemini(
            KNOWN_WORK_PROMPT.format(title=recognized_title),
            max_tokens=8192,
            temperature=0.1
        )

        logger.info(f'[summarizer] Known work summary: {len(summary)} chars')
        return summary

    except Exception as e:
        logger.warning(f'[summarizer] Known work detection failed: {e}')
        return None


def _summarize_personal_doc(pages: list[dict]) -> str:
    """For unknown/personal documents, sample key pages and summarize."""
    # Smart sampling: beginning + middle + end gives the best coverage
    total = len(pages)
    sampled = []

    if total <= 30:
        # Small doc — use all pages
        sampled = pages
    else:
        # First 10 pages (introduction, setup)
        sampled.extend(pages[:10])
        # 5 pages from 25% mark
        q1 = total // 4
        sampled.extend(pages[q1:q1 + 5])
        # 5 pages from middle
        mid = total // 2
        sampled.extend(pages[mid:mid + 5])
        # 5 pages from 75% mark
        q3 = (total * 3) // 4
        sampled.extend(pages[q3:q3 + 5])
        # Last 5 pages (conclusion, resolution)
        sampled.extend(pages[-5:])

    sample_text = '\n\n'.join(
        f'--- Page {p["page"]} ---\n{p["text"]}' for p in sampled
    )

    # Truncate if still too long (stay well under rate limits)
    if len(sample_text) > 150_000:
        sample_text = sample_text[:150_000]

    logger.info(f'[summarizer] Sampled {len(sampled)} pages, {len(sample_text)} chars')

    summary = _call_gemini(PERSONAL_DOC_PROMPT + sample_text, max_tokens=8192)
    logger.info(f'[summarizer] Personal doc summary: {len(summary)} chars')
    return summary
