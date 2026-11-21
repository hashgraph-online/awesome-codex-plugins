# Planning Workflow

Use this file from the first planning turn until the plan file exists. It owns classification, grounding, intent routing, questions, the durable draft, and plan writing.

## 1. Planner Role and Sticky Plan Mode

The planner reads, searches, and runs read-only analysis, then writes exactly two artifact types: `.hyper/drafts/<slug>.md` and `.hyper/plans/<slug>.md`. It never edits product code, configuration, or tests, and never dispatches an implementer. Delegated implementation is still implementation.

Plan mode is sticky. "Do X", "fix X", "build X", and "just do it" mean "plan X" while this skill is active. One request produces one plan, however large; size becomes more todos and waves, not a second plan.

## 2. Phase 0 - Classify

Classification sizes the grounding and the review, not the user's request.

| Class | Signal | Grounding | Review |
|---|---|---|---|
| Trivial | One file or one obvious edit, no cross-cutting choice | One targeted read plus one confirming read | Gap analysis only |
| Standard | One to five files, a clear feature or refactor | Parallel lanes, at most two waves | Gap analysis, plus dual review when `review_required` |
| Architecture | System design, five or more modules, long-term impact | Deeper lanes and external contracts | Dual review when `review_required`, recommended when intent is UNCLEAR |

Record the class in the draft. Intent UNCLEAR on non-Trivial work sets `review_required: true` even when the user never asked for it.

## 3. Phase 1 - Ground

Ground before asking. Two kinds of unknowns exist: discoverable facts, which come from the repository, the system, or the documentation, and preferences, which only the user owns. Only the second kind may reach a question.

Run these lanes in one turn when subagents are available, and read or search directly while they run:

- Implementation surface: call sites, existing patterns, test layout, the files the change will touch.
- Constraint surface: build, lint, typecheck, migrations, configuration, environment variables.
- External contract surface: official docs or upstream API contracts, only when the repository cannot answer.

Every lane prompt states TASK, DELIVERABLE, SCOPE, VERIFY, and that the lane is read-only. A subagent reply is a claim until the planner opens the cited file or runs the cited command.

Rules:

- Stop exploring a question when the collected evidence answers it, or after two consecutive waves add no new useful fact.
- Every claim that enters the plan carries `path:line`, a command with its output, or a documentation URL.
- Read-only means no edits, no installs, no branch changes, and no state-changing command.
- Unrelated modified or untracked files are recorded as a `dirty_worktree` risk and left alone; the plan never proposes overwriting them.
- The phase ends when the clearance check in §6 can be answered.

## 4. Phase 2 - Affected User and Ideal State

Name who the result touches: an end user, another programmer, a program or agent consuming the output, often more than one. State how each uses it today and how each will use it after.

Write rows into the draft and into the plan's `### Affected user and ideal state` section:

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | A property of the state where nothing snags, feels odd, regresses, or degrades for the user | The reason that property matters |
| GAP-1 | A difference between that state and today | The reason the difference exists |

Every later fork is held against these rows. Every todo closes at least one `GAP-` row. Every `IS-` row is proven by a QA check in `## Success criteria`.

When the ideal state is larger than the literal request, say so in one line and plan the ideal state. Never shrink the request to an invented MVP, phase 1, or reduced subset.

## 5. Phase 3 - Intent Routing

Make one judgment after grounding, then announce it in a single line before the first question.

| Verdict | Test | Behaviour |
|---|---|---|
| CLEAR | The desired outcome is defined; open items are preferences or owner-decisions | Ask only the surviving forks, each with the reason |
| UNCLEAR | The outcome itself is fuzzy, so asking would offload the planner's job onto the user | Research, adopt announced defaults, do not interview; `review_required: true` unless Trivial |
| On the fence | CLEAR and UNCLEAR are both defensible | Treat as CLEAR and ask exactly one question |

Overrides:

