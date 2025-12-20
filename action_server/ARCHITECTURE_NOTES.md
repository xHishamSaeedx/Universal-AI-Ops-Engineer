# Action Server Architecture Notes

## Design Philosophy: Strict Separation of Concerns

The action server follows a **clear separation** between chaos injection and remediation:

### What Action Server DOES:

✅ **Remediates the target server only**

- Restart target API container
- Restart target database container
- Verify target server health
- Execute complete remediation workflows

### What Action Server DOES NOT DO:

❌ **Control chaos injection**

- Does NOT stop chaos attacks
- Does NOT start chaos attacks
- Does NOT communicate with chaos server

## Why This Design?

### 1. **Clear Responsibility Boundaries**

```
┌─────────────────┐
│  Chaos Server   │  → Controls: Fault injection
│  (Attack)       │  → Managed by: Testers, CI/CD, Agent
└─────────────────┘

┌─────────────────┐
│ Action Server   │  → Controls: Target remediation
│ (Defend)        │  → Managed by: Agent only
└─────────────────┘

┌─────────────────┐
│ Target Server   │  → Controls: Nothing (victim)
│ (Victim)        │  → Managed by: No one (receives chaos & fixes)
└─────────────────┘
```

### 2. **Realistic Production Separation**

In real production systems:

- **Incident response systems** (PagerDuty, runbooks) don't control attack vectors
- **Remediation tools** (Kubernetes operators, auto-healing) focus on fixing, not breaking
- **Chaos tools** (Chaos Monkey, Gremlin) are separate from healing systems

### 3. **Agent Control Plane Responsibility**

The **Agent Control Plane** orchestrates both:

```python
# Agent's job: Coordinate chaos AND remediation

# 1. Start chaos (via chaos server)
attack_id = await chaos_server.start_attack()

# 2. Wait for failure
await monitor_target_until_degraded()

# 3. Trigger remediation (via action server)
result = await action_server.remediate()

# 4. Stop chaos (via chaos server)
await chaos_server.stop_attack(attack_id)

# 5. Verify recovery
await verify_target_healthy()
```

The agent is the **conductor**, not the action server.

## Workflow Example

### Before (Action server controlling chaos):

```
Agent → Action Server → Stop chaos + Fix target
```

**Problem:** Action server has too much power and responsibility

### After (Clean separation):

```
Agent → Chaos Server → Stop chaos attack
Agent → Action Server → Fix target server
```

**Benefit:** Each component has single responsibility

## Benefits of This Design

### 1. **Security**

- Action server has NO ability to inject faults
- Chaos control requires separate authentication
- Reduced blast radius if action server is compromised

### 2. **Testability**

- Can test action server without chaos server running
- Can test chaos server without action server
- Clear interfaces between components

### 3. **Flexibility**

- Can replace chaos server with different tool (Gremlin, Litmus)
- Can use action server for non-chaos incidents
- Agent can implement different orchestration strategies

### 4. **Auditability**

- Clear audit trail of who stopped chaos (agent, not action server)
- Separate logs for attack vs remediation
- Better compliance and traceability

## Implementation Details

### Removed from Action Server:

- ❌ `chaos_api_base_url` config setting
- ❌ `/action/stop-chaos-attack` endpoint
- ❌ `stop_chaos_attack()` method in verification utils
- ❌ Chaos attack ID parameter in remediation workflow

### What Remains:

- ✅ Target server URL and Docker control
- ✅ Health verification
- ✅ Container restart capabilities
- ✅ Complete remediation workflows

### Agent Must Now:

1. **Stop chaos separately:**

   ```python
   # Agent calls chaos server directly
   await httpx.post(f"{chaos_server}/api/v1/break/db_pool/{attack_id}/stop")
   ```

2. **Then trigger remediation:**
   ```python
   # Agent calls action server
   await httpx.post(f"{action_server}/api/v1/action/remediate-db-pool-exhaustion")
   ```

## Future Enhancements

With this clean separation, we can easily add:

1. **Multiple chaos sources**

   - Agent could coordinate chaos from multiple tools
   - Action server doesn't need to know about any of them

2. **Non-chaos incidents**

   - Production incidents (not from chaos)
   - Action server remediates the same way

3. **Complex orchestration**

   - Agent can implement sophisticated strategies
   - Start chaos → wait → remediate → verify → restart chaos

4. **Approval gates**
   - Different approval rules for chaos vs remediation
   - Clear separation of permissions

## Comparison to Real Systems

### Similar to:

- **Kubernetes**: Controllers (action server) heal, chaos mesh injects faults
- **AWS Systems Manager**: Automation documents remediate, fault injection simulator breaks
- **Netflix**: Chaos Monkey breaks, auto-scaling groups heal

### Different from:

- Monolithic tools that do both chaos and healing (less common in production)

## Summary

The action server is now a **pure remediation service** with:

- ✅ Single responsibility: Fix target server
- ✅ No knowledge of chaos systems
- ✅ Clear, testable interface
- ✅ Production-ready architecture

The agent control plane orchestrates the **full lifecycle**:

1. Inject chaos (via chaos server)
2. Detect failure (via monitoring)
3. Remediate (via action server)
4. Stop chaos (via chaos server)
5. Verify recovery (via action server)

This is the **correct production architecture** for autonomous incident response systems.
