"""Health check routes"""
from fastapi import APIRouter
from ..core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version
    }
