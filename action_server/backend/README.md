# Action Server - Remediation Control Plane

**Standalone remediation service for autonomous incident response.**

The Action Server provides safe, audited endpoints that the Agent Control Plane calls to execute system remediation actions. It has exclusive rights to mutate infrastructure (restart containers, modify configs, etc.).

## Architecture Role

```
┌─────────────────┐                    ┌─────────────────┐
│  Chaos Server   │                    │ Action Server   │
│  Port: 8080     │                    │  Port: 9000     │
│  /break/*       │                    │  /action/*      │
│  Injects faults │                    │  Remediates     │
└────────┬────────┘                    │                 │
         │                              │  Has Docker/    │
         │         ┌──────────────────┐ │  system access  │
         │         │ Agent Control    │ └────────┬────────┘
         │         │    Plane         │          │
         │         │                  │          │
         └────────▶│  - Observes      │◀─────────┘
                   │  - Diagnoses     │
                   │  - Plans         │   Calls actions only
                   │  - Orchestrates  │   (no chaos control)
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Target Server  │
                   │  Port: 8000     │
                   │  (Victim)       │
                   └─────────────────┘
```

**Port Allocation:**

- Target Server Backend: **8000**
- Target Server Frontend: **3000**
- Chaos Server Backend: **8080**
- Chaos Server Frontend: **5173**
- Action Server Backend: **9000**
- PostgreSQL: **5432**

**Separation of Concerns:**

- ⚠️ **Chaos Server**: Injects faults (controlled by agent/testers)
- 🔧 **Action Server**: Remediates target only (no chaos control)
- 🎯 **Target Server**: Business application (victim)

## Capabilities

### Container Management

- Restart target API container
- Restart target database container
- Check container status

### Health Verification

- Comprehensive health checks
- Pool status monitoring
- Error rate tracking
- Performance metrics

### Chaos Control

- Stop ongoing chaos attacks
- Coordinate with chaos server

### Complete Workflows

- Full remediation workflows with verification
- Multi-step execution with rollback support
- Detailed audit logging

## API Endpoints

### Core Actions

#### `POST /api/v1/action/restart-target-api`

Restart the target server's API container.

**Query Parameters:**

- `dry_run` (bool, optional): Preview action without executing

**Primary fix for:**

- Connection pool exhaustion
- Memory leaks
- Thread starvation
- Hung processes

**Example:**

```bash
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api"
```

#### `POST /api/v1/action/restart-target-db`

Restart the target server's database container.

**Escalation action for:**

- Persistent connection issues
- Database deadlocks
- Corrupted connection states

#### `GET /api/v1/action/verify-target-health`

Verify the health of the target server.

**Returns:**

```json
{
  "is_healthy": true,
  "health_status": "ok",
  "database_status": "ok",
  "pool_health": "healthy",
  "pool_utilization": "low",
  "error_rate_percent": 2.5,
  "avg_response_time_ms": 45.2
}
```

#### `POST /api/v1/action/remediate-db-pool-exhaustion`

Complete remediation workflow for database connection pool exhaustion.

**Query Parameters:**

- `escalate_to_db_restart` (bool, optional): Restart DB if API restart doesn't work

**Workflow:**

1. Restart target API to release connections
2. Verify health
3. Escalate to DB restart if needed
4. Return detailed execution log

**Example:**

```bash
curl -X POST "http://localhost:9000/api/v1/action/remediate-db-pool-exhaustion?escalate_to_db_restart=true"
```

**Response:**

```json
{
  "remediation_complete": true,
  "execution_log": [
    {
      "step": 1,
      "action": "restart_target_api",
      "status": "success",
      "result": { "stdout": "Container restarted" }
    },
    {
      "step": 2,
      "action": "verify_health",
      "status": "success",
      "result": { "is_healthy": true }
    }
  ],
  "final_health": {
    "is_healthy": true,
    "pool_health": "healthy",
    "error_rate_percent": 1.2
  },
  "recommendation": "✅ System recovered successfully. Pool health restored."
}
```

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for container management)
- Target server running
- Chaos server running (optional, for chaos control)

### Installation

1. **Navigate to backend directory:**

