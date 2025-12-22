from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.database import get_db, get_pool_metrics, get_engine
import psutil
import time
from pathlib import Path
from collections import deque
from datetime import datetime, timezone
from alembic import command
from alembic.config import Config
import os

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


def _ensure_items_table(db, engine):
    """Ensure items table exists, create if it doesn't."""
    from ..core.database import Base
    try:
        db.execute(text("SELECT COUNT(*) FROM items"))
    except Exception as table_error:
        if "does not exist" in str(table_error).lower() or "undefinedtable" in str(table_error).lower():
            Base.metadata.create_all(bind=engine)


@router.get("/test/items")
async def test_items_query():
    """
    Test endpoint that queries the items table.
    Useful for testing table_lock type - ACCESS EXCLUSIVE locks block all operations.
    """
    try:
        from ..core.database import get_session_local, get_engine
        session_local_cls = get_session_local()
        engine = get_engine()
        db = session_local_cls()
        try:
            _ensure_items_table(db, engine)
            
            # Query the items table - this will be blocked by ACCESS EXCLUSIVE lock
            result = db.execute(text("SELECT COUNT(*) as count FROM items"))
            row = result.fetchone()
            count = row[0] if row else 0
            
            result = db.execute(text("SELECT id, name FROM items LIMIT 10"))
            items = [{"id": r[0], "name": r[1]} for r in result.fetchall()]
            
            return {
                "status": "success",
                "count": count,
                "items": items,
                "message": "Successfully queried items table",
                "lock_type_tested": "table_lock"
            }
        finally:
            db.close()
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str or "pool" in error_str:
            return {
                "status": "timeout",
                "error": "Database connection timeout",
                "details": "This may indicate connection pool exhaustion or a lock"
            }
        elif "lock" in error_str or "waiting" in error_str or "blocked" in error_str:
            return {
                "status": "blocked",
                "error": "Query blocked by lock (likely long-running transaction)",
                "details": "This query is waiting for a lock on the items table"
            }
        else:
            return {
                "status": "error",
                "error": str(e),
                "hint": "If table doesn't exist, run: alembic upgrade head"
            }


@router.get("/test/items/update")
async def test_items_update():
    """
    Test endpoint that updates rows in the items table.
    Useful for testing row_lock type - SELECT FOR UPDATE blocks updates to locked rows.
    """
    try:
        from ..core.database import get_session_local, get_engine
        session_local_cls = get_session_local()
        engine = get_engine()
        db = session_local_cls()
        try:
            _ensure_items_table(db, engine)
            
            # First, ensure we have at least one row to update
            result = db.execute(text("SELECT COUNT(*) FROM items"))
            count = result.fetchone()[0]
            
            if count == 0:
                # Insert a test row
                db.execute(text("INSERT INTO items (name, description) VALUES ('test', 'test item')"))
                db.commit()
            
            # Try to update a row - this will be blocked if rows are locked with SELECT FOR UPDATE
            result = db.execute(
                text("UPDATE items SET description = 'updated' WHERE id = (SELECT id FROM items LIMIT 1)")
            )
            db.commit()
            
            return {
                "status": "success",
                "rows_updated": result.rowcount,
                "message": "Successfully updated items table",
                "lock_type_tested": "row_lock"
            }
        finally:
            db.close()
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str or "pool" in error_str:
            return {
                "status": "timeout",
                "error": "Database connection timeout",
                "details": "This may indicate connection pool exhaustion or a lock"
            }
        elif "lock" in error_str or "waiting" in error_str or "blocked" in error_str:
            return {
                "status": "blocked",
                "error": "Update blocked by row lock (SELECT FOR UPDATE)",
                "details": "This update is waiting for row locks to be released"
            }
        else:
            return {
                "status": "error",
                "error": str(e)
            }


