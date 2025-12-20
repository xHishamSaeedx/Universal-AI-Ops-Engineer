# Action Server Integration Guide

## Overview

The **Action Server** is a standalone FastAPI service that executes remediation actions. The **Agent Control Plane** calls this server to fix issues detected in the target server.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTONOMOUS REMEDIATION FLOW                  │
└─────────────────────────────────────────────────────────────────┘

1. OBSERVE                2. DIAGNOSE              3. EXECUTE
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Target     │────────▶│    Agent     │────────▶│   Action     │
│   Server     │ signals │   Control    │ actions │   Server     │
│              │◀────────│    Plane     │◀────────│              │
└──────────────┘ metrics └──────────────┘ results └──────────────┘
                                                          │
                                                          ▼
                                                   Restarts Target
```

## Agent Control Plane Usage

### Basic Action Call

```python
import httpx

async def fix_pool_exhaustion():
    """Agent detects pool exhaustion and calls action server to fix it"""

    action_server = "http://action-server:9000"

    async with httpx.AsyncClient() as client:
        # Call complete remediation workflow
        response = await client.post(
            f"{action_server}/api/v1/action/remediate-db-pool-exhaustion",
            params={
                "attack_id": "abc-123",  # Optional: stop this chaos attack
                "escalate_to_db_restart": True  # Restart DB if API restart fails
            },
            timeout=120.0  # 2 minute timeout
        )

        result = response.json()
        return result
```

### Response Structure

```json
{
  "remediation_complete": true,
  "execution_log": [
    {
      "step": 1,
      "action": "stop_chaos_attack",
      "status": "success",
      "result": { "status": "cancelling" }
    },
    {
      "step": 2,
      "action": "restart_target_api",
      "status": "success",
      "result": { "stdout": "Container restarted" }
    },
    {
      "step": 3,
      "action": "verify_health",
      "status": "success",
      "result": {
        "is_healthy": true,
        "pool_health": "healthy",
        "error_rate_percent": 1.2
      }
    }
  ],
  "final_health": {
    "is_healthy": true,
    "health_status": "ok",
    "pool_health": "healthy",
    "error_rate_percent": 1.2
  },
  "recommendation": "✅ System recovered successfully. Pool health restored."
}
```

## Complete Agent Workflow

### Example: Autonomous Pool Exhaustion Recovery

```python
import httpx
import asyncio
from typing import Dict, Any


