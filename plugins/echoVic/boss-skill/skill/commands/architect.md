---
description: "Boss Architect stage: design the system from a PRD or a request (architecture.md), then stop."
argument-hint: "<feature or request> [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# /boss:architect — architecture (Architect)

Writes `.boss/<feature>/architecture.md`. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Use it when

| Use `architect`                                  | Use something else                           |
| ------------------------------------------------ | -------------------------------------------- |
| The requirements are clear and need a design     | The requirements are vague: start at `pm`    |
| An existing system needs a design for a new part | You want an existing design judged: `review` |

## Steps

1. Settle the feature slug.
2. Read `.boss/<slug>/prd.md`. If it does not exist, work from the request and say so in the artifact.
3. On an existing repository, read `agents/shared/tech-detection.md` and detect the stack first. The
   design must fit the code that is already there.
4. Dispatch the Architect as a subagent: type `boss:boss-architect` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-architect.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It researches before it designs, and writes `.boss/<slug>/architecture.md`.
5. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require architecture.md --only architecture.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
6. **Report.** End with exactly these lines, filled in:

   ```
   Stage: architect — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:ui, or /boss:review for an API or CLI project
   ```
7. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:architect user-auth
/boss:architect add rate limiting to the public API
```