- An explicit "ask me", "interview me", "왜 안 물어봐" routes CLEAR, runs the interview, and turns the adopt-default filter off: every surviving fork is asked.
- "high accuracy", "ultra high accuracy", "고정밀", "deep review", "꼼꼼히", "정확도 높여" set `review_required: true` in any turn, including after the plan exists. When the plan already exists, run the required review in that same turn instead of rerouting.

Announce as one line: `Intent: CLEAR, review required` or `Intent: UNCLEAR, review not required`. The user must know whether they will be interviewed and whether a dual review is coming.

## 6. Phase 4 - Questions and Topology Lock

Apply both filters, in order, to every candidate question:

1. Could collected evidence answer it? Then explore instead of asking.
2. Does the affected user's ideal state, or the stated intent plus a defensible default, settle it? Then resolve it, record the resolution, and do not ask.

Owner-decisions survive both filters and are always asked, even when a default exists:

- an irreversible or destructive change
- a data or schema migration that cannot be rolled back
- a new paid resource or real spend
- credentials or account access
- external publication or sending
- a cross-cutting product choice the user lives with: public configuration surface, packaging or distribution, a pinned external dependency, the data shape, the audience or compliance limit

Question shape, reply handling, and delegation scope follow `rules/stance-calibration.md`:

- one to three per turn
- each names what was explored, why it did not settle the fork, and which plan decision depends on the answer
- two to four options, the recommended one first
- a skipped question resolves to the recommendation, and the resolution is recorded as uninformed
- every reply is classified as resolved, resolved but uninformed, unresolved with progress, or unresolved and blocked before the next turn
- a delegation phrase settles only the narrowest scope its words name, and after a plan-scoped delegation only a question about irreversible loss or a user-only step is still asked
- the question form in use is recorded in the draft, with its provenance

Always confirm the test strategy as TDD, tests-after, or none. Agent-executed QA is included either way.

Topology lock: from the request and the evidence, enumerate the one to six top-level components that can each succeed or fail independently, and record them in the draft's components ledger. Confirm the list in one turn. Never collapse to one component because the request looks small, and never add an adjacent component the request and evidence do not support. Every todo traces to a component.

Clearance check after each turn:

- Is the affected user named, with `IS-` and `GAP-` rows recorded?
- Is the objective defined?
- Is the scope explicit about what is in and out?
- Is the approach decided?
- Is the test strategy confirmed?
- Are budget, mandated stack, expected scale, and audience swept, each explored, defaulted, or asked?
- Is any blocking ambiguity left?

Any "no" is the next question. All "yes" moves to Phase 5.

## 7. Phase 5 - Durable Draft and Approval Gate

The draft survives compaction and session gaps. Write it before the plan file and update it as decisions land.

```markdown
---
slug: <slug>
intent: clear | unclear
review_required: true | false
question_form: batch | one_by_one | examples_first
question_form_source: declared | observed
approval: auto | user | pending
status: exploring | planning | reviewing | delivered | stopped
plan_path: .hyper/plans/<slug>.md
round_id: <id of the current review round>
plan_sha256: <shasum -a 256 of the plan file at review time>
---
## Request
## Affected user and ideal state
## Components

| id | outcome | status | evidence |
|---|---|---|---|

## Open assumptions

| assumption | default | rationale | reversible? |
|---|---|---|---|

## Decisions
## Questions asked
## Review
```

- The open-assumptions ledger holds every default adopted instead of asked: what was assumed, which default was chosen, why, and whether it can be reversed.
- The components ledger holds the topology lock with one row per component.
- `question_form` and `question_form_source` hold the form the run uses and whether the user declared it (`declared`) or it was read from replies (`observed`); `rules/stance-calibration.md` §4 sets both.
- `review` holds the round count, each verdict, accepted blockers, and open notes.
- `round_id` and `plan_sha256` hold the current round's digest binding. Update `plan_sha256` after every plan edit; the edit returns an approved round to `pending`.
- On any later turn, read the draft first and resume from its fields. Never reroute from memory. When the scope changed, update the draft and re-run only the affected phases.
- A slug is lowercase ASCII kebab-case matching `^[a-z0-9]+(-[a-z0-9]+)*$`, at most 48 characters. Reject `..`, `/`, and absolute paths.

