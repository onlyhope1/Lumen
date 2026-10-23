"""Worker module initialization."""

from worker.celery_app import celery_app
from worker.tasks import process_document

__all__ = ["celery_app", "process_document"]
