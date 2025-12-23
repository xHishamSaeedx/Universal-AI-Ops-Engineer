[4 tools called]

Based on your project's documentation, let me explain these two chaos engineering scenarios in simple but detailed terms.

## Failed Migrations

### What it is (in simple terms)

Failed migrations are like trying to renovate your house while people are still living in it. Your database schema needs updates (like adding rooms or changing layouts), but the renovation process breaks down mid-way, leaving your "house" in a messy, unusable state.

### How they happen in actual servers

In real production systems, failed migrations typically occur when:

1. **Schema conflicts** - Multiple developers try to change the same database table simultaneously during deployment
2. **Data integrity issues** - The migration tries to change data in ways that violate database rules (like trying to make a column required when it contains empty values)
3. **Lock timeouts** - The migration tries to modify millions of records but gets stuck waiting for other database operations to finish
4. **Missing prerequisites** - Code changes are deployed that depend on database changes that haven't run yet
5. **Environment differences** - Migration works fine in development testing but fails in production due to different data volumes or configurations

Your chaos server simulates this by manipulating the `alembic_version` table (which tracks what migrations have been applied) to create inconsistent states.

### Consequences

**Immediate impacts:**

- **Service crashes** - Applications can't start because the database structure doesn't match what the code expects
- **Deployment failures** - CI/CD pipelines halt, blocking new feature releases
- **Data access errors** - Queries fail because tables/columns are missing or renamed
- **Connection problems** - Apps can't connect to databases in inconsistent states

**Longer-term effects:**

- **Manual intervention requirements** - Teams need emergency procedures to fix database states
- **Lost confidence** - Developers become afraid to make necessary schema changes
- **Technical debt** - Partial migrations create permanent inconsistencies across environments

## Long Transactions

### What it is (in simple terms)

Long transactions are like someone hogging the only bathroom in a busy restaurant during dinner rush. A database transaction starts (like entering the bathroom) but takes forever to finish, blocking everyone else who needs to use the same resources.

### How they happen in actual servers

In real systems, long transactions occur when:

1. **Poor transaction boundaries** - Code opens a database transaction but doesn't close it properly, often due to exceptions or forgotten commits
2. **Complex operations inside transactions** - Business logic that takes minutes to complete (like processing large datasets) runs within a single transaction scope
3. **N+1 query problems** - Code loops through records and opens/closes transactions repeatedly instead of batching operations
4. **Missing timeouts** - Transactions have no time limits, so they can run indefinitely
5. **Lock escalation** - Small row-level locks grow into table-level locks that block everything

Your chaos server creates these by acquiring different types of database locks:

- **Table locks** - Blocks all operations on entire tables
- **Row locks** - Blocks updates to specific records
- **Advisory locks** - Application-level locks that coordinate between processes

### Consequences

**Immediate impacts:**

- **Query timeouts** - Other operations wait too long and give up
- **Connection pool exhaustion** - All available database connections get stuck waiting
- **Deadlock errors** - Competing transactions get permanently stuck waiting for each other
- **Service degradation** - Everything slows down as requests queue behind locks
- **Application failures** - HTTP 503 errors when services can't get database access

**Longer-term effects:**

- **Performance degradation** - Systems become gradually slower over time
- **Debugging nightmares** - Hard to trace why everything is slow
- **Resource waste** - CPU/memory get consumed by blocked operations
- **User frustration** - Slow or unresponsive features drive users away

Both scenarios teach teams about the importance of transaction management, proper deployment processes, and monitoring database health - critical skills for maintaining reliable production systems.
