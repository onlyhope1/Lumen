"""Pydantic schemas for Document API responses and requests."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Response schema for a single document."""

    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """Response returned after a successful upload."""

    id: uuid.UUID
    filename: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse]
    total: int
