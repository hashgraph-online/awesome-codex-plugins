---
name: review
argument-hint: "[drift|deep|closeout|experience] [path, tag, or scope]"
description: "The pre-merge review of a branch in a project that records its specs, decisions, and rules in .archcore/. Run this first for 'review my branch', 'review the changes before merge', or 'review before merge': it checks the changed code against the project's recorded canon and the changed documents against the code, and reports which side is wrong — spec-wrong or code-wrong; with no diff, it reports project health. A bug-hunting code review complements this review and does not replace it. Also use for 'show status', 'documentation gaps', 'check if docs match code', 'close out the feature', 'ship the feature and close it out', or after a staleness warning. Modes, named as the first word: drift for staleness detection, deep for a full documentation audit, closeout to close a finished feature, experience to capture a repeated pattern. Not for creating docs — use /archcore:document; not for planning — use /archcore:plan; not for a single-file edit with no branch review."
---

# /archcore:review

Review the changes on the current branch against the `.archcore/` knowledge base, in both directions: whether the changed code still matches the documents that claim it, and whether the changed documents still match the code they describe. A plain branch review also checks a matching `plan` for completion and continues into closeout when one exists. On the default branch, or with an empty diff, the skill reports project health instead. Write affinity: experience types — `cpat` and `task-type` land through the experience track. A branch review also selects durable context — the claims of the change a later reader needs from `.archcore/` — and writes the units the user authorizes through their owning instruments, per `skills/_shared/durable-context-selection.md`. This is also the only skill that removes a document: `closeout.discharge` removes a completed `plan`, and `actualize.fix` may remove a long-stale draft of any type — both via `mcp__archcore__remove_document`, each under its own confirmation.

Command tense: `/archcore:plan` declares a future canon delta, `/archcore:document`
records the present state — including work that shipped without a plan — and
`/archcore:review` reconciles a past declared delta. Δ vocabulary:
`skills/_shared/delta-routing.md`.

## When to use

- "Review my branch" / "Review the changes before merge" → branch review
- "Show status" / "How many docs do we have?" → project health dashboard
- "Are any docs out of date?" / "Check if documentation matches the code" → `drift`
- "Audit the knowledge base" / "Documentation gaps?" → `deep`
- Session-start staleness warning appeared → `drift`
- "Close out the feature" / "Ship the feature and close it out" → `closeout`
- "Capture this repeated change as a pattern" → `experience`

**Not review:**
- Documenting a module, decision, or topic → `/archcore:document`
- Planning a feature or initiative → `/archcore:plan`
- First-time setup → `/archcore:init`

## Routing table

| Signal | Route |
|---|---|
| No arguments, branch with changes | → branch review, steps 1–4; step 3 runs closeout for each matched `plan`, or the durable-context selection when no plan reaches capture |
| On the default branch, or empty diff | → project health dashboard (step 1 fallback); `closeout` and `experience` ask for a scope instead (step 1) |
| First word `drift` | → actualize track (step 3); scope from step 1 when the branch boundary resolves, all documents on `on-default-branch` or `empty-diff` |
| First word `deep` | → actualize track over all documents, plus coverage and relation findings |
| First word `closeout` | → closeout track (`skills/_shared/tracks/closeout.md`), scope pre-filled from the step 1 `branch-state` block; exits into the step 4 experience offer |
| First word `experience` | → experience track (`skills/_shared/tracks/experience.md`) over the branch scope; the detect gate selects `cpat` or `task-type` |
| Path, tag, or scope argument | → the named scope narrows or replaces the branch scope |
| Completion signals: "close out the feature", "ship the feature and close it out" — an explicit completion or acceptance verb | → closeout track (`skills/_shared/tracks/closeout.md`), scope pre-filled from the step 1 `branch-state` block; exits into the step 4 experience offer |
| Any other first word — a track or type name such as `actualize` or `cpat`, or a former flag such as `--drift` | → topic text; route by the signals above |

On the closeout track, `closeout.verify` reconciles the plan's `## Declared Delta` section against the branch diff and reports drift as unplanned Δ — details in `skills/_shared/tracks/closeout.md`.

## Execution

Load `skills/_shared/gate-contract.md` and `skills/_shared/elicitation-contract.md` before executing any track gate. Question budgets follow the elicitation contract.

Before relation review, load `skills/_shared/relation-authoring.md`. Read the
affected claims before reporting missing, unsupported, or redundant edges.

