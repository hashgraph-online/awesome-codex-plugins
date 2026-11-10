# Plan Shape

Read this immediately before writing `.hyper/plans/<slug>.md`. It restates the plan grammar this package writes into, so the plan file needs no other reference.

The plan is written by this skill from the insight bundle. It is not produced by a separate planning stage; the finished file is what an execution stage consumes.

## Contents

1. Location and slug
2. Header sequence
3. TL;DR
4. Scope
5. Verification strategy
6. Execution strategy
7. Todos
8. Final verification wave
9. Commit strategy
10. Success criteria
11. Handoff
12. Checkbox states
13. Worked fragment

## 1. Location and Slug

The plan lives at `.hyper/plans/<slug>.md`, where `<slug>` is the same slug as the debate directory. It is lowercase ASCII kebab-case, matches `^[a-z0-9]+(-[a-z0-9]+)*$`, and is at most 48 characters. Reject `..`, `/`, and absolute paths.

The first line is `# <slug> - Work Plan`.

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

A heading may be added only below the last one, and the executor ignores it. Reordering or renaming a header breaks the contract.

## 3. TL;DR

Filled last. Six lines:

- what the user gets
- why this approach
- what it will not do
- `Effort:` exactly one of `Quick`, `Short`, `Medium`, `Large`, `XL`, never hours or days
- `Risk:` the concrete risks the debate surfaced, including a dirty worktree when one exists
- `Decisions made for you:` each surviving decision from the bundle with its reversibility

The debate's provenance belongs on the `Risk:` line in one clause. It does not become a todo.

## 4. Scope

`### Affected user and ideal state` names who the result touches and how they use it today and after, then the rows:

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | A property of the state where nothing snags or regresses | The reason |
| GAP-1 | A difference between that state and today | The reason |

Every hard constraint from the bundle becomes an `IS-` row. Every rejected addition becomes a `### Must NOT have` line.

`### Must have` lists the required outcomes. `### Must NOT have` lists the additions the plan refuses: unrequested features, speculative abstractions, silent scope growth, and the specific alternatives the debate defeated.

## 5. Verification Strategy

State the test levels and the real checks: unit and integration commands, typecheck, lint, build, and the real-surface check per todo (an HTTP response, a terminal run, a browser flow, or a database diff). Name the adversarial classes that apply and why the others do not. Summarize the final verification wave here and specify it in §8.

## 6. Execution Strategy

One `### Wave <N>` block per wave, each listing the todo numbers that run in it, then the dependency matrix:

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

- Indentation is two spaces, and the nine fields appear in this order.
- `Acceptance` must be executable by an agent with no human judgment.
- `QA happy` and `QA failure` each prove the change works and fails safely; both carry an evidence path.
- `Tier: low` is the mechanical or single-file default, `medium` is standard multi-file work, and `high` is one cohesive hard problem that is never force-split.
- Implementation and its test are one todo.
- Only column-zero `- [ ] <N>.` rows count as todos. A heading, paragraph, or plain bullet is not a task.
- A todo gated by an open question states the gate in its `Acceptance` or is closed with `- [~]` and a nested `Unmet: <gap>`.

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

One commit per todo, using the repository's message convention, containing only that todo's write scope. State whether evidence files are committed or ignored, and whether a wave lands as one merge. The commit line in each todo and this strategy must agree.

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

`Auto-execute: yes` requires the plan file, a passing structural self-check, an approved or converged review, no opt-out, and no open owner-decision. When the bundle still carries an open question that needs the user, the handoff is `Auto-execute: no (<the open question>)`.

## 12. Checkbox States

| State | Meaning |
|---|---|
| `- [ ]` | Open |
| `- [x]` | Done and verified |
| `- [~]` | Closed as blocked, with a nested `Unmet: <gap>` line |

Nested checkboxes are never tasks.

## 13. Worked Fragment

```markdown
# login-rate-limit - Work Plan
## TL;DR
- What you get: a per-IP limit of 5 requests per minute on `/login`, applied across all nodes.
- Why this approach: the existing Redis client already holds shared counters, and the debate kept it over an in-process counter.
- What it will not do: no account lockout, no CAPTCHA, no admin bypass screen.
- Effort: Short
- Risk: the shared counter adds a Redis dependency to the login path; a five-perspective debate ran before this plan and settled the storage question.
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

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The header order, the `IS-`/`GAP-` row meaning, the nine todo fields, the tier vocabulary, the fixed `F1` to `F4` rows, the success-criteria columns, the handoff fields, and the checkbox states | this package's plan grammar, restated from `instructions/skill/SKILL_AUTHORING.md` and the family's plan contract |
| The slug rule | this package's design, following the repository's `.hyper/` working-directory convention |
| The gate rule for a todo blocked by an open question | this package's design, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - the fragment's paths and commands are fictional and exist only to show the shape.
