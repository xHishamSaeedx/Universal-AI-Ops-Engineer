# Agent Control Plane

Autonomous incident response agent that monitors target server and PostgreSQL logs, detects chaos, and diagnoses issues using LangGraph and LLM.

## Architecture

The agent operates **blind to chaos** - it only sees symptoms (logs, metrics, health status) and reacts like a real SRE.

```
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
│  LangGraph      │
└─────────────────┘
```

## Features

- **Log Monitoring**: Monitors both target server and PostgreSQL container logs
- **Chaos Detection**: Detects anomalies from logs and metrics
- **LLM Diagnosis**: Uses Groq LLM to diagnose chaos from symptoms
- **LangGraph Workflow**: Autonomous workflow using LangGraph StateGraph
- **Blind Operation**: Never knows about chaos server, only sees symptoms

## Technology Stack

- **Framework**: FastAPI (port 9001)
- **Agent Workflow**: LangGraph StateGraph
- **LLM**: Groq (Llama 3.1, Mixtral, etc.)
- **HTTP Client**: httpx (async)
- **Log Monitoring**: Docker logs API

## Workflow

The agent follows this LangGraph workflow:

1. **MONITOR** → Continuously poll target server and collect logs
2. **DETECT** → Identify anomalies (error rate, pool health, response time)
3. **GATHER** → Collect comprehensive symptoms
4. **DIAGNOSE** → Use LLM to diagnose chaos from symptoms and logs

## Setup

### 1. Install Dependencies

```bash
cd agent_control_plane/backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Start Target Server

Make sure target server and PostgreSQL are running:

```bash
cd ../../target_server
docker compose up -d
```

### 4. Run Agent Control Plane

```bash
cd agent_control_plane/backend
python main.py
```

The agent will:

- Start monitoring target server every 30 seconds
- Monitor logs from both target server and PostgreSQL containers
- Automatically detect and diagnose chaos

## API Endpoints

### Health Check

```bash
GET /health
```

### Manual Trigger

```bash
POST /api/v1/agent/trigger
```

Manually trigger the incident response workflow.

### Agent Status

```bash
GET /api/v1/agent/status
```

Get current agent status.

## Log Monitoring

The agent monitors logs from:

1. **Target Server Container** (`target_server_api`)

   - Application logs
   - Error logs
   - Pool-related errors

2. **PostgreSQL Container** (`target_server_db`)
   - Database logs
   - Connection errors
   - Query errors

The agent extracts chaos indicators:

- Pool errors (exhaustion, timeouts)
- Connection errors
- Timeout errors
- General application errors

## Chaos Detection

The agent detects chaos based on:

- **Error Rate**: > 50% (configurable)
- **Pool Health**: critical or degraded
- **Response Time**: > 1000ms
- **Health Status**: degraded, unhealthy, or down
- **Log Errors**: Presence of error patterns in logs

## LLM Diagnosis

When chaos is detected, the agent:

1. Collects symptoms (metrics, health, logs)
2. Extracts error patterns from logs
3. Sends to LLM (Groq) for diagnosis
4. Returns:
   - Diagnosis (e.g., "Database connection pool exhaustion")
   - Confidence level (0.0 to 1.0)
   - Root cause analysis
   - Chaos type

## Configuration

Key configuration options in `.env`:

```env
# Monitoring
POLL_INTERVAL_SECONDS=30
ANOMALY_THRESHOLD_ERROR_RATE=50.0
LOG_TAIL_LINES=100

# LLM
GROQ_API_KEY=your-key-here
LLM_MODEL=llama-3.1-70b-versatile
LLM_TEMPERATURE=0.3

# Target server
TARGET_API_BASE_URL=http://localhost:8000
TARGET_CONTAINER_NAME=target_server_api
TARGET_DB_CONTAINER_NAME=target_server_db
```

## Testing

### 1. Start All Services

```bash
# Terminal 1: Target server
cd target_server
docker compose up -d

# Terminal 2: Agent Control Plane
cd agent_control_plane/backend
python main.py
```

### 2. Trigger Chaos (from chaos server)

```bash
curl -X POST "http://localhost:8080/api/v1/break/db_pool"
```

### 3. Watch Agent Response

The agent will:

- Detect the chaos from logs and metrics
- Diagnose it using LLM
- Log the diagnosis

Check agent logs to see the diagnosis.

### 4. Manual Trigger

```bash
curl -X POST "http://localhost:9001/api/v1/agent/trigger"
```

## Current Limitations

- **Action Server Not Connected**: The agent diagnoses but doesn't execute remediation yet
- **No RAG**: Runbook retrieval not yet implemented
- **No Historical Trends**: Only current state analysis
- **No Verification Loop**: Doesn't verify if issue is resolved

## Future Enhancements

- Connect to action server for remediation
- Add RAG for runbook retrieval
- Add historical trend analysis
- Add verification loop
- Add incident history tracking
- Add learning from past incidents

## Troubleshooting

### Docker Logs Not Available

If Docker logs are not accessible, the agent will:

- Still monitor via API (health, metrics, pool status)
- Use fallback diagnosis without log analysis
- Log warnings about missing Docker access

### LLM Not Available

If Groq API key is not set:

- Agent uses fallback rule-based diagnosis
- Still detects chaos from metrics
- Less detailed diagnosis

### Target Server Not Reachable

The agent will:

- Log connection errors
- Continue monitoring (will retry)
- Not trigger false positives

## License

See LICENSE file in project root.
