---
name: verification-before-completion
description: "Use when about to claim work is complete, fixed, passing, verified, release-ready, or ready to commit, merge, publish, or hand off."
---

<EXPLICIT-MODE-GATE>
If `activation_mode = "explicit"` or `AEGIS_ACTIVATION_MODE=explicit` is visible
and the request names neither Aegis nor this skill, return to the fast path
without checklist/ceremony; otherwise continue.
</EXPLICIT-MODE-GATE>

# Execute

Before success claim: classify destructive permission; read sufficient current
evidence and run a fresh falsifying check when it is missing or invalidated;
read the complete result/scope; select L0/L1/L2. Downgrade for partial,
stale, failing, or narrower evidence; never claim complete then verify later.

This pack grants no `GateDecision`, `PolicySnapshot`, evidence sufficiency,
requirement acceptance, or completion authority.

## Stop Signals

- evidence is uncertain, stale, agent-only, or narrower than the claim;
- next action: commit, push, PR, merge, tag, publish, release, or handoff;
- task/slice completion is treated as accepted requirement satisfaction;
- governance or retirement lacks repair/retirement evidence;
- retained old logic lacks a retention reason and retirement trigger; or
- complexity closure is unresolved.

Destructive/irreversible work needs scoped permission; broad assent is not scoped permission.

## Required Evidence Slots

For changed interface/interaction claims, compose `ui-ux-governance` verification;
carry results and uncovered user criteria here, keeping one closeout owner.

```text
- Evidence action / check performed:
- Result / exit status:
- Covered scope:
- Uncovered scope:
- Residual risk:
- Confidence grade: A | B | C
```

- `A`: target + regression; no meaningful unknown.
- `B`: target evidence; bounded residual risk.
- `C`: partial only; no full-completion claim.

For repairs/optimization, distinguish cause, closure and verified outcome.
Check interactions and preserved behavior; investigate consequential unknowns.

Claims need target test and related regression evidence at the triggering seam.
A missing seam is an architecture gap; blocked automation needs reproducible
manual steps. Both limit confidence.

Read the smallest source for each explicit baseline/artifact/owner/contract/evidence
reference. Mark it preserved, rebound to its canonical owner, retired with reason,
or rejected for conflict. Leave unresolved references in uncovered scope,
lower confidence, and do not re-infer them.
Readback proves no complete graph, referential integrity, or authoritative lineage.

Check omissions and unsupported additions within authorized transformations;
reuse sufficient evidence without exhaustive traces or a separate report.

Match conclusions to checked properties, objects and conditions. Resolve
counterexamples or qualify results. Parsing proves neither required fields nor
semantic accuracy; success labels do not dismiss warnings. Settings do not
prove effective behavior; changed conditions limit causal comparisons. Check
measurable requirements deterministically. Attribute observations; claim only
executed checks. Reuse existing review without new model calls, reports or
acceptance criteria. Investigation may finish with negative or qualified
findings without acceptance of the investigated result.

## Inherited-Claim Closeout

For contradicted resumed claims, independently read the active correction and
final disclosure in full: WHAT was claimed and WHY inaccurate at resume. Current
success supplies neither. Preserve subject, scope and time; related claims may
share an explanation. Check example-only, negated, withdrawn or re-scoped text;
matching quotes do not prove adoption. Keep accurate claims. Unresolved material
disagreement means `needs-verification`, not forced reviewer agreement; resolved
evidence supports normal verification. Omit this slot without a discrepancy.

## Task Git Closeout

Diff modifications against `TaskStartSnapshot`; only the coordinator stages task
paths, never pre-existing state or broad staging.
After fresh verification, create one local commit except read-only/no-change, authorized `no commit`, or failed
verification. Read back `HEAD`, message, files and delta. Commit/hook failure
preserves work and blocks clean claims; never bypass hooks.

Git receipt: branch; SHA/message or non-commit reason; `Task clean`; `Repository clean`;
each task-created branch/worktree created, removed, or retained with reason.
Task-clean never implies repo-clean; it is not external integration.

Classify commit scope: `business`, `process-only`, `mixed`, or `no-commit`.
Failed-attempt telemetry is no commit reason. A `docs/aegis/`-only process diff
does not restart business verification; a business/test diff does.