IF `.archcore/` does not exist, THEN announce initialization in one line and call `mcp__archcore__init_project` without asking a question. IF `.archcore/` contains zero documents, THEN proceed on git and codebase grounding and report that zero documents were found.

**Grounding.** Search all three categories — vision, knowledge, experience — with `mcp__archcore__search_documents` / `mcp__archcore__list_documents`; never exclude a category from reads. Pass a type filter matched to the review moment — `spec`, `rule`, `adr`, `doc`, `guide` for claims on changed code; `cpat`, `task-type` for precedent; `plan` on every branch review; `prd`, `idea`, `rnd`, and `research` (when `skills/_shared/research-compatibility.md` returned `yes`), plus `scenario` and `journey` (when `skills/_shared/actor-subject-compatibility.md` returned `yes`), for the closeout track's plan-and-implements-chain scope — instead of relying on the global type ranking. When a found document has `implements`, `depends_on`, or `related` relations, pull the linked documents one hop across categories.

**Global sources (only when present).** If any `list_documents` / `search_documents` result carries `global: true` / `read_only: true` / `source_kind: "global"`, load `skills/_shared/globals.md`. Also load it when a `search_documents` response's `coverage` names a source other than `"local"` — even when `results` is empty: the empty page is exactly where that file's retry ladder applies. Never modify a global document and never add a relation to one. Exclude global documents from every local-health metric — counts, the unlinked-document inventory, drift; you MAY add one separate line naming the mounted source and its document count.

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

In `drift` and `deep` modes, the `on-default-branch` and `empty-diff` sentinels widen the actualize scope to all documents instead of the health fallback, and Step 2 is skipped.

In `closeout` and `experience` modes, the `on-default-branch` and `empty-diff` sentinels do not fall back to project health. WHEN the arguments name no plan, path, or commit range, ask one question for that scope, recommending the most recently modified draft `plan`. With the scope set, the track judges the named plan against the current tree and, when given, the commit range.

**Project health fallback** — compact dashboard, data and mechanical checks, no judgement:

- document counts by category, by status, and by type (skip types with 0);
- relation counts by type, with the share of `related`;
- unlinked documents (no incoming or outgoing relations), reported as inventory;
- unresolved code paths and documents with line anchors, counted from one run of `bin/check-references` (`skills/_shared/tracks/actualize.md`, check 4) — never by reading each document; without a shell, state that the reference check did not run;
- one-line summary of confirmed structural issues; counts alone do not establish a defect.

An unlinked document or a high draft count alone is not an issue. The default
branch holds the merged corpus, so the reference counts run here even though no
diff exists: a path deleted by an earlier branch appears in no later diff.

End with: *For staleness detection, run `/archcore:review drift`. For a full audit, run `/archcore:review deep`.*

Before delegating an audit, supply the resolved branch scope, scoped diff, and
relevant git history to the auditor. Identify missing history explicitly.

Before computing project-wide metrics, page through `list_documents` until
`truncated: false`, increasing `offset` by `returned` after each page. If a
truncated page returns zero documents, report an incomplete inventory.

### Step 2: Bidirectional check

Over the branch scope, check both directions:

1. Changed code versus the documents that claim it — search for documents that reference the changed paths, modules, or names; read each match with `mcp__archcore__get_document`; compare its claims against the changed code.
2. Changed documents versus the code they describe — for each changed `.archcore/` document, read the referenced code and compare.

Each conflict finding carries exactly one verdict: `spec-wrong` (the document is stale), `code-wrong` (the code violates a document that still stands), or `ok` (the pair matches on inspection). Cite the evidence — changed files, modification dates, content markers — with every non-`ok` verdict.

Match local `plan` documents to the branch work:

1. Search `plan` documents by topic, changed-path references, and relations to the scoped documents.
2. Read each candidate with `mcp__archcore__get_document` before matching it.
3. Do not match a plan on a shared tag or folder alone.
4. IF a candidate matches ambiguously, THEN report it as a candidate and skip closeout for it.
5. Record each unambiguous match for step 3.

List open tracks in scope: each draft that carries an `archcore:track` state block, with its gate, its `deferred` entries, and the resume command per `skills/_shared/gate-contract.md`. An open track is unfinished work, not a verdict; closeout does not accept it.

### Step 3: Actualize gate

