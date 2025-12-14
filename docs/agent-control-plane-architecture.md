# Agent Control Plane Architecture

Purpose: Coordinate perception, diagnosis, planning, orchestration, execution requests, and verification for the Universal AI Ops Engineer with strong safety controls.

## Goals
- Turn signals + docs into actionable, guarded remediation plans.
- Orchestrate multi-step tool calls with verification and rollback options.
- Keep humans in the loop via approvals and clear narratives.

## Capabilities
- Signal intake: subscribe to observability events (logs/metrics/traces), health checks, chaos events, and user prompts.
- Context building: retrieve runbooks/configs/incidents via RAG; stitch recent signals into a working set.
- Diagnosis: classify incident type, hypothesize root cause, estimate blast radius/severity.
- Planning: generate ordered actions with safety tags, pre/post checks, and rollback paths.
- Orchestration: sequence approved steps, manage concurrency, retry/rollback logic, and timing.
- Safety/approvals: enforce policies, seek human approval for risky steps, respect change windows.
- Tool routing: translate plan steps into action server calls; batch or parallelize when safe.
- Verification: run post-action health/SLI checks; re-plan if not healed.
- Explanation: produce concise briefs (what/why/actions/evidence/prevention).

## Components
- Ingress & Event Bus: webhook/queue for signals from observability, chaos server, and chat UI.
- Perception & Context Builder: normalizes signals; fetches docs/runbooks via RAG; tracks recent incidents.
- Diagnosis Agent: classifies and proposes root-cause hypotheses with confidence.
- Planner: builds/updates plans; sequences candidate steps and rollback hooks.
- Safety & Policy Engine: approvals, guardrails, and risk scoring; blocks disallowed actions.
- Orchestrator: executes the approved plan timeline (ordering, concurrency, retries, backoff), updates state, and hands steps to the Tool Router.
- Tool Router: maps orchestrated steps to action server endpoints; handles idempotency metadata.
- Verification Agent: runs post-step checks; compares before/after metrics; triggers re-plan or rollback.
- Narrative/Comms: crafts human-readable updates, approvals, and postmortems to chat/email.

## Key Flows
- Incident loop: signal ? context build ? diagnosis ? plan ? safety check ? orchestration ? tool calls ? verify ? iterate or explain.
- Chaos correlation: chaos events tagged with run_id feed perception to accelerate diagnosis.
- Approval gating: risky steps paused until approval; on deny, planner selects alternative.
- Rollback/retry: planner carries rollback hooks; orchestrator triggers rollback on verification regression.

## Integration Points
- Reads: Observability store, chaos events, docs/RAG, config/state DB.
- Writes: Action server (tool calls), dashboards/metrics, chat/webhook updates.
- Identity: uses service identity + scoped credentials; never stores raw secrets.

## Safety Notes
- Enforce max concurrent actions per service; timeouts on tools; per-step idempotency hints.
- Log every decision with correlation ids; trace spans around tool calls and verification.
- Provide dry-run mode for plan preview without executing tools.
