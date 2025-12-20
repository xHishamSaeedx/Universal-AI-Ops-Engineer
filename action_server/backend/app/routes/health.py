import logging
from fastapi import APIRouter
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint for the action server itself.
    Returns the operational status of the action server.
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "capabilities": [
            "restart_target_api",
            "restart_target_db",
            "verify_target_health",
            "remediate_db_pool_exhaustion"
        ],
        "scope": "target_server_only",
        "note": "Action server only controls target server remediation, not chaos injection"
    }


@router.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "description": "Remediation control plane for autonomous incident response"
    }
