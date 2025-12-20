# Action Server Configuration Summary

## ✅ Configuration Complete

The action server has been configured with the correct ports and endpoints for all services.

## 🔌 Port Configuration

### Action Server

- **Port**: 9000
- **URL**: http://localhost:9000
- **API Docs**: http://localhost:9000/docs

### Target Services

- **Target Server Backend**: 8000 (http://localhost:8000)
- **Target Server Frontend**: 3000 (http://localhost:3000)
- **PostgreSQL**: 5432 (localhost:5432)
- **Chaos Server Backend**: 8080 (http://localhost:8080)
- **Chaos Server Frontend**: 5173 (http://localhost:5173)

## 📝 Configuration Files Updated

### 1. Action Server Config (`app/core/config.py`)

```python
# Server settings
port: int = 9000

# Target server configuration
target_api_base_url: str = "http://localhost:8000"  # Target server only
target_docker_compose_path: str = "../../target_server/docker-compose.yml"  # From action_server/backend
```

### 2. Environment Template (`env.example`)

```env
PORT=9000
TARGET_API_BASE_URL=http://localhost:8000
TARGET_DOCKER_COMPOSE_PATH=../../target_server/docker-compose.yml
```

### 3. Documentation Updated

- ✅ `action_server/backend/README.md` - Architecture diagram with ports
- ✅ `action_server/QUICKSTART.md` - Port information section
- ✅ `docs/action-server-integration.md` - All example URLs
- ✅ `docs/port-allocation.md` - Complete port mapping guide
- ✅ Root `README.md` - Service port table

## 🧪 Test Files

### 1. Basic Tests (`test_actions.py`)

Tests individual action endpoints without requiring other services.

### 2. Integration Test (`test_integration.py`) - NEW!

Complete workflow test:

1. Verifies all services running
2. Starts chaos attack
3. Detects degradation
4. Calls remediation
5. Verifies recovery

Run it:

```bash
cd action_server/backend
python test_integration.py
```

## 🚀 Quick Start

### 1. Copy Environment File

```bash
cd action_server/backend
cp env.example .env
```

The defaults are already correct for local development!

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Server

```bash
python main.py
```

You should see:

```
🚀 Action Server - Remediation Control v1.0.0
🎯 Target API: http://localhost:8000
📋 Audit Logging: Enabled
🔒 Scope: Target server remediation only
Action server ready to receive remediation requests
```

### 4. Test Connectivity

```bash
# Test action server
curl http://localhost:9000/health

# Test it can reach target server
curl http://localhost:9000/api/v1/action/verify-target-health

# Test dry-run mode
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"
```

## 🔍 Verification Checklist

Run this to verify everything is configured correctly:

```bash
# 1. Check action server config
cd action_server/backend
grep "port:" app/core/config.py
grep "target_api_base_url:" app/core/config.py
grep "chaos_api_base_url:" app/core/config.py

# Expected output:
#   port: int = 9000
#   target_api_base_url: str = "http://localhost:8000"

# 2. Start action server
python main.py

# 3. In another terminal, test basic health
curl http://localhost:9000/health

# 4. Test with dry-run (safe, doesn't need target running)
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"
```

## 📊 Service Communication Flow

```
┌─────────────────────────────────────────────────────────┐
│               Action Server (Port 9000)                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Communicates with:                                      │
│                                                          │
│  1. Target Server (localhost:8000)                      │
│     - GET /api/v1/health                                │
│     - GET /api/v1/metrics                               │
│     - GET /api/v1/pool/status                           │
│                                                          │
│  2. Docker Socket                                        │
│     - docker compose restart api                         │
│     - docker compose restart db                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Next Steps

1. **Start Target Server**:

   ```bash
   cd target_server
   docker compose up -d
   ```

2. **Start Chaos Server**:

   ```bash
   cd chaos_server/backend
   python main.py
   ```

3. **Start Action Server**:

   ```bash
   cd action_server/backend
   python main.py
   ```

4. **Run Integration Test**:

   ```bash
   cd action_server/backend
   python test_integration.py
   ```

5. **Build Agent Control Plane** that will:
   - Observe target server metrics
   - Detect anomalies
   - Call action server to fix issues
   - Verify recovery

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 9000
netstat -ano | findstr :9000  # Windows
lsof -i :9000                  # Linux/Mac

# Change port if needed
# Edit action_server/backend/app/core/config.py
# Change port: int = 9000 to a different port
```

### Cannot Connect to Target Server

```bash
# Verify target is running
curl http://localhost:8000/api/v1/health

# Check docker containers
cd target_server
docker compose ps

# Check target server logs
docker compose logs -f api
```

### Cannot Connect to Chaos Server

```bash
# Verify chaos server is running
curl http://localhost:8080/api/v1/health

# Start if not running
cd chaos_server/backend
python main.py
```

### Docker Commands Fail

```bash
# Check Docker is running
docker ps

# Check docker-compose path
ls -la ../target_server/docker-compose.yml

# Verify Docker socket access
docker compose -f ../target_server/docker-compose.yml ps
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:9000/docs
- **Port Allocation Guide**: `docs/port-allocation.md`
- **Integration Guide**: `docs/action-server-integration.md`
- **Architecture Docs**: `docs/`

---

✅ **Configuration is complete and ready for agent integration!**
