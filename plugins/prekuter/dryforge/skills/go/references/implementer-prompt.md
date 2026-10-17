# implementer-prompt.md — the implementer subagent prompt

One subagent implements one task, **verified-first** (test-first where it fits), in its pinned
worktree, then commits and reports. The prompt has **required elements** (mandated — the scaffold)
and **wording you adapt** (the example below is one phrasing, not a fixed script).

## Required elements (every implementer prompt must pin)

- **Task contract** — the task's goal and **work targets (files | state | external resource)**,
  from the plan (behavioral, not premature code). **Defer plan-owned decisions to the plan — do not
  restate them.** Names (symbols, files, endpoints), shared conventions, and interfaces the plan
  already fixes must be referenced ("follow the plan's naming"), not re-specified in the prompt: a
  prompt that restates them in different words makes parallel implementers diverge. Pin only what
  *this* task adds. For a task that declares **no file diff** (a state-change / operational /
  external-config target), verification is by **commit message + captured external evidence**
  (command exit / render / API or state response), not necessarily a file diff — the
  captured-evidence floor still holds.
- **Spec section** — the spec requirement this task realizes, **quoted inline in this prompt**
  (the task worktree has no `.dryforge/` files to read — `.dryforge/` is gitignored). Build to the
  spec, not just to the task line ("correct" = matches the spec).
- **Hard gates** — the relevant non-negotiable constraints from the handoff.
- **Verify-first, right-sized** — drive the work against the task's **real verification gate**: the
  project's verify commands, discovered by the producer (which may be a typecheck/lint/test set, a
  build/run, or a single command — not every stack has all three; never assume the triad).
  **Consume the producer-set tier — don't re-derive "is this risky?" from scratch.** This task is
  classified RISK=<tier> by the producer. RISKY → test-first RED→GREEN against the project's verify
  commands. MECHANICAL → a confirming check against the gate, no RED ceremony. NONE → appropriate
  evidence (build / validate / render / apply), no unit-test ceremony. (Test-first means: failing
  test → confirm **RED** → minimal implementation → confirm **GREEN** → refactor.) If the tier
  looks wrong for what you find, return `DONE_WITH_CONCERNS` and say so — do not silently upgrade or
  skip. If the producer omitted the tier, judge risk yourself at build time. The floor is
  *captured-evidence verification*, not ceremony — **but testable behavior with real risk left
  untested is still needs-fix** (the tier sizes the ceremony, it is not an excuse to skip tests that
  matter).
- **Shared-write constraints** — which files are this task's to write, and which **not** to
  touch (the shared/registration files a later wiring step owns).
- **Worktree pin** — the absolute worktree path + branch; **omit isolation** (do *not* enable the
  platform's worktree-isolation dispatch option — the orchestrator already
  created the worktree; see `orchestration.md`); verify with `git rev-parse --show-toplevel` before
  editing.
- **Report contract** — commit when done; return the structured summary below. Do not dump diffs.

## Example skeleton (one wording — adapt; the elements above are required)

```
Implement <task id / goal> in the worktree at <ABS PATH> (branch <name>).
First: `git rev-parse --show-toplevel` must equal <ABS PATH> — if not, stop and report.
Spec to satisfy: <spec slice>.  Hard gates: <relevant gates>.
Files yours to write: <...>.  Do NOT touch: <shared / registration files>.
Verify against the task's gate (the project's verify commands). This task is RISK=<tier>: RISKY →
test-first (failing test → RED → minimal impl → GREEN → refactor); MECHANICAL → confirming check, no
RED; NONE → appropriate evidence (build / validate / render / apply). If the tier looks wrong, return
DONE_WITH_CONCERNS. For a no-file-diff target, evidence is commit message + captured external
response. Run the project's verify commands; capture exit codes.
When done: commit, then return ONLY the structured summary. Do not inline diffs.
```

## Structured return

- `status`: `DONE` | `DONE_WITH_CONCERNS` | `NEEDS_CONTEXT` | `BLOCKED`
- `files_changed`: paths — or, for a declared no-file-diff task (state-change / operational /
  external-config), the work target touched plus the commit that records it
- `verification`: the **literal command(s) run and their exit codes** (evidence, not "passed") —
  for a testable task, the tests added + their run; for a non-unit-testable deliverable, the gate
  actually run (build / validate / render / ...). A claimed pass with no command/exit code is
  needs-fix; and **omitting tests on a task that has real testable behavior is needs-fix** (the
  no-test path is only for genuinely non-unit-testable or trivial work)
- `concerns`: anything the orchestrator should weigh (or what is blocking)

## escalate-don't-guess (for the implementer)

If the task is ambiguous, conflicts with the spec, or can't be done as written — **do not
guess or quietly improvise.** Return `NEEDS_CONTEXT` or `BLOCKED` with specifics; the
orchestrator decides and escalates to the user if needed. A wrong guess is worse than a stop.

You are in a fresh session with no live user conversation — do NOT ask the user directly. Return
`NEEDS_CONTEXT` or `BLOCKED` instead; the orchestrator relays escalations to the user.

**Honor any shared-resource expectation the task declares** (a fixture, a shared file/state, an
external resource the plan says should be in a given state). If you find that shared resource in an
unexpected state, return `BLOCKED` with the specifics — do not work around it silently.
