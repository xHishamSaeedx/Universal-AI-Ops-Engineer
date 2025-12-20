# Agent Control Plane Architecture

## Core Principle: Blind Incident Response

The agent operates **completely blind to chaos** - it only sees symptoms and reacts like a real SRE.

```
┌─────────────────┐
│  Chaos Server   │  (Manual testing tool)
│  Port: 8080     │
└────────┬────────┘
         │ Injects faults
         ▼
┌─────────────────┐
│  Target Server  │  Emits logs/metrics
│  Port: 8000     │
└────────┬────────┘
         │ Symptoms only
         ▼
┌─────────────────┐
│ Agent Control   │  NO CONNECTION TO CHAOS!
│    Plane        │
│  Port: 9001     │  ✅ Monitors logs
│                 │  ✅ Detects anomalies
│  FastAPI +      │  ✅ Diagnoses with LLM
│  LangGraph      │  ✅ Takes action
└────────┬────────┘
         │ Calls remediation
         ▼
┌─────────────────┐
│ Action Server   │  Executes fixes
│  Port: 9000     │
└─────────────────┘
```

## Technology Stack

- **Framework**: FastAPI (port 9001)
- **Agent Workflow**: LangGraph StateGraph
- **LLM**: OpenAI GPT-4 / Claude
- **RAG**: Vector store + embeddings for runbooks
- **HTTP Client**: httpx (async)

## Agent Workflow (LangGraph)

### State Definition

```python
from typing import TypedDict

class AgentState(TypedDict):
    # Inputs
    symptoms: dict              # Logs, metrics, health status

    # Analysis
    diagnosis: str              # "DB connection pool exhaustion"
    confidence: float           # 0.0 to 1.0
    root_cause: str            # Investigation results

    # Action
    action_plan: list[dict]    # Steps to take
    execution_results: list    # Action outcomes

    # Outcome
    is_resolved: bool
    recommendation: str
```

### Workflow Steps

```python
1. MONITOR → Continuously poll target server
   - GET /api/v1/health
   - GET /api/v1/metrics
   - GET /api/v1/pool/status
   - Parse application logs

2. DETECT → Identify anomalies
   - Error rate spike (2% → 67%)
   - Pool health degraded (healthy → critical)
   - Response time increase (50ms → 1250ms)

3. GATHER → Collect all symptoms
   - Current metrics
   - Recent log patterns
   - Historical trends
   - System state

4. DIAGNOSE → Use LLM + RAG
   - Query runbooks for similar incidents
   - LLM analyzes symptoms
   - Returns: "Database connection pool exhaustion"

5. INVESTIGATE → Root cause analysis
   - Check traffic trends (traffic spike?)
   - Check query performance (slow queries?)
   - Check DB health (database issue?)
   - Determine: Connection leaks

6. PLAN → Create remediation strategy
   - Primary: Restart API container
   - Secondary: Restart database if needed
   - Verification steps

7. EXECUTE → Call action server
   POST /action/remediate-db-pool-exhaustion

8. VERIFY → Check recovery
   - Health status restored?
   - Pool health back to normal?
   - Error rate dropped?

9. LEARN → Update knowledge
   - Add incident to RAG
   - Update runbooks
   - Improve future diagnosis
```

## What Agent Sees vs Doesn't See

### ✅ Agent SEES:

```json
{
  "timestamp": "2024-12-20T15:30:00Z",
  "health_status": "degraded",
  "error_rate": 67.8,
  "pool_health": "critical",
  "pool_utilization": "high",
  "avg_response_time_ms": 1250,
  "logs": [
    "DB_ERROR: QueuePool limit reached",
    "503 Service temporarily unavailable"
  ]
}
```

### ❌ Agent DOES NOT SEE:

- Chaos server existence
- Attack ID or attack type
- That failure was intentional
- When attack will stop
- How to stop the attack

**Just like a real SRE getting paged at 3am!**

## Implementation Structure

```
agent_control_plane/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── monitor.py        # Observe target server
│   │   │   ├── detector.py       # Detect anomalies
│   │   │   ├── diagnoser.py      # LLM-based diagnosis
│   │   │   ├── investigator.py   # Root cause analysis
│   │   │   ├── planner.py        # Create action plans
│   │   │   └── workflow.py       # LangGraph StateGraph
│   │   ├── services/
│   │   │   ├── target_client.py  # HTTP client for target
│   │   │   ├── action_client.py  # HTTP client for actions
│   │   │   └── llm_service.py    # OpenAI/Claude wrapper
│   │   ├── rag/
│   │   │   ├── vector_store.py   # Embeddings storage
│   │   │   ├── runbooks.py       # Runbook retrieval
│   │   │   └── incidents.py      # Past incident lookup
│   │   ├── routes/
│   │   │   ├── agent.py          # Manual triggers
│   │   │   ├── health.py         # Agent health
│   │   │   └── status.py         # View agent state
│   │   └── core/
│   │       └── config.py
│   ├── main.py
│   └── requirements.txt
└── README.md
```

## API Endpoints

### Manual Triggers

```python
POST /agent/trigger
# Manually trigger incident response

GET /agent/status
# See what agent is doing

GET /agent/incidents
# View incident history
```

### Autonomous Operation

```python
# Background task (runs continuously)
@app.on_event("startup")
async def start_autonomous_monitoring():
    asyncio.create_task(monitor_and_respond_loop())
```

## Example: DB Pool Exhaustion Response

### 1. Monitoring (Continuous)

