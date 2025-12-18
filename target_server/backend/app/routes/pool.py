import logging

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import TimeoutError as SATimeoutError

from ..core.database import get_engine, get_pool_metrics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pool/status")
def pool_status():
    """Expose connection pool status/metrics for debugging."""
    return {"pool": get_pool_metrics()}


@router.post("/pool/hold")
def hold_db_connection(
    seconds: int = Query(30, ge=1, le=600, description="How long to hold the DB connection"),
):
    """
    Hold a DB connection open to simulate pool starvation.

    Uses Postgres' pg_sleep() to keep the connection checked out/busy.
    With small pool_size/max_overflow=0/pool_timeout, concurrent calls
    will trigger QueuePool timeout errors.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT pg_sleep(:seconds)"), {"seconds": seconds})
        return {"status": "released", "held_seconds": seconds}
    except SATimeoutError as e:
        # Log the full error but don't expose details to clients
        logger.error("DB_ERROR: %s", str(e))
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error("DB_ERROR: %s", str(e))
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

