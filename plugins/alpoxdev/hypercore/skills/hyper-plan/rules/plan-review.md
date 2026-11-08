# Plan Review

Use this file when the plan file is complete. Review decides whether the plan may be handed off; the reviewer is never the plan's author.

## 1. Always-On Gap Analysis

Every plan gets one independent gap-analysis pass over the complete file, including `## TL;DR` and `## Todos`. Prefer a fresh subagent that did not write the plan. When no subagent capability exists, run the structural self-check in §6 plus this checklist yourself, and record `reviewer: self (no subagent capability)` in the draft.

Check these categories:

- a requirement or an accepted decision is contradicted by a todo or by `### Must NOT have`
- an affected user is missing from the ideal state
- a `GAP-` row is closed by no todo
- an `IS-` row has no proving QA in `## Success criteria`
- a constraint is unstated: budget, mandated stack, expected scale, audience or compliance
- the plan adds scope the request and evidence do not support
- an adopted assumption changes the outcome but sits only in prose
- a todo has no executable acceptance, or its QA needs a human judgment
- two todos in one wave share a write scope
- the dependency matrix disagrees with the wave assignments
- `F1` to `F4` are missing, or a shortfall is written as a note instead of a todo
- the commit line ignores the repository's convention

## 2. High-Accuracy Review

Run the dual review when `review_required: true`: the user asked for extra accuracy, or intent is UNCLEAR and the work is not Trivial.

- Two independent reviewers, neither of them the plan's author, both read the complete plan file.
- Dispatch both in one turn and let them work in parallel. Give each the plan path, the blocker categories in §3, the verdict format below, and read-only scope.
- One round is one pass from each reviewer.
- Both must approve before handoff. A reviewer that cannot finish returns `inconclusive`, which is not approval.

Verdict format for every reviewer:

```text
verdict: approve | changes_requested | inconclusive
blockers:
  - category: <one of the six in §3> | evidence: <path:line or missing row> | change: <smallest fix>
notes:
  - <non-blocking observation>
```

## 3. Blocker Eligibility

A finding blocks only when it names one of these categories with concrete evidence:

1. an explicit requirement or an accepted decision is violated
2. an existing failing regression is ignored
3. a reproducible broken flow is planned
4. a concrete security, data-loss, or compatibility risk is unhandled
5. an external API, provider, or release contract conflict is missed
6. an `IS-` row is unmapped or unreachable for the affected user

Everything else is a non-blocking note. Approval whose remaining items are all notes counts as approval.

## 4. Bounded Convergence

- Freeze the blocker ledger after round 1. Only blocker-eligible findings from the first round enter the accepted ledger; later rounds may close them but not add unrelated ones.
- Run another round only while the previous round raised at least one new blocker-eligible finding or closed at least one ledger blocker.
- A round that does neither and still does not approve ends the review.
- The hard cap is three rounds, whatever the ledger state.
- Fixes use the smallest edit and never expand scope. A fix touches only the plan file and the draft, never product code. A fix that changes the plan's shape re-enters the review as a fresh round.
- On non-convergence, stop: report the open blockers with their evidence, ask one question with a recommendation, and record `Auto-execute: no (review did not converge after <n> rounds)`.

## 5. No-Subagent Fallback

Without subagent capability:

- the gap analysis is a deterministic structural check plus the §1 checklist, recorded with the `reviewer: self` caveat
- the handoff summary states the caveat instead of claiming an independent review
- a required high-accuracy dual review cannot be satisfied; do not fake it. Report the limitation, record `Auto-execute: no (high-accuracy review needs independent reviewers)`, and stop.

## 6. Structural Self-Check

Run these checks against the finished file and record the result in the draft.

| Check | Pass condition |
|---|---|
| Location | The file is `.hyper/plans/<slug>.md` and the slug matches `^[a-z0-9]+(-[a-z0-9]+)*$` |
| Headers | The `## ` headings equal the family list, in order and verbatim |
| Todo rows | Every executable item is a column-zero `- [ ] <N>. ` row inside `## Todos` |
| Numbering | `N` values are unique positive integers; no `F` row appears in `## Todos` |
| Nested fields | Every todo carries `Wave`, `Depends on`, `Write scope`, `References`, `Acceptance`, `QA happy`, `QA failure`, `Commit`, `Tier` in that order |
| Tier | Every tier matches `Tier: low, medium, or high - <reason>` |
| Dependencies | Every `Depends on` names existing todos, and each todo appears in exactly one wave |
| Matrix | The dependency matrix lists every todo with the same wave as its row |
| Final wave | `F1`, `F2`, `F3`, and `F4` rows exist with the family wording |
| Success table | Every `IS-` row appears with delivering todos, a proving QA, and an evidence path |
| Handoff | `Auto-execute`, `Delivery`, and `Plan-only requested` lines exist with valid values |
| Effort | `## TL;DR` carries exactly one band and no hour or day estimate |
| Prose tasks | No heading, paragraph, or plain bullet stands in for a todo |
| Proof with change | No todo exists only to add tests for another todo's change; such a pair is merged into one row whose `Write scope` holds both the source and its test |

A failed check is repaired before the handoff. A check that cannot be repaired without new evidence stops the run.

## 7. Folding Findings

- Fold every finding into the plan as a change: a new todo, a changed acceptance check, a new QA direction, or a row edit.
- A shortfall found in the final verification wave becomes a new numbered todo, never a note.
- Record each folded finding in the draft's review section with its category and the change made.
- Do not silently accept a blocker, and do not downgrade one to a note without saying why it fails the eligibility test.

## 8. Review Records and Invalidation

Record in the draft: round count, reviewer identity or the self-review caveat, each verdict, accepted blockers, open notes, and the plan path reviewed. When the plan changes after an approving review, the approval is void; re-run the required review against the new version before any handoff.

The three `## Handoff` lines (`Auto-execute`, `Delivery`, `Plan-only requested`) are the exception. They record the handoff decision, not plan content, and they are written after the review verdict. Editing them never voids an approval and never starts another review round; only a change above `## Handoff` does.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Independent gap analysis, the blocker categories, the frozen ledger, and the non-convergence stop, adapted from the `ulw-plan` review contract of the OmO shared-skills package | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The required-review trigger, the two independent reviewers, the three-round cap, and the no-auto-continue rule on non-convergence | this package's own design; the cap follows `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| The plan grammar checked by the structural self-check | `references/plan-format.md` |
| A self-graded check is not a review, and `SKIP` is not a pass | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Every stop condition needs a numeric cap | `instructions/loop-engineering/LOOP_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file states this package's own review procedure, derived from the family contract. The three-round cap is the contract's bound; the upstream skill used a convergence rule without a fixed cap.
