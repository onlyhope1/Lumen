"""Image text extractor using Tesseract OCR."""

import logging
import os
import shutil
from pathlib import Path
from PIL import Image
import pytesseract

from app.services.extractors.base import ExtractionResult

logger = logging.getLogger(__name__)

# Common Tesseract executable paths on Windows
_COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]


def _configure_tesseract():
    """Ensure tesseract binary is located if on Windows and not in PATH."""
    if shutil.which("tesseract"):
        return True
    for path in _COMMON_TESSERACT_PATHS:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


def extract_image(file_path: str) -> ExtractionResult:
    """Extract text from an image file using Tesseract OCR."""
    _configure_tesseract()
    try:
        with Image.open(file_path) as img:
            # Convert palette/RGBA images to RGB for optimal OCR
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            text = pytesseract.image_to_string(img)

        return ExtractionResult(
            text=text.strip(),
            page_count=1,
            method="ocr",
        )
    except pytesseract.TesseractNotFoundError as e:
        logger.error("Tesseract OCR is not installed or not in PATH: %s", e)
        raise RuntimeError(
            "Tesseract OCR is not installed or not found in system PATH. "
            "Please install Tesseract OCR for image text extraction."
        ) from e
    except Exception as e:
        logger.exception("OCR extraction failed for %s", file_path)
        raise RuntimeError(f"OCR failed: {e}") from e
