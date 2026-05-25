"""Text chunking service."""
from typing import List, Dict, Any


def chunk_text(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Split text into chunks with overlap, preserving metadata.
    Uses character-based splitting with sentence awareness.
    """
    if not text.strip():
        return []

    # Split by sentences first
    separators = ["\n\n", "\n", ". ", "! ", "? ", "; "]
    chunks: List[Dict[str, Any]] = []

    # Simple recursive character splitter
    segments = _split_text(text, chunk_size, chunk_overlap, separators)

    for i, segment in enumerate(segments):
        chunk_metadata = {**metadata, "chunk_index": i}
        chunks.append({
            "text": segment.strip(),
            "metadata": chunk_metadata,
        })

    return chunks


def _split_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: List[str]
) -> List[str]:
    """Recursively split text using separators."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Find the best separator
    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    if not separator:
        # Force split by chunk_size
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    # Split by separator
    parts = text.split(separator)
    chunks: List[str] = []
    current_chunk = ""

    for part in parts:
        candidate = current_chunk + separator + part if current_chunk else part

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If single part is too long, recursively split
            if len(part) > chunk_size:
                remaining_separators = separators[separators.index(separator) + 1:] if separator in separators else []
                if remaining_separators:
                    sub_chunks = _split_text(part, chunk_size, chunk_overlap, remaining_separators)
                    chunks.extend(sub_chunks)
                else:
                    # Force split
                    start = 0
                    while start < len(part):
                        end = start + chunk_size
                        chunks.append(part[start:end])
                        start = end - chunk_overlap
                current_chunk = ""
            else:
                current_chunk = part

    if current_chunk:
        chunks.append(current_chunk)

    return [c for c in chunks if c.strip()]
