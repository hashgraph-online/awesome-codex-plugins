# Plan Format

Use this reference before writing or validating the plan file. It owns the plan grammar: the header order, the todo row fields, the checkbox states, and a worked example.

## Contents

1. File Location and Slug
2. Header Sequence
3. TL;DR
4. Scope
5. Verification Strategy
6. Execution Strategy
7. Todos
8. Final Verification Wave
9. Commit Strategy
10. Success Criteria
11. Handoff
12. Checkbox States
13. Worked Example

## 1. File Location and Slug

The plan lives at `.hyper/plans/<slug>.md`; the draft lives at `.hyper/drafts/<slug>.md`. A slug is lowercase ASCII kebab-case, matches `^[a-z0-9]+(-[a-z0-9]+)*$`, and is at most 48 characters. Reject `..`, `/`, and absolute paths. The plan's first line is `# <slug> - Work Plan`.

## 2. Header Sequence

These headings appear once each, in this order, verbatim:

```text
# <slug> - Work Plan
## TL;DR
## Scope
### Affected user and ideal state
### Must have
### Must NOT have
## Verification strategy
## Execution strategy
## Todos
## Final verification wave
## Commit strategy
## Success criteria
## Handoff
```

Adding a heading is allowed only below the last one, and the executor ignores it. Reordering or renaming the headers breaks the contract.

## 3. TL;DR

Filled last. It carries six lines:

- what the user gets
- why this approach
- what it will not do
- `Effort:` exactly one of `Quick`, `Short`, `Medium`, `Large`, `XL`, never hours or days
- `Risk:` the concrete risks found during grounding, including a dirty worktree when one exists
- `Decisions made for you:` each adopted default with its reversibility

## 4. Scope

`### Affected user and ideal state` names who the result touches and how they use it today and after, then the rows:

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | A property of the state where nothing snags or regresses | The reason |
| GAP-1 | A difference between that state and today | The reason |

`### Must have` lists the required outcomes. `### Must NOT have` lists the additions the plan refuses: unrequested features, speculative abstractions, silent scope growth. It is a guardrail, never a reduction of the request.

## 5. Verification Strategy

State the test levels and the real checks: unit and integration commands, typecheck, lint, build, and the real-surface check per todo (an HTTP response, a terminal run, a browser flow, or a database diff). Name the adversarial classes that apply and why the others do not. The final verification wave is summarized here and specified in §8.

## 6. Execution Strategy

One `### Wave <N>` block per wave, each listing the todo numbers that run in it, followed by the dependency matrix:

```markdown
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/auth/login.ts |
```

Todos in one wave either have disjoint write scopes or run in sequence. Target five to eight todos per wave; fewer than three in a non-final wave means under-splitting.

## 7. Todos

Every executable item is a column-zero row, numbered with a unique positive integer:

```markdown
- [ ] <N>. <title>
  Wave: <wave number>
  Depends on: <todo numbers or none>
  Write scope: <exact paths or globs>
  References: <paths with line anchors, documentation URLs>
  Acceptance: <literal command and expected result>
  QA happy: <tool, exact invocation, binary observable>; evidence: <path>
  QA failure: <tool, exact invocation, binary observable>; evidence: <path>
  Commit: <message in the repository's convention>
  Tier: low | medium | high - <one-line reason>
```

Field rules:

- The indentation is two spaces, and the nine fields appear in this order.
- `Acceptance` must be executable by an agent with no human judgment.
- `QA happy` and `QA failure` each prove the change works and fails safely; both carry an evidence path.
- `Tier: low` is the mechanical or single-file default, `medium` is standard multi-file work, and `high` is one cohesive hard problem that is never force-split.
- Implementation and its test are one todo.
- Only column-zero `- [ ] <N>.` rows count as todos. A heading, paragraph, or plain bullet is not a task.

## 8. Final Verification Wave

Runs after every todo. The rows are fixed:

```markdown
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
```

A shortfall found here becomes a new `- [ ] <N>.` todo, never a note.

## 9. Commit Strategy

One commit per todo, using the repository's message convention, containing only that todo's write scope. State whether evidence files are committed or ignored, and whether a wave lands as one merge. The planned commit line in each todo and the strategy here must agree.

## 10. Success Criteria

| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 3 | `curl -i` returns 429 on the sixth request | `.hyper/qa/<slug>/3-happy.txt` |

Every `IS-` row appears exactly once. A row without a proving QA means the plan is unfinished.

## 11. Handoff

```markdown
## Handoff
- Auto-execute: yes | no (<reason>)
- Delivery: local | make-pr | ship
- Plan-only requested: yes | no
```

