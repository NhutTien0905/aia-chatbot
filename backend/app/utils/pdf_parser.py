"""PDF parsing utility using PyMuPDF."""
import fitz  # PyMuPDF
from typing import List, Dict, Any
from datetime import datetime


def extract_text_from_pdf(
    file_bytes: bytes,
    filename: str,
    max_pages: int = 20
) -> List[Dict[str, Any]]:
    """
    Extract text from PDF file, page by page.
    Returns list of dicts with text and metadata.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_data: List[Dict[str, Any]] = []

    num_pages = min(len(doc), max_pages)

    for page_num in range(num_pages):
        page = doc[page_num]
        text = page.get_text("text").strip()

        if text:
            pages_data.append({
                "text": text,
                "metadata": {
                    "filename": filename,
                    "page_number": page_num + 1,
                    "upload_date": datetime.now().isoformat(),
                    "source_type": "pdf",
                }
            })

    doc.close()
    return pages_data