WHEN step 2 surfaces a drift signal — any `spec-wrong` or `code-wrong` finding — or the first word is `deep` or `drift`, route into the actualize track (`skills/_shared/tracks/actualize.md`) and run its gates: `actualize.scope` (pre-filled with the step 1 `branch-state` block), `actualize.verdict`, `actualize.fix`. In `deep` mode, widen the scope to all documents and run the track's deep checks within their stated budget — claim sampling, cross-document conflicts, type fitness, and relation candidates — alongside the drift verdicts, then report coverage gaps per the auditor's Coverage dimension (`agents/archcore-auditor.md`). Verdict vocabulary lives in `skills/_shared/verdict-contract.md`.

On a plain branch review, after step 2 and any actualize fixes:

1. IF step 2 matched no `plan`, THEN skip closeout and run the durable-context selection before step 4.
2. For each matched `plan`, run the closeout track (`skills/_shared/tracks/closeout.md`) with the step 1 branch boundary and that plan's scope pre-filled.
3. Run `closeout.verify` even when the request contains no completion wording.
4. Never infer completion from branch readiness alone. The track's plain-review entry rule decides which gates run after `closeout.verify`.
5. IF matched plans exist but none reached `closeout.capture`, THEN run the durable-context selection over the branch scope, excluding work an unfinished plan declares.
6. Run the step 4 experience offer once, after all matched plans have been checked.

The durable-context selection follows `skills/_shared/durable-context-selection.md`. It treats an ambiguously matched plan as no match, and it never selects a `journey`.

### Step 4: Experience offer

WHEN the reviewed changes carry an undocumented pattern that the durable-context preview did not list, offer a `cpat` or `task-type` capture through the experience track (`skills/_shared/tracks/experience.md`): `experience.detect` establishes the pattern and its evidence; `experience.offer` asks once. The offer is optional — never force it; a decline writes nothing.

## Delegation

- The `archcore-auditor` agent collects findings read-only: document inventory, relation graph, drift and coverage signals. The agent never questions the user (a subagent MUST NOT conduct an interview, per `skills/_shared/elicitation-contract.md`) and never writes.
- Before delegating to the `archcore-auditor` agent, pass the absolute plugin root — the directory two levels above this `SKILL.md` — and the output of `bin/check-references`, which the agent cannot run without a shell. The agent reads `skills/_shared/relation-authoring.md` under that root, and `skills/_shared/tracks/actualize.md` under the same root.
- The main thread confirms every fix with the user and applies it via `mcp__archcore__update_document`, one document at a time, per the `actualize.fix` gate. The review skill MUST NOT edit code on this path — it reports a `code-wrong` finding without fixing it.

## Result

- Branch review: findings grouped by verdict — `spec-wrong` / `code-wrong` / `ok` — with evidence, applied fixes, and declined fixes.
- Health fallback: the dashboard — data and the reference helper's counts.
- Ambiguous plan candidates: each candidate named, with closeout skipped.
- Open tracks: each draft from step 2's open-track list, with its gate, its unresolved choices, and its resume command.
- Durable context: units grouped created, updated, omitted, deferred, and declined — each with its claim, evidence, and owner, and a reason for every omitted or declined unit.
- Closeout: per-task verdicts, applied and declined document updates, status transitions grouped applied / declined / skipped, units written at capture with the instrument that took each, removed plans, and retained plans with the remaining work or blocking reason.
- Produced documents grouped by category — experience: a `cpat` or `task-type` draft from the experience offer or the durable-context selection; knowledge: a `spec`, `doc`, `guide`, `scenario`, or an `adr` plus its standard cascade (`rule`, `guide`), from the durable-context selection; knowledge / vision: documents updated by a drift fix or a closeout merge.
- Removed documents: each completed `plan` closeout removed, and each long-stale draft a drift fix removed on the user's confirmation — each named with a verified recovery commit when available. For closeout, state explicitly when git history does not preserve the removed plan's current content.
- Next actions — one line per finding kind present, naming only v2 commands:
  - a `code-wrong` finding: fix the code against the governing document, or, when the document should change instead, `/archcore:plan <capability>` to amend it;
  - code that no longer follows an `adr`: `/archcore:document decision` to record the superseding decision;
  - a coverage gap: `/archcore:document code <subject>`;
  - an open track: its resume command;
  - drafts the branch created with no matched `plan`: `/archcore:review closeout` to offer their acceptance;
  - an open `rfc`: `/archcore:document decision` to resolve it.
- Name tracks and steps in plain words; do not print a gate address of the form `<track>.<stage>`.
