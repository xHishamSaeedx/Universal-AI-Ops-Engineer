import asyncio
import threading
import time
import uuid
from typing import Any, Optional

import psycopg2
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED

from app.core.config import settings

router = APIRouter()

# In-memory attack registry
_attacks: dict[str, dict[str, Any]] = {}

# Thread-safe connection storage for long-running transactions
_connections: dict[str, tuple[psycopg2.extensions.connection, threading.Thread]] = {}

# SQL constants
SQL_BEGIN = "BEGIN;"
SQL_ROLLBACK = "ROLLBACK;"
SQL_COMMIT = "COMMIT;"


def _get_db_connection(database_url: str):
    """Create a database connection to the target server's database."""
    try:
        conn = psycopg2.connect(database_url)
        # Don't use AUTOCOMMIT - we need explicit transactions
        conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to target database: {str(e)}"
        )


def _get_backend_pid(conn) -> Optional[int]:
    """Get the PostgreSQL backend process ID for this connection."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_backend_pid();")
            result = cur.fetchone()
            return result[0] if result else None
    except Exception:
        return None


def _kill_backend_pid(database_url: str, pid: int) -> bool:
    """Terminate a PostgreSQL backend process by PID."""
    try:
        kill_conn = _get_db_connection(database_url)
        try:
            with kill_conn.cursor() as cur:
                cur.execute("SELECT pg_terminate_backend(%s);", (pid,))
                result = cur.fetchone()
                return result[0] if result else False
        finally:
            kill_conn.close()
    except Exception:
        return False


def _get_blocked_queries(database_url: str, blocking_pid: int) -> list[dict[str, Any]]:
    """Get queries blocked by the specified backend PID."""
    try:
        conn = _get_db_connection(database_url)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        blocked_locks.pid AS blocked_pid,
                        blocked_activity.usename AS blocked_user,
                        blocked_activity.query AS blocked_query,
                        blocked_activity.state AS blocked_state,
                        blocking_activity.query AS blocking_query
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_stat_activity blocked_activity 
                        ON blocked_activity.pid = blocked_locks.pid
                    JOIN pg_catalog.pg_locks blocking_locks 
                        ON blocking_locks.locktype = blocked_locks.locktype
                        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                        AND blocking_locks.pid != blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocking_activity 
                        ON blocking_activity.pid = blocking_locks.pid
                    WHERE NOT blocked_locks.granted
                        AND blocking_activity.pid = %s;
                """, (blocking_pid,))
                rows = cur.fetchall()
                return [
                    {
                        "blocked_pid": row[0],
                        "blocked_user": row[1],
                        "blocked_query": row[2],
                        "blocked_state": row[3],
                        "blocking_query": row[4],
                    }
                    for row in rows
                ]
        finally:
            conn.close()
    except Exception:
        return []


def _run_table_lock_attack(
    attack_id: str,
    database_url: str,
    table_name: str,
    duration_seconds: Optional[int],
    event: threading.Event
):
    """Run a table lock attack in a background thread."""
    conn = None
    try:
        conn = _get_db_connection(database_url)
        pid = _get_backend_pid(conn)
        
        _attacks[attack_id]["backend_pid"] = pid
        _attacks[attack_id]["state"] = "running"
        _attacks[attack_id]["started_at"] = time.time()
        
        with conn.cursor() as cur:
            # Begin transaction
            cur.execute(SQL_BEGIN)
            
            # Acquire ACCESS EXCLUSIVE lock (blocks all operations)
            cur.execute(f"LOCK TABLE {table_name} IN ACCESS EXCLUSIVE MODE;")
            
            _attacks[attack_id]["lock_acquired_at"] = time.time()
            _attacks[attack_id]["lock_type"] = "ACCESS EXCLUSIVE"
            _attacks[attack_id]["locked_table"] = table_name
            
            # Hold the lock until event is set or duration expires
            if duration_seconds:
                # Sleep in small increments to check event
                elapsed = 0
                while elapsed < duration_seconds and not event.is_set():
                    time.sleep(1)
                    elapsed += 1
                    
                    # Update blocked queries periodically
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            else:
                # Hold indefinitely until event is set
                while not event.is_set():
                    time.sleep(1)
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            
            # Release lock
            if not event.is_set():
                cur.execute(SQL_ROLLBACK)
                _attacks[attack_id]["state"] = "completed"
            else:
                cur.execute(SQL_ROLLBACK)
                _attacks[attack_id]["state"] = "rolled_back"
            
            _attacks[attack_id]["finished_at"] = time.time()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()
    
    finally:
        if conn and not conn.closed:
            try:
                conn.close()
            except Exception:
                pass


