---
description: "Boss tasks stage: break a plan into atomic tasks with file-level write sets (tasks.md), then stop."
argument-hint: "<feature or request> [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:tasks — task breakdown (Scrum Master)

Writes `.boss/<feature>/tasks.md`. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Use it when

| Use `tasks`                                        | Use something else                     |
| -------------------------------------------------- | -------------------------------------- |
| A plan or design exists and needs splitting        | There is no design yet: `architect`    |
| Work must be divided so agents can run in parallel | One small change: go straight to `dev` |

## Steps

1. Settle the feature slug.
2. Read `.boss/<slug>/plan.md`. If it does not exist, fall back to `tech-review.md` and
   `architecture.md`, then `prd.md`, then the request.
3. Repo preflight: collect the git state, the CI setup, the test commands and the stack, for `tasks.md`.
4. Dispatch the Scrum Master as a subagent: type `boss:boss-scrum-master` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-scrum-master.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It writes `.boss/<slug>/tasks.md` with the task list, file-level write sets, test cases, risk levels,
   blast radius, evidence waves and the contract matrix.
5. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require tasks.md --only tasks.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
6. **Report.** End with exactly these lines, filled in:

   ```
   Stage: tasks — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:dev
   ```
7. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:tasks user-auth
/boss:tasks split the payment migration into parallel tasks
```
