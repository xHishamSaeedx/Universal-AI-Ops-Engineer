import asyncio
import time
import uuid
from typing import Any, Optional

import httpx
import psycopg2
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.core.config import settings

router = APIRouter()

# In-memory attack registry
_attacks: dict[str, dict[str, Any]] = {}

# SQL constants
DELETE_ALEMBIC_VERSION_SQL = "DELETE FROM alembic_version;"


def _get_db_connection(database_url: str):
    """Create a database connection to the target server's database."""
    try:
        # Parse the database URL
        # Format: postgresql://user:password@host:port/database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to target database: {str(e)}"
        )


def _get_current_alembic_version(conn) -> Optional[str]:
    """Get the current Alembic version from the database."""
    try:
        with conn.cursor() as cur:
            # Check if alembic_version table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                return None
            
            # Get current version
            cur.execute("SELECT version_num FROM alembic_version LIMIT 1;")
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Alembic version: {str(e)}"
        )


def _set_alembic_version(conn, version: str) -> None:
    """Set the Alembic version in the database."""
    try:
        with conn.cursor() as cur:
            # Check if table exists, create if not
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                # Create the table if it doesn't exist
                cur.execute("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """)
            
            # Delete existing version and insert new one
            cur.execute(DELETE_ALEMBIC_VERSION_SQL)
            cur.execute("INSERT INTO alembic_version (version_num) VALUES (%s);", (version,))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set Alembic version: {str(e)}"
        )


