"""Base types for extractors."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractionResult:
    """Result of a text extraction operation."""

    text: str
    page_count: Optional[int] = None
    method: str = "unknown"  # "direct", "ocr", or "docx"

    @property
    def is_empty(self) -> bool:
        return not self.text or not self.text.strip()
