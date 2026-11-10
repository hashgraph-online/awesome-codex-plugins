# QA matrix

The leader lane. The reviewer reads code; the leader runs it. A row is one criterion exercised on the real surface, and a row without a real observation is not evidence.

## Contents

1. Find the real surface
2. Matrix columns
3. Criterion rows
4. Raw observation
5. `N/A` and `unproven`
6. Cleanup
7. Depth by risk

## 1. Find the real surface

Read the project's own manifests and configuration and write down the commands before running anything.

- What builds it, what runs it, what tests it: `package.json` scripts, `Makefile`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `justfile`, a `bin/` or `scripts/` directory, CI workflow files.
- How it is started for a manual check: a dev server, a CLI binary, a library entry point, a queue consumer.
- What state it needs: a database, a fixture, a seed command, a fake external service.
- What the change touches: a network call, a file format, a migration, a permission boundary, a user-facing surface.

Prefer the project's declared commands over invented ones. A command taken from CI is better evidence than one composed by hand. When the project has no command for something the change affects, say so and exercise the closest real surface.

## 2. Matrix columns

Every row has all of these columns. A missing column is an incomplete row.

| Column | Content |
|---|---|
| Criterion | What the row checks, in one line |
| Scenario | The exact input, user action, or command, including the awkward part |
| Expected | What should happen, written before the run and derived from the goal or the constraint |
| Observed | The raw result: status code, body, exit code, output lines, screenshot path, error text |
| Verdict | `pass`, `fail`, `unproven`, or `N/A` |
| Artifact | A path, a command with its output captured in the report, or a screenshot file |
| Identity | The content identity the row ran against |
| Cleanup | What was created and what was removed |

Write `Expected` before `Observed`. Filling it afterwards turns the row into a description of whatever happened.

## 3. Criterion rows

The matrix must cover these rows when they apply, plus one row per goal-specific criterion the change introduces. Add rows; do not replace these.

| Row | Checks |
|---|---|
| Goal | The primary path the goal describes works end to end |
| Changed path | The specific branch, endpoint, flag, or component the diff touches behaves as the goal says |
| Normal input | A realistic input, not a toy one |
| Empty or absent input | Nothing supplied, an empty collection, a missing optional field |
| Boundary | The smallest, largest, and off-by-one values that matter here |
| Malformed input | Wrong type, truncated, wrong encoding, unexpected field, a value outside the allowed set |
| Failure path | The dependency fails, returns an error, times out, or is unreachable |
| Concurrency or repeat | Two callers at once, the same request twice, a retried operation |
| Permission and authz | A caller without the right is refused, and the refusal does not leak data |
| Existing behavior | The previous behavior that must not change still works |
| Tests | The project's test command runs, and the new tests actually exercise the change |
| Build and static checks | The build, type check, and lint the project declares |

The last two are gates rather than niceties: a change whose tests do not run, or whose declared build fails, is not `passed`.

## 4. Raw observation

- Quote the actual output. Truncate only in the middle, keep the head and the failing tail, and say where the truncation happened.
- Record the exit code next to every command.
- For a rendered surface, save the screenshot and name the viewport, theme, and input method.
- For an API, keep the status line, the relevant headers, and the body. Do not summarize a body you did not read.
- For a timing or memory claim, record the measurement method, the number of runs, and the spread, not a single number presented as the value.
- Never write "works fine". Write what was sent and what came back.

## 5. `N/A` and `unproven`

`N/A` is allowed only with a reason tied to this goal and this change.

- Good: "Concurrency row: `N/A`. This change only renames a constant used at import time; no shared mutable state is added or touched, and the changed module has no request path."
- Bad: "Concurrency: `N/A`, not applicable."
- Bad: "Failure path: `N/A`, tested by the author." A claim by the author is not an exemption.

`unproven` is the honest outcome when the row applies but could not run. Name the missing capability, the exact command that failed, and what would settle it. A required row left `unproven` makes the verdict `inconclusive`, not `passed`.

## 6. Cleanup

Every row that creates state lists what it created: a temporary file, a database row, a background process, a queue message, a container, a branch.

- Remove it, and record the removal command and its exit code.
- A process started for the check is stopped; a port it bound is released.
- State that could not be removed is named in the report and in the closing summary, with the path or identifier.
- Never leave a migrated database, a seeded table, or a running server behind silently.

## 7. Depth by risk

Match the effort to what the change can break.

| Risk | Examples | Depth |
|---|---|---|
| Low | A constant, a message string, an internal rename with no behavior change | Goal row, existing behavior, build and tests |
| Medium | A new branch in existing logic, a validation rule, a query change | The low set plus normal, empty, boundary, and malformed input |
| High | Authz, payments or money, data deletion, a migration, a public interface, concurrency, anything that touches secrets or personal data | The full table, with the failure, concurrency, and permission rows exercised, not reasoned about |

The risk level is written in the report next to the matrix so a reader can see how much the verdict leans on.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Hands-on QA on the real surface, with a matrix row per criterion and a cleanup column | `dbc-hbin/omp-ulw@74df40f review-work` (mechanism reference, re-authored) |
| `N/A` needing a goal-specific reason | same source, re-authored |
| Preferring the project's declared commands over invented ones | this package's chosen design |
| The risk table and the `unproven` outcome | this package's chosen design |

### Evidence grade

`MECHANISM` for the matrix shape and the `N/A` rule. `LOCAL` for the columns, the row list, the risk table, and the `unproven` handling. The risk table is guidance, not a measured threshold.