async def _get_head_version_from_target(target_api_base_url: str) -> Optional[str]:
    """Get the head (latest) migration version from target server."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{target_api_base_url.rstrip('/')}/api/v1/migrations/status"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("head_version")
    except Exception:
        # If we can't get it from API, return None and we'll use a fallback
        return None


async def _run_attack(
    attack_id: str,
    target_database_url: str,
    failure_type: str,
    duration_seconds: Optional[int],
    target_api_base_url: Optional[str] = None
) -> None:
    """Run the migration failure attack."""
    _attacks[attack_id]["state"] = "running"
    _attacks[attack_id]["started_at"] = time.time()
    
    try:
        # Connect to database
        conn = _get_db_connection(target_database_url)
        
        try:
            # Get current version (for rollback)
            original_version = _get_current_alembic_version(conn)
            _attacks[attack_id]["original_version"] = original_version
            
            # Corrupt the version based on failure type
            if failure_type == "invalid_version":
                # Set to a clearly invalid version that doesn't exist
                corrupted_version = "999_invalid_chaos_migration"
            elif failure_type == "missing_version":
                # Delete the version entirely
                with conn.cursor() as cur:
                    cur.execute(DELETE_ALEMBIC_VERSION_SQL)
                corrupted_version = None
            elif failure_type == "future_version":
                # Set to a future version that doesn't exist yet
                corrupted_version = "999_future_chaos_migration"
            elif failure_type == "db_behind_code":
                # Set to an older version so DB is behind the code
                # Try to get head version from target server, then set to an older version
                head_version = None
                if target_api_base_url:
                    head_version = await _get_head_version_from_target(target_api_base_url)
                
                # If we got head version and it's not "001", use "001" (initial migration)
                # Otherwise, if head is "001", we can't go back further, so use a known older pattern
                if head_version and head_version != "001":
                    # Set to the initial migration which is guaranteed to be older
                    corrupted_version = "001"
                elif head_version == "001":
                    # Can't go back from initial, so this scenario doesn't apply
                    # Set to None to indicate this can't be done
                    corrupted_version = None
                    _attacks[attack_id]["error"] = "Cannot set DB behind code: head is already at initial migration (001)"
                else:
                    # Fallback: use "001" as it's typically the initial migration
                    corrupted_version = "001"
            else:
                # Default to invalid_version
                corrupted_version = "999_invalid_chaos_migration"
            
            if corrupted_version:
                _set_alembic_version(conn, corrupted_version)
                _attacks[attack_id]["corrupted_version"] = corrupted_version
            else:
                _attacks[attack_id]["corrupted_version"] = None
            
            _attacks[attack_id]["failure_type"] = failure_type
            _attacks[attack_id]["corrupted_at"] = time.time()
            
            # If duration is specified, schedule auto-rollback
            if duration_seconds and duration_seconds > 0:
                await asyncio.sleep(duration_seconds)
                # Auto-rollback
                await _rollback_attack(attack_id, target_database_url)
            else:
                # No auto-rollback, keep it corrupted
                _attacks[attack_id]["state"] = "completed"
                _attacks[attack_id]["finished_at"] = time.time()
        
        finally:
            conn.close()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()


async def _rollback_attack(attack_id: str, target_database_url: str) -> None:
    """Rollback the migration failure attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        return
    
    try:
        conn = _get_db_connection(target_database_url)
        
        try:
            original_version = attack.get("original_version")
            
            if original_version is None:
                # If there was no original version, delete the table entry
                with conn.cursor() as cur:
                    cur.execute(DELETE_ALEMBIC_VERSION_SQL)
            else:
                # Restore the original version
                _set_alembic_version(conn, original_version)
            
            # Verify the rollback worked
            restored_version = _get_current_alembic_version(conn)
            if restored_version != original_version:
                raise ValueError(
                    f"Rollback verification failed: expected {original_version}, got {restored_version}"
                )
            
            _attacks[attack_id]["state"] = "rolled_back"
            _attacks[attack_id]["rolled_back_at"] = time.time()
            _attacks[attack_id]["finished_at"] = time.time()
            _attacks[attack_id]["restored_version"] = restored_version
        
        finally:
            conn.close()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "rollback_failed"
        _attacks[attack_id]["rollback_error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()
        # Re-raise so the caller knows it failed
        raise


@router.post("/break/migrations")
async def break_migrations(
    target_database_url: str = Query(
        default=settings.target_database_url,
        description="Target server database URL"
    ),
    failure_type: str = Query(
        default="invalid_version",
        regex="^(invalid_version|missing_version|future_version|db_behind_code)$",
        description="Type of migration failure to inject"
    ),
    duration_seconds: Optional[int] = Query(
        default=None,
        ge=1,
        le=3600,
        description="Auto-rollback after this many seconds (None = manual rollback required)"
    ),
    target_api_base_url: Optional[str] = Query(
        default=None,
        description="Target server API base URL (optional, defaults to settings.target_api_base_url)"
    ),
):
    """
    Corrupt the Alembic version table in the target server's database to simulate
    failed migrations. This will cause Alembic to detect version mismatches.
    
    Failure types:
    - invalid_version: Set version to a clearly invalid revision ID
    - missing_version: Delete the version record entirely
    - future_version: Set version to a future revision that doesn't exist
    - db_behind_code: Set DB to an older version so migration head > DB version
    """
    attack_id = str(uuid.uuid4())
    # Use provided target_api_base_url or fallback to settings default
    effective_api_url = target_api_base_url or settings.target_api_base_url
    
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_database_url": target_database_url,
        "target_api_base_url": effective_api_url,
        "failure_type": failure_type,
        "duration_seconds": duration_seconds,
        "created_at": time.time(),
    }
    
    asyncio.create_task(_run_attack(attack_id, target_database_url, failure_type, duration_seconds, effective_api_url))
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/migrations/{attack_id}")
async def break_migrations_status(attack_id: str):
    """Get the status of a migration failure attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    # Don't expose sensitive database URLs in response
    response = {k: v for k, v in attack.items() if k != "target_database_url"}
    return response


@router.post("/break/migrations/{attack_id}/stop")
async def break_migrations_stop(attack_id: str):
    """Stop and rollback a migration failure attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    if attack["state"] == "rolled_back":
        # Already rolled back
        return {"status": "already_rolled_back", "attack_id": attack_id}
    
    if attack["state"] in ["failed", "rollback_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot rollback attack in state: {attack['state']}. Error: {attack.get('rollback_error', 'Unknown error')}"
        )
    
    # Get the database URL (use stored one or fallback to settings)
    target_database_url = attack.get("target_database_url")
    if not target_database_url:
        target_database_url = settings.target_database_url
    
    try:
        # Rollback the attack
        await _rollback_attack(attack_id, target_database_url)
        
        # Check final state
        attack = _attacks.get(attack_id)
        if attack and attack["state"] == "rolled_back":
            return {
                "status": "rolled_back",
                "attack_id": attack_id,
                "restored_version": attack.get("restored_version")
            }
        else:
            return {
                "status": "rollback_failed",
                "attack_id": attack_id,
                "error": attack.get("rollback_error", "Unknown error") if attack else "Attack not found"
            }
    except Exception as e:
        # If rollback failed, return error details
        attack = _attacks.get(attack_id)
        error_msg = str(e)
        if attack and attack.get("rollback_error"):
            error_msg = attack["rollback_error"]
        
        raise HTTPException(
            status_code=500,
            detail=f"Rollback failed: {error_msg}"
        )
