import asyncio
import time
import uuid
from pathlib import Path
from shutil import copy
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()
_attacks: dict[str, dict[str, Any]] = {}


def find_workspace_root() -> Path:
    """
    Find the workspace root by looking for a directory that contains both
    'chaos_server' and 'target_server' directories.
    """
    # Start from the current file's directory
    current = Path(__file__).resolve().parent
    
    # Go up until we find a directory that contains both chaos_server and target_server
    # Or until we hit a reasonable limit (e.g., 10 levels up)
    for _ in range(10):
        if (current / "chaos_server").exists() and (current / "target_server").exists():
            return current
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent
    
    # Fallback: return current working directory if we can't find workspace root
    return Path.cwd()


def modify_env_file(env_file_path: str, var_name: str, new_value: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """
    Modify an .env file by setting, changing, or removing a variable.
    
    Args:
        env_file_path: Path to the .env file
        var_name: Name of the environment variable
        new_value: New value to set (None = remove the variable)
    
    Returns:
        (backup_path, original_value) - path to backup file and original value if it existed
    """
    env_path = Path(env_file_path)
    
    # Backup original file
    backup_path = None
    original_value = None
    
    if env_path.exists():
        backup_path = str(env_path) + ".backup"
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Read current content
    lines = []
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # Find and update/remove the variable
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Handle both VAR=value and VAR = value formats, and ignore comments
        if not stripped.startswith('#') and (stripped.startswith(f"{var_name}=") or stripped.startswith(f"{var_name} =")):
            found = True
            if '=' in line:
                original_value = line.split('=', 1)[1].strip()
                # Remove quotes if present
                if original_value.startswith('"') and original_value.endswith('"'):
                    original_value = original_value[1:-1]
                elif original_value.startswith("'") and original_value.endswith("'"):
                    original_value = original_value[1:-1]
            # Don't add this line if we're removing it (new_value is None)
            if new_value is not None:
                new_lines.append(f"{var_name}={new_value}\n")
        else:
            new_lines.append(line)
    
    # If variable wasn't found, add it (unless we're removing it)
    if not found and new_value is not None:
        new_lines.append(f"{var_name}={new_value}\n")
    
    # Write modified content
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return backup_path, original_value


def restore_env_file(env_file_path: str, backup_path: Optional[str]) -> None:
    """Restore .env file from backup."""
    if backup_path and Path(backup_path).exists():
        copy(backup_path, env_file_path)


async def restart_container(compose_file: str, service: str = "api") -> dict:
    """
    Restart a Docker Compose service.
    
    Args:
        compose_file: Path to docker-compose.yml
        service: Name of the service to restart
    
    Returns:
        dict with success status and output
    """
    import sys
    import subprocess
    
    compose_file_path = Path(compose_file).resolve()
    compose_dir = compose_file_path.parent
    # Use absolute path for -f flag to avoid any path resolution issues
    compose_file_abs = str(compose_file_path)
    
    # Build command - use absolute path for compose file
    command = ["docker", "compose", "-f", compose_file_abs, "restart", service]
    
    # Use asyncio.to_thread for Windows compatibility (like action_server does)
    def run_command():
        try:
            result = subprocess.run(
                command,
                cwd=str(compose_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 60 seconds",
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e) or repr(e),
                "returncode": -1,
                "stdout": "",
                "stderr": str(e) or repr(e),
            }
    
    try:
        result = await asyncio.to_thread(run_command)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute command: {str(e)}",
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


async def _run_attack(
    attack_id: str,
    target_env_file: str,
    env_var_name: str,
    failure_type: str,
    wrong_value: Optional[str],
    compose_file: str,
    duration_seconds: Optional[int],
    target_api_base_url: str
) -> None:
    """Run the env var chaos attack."""
    _attacks[attack_id]["state"] = "running"
    _attacks[attack_id]["started_at"] = time.time()
    
    try:
        # Step 1: Backup and modify .env
        if failure_type == "missing":
            backup_path, original_value = modify_env_file(target_env_file, env_var_name, new_value=None)
            _attacks[attack_id]["action"] = f"Removed {env_var_name}"
        else:  # wrong
            wrong_val = wrong_value or "INVALID_VALUE_12345"
            backup_path, original_value = modify_env_file(target_env_file, env_var_name, new_value=wrong_val)
            _attacks[attack_id]["action"] = f"Set {env_var_name}={wrong_val}"
        
        _attacks[attack_id]["backup_path"] = backup_path
        _attacks[attack_id]["original_value"] = original_value
        
        # Step 2: Restart container to pick up changes
        restart_result = await restart_container(compose_file, service="api")
        if not restart_result.get("success"):
            # Collect all available error information
            error_parts = []
            if restart_result.get("error"):
                error_parts.append(restart_result.get("error"))
            if restart_result.get("stderr"):
                error_parts.append(f"stderr: {restart_result.get('stderr')}")
            if restart_result.get("stdout"):
                error_parts.append(f"stdout: {restart_result.get('stdout')}")
            if restart_result.get("returncode") is not None and restart_result.get("returncode") != 0:
                error_parts.append(f"returncode: {restart_result.get('returncode')}")
            
            error_msg = " | ".join(error_parts) if error_parts else "Unknown error (no error details available)"
            raise Exception(f"Failed to restart container: {error_msg}")
        
        _attacks[attack_id]["container_restarted"] = True
        _attacks[attack_id]["restart_output"] = restart_result.get("stdout", "")
        
        # Step 3: Wait a bit for container to start
        await asyncio.sleep(5)
        
        # Step 4: Verify the endpoint fails (optional check)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{target_api_base_url.rstrip('/')}/api/v1/test/env"
                resp = await client.get(url)
                _attacks[attack_id]["test_endpoint_status"] = resp.status_code
                try:
                    _attacks[attack_id]["test_endpoint_response"] = resp.json()
                except Exception:
                    _attacks[attack_id]["test_endpoint_response"] = resp.text[:200]
        except Exception as e:
            _attacks[attack_id]["test_endpoint_status"] = "error"
            _attacks[attack_id]["test_endpoint_error"] = str(e)
        
        # Step 5: Auto-rollback if duration specified
        if duration_seconds and duration_seconds > 0:
            await asyncio.sleep(duration_seconds)
            await _rollback_attack(attack_id, target_env_file, compose_file)
        else:
            _attacks[attack_id]["state"] = "completed"
            _attacks[attack_id]["finished_at"] = time.time()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "failed"
        _attacks[attack_id]["error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()


async def _rollback_attack(attack_id: str, target_env_file: str, compose_file: str) -> None:
    """Rollback env var changes."""
    attack = _attacks.get(attack_id)
    if not attack:
        return
    
    try:
        backup_path = attack.get("backup_path")
        if backup_path:
            restore_env_file(target_env_file, backup_path)
            restart_result = await restart_container(compose_file, service="api")
            if restart_result.get("success"):
                await asyncio.sleep(3)  # Wait for container to restart
            else:
                raise Exception(f"Failed to restart container during rollback: {restart_result.get('error', 'Unknown error')}")
        
        _attacks[attack_id]["state"] = "rolled_back"
        _attacks[attack_id]["rolled_back_at"] = time.time()
        _attacks[attack_id]["finished_at"] = time.time()
    
    except Exception as e:
        _attacks[attack_id]["state"] = "rollback_failed"
        _attacks[attack_id]["rollback_error"] = str(e)
        _attacks[attack_id]["finished_at"] = time.time()
        raise


@router.post("/break/env_vars")
async def break_env_vars(
    target_env_file: Optional[str] = Query(default=None, description="Path to target server .env file (defaults to settings.target_env_file)"),
    env_var_name: str = Query(default="EXTERNAL_API_KEY", description="Environment variable to break"),
    failure_type: str = Query(default="missing", regex="^(missing|wrong)$", description="Type of failure: 'missing' removes the var, 'wrong' sets an invalid value"),
    wrong_value: Optional[str] = Query(default=None, description="Wrong value to set (if failure_type=wrong, defaults to 'INVALID_VALUE_12345')"),
    compose_file: Optional[str] = Query(default=None, description="Path to docker-compose.yml (defaults to settings.target_compose_file)"),
    duration_seconds: Optional[int] = Query(default=None, ge=1, le=3600, description="Auto-rollback after this many seconds (None = manual rollback required)"),
    target_api_base_url: Optional[str] = Query(default=None, description="Target server API base URL (optional, defaults to settings)"),
):
    """
    Break environment variables in target server by modifying .env file and restarting container.
    
    This simulates configuration errors where:
    - Environment variables are missing (missing)
    - Environment variables have wrong/invalid values (wrong)
    
    The attack:
    1. Backs up the current .env file
    2. Modifies/removes the specified environment variable
    3. Restarts the target server container to pick up changes
    4. Optionally auto-rollbacks after duration_seconds
    """
    attack_id = str(uuid.uuid4())
    effective_api_url = target_api_base_url or settings.target_api_base_url
    
    # Use defaults from settings if not provided
    effective_env_file = target_env_file or settings.target_env_file
    effective_compose_file = compose_file or settings.target_compose_file
    
    # Resolve paths (make absolute if relative)
    env_path = Path(effective_env_file)
    compose_path = Path(effective_compose_file)
    
    if not env_path.is_absolute():
        # Resolve relative to workspace root
        workspace_root = find_workspace_root()
        env_path = workspace_root / env_path
    
    if not compose_path.is_absolute():
        # Resolve relative to workspace root
        workspace_root = find_workspace_root()
        compose_path = workspace_root / compose_path
    
    _attacks[attack_id] = {
        "id": attack_id,
        "state": "starting",
        "target_env_file": str(env_path),
        "compose_file": str(compose_path),
        "env_var_name": env_var_name,
        "failure_type": failure_type,
        "wrong_value": wrong_value,
        "duration_seconds": duration_seconds,
        "created_at": time.time(),
    }
    
    asyncio.create_task(_run_attack(
        attack_id, str(env_path), env_var_name, failure_type, wrong_value,
        str(compose_path), duration_seconds, effective_api_url
    ))
    
    return {"status": "started", "attack_id": attack_id}


@router.get("/break/env_vars/{attack_id}")
async def break_env_vars_status(attack_id: str):
    """Get the status of an env vars chaos attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    # Don't expose backup paths in response (but keep in memory for rollback)
    response = {k: v for k, v in attack.items() if k != "backup_path"}
    return response


@router.post("/break/env_vars/{attack_id}/stop")
async def break_env_vars_stop(attack_id: str):
    """Stop and rollback an env vars chaos attack."""
    attack = _attacks.get(attack_id)
    if not attack:
        raise HTTPException(status_code=404, detail="Unknown attack_id")
    
    if attack["state"] == "rolled_back":
        return {"status": "already_rolled_back", "attack_id": attack_id}
    
    if attack["state"] in ["failed", "rollback_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot rollback attack in state: {attack['state']}. Error: {attack.get('rollback_error', attack.get('error', 'Unknown error'))}"
        )
    
    target_env_file = attack.get("target_env_file")
    compose_file = attack.get("compose_file")
    
    if not target_env_file or not compose_file:
        raise HTTPException(
            status_code=400,
            detail="Missing target_env_file or compose_file in attack record"
        )
    
    try:
        await _rollback_attack(attack_id, target_env_file, compose_file)
        
        attack = _attacks.get(attack_id)
        if attack and attack["state"] == "rolled_back":
            return {
                "status": "rolled_back",
                "attack_id": attack_id,
                "restored_at": attack.get("rolled_back_at")
            }
        else:
            return {
                "status": "rollback_failed",
                "attack_id": attack_id,
                "error": attack.get("rollback_error", "Unknown error") if attack else "Attack not found"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rollback failed: {str(e)}"
        )