```python
async def monitor_target():
    """Poll every 30 seconds"""
    health = await target_client.get("/api/v1/health")
    metrics = await target_client.get("/api/v1/metrics")
    pool = await target_client.get("/api/v1/pool/status")

    return {
        "health": health,
        "metrics": metrics,
        "pool": pool,
        "timestamp": datetime.utcnow()
    }
```

### 2. Detection

```python
def detect_anomaly(current, historical):
    """Detect if system is unhealthy"""

    # Multiple signals
    high_errors = current["error_rate"] > 50
    critical_pool = current["pool_health"] == "critical"
    slow_response = current["avg_response_time"] > 1000

    return high_errors and critical_pool and slow_response
```

### 3. Diagnosis with LLM

```python
async def diagnose(symptoms: dict):
    """Use LLM + RAG for diagnosis"""

    # Query RAG for similar incidents
    similar = await rag.search(
        "high error rate critical pool timeout"
    )

    # Use LLM
    prompt = f"""
    Symptoms observed:
    - Error rate: {symptoms['error_rate']}%
    - Pool health: {symptoms['pool_health']}
    - Response time: {symptoms['avg_response_time']}ms
    - Logs: {symptoms['logs']}

    Similar past incidents:
    {similar}

    Diagnose the issue. Be specific.
    """

    diagnosis = await llm.complete(prompt)
    return diagnosis
```

### 4. Execute Action

```python
async def execute_remediation():
    """Call action server"""

    result = await action_client.post(
        "/action/remediate-db-pool-exhaustion",
        params={"escalate_to_db_restart": True}
    )

    return result
```

### 5. Verify Recovery

```python
async def verify_recovery():
    """Check if issue is resolved"""

    await asyncio.sleep(10)  # Wait for recovery

    health = await action_client.get(
        "/action/verify-target-health"
    )

    return health["is_healthy"]
```

## LangGraph Workflow Code

```python
from langgraph.graph import StateGraph, END

def create_incident_response_workflow():
    """Complete autonomous incident response"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("monitor", monitor_target_server)
    workflow.add_node("detect", detect_anomaly)
    workflow.add_node("gather", gather_all_symptoms)
    workflow.add_node("diagnose", diagnose_with_llm)
    workflow.add_node("investigate", investigate_root_cause)
    workflow.add_node("plan", create_action_plan)
    workflow.add_node("execute", call_action_server)
    workflow.add_node("verify", verify_recovery)
    workflow.add_node("learn", update_rag_database)

    # Define flow
    workflow.add_edge("monitor", "detect")

    workflow.add_conditional_edges(
        "detect",
        lambda state: "gather" if state["is_unhealthy"] else "monitor",
    )

    workflow.add_edge("gather", "diagnose")
    workflow.add_edge("diagnose", "investigate")
    workflow.add_edge("investigate", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "verify")

    workflow.add_conditional_edges(
        "verify",
        lambda state: "learn" if state["is_resolved"] else "plan",
        {
            "learn": "learn",
            "plan": "plan"  # Retry with different approach
        }
    )

    workflow.add_edge("learn", END)

    workflow.set_entry_point("monitor")

    return workflow.compile()
```

## Dependencies

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.0
langgraph==0.2.50
langchain==0.3.15
langchain-openai==0.2.15
httpx==0.28.1
pydantic==2.11.3
openai==1.54.0
python-dotenv==1.0.1
```

## Configuration

```env
# Agent Control Plane
PORT=9001
DEBUG=true

# Target server (monitoring)
TARGET_API_BASE_URL=http://localhost:8000

# Action server (remediation)
ACTION_SERVER_URL=http://localhost:9000

# LLM
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-4

# RAG
VECTOR_STORE_PATH=./data/vector_store
RUNBOOKS_PATH=./data/runbooks

# Monitoring
POLL_INTERVAL_SECONDS=30
ANOMALY_THRESHOLD_ERROR_RATE=50
```

## Testing Workflow

### 1. Manual Chaos Test

```bash
# Start chaos attack (you control this)
curl -X POST "http://localhost:8080/api/v1/break/db_pool"

# Agent detects and responds automatically
# - Sees symptoms
# - Diagnoses pool exhaustion
# - Calls action server
# - Verifies recovery

# Stop chaos (optional)
curl -X POST "http://localhost:8080/api/v1/break/db_pool/{id}/stop"
```

### 2. Autonomous Operation

```bash
# Start agent
cd agent_control_plane/backend
python main.py

# Agent runs continuously
# - Monitors every 30 seconds
# - Responds to any incidents
# - No human intervention needed
```

## Key Design Principles

1. **Blind Operation**: Agent never knows about chaos server
2. **Symptom-Based**: Only responds to observable symptoms
3. **LLM-Powered**: Uses AI for diagnosis and reasoning
4. **RAG-Enhanced**: Learns from past incidents
5. **Action-Oriented**: Calls action server to fix issues
6. **Verifiable**: Always checks if fix worked
7. **Learnable**: Updates knowledge base with each incident

## Why This Architecture?

✅ **Realistic**: Works like real SREs  
✅ **Flexible**: Handles chaos AND production incidents  
✅ **Intelligent**: Uses LLM for diagnosis  
✅ **Autonomous**: No human intervention needed  
✅ **Testable**: Easy to validate with chaos  
✅ **Production-Ready**: Can deploy to real systems

The agent is a **true autonomous SRE** that works in production, not just in chaos tests.
