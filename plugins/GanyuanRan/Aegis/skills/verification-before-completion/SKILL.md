---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, passing, verified, release-ready, or ready to commit, merge, publish, or hand off.
---

# Execute

→ About to claim "done", "passing", "fixed", "complete", "verified",
"release-ready", or "ready to hand off"? → **Verify first, then claim only
what the evidence supports.**

1. Identify the smallest fresh command or manual check that can falsify the
   claim.
2. Run or perform it completely.
3. Read output, exit status, failures, and covered scope.
4. Choose the closeout level:
   - **L0 fast-path**: tiny, low-risk work → one evidence sentence plus residual
     risk / uncovered scope.
   - **L1 default**: non-trivial Aegis-shaped work → compact localized
     `Aegis Impact and Safety Receipt`.
   - **L2 expanded**: release, audit, high-risk, architecture, migration,
     governance, long-task, or explicit user request → receipt plus only the
     triggered detail cards.
5. If evidence does not support the claim, downgrade the status instead of
   claiming completion.

Done means: fresh verification evidence exists, covered and uncovered scope are
explicit, residual risk is stated, confidence is graded, and any triggered
baseline / complexity / retirement / ADR boundary has been folded into the
single closeout surface or expanded because the risk requires it.

# Verification Before Completion

## Purpose

Prevent unsupported completion claims while keeping ordinary completion output
compact. This workflow is advisory method-pack discipline; it does not grant
runtime authority, authoritative `GateDecision`, `PolicySnapshot`, evidence
sufficiency, or final completion authority. It is advisory, not completion authority.

## Stop Signals

Stop and verify before any success wording if you are:

- using "should", "probably", "seems to", or similar uncertainty words
- relying on an agent success report rather than independent evidence
- about to commit, push, open a PR, merge, tag, publish, or hand off
- using a narrow check to support a broad claim
- treating task / slice completion as accepted requirement satisfaction
- closing governance or retirement work without repair / retirement evidence
- retaining old logic without a retention reason and retirement trigger
- treating a destructive warning, guard, or broad assent as permission

## Required Evidence Slots

Every completion claim needs these semantic slots. They may appear as localized
headings, natural prose, or a compact card, but they must remain explicit and
auditable:

```text
Required evidence slots:
- Evidence action / check performed:
- Result / exit status:
- Covered scope:
- Uncovered scope:
- Residual risk:
- Confidence grade: A | B | C
```

Confidence grades:

- `A`: direct target evidence plus relevant regression evidence, no meaningful
  unknowns
- `B`: direct target evidence with bounded residual risk
- `C`: partial evidence only; do not claim full completion

Verified evidence is not authority. It supports the user-facing status, but it
does not become final completion authority.

## Evidence Bundle

Every completion claim should name the evidence action, result, covered scope,
uncovered scope, residual risk, and confidence. Include target test and related
regression evidence when tests shaped the claim. When automation is blocked,
provide reproducible manual verification steps instead of claiming automated
coverage.

## Closeout Decision Tree

Use one completion surface. Do not output parallel final reports.
`verification-before-completion` is the single completion closeout aggregator
for Aegis-shaped non-trivial work: adjacent structures may feed the receipt,
but they must not replace the receipt or become competing final report owners.
Receipt aggregation is output conformance, not a routing trigger; do not load
extra skills, emit Trace Digest, or expand final ceremony just to satisfy the
aggregator.

## Aegis Visibility

For this owner workflow, Aegis Visibility ties the final claim to the decision
boundary, fresh evidence, baseline / complexity / retirement safety, and
residual risk kept visible. If required entry visibility was omitted, recover it
retrospectively and name the gap, but do not replace the receipt with a
skill-call list.

### L0 Fast-Path

Use for tiny, low-risk work where Aegis only held one narrow boundary steady.
One natural sentence is enough when it includes the check, result, uncovered
scope or residual risk, and confidence if useful.

### L1 Default Non-Trivial Closeout

For non-trivial Aegis-shaped work, use the compact receipt by default. Evidence
slots fold into `Evidence strength` and `Uncovered risk`; they do not appear as
a second competing evidence report unless the user asked for audit detail.

