"""LLM generation client using Gemini.

Uses centralized gemini_config for lazy SDK initialization.
All calls have explicit timeouts to prevent hanging workers.
"""
import asyncio
import google.generativeai as genai
from generation.gemini_config import get_model

# Default timeout for LLM calls (seconds)
LLM_TIMEOUT = 120


def generate_answer(prompt: str) -> str:
    model = get_model()
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=2048,
        )
    )
    return response.text


async def generate_answer_async(prompt: str) -> str:
    """Non-blocking asynchronous LLM generation call with timeout."""
    model = get_model()
    response = await asyncio.wait_for(
        model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
            )
        ),
        timeout=LLM_TIMEOUT,
    )
    return response.text


async def generate_answer_stream_async(prompt: str):
    """Yield answer chunks asynchronously for SSE streaming."""
    model = get_model()
    response = await asyncio.wait_for(
        model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
            ),
            stream=True
        ),
        timeout=LLM_TIMEOUT,
    )
    async for chunk in response:
        yield chunk
