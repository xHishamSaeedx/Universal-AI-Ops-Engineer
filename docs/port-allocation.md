# Port Allocation Guide

## Service Port Mapping

This document lists all ports used by services in the Universal AI Ops Engineer project.

### Production Services

| Service                      | Port | URL                         | Purpose                                 |
| ---------------------------- | ---- | --------------------------- | --------------------------------------- |
| **Target Server Backend**    | 8000 | http://localhost:8000       | FastAPI - Business application (victim) |
| **Target Server Frontend**   | 3000 | http://localhost:3000       | React/Vite - Target UI                  |
| **Target Server PostgreSQL** | 5432 | postgresql://localhost:5432 | Database                                |
| **Chaos Server Backend**     | 8080 | http://localhost:8080       | FastAPI - Fault injection               |
| **Chaos Server Frontend**    | 5173 | http://localhost:5173       | React/Vite - Chaos control UI           |
| **Action Server Backend**    | 9000 | http://localhost:9000       | FastAPI - Remediation control           |

### Port Ranges Reserved

```
8000-8099: Application backends
3000-3099: Frontend applications
5000-5999: Databases and storage
9000-9099: Control plane services
```

## Service Communication Matrix

```
┌─────────────────┐
│ Action Server   │ :9000
│ (Remediation)   │
└────────┬────────┘
         │
         ├─────────────▶ Target Server Backend :8000
         │               (Health checks, verification)
         │
         ├─────────────▶ Chaos Server Backend :8080
         │               (Stop attacks)
         │
         └─────────────▶ Docker Socket
                         (Restart containers)

┌─────────────────┐
│ Chaos Server    │ :8080
│ (Fault Inject)  │
└────────┬────────┘
         │
         └─────────────▶ Target Server Backend :8000
                         (Attack endpoints)

┌─────────────────┐
│ Target Server   │ :8000
│ (Application)   │
└────────┬────────┘
         │
         └─────────────▶ PostgreSQL :5432
                         (Database queries)
```

## API Endpoints by Service

### Target Server (Port 8000)

**Health & Monitoring:**

- `GET /api/v1/health` - Health check
- `GET /api/v1/metrics` - Application metrics
- `GET /api/v1/pool/status` - Connection pool status

**Testing Endpoints:**

- `POST /api/v1/pool/hold` - Hold DB connection (for testing)

**Frontend:**

- Port 3000 proxies to port 8000

### Chaos Server (Port 8080)

**Chaos Injection:**

- `POST /api/v1/break/db_pool` - Start pool exhaustion attack
- `GET /api/v1/break/db_pool/{attack_id}` - Check attack status
- `POST /api/v1/break/db_pool/{attack_id}/stop` - Stop attack

**Health:**

- `GET /api/v1/health` - Chaos server health

**Frontend:**

- Port 5173 proxies to port 8080

### Action Server (Port 9000)

**Remediation Actions:**

- `POST /api/v1/action/restart-target-api` - Restart target API
- `POST /api/v1/action/restart-target-db` - Restart target database
- `POST /api/v1/action/stop-chaos-attack` - Stop chaos attack
- `POST /api/v1/action/remediate-db-pool-exhaustion` - Complete workflow

**Verification:**

- `GET /api/v1/action/verify-target-health` - Verify target health

**Health:**

- `GET /health` - Action server health

## Configuration Files

### Target Server

```env
# target_server/backend/.env
PORT=8000
DATABASE_URL=postgresql://postgres:password@localhost:5432/target_server
```

### Chaos Server

```env
# chaos_server/backend/.env
PORT=8080
TARGET_API_BASE_URL=http://localhost:8000
```

### Action Server

```env
# action_server/backend/.env
PORT=9000
TARGET_API_BASE_URL=http://localhost:8000
TARGET_DOCKER_COMPOSE_PATH=../../target_server/docker-compose.yml
```

## Docker Compose Port Mappings

### Target Server (docker-compose.yml)

```yaml
services:
  db:
    ports:
      - "5432:5432" # PostgreSQL

  api:
    ports:
      - "8000:8000" # FastAPI backend
```

### Frontend Development Servers

```bash
# Target frontend
cd target_server/frontend
npm run dev  # Port 3000

# Chaos frontend
cd chaos_server/frontend
npm run dev  # Port 5173
```

## Starting All Services

### Start Order

1. **Target Server** (with database):

   ```bash
   cd target_server
   docker compose up -d
   # Backend: 8000, DB: 5432

   cd frontend
   npm run dev
   # Frontend: 3000
   ```

2. **Chaos Server**:

   ```bash
   cd chaos_server/backend
   python main.py
   # Backend: 8080

   cd ../frontend
   npm run dev
   # Frontend: 5173
   ```

3. **Action Server**:
   ```bash
   cd action_server/backend
   python main.py
   # Backend: 9000
   ```

### Verify All Services

```bash
# Target server
curl http://localhost:8000/api/v1/health
curl http://localhost:3000  # Frontend

# Chaos server
curl http://localhost:8080/api/v1/health
curl http://localhost:5173  # Frontend

# Action server
curl http://localhost:9000/health

# Database
psql -h localhost -p 5432 -U postgres -d target_server
```

## Port Conflicts

If you encounter "port already in use" errors:

### Check what's using a port:

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### Change ports if needed:

1. Update `.env` files
2. Update `vite.config.js` for frontends
3. Update docker-compose port mappings
4. Update action server's target URLs

## Firewall Configuration

For production deployment, ensure these ports are:

**Open internally:**

- 8000 (target API)
- 8080 (chaos API)
- 9000 (action API)
- 5432 (PostgreSQL - restrict to backend only)

**Open to users:**

- 3000 (target frontend)
- 5173 (chaos frontend)

**Closed externally:**

- 5432 (PostgreSQL)
- Docker socket

## Agent Configuration

When building the Agent Control Plane, configure these endpoints:

```python
# Agent configuration
TARGET_SERVER_URL = "http://localhost:8000"
CHAOS_SERVER_URL = "http://localhost:8080"
ACTION_SERVER_URL = "http://localhost:9000"

# For Docker deployment
TARGET_SERVER_URL = "http://target-server:8000"
CHAOS_SERVER_URL = "http://chaos-server:8080"
ACTION_SERVER_URL = "http://action-server:9000"
```

## Health Check Summary

Quick health check script:

```bash
#!/bin/bash
echo "Checking all services..."

echo -n "Target Server (8000): "
curl -s http://localhost:8000/api/v1/health | jq -r '.status'

echo -n "Chaos Server (8080): "
curl -s http://localhost:8080/api/v1/health | jq -r '.status'

echo -n "Action Server (9000): "
curl -s http://localhost:9000/health | jq -r '.status'

echo -n "PostgreSQL (5432): "
pg_isready -h localhost -p 5432 -U postgres
```

## Next Steps

1. ✅ All ports allocated and documented
2. ✅ Action server configured with correct endpoints
3. 📋 Agent Control Plane will use these configurations
4. 📋 Consider containerizing action server for consistency
5. 📋 Add action server to main docker-compose (optional)
