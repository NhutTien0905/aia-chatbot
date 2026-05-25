"""LLM service for generating answers with citations."""
from typing import List, Dict, Any, AsyncGenerator
from openai import OpenAI
from ..config import settings


SYSTEM_PROMPT = """You are an insurance document assistant. You help users understand their insurance documents.

CRITICAL RULES:
1. Answer questions ONLY based on the provided context from uploaded documents.
2. If the answer is NOT in the context, you MUST say: "I don't have enough information in the uploaded documents to answer this question."
3. NEVER make up or hallucinate information.
4. Always cite your sources using numbered references like [1], [2], etc. matching the source numbers provided in the context.
5. Support both English and Vietnamese - respond in the same language as the question.
6. You may use **bold text** to emphasize key terms or important information.

CITATION FORMAT:
- Use numbered references in your answer: [1], [2], [3], etc.
- The numbers correspond to the source list provided with the context.
- Place the citation immediately after the relevant statement.
- Example: "Your coverage includes theft [1] and fire damage [2]."

When citing, use the numbered source references provided with each context chunk."""


def build_context_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Build context string from retrieved chunks with numbered sources."""
    if not chunks:
        return "No relevant documents found."

    context_parts = []
    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata", {})
        source_info = f"[Source {i + 1}: {metadata.get('filename', 'unknown')}"

        if metadata.get("page_number"):
            source_info += f", Page {metadata['page_number']}"
        if metadata.get("section_number"):
            source_info += f", Section {metadata['section_number']}"
        if metadata.get("paragraph_range"):
            source_info += f", Paragraphs {metadata['paragraph_range']}"

        source_info += "]"

        context_parts.append(f"{source_info}\n{chunk['text']}")

    return "\n\n---\n\n".join(context_parts)


def generate_answer_stream(
    question: str,
    chunks: List[Dict[str, Any]]
) -> AsyncGenerator[str, None]:
    """Generate streaming answer from LLM."""
    client = OpenAI(
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )

    context = build_context_prompt(chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context from uploaded documents:\n\n{context}\n\n---\n\nUser question: {question}"}
    ]

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=messages,
        temperature=0.1,
        max_completion_tokens=2000,
        stream=True,
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def generate_answer(
    question: str,
    chunks: List[Dict[str, Any]]
) -> str:
    """Generate non-streaming answer from LLM."""
    client = OpenAI(
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )

    context = build_context_prompt(chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context from uploaded documents:\n\n{context}\n\n---\n\nUser question: {question}"}
    ]

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=messages,
        temperature=0.1,
        max_completion_tokens=2000,
    )

    return response.choices[0].message.content or "I couldn't generate a response."
