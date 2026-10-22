---
name: data-migration
description: Hard gate before any database schema change or data transformation in production. Requires a written migration plan with rollback strategy, dry run, and verification steps before execution. Prevents data loss, downtime, and irreversible schema changes.
---

# Data Migration

## The Law

```
EVERY MIGRATION NEEDS A ROLLBACK.
A migration without a rollback plan is a one-way door.
Before you open it, know how to close it.
```

## When to Use

Use this skill before:
- Any `ALTER TABLE` in production
- Any column rename, type change, or removal
- Any large `UPDATE` or `DELETE` (more than 1000 rows)
- Any index creation on a large table
- Any data backfill or transformation script

## The Migration Process

### Step 1: Classify the Migration

| Type | Risk | Strategy |
|------|------|---------|
| Additive (new table, new nullable column) | Low | Single deploy |
| Non-breaking change (add index, add constraint) | Low–Medium | Verify impact first |
| Column rename or type change | High | Multi-phase deploy |
| Column or table removal | High | Multi-phase deploy |
| Large data backfill (>100k rows) | Medium | Batched, off-peak |
| Destructive (DROP TABLE, DELETE) | Critical | Backup + explicit approval |

### Step 2: Write the Migration Plan

Save to `docs/migrations/YYYY-MM-DD-description.md`:

```markdown
# Migration: [Title]

## Summary
[What changes and why]

## Risk Level
[Low / Medium / High / Critical]

## Migration Steps

### UP (apply)
\```sql
-- Step 1: Add new column (nullable — safe, no lock)
ALTER TABLE orders ADD COLUMN discount_amount NUMERIC(10,2);

-- Step 2: Backfill (batched — see script)
-- Run: scripts/migrations/backfill-discount.sql

-- Step 3: Add NOT NULL constraint after backfill
ALTER TABLE orders ALTER COLUMN discount_amount SET NOT NULL;
\```

### DOWN (rollback)
\```sql
ALTER TABLE orders DROP COLUMN IF EXISTS discount_amount;
\```

## Rollback Plan
[How to revert if something goes wrong — step by step]

## Estimated Duration
[How long will the migration take? Any locking risk?]

## Verification
- [ ] Row count before: SELECT COUNT(*) FROM orders;
- [ ] Row count after matches
- [ ] Sample rows spot-checked: SELECT * FROM orders LIMIT 10;
- [ ] Application queries tested against migrated schema
- [ ] No errors in application logs after deploy
```

### Step 3: Zero-Downtime Patterns

**Column rename** — never rename directly; multi-phase:
```
Phase 1: Add new column (old and new both exist)
Phase 2: Deploy app that writes to BOTH columns, reads from old
Phase 3: Backfill new column from old
Phase 4: Deploy app that writes to BOTH, reads from new
Phase 5: Drop old column
```

**Type change** — same multi-phase approach; never `ALTER COLUMN TYPE` on large tables in production directly.

**Index creation on large table** — always `CREATE INDEX CONCURRENTLY`:
```sql
-- [INVALID] — takes full table lock
CREATE INDEX idx_orders_user ON orders(user_id);

-- [VALID] — non-blocking on PostgreSQL
CREATE INDEX CONCURRENTLY idx_orders_user ON orders(user_id);
```

**Large backfill** — never in one transaction; batch it:
```sql
-- Process in batches of 1000 rows until done
DO $$
DECLARE
  batch_size INT := 1000;
  rows_updated INT;
BEGIN
  LOOP
    UPDATE orders
    SET discount_amount = 0
    WHERE discount_amount IS NULL
    LIMIT batch_size;

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;
    PERFORM pg_sleep(0.1);  -- yield between batches
  END LOOP;
END $$;
```

### Step 4: Pre-Migration Checklist

Before executing in production:

- [ ] Migration tested in staging with production-sized dataset
- [ ] DOWN migration tested — rollback actually works
- [ ] Row counts recorded (before state documented)
- [ ] Backup taken or verified recent backup exists
- [ ] Maintenance window announced if locking is expected
- [ ] Application can tolerate both old and new schema simultaneously (for multi-phase migrations)
- [ ] Monitoring alerts active during migration

### Step 5: Execute

```bash
# Dry run first (PostgreSQL)
psql $DATABASE_URL --dry-run -f migration.sql

# Real run with timing
psql $DATABASE_URL -f migration.sql --echo-all

# Check for locks during execution
SELECT pid, query, state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE state != 'idle';
```

### Step 6: Verify

```sql
-- Row count matches expectations
SELECT COUNT(*) FROM affected_table;

-- Sample spot-check
SELECT * FROM affected_table LIMIT 20;

-- No NULL where NOT NULL expected
SELECT COUNT(*) FROM affected_table WHERE new_column IS NULL;

-- No application errors in logs for 10 minutes post-migration
```

## Rollback Decision Tree

```
Migration complete?
  └── No errors in monitoring for 10 minutes? → DONE
  └── Errors found?
      ├── Can app tolerate the error state? → Fix forward (hotfix)
      └── Cannot tolerate? → ROLLBACK IMMEDIATELY
          ├── Run DOWN migration
          ├── Verify application recovers
          └── Document in post-mortem
```

## Hard Rules

- **Never DROP a column in the same deploy as the last code that reads it** — always separate by at least one deploy
- **Never run destructive migrations (DROP TABLE, DELETE) without an explicit human approval step** — not just a code review
- **Never skip the DOWN migration** — "we can recreate it" is not a rollback strategy
- **Never migrate in peak traffic hours** — schedule for the lowest-traffic window
