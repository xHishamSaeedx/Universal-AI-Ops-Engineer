# Universal AI Ops Engineer

🤖 **Autonomous AI SRE that monitors, detects, diagnoses, and fixes system failures without human intervention.**

A complete demonstration of production-grade chaos engineering and autonomous incident response using AI agents.

## 🎯 What This Is

This project showcases a full **autonomous incident response system** with:

- **Target Server** - A production-like FastAPI application that can fail
- **Chaos Server** - Controlled fault injection to simulate real outages
- **Action Server** - Safe remediation execution with Docker control
- **Agent Control Plane** _(coming soon)_ - AI that observes, diagnoses, and orchestrates fixes

This isn't a toy demo. It's an enterprise-grade architecture that demonstrates:

- ✅ Chaos engineering principles
- ✅ Autonomous remediation
- ✅ Observability and metrics
- ✅ Safe mutation controls
- ✅ Audit trails and verification

## 🏗️ Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│  Chaos Server   │                    │ Action Server   │
│  Port: 8080     │                    │  Port: 9000     │
│  /break/*       │                    │  /action/*      │
│  Injects faults │                    │  Remediates     │
└────────┬────────┘                    │  Target Only    │
         │                              │                 │
         │         ┌──────────────────┐ │  Has Docker/    │
         │         │ Agent Control    │ │  system access  │
         │         │    Plane         │ └────────┬────────┘
         │         │                  │          │
         └────────▶│  - Observes      │◀─────────┘
                   │  - Diagnoses     │
                   │  - Plans         │
                   │  - Orchestrates  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Target Server  │
                   │  Port: 8000     │
                   │  FastAPI + DB   │
                   │  (Victim)       │
                   └─────────────────┘
```

**Clean Separation:**

- ⚠️ **Chaos Server**: Breaks things (controlled by agent/testers)
- 🔧 **Action Server**: Fixes target only (no chaos control)
- 🧠 **Agent**: Orchestrates both (the conductor)
- 🎯 **Target**: Victim (receives chaos & fixes)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Node.js 18+ (for frontends)

### 1. Start Target Server

```bash
cd target_server
docker compose up -d

# Verify
curl http://localhost:8000/api/v1/health
```

**Ports:**

- Backend: 8000
- Frontend: 3000
- PostgreSQL: 5432

### 2. Start Chaos Server

```bash
cd chaos_server/backend
pip install -r requirements.txt
python main.py
```

**Port:** 8080

### 3. Start Action Server

```bash
cd action_server/backend
pip install -r requirements.txt
cp env.example .env
python main.py
```

**Port:** 9000

### 4. Run Integration Test

```bash
cd action_server/backend
python test_integration.py
```

This will:

1. ✅ Verify all services are running
2. 💥 Start a chaos attack (DB pool exhaustion)
3. 🔍 Detect the failure
4. 🔧 Call action server to remediate
5. ✅ Verify recovery

## 📊 Service Ports

| Service                | Port | URL                   |
| ---------------------- | ---- | --------------------- |
| Target Server Backend  | 8000 | http://localhost:8000 |
| Target Server Frontend | 3000 | http://localhost:3000 |
| PostgreSQL             | 5432 | localhost:5432        |
| Chaos Server Backend   | 8080 | http://localhost:8080 |
| Chaos Server Frontend  | 5173 | http://localhost:5173 |
| Action Server Backend  | 9000 | http://localhost:9000 |

See [docs/port-allocation.md](docs/port-allocation.md) for details.

## 🎮 Try It Out

### Scenario: Database Connection Pool Exhaustion

1. **Check initial health:**

   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/api/v1/pool/status
   ```

2. **Start chaos attack:**

   ```bash
   curl -X POST "http://localhost:8080/api/v1/break/db_pool?connections=10&hold_seconds=30"
   ```

3. **Watch target degrade:**

   ```bash
   # You'll see errors and timeouts
   curl http://localhost:8000/api/v1/health
   ```

4. **Trigger remediation:**

   ```bash
   curl -X POST "http://localhost:9000/api/v1/action/remediate-db-pool-exhaustion?escalate_to_db_restart=true"
   ```

5. **Stop chaos (optional):**

   ```bash
   # Get attack_id from step 2 response, then:
   curl -X POST "http://localhost:8080/api/v1/break/db_pool/{attack_id}/stop"
   ```

6. **Verify recovery:**
   ```bash
   curl http://localhost:9000/api/v1/action/verify-target-health
   ```

## 📚 Documentation

- **[Architecture Overview](docs/architecture.md)** - System design and components
- **[Chaos Server](docs/chaos-server-architecture.md)** - Fault injection system
- **[Pool Exhaustion Guide](docs/poolexhaustion.md)** - DB connection pool scenario
- **[Action Server Integration](docs/action-server-integration.md)** - Remediation API usage
- **[Port Allocation](docs/port-allocation.md)** - Service port mappings
- **[Observability Improvements](docs/observability-improvements.md)** - Metrics and health checks

### Component READMEs

- [Target Server](target_server/README.md) - The application that fails
- [Chaos Server](chaos_server/backend/README.md) - Fault injection
- [Action Server](action_server/backend/README.md) - Remediation control
- [Action Server Quick Start](action_server/QUICKSTART.md) - 5-minute setup

## 🧪 Testing

### Unit Tests

```bash
# Test action server endpoints
cd action_server/backend
python test_actions.py
```

### Integration Test

```bash
# Full chaos → remediation workflow
cd action_server/backend
python test_integration.py
```

### Manual Testing

```bash
# Dry-run mode (preview without executing)
curl -X POST "http://localhost:9000/api/v1/action/restart-target-api?dry_run=true"
```

## 🔧 Development

### API Documentation

- Target Server: http://localhost:8000/docs
- Chaos Server: http://localhost:8080/docs
- Action Server: http://localhost:9000/docs

### Health Checks

```bash
# Check all services
curl http://localhost:8000/api/v1/health  # Target
curl http://localhost:8080/api/v1/health  # Chaos
curl http://localhost:9000/health         # Action
```

### View Logs

```bash
# Target server (Docker)
docker compose -f target_server/docker-compose.yml logs -f

# Action server
tail -f action_server/backend/action_server_audit.log

# Chaos server
# Check console output
```

## 🎯 Key Features

### Chaos Server

- ✅ Database pool exhaustion attacks
- ✅ Controlled fault injection
- ✅ Attack lifecycle management (start/stop)
- ✅ Configurable intensity and duration

### Target Server

- ✅ Realistic production application
- ✅ Intentionally fragile configuration
- ✅ Comprehensive health endpoints
- ✅ Pool status and metrics

### Action Server

- ✅ Container restart capabilities
- ✅ Health verification
- ✅ Complete remediation workflows
- ✅ Dry-run mode
- ✅ Audit logging
- ✅ Rate limiting

## 🛡️ Safety Features

- **Blast Radius Control** - Only affects sandboxed services
- **Rate Limiting** - Prevents restart loops
- **Dry-Run Mode** - Preview actions before executing
- **Audit Trails** - All actions logged with timestamps
- **Verification** - Post-remediation health checks
- **Rollback Support** - Stop chaos attacks on demand

## 📈 Roadmap

- [x] Target Server with intentional failure points
- [x] Chaos Server with DB pool exhaustion
- [x] Action Server with remediation capabilities
- [x] Complete integration tests
- [ ] Agent Control Plane with AI diagnosis
- [ ] RAG integration for runbook lookup
- [ ] Additional chaos scenarios (CPU, memory, network)
- [ ] Multi-step remediation workflows
- [ ] Approval gates for high-risk actions
- [ ] Metrics and observability dashboard

## 🤝 Contributing

This is a portfolio/demonstration project. See individual component READMEs for architecture details.

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🎓 Learning Resources

This project demonstrates:

- **Chaos Engineering** - Netflix-style fault injection
- **Site Reliability Engineering** - Autonomous incident response
- **Docker & Containers** - Container lifecycle management
- **FastAPI** - Modern Python web frameworks
- **Database Operations** - Connection pool management
- **Observability** - Health checks, metrics, logging
- **System Design** - Separation of concerns, clean architecture

Perfect for:

- Learning chaos engineering principles
- Understanding autonomous systems
- Building AI-driven operations tools
- Demonstrating SRE capabilities

---

Built with ❤️ to showcase autonomous incident response and chaos engineering principles.
