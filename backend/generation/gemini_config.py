"""Centralized Gemini API configuration.

All modules that use Gemini import from here to avoid:
  - Duplicate genai.configure() calls at import time
  - Crashes when GEMINI_API_KEY is not yet set
  - Scattered model name resolution
"""
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

_configured = False

LLM_MODEL = os.getenv('GEMINI_LLM_MODEL', 'gemini-3.5-flash')


def _ensure_configured():
    """Lazily configure the Gemini SDK on first use (not at import time)."""
    global _configured
    if _configured:
        return

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError(
            'GEMINI_API_KEY environment variable is not set. '
            'Set it in your .env file or environment.'
        )

    genai.configure(api_key=api_key)
    _configured = True
    logger.info('[gemini] SDK configured successfully')


def get_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Return a configured GenerativeModel instance.

    Call this instead of genai.GenerativeModel() directly.
    """
    _ensure_configured()
    return genai.GenerativeModel(model_name or LLM_MODEL)
