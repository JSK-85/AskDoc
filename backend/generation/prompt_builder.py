SYSTEM_PROMPT = '''You are an expert document analyst. Answer using the document overview and context passages provided below.

Guidelines:
- Use ONLY information from the provided context. Do not use outside knowledge.
- Think carefully and reason through the context before answering. Connect information across different passages.
- If the question uses different wording than the document, look for equivalent concepts (e.g., "fake name" = alias/pseudonym/cover identity, "main character" = protagonist/central figure).
- The Document Overview contains a comprehensive summary — use it for big-picture and character questions.
- The Retrieved Passages contain specific text excerpts — use them for detailed evidence and page citations.
- Reference page numbers where you found the answer, e.g. (page 4).
- Be detailed and thorough. Provide complete answers with all relevant information.
- ONLY say "I could not find this in the uploaded document" if the information is truly absent from ALL provided context.'''


def build_prompt(question: str, chunks: list[dict], summary: str | None = None) -> str:
    parts = [SYSTEM_PROMPT]

    # Include the document-level summary for global context
    if summary:
        parts.append(f'\nDocument Overview:\n{summary}')

    # Include retrieved chunk passages for specific evidence
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f'[Context {i} | Page {c["page"]}]\n{c["text"]}')
    context_str = '\n\n'.join(context_parts)
    parts.append(f'\nRetrieved Passages:\n{context_str}')

    parts.append(f'\nQuestion: {question}')
    return '\n'.join(parts)

