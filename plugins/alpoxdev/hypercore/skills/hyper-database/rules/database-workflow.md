# Database Workflow

Use this rule once the engines are routed. It picks the mode, fixes the phases of each mode, gates side effects, and names the report path.

## 1. Mode Selection

| Request shape | Mode | Edits files |
|---|---|---|
| "설계해줘", "design the schema", a new service, a new collection or key space | design | yes, when the repository exists and the user did not say report only |
| "점검", "리뷰", "audit", "is this safe", or an upstream "audit only; do not edit" | review | no target files; the report under `.hyper/database/` is the only write |
| "계획 봐줘", "explain this plan", "why is this query slow" with no request to change anything | review, with the plan reading of tune (no index or query edits) | no target files; the report only |
| "마이그레이션 써줘", "add a column", "rename", "backfill", "fix this migration" | change | yes |
| "느려", "slow", "timeout", "lock wait", "deadlock", "hot key", "throttled", "index 잡아줘" | tune | yes, for index and query files |
| "백업", "복구", "리플리카", "failover", "pooling", "upgrade", "보안", "모니터링", "capacity" | operate | configuration and runbook files only |
| "뭐 쓸까", "which database", "Redis vs Valkey", "single-table or not" | choose | no |

- When a request carries two shapes ("설계하고 마이그레이션까지"), run them in this order: choose, design, change, tune, operate. Review never combines with an editing mode in one run.
- "점검만", "report only", "do not edit", or an upstream audit request always wins: the mode becomes review.

## 2. Design Inputs

Collect these before any design, index, or engine decision. Read them from files first (API routes, query code, existing schema, issue text, load numbers), then ask one batched question for the rest.

| Input | Why it decides |
|---|---|
| Access patterns: each read and write, its filter, sort, and frequency | Keys, indexes, and NoSQL layouts are derived from them |
| Volume and growth: rows or items now, per day, retention | Partitioning, TTL, and index cost |
| Invariants: what must never be violated (unique email, balance >= 0, one active plan) | Constraints and transaction boundaries |
| Consistency need: read-your-writes, strong, or eventual is fine | Engine, replica reads, and cache design |
| Latency and availability targets, RPO and RTO | Topology, backup method, and failover |
| Tenancy and data sensitivity (PII, payment, regulated region) | Isolation model, encryption, retention, and deletion |
| Platform constraints: managed service, existing engine, team skill, budget | The choice set |

When the user gives no answer and one is needed, proceed with a stated assumption in the report's `가정` list, never a silent guess.

## 3. Phases per Mode

| Mode | Phases |
|---|---|
| design | inputs -> entity and access-pattern table -> engine fit check -> logical model -> physical model (types, keys, constraints, indexes, partitioning or key layout) -> DDL or schema files -> operations section -> verify -> report |
| review | inputs from files -> rule pass by ID (engine-neutral, then engine guide) -> severity ranking -> report with fixes, no edits |
| change | current schema and data volume -> change classified by `rules/schema-changes.md` §2 -> expand/contract steps -> migration files -> lint or dry run -> rollback plan -> report |
| tune | the slow statement and its plan or metric -> cause by rule ID -> one change at a time (index, query rewrite, configuration) -> re-measure -> keep or revert -> report |
| operate | current topology and settings -> gaps against `rules/operations.md` -> configuration or runbook changes -> verification steps -> report |
| choose | inputs -> candidate engines that meet hard constraints -> comparison table on access fit, consistency, operations cost, ecosystem, license -> recommendation with what would change it -> report |

## 4. Side-Effect Gates

| Action | Rule |
|---|---|
| Read schema files, migrations, queries, and configuration | Allowed |
| Run the detector, a linter, a type check, or the ORM's offline diff | Allowed |
| Start a disposable local database (container, in-memory, a temporary file) to test DDL, plans, or a restore | Allowed; tear it down after the run and say so in the report |
| `EXPLAIN` without execution against a non-disposable database | Only when the user provided that connection for this run; read-only role preferred |
| `EXPLAIN ANALYZE`, DML, DDL, `VACUUM FULL`, index builds, `FLUSHALL`, `KEYS`, `DEBUG`, a restore, a failover, or a configuration change on a shared, staging, or production target | Only on the user's explicit request in this run, with the target name confirmed; otherwise write the command and the verification for the user to run |
| Read-only inspection of a non-disposable target (`SHOW`, `pg_stat_*` views, `INFO`, `CONFIG GET`, `SLOWLOG GET`, `explain()` without execution, `rs.status()`) | Only when the user provided that connection for this run or asked to inspect that target; prefer a read-only role. On managed services where these are blocked, read the provider's parameter group or console settings instead |
| Creating managed resources, changing billing tiers, deleting backups, or dropping data | Ask first, always |

Never print credentials, connection-string values, or customer rows. Redact them as `<redacted>` in commands and output excerpts. Do not open a real `.env` or secrets file to obtain a connection unless the user asked for it in this run; ask the user to provide or run the connection instead.

Before any runtime check, confirm the target's identity: when the user calls a target "production" but the files show a local or test database (or the reverse), stop and ask once, quoting both.

## 5. Severity

| Severity | Meaning | Example |
|---|---|---|
| critical | Data loss, corruption, security exposure, or an outage on deploy | `DROP COLUMN` with live readers; Redis exposed without auth; no tested restore for a primary store |
| high | A likely incident or a correctness bug under normal growth | table rewrite under `ACCESS EXCLUSIVE` on a large table; missing unique constraint behind an invariant; hot partition key |
| medium | Measurable waste or a design that blocks the next step | unused or duplicate index; N+1 query; TTL missing on a cache key family |
| low | Convention or maintainability | naming drift, missing comment on a non-obvious column |

## 6. Report Path

Write `.hyper/database/<slug>/report.md`, where `<slug>` is a short kebab-case name of the job; add `-2`, `-3` when the folder exists for another job. Put supporting artifacts (plans before and after, linter output, the detector JSON) beside it as files, and link them from the report. Follow [../references/report-template.md](../references/report-template.md).

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| `EXPLAIN ANALYZE` runs the statement, so writes need a transaction rolled back | <https://www.postgresql.org/docs/current/sql-explain.html> |
| Access-pattern-first design for key-value and document stores | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html> |
| The mode set, the phase order, the gates, and the severity scale | this package's chosen design, not a validated optimum |
