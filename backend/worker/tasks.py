"""Celery background tasks for document processing."""

import asyncio
import logging
import uuid
from sqlalchemy import select

from worker.celery_app import celery_app
from app.core.database import async_session
from app.models.document import Document
from app.services.extraction import extract_text

logger = logging.getLogger(__name__)


async def _process_document_async(document_id: str) -> dict:
    """Async implementation of document processing pipeline."""
    doc_uuid = uuid.UUID(document_id)

    async with async_session() as session:
        stmt = select(Document).where(Document.id == doc_uuid)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()

        if not doc:
            error_msg = f"Document {document_id} not found in database"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Transition status to processing
        doc.status = "processing"
        doc.error_message = None
        await session.commit()
        logger.info("Document %s status set to processing", document_id)

        try:
            # Run text extraction
            extraction = extract_text(doc.file_path, doc.content_type)

            doc.extracted_text = extraction.text
            doc.page_count = extraction.page_count
            doc.status = "ready"
            await session.commit()

            logger.info(
                "Document %s processed successfully (method: %s, pages: %s, chars: %d)",
                document_id,
                extraction.method,
                extraction.page_count,
                len(extraction.text or ""),
            )
            return {
                "status": "success",
                "document_id": document_id,
                "pages": extraction.page_count,
                "method": extraction.method,
            }

        except Exception as exc:
            logger.exception("Failed processing document %s", document_id)
            doc.status = "failed"
            doc.error_message = str(exc)
            await session.commit()
            return {
                "status": "failed",
                "document_id": document_id,
                "error": str(exc),
            }


@celery_app.task(name="process_document", bind=True, max_retries=2)
def process_document(self, document_id: str) -> dict:
    """Celery task entry point to extract and index document content."""
    logger.info("Celery task process_document started for ID: %s", document_id)
    try:
        return asyncio.run(_process_document_async(document_id))
    except Exception as exc:
        logger.exception("Unhandled error in task process_document: %s", exc)
        raise self.retry(exc=exc, countdown=10)
