# Agent Control Plane - Quick Start Guide

## Prerequisites

1. **Target Server Running**: The target server and PostgreSQL must be running
2. **Docker**: For log monitoring (Docker Desktop on Windows)
3. **Groq API Key**: For LLM-based diagnosis (optional, has fallback)

## Quick Start

### 1. Start Target Server

```bash
cd ../target_server
docker compose up -d
```

Verify it's running:

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Install Dependencies

```bash
cd agent_control_plane/backend
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp env.example .env
```

Edit `.env` and set:

- `GROQ_API_KEY` (optional, but recommended for better diagnosis)
- Verify `TARGET_API_BASE_URL=http://localhost:8000`
- Verify container names match your setup

### 4. Run Agent Control Plane

```bash
python main.py
```

You should see:

```
Starting Agent Control Plane v1.0.0
Target server: http://localhost:8000
Poll interval: 30s
Autonomous monitoring started
```

### 5. Test Manual Trigger

In another terminal:

```bash
curl -X POST http://localhost:9001/api/v1/agent/trigger
```

This will run the workflow once and return the diagnosis.

### 6. Test with Chaos

1. Start chaos server (if not running):

   ```bash
   cd ../chaos_server/backend
   python main.py
   ```

2. Trigger chaos:

   ```bash
   curl -X POST http://localhost:8080/api/v1/break/db_pool
   ```

3. Watch agent logs - it should detect and diagnose the chaos automatically

## What the Agent Does

1. **Monitors** target server every 30 seconds:

   - Health endpoint
   - Metrics endpoint
   - Pool status endpoint
   - Application logs (from Docker)
   - PostgreSQL logs (from Docker)

2. **Detects** anomalies:

   - High error rate (>50%)
   - Critical pool health
   - Slow response times
   - Error patterns in logs

3. **Gathers** comprehensive symptoms when anomaly detected

4. **Diagnoses** using LLM:
   - Analyzes symptoms and logs
   - Identifies chaos type
   - Provides root cause analysis
   - Returns confidence level

## API Endpoints

- `GET /health` - Health check
- `GET /` - Root endpoint
- `POST /api/v1/agent/trigger` - Manually trigger workflow
- `GET /api/v1/agent/status` - Get agent status

## Troubleshooting

### Docker Logs Not Available

If you see warnings about Docker logs:

- Make sure Docker Desktop is running
- Verify container names in `.env` match your setup
- Agent will still work via API monitoring

### LLM Not Available

If Groq API key is not set:

- Agent uses fallback rule-based diagnosis
- Still detects chaos from metrics
- Less detailed diagnosis

### Target Server Not Reachable

- Check if target server is running: `curl http://localhost:8000/healthz`
- Verify `TARGET_API_BASE_URL` in `.env`
- Agent will retry on next poll cycle

## Next Steps

- Connect to action server for automatic remediation
- Add RAG for runbook retrieval
- Add incident history tracking
