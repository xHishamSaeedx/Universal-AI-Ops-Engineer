# Universal AI Ops Engineer - Build Order

## Executive Summary

Start with the foundational components that create a testable environment, then build the monitoring and action capabilities, followed by chaos injection, and finally the intelligent orchestration layer.

## Recommended Build Order

### 1. Target Server (Start Here)

**Why**: Foundation component - you need a system to monitor and fix before building the monitoring infrastructure.

**Tech Stack**:

- **Backend API**: FastAPI (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Streamlit (Python web UI) or simple HTML/CSS
- **Containerization**: Docker + Docker Compose
- **Database Migrations**: Alembic
- **Environment Management**: python-dotenv
- **Health Checks**: Custom `/health` endpoints returning JSON status

**Components to build**:

- FastAPI backend API with REST endpoints
- Postgres database with connection pooling
- Basic frontend (Streamlit or dummy) for testing
- Docker Compose orchestration (multi-service setup)
- Basic health endpoints (`/healthz`, `/ready`)
- Environment variable configuration (`.env` files)
- Database models and basic CRUD operations

**Deliverables**: Working sandbox environment where failures can occur.

---

### 2. Action & Execution Plane

**Why**: Need actions before you can monitor their effects and success.

**Tech Stack**:

- **Action Server**: FastAPI (Python async web framework)
- **Script Execution**: Python subprocess module for shell commands
- **Authentication**: API key authentication (simple header-based)
- **Container Management**: Docker Python SDK or docker-py
- **File Operations**: Python os, shutil modules
- **Database Operations**: psycopg2 for PostgreSQL connections
- **Logging**: Python logging module with structured JSON output
- **Error Handling**: Custom exception classes and try/catch blocks

**Components to build**:

- Action Server (FastAPI app) running on separate port (e.g., 9000)
- REST endpoints for system modifications:
  - `POST /action/restart-api` - Docker Compose restart api service
  - `POST /action/restart-db` - Docker Compose restart db service
  - `POST /action/regenerate-env` - Generate new secrets and update .env
  - `POST /action/clear-cache` - Remove cache directory and recreate
  - `POST /action/restore-db` - Restore from PostgreSQL snapshot
  - `POST /action/run-migrations` - Execute Alembic migrations
  - `POST /action/switch-to-fallback` - Update .env with backup API endpoint
- Python scripts for each action (subprocess calls to Docker/system commands)
- Safety controls: rate limiting, authentication, idempotency checks
- Comprehensive error handling and rollback mechanisms

**Deliverables**: API endpoints that can programmatically fix system issues.

---

### 3. Observability & Knowledge

**Why**: Need monitoring to detect issues and validate fixes.

**Tech Stack**:

- **Database**: Supabase (PostgreSQL with real-time subscriptions)
- **Visualization**: Grafana with PostgreSQL data source
- **Metrics Collection**: psutil (Python system metrics), requests (HTTP latency)
- **Logging**: Python logging with JSON formatting, file rotation
- **Vector Database**: Pinecone, Weaviate, or ChromaDB for embeddings
- **Embeddings**: OpenAI text-embedding-ada-002 or sentence-transformers
- **RAG Framework**: LangChain or LlamaIndex
- **Document Processing**: PyPDF2, python-docx for parsing documentation
- **Search**: Elasticsearch or simple vector similarity search

**Components to build**:

- Logging system (Supabase for structured logs + Grafana for visualization)
- Metrics collection:
  - System metrics (CPU, memory, disk usage via psutil)
  - Application metrics (response times, error rates)
  - Database metrics (connection counts, query performance)
  - Container metrics (Docker stats API)
- Error detection and parsing (log analysis, pattern matching)
- RAG system for documentation/runbooks:
  - System troubleshooting guides (PDF/markdown documents)
  - Fix strategies for common issues (runbook database)
  - Configuration documentation (API specs, environment variables)
  - Vector embeddings for semantic search
- Health check endpoints (detailed status reporting)
- Alerting rules (threshold-based notifications)

**Deliverables**: Comprehensive monitoring system that feeds data to the agent.

---

### 4. Chaos Server

**Why**: Need controlled failure injection to test agent responses.

**Tech Stack**:

- **Chaos Server**: FastAPI (Python web framework)
- **Database Faults**: psycopg2, SQL injection scripts
- **Network Faults**: iptables, tc (traffic control) commands
- **Compute Faults**: stress-ng, dd (disk filling), Python memory allocation
- **Scheduling**: APScheduler or cron-like Python scheduling
- **Event Emission**: Webhook calls to observability endpoints
- **State Management**: SQLite or in-memory dict for fault tracking
- **Safety Controls**: Threading locks, timeout decorators
- **Configuration**: YAML/JSON config files for fault parameters

**Components to build**:

- Chaos injection API (`/break/*` endpoints) on dedicated port (e.g., 8001)
- Fault types with implementation:
  - Database failures: connection pool exhaustion, auth failures, table locks
  - API failures: artificial latency delays, service crashes, error responses
  - Compute failures: CPU stress loops, memory leaks, disk space filling
  - Network failures: DNS manipulation, connection blocking, packet loss
- Safety controls:
  - Global kill switch (`/kill` endpoint)
  - Blast radius limits (duration, intensity, scope)
  - Auto-rollback mechanisms with timeouts
  - Concurrent fault limits
- Event emission system (structured events to observability)
- Scheduled chaos scenarios (cron-based random fault injection)
- Chaos monkey mode (automated randomized failures)
- Fault correlation IDs for incident tracking

**Deliverables**: Controlled testing environment for agent validation.

---

### 5. AI Agent Control Plane (Final Component)

**Why**: Intelligent orchestration layer that ties everything together.

**Tech Stack**:

- **Agent Framework**: LangGraph or CrewAI for multi-agent orchestration
- **LLM**: OpenAI GPT-4 or Claude for reasoning and planning
- **RAG Integration**: LangChain or LlamaIndex for document retrieval
- **Action Calling**: OpenAI Function Calling or tool calling APIs
- **State Management**: Redis or in-memory state for agent memory
- **Event Processing**: Webhook endpoints for signal intake
- **Safety Controls**: Rule-based filtering, approval workflows
- **Communication**: Slack/Discord webhooks for human notifications
- **Database**: Supabase/PostgreSQL for incident tracking and state
- **Async Processing**: Python asyncio for concurrent operations
- **Configuration**: YAML for agent behaviors and safety rules

**Components to build**:

- Multi-agent architecture:
  - Perception Agent: Signal processing and context building
  - Diagnosis Agent: Root cause analysis with RAG
  - Planning Agent: Action sequencing and rollback planning
  - Verification Agent: Post-action validation
- Signal intake system (webhooks from observability and chaos server)
- Diagnosis engine with RAG integration (query documentation for solutions)
- Planning and safety controls (risk assessment, approval gates)
- Action orchestration (parallel execution, dependency management, rollback)
- Human approval workflows (Slack/Discord notifications, approval buttons)
- Narrative generation (incident summaries, action explanations)
- Agent memory and learning (incident pattern recognition)
- Safety guardrails (action validation, blast radius limits)

**Deliverables**: Autonomous SRE assistant that monitors, diagnoses, fixes, and explains issues.

## Validation at Each Step

- **Step 1**: Manual testing - break things manually, verify restart works
- **Step 2**: Action testing - call endpoints manually, verify fixes work
- **Step 3**: Monitoring testing - inject failures, verify detection
- **Step 4**: Chaos testing - automated fault injection, verify detection
- **Step 5**: Agent testing - full autonomous operation with chaos monkey

## Dependencies

- Target Server enables Action Plane
- Action Plane enables meaningful Observability
- Observability enables Chaos Server correlation
- Chaos Server enables Agent Control Plane testing
- Agent Control Plane orchestrates all components

## Risk Mitigation

- Build incrementally with working validation at each step
- Start with simple Docker Compose setup
- Use idempotent, reversible actions
- Include comprehensive logging from day one
- Test manually before automating
