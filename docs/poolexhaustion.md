# Database Connection Pool Exhaustion: Production SRE Implementation Guide

## 1. Architectural Roles (Critical Separation)

Before implementation, establish clear responsibility boundaries.

### A. Target Server (Application Stack)
Your production application that can fail:
- **FastAPI backend** - Business logic and API endpoints
- **PostgreSQL** - Data persistence layer
- **SQLAlchemy** - ORM and connection pooling
- **Alembic** - Database migrations
- **Streamlit frontend** - User interface
- **Docker Compose** - Container orchestration

**Key Constraints:**
- Runs core business logic
- Exposes health endpoints
- Can experience failures
- Must remain unaware of chaos/agent systems

### B. Chaos + Action Server (Control Plane)
Dedicated control system with mutation privileges:
- **Chaos endpoints** (`/break/*`) - Fault injection
- **Action endpoints** (`/action/*`) - Remediation execution
- **System mutation rights** - Container restarts, config changes
- **Exclusive restart permissions** - Only entity allowed to restart services

**Architectural Principle:** Agent communicates exclusively with control plane, never directly with target services.

## 2. Container Architecture

```yaml
services:
  api:              # Target backend service
  db:               # PostgreSQL instance
  frontend:         # Streamlit UI
  chaos-controller: # Chaos injection + remediation server
```

**Security Rule:** Target services cannot self-restart. Only the chaos/action server possesses mutation capabilities.

## 3. Target Server Design

### 3.1 Database Engine Configuration (Intentionally Fragile)

Configure SQLAlchemy with constrained pool settings to simulate production misconfigurations:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,           # Limited connection pool
    max_overflow=0,        # No overflow connections
    pool_timeout=3,        # Short timeout for failures
    pool_pre_ping=True     # Connection health validation
)
```

### 3.2 Health Endpoint (SRE-Standard)

Implement dependency-aware health checks:

```python
@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status
    }
```

### 3.3 Logging (Detection Signals)

Implement structured error logging for agent parsing:

```python
except Exception as e:
    logger.error(f"DB_ERROR: {str(e)}")
    raise HTTPException(status_code=503)
```

## 4. Chaos Server: Controlled Fault Injection

The chaos server injects deterministic, reversible failures that mirror production scenarios.

### 4.1 Chaos Endpoint: `/break/db_pool`

Located on chaos server but targets shared database:

```python
leaked_conns = []

@app.post("/break/db_pool")
def break_db_pool():
    for _ in range(20):
        conn = psycopg2.connect(DB_URL)
        leaked_conns.append(conn)
    return {"status": "DB pool exhausted"}
```

**Failure Simulation:**
- Connection leaks
- Query handling failures
- Thread pool starvation
- Realistic production outage patterns

### 4.2 Architectural Correctness

```
Chaos Server = Failure Injector
Target API = Victim Service
Database = Shared Dependency
```

This mirrors enterprise chaos engineering frameworks and fault injection systems.

## 5. Agent Observation Layer

Agent-driven monitoring requires correlation of multiple signals:

### Signal Sources:
1. **Health Endpoint**
   ```
   GET /health → {"database": "unhealthy"}
   ```

2. **Application Logs**
   ```
   DB_ERROR: QueuePool limit reached
   ```

3. **Behavioral Metrics**
   - 503 HTTP responses
   - Latency spikes
   - Error rate increases

**Diagnosis Confidence:** High when all signals correlate.

## 6. Diagnosis Logic (Deterministic)

Systematic elimination of alternative causes:

| Check | Result | Implication |
|-------|--------|-------------|
| DB container running | ✅ Yes | DB process is healthy |
| Network reachable | ✅ Yes | Connectivity intact |
| Authentication errors | ❌ No | Not credential issue |
| Pool timeout errors | ✅ Yes | Connection pool exhausted |

**Conclusion:** Database connection pool exhaustion due to leaked/unreleased connections.

## 7. Action Server: Safe Remediation

### 7.1 Primary Action: API Restart

```python
@app.post("/action/restart-api")
def restart_api():
    subprocess.run(
        ["docker", "compose", "restart", "api"],
        check=True
    )
    return {"status": "api restarted"}
```

**Effects:**
- Clears leaked connections
- Releases blocked threads
- Resets stale sessions
- Minimal service disruption

### 7.2 Verification Protocol

Post-remediation validation sequence:
1. Health endpoint check (`/health`)
2. Test database query execution
3. Latency baseline confirmation
4. Error rate monitoring

**Escalation Path:**
- If unresolved: DB container restart
- If persistent: Configuration adjustment (pool size increase)

## 8. Real-World SRE Alignment

This implementation matches production patterns:

- **Google SRE** incident response loops
- **Kubernetes** remediation controllers
- **AWS Systems Manager** automation documents
- **Enterprise chaos engineering** frameworks

## 9. Technology Stack Mapping

| Technology | Role | Responsibility |
|------------|------|----------------|
| FastAPI | Dual-purpose | Target service + action server endpoints |
| PostgreSQL | Failure domain | Shared database dependency |
| SQLAlchemy | Failure source | Connection pool management |
| Docker Compose | Isolation | Container lifecycle control |
| Alembic | Validation | Schema consistency checks |
| python-dotenv | Configuration | Environment variable management |
| Health Endpoints | Monitoring | Agent signal sources |
| Streamlit | Interface | Human oversight and control |

## 10. Implementation Outcomes

After completing this scenario, you achieve:

- ✅ **Real chaos injection system** with controlled fault scenarios
- ✅ **Autonomous remediation loop** with verification
- ✅ **Repeatable demonstration** of SRE capabilities
- ✅ **Reusable agent template** for additional failure modes

## Engineering Validation

Database connection pool exhaustion represents the optimal first implementation because it:

- **Stresses architecture** through multi-component interactions
- **Enforces clean separation** of chaos, action, and target systems
- **Proves agent autonomy** with deterministic decision-making
- **Mirrors real production outages** experienced by SRE teams

This foundation enables systematic expansion to additional failure scenarios while maintaining architectural integrity.
