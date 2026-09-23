# Data safety

Use this module whenever a change reads protected data, writes durable state, changes a schema, or alters database permissions or resource use.

## Establish authority and isolation

- Locate the schema authority: migrations, declarative schema, application models, or an external owner. Follow that authority and its ordering rules; do not create a second source of truth.
- Use least-privilege identities with only the required operations and objects. A read-only label or prompt is not enforcement; verify the deployed credential, role, service, and database policy.
- Derive tenant scope from authenticated authorization context, not model output or client-provided filters. Enforce tenant isolation at application and data boundaries, and test owner, administrator, pool-reuse, background-worker, and missing-context cases.
- Use parameterized queries or structurally generated operations. Allowlist identifiers that cannot be parameters. Generated SQL is an untrusted proposal until reviewed and exercised against isolated data.
- Fail closed when identity, permission scope, tenant, schema version, operation intent, or transaction state is missing or contradictory.

## Make writes reconcilable

Define transaction boundaries and durable postconditions before code. Give every retriable consequential write a stable operation identity and a uniqueness or deduplication rule. If a timeout, disconnect, or failover leaves an ambiguous outcome, stop automatic retries and reconcile the operation record or authoritative state first. A driver retry does not make a multi-step business transition semantically idempotent.

Require explicit authority for production writes, destructive operations, DDL, bulk changes, privilege changes, and irreversible transformations. Separate approval from execution and record who authorized what scope.

Every response that proposes a runtime write must state the production decision explicitly. Write `Production authority: granted` only when the user or an identified policy owner supplied evidence for the exact scope; otherwise write `Production authority: not granted; design or test only; write disabled.` Do not hide this decision in a list of unknowns or infer authority from a request to design automatic behavior.

## Change schemas safely

Prefer an expand-and-contract migration when old and new application versions overlap:

1. Expand with compatible structures and safe defaults.
2. Deploy code that tolerates both versions; dual-write or backfill only with an owned reconciliation rule.
3. Backfill in bounded, resumable batches and verify invariants.
4. Switch reads or constraints after measured convergence.
5. Contract only after incompatible consumers are gone and recovery criteria are met.

Treat a proposed index, materialized view, partition, summary table, generated column, or constraint as a schema change even when it appears inside a performance plan. Either leave it as an evidence-gated lead, or include its expand-and-contract compatibility, migration ordering, resource preflight, staged rollout, and rollback or roll-forward behavior.

Before rollout, run a lock and resource preflight using representative data and the actual migration mechanism. Record expected lock mode and duration, scan or rewrite cost, log and replication impact, connection and storage headroom, transaction behavior, cancellation behavior, and compatibility with every live version.

Verify that a backup is recent, readable, complete for the affected state, and restorable through a timed exercise or equivalent project evidence. A configured backup without restore proof is not recovery evidence.

Use a staged rollout with explicit cohorts, health signals, pause thresholds, and ownership. Distinguish rollback from roll-forward: revert code or additive schema when reversal is safe; repair forward when a data transformation, external side effect, or destructive contract step cannot be reliably undone. Never promise rollback without a tested path.

Block release when compatibility, authorization, tenant isolation, backup verification, resource headroom, or an ambiguous outcome cannot be established. Preserve the failing evidence and name the missing authority or proof.