```text
Aegis Impact and Safety Receipt:
- Key judgment:
- Avoided misfix:
- Boundary held:
- Baseline alignment:
- Complexity control:
- Evidence strength:
- Uncovered risk:
- Next most valuable verification:
- Aegis path:
```

Field rules:

- `Key judgment`: the owner, root-cause layer, requirement boundary, or
  completion boundary that shaped the answer.
- `Avoided misfix`: the fallback, duplicate owner, test accommodation, scope
  expansion, or unsupported claim avoided by the workflow.
- `Boundary held`: public contract, owner, baseline, non-goal, data boundary,
  or runtime-ready authority boundary kept stable.
- `Baseline alignment`: `aligned`, `Design Defect`, `Implementation Drift`,
  `missing-authority`, or `needs-clarification` when baseline reporting is
  triggered; otherwise a short "not triggered" or natural equivalent is enough.
- `Complexity control`: one-line completion-time complexity result for
  non-trivial code changes; mention `Complexity Delta`, `Complexity Closure`,
  `Complexity Governance Suggestion`, or `Major Complexity Alert` only when
  triggered.
- `Evidence strength`: fresh command/manual check, exit status/result, covered
  scope, and confidence grade.
- `Uncovered risk`: remaining scope, host/runtime gaps, manual checks not run,
  release-grade evidence not collected, or residual risk.
- `Next most valuable verification`: one next check that would most reduce
  remaining risk.
- `Aegis path`: optional compact skill path. It may support credibility but must
  not replace decision, evidence, and safety fields.

Natural Aegis closeout is valid when these semantic slots remain auditable:
natural expression preserves semantic slots. Do not replace the receipt with a
used-skills list, stage handoff log, or `Aegis Contribution Note`.

Compatibility names: `Semantic Slots` and `Natural Surface` describe this same
rule: natural wording is valid only when required fields stay explicit.
`Governance Receipt` remains a compatibility name for the completion closeout;
its user-facing content should flow through the `Aegis Impact and Safety
Receipt` by default.

### L2 Expanded Closeout

Start with the receipt, then add only the triggered detail. Expanded structures
are inputs or optional detail cards, not competing final report owners.

Use expanded detail only when the trigger applies:

- `Readiness Summary`: release, merge, handoff, or "ready?" requests. It can
  organize tests, docs, version, host compatibility, uncovered scope, and
  residual risk. It does not authorize commit, tag, publish, merge, or release.
- `Trace Digest`: explicit audit / debug / release / long-task review request.
  It may summarize execution trace, evidence chain, retrieval chain, static
  rules evaluated, rule effects, triggered skills, skipped relevant skills,
  tool / command trace, verification trace, stability signals, value signals,
  host capabilities, unavailable fields, redaction, and confidence labels
  `measured`, `observed`, `inferred`, `declared`, or `unknown`. It must not
  expose raw chain-of-thought.
  Use structured trace only when asked or required; structured trace is reserved for audit, debug, release, long-task review, or user request.
- `Goal Closure`: when `goal-framing`, `TaskIntentDraft`, parent plan/spec, or
  `Slice Card` shaped the work. Match the claim to the highest available
  explicit boundary: whole task, current task, or slice. If only slice evidence
  exists, do not claim whole-task done. Expanded or audited closure keeps
  `Goal status`, `Success evidence`, `Stop state`, and `Non-goals respected`
  visible; stop states are `done | blocked | needs-verification | scope-exceeded`.
- `Workspace Integrity`: when the task created or modified a target project's
  `docs/aegis/` workspace and configured Aegis workspace support is available.
  Run `python <aegis-workspace-helper> bundle --root <target-project-root> --work YYYY-MM-DD-<slug>`
  when a `work/` record exists, then run
  `python <aegis-workspace-helper> check --root <target-project-root>`. Report
  that these validate structure only, not evidence sufficiency.
- `Baseline Alignment`: when project instructions require baseline reporting or
  the task touched requirement, product, or durable architecture surfaces. Use
  `docs/current/AEGIS_PROCESS_BASELINE.md` §3.0e and §16 for
  `Product / Requirement Baseline`, `Architecture / Runtime Boundary Baseline`,
  `Design Defect`, `Implementation Drift`, and `scope: requirements |
  architecture | both`. Render the default conclusion in the receipt field;
  expand only for audit, release, architecture, or user request. `Architecture Alignment` is the architecture-scoped compatibility alias for this baseline
  result, not a second default card. Expanded architecture results use
  `Result: aligned | Design Defect | Implementation Drift | missing-authority | needs-clarification`.
