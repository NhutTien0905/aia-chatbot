"""Document ingestion pipeline."""
from typing import List, Dict, Any, Tuple
from ..utils.pdf_parser import extract_text_from_pdf
from ..utils.docx_parser import extract_text_from_docx
from ..utils.image_parser import extract_text_from_image
from .chunking import chunk_text
from .vectorstore import add_documents
from .bm25 import build_bm25_index
from .summarizer import summarize_chunks
from ..config import settings


ALLOWED_EXTENSIONS = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
}

ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}


def validate_file(filename: str, content_type: str, size: int) -> Tuple[bool, str]:
    """Validate uploaded file."""
    # Check extension
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Allowed: {ALLOWED_FILE_EXTENSIONS}"

    # Check content type
    if content_type not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported content type: {content_type}"

    # Check size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if size > max_size:
        return False, f"File too large: {size / 1024 / 1024:.1f}MB. Max: {settings.max_file_size_mb}MB"

    return True, ""


async def process_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    session_id: str
) -> Dict[str, Any]:
    """Process a single document through the ingestion pipeline."""
    file_type = ALLOWED_EXTENSIONS.get(content_type, "unknown")

    # Step 1: Extract text based on file type
    if file_type == "pdf":
        pages_data = extract_text_from_pdf(
            file_bytes, filename, max_pages=settings.max_pdf_pages
        )
    elif file_type == "docx":
        pages_data = extract_text_from_docx(file_bytes, filename)
    elif file_type == "image":
        pages_data = extract_text_from_image(file_bytes, filename)
    else:
        return {"success": False, "error": "Unsupported file type", "num_chunks": 0}

    if not pages_data:
        return {"success": False, "error": "No text could be extracted from file", "num_chunks": 0}

    # Step 2: Chunk the extracted text
    all_chunks: List[Dict[str, Any]] = []
    for page_data in pages_data:
        chunks = chunk_text(
            text=page_data["text"],
            metadata=page_data["metadata"],
            chunk_size=500,
            chunk_overlap=50,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return {"success": False, "error": "No chunks generated", "num_chunks": 0}

    # Step 3: Summarize long chunks for token optimization
    all_chunks = summarize_chunks(all_chunks)

    # Step 4: Index into vector store
    try:
        num_indexed = add_documents(session_id, all_chunks)
    except Exception as e:
        return {"success": False, "error": f"Indexing failed: {str(e)}", "num_chunks": 0}

    return {
        "success": True,
        "error": None,
        "num_chunks": num_indexed,
        "file_type": file_type,
    }
