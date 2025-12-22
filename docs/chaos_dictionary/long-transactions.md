# Long-Running Transactions: DevOps Chaos Engineering Scenario

## 1. Definition

Long-running transactions occur when database transactions remain open for extended periods, holding locks and blocking other operations. These transactions can cause query timeouts, deadlocks, connection pool exhaustion, and severe performance degradation.

### Types of Long-Running Transactions

- **Table Locks**: ACCESS EXCLUSIVE locks that block all operations on a table
- **Row Locks**: SELECT FOR UPDATE locks that block updates to specific rows
- **Advisory Locks**: Application-level locks using PostgreSQL advisory lock functions

## 2. Symptoms

### Application-Level Symptoms

- **Query Timeouts**: Operations timing out while waiting for locks
- **Deadlock Errors**: Transaction deadlock exceptions in application logs
- **Connection Pool Exhaustion**: All connections held by idle transactions
- **Latency Spikes**: Slow response times as queries queue behind locks
- **HTTP 503 Errors**: Service unavailable due to connection/timeout issues

### Database-Level Symptoms

- **Lock Contention**: Queries waiting for locks in `pg_locks` and `pg_stat_activity`
- **Transaction Backlog**: Growing queue of blocked queries
- **High Connection Count**: Many connections stuck in "idle in transaction" state
- **Lock Wait Times**: Increasing `wait_time` metrics in `pg_stat_activity`
- **Query Queue**: Queries stuck in "waiting" state

### Operational Symptoms

- **Performance Degradation**: Gradual slowdown of database operations
- **Alert Fatigue**: Multiple timeout and lock-related alerts
- **User Complaints**: Reports of slow or unresponsive features
- **Cascade Failures**: One blocked query causing chain reactions
- **Resource Exhaustion**: CPU/memory spikes from blocked queries accumulating

## 3. Consequences

### Immediate Business Impact

- **Service Degradation**: Slow or unresponsive application features
- **Transaction Failures**: Critical operations timing out or failing
- **Data Inconsistency Risk**: Long transactions holding locks increase conflict potential
- **User Experience Impact**: Poor responsiveness leading to user frustration
- **Revenue Loss**: E-commerce transactions failing during checkout

### Long-term Technical Debt

- **Connection Pool Misconfiguration**: Reveals inadequate pool sizing
- **Transaction Management Issues**: Poor transaction boundaries in application code
- **Lock Escalation Patterns**: Unoptimized locking strategies
- **Monitoring Gaps**: Lack of visibility into transaction duration and locks
- **Operational Complexity**: Difficult diagnosis and resolution procedures

### Operational Consequences

- **On-Call Overhead**: Emergency response to performance incidents
- **Debugging Complexity**: Difficult to trace root cause of lock contention
- **Incident Duration**: Long resolution times as teams diagnose lock issues
- **Team Confidence Impact**: Reduced trust in system reliability
- **SLA Violations**: Service level agreements not met due to degraded performance

## 4. Causes

### Application Development Issues

- **Poor Transaction Boundaries**: Transactions opened too early and closed too late
- **Missing Transaction Cleanup**: Exceptions not properly rolling back transactions
- **N+1 Query Problems**: Opening transactions per iteration in loops
- **Long-Running Business Logic**: Complex operations executed within transaction scope
- **Missing Timeout Configuration**: No transaction timeout limits

### Database Design Issues

- **Inefficient Locking Strategies**: Table-level locks instead of row-level
- **Missing Indexes**: Full table scans requiring table locks
- **Large Batch Operations**: Bulk updates without chunking
- **Unoptimized Queries**: Slow queries holding locks longer than necessary
- **Lock Escalation**: Row locks escalating to table locks

### Infrastructure and Configuration

- **Connection Pool Settings**: Insufficient pool size or timeout configuration
- **Transaction Isolation Levels**: Higher isolation levels causing longer lock holds
- **Missing Lock Monitoring**: No visibility into lock contention
- **Resource Constraints**: CPU/memory limits causing slow query execution
- **Network Latency**: Slow network increasing transaction duration

### Tool and Process Failures

