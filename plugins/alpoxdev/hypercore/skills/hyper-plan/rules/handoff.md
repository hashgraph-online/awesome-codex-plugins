# Handoff

Use this file when the review verdict is known. It owns the chat summary, the auto-continue decision, the opt-out and delivery words, and the stop report.

## 1. Handoff Summary Shape

Deliver this structure in Korean, derived from the finished plan file. Count rows with a command or a search, never estimate.

1. **What this plan drives** - the work it performs, in one or two sentences.
2. **Affected user and ideal state** - who the result touches and what exists or behaves differently for them after execution.
3. **Shape** - the number of todos (`- [ ] <N>.` rows), the number of `F` rows, the wave count, and the tier mix, for example `6 low, 2 medium, 1 high`.
4. **Added beyond the request** - what exploration surfaced and the plan folded in, each with a one-line reason; say `none` when nothing was added.
5. **Verification** - the final verification wave plus the key QA commands that will prove completion.
6. **Execution handoff** - the next step, the delivery mode, and the plan path.

## 2. Auto-Continue Rule

Continue into `hyper-execute` only as written below. The step is automatic, not a question. When all three conditions hold, the handoff proceeds in the same session:

1. the plan file exists, the structural self-check in `rules/plan-review.md` passed, and the required review approved or converged with no open blocker
2. the user neither opted out nor asked to approve the plan first
3. no unresolved owner-decision remains

Pass the resulting delivery flag through, whether the user gave a flag or a phrase (§3): `--make-pr`, `--ship`.

A landing policy is not a delivery mode. When the user named one (`--land cherry-pick`, "linear history", "cherry-pick으로 반영"), keep `Delivery:` at its value, write `Landing: <merge|cherry-pick>` on the plan's `## Commit strategy` line, and pass the policy to the execution handoff beside the delivery flag. The three `## Handoff` lines never gain a landing line.

Continue by invoking the execution skill in this same session, without ending the turn: load `hyper-execute` through the runtime's skill mechanism (or read its `SKILL.md` where skills are plain files) and follow it from its first phase with the slug and the delivery flag. Record `Auto-execute: yes` in the plan before switching. Only when that skill is not installed in this session, stop with `Auto-execute: no (execution skill not installed)` and print the exact invocation `hyper-execute <slug>` plus the delivery flag so the user can run it.

## 3. Opt-Out and Delivery Words

An explicit opt-out stops the run after the plan. These words count:

- `--plan-only`
- "plan only", "just the plan"
- "계획만", "계획만 세워줘", "실행하지 말고", "실행하지 마", "실행은 나중에"
- "don't execute", "no execution"

An approval hold also stops the run after the plan without ending the work. These words count:

- "승인은 내가 할게", "내가 승인할게"
- "I'll approve", "wait for my approval"

Record the hold as `approval: user`, deliver the plan, and stop with `Auto-execute: no (approval requested)`. When the user approves in a later message, continue into execution against the same plan: no re-planning, and no new review unless the plan itself changed.

Delivery words select the mode. Recognize the flags and the natural-language phrases:

| Word or flag | Handoff value | Effect |
|---|---|---|
| none | `Delivery: local` | Implementation commits on the integration base, no push |
| `--make-pr`, "make a PR", "PR만", "PR까지만", "PR로" | `Delivery: make-pr` | Implementation arrives as a pull request, no merge |
| `--ship`, "ship", "merge it", "머지까지", "배포까지" | `Delivery: ship` | Pull request, then merge once checks pass |

Pass the resulting flag through to the handoff, whether the user typed a flag or a phrase.

## 4. Hard Stops

Stop without auto-continue when any of these holds:

- an owner-decision is unresolved: an irreversible or destructive change, a migration that cannot roll back, a new paid resource or spend, credentials or account access, external publication or sending
- the user asked to approve the plan first
- a required high-accuracy review cannot run because no independent reviewer is available
- the required review did not converge within three rounds
- the structural self-check failed and cannot be repaired without new evidence
- the plan file cannot be written at `.hyper/plans/<slug>.md`
- the user's requirement turned out to be a different output shape, such as a requirements package or a research report

## 5. Stop Reporting

Say the stop reason in one line using the plan's own vocabulary, then state the one thing the user can do to unblock it. Do not repeat the whole plan.

| Reason | Line |
|---|---|
| Opt-out | `Auto-execute: no (plan only requested)` |
| Approval hold | `Auto-execute: no (approval requested)` |
| Open owner-decision | `Auto-execute: no (owner decision pending: <topic>)` |
| High-accuracy review unavailable | `Auto-execute: no (high-accuracy review needs independent reviewers)` |
| Non-converged review | `Auto-execute: no (review did not converge after 3 rounds)` |
| Failed self-check | `Auto-execute: no (structural self-check failed: <check>)` |
| Unwritable plan | `Auto-execute: no (plan file not writable: <path>)` |
| Execution skill not installed | `Auto-execute: no (execution skill not installed)` |

## 6. Handoff Section Fields

The plan's `## Handoff` section carries exactly these lines:

```markdown
## Handoff
- Auto-execute: yes | no (<reason>)
- Delivery: local | make-pr | ship
- Plan-only requested: yes | no
```

The chat summary and the plan file must agree. The chat value is computed at handoff time; the file value is edited to match before the summary is sent.

Write these three lines after the review verdict. They record the handoff decision, not plan content, so editing them never voids an approval and never triggers another review round.

## 7. What the Handoff Never Does

- It never implements, edits product code, or dispatches an implementer.
- It never asks "shall I proceed?" when the auto-continue conditions hold.
- It never claims a review receipt that is not recorded in the draft.
- It never starts a second plan for the same request.
- It never commits, pushes, or opens a pull request itself.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The handoff summary shape and the counted row report, adapted from the `ulw-plan` delivery format of the OmO shared-skills package | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The auto-continue conditions, the opt-out words, the delivery modes, the hard stops, and the handoff field values | user instruction, 2026-11-03; this package's own design |
| Auto-continue is the default and happens without a permission question | user instruction, 2026-11-03 |
| Handoff values written into durable state, not only into chat | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Approval as a recorded structural node rather than a chat passphrase | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file states this package's own handoff procedure and the family contract's gate. The opt-out vocabulary is a chosen list, not an exhaustive natural-language parser.
