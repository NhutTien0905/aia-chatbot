"""Image OCR utility using EasyOCR."""
from typing import List, Dict, Any
from datetime import datetime
from PIL import Image
import io
import torch
import numpy as np


# Global reader instance (lazy loaded)
_reader = None

# check CUDA is available or not
is_gpu = torch.cuda.is_available()

def _get_reader():
    """Lazy load EasyOCR reader."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en", "vi"], gpu=is_gpu)
    return _reader


def extract_text_from_image(
    file_bytes: bytes,
    filename: str
) -> List[Dict[str, Any]]:
    """
    Extract text from image using EasyOCR.
    Supports English and Vietnamese.
    """
    reader = _get_reader()

    # Open and preprocess image
    image = Image.open(io.BytesIO(file_bytes))

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Convert to numpy array for EasyOCR
    img_array = np.array(image)

    # Run OCR
    results = reader.readtext(img_array, detail=1)

    # Combine all text
    texts = [result[1] for result in results]
    full_text = "\n".join(texts)

    if not full_text.strip():
        return []

    return [{
        "text": full_text,
        "metadata": {
            "filename": filename,
            "page_number": 1,
            "upload_date": datetime.now().isoformat(),
            "source_type": "image",
        }
    }]
