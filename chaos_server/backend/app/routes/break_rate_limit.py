import asyncio
import time
import uuid
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()

# In-memory attack registry
_attacks: dict[str, dict[str, Any]] = {}


async def _get_current_config(target_base_url: str) -> dict:
    """Get current rate limit configuration from target server."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get(f"{target_base_url.rstrip('/')}/api/v1/rate_limit/config")
            if response.status_code == 200:
                data = response.json()
                return data.get("config", {})
            return {}
    except Exception as e:
        raise Exception(f"Failed to get current config: {str(e)}")


async def _update_config(target_base_url: str, enabled: bool = None, max_requests: int = None, window_seconds: int = None) -> dict:
    """Update rate limit configuration on target server."""
    try:
        payload = {}
        if enabled is not None:
            payload["enabled"] = enabled
        if max_requests is not None:
            payload["max_requests"] = max_requests
        if window_seconds is not None:
            payload["window_seconds"] = window_seconds
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.post(
                f"{target_base_url.rstrip('/')}/api/v1/rate_limit/config",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("config", {})
            else:
                raise Exception(f"Failed to update config: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Failed to update config: {str(e)}")


async def _get_stats(target_base_url: str) -> dict:
    """Get rate limit statistics from target server."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get(f"{target_base_url.rstrip('/')}/api/v1/rate_limit/stats")
            if response.status_code == 200:
                data = response.json()
                return data.get("stats", {})
            return {}
    except Exception:
        return {}


async def _send_request(client: httpx.AsyncClient, url: str) -> dict:
    """Send a single request and return response info."""
    try:
        response = await client.get(url)
        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "rate_limited": response.status_code == 429,
            "headers": dict(response.headers),
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "rate_limited": False,
            "error": str(e),
        }


async def _flood_requests(
    target_base_url: str,
    endpoint: str,
    total_requests: int,
    requests_per_second: float
) -> dict:
    """Send requests at specified rate and track responses."""
    url = f"{target_base_url.rstrip('/')}{endpoint}"
    results = {
        "total_sent": 0,
        "successful": 0,
        "rate_limited": 0,
        "errors": 0,
        "responses": [],
    }
    
    delay_between_requests = 1.0 / requests_per_second if requests_per_second > 0 else 0
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        for i in range(total_requests):
            result = await _send_request(client, url)
            results["total_sent"] += 1
            
            if result.get("success"):
                results["successful"] += 1
            elif result.get("rate_limited"):
                results["rate_limited"] += 1
            else:
                results["errors"] += 1
            
            # Store first few and last few responses for debugging
            if i < 5 or i >= total_requests - 5:
                results["responses"].append({
                    "request": i + 1,
                    **result
                })
            
            # Rate limiting: wait before next request
            if i < total_requests - 1:  # Don't wait after last request
                await asyncio.sleep(delay_between_requests)
    
    return results


