# Observability Improvements - Sanitized Health Endpoints

## Overview

The health endpoints have been updated to provide **symptoms instead of root causes**, making agent diagnosis more realistic and challenging.

## Changes Made

### 1. Health Endpoint (`/api/v1/health`) - Sanitized Errors

**Before:**

```json
{
  "services": {
    "database": {
      "error": "QueuePool limit of size 5 overflow 0 reached, connection timed out, timeout 3.00"
    }
  }
}
```

**After:**

```json
{
  "services": {
    "database": {
      "error": "Database connection timeout"
    }
  }
}
```

**Impact:** Agent must correlate this generic error with other metrics to diagnose pool exhaustion.

---

### 2. Pool Status Endpoint (`/api/v1/pool/status`) - Health Indicators

**Before:**

```json
{
  "pool_type": "QueuePool",
  "checked_out": 5,
  "status": "Pool size: 5  Connections in pool: 0  Current Overflow: 0  Current Checked out connections: 5"
}
```

**After:**

```json
{
  "pool_type": "QueuePool",
  "pool_size": 5,
  "pool_health": "critical",
  "pool_utilization": "high"
}
```

**Impact:** Agent sees health indicators but must investigate trends over time to understand the problem.

---

### 3. API Error Messages - Generic Responses

**Before:**

```json
{
  "detail": "DB pool exhausted (timeout)"
}
```

**After:**

```json
{
  "detail": "Service temporarily unavailable"
}
```

**Impact:** Agent must look at logs and metrics to understand why service is unavailable.

---

### 4. New Metrics Endpoint (`/api/v1/metrics`) - Rich Data

**Added comprehensive metrics endpoint:**

```json
{
  "timestamp": "2024-12-19T10:30:00.000Z",
  "application": {
    "avg_response_time_ms": 1250.45,
    "error_rate_percent": 67.8,
    "total_requests": 150,
    "request_sample_size": 100
  },
  "database": {
    "pool_type": "QueuePool",
    "pool_size": 5,
    "pool_health": "critical",
    "pool_utilization": "high"
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 60.3,
    "process_count": 125
  }
}
```

**Impact:** Agent must analyze multiple metrics together to build a complete picture:

- High error rate + critical pool health = pool exhaustion
- Rising response times + high utilization = degrading performance
- Pattern recognition across multiple data points

---

## Diagnosis Workflow Now Required

### Example: Pool Exhaustion Scenario

**What the agent sees:**

1. `/health` → "Database connection timeout"
2. `/metrics` → error_rate: 67%, avg_response_time: 1250ms, pool_health: "critical"
3. API calls → 503 "Service temporarily unavailable"

**What the agent must do:**

1. **Correlate signals**: Multiple 503s + timeout error + critical pool health
2. **Query RAG/docs**: "What causes database connection timeouts with high error rates?"
3. **Analyze trends**: Is error rate increasing? Response times rising?
4. **Diagnose**: Likely connection pool exhaustion
5. **Plan actions**: Check pool metrics, restart API, or scale pool size
6. **Verify**: Check if error rate drops and pool_health improves

---

## Why This Is Better

### Before (Too Easy):

- ❌ Error message says "pool exhausted" → agent just restarts
- ❌ Exact checked_out count visible → no analysis needed
- ❌ No diagnosis work required

### After (Realistic):

- ✅ Generic symptoms require correlation
- ✅ Health indicators need interpretation
- ✅ Must query multiple endpoints to build context
- ✅ Requires RAG lookup for understanding
- ✅ Forces proper incident investigation workflow

---

## Testing the Agent

When chaos server exhausts the pool:

```bash
POST http://chaos-server:8001/api/v1/break/db_pool
```

The agent should:

1. Detect degraded `/health` status
2. Query `/metrics` and see critical pool health
3. Correlate high error rate + timeout errors
4. Look up solution in RAG docs
5. Execute remediation (restart API / scale pool)
6. Verify metrics return to normal

---

## Logs Still Available

Full error details are still logged server-side:

```python
logger.error("DB_ERROR: QueuePool limit reached...")
```

This allows the agent to query logs as part of investigation, but forces it to actively look for details rather than getting them handed directly in API responses.

---

## Mimics Real Production Systems

This setup now mirrors how real monitoring works:

- **Datadog/New Relic**: Show aggregated metrics, not raw errors
- **Prometheus**: Provides utilization percentages, health states
- **Load balancers**: Return generic 503s, not detailed stack traces
- **Health checks**: Indicate healthy/unhealthy, not exact causes

The agent must **act like a real SRE** - investigating, correlating, and diagnosing rather than just reading obvious error messages.