Approval is a recorded step, not a passphrase hunt:

- `approval: auto` when the plan is delivered under the default auto-continue and the brief is announced rather than awaited.
- `approval: user` when the user asked to be interviewed, asked to approve the plan first, or an owner-decision is still open.
- `approval: pending` before the plan file exists.

An approval hold stops the run after the plan without ending the work. "승인은 내가 할게", "내가 승인할게", "I'll approve", and "wait for my approval" record `approval: user`, deliver the plan, and stop with `Auto-execute: no (approval requested)`. When the user approves in a later message, continue into execution against the same plan: no re-planning, and no new review unless the plan itself changed.

Announce the brief once: affected user, the `IS-` and `GAP-` rows, the findings with paths, each fork resolved against the ideal state, each open owner-decision with a recommendation, and the approach. Approval authorizes writing the plan only, never implementation.

## 8. Phase 6 - Write the Plan

1. Create the file from `assets/plan-template.md` at `.hyper/plans/<slug>.md`. Keep the headers exactly as written and in order.
2. Fill `## Scope`, `## Verification strategy`, `## Execution strategy`, `## Todos`, `## Final verification wave`, `## Commit strategy`, and `## Success criteria`.
3. Fill `## TL;DR` last, so it summarizes the finished plan rather than the intention.

Decision-complete rules:

- Name the exact path of every file the work touches, and write "every X in Y" when a sweep is intended.
- Fill `### Must NOT have` with the additions the plan refuses, so the executor does not invent scope.
- `Acceptance` carries the literal command and the expected result.
- `QA happy` and `QA failure` each carry the tool, the exact invocation, a binary observable, and an evidence path.
- `References` carries paths with line anchors or documentation URLs.
- Leave the implementer no judgment call.

Sizing rules:

- Target five to eight todos per wave. Fewer than three in a non-final wave means under-splitting.
- Implementation and its test are one todo.
- `Tier: low` is the default for mechanical and single-file work, `medium` for standard multi-file work, and `high` for one cohesive hard problem. Never force-split a high tier to look parallel.
- Todos in the same wave either have disjoint write scopes or run serialized.

`## TL;DR` carries what the user gets, why this approach, what it will not do, exactly one effort band (Quick, Short, Medium, Large, or XL), the risk line, and the decisions made for the user with their reversibility. Never write hours or days.

## 9. Stop Rules

- Plan complete, review passed, no opt-out, no approval hold, no open owner-decision: deliver the handoff summary and continue per `rules/handoff.md`.
- User opted out: deliver the plan and record `Auto-execute: no (plan only requested)`.
- User asked to approve first: deliver the plan and stop with `Auto-execute: no (approval requested)`; a later approval resumes the handoff against the same plan.
- Owner-decision open: deliver the available plan, ask the single question with a recommendation, and wait.
- A required high-accuracy review cannot run: stop with `Auto-execute: no (high-accuracy review needs independent reviewers)`.
- Review did not converge: report the blockers, do not auto-continue.
- Structural self-check failed and cannot be repaired without new evidence: report the failure, do not auto-continue.
- Brief announced: do not re-explore unless the user changed the scope.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Classification, the explore-before-asking rule, the two filters, the ideal-state and gap rows, the topology lock, the durable draft, the approval gate, and plan filling order, adapted from the `ulw-plan` skill of the OmO shared-skills package | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The plan file paths, the slug rule, the draft fields, the approval values, the auto-continue gate, and the plan grammar | this package's own design, user instruction, 2026-11-03; grammar stated once in `references/plan-format.md` |
| Classification sizes grounding and review while the request stays whole | user instruction, 2026-11-03 |
| A bounded exploration and a bounded question loop | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| Read-only delegation prompts carry task, deliverable, scope, and verify, and the parent verifies child claims | `instructions/context-engineering/references/parallel-workflows.md` |
| Approval is a structural node recorded in durable state | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file states this package's own procedure, adapted from the upstream planner and constrained by the family contract. The numeric bounds are this package's choices, not validated optima.
