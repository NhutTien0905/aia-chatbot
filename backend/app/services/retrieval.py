"""Hybrid retrieval service combining semantic search, BM25, and reranking."""
from typing import List, Dict, Any, Optional
from .vectorstore import search_documents, get_all_documents
from .bm25 import search_bm25, build_bm25_index
from .reranker import rerank_documents


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.
    k is a constant (typically 60) to prevent high-ranked items
    from dominating.
    """
    fused_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for results in results_list:
        for rank, result in enumerate(results):
            # Create a unique key from text content
            doc_key = result["text"][:100]  # Use first 100 chars as key
            score = 1.0 / (k + rank + 1)

            if doc_key in fused_scores:
                fused_scores[doc_key] += score
            else:
                fused_scores[doc_key] = score
                doc_map[doc_key] = result

    # Sort by fused score
    sorted_keys = sorted(
        fused_scores.keys(),
        key=lambda x: fused_scores[x],
        reverse=True
    )

    results = []
    for key in sorted_keys:
        doc = doc_map[key]
        doc["score"] = fused_scores[key]
        results.append(doc)

    return results


def hybrid_search(
    session_id: str,
    query: str,
    top_k: int = 5,
    filter_filenames: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining semantic (ChromaDB) and BM25,
    then rerank with Cohere Rerank v4 for improved precision.

    If filter_filenames is provided, only chunks from those files are considered.
    """
    # Ensure BM25 index is built
    all_docs = get_all_documents(session_id)
    if all_docs:
        build_bm25_index(session_id, all_docs)

    # Retrieve more candidates for reranking (top_k * 2)
    candidate_k = top_k * 2

    # Semantic search (with optional metadata filter)
    semantic_results = search_documents(
        session_id, query, top_k=candidate_k, filter_filenames=filter_filenames
    )

    # BM25 search
    bm25_results = search_bm25(session_id, query, top_k=candidate_k)

    # Filter BM25 results by filename if specified
    if filter_filenames and bm25_results:
        bm25_results = [
            r for r in bm25_results
            if r.get("metadata", {}).get("filename") in filter_filenames
        ]

    # If only one source has results, use that
    if not semantic_results and not bm25_results:
        return []
    if not semantic_results:
        candidates = bm25_results[:candidate_k]
    elif not bm25_results:
        candidates = semantic_results[:candidate_k]
    else:
        # Fuse results
        candidates = reciprocal_rank_fusion([semantic_results, bm25_results])
        candidates = candidates[:candidate_k]

    # Rerank candidates to get final top_k
    reranked = rerank_documents(query, candidates, top_n=top_k)

    return reranked
