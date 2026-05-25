"""BM25 search service for hybrid retrieval."""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import re

# In-memory BM25 indexes per session
_bm25_indexes: Dict[str, Dict[str, Any]] = {}


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer for BM25."""
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def build_bm25_index(session_id: str, documents: List[Dict[str, Any]]) -> None:
    """Build or rebuild BM25 index for a session."""
    if not documents:
        return

    corpus = [_tokenize(doc["text"]) for doc in documents]
    bm25 = BM25Okapi(corpus)

    _bm25_indexes[session_id] = {
        "bm25": bm25,
        "documents": documents,
    }


def search_bm25(
    session_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Search using BM25 index."""
    if session_id not in _bm25_indexes:
        return []

    index_data = _bm25_indexes[session_id]
    bm25 = index_data["bm25"]
    documents = index_data["documents"]

    tokenized_query = _tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # Get top-k indices
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "text": documents[idx]["text"],
                "metadata": documents[idx]["metadata"],
                "score": float(scores[idx]),
            })

    return results


def remove_index(session_id: str) -> None:
    """Remove BM25 index for a session."""
    _bm25_indexes.pop(session_id, None)
