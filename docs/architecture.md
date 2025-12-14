# Universal AI Ops Engineer - Chaos-Ready Architecture (Executive Overview)

## Goal
Deliver an autonomous SRE/DevOps assistant that monitors, diagnoses, fixes, and explains issues across a small production-like stack, while a chaos server continuously injects real-world failure modes to harden reliability.

## Core Lanes
- Experience: Humans receive plain-language incident briefs, approvals, and postmortems; they can trigger chaos drills on demand.
- Observability & Knowledge: Logs/metrics/traces flow into Supabase/Grafana (or similar) plus a curated RAG store of runbooks, configs, and system docs.
- Agent Control Plane: Multi-agent loop (perception/diagnosis, planner, verifier) orchestrated with LangGraph/CrewAI; safety rules and approval gates wrap risky actions.
- Action & Execution Plane: Action server (FastAPI/n8n) exposes controlled tools that call script library + infra APIs (Docker/K8s/GitHub/secrets) to change the system.
- Target Stack: Backend API, Postgres DB, Frontend; instrumented with health checks and restart hooks for repeatable remediation.
- Chaos Server: Dedicated service exposing /break/* endpoints and a scheduler (“chaos monkey”) to trigger faults (latency, OOM, DB auth, disk full, etc.) and emit events.
- Validation & Reporting: Automated checks after each action, metrics comparison (before/after), dashboards, and concise narratives pushed to chat/email.

## How It Orchestrates (happy-path loop)
1) Observe: Streams from logs/metrics + health probes land in observability store; changes in chaos state also raise events.
2) Diagnose: Perception agent fuses signals with RAG docs/runbooks to classify incident, hypothesize root cause, and estimate blast radius.
3) Plan: Planner proposes a guarded sequence (e.g., clear cache ? restart API ? verify DB) with rollback branches; safety layer enforces policies/approvals.
4) Act: Approved steps invoke action server endpoints that run idempotent scripts (docker compose restart, rotate secrets, restore snapshot, rerun migrations, switch to fallback API).
5) Verify: Validation layer re-checks health, SLIs, and logs; if still degraded, the plan iterates or escalates with context.
6) Explain: Agent posts a short brief: what broke, why, actions taken, evidence, and prevention notes; updates dashboards.

## Chaos Integration (first-class citizen)
- Injection: Chaos server triggers targeted faults via /break/* routes or scheduled drills; it can randomize blast radius and duration.
- Telemetry: Every chaos event is labeled and shipped to observability so diagnosis can correlate symptoms to injections.
- Safety: Chaos only runs in sandboxed envs with kill-switch; approvals required for persistent or destructive scenarios.
- Learning: Post-incident data feeds RAG store to improve future diagnosis and playbook quality.

## Security & Guardrails
- Action server is the only component with mutation rights; all calls are authenticated, rate-limited, and policy-checked.
- Secrets managed via Vault/Doppler and rotated through controlled actions; no direct secret exposure to the agent.
- Idempotent, reversible scripts with rollbacks; change audit log recorded per action.

## Interfaces
- Human: Chat/UI for approvals, chaos drill triggers, and status; dashboards for SLIs.
- Machine: REST/webhook endpoints for actions, health/metrics exporters, event bus for observability + chaos events.
