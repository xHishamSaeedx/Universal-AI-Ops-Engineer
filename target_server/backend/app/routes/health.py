from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.database import get_db, get_pool_metrics
import psutil
import time
from pathlib import Path
from collections import deque
from datetime import datetime, timezone

router = APIRouter()

# In-memory metrics tracking (for demo purposes)
# In production, this would be in Redis/Prometheus/etc.
_request_times = deque(maxlen=100)
_error_count = 0
_success_count = 0

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns health status with sanitized errors.
    Provides symptoms rather than root causes to enable proper diagnosis.
    """
    # Test database connection
    try:
        from ..core.database import get_session_local
        session_local_cls = get_session_local()
        db = session_local_cls()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
        db_error = None
    except Exception as e:
        db_status = "unhealthy"
        # Sanitize error message - don't expose exact root cause
        error_str = str(e).lower()
        if "timeout" in error_str or "pool" in error_str:
            db_error = "Database connection timeout"
        elif "auth" in error_str or "password" in error_str:
            db_error = "Database authentication failed"
        elif "refused" in error_str or "connect" in error_str:
            db_error = "Database connection refused"
        else:
            db_error = "Database error"

    # Get system metrics
    # Cross-platform disk root (Windows needs a drive like "C:\\")
    disk_root = Path.cwd().anchor or "/"
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage(disk_root).percent
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

@router.get("/metrics")
async def metrics_endpoint():
    """
    Observability metrics endpoint
    Returns aggregated metrics that require analysis to diagnose issues.
    This mimics what agents would see in Prometheus/Grafana.
    """
    global _request_times, _error_count, _success_count
    
    # Calculate response time statistics
    avg_response_time = sum(_request_times) / len(_request_times) if _request_times else 0
    
    # Calculate error rate
    total_requests = _error_count + _success_count
    error_rate = (_error_count / total_requests * 100) if total_requests > 0 else 0
    
    # Get pool metrics (sanitized)
    pool_metrics = get_pool_metrics()
    
    # System resource metrics
    disk_root = Path.cwd().anchor or "/"
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "application": {
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate_percent": round(error_rate, 2),
            "total_requests": total_requests,
            "request_sample_size": len(_request_times)
        },
        "database": pool_metrics,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(disk_root).percent,
            "process_count": len(psutil.pids())
        }
    }
