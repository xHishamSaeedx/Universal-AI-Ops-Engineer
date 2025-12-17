import asyncio
import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()

# In-memory attack registry (good enough for now; no agent/action yet)
_attacks: dict[str, dict[str, Any]] = {}


async def _hold_one(client: httpx.AsyncClient, target_base_url: str, seconds: int) -> dict[str, Any]:
    url = f"{target_base_url.rstrip('/')}/api/v1/pool/hold"
    resp = await client.post(url, params={"seconds": seconds})
    return {
        "status_code": resp.status_code,
        "body": resp.json()
        if resp.headers.get("content-type", "").startswith("application/json")
        else resp.text,
    }


async def _run_attack(attack_id: str, target_base_url: str, connections: int, hold_seconds: int) -> None:
    _attacks[attack_id]["state"] = "running"
    _attacks[attack_id]["started_at"] = time.time()

    results: list[dict[str, Any]] = []

    async def _wrapped(i: int):
        try:
            r = await _hold_one(client, target_base_url, hold_seconds)
            results.append({"i": i, **r})
        except Exception as e:
            results.append({"i": i, "error": str(e)})

    timeout = httpx.Timeout(
        timeout=hold_seconds + 15.0,  # Default timeout for all operations
        connect=5.0  # Specific connect timeout
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [asyncio.create_task(_wrapped(i)) for i in range(connections)]
        _attacks[attack_id]["tasks"] = tasks
        try:
            await asyncio.gather(*tasks)
            _attacks[attack_id]["state"] = "completed"
            _attacks[attack_id]["results"] = results
            _attacks[attack_id]["finished_at"] = time.time()
        except asyncio.CancelledError:
            _attacks[attack_id]["state"] = "cancelled"
            _attacks[attack_id]["finished_at"] = time.time()
            raise


@router.post("/break/db_pool")
async def break_db_pool(
    target_base_url: str = Query(default=settings.target_api_base_url),
    connections: int = Query(20, ge=1, le=500, description="How many concurrent holds to start"),
    hold_seconds: int = Query(60, ge=1, le=600, description="How long each hold lasts"),
):
    """
    Exhaust the target server's SQLAlchemy connection pool by triggering many
    concurrent /pool/hold calls that keep DB connections checked out.
    """
    attack_id = str(uuid.uuid4())
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_base_url": target_base_url,
        "connections": connections,
        "hold_seconds": hold_seconds,
        "created_at": time.time(),
        "tasks": [],
    }

    asyncio.create_task(_run_attack(attack_id, target_base_url, connections, hold_seconds))
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/db_pool/{attack_id}")
async def break_db_pool_status(attack_id: str):
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    # don't dump tasks (not JSON serializable)
    return {k: v for k, v in attack.items() if k != "tasks"}


@router.post("/break/db_pool/{attack_id}/stop")
async def break_db_pool_stop(attack_id: str):
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    tasks = attack.get("tasks") or []
    for t in tasks:
        try:
            t.cancel()
        except Exception:
            pass
    attack["state"] = "cancelling"
    return {"status": "cancelling", "attack_id": attack_id}

