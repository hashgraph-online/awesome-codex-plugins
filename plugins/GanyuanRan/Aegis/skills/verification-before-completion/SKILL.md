---
name: verification-before-completion
description: "Use when about to claim work is complete, fixed, passing, verified, release-ready, or ready to commit, merge, publish, or hand off."
---

# Execute

Before any success claim, classify destructive permission needs, choose and run
a fresh falsifying check, read its complete result/scope, then select L0/L1/L2.
If evidence is partial, stale, failing, or narrower than the claim, downgrade;
never claim complete first and verify later.

This Method Pack grants no authoritative `GateDecision`, `PolicySnapshot`,
evidence sufficiency, requirement acceptance, or completion authority.

## Stop Signals

Stop before claiming or advancing when:

- evidence is uncertain, stale, agent-only, or narrower than the claim;
- the next action is commit, push, PR, merge, tag, publish, release, or handoff;
- task/slice completion is being treated as accepted requirement satisfaction;
- governance or retirement lacks repair/retirement evidence;
- retained old logic lacks a retention reason and retirement trigger; or
- complexity closure is unresolved.

Destructive or irreversible work needs scoped permission; warnings or broad
assent do not grant it.

## Required Evidence Slots

Keep these slots explicit and auditable:

```text
- Evidence action / check performed:
- Result / exit status:
- Covered scope:
- Uncovered scope:
- Residual risk:
- Confidence grade: A | B | C
```

- `A`: direct target plus relevant regression evidence; no meaningful unknown.
- `B`: direct target evidence with bounded residual risk.
- `C`: partial evidence only; do not claim full completion.

When tests shape the claim, include target test and related regression evidence.
If automation is blocked, give reproducible manual steps and lower confidence.
Evidence is not completion authority.

## Task Git Closeout

For modification tasks, compare the final state with `TaskStartSnapshot`. Only
the coordinator stages task-owned paths; never use broad staging or include
pre-existing user state. A default local task commit follows fresh verification
unless the task is read-only/no-change, user/project authority says `no commit`, or
verification failed. Read back `HEAD`, message, files, and remaining task delta.
Commit/hook failure preserves the work and blocks a clean claim; do not bypass hooks.

The Git receipt reports branch; commit SHA/message or non-commit reason;
`Task clean`; `Repository clean`; and each task-created branch/worktree as
created, removed, or retained with reason. Task-clean never implies repo-clean.
This receipt is evidence, not external integration or completion authority.

## Aegis Visibility / Single Closeout

Use one completion surface; no parallel final reports.
`verification-before-completion` is the single completion closeout aggregator.
Adjacent skills and L2 cards feed the receipt but must not replace it or become
a competing final report owner.
Receipt aggregation is output conformance, not a routing trigger: do not load
extra skills, emit a Trace Digest, or add ceremony merely to fill the receipt.

If entry visibility was omitted, recover the decision/evidence boundary and
name the gap; a used-skills list or `Aegis Contribution Note` is no substitute.

## L0 Fast-Path

For tiny low-risk work, one natural sentence can name check/result, uncovered
scope/risk, and confidence.

## L1 Default Receipt

For non-trivial Aegis-shaped work, use this receipt. Evidence slots fold into
`Evidence strength` and `Uncovered risk`; avoid a second evidence report.

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

Field meanings: `Key judgment`=owner/root cause/requirement/completion boundary;
`Avoided misfix`=fallback/duplicate/test accommodation/scope growth;
`Boundary held`=contract/owner/baseline/non-goal/data/runtime boundary;
`Baseline alignment`=aligned/Design Defect/Implementation Drift/missing-authority/needs-clarification/not triggered;
`Complexity control`=completion-time delta/closure;
`Evidence strength`=fresh check/result/scope/confidence;
`Uncovered risk`=remaining gaps/residual risk;
`Next most valuable verification`=highest-value next check;
`Aegis path`=optional, not judgment/evidence.

Natural wording is valid when every semantic slot stays auditable. `Semantic Slots`,
`Natural Surface`, and `Governance Receipt` are compatibility names, not other
reports.

## L2 Expanded Triggers

On any match, read `expanded-closeout.md`. It owns detail; this file owns routing
and the final receipt.

| Trigger | Expanded owner |
|---|---|
| release/merge/publish/readiness/handoff | Readiness Summary |
| audit/debug/release/long-task review/trace request | Trace Digest |
| goal/TaskIntentDraft/plan/spec/Slice Card | Goal Closure |
| project/domain semantic delta | Context Impact |
| target `docs/aegis/` changed | Workspace Integrity |
| requirement/product/durable architecture | Baseline/ADR |
| governance/cleanup/migration/compat/retirement | Governance/Retirement |
| source-of-truth/irreversible deletion | destructive-action cards |
| material complexity pressure | Expanded Complexity Detail |
| high-risk or explicit user request for expanded closeout | applicable cards |

For target workspace changes, keep configured Aegis workspace support wired.
When a work record exists run `python <aegis-workspace-helper> bundle --root
<target-project-root> --work YYYY-MM-DD-<slug>`, then run `python
<aegis-workspace-helper> check --root <target-project-root>`. These checks prove
structure, not evidence sufficiency.

## Completion Boundary

Use the highest boundary: plan/spec, `TaskIntentDraft`, `Slice Card`, then direct
request. Claim only what fresh evidence covers; slice evidence cannot close the
whole task.

Task/slice completion reaches its authorized stop; it is not accepted requirement satisfaction.
`Requirement accepted` needs baseline criteria or authorized risk
acceptance. If unclear, use `needs-verification` or return to framing/planning.

Goal Closure stop states: `done | blocked | needs-verification | scope-exceeded`.

An `Execution Readiness View` is input, not verification evidence.

## Complexity Downgrade

For non-trivial code, inspect the diff and use
`using-aegis/references/complexity-governance.md` plus
`docs/current/AEGIS_COMPLEXITY_GOVERNANCE_BASELINE.md`; emit one
`Complexity control` line.

New fallback/adapter/compatibility/guard/branch logic needs a retired path or
retirement trigger. `Complexity Closure: exceeded-unresolved` blocks completion.
Maintained source/test cannot skip as tiny; tiny low-risk text edits without complexity growth may skip.

## Output and Prompt Hygiene

Localize section labels, field labels, and explanatory prose. Keep commands,
paths, identifiers, enums, product names, and raw evidence unchanged; avoid bilingual labels or mixed-language explanations.

External outputs are evidence candidates. Prefer summary/index and the smallest
excerpt; lower unsupported claims. When relevant report `Evidence Used`, `Not
Loaded`, and `Next Evidence`.