- **ORM Configuration Issues**: ORM holding transactions open longer than needed
- **Connection Leaks**: Connections not properly released back to pool
- **Background Job Locking**: Scheduled jobs holding locks during execution
- **Monitoring Blind Spots**: Long transactions not detected until they cause issues
- **Missing Alerting**: No alerts for transaction duration thresholds

## 5. Immediate Quick Solutions

### Emergency Mitigation

```bash
# 1. Identify long-running transactions
psql -h localhost -U postgres -d target_server -c "
SELECT pid, now() - xact_start as duration, state, query
FROM pg_stat_activity
WHERE state = 'active in transaction'
  AND now() - xact_start > interval '30 seconds';"

# 2. Kill specific blocking transactions
psql -h localhost -U postgres -d target_server -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid = <blocking_pid>;"

# 3. Check for blocked queries
psql -h localhost -U postgres -d target_server -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;"
```

### Temporary Workarounds

- **Connection Pool Restart**: Restart application to clear idle transactions
- **Query Cancellation**: Cancel long-running queries manually
- **Lock Release**: Force rollback of blocking transactions
- **Read Replicas**: Route read queries to replicas to reduce contention
- **Graceful Degradation**: Disable non-critical features to reduce load

### Quick Diagnosis Commands

```bash
# Check active long transactions
SELECT pid, now() - xact_start as duration, state, query
FROM pg_stat_activity
WHERE state = 'active in transaction'
ORDER BY xact_start;

# Find blocking queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocking_locks.pid AS blocking_pid,
    blocked_activity.query AS blocked_query,
    blocking_activity.query AS blocking_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;

# Monitor lock waits
SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';
```

## 6. Different Ways to Diagnose Root Cause

### Database State Analysis

```sql
-- Check long-running transactions
SELECT
    pid,
    now() - xact_start as transaction_duration,
    now() - query_start as query_duration,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE state = 'active in transaction'
ORDER BY xact_start;

-- Analyze lock contention
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_query,
    blocking_activity.query AS blocking_query,
    blocked_locks.locktype,
    blocked_locks.relation::regclass AS locked_table
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check idle-in-transaction connections
SELECT pid, now() - state_change as idle_duration, query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY state_change;
```

### Application Code Analysis

```python
# Check for transaction boundary issues
def check_transaction_patterns():
    # Look for:
    # 1. Transactions opened but not closed
    # 2. Exception handling without rollback
    # 3. Long-running operations in transaction scope
    # 4. Missing transaction timeouts

    patterns = [
        'BEGIN.*SELECT.*(?!COMMIT|ROLLBACK)',
        'db.begin()\n.*sleep|time.sleep',
        'with transaction:\n.*time.sleep',
    ]

    for pattern in patterns:
        find_violations(pattern)

# Identify connection leaks
def detect_connection_leaks():
    # Monitor connection pool utilization
    # Track connection checkout duration
    # Alert on connections held > threshold
    pass
```

### Log Analysis and Monitoring

```bash
# Search for timeout errors
grep -r "timeout" /var/log/application/ | grep -i "transaction\|lock"

# Check for deadlock errors
grep -r "deadlock" /var/log/application/

# Monitor transaction duration in application logs
tail -f /var/log/application/app.log | grep "transaction_duration"

# Database log analysis
grep "duration:" /var/log/postgresql/postgresql-*.log | \
    awk '{if ($NF > 30000) print}'  # Transactions > 30 seconds
```

### Environment Comparison

```bash
# Compare transaction timeout settings
psql -c "SHOW statement_timeout;"
psql -c "SHOW lock_timeout;"
psql -c "SHOW idle_in_transaction_session_timeout;"

# Compare connection pool settings across environments
diff dev.env prod.env | grep -i pool\|timeout

# Check for configuration differences
grep -r "transaction" config/ | diff dev.config prod.config
```

### Performance Monitoring

```sql
-- Monitor transaction statistics
SELECT
    datname,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database
WHERE datname = 'target_server';

-- Check lock statistics
SELECT
    locktype,
    mode,
    count(*) as lock_count
FROM pg_locks
GROUP BY locktype, mode
ORDER BY lock_count DESC;
```

### Automated Diagnostic Tools

