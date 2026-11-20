---
description: "Boss dev stage: implement tasks test-first with Frontend and Backend agents, then stop."
argument-hint: "<feature or request> [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep, LSP
---

# /boss:dev — implementation (Frontend and Backend)

Implements the tasks, test first. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Use it when

| Use `dev`                                        | Use something else               |
| ------------------------------------------------ | -------------------------------- |
| Tasks or a design exist and code must be written | The requirements are vague: `pm` |
| An existing project needs a new feature          | You only want tests run: `qa`    |

## Steps

1. Settle the feature slug.
2. Read `.boss/<slug>/tasks.md` and `architecture.md`. If they do not exist, use `prd.md`, then the
   request.
3. With a `tasks.md`, check the tasks for write-set conflicts and group the ones that are safe to run in
   parallel (`references/evidence-waves.md`).
4. If the blast radius meets a confirmation trigger in `references/evidence-waves.md`, ask the user
   before dispatching.
5. Dispatch the developers as subagents: `boss:boss-frontend` for frontend tasks and `boss:boss-backend`
   for backend tasks in a Claude Code plugin install, else general subagents given
   `agents/boss-frontend.md` or `agents/boss-backend.md`. Run them in parallel only when their write sets
   do not overlap. Each follows TDD: a failing test (RED), the least code that passes (GREEN), refactor.
6. At the end of each wave, run type checking, lint and the tests. Fix what fails before the next wave.
7. **Verify. This step is not optional.** There is no document to check for this stage; give the verifier the task list and the diff, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
8. **Report.** End with exactly these lines, filled in:

   ```
   Stage: dev — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:qa
   ```
9. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:dev user-auth
/boss:dev add card payments to the checkout
```