class AgentControlPlane:
    """Agent that detects and fixes issues autonomously"""

    def __init__(self):
        self.target_api = "http://localhost:8000"  # Target server backend
        self.action_server = "http://localhost:9000"  # Action server backend
        self.chaos_server = "http://localhost:8080"  # Chaos server backend

    async def observe_target(self) -> Dict[str, Any]:
        """Step 1: Observe target server for symptoms"""
        async with httpx.AsyncClient() as client:
            # Check health
            health = await client.get(f"{self.target_api}/api/v1/health")
            health_data = health.json()

            # Check metrics
            metrics = await client.get(f"{self.target_api}/api/v1/metrics")
            metrics_data = metrics.json()

            # Check pool status
            pool = await client.get(f"{self.target_api}/api/v1/pool/status")
            pool_data = pool.json()

            return {
                "health": health_data,
                "metrics": metrics_data,
                "pool": pool_data
            }

    async def diagnose(self, symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Diagnose the issue"""
        pool_health = symptoms["pool"]["pool"].get("pool_health")
        error_rate = symptoms["metrics"]["application"].get("error_rate_percent", 0)
        db_status = symptoms["health"]["services"]["database"].get("status")

        # Simple rule-based diagnosis
        if pool_health == "critical" and error_rate > 50 and db_status == "unhealthy":
            return {
                "issue": "db_pool_exhaustion",
                "confidence": "high",
                "severity": "critical",
                "root_cause": "Database connection pool exhausted - leaked connections"
            }

        return {"issue": "unknown", "confidence": "low"}

    async def execute_remediation(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Call action server to fix the issue"""
        if diagnosis["issue"] == "db_pool_exhaustion":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.action_server}/api/v1/action/remediate-db-pool-exhaustion",
                    params={"escalate_to_db_restart": True},
                    timeout=120.0
                )
                return response.json()

        return {"error": "No remediation available"}

    async def verify_recovery(self) -> bool:
        """Step 4: Verify the fix worked"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.action_server}/api/v1/action/verify-target-health"
            )
            health = response.json()
            return health.get("is_healthy", False)

    async def autonomous_incident_response(self):
        """Complete autonomous incident response loop"""
        print("🤖 Agent: Starting incident detection...")

        # Step 1: Observe
        print("👀 Agent: Observing target server...")
        symptoms = await self.observe_target()

        # Step 2: Diagnose
        print("🧠 Agent: Diagnosing issue...")
        diagnosis = await self.diagnose(symptoms)

        if diagnosis["issue"] == "unknown":
            print("❓ Agent: No issue detected or unable to diagnose")
            return

        print(f"🔍 Agent: Diagnosed {diagnosis['issue']} with {diagnosis['confidence']} confidence")
        print(f"📊 Root cause: {diagnosis['root_cause']}")

        # Step 3: Execute remediation
        print("🔧 Agent: Executing remediation via action server...")
        result = await self.execute_remediation(diagnosis)

        if result.get("remediation_complete"):
            print("✅ Agent: Remediation completed successfully")
            print(f"📋 Executed {len(result['execution_log'])} steps")
        else:
            print("⚠️ Agent: Remediation partially completed or failed")

        # Step 4: Verify
        print("🔍 Agent: Verifying recovery...")
        is_recovered = await self.verify_recovery()

        if is_recovered:
            print("✅ Agent: System fully recovered")
            print(f"💡 Recommendation: {result.get('recommendation')}")
        else:
            print("⚠️ Agent: System still degraded - escalating to human")

        return result


# Usage
async def main():
    agent = AgentControlPlane()
    await agent.autonomous_incident_response()


if __name__ == "__main__":
    asyncio.run(main())
```

## Available Actions

### Individual Actions

#### 1. Restart Target API

```python
response = await client.post(
    f"{action_server}/api/v1/action/restart-target-api",
    params={"dry_run": False}  # Set True for preview
)
```

**Use for:**

- Connection pool exhaustion
- Memory leaks
- Thread starvation
- Hung processes

#### 2. Restart Target Database

```python
response = await client.post(
    f"{action_server}/api/v1/action/restart-target-db",
    params={"dry_run": False}
)
```

**Use for:**

- Persistent connection issues after API restart
- Database deadlocks
- Corrupted connection states

#### 3. Verify Target Health

```python
response = await client.get(
    f"{action_server}/api/v1/action/verify-target-health"
)

health = response.json()
is_healthy = health["is_healthy"]
```

**Returns:**

- Overall health status
- Pool health and utilization
- Error rates
- Response times

#### 4. Stop Chaos Attack

```python
response = await client.post(
    f"{action_server}/api/v1/action/stop-chaos-attack",
    params={"attack_id": "abc-123"}
)
```

**Use for:**

- Stopping ongoing chaos tests
- Part of remediation workflow

### Complete Workflows

#### 5. Remediate DB Pool Exhaustion

```python
response = await client.post(
    f"{action_server}/api/v1/action/remediate-db-pool-exhaustion",
    params={
        "attack_id": "abc-123",  # Optional
        "escalate_to_db_restart": True  # Optional
    }
)
```

**What it does:**

1. Stops chaos attack (if attack_id provided)
2. Restarts API container
3. Verifies health
4. Escalates to DB restart if needed
5. Returns detailed execution log

## Error Handling

### Connection Errors

```python
try:
    response = await client.post(
        f"{action_server}/api/v1/action/restart-target-api"
    )
except httpx.ConnectError:
    print("❌ Cannot connect to action server")
    # Escalate to human
except httpx.TimeoutException:
    print("⏱️ Action timed out")
    # Retry or escalate
```

### Failed Actions

```python
result = response.json()

if not result.get("remediation_complete"):
    # Check execution log for failures
    for step in result["execution_log"]:
        if step["status"] == "failed":
            print(f"Step {step['step']} failed: {step.get('error')}")

    # Escalate to human
    notify_human(result)
```

## Safety Features

### Dry-Run Mode

Test actions without executing:

```python
response = await client.post(
    f"{action_server}/api/v1/action/restart-target-api",
    params={"dry_run": True}
)

preview = response.json()
print(f"Would execute: {preview['details']['command']}")
print(f"Risk level: {preview['details']['risk_level']}")
```

### Rate Limiting

- Maximum 5 restarts per minute per endpoint
- Prevents accidental restart loops

### Audit Logging

- All actions logged with timestamp
- JSON format for easy parsing
- Includes user, params, result

### Timeouts

- Health checks: 10 seconds
- Actions: 120 seconds
- Configurable per environment

## Testing

### Test Action Server Connectivity

```python
async def test_connectivity():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("http://action-server:9000/health")
            if resp.status_code == 200:
                print("✅ Action server is reachable")
                return True
        except Exception as e:
            print(f"❌ Action server unreachable: {str(e)}")
            return False
```

### Test Complete Workflow

```bash
# 1. Start chaos attack
curl -X POST "http://localhost:8080/api/v1/break/db_pool"

# 2. Wait for symptoms
sleep 5

# 3. Agent detects and calls action server
python agent_control_plane.py

# 4. Verify recovery
curl "http://action-server:9000/api/v1/action/verify-target-health"
```

## Configuration

### Environment Variables

```env
# In agent control plane
ACTION_SERVER_URL=http://localhost:9000
TARGET_SERVER_URL=http://localhost:8000
CHAOS_SERVER_URL=http://localhost:8080

# Timeouts
ACTION_TIMEOUT_SECONDS=120
HEALTH_CHECK_INTERVAL_SECONDS=30
```

### Network Configuration

Ensure proper network connectivity:

- Agent → Action Server (port 9000)
- Action Server → Target Server (port 8000)
- Action Server → Chaos Server (port 8001)
- Action Server → Docker socket

## Next Steps

1. **Implement Agent Control Plane** that calls these endpoints
2. **Add observability** - metrics, traces, logs
3. **Implement RAG** for diagnosis using documentation
4. **Add more actions** - scale pool, rotate credentials, etc.
5. **Add approval gates** for high-risk actions
6. **Implement rollback** capabilities

## API Reference

Full API documentation available at:

- Swagger UI: http://action-server:9000/docs
- ReDoc: http://action-server:9000/redoc

## Support

For issues or questions:

1. Check action server logs
2. Review audit logs (`action_server_audit.log`)
3. Test with dry-run mode
4. Verify network connectivity
