"""Health check router."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return service health status."""
    return {
        "status": "healthy",
        "service": "ai-doc-intelligence",
    }
