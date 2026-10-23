"""PDF text extractor with OCR fallback for scanned documents."""

import logging
from PyPDF2 import PdfReader

from app.services.extractors.base import ExtractionResult
from app.services.extractors.image_extractor import _configure_tesseract

logger = logging.getLogger(__name__)


def _extract_direct(file_path: str) -> tuple[str, int]:
    """Extract embedded text directly from PDF using PyPDF2."""
    reader = PdfReader(file_path)
    page_texts = []
    page_count = len(reader.pages)

    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            page_texts.append(page_text.strip())

    return "\n\n".join(page_texts), page_count


def _extract_ocr(file_path: str) -> tuple[str, int]:
    """Extract text from scanned PDF by rendering pages to images and running OCR."""
    import pytesseract
    from pdf2image import convert_from_path

    _configure_tesseract()
    logger.info("Running OCR extraction for scanned PDF: %s", file_path)

    images = convert_from_path(file_path)
    page_count = len(images)
    page_texts = []

    for idx, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        if text.strip():
            page_texts.append(text.strip())

    return "\n\n".join(page_texts), page_count


def extract_pdf(file_path: str) -> ExtractionResult:
    """Extract text from PDF.

    First attempts direct text extraction. If the text is empty or negligible
    (indicating a scanned or rasterized PDF), falls back to OCR.
    """
    try:
        direct_text, page_count = _extract_direct(file_path)
        # If substantial text found, return direct extraction
        if len(direct_text.strip()) >= 50:
            return ExtractionResult(
                text=direct_text,
                page_count=page_count,
                method="direct",
            )
        logger.info(
            "PDF %s has minimal embedded text (%d chars). Attempting OCR fallback...",
            file_path,
            len(direct_text.strip()),
        )
    except Exception as e:
        logger.warning("Direct PDF extraction encountered an error: %s. Trying OCR fallback...", e)
        direct_text = ""
        page_count = 1

    # Attempt OCR fallback
    try:
        ocr_text, ocr_pages = _extract_ocr(file_path)
        if ocr_text.strip():
            return ExtractionResult(
                text=ocr_text,
                page_count=ocr_pages,
                method="ocr",
            )
    except Exception as ocr_err:
        logger.warning(
            "OCR fallback unavailable or failed (%s). Retaining direct extraction output.",
            ocr_err,
        )

    # Return whatever direct text was retrieved even if short
    return ExtractionResult(
        text=direct_text,
        page_count=page_count,
        method="direct" if direct_text else "empty",
    )
