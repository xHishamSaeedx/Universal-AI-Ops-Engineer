import asyncio
import subprocess
import time
import uuid
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()

# In-memory attack registry
_attacks: dict[str, dict[str, Any]] = {}


def _get_container_name() -> str:
    """Get the target server API container name."""
    # Default from docker-compose.yml: target_server_api
    return "target_server_api"


async def _check_container_running(container_name: str) -> bool:
    """Check if container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return container_name in result.stdout
    except Exception:
        return False


async def _stop_container(container_name: str) -> dict[str, Any]:
    """Stop the target server API container."""
    try:
        result = subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            text=True,
            check=True
        )
        return {"success": True, "message": f"Container {container_name} stopped", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "stderr": e.stderr}


async def _start_container(container_name: str) -> dict[str, Any]:
    """Start the target server API container."""
    try:
        result = subprocess.run(
            ["docker", "start", container_name],
            capture_output=True,
            text=True,
            check=True
        )
        return {"success": True, "message": f"Container {container_name} started", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "stderr": e.stderr}


async def _restart_container(container_name: str) -> dict[str, Any]:
    """Restart the target server API container."""
    try:
        result = subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True,
            text=True,
            check=True
        )
        return {"success": True, "message": f"Container {container_name} restarted", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e), "stderr": e.stderr}


async def _verify_api_down(target_base_url: str) -> bool:
    """Verify that the API is actually down."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
            response = await client.get(f"{target_base_url.rstrip('/')}/healthz")
            return False  # API is up
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
        return True  # API is down
    except Exception:
        return True  # Assume down on any error


async def _verify_api_up(target_base_url: str, max_retries: int = 10, delay: float = 1.0) -> bool:
    """Verify that the API is back up."""
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
                response = await client.get(f"{target_base_url.rstrip('/')}/healthz")
                if response.status_code == 200:
                    return True
        except Exception:
            pass
        await asyncio.sleep(delay)
    return False


async def _run_attack(
    attack_id: str,
    target_base_url: str,
    crash_type: str,
    duration_seconds: Optional[int],
    container_name: str
) -> None:
    """Run the API crash attack."""
    _attacks[attack_id]["state"] = "running"
    _attacks[attack_id]["started_at"] = time.time()
    
    try:
        # Check if container exists and is running
        is_running = await _check_container_running(container_name)
        if not is_running:
            _attacks[attack_id]["state"] = "failed"
            _attacks[attack_id]["error"] = f"Container {container_name} is not running"
            _attacks[attack_id]["finished_at"] = time.time()
            return
        
        _attacks[attack_id]["container_was_running"] = True
        
        # Perform the crash based on type
        if crash_type == "stop":
            result = await _stop_container(container_name)
            _attacks[attack_id]["stop_result"] = result
            if not result["success"]:
                _attacks[attack_id]["state"] = "failed"
                _attacks[attack_id]["error"] = result.get("error", "Failed to stop container")
                _attacks[attack_id]["finished_at"] = time.time()
                return
            
            # Verify API is down
            await asyncio.sleep(2)  # Give Docker time to stop
            is_down = await _verify_api_down(target_base_url)
            _attacks[attack_id]["api_verified_down"] = is_down
            
            # If auto-recovery is enabled, wait and restart
            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                restart_result = await _start_container(container_name)
                _attacks[attack_id]["restart_result"] = restart_result
                
                if restart_result["success"]:
                    # Wait for container to be healthy
                    await asyncio.sleep(3)
                    is_up = await _verify_api_up(target_base_url)
                    _attacks[attack_id]["api_verified_up"] = is_up
                    _attacks[attack_id]["state"] = "completed" if is_up else "partially_recovered"
                else:
                    _attacks[attack_id]["state"] = "failed_to_recover"
                    _attacks[attack_id]["error"] = restart_result.get("error", "Failed to restart container")
            else:
                _attacks[attack_id]["state"] = "crashed"  # Manual recovery required
        
        elif crash_type == "restart":
            result = await _restart_container(container_name)
            _attacks[attack_id]["restart_result"] = result
            if not result["success"]:
                _attacks[attack_id]["state"] = "failed"
                _attacks[attack_id]["error"] = result.get("error", "Failed to restart container")
                _attacks[attack_id]["finished_at"] = time.time()
                return
            
            # Verify API comes back up
            await asyncio.sleep(5)  # Give container time to restart
            is_up = await _verify_api_up(target_base_url)
            _attacks[attack_id]["api_verified_up"] = is_up
            _attacks[attack_id]["state"] = "completed" if is_up else "partially_recovered"
        
        _attacks[attack_id]["finished_at"] = time.time()
        
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()


@router.post("/break/api_crash")
async def break_api_crash(
    target_base_url: str = Query(
        default=settings.target_api_base_url,
        description="Target server API base URL"
    ),
    crash_type: str = Query(
        default="stop",
        regex="^(stop|restart)$",
        description="Type of crash: 'stop' (stops container, requires manual/auto recovery) or 'restart' (restarts container)"
    ),
    duration_seconds: Optional[int] = Query(
        default=None,
        ge=1,
        le=3600,
        description="Auto-recovery: restart container after N seconds (only for 'stop' type, None = manual recovery required)"
    ),
    container_name: Optional[str] = Query(
        default=None,
        description="Docker container name (defaults to 'target_server_api')"
    ),
):
    """
    Crash the target server API by stopping or restarting its Docker container.
    
    Crash types:
    - stop: Stops the container (API goes down). If duration_seconds is set, auto-restarts after that time.
    - restart: Immediately restarts the container (brief downtime, then recovery).
    
    This simulates:
    - Container crashes (OOM kills, system failures)
    - Service restarts
    - Deployment issues
    """
    attack_id = str(uuid.uuid4())
    effective_container_name = container_name or _get_container_name()
    
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_base_url": target_base_url,
        "crash_type": crash_type,
        "duration_seconds": duration_seconds,
        "container_name": effective_container_name,
        "created_at": time.time(),
    }
    
    asyncio.create_task(_run_attack(attack_id, target_base_url, crash_type, duration_seconds, effective_container_name))
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/api_crash/{attack_id}")
async def break_api_crash_status(attack_id: str):
    """Get the status of an API crash attack."""
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


@router.post("/break/api_crash/{attack_id}/stop")
async def break_api_crash_stop(attack_id: str):
    """Stop the attack and attempt recovery (restart container if it was stopped)."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    if attack["state"] in ["completed", "crashed", "failed", "partially_recovered"]:
        return {
            "status": f"already_{attack['state']}",
            "attack_id": attack_id,
            "state": attack["state"]
        }
    
    # If container was stopped, try to restart it
    container_name = attack.get("container_name", _get_container_name())
    
    if attack.get("crash_type") == "stop" and attack.get("container_was_running"):
        # Check if container is currently stopped
        is_running = await _check_container_running(container_name)
        if not is_running:
            restart_result = await _start_container(container_name)
            attack["manual_restart_result"] = restart_result
            if restart_result["success"]:
                attack["state"] = "recovered"
            else:
                attack["state"] = "recovery_failed"
                attack["error"] = restart_result.get("error", "Failed to restart container")
        else:
            attack["state"] = "already_running"
    else:
        attack["state"] = "cancelled"
    
    attack["finished_at"] = time.time()
    return {"status": "stopped", "attack_id": attack_id, "state": attack["state"]}

