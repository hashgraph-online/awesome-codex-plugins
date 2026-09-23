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

Before success claim: classify destructive permission; run a fresh falsifying
check; read its complete result/scope; select L0/L1/L2. Downgrade for partial,
stale, failing, or narrower evidence; never claim complete then verify later.

This Method Pack grants no authoritative `GateDecision`, `PolicySnapshot`,
evidence sufficiency, requirement acceptance, or completion authority.

## Stop Signals

- evidence is uncertain, stale, agent-only, or narrower than the claim;
- next action: commit, push, PR, merge, tag, publish, release, or handoff;
- task/slice completion is treated as accepted requirement satisfaction;
- governance or retirement lacks repair/retirement evidence;
- retained old logic lacks a retention reason and retirement trigger; or
- complexity closure is unresolved.

Destructive/irreversible work needs scoped permission; broad assent is not scoped permission.

## Required Evidence Slots

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

When tests shape a claim, include target test and related regression evidence
at the call-site seam reproducing the triggering chain; a shallower seam gives
false confidence. Missing seam is an architecture gap. Blocked automation needs
reproducible manual steps. Both lower confidence.

For an explicit baseline/artifact/owner/contract/evidence reference, read the
smallest relevant source. Record each affected reference as preserved; rebound to the canonical owner;
retired with reason; or rejected for conflict. Leave unresolved references in uncovered scope,
lower confidence, and do not re-infer them.
Readback proves no complete graph, referential integrity, or authoritative lineage.

## Task Git Closeout

For modifications, diff against `TaskStartSnapshot`. Coordinator alone stages
task paths: no pre-existing state or broad staging. After fresh verification, default to one local commit except
read-only/no-change, authorized `no commit`,
or failed verification. Read back `HEAD`, message, files, and task delta.
Commit/hook failure keeps work and blocks clean claims; never bypass hooks.

Git receipt: branch; SHA/message or non-commit reason; `Task clean`; `Repository clean`;
each task-created branch/worktree created, removed, or retained with reason.
Task-clean never implies repo-clean; it is not external integration.

Classify commit scope: `business`, `process-only`, `mixed`, or `no-commit`.
Failed-attempt telemetry is no commit reason. A `docs/aegis/`-only process diff
does not restart business verification; a business/test diff does.

## Aegis Visibility / Single Closeout

Use one completion surface. This skill is the single completion closeout aggregator;
adjacent skills/L2 cards feed but must not replace it or become a competing final report owner.
Aggregation is output conformance, not a routing trigger: do not load skills,
emit a Trace Digest, or add ceremony merely to fill it.

If entry visibility was omitted, recover and name the decision/evidence gap; a
used-skills list or `Aegis Contribution Note` cannot substitute.

## L0 Fast-Path

For tiny low-risk work, one natural sentence can name check/result, uncovered
scope/risk, and confidence.

## L1 Default Receipt

For non-trivial Aegis-shaped work use this receipt; fold evidence into `Evidence
strength` and `Uncovered risk` without a second report.

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

Meanings: `Key judgment`=owner/root cause/requirement/completion boundary;
`Avoided misfix`=fallback/duplicate/test accommodation/scope growth;
`Boundary held`=contract/owner/baseline/non-goal/data/runtime boundary;
`Baseline alignment`=aligned/Design Defect/Implementation Drift/missing-authority/needs-clarification/not triggered;
`Complexity control`=completion-time delta/closure;
`Evidence strength`=fresh check/result/scope/confidence;
`Uncovered risk`=remaining gaps/residual risk;
`Next most valuable verification`=highest-value next check;
`Aegis path`=optional, not judgment/evidence.

Natural wording is valid when every semantic slot stays auditable. `Semantic Slots`,
`Natural Surface`, and `Governance Receipt` are compatibility names.

Report done/verified/risked/blocked. Do not explain obvious trade-offs; do not list actions not taken.

## L2 Expanded Triggers

On any match read `expanded-closeout.md`: it owns detail; this file owns routing
and the final receipt.

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

Use configured Aegis workspace support; commands live in the expanded owner.

## Completion Boundary

Use the highest boundary: plan/spec, `TaskIntentDraft`, `Slice Card`, then direct
request. Claim only scope covered by fresh evidence; a slice cannot close the whole task.

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

Localize section labels, field labels, and explanatory prose. Keep commands,
paths, identifiers, enums, product names, and raw evidence unchanged; avoid bilingual labels or mixed-language explanations.

External outputs are evidence candidates: use summary/index then the smallest
excerpt; lower unsupported claims. When relevant report `Evidence Used`, `Not
Loaded`, and `Next Evidence`.
