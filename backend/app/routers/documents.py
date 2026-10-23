"""Documents router — upload, list, get, delete documents."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
)
from app.services.file_storage import (
    ALLOWED_CONTENT_TYPES,
    save_upload,
    delete_file,
)

router = APIRouter(prefix="/documents", tags=["documents"])

# Placeholder owner ID until auth is implemented in Phase 9
PLACEHOLDER_OWNER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for processing.

    Accepts PDF, DOCX, PNG, JPEG, and TIFF files.
    The document is saved to disk and queued for async text extraction.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    # Read and validate size
    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save file to disk
    file_path, file_size = await save_upload(
        file_bytes, file.filename or "upload", file.content_type
    )

    # Create document record
    doc = Document(
        filename=file.filename or "upload",
        content_type=file.content_type,
        file_path=file_path,
        file_size=file_size,
        status="queued",
        owner_id=PLACEHOLDER_OWNER_ID,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        message="Document uploaded successfully and queued for processing",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all documents, optionally filtered by status."""
    query = select(Document).where(Document.owner_id == PLACEHOLDER_OWNER_ID)

    if status_filter:
        query = query.where(Document.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Fetch page
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single document by ID."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == PLACEHOLDER_OWNER_ID,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its file from disk."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == PLACEHOLDER_OWNER_ID,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file from disk
    delete_file(doc.file_path)

    # Delete from database
    await db.delete(doc)
