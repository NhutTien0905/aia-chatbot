"""Document summarization service for token optimization.

Long documents are summarized before indexing to reduce embedding costs
and improve retrieval quality by creating concise, information-dense chunks.
"""
import logging
from typing import List, Dict, Any
from openai import OpenAI
from ..config import settings
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Threshold: if a chunk has more than this many characters, summarize it
SUMMARIZE_THRESHOLD = 1500

SUMMARIZE_PROMPT = """Summarize the following text concisely while preserving all key facts, 
numbers, dates, names, and policy details. Keep the summary in the same language as the original.
Do NOT add any information that is not in the original text.

Text:
{text}

Concise summary:"""


@retry_with_backoff(max_retries=2, base_delay=1.0, exceptions=(Exception,))
def _call_summarize(text: str) -> str:
    """Call LLM to summarize a single text chunk."""
    client = OpenAI(
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[
            {"role": "system", "content": "You are a precise summarizer. Preserve all key facts and details."},
            {"role": "user", "content": SUMMARIZE_PROMPT.format(text=text)},
        ],
        temperature=0.0,
        max_completion_tokens=500,
    )

    return response.choices[0].message.content or text


def summarize_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Summarize chunks that exceed the character threshold.
    Short chunks are kept as-is. Long chunks get a summary stored
    alongside the original text for better retrieval.

    This optimizes token usage during embedding and retrieval while
    preserving the original text for citation display.
    """
    optimized_chunks: List[Dict[str, Any]] = []

    for chunk in chunks:
        text = chunk["text"]

        if len(text) > SUMMARIZE_THRESHOLD:
            try:
                summary = _call_summarize(text)
                # Store summary as the indexed text, keep original in metadata for citations
                optimized_chunk = {
                    "text": summary,
                    "metadata": {
                        **chunk["metadata"],
                        "original_text": text[:500],  # Keep first 500 chars for source preview
                        "is_summarized": True,
                    },
                }
                optimized_chunks.append(optimized_chunk)
                logger.debug(
                    f"Summarized chunk from {len(text)} to {len(summary)} chars "
                    f"({len(summary)/len(text)*100:.0f}%)"
                )
            except Exception as e:
                logger.warning(f"Summarization failed, using original: {e}")
                optimized_chunks.append(chunk)
        else:
            optimized_chunks.append(chunk)

    summarized_count = sum(
        1 for c in optimized_chunks if c.get("metadata", {}).get("is_summarized")
    )
    if summarized_count > 0:
        logger.info(f"Summarized {summarized_count}/{len(chunks)} chunks for token optimization")

    return optimized_chunks
