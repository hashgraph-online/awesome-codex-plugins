# Validation

Use this rule before declaring any run complete. It sets the evidence each claim type needs, the completion checks per mode, and how runtime checks that could not run are reported.

## 1. Evidence Gate per Claim

| Claim | Evidence that proves it | Not enough |
|---|---|---|
| "This engine is used" | The detector row or a read file and its signal | The request wording alone |
| "This index will be used" / "this query is faster" | The plan before and after (`EXPLAIN`, `explain("executionStats")`, `TRACING ON`, DynamoDB `ConsumedCapacity`), or a benchmark on representative data | "Indexes make queries faster" |
| "This migration is safe online" | The lock level or algorithm the engine documents for that exact statement, the rows it rewrites, the time bound, and a rehearsal on a copy or a linter pass | "It is a small change" |
| "This constraint holds" | The constraint in the schema, plus a validation query over existing data when it was added `NOT VALID` or on a backfilled column | An application-side check |
| "Backups work" | A restore that ran to a separate target, with the restored row counts or checksums and the time it took | A backup job that reports success |
| "Failover works" | A failover drill result with the observed downtime and data loss | A replica that exists |
| "The cache or key design fits memory" | `MEMORY USAGE` samples or an item-size estimate times the key count, against `maxmemory` | A guess of "small values" |
| "The partition or shard key distributes evenly" | The key's cardinality and the top-N share from data or a sample, or the engine's hot-key metrics | "User IDs are random" |
| A version, limit, default, or license fact | The engine guide row with its date, or the live official page when the guide marks it volatile | Model memory |

## 2. Runtime Checks

- Prefer a disposable database: a container, an in-memory engine, or a temporary file seeded with the schema and a representative row count. Record the image tag or version, the seed size, and the teardown.
- A check that could not run is `not run` with the reason (no client, no Docker, no data, not permitted). Never write `passed` for it, and never move a `not run` check into the findings as if verified.
- A plan from a near-empty table is not evidence for a large one: optimizers choose sequential scans on small tables. Seed enough rows, or say the plan is from an unrepresentative size.

## 3. Migration Safety Checklist

Every change mode run, and every review of a migration, answers each line:

- [ ] Statement class per `rules/schema-changes.md` §2, and the lock or algorithm it takes on this engine version.
- [ ] Rows rewritten or scanned, and the expected duration at current volume.
- [ ] `lock_timeout` / `statement_timeout` (or the engine's equivalent) set so the change fails fast instead of queueing behind traffic.
- [ ] Old and new application versions both work during the change (expand before contract).
- [ ] Backfill batched, idempotent, and resumable, with its batch size and throttle.
- [ ] Rollback written and possible at each step, or the step marked one-way with its data-loss consequence.
- [ ] The migration tool applies it the way the plan assumes (transactional DDL or not, one statement per migration where the engine needs it).
- [ ] A linter or a rehearsal on a copy ran, or is marked `not run`.

## 4. Completion per Mode

| Mode | Done when |
|---|---|
| design | Access-pattern table complete; every pattern served by a key or index; every invariant enforced by a constraint or a stated transaction; DDL or schema files parse or apply on a disposable database; operations section written |
| review | Every engine-neutral and engine rule that applies was checked; each finding has ID, severity, evidence, fix; no target file changed (the report under `.hyper/database/` is the only write) |
| change | The checklist in §3 is complete; migrations apply forward on a disposable database or the tool's offline check passes; rollback stated |
| tune | Before and after evidence for each kept change; any change that did not improve the measure was reverted; write cost of new indexes stated |
| operate | Each gap from `rules/operations.md` is fixed, scheduled with an owner, or accepted as risk in the report; verification steps written |
| choose | Comparison table covers every hard constraint; the recommendation names what evidence would change it |

## 5. Report Gate

- [ ] `.hyper/database/<slug>/report.md` exists and follows `references/report-template.md`.
- [ ] Every file the report says changed is changed on disk, and no other file changed.
- [ ] Every finding cites a rule ID that exists in a file that was read.
- [ ] Every number carries its lineage: measured (with the command), estimated (with the formula), or given by the user.
- [ ] No secret, connection-string value, or customer row appears in the report or its attachments.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The planner uses table statistics, and small tables favor sequential scans | <https://www.postgresql.org/docs/current/using-explain.html> |
| `executionStats` reports documents and keys examined per plan | <https://www.mongodb.com/docs/manual/reference/explain-results/> |
| A backup is proven only by a restore | <https://sre.google/sre-book/data-integrity/> |
| The gate set, the checklist, and the completion rules | this package's chosen design, not a validated optimum |