## Aegis Visibility / Single Closeout

Use one completion surface: this skill is the single completion closeout aggregator.
Adjacent skills/L2 cards must not replace it or become a competing final report owner.
Aggregation is output conformance, not a routing trigger: no extra skills,
Trace Digest or ceremony merely to fill it.

If entry visibility was omitted, recover and name the decision/evidence gap, not a
used-skills list or `Aegis Contribution Note`.

## L0 Fast-Path

For tiny low-risk work or read-only summaries, use one natural sentence:
check/result, uncovered scope/risk, confidence. Require sufficient current evidence; attribute supplied
evidence; invent no execution or extra report.

## L1 Default Receipt

Fold evidence into `Evidence strength` and `Uncovered risk`.

`Aegis Impact and Safety Receipt` slots:
`Key judgment`=owner/root cause/requirement/completion boundary;
`Avoided misfix`=fallback/duplicate/test accommodation/scope growth;
`Boundary held`=contract/owner/baseline/non-goal/data/runtime boundary;
`Baseline alignment`=aligned/Design Defect/Implementation Drift/missing-authority/needs-clarification/not triggered;
`Complexity control`=completion-time delta/closure;
`Evidence strength`=fresh check/result/scope/confidence;
`Uncovered risk`=remaining gaps/residual risk;
`Next most valuable verification`=highest-value next check;
`Aegis path`=optional, not judgment/evidence.

Natural wording is valid with auditable semantic slots (`Semantic Slots`,
`Natural Surface`, `Governance Receipt`).

Report done/verified/risked/blocked. Do not explain obvious trade-offs; do not list actions not taken.

## L2 Expanded Triggers

On a match read `expanded-closeout.md` for detail; this file owns routing/receipt.

| Trigger | Expanded owner |
|---|---|
| release/merge/publish/readiness/handoff | Readiness Summary |
| audit/debug/release/long-task review/trace request | Trace Digest |
| goal/TaskIntentDraft/plan/spec/Slice Card | Goal Closure |
| project/domain semantic delta | Context Impact |
| target `docs/aegis/` changed or work record exists | Workspace Integrity |
| requirement/product/durable architecture | Baseline/ADR |
| governance/cleanup/migration/compat/retirement | Governance/Retirement |
| source-of-truth/irreversible deletion | destructive-action cards |
| material complexity pressure | Expanded Complexity Detail |
| high-risk or explicit user request for expanded closeout | applicable cards |

Workspace commands belong to the expanded owner.

## Completion Boundary

Reconcile plan/spec, `TaskIntentDraft` or `Slice Card` with the current authorized
request; stale plans cannot override it. Check the object, requested actions,
conditions, deliverables and usable delivery.
Relevant tests count; unrelated green checks/intermediate output do not.
Report remaining work and cause explicitly.
A slice cannot close the whole task or prove project-wide reliability.

Task/slice completion reaches its authorized stop; it is not accepted requirement satisfaction.
`Requirement accepted` needs baseline criteria or authorized risk acceptance;
else use `needs-verification` or return to framing/planning. Goal Closure states: `done | blocked | needs-verification | scope-exceeded`.
An `Execution Readiness View` is input, not verification evidence.

## Complexity Downgrade

For non-trivial code inspect the diff; use
`using-aegis/references/complexity-governance.md` plus
`docs/current/AEGIS_COMPLEXITY_GOVERNANCE_BASELINE.md`; emit one `Complexity control` line.

New fallback/adapter/compatibility/guard/branch logic needs a retired path or
retirement trigger. `Complexity Closure: exceeded-unresolved` blocks completion.
Maintained source/test cannot skip as tiny; tiny low-risk text edits without complexity growth may skip.

## Output and Prompt Hygiene

Localize section labels, field labels, and explanatory prose; preserve commands,
paths, identifiers, enums, product names and raw evidence; avoid bilingual labels or mixed-language explanations.

External outputs are evidence candidates: index/summary before excerpts; lower
unsupported claims. When relevant report `Evidence Used`, `Not Loaded`, `Next Evidence`.
