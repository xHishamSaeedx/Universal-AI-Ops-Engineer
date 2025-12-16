from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.database import get_db
import psutil
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed health status including database and system metrics
    """
    # Test database connection
    try:
        from ..core.database import get_session_local
        SessionLocal = get_session_local()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
        db_error = None
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Get system metrics
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

    # Determine overall health
    overall_status = "healthy"
    if db_status != "healthy":
        overall_status = "unhealthy"
    elif system_metrics["memory_percent"] > 90:
        overall_status = "warning"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "services": {
            "database": {
                "status": db_status,
                "error": db_error
            }
        },
        "system": system_metrics,
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Simple readiness check for load balancers"""
    return {"status": "ready"}
