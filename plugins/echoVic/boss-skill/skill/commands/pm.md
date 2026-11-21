---
description: "Boss PM stage: turn a request into a verified PRD (prd.md), then stop."
argument-hint: "<what to build> [--quick] [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# /boss:pm — requirements (PM)

Turns a request into `.boss/<feature>/prd.md`. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Use it when

| Use `pm`                                        | Use something else                         |
| ----------------------------------------------- | ------------------------------------------ |
| There is an idea but the requirements are vague | A PRD already exists: start at `architect` |
| You want requirements someone can test against  | A small bug fix: no Boss stage is needed   |

## Steps

1. Settle the feature slug (short English kebab-case) and create `.boss/<slug>/`.
2. Clarify, unless `--quick` or the user said not to ask: the request must say what to build, for whom
   and the core scenario. Ask for what is missing, one question at a time.
3. Dispatch the PM as a subagent: type `boss:boss-pm` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-pm.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It writes `.boss/<slug>/prd.md`.
4. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require prd.md --only prd.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
5. **Report.** End with exactly these lines, filled in:

   ```
   Stage: pm — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:architect
   ```
6. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:pm an asset manager for designers
/boss:pm user authentication --quick
/boss:pm team invitations --stop-after architect
```
