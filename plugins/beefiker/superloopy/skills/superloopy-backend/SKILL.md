---
name: superloopy-backend
description: Use only after explicit Codex `$superloopy:superloopy-backend` or Claude Code `/superloopy:superloopy-backend` invocation, a backend task beginning with leading `loopy` or `루피`, or an active Superloopy loop routes backend work here. Relevant work includes backend application boundaries, APIs, persistence, migrations, transactions, background jobs, caches, events, reliability, security, and runtime database-agent tools. Plain API, server, database, SQL, or agent vocabulary does not activate this workflow.
---

# SUPERLOOPY BACKEND ENABLED

Open the response with `SUPERLOOPY BACKEND ENABLED`. If another active Superloopy mode mandates its own first line, print that first and this marker on the next line. Resolve this skill's installed directory, set `BACKEND_SKILL_DIR` to that absolute path, and announce `BACKEND_SKILL_DIR=<path>` before loading a reference. Do not assume the repository-relative path is the installed path.

## Discover in proportion to the change

Inspect the repository before prescribing commands, code, schema, or infrastructure: its instructions, its recorded conventions and the hooks, linters, formatters, or convention checks that enforce them, language and runtime, data stores and schema authority, test commands, generated artifacts and how they are regenerated, and the project's own definition of done for a change of this kind. Preserve the existing stack and patterns; remain stack-neutral when evidence does not select a technology. Ask only when a missing fact would materially change the implementation or its safety.

Fill the context card only as far as the classified change reaches. A change confined to one unit needs the first five lines; a schema, contract, or runtime-agent change needs all of it. A card filled to the bottom for a two-line fix is cost, not diligence.

```text
User outcome:
Language and runtime / existing architecture:
Recorded conventions and their enforcement:
Generated artifacts and their regeneration command:
Project definition of done (one line per item, copied from the project):
Data stores / schema authority:
API consumers / compatibility:
Deployment model / production access / compliance constraints:
Unknowns that affect the decision:
```

## Classify and route

Classify the change as one or more of: API behavior, schema or migration, transaction, background job, cache, event or queue, runtime agent tool, performance, reliability, or security. Load only the modules the classification names:

- [Architecture](references/architecture.md) — system boundaries, API or event contracts, consistency, transactions, idempotency, caching, background work, compatibility, stack restraint.
- [Data safety](references/data-safety.md) — whenever the diff touches a query, mapper, schema, migration, privilege, or transaction boundary: schema authority, tenant isolation, least-privilege identities, reconcilable writes, migration preflight, rollout and recovery.
- [Runtime agents](references/runtime-agents.md) — typed tool boundaries with read-only, least-privilege defaults; authorization and tenant scope from verified context; retrieved records are untrusted data, not instructions or authority; bounded time, rows, payload, cost, retries.
- [Testing and operations](references/testing-and-operations.md) — realistic persistence tests, observability, performance evidence, rollout and recovery proof.
- [Evidence](references/evidence.md) — when finishing: where the active or standalone evidence root comes from, how to publish, how to recover a lost receipt.
- [Upstream notice](references/upstream-notice.md) — only when auditing the public evidence behind this guidance.

Do not load unrelated modules or invent their contents when a reference is unavailable; state the missing guidance as a blocker or evidence gap.

## Contracts before code

Define the request and response or event shapes, invariants, authorization decision, tenant boundary, consistency expectation, idempotency behavior, failure semantics, observability, compatibility, and rollout before implementation. For runtime database agents, default to typed application tools or narrowly scoped services with read-only, least-privilege capability, explicit allowlists, bounds, redaction, and auditability.

Honor the project's recorded conventions as constraints, not suggestions: naming, layering, error and log shape, endpoint form, and anything its own hooks, linters, formatters, or convention checks already enforce. A change that a project check would reject is not finished. When a change adds a member to an established published surface — another endpoint, operation, tool, field, error code, or event — its existing siblings specify the name and shape it inherits; the informal wording of the request does not.

Require explicit user authority before production writes, destructive operations, DDL, bulk changes, privilege changes, or dependency additions. Preflight migrations and consequential data changes for old/new version compatibility, locks and resources, transaction behavior, backup validity, staged rollout, and rollback or roll-forward. Prefer an isolated or disposable real database for behavior that depends on transactions, concurrency, migrations, tenant separation, or query semantics; a mock or single fixture does not prove database behavior.

## Rules that are decisions

Each of these is checkable from the diff or from a run. Measured effect (see the README): about a quarter fewer changes ship an untested part; the rest is checkable procedure without a separately measured effect.