def _run_row_lock_attack(
    attack_id: str,
    database_url: str,
    table_name: str,
    lock_count: int,
    duration_seconds: Optional[int],
    event: threading.Event
):
    """Run a row lock attack (SELECT FOR UPDATE) in a background thread."""
    conn = None
    try:
        conn = _get_db_connection(database_url)
        pid = _get_backend_pid(conn)
        
        _attacks[attack_id]["backend_pid"] = pid
        _attacks[attack_id]["state"] = "running"
        _attacks[attack_id]["started_at"] = time.time()
        
        with conn.cursor() as cur:
            # Begin transaction
            cur.execute(SQL_BEGIN)
            
            # Acquire row-level locks
            cur.execute(f"SELECT id FROM {table_name} LIMIT %s FOR UPDATE;", (lock_count,))
            rows = cur.fetchall()
            
            _attacks[attack_id]["lock_acquired_at"] = time.time()
            _attacks[attack_id]["lock_type"] = "ROW (FOR UPDATE)"
            _attacks[attack_id]["locked_table"] = table_name
            _attacks[attack_id]["locked_rows"] = len(rows)
            
            # Hold the locks until event is set or duration expires
            if duration_seconds:
                elapsed = 0
                while elapsed < duration_seconds and not event.is_set():
                    time.sleep(1)
                    elapsed += 1
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            else:
                while not event.is_set():
                    time.sleep(1)
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            
            # Release locks
            if not event.is_set():
                cur.execute(SQL_ROLLBACK)
                _attacks[attack_id]["state"] = "completed"
            else:
                cur.execute(SQL_ROLLBACK)
                _attacks[attack_id]["state"] = "rolled_back"
            
            _attacks[attack_id]["finished_at"] = time.time()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()
    
    finally:
        if conn and not conn.closed:
            try:
                conn.close()
            except Exception:
                pass


def _run_advisory_lock_attack(
    attack_id: str,
    database_url: str,
    lock_id: int,
    duration_seconds: Optional[int],
    event: threading.Event
):
    """Run an advisory lock attack in a background thread."""
    conn = None
    try:
        conn = _get_db_connection(database_url)
        pid = _get_backend_pid(conn)
        
        _attacks[attack_id]["backend_pid"] = pid
        _attacks[attack_id]["state"] = "running"
        _attacks[attack_id]["started_at"] = time.time()
        
        with conn.cursor() as cur:
            # Begin transaction
            cur.execute(SQL_BEGIN)
            
            # Acquire advisory lock (session-level)
            cur.execute("SELECT pg_advisory_lock(%s);", (lock_id,))
            
            _attacks[attack_id]["lock_acquired_at"] = time.time()
            _attacks[attack_id]["lock_type"] = "ADVISORY"
            _attacks[attack_id]["lock_id"] = lock_id
            
            # Hold the lock until event is set or duration expires
            if duration_seconds:
                elapsed = 0
                while elapsed < duration_seconds and not event.is_set():
                    time.sleep(1)
                    elapsed += 1
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            else:
                while not event.is_set():
                    time.sleep(1)
                    if pid:
                        blocked = _get_blocked_queries(database_url, pid)
                        _attacks[attack_id]["blocked_queries"] = blocked
                        _attacks[attack_id]["blocked_count"] = len(blocked)
            
            # Release advisory lock
            cur.execute("SELECT pg_advisory_unlock(%s);", (lock_id,))
            
            if not event.is_set():
                cur.execute(SQL_COMMIT)
                _attacks[attack_id]["state"] = "completed"
            else:
                cur.execute(SQL_ROLLBACK)
                _attacks[attack_id]["state"] = "rolled_back"
            
            _attacks[attack_id]["finished_at"] = time.time()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()
    
    finally:
        if conn and not conn.closed:
            try:
                conn.close()
            except Exception:
                pass


