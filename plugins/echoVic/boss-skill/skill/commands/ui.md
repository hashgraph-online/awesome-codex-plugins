---
description: "Boss UI stage: produce a UI spec and a machine-readable design contract, then stop."
argument-hint: "<feature or request> [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:ui — UI design (UI Designer)

Writes `.boss/<feature>/ui-spec.md` and `.boss/<feature>/ui-design.json`. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Use it when

| Use `ui`                                   | Use something else                     |
| ------------------------------------------ | -------------------------------------- |
| The feature has screens that need a spec   | An API or CLI project: skip this stage |
| An existing screen needs states and tokens | You want code written: `dev`           |

## Steps

1. Settle the feature slug.
2. Read `.boss/<slug>/prd.md`. If it does not exist, work from the request and say so in the artifact.
3. Dispatch the UI Designer as a subagent: type `boss:boss-ui-designer` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-ui-designer.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It writes `.boss/<slug>/ui-spec.md` and `.boss/<slug>/ui-design.json`, and `.boss/<slug>/prototype/`
   only if the user agrees to an interactive prototype.
4. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require ui-spec.md --only ui-spec.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
5. **Report.** End with exactly these lines, filled in:

   ```
   Stage: ui — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:review
   ```
6. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## HTML prototype

Before designing, the UI Designer asks whether the user wants an interactive prototype. With a yes, it
writes `.boss/<slug>/prototype/`, serves it on `127.0.0.1` and the user picks a variant in the browser.
The server stops once the design is confirmed; the files stay.

## Examples

```
/boss:ui user-auth
/boss:ui the settings page needs empty and error states
```
