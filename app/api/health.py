"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Endpoint kesehatan sederhana untuk memastikan server berjalan."""
    return {"status": "ok"}
