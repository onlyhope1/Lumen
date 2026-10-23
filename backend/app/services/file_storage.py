"""File storage service — saves uploaded files to disk."""

import os
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings

# Allowed MIME types for upload
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "image/png",
    "image/jpeg",
    "image/tiff",
}

# Map content types to extensions for clean file names
EXTENSION_MAP = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/tiff": ".tiff",
}


def get_upload_dir() -> Path:
    """Return the upload directory, creating it if needed."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def save_upload(file_bytes: bytes, original_filename: str, content_type: str) -> tuple[str, int]:
    """Save uploaded file to disk.

    Returns:
        (file_path, file_size) — path relative to UPLOAD_DIR and size in bytes.
    """
    ext = EXTENSION_MAP.get(content_type, Path(original_filename).suffix)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = get_upload_dir()
    full_path = upload_dir / unique_name

    async with aiofiles.open(full_path, "wb") as f:
        await f.write(file_bytes)

    return str(full_path), len(file_bytes)


def delete_file(file_path: str) -> None:
    """Delete a file from disk if it exists."""
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