async def _run_attack(
    attack_id: str,
    target_base_url: str,
    max_requests: int,
    window_seconds: int,
    flood_requests: int,
    flood_rate: float,
    target_endpoint: str,
    duration_seconds: Optional[int],
) -> None:
    """Run the rate limit attack."""
    _attacks[attack_id]["state"] = "running"
    _attacks[attack_id]["started_at"] = time.time()
    
    try:
        # Step 1: Get and backup current config
        original_config = await _get_current_config(target_base_url)
        _attacks[attack_id]["original_config"] = original_config
        
        if not original_config:
            _attacks[attack_id]["state"] = "failed"
            _attacks[attack_id]["error"] = "Failed to get current rate limit configuration"
            _attacks[attack_id]["finished_at"] = time.time()
            return
        
        # Step 2: Set restrictive limits
        new_config = await _update_config(
            target_base_url,
            enabled=True,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
        _attacks[attack_id]["restrictive_config"] = new_config
        
        # Verify config was updated
        if new_config.get("max_requests") != max_requests:
            _attacks[attack_id]["state"] = "failed"
            _attacks[attack_id]["error"] = f"Failed to set restrictive limits. Expected {max_requests}, got {new_config.get('max_requests')}"
            _attacks[attack_id]["finished_at"] = time.time()
            return
        
        _attacks[attack_id]["config_updated"] = True
        
        # Step 3: Send request flood
        await asyncio.sleep(1)  # Brief pause after config update
        
        flood_results = await _flood_requests(
            target_base_url,
            target_endpoint,
            flood_requests,
            flood_rate,
        )
        _attacks[attack_id]["flood_results"] = flood_results
        
        # Step 4: Get stats from target server
        stats = await _get_stats(target_base_url)
        _attacks[attack_id]["target_stats"] = stats
        
        # Step 5: Verify 429s were generated
        expected_429s = max(0, flood_requests - max_requests)
        actual_429s = flood_results["rate_limited"]
        
        _attacks[attack_id]["verification"] = {
            "expected_429s": expected_429s,
            "actual_429s": actual_429s,
            "verified": actual_429s >= expected_429s * 0.8,  # Allow 20% tolerance
        }
        
        # Step 6: Auto-recovery if enabled
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
            
            # Restore original config
            restored_config = await _update_config(
                target_base_url,
                enabled=original_config.get("enabled", True),
                max_requests=original_config.get("max_requests", 100),
                window_seconds=original_config.get("window_seconds", 60),
            )
            _attacks[attack_id]["restored_config"] = restored_config
            
            # Verify recovery
            await asyncio.sleep(1)
            recovery_test = await _flood_requests(
                target_base_url,
                target_endpoint,
                max_requests + 5,  # Send a few more than the restored limit
                flood_rate,
            )
            _attacks[attack_id]["recovery_test"] = recovery_test
            
            # Check if recovery worked (should get 429s again with restored limit)
            if recovery_test["rate_limited"] > 0:
                _attacks[attack_id]["state"] = "completed"
                _attacks[attack_id]["recovery_verified"] = True
            else:
                _attacks[attack_id]["state"] = "partially_recovered"
                _attacks[attack_id]["recovery_verified"] = False
        else:
            _attacks[attack_id]["state"] = "completed"  # Manual recovery required
        
        _attacks[attack_id]["finished_at"] = time.time()
        
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()


@router.post("/break/rate_limit")
async def break_rate_limit(
    target_base_url: str = Query(
        default=settings.target_api_base_url,
        description="Target server API base URL"
    ),
    max_requests: int = Query(
        default=10,
        ge=1,
        le=1000,
        description="Restrictive rate limit (max requests per window)"
    ),
    window_seconds: int = Query(
        default=60,
        ge=1,
        le=3600,
        description="Time window in seconds"
    ),
    flood_requests: int = Query(
        default=30,
        ge=1,
        le=10000,
        description="Total number of requests to send"
    ),
    flood_rate: float = Query(
        default=5.0,
        ge=0.1,
        le=100.0,
        description="Requests per second to send"
    ),
    target_endpoint: str = Query(
        default="/api/v1/health",
        description="Endpoint to hit with requests"
    ),
    duration_seconds: Optional[int] = Query(
        default=None,
        ge=1,
        le=3600,
        description="Auto-recovery: restore original limits after N seconds (None = manual recovery)"
    ),
):
    """
    Break rate limits by setting restrictive limits and flooding with requests.
    
    This attack:
    1. Backs up current rate limit configuration
    2. Sets very restrictive limits (e.g., 10 requests per minute)
    3. Sends a flood of requests that exceed the limit
    4. Verifies 429 responses are generated (appear in target server logs)
    5. Optionally auto-recovers by restoring original limits
    
    This simulates misconfigured rate limits causing legitimate traffic to be blocked.
    """
    attack_id = str(uuid.uuid4())
    
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_base_url": target_base_url,
        "max_requests": max_requests,
        "window_seconds": window_seconds,
        "flood_requests": flood_requests,
        "flood_rate": flood_rate,
        "target_endpoint": target_endpoint,
        "duration_seconds": duration_seconds,
        "created_at": time.time(),
    }
    
    asyncio.create_task(_run_attack(
        attack_id,
        target_base_url,
        max_requests,
        window_seconds,
        flood_requests,
        flood_rate,
        target_endpoint,
        duration_seconds,
    ))
    
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/rate_limit/{attack_id}")
async def break_rate_limit_status(attack_id: str):
    """Get the status of a rate limit attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    # Calculate duration if attack is running
    duration = None
    if attack.get("started_at") and not attack.get("finished_at"):
        duration = time.time() - attack["started_at"]
    elif attack.get("started_at") and attack.get("finished_at"):
        duration = attack["finished_at"] - attack["started_at"]
    
    response = {
        k: v for k, v in attack.items()
        if k not in []  # No sensitive data to exclude
    }
    response["duration_seconds"] = duration
    return response


@router.post("/break/rate_limit/{attack_id}/stop")
async def break_rate_limit_stop(attack_id: str):
    """Stop the attack and restore original rate limit configuration."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    if attack["state"] in ["completed", "failed", "partially_recovered"]:
        return {
            "status": f"already_{attack['state']}",
            "attack_id": attack_id,
            "state": attack["state"]
        }
    
    target_base_url = attack.get("target_base_url", settings.target_api_base_url)
    original_config = attack.get("original_config")
    
    if not original_config:
        attack["state"] = "recovery_failed"
        attack["error"] = "No original config to restore"
        attack["finished_at"] = time.time()
        return {
            "status": "recovery_failed",
            "attack_id": attack_id,
            "error": "No original config to restore"
        }
    
    try:
        # Restore original config
        restored_config = await _update_config(
            target_base_url,
            enabled=original_config.get("enabled", True),
            max_requests=original_config.get("max_requests", 100),
            window_seconds=original_config.get("window_seconds", 60),
        )
        attack["manual_restored_config"] = restored_config
        attack["state"] = "recovered"
        attack["finished_at"] = time.time()
        
        return {
            "status": "recovered",
            "attack_id": attack_id,
            "restored_config": restored_config
        }
    except Exception as e:
        attack["state"] = "recovery_failed"
        attack["error"] = str(e)
        attack["finished_at"] = time.time()
        return {
            "status": "recovery_failed",
            "attack_id": attack_id,
            "error": str(e)
        }