```python
def diagnose_long_transactions():
    diagnostics = {
        'long_transactions': check_long_running_transactions(),
        'blocked_queries': check_blocked_queries(),
        'lock_contention': analyze_lock_contention(),
        'idle_connections': check_idle_in_transaction(),
        'connection_pool': check_pool_utilization(),
        'transaction_timeouts': check_timeout_settings()
    }

    # Generate diagnostic report
    report = generate_diagnostic_report(diagnostics)

    # Suggest remediation steps
    recommendations = generate_recommendations(diagnostics)

    return report, recommendations

def check_long_running_transactions():
    """Identify transactions running longer than threshold."""
    query = """
        SELECT pid, now() - xact_start as duration, state, query
        FROM pg_stat_activity
        WHERE state = 'active in transaction'
          AND now() - xact_start > interval '30 seconds'
        ORDER BY xact_start;
    """
    return execute_query(query)

def check_blocked_queries():
    """Find queries blocked by locks."""
    query = """
        SELECT blocked_locks.pid AS blocked_pid,
               blocking_locks.pid AS blocking_pid,
               blocked_activity.query AS blocked_query
        FROM pg_locks blocked_locks
        JOIN pg_stat_activity blocked_activity
            ON blocked_activity.pid = blocked_locks.pid
        JOIN pg_locks blocking_locks
            ON blocking_locks.locktype = blocked_locks.locktype
            AND blocking_locks.pid != blocked_locks.pid
        WHERE NOT blocked_locks.granted;
    """
    return execute_query(query)
```

### Chaos Engineering Validation

```python
# Simulate long-running transactions for testing
def simulate_long_transaction_chaos():
    scenarios = [
        'table_lock_blocking_all_queries',
        'row_lock_blocking_updates',
        'advisory_lock_contention',
        'cascading_lock_deadlock'
    ]

    for scenario in scenarios:
        run_chaos_experiment(scenario)
        validate_recovery_procedures(scenario)
        document_learned_patterns(scenario)
```

## 7. Chaos Server Implementation

### Endpoint: `/api/v1/break/long_transactions`

#### Starting a Long-Running Transaction Attack

```bash
# Table lock (blocks all operations on a table)
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&duration_seconds=60"

# Row lock (blocks updates to specific rows)
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=row_lock&target_table=items&lock_count=50&duration_seconds=120"

# Advisory lock (blocks other advisory lock attempts)
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=advisory_lock&lock_count=1&advisory_lock_id=12345&duration_seconds=180"
```

#### Parameters

- `lock_type` (required): `table_lock` | `row_lock` | `advisory_lock`
- `duration_seconds` (optional): Auto-rollback after N seconds (default: None = manual rollback)
- `target_table` (optional): Table name for table_lock/row_lock (default: "items")
- `lock_count` (optional): Number of locks for row_lock/advisory_lock (default: 10)
- `advisory_lock_id` (optional): Specific advisory lock ID (default: auto-generated)
- `target_database_url` (optional): Override default database URL

#### Checking Attack Status

```bash
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}"
```

Response includes:

- `state`: running | completed | rolled_back | failed
- `backend_pid`: PostgreSQL backend process ID
- `lock_type`: Type of lock created
- `blocked_count`: Number of queries currently blocked
- `blocked_queries`: Details of blocked queries
- `elapsed_seconds`: How long the attack has been running

#### Stopping/Rolling Back Attack

```bash
# Graceful rollback
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/{attack_id}/stop"

# Force kill if graceful rollback fails
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/{attack_id}/stop?force_kill=true"
```

## 8. Remediation Actions

### Automatic Remediation

1. **Kill Blocking Transaction**: Terminate the backend PID holding locks
2. **Connection Pool Restart**: Restart application to clear idle transactions
3. **Query Cancellation**: Cancel long-running queries automatically
4. **Lock Release**: Force rollback of blocking transactions
5. **Configuration Update**: Adjust timeout settings to prevent future issues

### Manual Remediation Steps

1. Identify the blocking transaction PID
2. Check what queries are being blocked
3. Attempt graceful cancellation (pg_cancel_backend)
4. If necessary, force termination (pg_terminate_backend)
5. Verify locks are released
6. Monitor for recurrence

This comprehensive approach to long-running transactions provides DevOps teams with the knowledge and tools to prevent, diagnose, and recover from transaction-related incidents while building resilient database operations.
