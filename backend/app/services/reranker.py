"""Reranker service using Cohere Rerank v4 via Azure AI."""
import logging
from typing import List, Dict, Any

from openai import OpenAI

from ..config import settings

logger = logging.getLogger(__name__)

# Initialize reranker client
_reranker_client: OpenAI | None = None


def get_reranker_client() -> OpenAI:
    """Get or create the reranker OpenAI client."""
    global _reranker_client
    if _reranker_client is None:
        _reranker_client = OpenAI(
            base_url=settings.reranker_endpoint,
            api_key=settings.reranker_api_key,
        )
    return _reranker_client


def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """
    Rerank documents using Cohere Rerank model via Azure AI.

    Args:
        query: The user query to rerank against.
        documents: List of document dicts with at least a "text" field.
        top_n: Number of top results to return.

    Returns:
        Reranked list of documents (top_n), with rerank_score added.
        Falls back to original order (truncated) if reranking fails.
    """
    if not documents:
        return []

    if not settings.reranker_api_key:
        logger.warning("Reranker API key not configured, skipping rerank.")
        return documents[:top_n]

    try:
        client = get_reranker_client()
        doc_texts = [doc["text"] for doc in documents]

        response = client.post(
            "",
            body={
                "model": settings.reranker_model,
                "query": query,
                "documents": doc_texts,
                "top_n": top_n,
            },
            cast_to=object,
        )

        # Parse response and map back to original documents
        reranked = []
        for result in response["results"]:
            idx = result["index"]
            doc = documents[idx].copy()
            doc["rerank_score"] = result["relevance_score"]
            reranked.append(doc)

        return reranked

    except Exception as e:
        logger.error(f"Reranking failed, falling back to RRF scores: {e}")
        return documents[:top_n]
