# Long-Running Transactions Chaos: Usage Guide

Complete guide for using the long-running transactions chaos attack feature, including all commands, test endpoints, and troubleshooting.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Lock Types](#lock-types)
4. [Testing Impact](#testing-impact)
5. [Monitoring & Observability](#monitoring--observability)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Start a Table Lock Attack

```bash
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&duration_seconds=60"
```

Response:

```json
{
  "status": "started",
  "attack_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Attack Status

```bash
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}"
```

### Stop Attack

```bash
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/{attack_id}/stop"
```

---

## API Endpoints

### 1. Start Long-Running Transaction Attack

**Endpoint:** `POST /api/v1/break/long_transactions`

**Parameters:**

- `lock_type` (required): `table_lock` | `row_lock` | `advisory_lock`
- `target_database_url` (optional): Database URL (defaults to settings)
- `duration_seconds` (optional): Auto-rollback after N seconds (1-3600, default: None = manual)
- `target_table` (optional): Table name for `table_lock`/`row_lock` (default: "items")
- `lock_count` (optional): Number of locks for `row_lock`/`advisory_lock` (1-10000, default: 10)
- `advisory_lock_id` (optional): Specific advisory lock ID (default: auto-generated)

**Examples:**

```bash
# Table lock - blocks all operations on items table for 60 seconds
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&duration_seconds=60"

# Row lock - locks 50 rows for 120 seconds
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=row_lock&target_table=items&lock_count=50&duration_seconds=120"

# Advisory lock - blocks advisory lock attempts for 180 seconds
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=advisory_lock&lock_count=1&advisory_lock_id=12345&duration_seconds=180"

# Manual rollback (no duration)
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items"

# Custom database URL
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&target_database_url=postgresql://user:pass@host:5432/db"
```

### 2. Get Attack Status

**Endpoint:** `GET /api/v1/break/long_transactions/{attack_id}`

**Example:**

```bash
curl "http://localhost:8080/api/v1/break/long_transactions/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "running",
  "lock_type": "table_lock",
  "target_table": "items",
  "backend_pid": 12345,
  "blocked_count": 3,
  "blocked_queries": [
    {
      "blocked_pid": 12346,
      "blocked_user": "postgres",
      "blocked_query": "SELECT * FROM items",
      "blocked_state": "active",
      "blocking_query": "LOCK TABLE items IN ACCESS EXCLUSIVE MODE"
    }
  ],
  "elapsed_seconds": 15.5,
  "started_at": 1704067200.0,
  "lock_acquired_at": 1704067201.0
}
```

### 3. Stop/Rollback Attack

**Endpoint:** `POST /api/v1/break/long_transactions/{attack_id}/stop`

**Parameters:**

- `force_kill` (optional): `true` to force kill backend process if graceful rollback fails

**Examples:**

```bash
# Graceful rollback
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/550e8400-e29b-41d4-a716-446655440000/stop"

# Force kill if graceful rollback fails
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/550e8400-e29b-41d4-a716-446655440000/stop?force_kill=true"
```

**Response:**

```json
{
  "status": "rolled_back",
  "attack_id": "550e8400-e29b-41d4-a716-446655440000",
  "elapsed_seconds": 25.3
}
```

---

## Lock Types

### 1. Table Lock (`table_lock`)

**What it does:**

- Acquires `ACCESS EXCLUSIVE` lock on the specified table
- Blocks ALL operations (SELECT, INSERT, UPDATE, DELETE, etc.)
- Most aggressive lock type

**Use case:** Testing how your application handles complete table unavailability

**Example:**

```bash
# Start attack
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&duration_seconds=60"

# Test impact (this will hang)
curl "http://localhost:8000/api/v1/test/items"
```

### 2. Row Lock (`row_lock`)

**What it does:**

- Uses `SELECT FOR UPDATE` to lock specific rows
- Blocks updates to those rows only
- Other rows remain accessible

**Use case:** Testing row-level contention and update blocking

**Example:**

```bash
# Start attack (locks 50 rows)
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=row_lock&target_table=items&lock_count=50&duration_seconds=120"

# Test impact (update will hang if trying to update locked rows)
curl "http://localhost:8000/api/v1/test/items/update"
```

### 3. Advisory Lock (`advisory_lock`)

**What it does:**

- Uses PostgreSQL `pg_advisory_lock()` function
- Blocks other sessions from acquiring the same advisory lock
- Application-level locking mechanism

**Use case:** Testing advisory lock contention in distributed systems

**Example:**

```bash
# Start attack with lock_id 12345
curl -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=advisory_lock&lock_count=1&advisory_lock_id=12345&duration_seconds=180"

# Test impact (will be blocked)
curl "http://localhost:8000/api/v1/test/advisory-lock?lock_id=12345"
```

---

**Note:** For connection pool exhaustion testing, use the `/break/db_pool` endpoint instead, which is specifically designed for that purpose.

---

## Testing Impact

### Target Server Test Endpoints

The target server provides test endpoints to verify lock impact:

#### 1. Test Table Lock Impact

```bash
# This queries the items table - will be blocked by table_lock
curl "http://localhost:8000/api/v1/test/items"
```

**Expected behavior with table_lock:**

- Request hangs or times out
- Returns `"status": "blocked"` if lock detected

#### 2. Test Row Lock Impact

```bash
# This updates rows - will be blocked by row_lock on those rows
curl "http://localhost:8000/api/v1/test/items/update"
```

**Expected behavior with row_lock:**

- Request hangs if trying to update locked rows
- Returns `"status": "blocked"` if lock detected

#### 3. Test Advisory Lock Impact

```bash
# This attempts to acquire advisory lock - will be blocked if lock_id matches
curl "http://localhost:8000/api/v1/test/advisory-lock?lock_id=12345"
```

**Expected behavior with advisory_lock:**

- Returns `"lock_acquired": false` if lock is held
- Returns `"status": "blocked"` if lock detected

### Complete Testing Workflow

```bash
# Terminal 1: Start table lock attack
ATTACK_ID=$(curl -s -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items" | jq -r '.attack_id')
echo "Attack ID: $ATTACK_ID"

# Terminal 2: Check status
curl "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID" | jq

# Terminal 3: Test impact (this will hang)
curl "http://localhost:8000/api/v1/test/items"

# Terminal 4: Check blocked queries count
curl "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID" | jq '.blocked_count'

# Terminal 1: Stop attack
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID/stop"
```

---

## Monitoring & Observability

### Check Attack Status

```bash
# Get full attack details
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq

# Watch status in real-time (updates every second in UI)
watch -n 1 'curl -s "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq ".state, .blocked_count, .elapsed_seconds"'
```

### Monitor Blocked Queries

```bash
# Get list of blocked queries
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq '.blocked_queries'

# Count blocked queries
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq '.blocked_count'
```

### Check Target Server Health

```bash
# Health check (may show database errors)
curl "http://localhost:8000/api/v1/health" | jq

# Pool status
curl "http://localhost:8000/api/v1/pool/status" | jq

# Metrics
curl "http://localhost:8000/api/v1/metrics" | jq
```

### Direct PostgreSQL Queries

If you have `psql` access:

```sql
-- See the long-running transaction
SELECT
    pid,
    now() - xact_start as transaction_duration,
    state,
    query
FROM pg_stat_activity
WHERE state = 'active in transaction'
ORDER BY xact_start;

-- See blocked queries
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.query AS blocked_query,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.query AS blocking_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check idle-in-transaction connections
SELECT pid, now() - state_change as idle_duration, query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY state_change;
```

### Alembic Database Migration Commands

**Prerequisites:** Navigate to `target_server/backend` directory

```bash
cd target_server/backend
```

#### Check Migration Status

```bash
# Show current migration version in database
alembic current

# Show migration history
alembic history

# Show detailed history with revisions
alembic history --verbose

# Check if database is up to date
alembic check
```

#### Apply Migrations

```bash
# Apply all pending migrations (upgrade to latest)
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade 001

# Apply next migration only
alembic upgrade +1

# Apply multiple migrations
alembic upgrade +2
```

#### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade 001

# Rollback to base (remove all migrations)
alembic downgrade base

# Rollback multiple migrations
alembic downgrade -2
```

#### Create New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (manual)
alembic revision -m "description of changes"

# Create migration with specific revision ID
alembic revision -m "description" --rev-id=002
```

#### View Migration Details

```bash
# Show current head revision
alembic show head

# Show specific revision details
alembic show 001

# Show SQL that would be executed (dry run)
alembic upgrade head --sql

# Show SQL for downgrade
alembic downgrade -1 --sql
```

#### Migration Scripts

```bash
# Run migrations using Python script (if available)
python alembic_upgrade.py

# Or directly with alembic command
alembic upgrade head
```

#### Common Workflow for Long-Transaction Testing

```bash
# 1. Ensure database is set up
cd target_server/backend

# 2. Check current state
alembic current

# 3. Apply all migrations to create tables
alembic upgrade head

# 4. Verify tables exist
psql "postgresql://postgres:password@localhost:5432/target_server" -c "\dt"

# 5. Now you can test long transactions
# (Tables like 'items' should now exist)
```

#### Troubleshooting Migrations

```bash
# If migration fails, check current state
alembic current

# View migration file to understand what it does
cat alembic/versions/001_initial_migration.py

# Check for migration conflicts
alembic history

# If stuck, you can manually fix and continue
# (Use with caution - understand what you're doing)
alembic stamp head  # Mark current state as head without running migrations
```

#### Reset Database (Nuclear Option)

```bash
# WARNING: This will delete all data!

# Rollback all migrations
alembic downgrade base

# Re-apply all migrations
alembic upgrade head

# Or if using Docker, reset the volume
docker-compose down -v
docker-compose up -d
cd target_server/backend
alembic upgrade head
```

---

## Troubleshooting

### Attack Not Starting

**Problem:** Attack returns but state stays "starting"

**Solutions:**

```bash
# Check if database is accessible
psql "postgresql://postgres:password@localhost:5432/target_server" -c "SELECT 1"

# Check attack status for errors
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq '.error'

# Verify database URL in settings
curl "http://localhost:8080/api/v1/health"
```

### Attack Not Blocking Queries

**Problem:** Attack is running but no queries are blocked

**Solutions:**

```bash
# Verify lock type and table name match
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq '.lock_type, .target_table'

# Ensure you're testing the correct table
# For table_lock: use /test/items
# For row_lock: use /test/items/update
# For advisory_lock: use /test/advisory-lock with matching lock_id

# Check if table exists
curl "http://localhost:8000/api/v1/test/items"
```

### Can't Stop Attack

**Problem:** Stop endpoint doesn't work

**Solutions:**

```bash
# Try graceful rollback first
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/{attack_id}/stop"

# If that fails, force kill
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/{attack_id}/stop?force_kill=true"

# Check attack state
curl "http://localhost:8080/api/v1/break/long_transactions/{attack_id}" | jq '.state'

# If still stuck, manually kill PostgreSQL backend
# Get backend_pid from attack status, then:
psql "postgresql://postgres:password@localhost:5432/target_server" -c "SELECT pg_terminate_backend({backend_pid})"
```

### Table Doesn't Exist

**Problem:** Error: "relation 'items' does not exist"

**Solutions:**

```bash
# Option 1: Let test endpoint create it automatically
curl "http://localhost:8000/api/v1/test/items"

# Option 2: Run migrations
cd target_server/backend
alembic upgrade head

# Option 3: Create manually
psql "postgresql://postgres:password@localhost:5432/target_server" -c "CREATE TABLE items (id SERIAL PRIMARY KEY, name VARCHAR(255), description TEXT);"
```

### Connection Pool Exhausted

**Problem:** All requests timeout, even without attack

**Solutions:**

```bash
# Check pool status
curl "http://localhost:8000/api/v1/pool/status" | jq

# Restart target server to clear connections
# If using Docker:
docker-compose restart api

# If running locally:
# Stop and restart the FastAPI server
```

---

## Example Scenarios

### Scenario 1: Test Table Lock Impact

```bash
# 1. Start table lock attack
ATTACK_ID=$(curl -s -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=table_lock&target_table=items&duration_seconds=60" | jq -r '.attack_id')

# 2. Verify attack is running
curl "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID" | jq '.state'

# 3. Test impact (in separate terminal - this will hang)
curl "http://localhost:8000/api/v1/test/items"

# 4. Check blocked queries
curl "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID" | jq '.blocked_count'

# 5. Stop attack early
curl -X POST "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID/stop"
```

### Scenario 2: Test Connection Pool Exhaustion

**Note:** Use the DB Pool Exhaustion Attack (`/break/db_pool`) for this scenario instead of long transactions.

```bash
# Use the dedicated pool exhaustion endpoint
curl -X POST "http://localhost:8080/api/v1/break/db_pool?connections=20&hold_seconds=60"

# Check pool status
curl "http://localhost:8000/api/v1/pool/status" | jq
```

### Scenario 3: Test Row Lock Contention

```bash
# 1. Start row lock attack
ATTACK_ID=$(curl -s -X POST "http://localhost:8080/api/v1/break/long_transactions?lock_type=row_lock&target_table=items&lock_count=10&duration_seconds=120" | jq -r '.attack_id')

# 2. Try to update rows (will be blocked)
curl "http://localhost:8000/api/v1/test/items/update"

# 3. Monitor blocked queries
watch -n 1 'curl -s "http://localhost:8080/api/v1/break/long_transactions/$ATTACK_ID" | jq ".blocked_count, .blocked_queries[].blocked_query"'
```

---

## Best Practices

1. **Always set duration_seconds** for automated testing to prevent leaving attacks running
2. **Monitor blocked_count** to verify the attack is working
3. **Use force_kill sparingly** - try graceful rollback first
4. **Test one lock type at a time** to isolate effects
5. **Clean up attacks** after testing to avoid resource leaks
6. **Check target server health** before and after attacks
7. **Use the UI** for easier monitoring and control

---

## UI Usage

The Chaos Server frontend provides a UI for managing long-running transaction attacks:

1. Navigate to **DB Chaos** page
2. Scroll to **Long-Running Transactions Attack** section
3. Select lock type and configure parameters
4. Click **Start Long Transaction**
5. Monitor status, backend PID, and blocked queries count
6. Use **Rollback Transaction** or **Force Kill** to stop

The UI automatically polls attack status every second and displays:

- Attack state
- Backend PID
- Blocked queries count
- Full attack details in JSON format
