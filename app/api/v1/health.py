from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check")
async def health_check():
    """Returns the API health status, version, and storage readiness."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "storage_ready": settings.STORAGE_DIR.exists(),
        "certificates_dir": str(settings.CERTIFICATES_DIR),
    }
