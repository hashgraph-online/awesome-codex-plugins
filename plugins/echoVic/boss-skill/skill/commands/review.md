---
description: "Boss review stage: review the current branch's diff, a code path, or an architecture document, then stop. Read-only."
argument-hint: "[feature | path] [--base <ref>] [--continue] [--stop-after <stage>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:review — technical review (Tech Lead)

Reviews code or a design and writes the findings to `.boss/<feature>/`. It changes no source file. Runs this stage only, unless `--continue` or `--stop-after` is given.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## What gets reviewed

Pick the first row that applies.

| Situation                                               | Review                      | Writes                      |
| ------------------------------------------------------- | --------------------------- | --------------------------- |
| The user named a file or directory                      | Code                        | `code-review.md`            |
| `.boss/<slug>/architecture.md` exists, or pipeline mode | Design                      | `tech-review.md`, `plan.md` |
| A git repository whose branch differs from its base     | Diff                        | `code-review.md`            |
| None of these                                           | Ask the user what to review | nothing                     |

## Steps: diff or code review

1. Settle the feature slug. With no feature name, use the current branch name.
2. Find the change. The base is `--base <ref>` if given, else the merge base with the default branch
   (`git merge-base HEAD origin/<default>`, or the local default branch when there is no remote). The
   change is `git diff <base>...HEAD` plus uncommitted work. For a named path, it is that path.
3. Dispatch the Tech Lead as a subagent: type `boss:boss-tech-lead` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-tech-lead.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   Tell it this is a read-only diff review (the `code-review.md` contract in its file), and give it the
   base, the head and the changed files. It writes `.boss/<slug>/code-review.md`.
4. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require code-review.md --only code-review.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
5. **Report.** End with exactly these lines, filled in:

   ```
   Stage: review — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:dev to fix blockers, else /boss:qa
   ```
6. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Steps: design review

1. Settle the feature slug.
2. Dispatch the Tech Lead as a subagent: type `boss:boss-tech-lead` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-tech-lead.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It writes `.boss/<slug>/tech-review.md`, and when the verdict is not a rejection, `.boss/<slug>/plan.md`.
3. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require tech-review.md,plan.md --only tech-review.md,plan.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
4. **Report.** End with exactly these lines, filled in:

   ```
   Stage: review — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: /boss:tasks
   ```
5. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:review
/boss:review src/auth
/boss:review --base release/2.4
/boss:review user-auth --continue
```
