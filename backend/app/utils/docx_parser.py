"""DOCX parsing utility using python-docx."""
from docx import Document
from typing import List, Dict, Any
from datetime import datetime
import io


def extract_text_from_docx(
    file_bytes: bytes,
    filename: str
) -> List[Dict[str, Any]]:
    """
    Extract text from DOCX file, grouped by sections.
    Sections are determined by headings or every N paragraphs.
    """
    doc = Document(io.BytesIO(file_bytes))
    sections_data: List[Dict[str, Any]] = []

    current_section: List[str] = []
    section_number = 1
    paragraph_start = 1
    paragraphs_per_section = 10

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue

        # Start new section on headings
        is_heading = para.style.name.startswith("Heading")

        if is_heading and current_section:
            # Save current section
            sections_data.append({
                "text": "\n".join(current_section),
                "metadata": {
                    "filename": filename,
                    "section_number": section_number,
                    "paragraph_range": f"{paragraph_start}-{paragraph_start + len(current_section) - 1}",
                    "upload_date": datetime.now().isoformat(),
                    "source_type": "docx",
                }
            })
            section_number += 1
            paragraph_start = i + 1
            current_section = [text]
        elif len(current_section) >= paragraphs_per_section:
            # Save section when it gets too long
            sections_data.append({
                "text": "\n".join(current_section),
                "metadata": {
                    "filename": filename,
                    "section_number": section_number,
                    "paragraph_range": f"{paragraph_start}-{paragraph_start + len(current_section) - 1}",
                    "upload_date": datetime.now().isoformat(),
                    "source_type": "docx",
                }
            })
            section_number += 1
            paragraph_start = i + 1
            current_section = [text]
        else:
            current_section.append(text)

    # Don't forget the last section
    if current_section:
        sections_data.append({
            "text": "\n".join(current_section),
            "metadata": {
                "filename": filename,
                "section_number": section_number,
                "paragraph_range": f"{paragraph_start}-{paragraph_start + len(current_section) - 1}",
                "upload_date": datetime.now().isoformat(),
                "source_type": "docx",
            }
        })

    return sections_data
