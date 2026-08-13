"""Lightweight query rewriter using Gemini.

When a user asks a "twisted" question like "what was Tarighian's fake name",
the embedding of those exact words may not match chunks that say "alias",
"cover identity", "pseudonym", etc.

This module rewrites the user's question into an expanded search query that
includes synonyms and alternative phrasings, dramatically improving retrieval.
"""
import google.generativeai as genai
import logging
from generation.gemini_config import get_model

logger = logging.getLogger(__name__)

REWRITE_PROMPT = '''Given this user question, generate a single expanded search query
that includes the original question plus synonyms, alternative phrasings, and related
terms that might appear in a document. This will be used for semantic search.

Rules:
- Output ONLY the expanded search query, nothing else
- Keep it under 100 words
- Include the original key terms
- Add synonyms and related phrases
- Do NOT answer the question

User question: '''


def rewrite_query(question: str) -> str:
    """Expand a user question into a richer search query for better retrieval.

    Returns the expanded query string, or the original question if rewriting fails.
    """
    try:
        model = get_model()
        response = model.generate_content(
            REWRITE_PROMPT + question,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=150,
            )
        )
        expanded = response.text.strip()
        logger.info(f'[rewriter] "{question}" -> "{expanded[:100]}..."')
        return expanded
    except Exception as e:
        logger.warning(f'[rewriter] Failed, using original query: {e}')
        return question
