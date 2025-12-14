# Chaos Server Architecture

Purpose: purpose-built service to inject controlled failures, emit events, and orchestrate chaos drills for the Universal AI Ops Engineer.

## Goals
- Reproducible faults across app/API, DB, network, compute, auth, and storage.
- Safe by design: guardrails, blast-radius controls, kill-switch, and audit trails.
- Observable: all injections emit structured events/metrics for correlation.
- Composable: API/SDK/CLI for manual drills, scheduled chaos monkey, and scripted scenarios.

## Capabilities (what it can do)
- Fault injections (HTTP `POST /break/*`):
  - API layer: latency, 5xx bursts, crash/restart, circuit-breaker trips.
  - Database: auth failures, pool exhaustion, long transaction locks, crash/restart.
  - Compute: high CPU, memory leak/OOM, disk fill, thread starvation.
  - Network: packet loss, DNS failure, LB misroute, bandwidth throttle.
  - Cache/queue: corruption, eviction storm, backlog growth, worker crash.
  - Auth/secrets: expired tokens, rotated secrets, bad config.
  - Third-party: upstream 5xx, timeout, rate-limit, fallback offline.
- Scheduling:
  - Chaos monkey: randomized injections by class/severity with cooldowns.
  - Scenario runner: ordered scripts for multi-step drills (e.g., DB auth failure then API restart).
  - Calendared drills: run at windows with safety approvals.
- Safety & governance:
  - Global kill switch; per-tenant/service allowlist; max concurrency.
  - Blast radius config (scope, duration, intensity); dry-run mode.
  - RBAC/API keys; approval webhooks; audit log with correlation ids.
- Observability:
  - Emits events to event bus/logs with tags (fault_type, target, severity, run_id).
  - Exports metrics (injections_total, active_faults, failures, duration).
  - Health checks for chaos server itself.
- Integrations:
  - Notifies agent/event bus to correlate symptoms with injections.
  - Hooks to action server for auto-rollback on kill-switch.
  - SDK/CLI to trigger faults locally or in CI.

## Components (how it works)
- API Layer: REST endpoints `/break/*`, `/scenarios/*`, `/kill`, `/status` with auth and validation.
- Fault Modules: pluggable executors per domain (api, db, network, compute, cache, auth, third-party); each supports inject, rollback, and status.
- Scheduler:
  - Chaos Monkey: randomized selection based on policies.
  - Scenario Runner: executes predefined sequences with delays and guards.
- State & Config:
  - Persistent store for runs, audit, and configs (e.g., SQLite/Postgres).
  - Config loader for blast radius, allowlists, intensity presets.
- Safety & Policy Engine:
  - Evaluates requests vs. policies; enforces approvals and kill-switch.
  - Limits duration and concurrent faults; auto-rollbacks on expiry.
- Observability Hooks:
  - Structured events to logs/bus; metrics exporter; tracing for injections.
- Integration Layer:
  - Webhooks to agent/observability; CLI/SDK wrappers for local use.

## Key Flows
- Manual drill: User/agent calls `/break/db_auth?duration=120s&intensity=medium`; policy engine approves ? DB fault module injects (e.g., rotate creds to invalid) ? events/metrics emitted ? auto-rollback at expiry or on `/kill`.
- Scheduled chaos monkey: Scheduler selects fault from allowed pool, applies blast-radius caps, triggers inject ? emits events ? rollback after duration.
- Scenario run: `/scenarios/run/latency-then-oom` executes ordered faults with waits; halts if kill-switch or health threshold breached.
- Kill-switch: `/kill` clears active faults, triggers rollbacks, emits termination events, and pauses scheduler.

## Implementation Notes
- Keep injections idempotent and reversible; every injector must define `inject()` and `rollback()`.
- Tag all events with `run_id` and `scenario_id` for correlation with observability and incident timelines.
- Provide dry-run mode that validates policies without executing faults.
