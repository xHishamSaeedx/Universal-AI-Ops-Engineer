from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

# Create Base class for models
Base = declarative_base()

# Global variables for lazy initialization
_engine = None
_SessionLocal = None

logger = logging.getLogger(__name__)

def get_engine():
    """Get database engine with lazy initialization"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            echo=settings.debug
        )
    return _engine

def get_session_local():
    """Get SessionLocal class with lazy initialization"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_db():
    """Dependency to get database session"""
    session_local_cls = get_session_local()
    db = session_local_cls()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log the error but don't crash the app startup
        logger.warning("Could not create database tables: %s", e)
        logger.warning("Database tables will be created when the database is available.")


def _calculate_pool_health(utilization: float) -> tuple[str, str]:
    """Calculate pool health and utilization status based on percentage."""
    if utilization >= 90:
        return "critical", "high"
    elif utilization >= 70:
        return "degraded", "elevated"
    elif utilization >= 50:
        return "healthy", "moderate"
    else:
        return "healthy", "low"


def get_pool_metrics() -> dict:
    """
    Best-effort pool metrics for observability/debugging.
    Returns sanitized metrics that indicate health without revealing exact state.
    """
    engine = get_engine()
    pool = getattr(engine, "pool", None)
    if pool is None:
        return {"pool_health": "unknown"}

    checkedout_fn = getattr(pool, "checkedout", None)
    pool_size = getattr(pool, "size", lambda: settings.db_pool_size)()
    
    metrics: dict = {
        "pool_type": pool.__class__.__name__,
        "pool_size": pool_size,
    }

    # Provide health indicators instead of exact counts
    if callable(checkedout_fn):
        try:
            checked_out = checkedout_fn()
            utilization = (checked_out / pool_size * 100) if pool_size > 0 else 0
            health, utilization_level = _calculate_pool_health(utilization)
            metrics["pool_health"] = health
            metrics["pool_utilization"] = utilization_level
        except Exception:
            metrics["pool_health"] = "unknown"
            metrics["pool_utilization"] = "unknown"
    else:
        metrics["pool_health"] = "unknown"
        metrics["pool_utilization"] = "unknown"

    return metrics