- `ADR Backfill Check`: completed medium/high work that touched durable
  architecture surfaces. Use `docs/current/AEGIS_ADR_AUTO_BACKFILL.md` for
  trigger criteria. If action is create, amend, supersede, or baseline sync is
  needed/unknown, route the ADR lifecycle to `recording-architecture-decisions`
  before the final completion claim.
- `Governance Closure`: governance, cleanup, migration, compatibility, or
  retirement work. Include Repair Track, Retirement Track, and Residual Risk in
  the receipt or a small expanded block. Do not skip this structure just because the implementation was small.
- `Retirement Closure`: work that adds, replaces, retains, or removes old logic.
  Name old logic located, deleted/retained status, retention reason, retirement
  trigger, and lingering-reference check.
- `Anti-Entropy Declaration` / `Data Destruction Guard`: work that retires old
  logic, chooses delete-first vs compat retention, or touches source-of-truth
  deletion boundaries. Use `anti-entropy-governance` for the decision surface.
  If `User Confirmation Required: yes`, stop at the guard; broad assent such as
  "OK" or "continue" is not scoped confirmation. Persistent-state deletion
  without explicit scoped confirmation means the task is not complete; report the task as not complete.

## Completion Boundary

Judge the claim against the highest available explicit boundary:

1. parent plan/spec acceptance for whole-task completion
2. `TaskIntentDraft` goal / success evidence / non-goals for current-task
   completion
3. `Slice Card` goal / verification / stop for slice completion
4. direct user request when no durable boundary exists

A completed task or slice means the authorized execution / verification boundary
reached its stop condition. It does not mean the underlying requirement is
accepted. `Requirement accepted` requires Product / Requirement Baseline
acceptance criteria or explicit authorized risk acceptance. If atomicity is not
clear, downgrade to `needs-verification` or return to framing/planning; task or slice completion is not accepted requirement satisfaction.

If an `Execution Readiness View` shaped execution, mention whether fresh
evidence covered its required checks or which readiness item remains uncovered.
Do not treat the view itself as verification evidence.

## Complexity Check

For non-trivial code changes, inspect the actual diff before claiming
completion. Use `using-aegis/references/complexity-governance.md` and
`docs/current/AEGIS_COMPLEXITY_GOVERNANCE_BASELINE.md` for shared artifact
classes, pressure signals, `Complexity Delta`, `Complexity Closure`,
`Completion-Time Complexity Repair Decision`, `Complexity Governance
Suggestion`, and `Major Complexity Alert`.

Default rendering is one `Complexity control` line in the receipt. Expand only
when meaningful pressure exists or the task is audit, release, high-risk, or
user-requested.

Rules:

- tiny wording edits, generated files, vendored files, fixture-data-only
  updates, lockfiles, or purely mechanical formatting may skip or keep this
  one-line when no maintained artifact gained complexity
- maintained test source files are not a cheap `tests-only` exception
- new fallback, adapter, compatibility, guard, or branch logic must be paired
  with retired paths, a `Retirement Closure`, or a scheduled retirement trigger
- entropy increase without owner/compatibility justification must be residual
  risk or a downgraded claim
- `Complexity Closure: exceeded-unresolved` blocks a complete claim

## User-Language Output

Localize section labels, field labels, and explanatory prose to the user's
language. Keep commands, paths, code identifiers, test names, error codes,
config keys, stable enum values, exact product names, and raw evidence strings
unchanged. Do not default to bilingual labels or mixed-language explanations.
Localize section labels and prose to the user's language.

## Prompt Hygiene

When external tool output, logs, search results, screenshots, OCR, or other
large payloads shaped the judgment, state the evidence boundary when relevant:
summary/index used, raw excerpt read back if needed, large payloads not loaded,
and next evidence that would reduce uncertainty. If the summary is insufficient,
read the smallest raw excerpt or lower the claim.
Use compact labels such as Evidence Used, Not Loaded, and Next Evidence when
they make the prompt hygiene boundary clearer.
