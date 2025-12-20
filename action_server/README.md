# Action Server

**Standalone remediation control plane for autonomous incident response.**

The Action Server is a dedicated FastAPI service that provides safe, audited endpoints for system remediation. It is called by the Agent Control Plane to execute fixes for detected issues.

## Quick Start

```bash
# Navigate to backend
cd action_server/backend

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env

# Run
python main.py
```

Server runs at: http://localhost:9000

API Documentation: http://localhost:9000/docs

## Key Endpoints

- `POST /api/v1/action/restart-target-api` - Restart API container
- `POST /api/v1/action/restart-target-db` - Restart database container
- `GET /api/v1/action/verify-target-health` - Check target health
- `POST /api/v1/action/remediate-db-pool-exhaustion` - Complete remediation workflow

## Architecture

```
Agent Control Plane ──────▶ Action Server ──────▶ Target Server
   (Observes & Plans)        (Executes Fixes)      (Gets Fixed)
```

See `backend/README.md` for detailed documentation.
