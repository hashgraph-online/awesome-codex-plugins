# SQL Safety Checklist

Domain-specific checklist for code that interacts with databases.

## Mandatory Checks

### Injection Prevention
- [ ] All user input is parameterized (no string interpolation in queries)
- [ ] ORM queries use parameter binding, not f-strings or `.format()`
- [ ] Raw SQL uses `?` or `$N` placeholders, never concatenation
- [ ] Dynamic table/column names are validated against an allowlist

### Migration Safety
- [ ] Migrations are reversible (both `up` and `down` defined)
- [ ] No `DROP TABLE` or `DROP COLUMN` without explicit data migration plan
- [ ] Large table migrations use batched operations (not full-table locks)
- [ ] Index creation uses `CONCURRENTLY` where supported (PostgreSQL)
- [ ] Migration tested on production-size dataset (not just empty dev DB)

### Query Performance
- [ ] Queries touching >1000 rows have appropriate indexes
- [ ] No `SELECT *` in production code (explicit column lists)
- [ ] N+1 queries identified and resolved (use `includes`/`preload`/`JOIN`)
- [ ] Pagination used for unbounded result sets
- [ ] `EXPLAIN ANALYZE` run on new queries touching large tables

### Transaction Safety
- [ ] Long-running transactions avoided (< 30s)
- [ ] Deadlock-prone operations use consistent lock ordering
- [ ] Retry logic for serialization failures / deadlocks
- [ ] Connection pool sized for peak concurrent transactions

### Data Integrity
- [ ] Foreign keys enforced at database level (not just application)
- [ ] NOT NULL constraints on required fields
- [ ] Unique constraints on business-key columns
- [ ] Check constraints on bounded values (enums, ranges)
- [ ] Soft deletes use `deleted_at` timestamp, not boolean

## When to Apply

Load this checklist when:
- Changed files contain SQL queries or ORM calls
- Migration files are in the changeset
- Database schema changes are proposed in the plan
- Code interacts with `database/sql`, `sqlx`, `gorm`, `sqlalchemy`, `activerecord`, `prisma`, `knex`, or similar
