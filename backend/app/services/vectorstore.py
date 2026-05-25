"""ChromaDB vector store service."""
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..config import settings
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )
    return _chroma_client


def get_openai_client() -> OpenAI:
    """Get OpenAI client configured for Azure."""
    return OpenAI(
        base_url=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
    )


@retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(Exception,))
def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text with retry."""
    client = get_openai_client()
    response = client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=text
    )
    return response.data[0].embedding


@retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(Exception,))
def _embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a single batch with retry."""
    client = get_openai_client()
    response = client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=texts
    )
    return [d.embedding for d in response.data]


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts with retry logic."""
    all_embeddings: List[List[float]] = []
    batch_size = 20

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Embedding batch {i // batch_size + 1} ({len(batch)} texts)")
        embeddings = _embed_batch(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def get_collection_name(session_id: str) -> str:
    """Get collection name for a session."""
    # ChromaDB collection names must be 3-63 chars, alphanumeric + underscores
    clean_id = session_id.replace("-", "_")[:50]
    return f"s_{clean_id}"


def add_documents(
    session_id: str,
    chunks: List[Dict[str, Any]]
) -> int:
    """Add document chunks to ChromaDB collection."""
    if not chunks:
        return 0

    client = get_chroma_client()
    collection_name = get_collection_name(session_id)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    # Prepare data
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"{session_id}_{i}_{chunk['metadata'].get('filename', 'unknown')}"
           for i, chunk in enumerate(chunks)]

    # Get embeddings
    embeddings = get_embeddings_batch(texts)

    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


def search_documents(
    session_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Search documents in a session's collection."""
    client = get_chroma_client()
    collection_name = get_collection_name(session_id)

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        return []

    # Get query embedding
    query_embedding = get_embedding(query)

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    search_results: List[Dict[str, Any]] = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            search_results.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "score": 1 - (results["distances"][0][i] if results["distances"] else 0),
            })

    return search_results


def delete_collection(session_id: str) -> bool:
    """Delete a session's collection."""
    client = get_chroma_client()
    collection_name = get_collection_name(session_id)
    try:
        client.delete_collection(name=collection_name)
        return True
    except Exception:
        return False


def get_all_documents(session_id: str) -> List[Dict[str, Any]]:
    """Get all documents in a session's collection (for BM25 indexing)."""
    client = get_chroma_client()
    collection_name = get_collection_name(session_id)

    try:
        collection = client.get_collection(name=collection_name)
        results = collection.get(include=["documents", "metadatas"])

        docs = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                docs.append({
                    "text": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return docs
    except Exception:
        return []
