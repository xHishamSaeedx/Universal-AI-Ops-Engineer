import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.utils.docker import DockerController
from app.utils.verification import TargetServerVerifier
from app.utils.audit import AuditLogger

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize utilities
docker_controller = DockerController()
verifier = TargetServerVerifier()
audit_logger = AuditLogger()


class ActionResponse(BaseModel):
    """Standard response model for all actions"""
    action: str
    status: str
    message: str
    details: dict = {}


class RemediationResponse(BaseModel):
    """Response model for complete remediation workflows"""
    remediation_complete: bool
    execution_log: list[dict]
    final_health: dict
    recommendation: str


@router.post("/action/restart-target-api", response_model=ActionResponse)
async def restart_target_api(
    dry_run: bool = Query(False, description="Preview action without executing")
):
    """
    Restart the target server's API container.
    
    **Primary remediation for:**
    - Connection pool exhaustion
    - Memory leaks
    - Thread starvation
    - Hung processes
    
    **Effect:**
    - Clears all database connections
    - Releases memory and threads
    - Resets application state
    - ~5-10 seconds downtime
    """
    action_name = "restart_target_api"
    
    if dry_run:
        audit_logger.log(action_name, {"dry_run": True}, "preview")
        return ActionResponse(
            action=action_name,
            status="dry_run",
            message="Would restart target API container",
            details={
                "command": f"docker compose -f {settings.target_docker_compose_path} restart api",
                "estimated_downtime": "5-10 seconds",
                "risk_level": "low"
            }
        )
    
    try:
        logger.info("Executing: Restart target API container")
        
        # Execute restart
        result = await docker_controller.restart_container(
            compose_file=settings.target_docker_compose_path,
            service_name="api"
        )
        
        # Wait for container to be ready
        await asyncio.sleep(5)
        
        # Verify health
        health = await verifier.check_target_health()
        
        audit_logger.log(action_name, {}, "success", health)
        
        return ActionResponse(
            action=action_name,
            status="completed",
            message="Target API container restarted successfully",
            details={
                "restart_output": result.get("stdout", ""),
                "health_check": health
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to restart target API: {str(e)}")
        audit_logger.log(action_name, {}, "failed", {"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart target API: {str(e)}"
        )


@router.post("/action/restart-target-db", response_model=ActionResponse)
async def restart_target_db(
    dry_run: bool = Query(False, description="Preview action without executing")
):
    """
    Restart the target server's database container.
    
    **Escalation action for:**
    - Persistent connection issues after API restart
    - Database deadlocks
    - Corrupted connection states
    
    **Effect:**
    - Terminates all database connections
    - Clears database caches
    - ~10-15 seconds downtime
    - Higher impact than API restart
    """
    action_name = "restart_target_db"
    
    if dry_run:
        audit_logger.log(action_name, {"dry_run": True}, "preview")
        return ActionResponse(
            action=action_name,
            status="dry_run",
            message="Would restart target database container",
            details={
                "command": f"docker compose -f {settings.target_docker_compose_path} restart db",
                "estimated_downtime": "10-15 seconds",
                "risk_level": "medium"
            }
        )
    
    try:
        logger.info("Executing: Restart target database container")
        
        # Execute restart
        result = await docker_controller.restart_container(
            compose_file=settings.target_docker_compose_path,
            service_name="db"
        )
        
        # Database needs more time to be ready
        await asyncio.sleep(10)
        
        # Verify health
        health = await verifier.check_target_health()
        
        audit_logger.log(action_name, {}, "success", health)
        
        return ActionResponse(
            action=action_name,
            status="completed",
            message="Target database container restarted successfully",
            details={
                "restart_output": result.get("stdout", ""),
                "health_check": health
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to restart target database: {str(e)}")
        audit_logger.log(action_name, {}, "failed", {"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart target database: {str(e)}"
        )


@router.get("/action/verify-target-health")
async def verify_target_health():
    """
    Verify the health of the target server.
    
    **Checks:**
    - Overall service status
    - Database connectivity
    - Connection pool health
    - Error rates
    - Response times
    
    **Returns:**
    - Comprehensive health assessment
    - Pool utilization metrics
    - Performance indicators
    """
    try:
        health = await verifier.check_target_health()
        return health
        
    except Exception as e:
        logger.error(f"Health verification failed: {str(e)}")
        return {
            "is_healthy": False,
            "error": str(e),
            "message": "Unable to verify target server health"
        }


@router.post("/action/remediate-db-pool-exhaustion", response_model=RemediationResponse)
async def remediate_db_pool_exhaustion(
    escalate_to_db_restart: bool = Query(False, description="Restart DB if API restart doesn't resolve issue")
):
    """
    Complete remediation workflow for database connection pool exhaustion.
    
    **Workflow:**
    1. Restart target API to release connections
    2. Verify health
    3. Escalate to DB restart if needed
    4. Return detailed execution log
    
    **Agent usage:**
    ```python
    response = await client.post(
        "http://action-server:9000/action/remediate-db-pool-exhaustion",
        params={"escalate_to_db_restart": True}
    )
    ```
    
    **Note:** Action server only controls target server remediation.
    Chaos attacks should be stopped separately via the chaos server.
    """
    execution_log = []
    
    try:
        # Step 1: Restart API container
        logger.info("Step 1: Restarting target API container")
        restart_result = await docker_controller.restart_container(
            compose_file=settings.target_docker_compose_path,
            service_name="api"
        )
        execution_log.append({
            "step": 1,
            "action": "restart_target_api",
            "status": "success",
            "result": {"stdout": restart_result.get("stdout", "")}
        })
        
        # Step 2: Wait and verify health
        logger.info("Step 2: Waiting for API to be ready and verifying health")
        await asyncio.sleep(5)
        health_check = await verifier.check_target_health()
        execution_log.append({
            "step": 2,
            "action": "verify_health",
            "status": "success",
            "result": health_check
        })
        
        # Step 3: Escalate if not healthy
        if not health_check.get("is_healthy") and escalate_to_db_restart:
            logger.warning("Step 3: Health check failed, escalating to DB restart")
            db_restart_result = await docker_controller.restart_container(
                compose_file=settings.target_docker_compose_path,
                service_name="db"
            )
            execution_log.append({
                "step": 3,
                "action": "escalate_db_restart",
                "status": "success",
                "result": {"stdout": db_restart_result.get("stdout", "")}
            })
            
            # Re-verify after escalation
            logger.info("Step 4: Re-verifying health after DB restart")
            await asyncio.sleep(10)
            health_check = await verifier.check_target_health()
            execution_log.append({
                "step": 4,
                "action": "verify_after_escalation",
                "status": "success",
                "result": health_check
            })
        
        # Determine final recommendation
        is_healthy = health_check.get("is_healthy", False)
        recommendation = (
            "✅ System recovered successfully. Pool health restored."
            if is_healthy
            else "⚠️ Health check still failing. Manual intervention may be required. "
                 "Check logs and consider scaling pool size."
        )
        
        audit_logger.log(
            "remediate_db_pool_exhaustion",
            {"escalated": escalate_to_db_restart},
            "success" if is_healthy else "partial",
            {"final_health": health_check}
        )
        
        return RemediationResponse(
            remediation_complete=is_healthy,
            execution_log=execution_log,
            final_health=health_check,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Remediation workflow failed: {str(e)}")
        audit_logger.log(
            "remediate_db_pool_exhaustion",
            {},
            "failed",
            {"error": str(e), "execution_log": execution_log}
        )
        
        return RemediationResponse(
            remediation_complete=False,
            execution_log=execution_log,
            final_health={"is_healthy": False, "error": str(e)},
            recommendation=f"❌ Remediation workflow failed: {str(e)}"
        )
