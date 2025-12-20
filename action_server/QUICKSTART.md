# Action Server - Quick Start Guide

Get the action server running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose installed
- Target server running (optional for testing)

## Setup Steps

### 1. Navigate to Backend

```bash
cd action_server/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example config
cp env.example .env

# Edit .env with your settings (optional - defaults work for local development)
```

### 5. Start the Server

```bash
python main.py
```

The server will start at: **http://localhost:9000**

### Port Information

The action server uses port **9000** and communicates with:

- **Target Server**: http://localhost:8000 (backend)
- **PostgreSQL**: localhost:5432 (via target server)

**Note:** Action server only controls target server remediation, not chaos injection.

## Verify Installation

### Option 1: Browser

Open http://localhost:9000/docs to see the interactive API documentation

### Option 2: Test Script

```bash
python test_actions.py
```

### Option 3: cURL

```bash
curl http://localhost:9000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Action Server - Remediation Control",
  "version": "1.0.0",
  "capabilities": [
    "restart_target_api",
    "restart_target_db",
    "verify_target_health",
    "stop_chaos_attack",
    "remediate_db_pool_exhaustion"
  ]
}
```

## Test an Action (Dry Run)

```bash
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"
```

This previews what would happen without actually executing.

## Next Steps

1. **Start Target Server** (if not running):

   ```bash
   cd ../target_server
   docker compose up
   ```

2. **Test Health Verification**:

   ```bash
   curl http://localhost:9000/api/v1/action/verify-target-health
   ```

3. **Test Complete Workflow**:

   - Start chaos attack (from chaos server)
   - Watch action server remediate it

4. **Integrate with Agent**:
   - See `docs/action-server-integration.md` for agent integration examples

## Configuration

Edit `.env` to customize:

```env
# Target server location
TARGET_API_BASE_URL=http://localhost:8000

# Path to target's docker-compose.yml (relative from action_server/backend)
TARGET_DOCKER_COMPOSE_PATH=../../target_server/docker-compose.yml
```

## Troubleshooting

### Server won't start

- Check Python version: `python --version` (need 3.11+)
- Verify dependencies: `pip install -r requirements.txt`
- Check port 9000 is available

### Can't connect to target server

- Ensure target server is running
- Check `TARGET_API_BASE_URL` in `.env`
- Test connectivity: `curl http://localhost:8000/api/v1/health`

### Docker commands fail

- Ensure Docker is running
- Check Docker permissions
- Verify `TARGET_DOCKER_COMPOSE_PATH` is correct

## API Documentation

- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **OpenAPI JSON**: http://localhost:9000/openapi.json

## Key Endpoints

### Health Check

```bash
GET http://localhost:9000/health
```

### Restart Target API

```bash
POST http://localhost:9000/api/v1/action/restart-target-api
```

### Verify Target Health

```bash
GET http://localhost:9000/api/v1/action/verify-target-health
```

### Complete Remediation Workflow

```bash
POST http://localhost:9000/api/v1/action/remediate-db-pool-exhaustion?escalate_to_db_restart=true
```

## Development Mode

The server runs with auto-reload in development:

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

## Production Deployment

For production, disable debug mode and configure properly:

```env
DEBUG=false
ENABLE_AUDIT_LOGGING=true
MAX_RESTARTS_PER_MINUTE=3
```

Run with production ASGI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --workers 4
```

## Support

- **Documentation**: See `backend/README.md` for detailed docs
- **Integration Guide**: See `docs/action-server-integration.md`
- **Logs**: Check console output and `action_server_audit.log`

You're ready to go! 🚀
