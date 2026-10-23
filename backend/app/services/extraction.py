"""Text extraction pipeline — extracts text from PDFs, DOCX, and images.

Supports:
- Text-based PDFs -> direct text extraction via PyPDF2 / pypdf
- Scanned PDFs -> pdf2image + Tesseract OCR fallback
- DOCX -> python-docx paragraph extraction
- Images (PNG, JPEG, TIFF) -> Tesseract OCR
"""

import logging
from pathlib import Path

from app.services.extractors.base import ExtractionResult
from app.services.extractors.pdf_extractor import extract_pdf
from app.services.extractors.docx_extractor import extract_docx
from app.services.extractors.image_extractor import extract_image

logger = logging.getLogger(__name__)

# Map content types to extraction functions
EXTRACTOR_MAP = {
    "application/pdf": extract_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_docx,
    "image/png": extract_image,
    "image/jpeg": extract_image,
    "image/tiff": extract_image,
}


def extract_text(file_path: str, content_type: str) -> ExtractionResult:
    """Extract text from a file based on its content type.

    Args:
        file_path: Path to the file on disk.
        content_type: MIME type of the file.

    Returns:
        ExtractionResult with the extracted text and metadata.

    Raises:
        ValueError: If the content type is not supported.
        RuntimeError: If extraction fails.
    """
    extractor = EXTRACTOR_MAP.get(content_type)
    if not extractor:
        raise ValueError(f"Unsupported content type for extraction: {content_type}")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info("Extracting text from %s (type: %s)", path.name, content_type)

    try:
        result = extractor(file_path)
        logger.info(
            "Extraction complete: %d chars, %s pages, method=%s",
            len(result.text),
            result.page_count,
            result.method,
        )
        return result
    except Exception as e:
        logger.exception("Extraction failed for %s", file_path)
        raise RuntimeError(f"Text extraction failed: {e}") from e


__all__ = ["extract_text", "ExtractionResult"]