```bash
cd action_server/backend
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start the server:**

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

### Configuration

Edit `.env` file:

```env
# Target server location
TARGET_API_BASE_URL=http://localhost:8000

# Path to target server's docker-compose.yml (relative from action_server/backend)
TARGET_DOCKER_COMPOSE_PATH=../../target_server/docker-compose.yml

# Safety settings
MAX_RESTARTS_PER_MINUTE=5
ACTION_TIMEOUT_SECONDS=120

# Enable audit logging
ENABLE_AUDIT_LOGGING=true
```

## Agent Integration

The Agent Control Plane calls this action server to execute remediation actions:

```python
import httpx

async def agent_fixes_pool_exhaustion(attack_id: str):
    """Example: Agent detects and fixes pool exhaustion"""

    # Agent calls action server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://action-server:9000/api/v1/action/remediate-db-pool-exhaustion",
            params={
                "attack_id": attack_id,
                "escalate_to_db_restart": True
            }
        )

        result = response.json()

        if result["remediation_complete"]:
            print("✅ System recovered")
            print(f"Recommendation: {result['recommendation']}")
        else:
            print("⚠️ Manual intervention needed")
            print(f"Execution log: {result['execution_log']}")
```

## Safety Features

### Rate Limiting

- Maximum 5 restarts per minute per endpoint
- Prevents accidental restart loops

### Audit Logging

- All actions logged to `action_server_audit.log`
- JSON format for easy parsing
- Includes timestamp, action, params, result, and user

### Dry-Run Mode

- Preview actions without executing
- See estimated downtime and risk level

```bash
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"
```

### Error Handling

- Comprehensive exception handling
- Detailed error messages
- Graceful degradation

## Monitoring

### Health Check

```bash
curl http://localhost:9000/health
```

### View Audit Logs

```bash
tail -f action_server_audit.log
```

### API Documentation

- Swagger UI: http://localhost:9000/docs
- ReDoc: http://localhost:9000/redoc

## Testing

### Test Container Restart

```bash
# Dry run first
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"

# Execute
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api"
```

### Test Health Verification

```bash
curl http://localhost:9000/api/v1/action/verify-target-health
```

### Test Complete Workflow

```bash
# 1. Start chaos attack (from chaos server)
curl -X POST "http://localhost:8080/api/v1/break/db_pool"

# 2. Wait for pool exhaustion
sleep 5

# 3. Trigger remediation (action server doesn't need attack ID)
curl -X POST "http://localhost:9000/api/v1/action/remediate-db-pool-exhaustion?escalate_to_db_restart=true"

# 4. Stop chaos attack separately (if needed)
curl -X POST "http://localhost:8080/api/v1/break/db_pool/{attack_id}/stop"
```

## Security Considerations

1. **Access Control**: In production, add authentication/authorization
2. **Network Isolation**: Run in secure network with firewall rules
3. **Docker Permissions**: Ensure proper Docker socket permissions
4. **Rate Limiting**: Configure appropriate limits for your environment
5. **Audit Logs**: Regularly review and rotate audit logs

## Troubleshooting

### Cannot connect to target server

- Check `TARGET_API_BASE_URL` in `.env`
- Verify target server is running
- Check network connectivity

### Docker commands fail

- Ensure Docker is running
- Check `TARGET_DOCKER_COMPOSE_PATH` is correct
- Verify Docker socket permissions

### Health checks timeout

- Increase `HEALTH_CHECK_TIMEOUT_SECONDS`
- Check target server performance
- Verify network latency

## Next Steps

1. **Add more actions**: Implement additional remediation actions
2. **Integrate with Agent**: Connect Agent Control Plane
3. **Add metrics**: Expose Prometheus metrics
4. **Implement webhooks**: Notify external systems of actions
5. **Add rollback**: Implement action rollback capabilities

## Architecture Notes

- **Exclusive Mutation Rights**: Only this server can restart containers
- **Idempotent Operations**: Safe to retry actions
- **Stateless Design**: No persistent state, easy to scale
- **Observable**: Comprehensive logging and audit trail
- **Agent-Friendly**: Structured responses for easy parsing