@router.post("/break/long_transactions")
async def break_long_transactions(
    target_database_url: str = Query(
        default=settings.target_database_url,
        description="Target server database URL"
    ),
    lock_type: str = Query(
        default="table_lock",
        regex="^(table_lock|row_lock|advisory_lock)$",
        description="Type of lock to create"
    ),
    duration_seconds: Optional[int] = Query(
        default=None,
        ge=1,
        le=3600,
        description="Auto-rollback after this many seconds (None = manual rollback required)"
    ),
    target_table: Optional[str] = Query(
        default="items",
        description="Target table name (for table_lock and row_lock types)"
    ),
    lock_count: int = Query(
        default=10,
        ge=1,
        le=10000,
        description="Number of rows/advisory locks to acquire (for row_lock and advisory_lock)"
    ),
    advisory_lock_id: Optional[int] = Query(
        default=None,
        description="Advisory lock ID (for advisory_lock type, defaults to random)"
    ),
):
    """
    Create long-running database transactions that hold locks and block other queries.
    
    Lock types:
    - table_lock: ACCESS EXCLUSIVE lock on a table (blocks all operations)
    - row_lock: SELECT FOR UPDATE locks on multiple rows (blocks updates to those rows)
    - advisory_lock: pg_advisory_lock() session lock (blocks other advisory lock attempts)
    
    This will cause:
    - Query timeouts in the target server
    - Lock waits and deadlocks
    - Performance degradation
    
    Note: For connection pool exhaustion testing, use the /break/db_pool endpoint instead.
    """
    attack_id = str(uuid.uuid4())
    
    # Generate advisory lock ID if not provided
    if lock_type == "advisory_lock" and advisory_lock_id is None:
        advisory_lock_id = hash(f"chaos_{attack_id}") % (2**31)
    
    # Create event for stopping the attack
    stop_event = threading.Event()
    
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_database_url": target_database_url,
        "lock_type": lock_type,
        "duration_seconds": duration_seconds,
        "target_table": target_table if lock_type in ["table_lock", "row_lock"] else None,
        "lock_count": lock_count if lock_type in ["row_lock", "advisory_lock"] else None,
        "advisory_lock_id": advisory_lock_id if lock_type == "advisory_lock" else None,
        "stop_event": stop_event,
        "created_at": time.time(),
    }
    
    # Start attack in background thread based on lock type
    thread = None
    if lock_type == "table_lock":
        thread = threading.Thread(
            target=_run_table_lock_attack,
            args=(attack_id, target_database_url, target_table, duration_seconds, stop_event),
            daemon=True
        )
    elif lock_type == "row_lock":
        thread = threading.Thread(
            target=_run_row_lock_attack,
            args=(attack_id, target_database_url, target_table, lock_count, duration_seconds, stop_event),
            daemon=True
        )
    elif lock_type == "advisory_lock":
        thread = threading.Thread(
            target=_run_advisory_lock_attack,
            args=(attack_id, target_database_url, advisory_lock_id, duration_seconds, stop_event),
            daemon=True
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid lock_type: {lock_type}. Must be one of: table_lock, row_lock, advisory_lock"
        )
    
    if thread:
        thread.start()
        _connections[attack_id] = (None, thread)  # Connection is handled internally
    
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/long_transactions/{attack_id}")
async def break_long_transactions_status(attack_id: str):
    """Get the status of a long-running transaction attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    # Calculate elapsed time if running
    if attack.get("started_at") and attack["state"] in ["running", "starting"]:
        attack["elapsed_seconds"] = time.time() - attack["started_at"]
    
    # Don't expose sensitive database URLs in response
    response = {k: v for k, v in attack.items() if k not in ["target_database_url", "stop_event"]}
    return response


@router.post("/break/long_transactions/{attack_id}/stop")
async def break_long_transactions_stop(
    attack_id: str,
    force_kill: bool = Query(
        default=False,
        description="Force kill the backend process if normal rollback fails"
    )
):
    """Stop and rollback a long-running transaction attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    if attack["state"] in ["completed", "rolled_back", "failed"]:
        return {
            "status": f"already_{attack['state']}",
            "attack_id": attack_id,
            "state": attack["state"]
        }
    
    # Signal the thread to stop
    stop_event = attack.get("stop_event")
    if stop_event:
        stop_event.set()
    
    # Wait a bit for graceful shutdown
    await asyncio.sleep(2)
    
    # Check if it stopped gracefully
    attack = _attacks.get(attack_id)  # Refresh state
    if attack and attack["state"] not in ["rolled_back", "completed", "failed"]:
        # If still running, try force kill
        if force_kill:
            backend_pid = attack.get("backend_pid")
            if backend_pid:
                target_database_url = attack.get("target_database_url", settings.target_database_url)
                killed = _kill_backend_pid(target_database_url, backend_pid)
                if killed:
                    attack["state"] = "force_killed"
                    attack["finished_at"] = time.time()
                    attack["force_killed"] = True
                    return {
                        "status": "force_killed",
                        "attack_id": attack_id,
                        "backend_pid": backend_pid
                    }
    
    # Refresh state one more time
    attack = _attacks.get(attack_id)
    if attack:
        if attack["state"] == "rolled_back":
            return {
                "status": "rolled_back",
                "attack_id": attack_id,
                "elapsed_seconds": attack.get("finished_at", time.time()) - attack.get("started_at", time.time())
            }
        elif attack["state"] == "completed":
            return {
                "status": "completed",
                "attack_id": attack_id,
                "message": "Attack completed naturally (duration expired)"
            }
        else:
            return {
                "status": "stopping",
                "attack_id": attack_id,
                "message": "Stop signal sent, attack should rollback soon",
                "state": attack["state"]
            }
    
    return {"status": "unknown", "attack_id": attack_id}

