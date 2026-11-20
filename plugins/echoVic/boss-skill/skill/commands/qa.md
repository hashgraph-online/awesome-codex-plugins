---
description: "Boss QA stage: test the feature or the current branch and record the evidence (qa-report.md), then stop."
argument-hint: "[feature | path] [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:qa — testing and the quality gate (QA)

Runs the tests, attacks the critical paths and writes `.boss/<feature>/qa-report.md`. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## What gets tested

Pick the first row that applies.

| Situation                           | Scope                                            |
| ----------------------------------- | ------------------------------------------------ |
| `.boss/<slug>/prd.md` exists        | Its acceptance scenarios                         |
| The user described what to test     | That description                                 |
| A git repository with a branch diff | The changed code and the paths that depend on it |
| No runnable code                    | Stop and suggest `dev`                           |

## Steps

1. Settle the feature slug. With no feature name, use the current branch name.
2. Settle the scope from the table above. It goes at the top of the report.
3. Dispatch the QA as a subagent: type `boss:boss-qa` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-qa.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It runs the tests and writes `.boss/<slug>/qa-report.md`. Every verification records the command,
   the observed exit code, the passed/failed/skipped counts and the failure details. Anything not run is
   marked unverified.
4. Apply Gate 1 in `references/quality-gate.md`: unit and integration tests pass, coverage is at least
   70%, there is no P0 or P1 bug, and E2E tests exist and pass. Report a failed gate as failed, with its
   evidence. Do not edit assertions or skip tests to make it pass.
5. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require qa-report.md --only qa-report.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
6. **Report.** End with exactly these lines, filled in:

   ```
   Stage: qa — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:ship
   ```
7. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:qa
/boss:qa user-auth
/boss:qa the checkout flow on mobile widths
```