@router.get("/test/advisory-lock")
async def test_advisory_lock(lock_id: int = 12345):
    """
    Test endpoint that attempts to acquire an advisory lock.
    Useful for testing advisory_lock type - pg_advisory_lock blocks other advisory lock attempts.
    """
    try:
        from ..core.database import get_session_local
        session_local_cls = get_session_local()
        db = session_local_cls()
        try:
            # Try to acquire advisory lock - this will be blocked if another session holds it
            result = db.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id})
            acquired = result.fetchone()[0]
            
            if acquired:
                # Release it immediately
                db.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
                db.commit()
                return {
                    "status": "success",
                    "lock_acquired": True,
                    "message": "Successfully acquired and released advisory lock",
                    "lock_type_tested": "advisory_lock",
                    "lock_id": lock_id
                }
            else:
                return {
                    "status": "blocked",
                    "lock_acquired": False,
                    "message": "Advisory lock is held by another session",
                    "lock_type_tested": "advisory_lock",
                    "lock_id": lock_id
                }
        finally:
            db.close()
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str or "pool" in error_str:
            return {
                "status": "timeout",
                "error": "Database connection timeout",
                "details": "This may indicate connection pool exhaustion"
            }
        else:
            return {
                "status": "error",
                "error": str(e)
            }



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


def _get_alembic_config():
    """Get Alembic configuration."""
    # Get the backend directory (parent of app)
    backend_dir = Path(__file__).parent.parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    
    cfg = Config(str(alembic_ini_path))
    # Set the database URL from settings
    from ..core.config import settings
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    
    return cfg


@router.get("/migrations/status")
async def migration_status():
    """
    Check the status of database migrations.
    Returns current version, head version, and whether they match.
    This endpoint helps detect migration failures and version mismatches.
    """
    try:
        from ..core.config import settings
        from sqlalchemy import inspect as sqlalchemy_inspect
        
        engine = get_engine()
        cfg = _get_alembic_config()
        
        # Get current version from database
        current_version = None
        version_table_exists = False
        
        try:
            with engine.connect() as conn:
                # Check if alembic_version table exists
                inspector = sqlalchemy_inspect(engine)
                tables = inspector.get_table_names()
                version_table_exists = "alembic_version" in tables
                
                if version_table_exists:
                    result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                    row = result.fetchone()
                    current_version = row[0] if row else None
        except Exception as e:
            return {
                "status": "error",
                "error": "Failed to read current migration version",
                "details": str(e),
                "current_version": None,
                "head_version": None,
                "is_up_to_date": False,
                "version_table_exists": version_table_exists
            }
        
        # Get head version (latest migration in codebase)
        head_version = None
        try:
            # Use Alembic's script directory to find head
            from alembic.script import ScriptDirectory
            script = ScriptDirectory.from_config(cfg)
            head_revision = script.get_current_head()
            head_version = head_revision if head_revision else None
        except Exception as e:
            # If we can't determine head, that's also a problem
            return {
                "status": "error",
                "error": "Failed to determine head migration version",
                "details": str(e),
                "current_version": current_version,
                "head_version": None,
                "is_up_to_date": False,
                "version_table_exists": version_table_exists
            }
        
        # Check if versions match
        is_up_to_date = current_version == head_version
        
        # Determine status
        if not version_table_exists:
            status = "no_migrations"
            error = "Alembic version table does not exist"
        elif current_version is None:
            status = "missing_version"
            error = "No version recorded in database"
        elif current_version != head_version:
            status = "version_mismatch"
            error = f"Current version ({current_version}) does not match head version ({head_version})"
        else:
            status = "up_to_date"
            error = None
        
        return {
            "status": status,
            "error": error,
            "current_version": current_version,
            "head_version": head_version,
            "is_up_to_date": is_up_to_date,
            "version_table_exists": version_table_exists,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": "Failed to check migration status",
            "details": str(e),
            "current_version": None,
            "head_version": None,
            "is_up_to_date": False,
            "version_table_exists": False
        }
