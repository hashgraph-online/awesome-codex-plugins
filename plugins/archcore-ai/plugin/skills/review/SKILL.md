---
name: review
argument-hint: "[--deep] [--drift] [path, tag, or scope]"
description: "Review branch changes against Archcore docs, or report project health. Use for 'review my branch', 'review the changes before merge', 'show status', 'documentation gaps', 'check if docs match code', 'close out the feature', 'ship the feature and close it out', or after a staleness warning. --drift for staleness detection, --deep for a full documentation audit. Not for creating docs — use /archcore:document; not for planning — use /archcore:plan."
---

# /archcore:review

Review the changes on the current branch against the `.archcore/` knowledge base, in both directions: whether the changed code still matches the documents that claim it, and whether the changed documents still match the code they describe. On the default branch, or with an empty diff, the skill reports project health instead. Write affinity: experience types — `cpat` and `task-type` land through the experience track.

## When to use

- "Review my branch" / "Review the changes before merge" → branch review
- "Show status" / "How many docs do we have?" → project health dashboard
- "Are any docs out of date?" / "Check if documentation matches the code" → `--drift`
- "Audit the knowledge base" / "Documentation gaps?" → `--deep`
- Session-start staleness warning appeared → `--drift`
- "Close out the feature" / "Ship the feature and close it out" → `closeout` track

**Not review:**
- Documenting a module, decision, or topic → `/archcore:document`
- Planning a feature or initiative → `/archcore:plan`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| No arguments, branch with changes | → branch review, steps 1–4 |
| On the default branch, or empty diff | → project health dashboard (step 1 fallback) |
| `--drift` | → actualize track (step 3); scope from step 1 when the branch boundary resolves, all documents on `on-default-branch` or `empty-diff` |
| `--deep` | → actualize track over all documents, plus coverage and relation findings |
| Path, tag, or scope argument | → the named scope narrows or replaces the branch scope |
| Completion signals: "close out the feature", "ship the feature and close it out" — an explicit completion or acceptance verb, not mere branch readiness. A plain "review my branch" stays on branch review even for a merge-ready branch | → closeout track (`skills/_shared/tracks/closeout.md`), scope pre-filled from the step 1 `branch-state` block; exits into the step 4 experience offer |
| Named track or type (`actualize`, `experience`, `closeout`, `cpat`, `task-type`) | → execute the named path without routing |

## Execution

Load `skills/_shared/gate-contract.md` and `skills/_shared/elicitation-contract.md` before executing any track gate. Question budgets follow the elicitation contract.

IF `.archcore/` does not exist, THEN announce initialization in one line and call `mcp__archcore__init_project` without asking a question. IF `.archcore/` contains zero documents, THEN proceed on git and codebase grounding and report that zero documents were found.

**Grounding.** Search all three categories — vision, knowledge, experience — with `mcp__archcore__search_documents` / `mcp__archcore__list_documents`; never exclude a category from reads. Pass a type filter matched to the review moment — `spec`, `rule`, `adr`, `doc`, `guide` for claims on changed code; `cpat`, `task-type` for precedent; `plan`, `prd`, `idea`, `rnd` for the closeout track's plan-and-implements-chain scope — instead of relying on the global type ranking. When a found document has `implements` or `related` relations, pull the linked documents one hop across categories.

**Global sources (only when present).** If any `list_documents` / `search_documents` result carries `global: true` / `read_only: true` / `source_kind: "global"`, load `skills/_shared/globals.md`. Never modify a global document and never add a relation to one. Exclude global documents from every local-health metric — counts, orphan detection, drift; you MAY add one separate line naming the mounted source and its document count.

### Step 1: Branch scope

Resolve the branch work boundary per `skills/_shared/branch-state.md` — plain git, offline. On success, the `branch-state` output block (committed and uncommitted changes since the merge base) is the review scope. A path, tag, or scope argument narrows the changed-file list.

Handle every sentinel the contract defines:

| Sentinel | Response |
|---|---|
| `no-repo` | Request an explicit path or topic; review that scope without a diff. |
| `detached-head` | State the detached state; request an explicit path, topic, or ref. |
| `no-default-branch` | Request an explicit path or topic. |
| `no-merge-base` | Request an explicit path or topic. |
| `on-default-branch` | Report project health instead of a branch review. |
| `empty-diff` | Report project health instead of a branch review. |

With `--drift`, the `on-default-branch` and `empty-diff` sentinels widen the actualize scope to all documents instead of the health fallback.

**Project health fallback** — compact dashboard, data only, no analysis:

- document counts by category, by status, and by type (skip types with 0);
- relation counts by type;
- orphaned documents (no incoming or outgoing relations);
- one-line issues summary (orphans, high draft count).

End with: *For staleness detection, run `/archcore:review --drift`. For a full audit, run `/archcore:review --deep`.*

### Step 2: Bidirectional check

Over the branch scope, check both directions:

1. Changed code versus the documents that claim it — search for documents that reference the changed paths, modules, or names; read each match with `mcp__archcore__get_document`; compare its claims against the changed code.
2. Changed documents versus the code they describe — for each changed `.archcore/` document, read the referenced code and compare.

Each conflict finding carries exactly one verdict: `spec-wrong` (the document is stale), `code-wrong` (the code violates a document that still stands), or `ok` (the pair matches on inspection). Cite the evidence — changed files, modification dates, content markers — with every non-`ok` verdict.

### Step 3: Actualize gate

WHEN step 2 surfaces a drift signal — any `spec-wrong` or `code-wrong` finding — or the user passed `--deep` or `--drift`, route into the actualize track (`skills/_shared/tracks/actualize.md`) and run its gates: `actualize.scope` (pre-filled with the step 1 `branch-state` block), `actualize.verdict`, `actualize.fix`. With `--deep`, widen the scope to all documents and report coverage gaps, relation health, status, and consistency findings alongside the drift verdicts.

### Step 4: Experience offer

WHEN the reviewed changes repeat an undocumented pattern, offer a `cpat` or `task-type` capture through the experience track (`skills/_shared/tracks/experience.md`): `experience.detect` establishes the repeated edit shape and its evidence; `experience.offer` asks once. The offer is optional — never force it; a decline writes nothing.

## Delegation

- The `archcore-auditor` agent collects findings read-only: document inventory, relation graph, drift and coverage signals. The agent never questions the user (a subagent MUST NOT conduct an interview, per `skills/_shared/elicitation-contract.md`) and never writes.
- The main thread confirms every fix with the user and applies it via `mcp__archcore__update_document`, one document at a time, per the `actualize.fix` gate. The review skill MUST NOT edit code on this path — it reports a `code-wrong` finding without fixing it.

## Result

- Branch review: findings grouped by verdict — `spec-wrong` / `code-wrong` / `ok` — with evidence, applied fixes, and declined fixes.
- Health fallback: the dashboard, data only.
- Closeout: per-task verdicts from `closeout.verify`, applied and declined document updates from `closeout.merge`, and status transitions grouped applied / declined / skipped from `closeout.accept`.
- Produced documents grouped by category — experience: a `cpat` or `task-type` draft from the experience offer; knowledge / vision: documents updated at `actualize.fix` or `closeout.merge`.