`Auto-execute: yes` requires the plan file, a passing structural self-check, an approved or converged review, no opt-out, and no open owner-decision.

## 12. Checkbox States

| State | Meaning |
|---|---|
| `- [ ]` | Open |
| `- [x]` | Done and verified |
| `- [~]` | Closed as blocked, with a nested `Unmet: <gap>` line |

Nested checkboxes are never tasks.

## 13. Worked Example

```markdown
# login-rate-limit - Work Plan
## TL;DR
- What you get: a per-IP limit of 5 requests per minute on `/login`, applied across all nodes.
- Why this approach: the existing Redis client already holds shared counters.
- What it will not do: no account lockout, no CAPTCHA, no admin bypass screen.
- Effort: Short
- Risk: the shared counter adds a Redis dependency to the login path.
- Decisions made for you: Redis storage (reversible), 429 with `Retry-After` (reversible).
## Scope
### Affected user and ideal state
Affected user: a person signing in through a load balancer.
| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | One count per IP across nodes | A user behind a balancer is not counted five times |
| IS-2 | The over-limit reply says when to retry | The user can wait instead of guessing |
| GAP-1 | No limit exists today | Brute force is unbounded |
### Must have
- A 5-per-minute per-IP limit on `POST /login`.
### Must NOT have
- Account lockout, CAPTCHA, or an admin bypass endpoint.
## Verification strategy
- `bun test src/auth` for unit and integration, `bun run typecheck`, `curl -i` for the real-surface check.
## Execution strategy
### Wave 1
- Todos 1 to 3.
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/util/rate-limit.ts |
| 2 | 1 | 1 | src/auth/login.ts |
| 3 | 2 | 1 | src/auth/login.test.ts |
## Todos
- [ ] 1. Add a shared per-IP counter
  Wave: 1
  Depends on: none
  Write scope: src/util/rate-limit.ts
  References: src/redis.ts:12
  Acceptance: `bun test src/util` exits 0 with 3 passing
  QA happy: `bun -e "..."` prints `ok 1..5`; evidence: .hyper/qa/login-rate-limit/1-happy.txt
  QA failure: the same script with a stopped Redis exits non-zero; evidence: .hyper/qa/login-rate-limit/1-failure.txt
  Commit: feat(auth): add shared per-IP counter
  Tier: low - one utility module
- [ ] 2. Enforce the limit in the login handler
  Wave: 1
  Depends on: 1
  Write scope: src/auth/login.ts
  References: src/auth/login.ts:40
  Acceptance: `bun test src/auth/login.test.ts` exits 0 with 4 passing
  QA happy: `curl -i` five times returns 200 then 429; evidence: .hyper/qa/login-rate-limit/2-happy.txt
  QA failure: a malformed IP header returns 400, not 500; evidence: .hyper/qa/login-rate-limit/2-failure.txt
  Commit: feat(auth): enforce per-IP login limit
  Tier: medium - one handler plus the shared limiter
- [ ] 3. Return the retry window
  Wave: 1
  Depends on: 2
  Write scope: src/auth/login.ts
  References: src/auth/login.ts:40
  Acceptance: `bun test src/auth/login.test.ts` exits 0 with 5 passing
  QA happy: the 429 response carries `Retry-After: 60`; evidence: .hyper/qa/login-rate-limit/3-happy.txt
  QA failure: a request just under the limit has no `Retry-After`; evidence: .hyper/qa/login-rate-limit/3-failure.txt
  Commit: feat(auth): return retry window on limit
  Tier: low - one response header
## Final verification wave
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
## Commit strategy
One commit per todo, conventional commits, no evidence files committed, wave 1 lands as one merge.
## Success criteria
| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 2 | five requests from one IP share one count | .hyper/qa/login-rate-limit/2-happy.txt |
| IS-2 | 3 | the 429 response carries `Retry-After` | .hyper/qa/login-rate-limit/3-happy.txt |
## Handoff
- Auto-execute: yes
- Delivery: local
- Plan-only requested: no
```

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The header order, the `IS-` and `GAP-` row meaning, the todo field list, the tier vocabulary, the fixed `F1` to `F4` rows, the success-criteria columns, the handoff fields, and the checkbox states | this package's own design, user instruction, 2026-11-03 |
| The slug rule and the draft path | this package's own design, following the repository's `.hyper/` working-directory convention |
| The plan skeleton and the producer rules, adapted from the `ulw-plan` template script of the OmO shared-skills package | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Column-zero task rows as the only counted tasks | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |

### Evidence grade

`LOCAL` - this file restates the family contract's grammar with an illustrative example. The example's paths and commands are fictional and exist only to show the shape.