1. **Reproduce first, and re-run the same reproduction at the end.** Capture the reported symptom as a runnable reproduction before changing anything, at the conditions the report describes rather than narrowed onto the cause you find. A change that does not make the reported behavior go away is not a fix, however well the cause is explained.
2. **Extend the suite that already states the contract.** Put new cases in the test file that already covers the unit you are changing. A second file, fixture, bootstrap, or harness for a unit that has one is a change to the project's test topology and carries its own stated reason. New coverage may not be bought by mutating fixture state other cases depend on, and releases what it creates through the suite's own teardown.
3. **Prove a post-hoc regression test can fail.** Revert the change and watch the test go red. Where the runner stops at the first failure, do it per assertion or per case, because a test passes a whole-run check on the strength of one assertion while the others never see the defect.
4. **A red existing test is the contract, not an obstacle.** Decide which of the two is wrong before editing either. A test quietly renamed, narrowed, relaxed, or disabled to fit the new code certifies the change against itself; amend it only when the contract genuinely moved and you can say what moved it.
5. **Regenerate what your change invalidated** — client code from a schema, an ORM or query-builder model, a typed API contract, an enumeration catalog — with the project's own command, in the same change. A stale artifact is an incomplete change.
6. **Walk the project's own definition of done** — changelog entries, request examples, documentation, review steps — item by item against the files you touched, in addition to this skill's evidence requirements; do not substitute one for the other.
7. **Repair what the change falsified; author nothing else.** A documented rule, an endpoint or field description, an error message, a response template, or the version identity an artifact ships under is part of the contract, whether the change falsified it or authored it; one that contradicts the code is a defect the change ships. Correct those statements in the same change and declare a moved meaning where consumers read it. A statement you add describes the hunk it sits in; a claim about code elsewhere is checked against that code or not written. Do not author new prose about behavior the change did not move.
8. **Put a case on each side of every condition you add.** A side no input can reach is a dead branch to delete, not a comparison to document.

## Repair the class, and stop where behavior was already correct

Narrow means minimal in mechanism, not partial in coverage: repair the mechanism that produced the defect rather than the single instance it was reported through, and before calling it fixed, enumerate every other route into that mechanism from your own diff — the other call sites of each symbol you changed, the other branches of each statement you edited, the other code that writes each value you moved, the other input shapes the condition you added accepts — and either correct each in the same change or pin it: an assertion that locks its present behavior, or a filed follow-up whose id the change carries. Decide each candidate by the two checks in [Sweep](references/sweep.md). Any correction you make beyond the site the report names is a behavior change of its own and carries what the requested one carries — a test that fails without it and a stated reason on the change — and callers that were behaving correctly keep the behavior they have.

## Fail closed

- If database identity, permission scope, schema version, authorization, or tenant context is uncertain, deny or pause the operation.
- If a write has an ambiguous outcome, do not retry it automatically; reconcile through an idempotency key, operation record, or authoritative read first.
- If a query exceeds time, result, payload, or cost bounds, cancel it and require a narrower request.
- If migration preflight fails, block rollout and preserve the exact evidence.
- If realistic database proof is unavailable, run the safe checks that remain and report the missing integration evidence; do not claim migration or production safety.

## Finish with a receipt

Report the context card, change classification, contracts, changed behavior, validation evidence, rollout and recovery notes, unresolved risks, and blockers. Four entries are named fields, because the obligations behind them are the ones a run reaches the end without having done:

- `regression_test_failed_without_fix` — one row per new case, not per file: the hunk whose reversion reddens that case, the command, and the assertion that failed. Two cases naming the same hunk are one case; a case naming none is not evidence.
- `unrequested_changes` — every hunk not on the path from the reported symptom to the repair, each with its own failing test, or reverted before you finish; a formatting or flag-only hunk has no expressible test and is reverted. `none` if there are none.
- `routes_into_the_mechanism` — one row per symbol, statement, writer and input shape from the clause above: each corrected here, or pinned, naming the assertion that locks it or the follow-up id. A route recorded only in this report reaches nobody.
- `definition_of_done` — the project's own list from the context card, item by item, each marked done or explicitly deferred.

Redact credentials, connection strings, tokens, and protected row data; reference large artifacts by path instead of inlining them.

Publish the report by passing it on standard input to `node "$BACKEND_SKILL_DIR/scripts/write-evidence-report.mjs" write "<project-root>" "<active-evidence-root>" "<qualified-report-id>"`, exactly as [Evidence](references/evidence.md) directs: it resolves the active evidence root inside a Superloopy loop or the project-local root for a standalone run, mints a qualified report id that names one attempt (a re-attempt gets a new id such as `-attempt-2`), recovers a lost receipt with `recover` only for the invocation whose receipt was lost, and keeps the evidence root out of the change under review. Never write the target path directly. Announce the printed path and end with this exact receipt after replacing the placeholder:

`SUPERLOOPY_EVIDENCE: <BACKEND_EVIDENCE_REPORT>`
