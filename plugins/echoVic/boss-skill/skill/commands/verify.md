---
description: "Boss verify: check existing .boss artifacts against their role contracts and report what fails. Read-only."
argument-hint: "[feature]"
allowed-tools: Agent, Task, Skill, Read, Write, Bash, Glob, Grep
---

# /boss:verify — contract verification (Verifier)

Checks the artifacts that already exist in `.boss/<feature>/` against the contracts of the roles that
wrote them. It changes no artifact and no source file.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## Steps

1. Settle the feature. With no name and one folder under `.boss/`, use it. With several, ask which.
2. Run the checker on the whole folder: `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<feature>`.
3. For each artifact present, dispatch the verifier (`boss:boss-verifier`, or a general subagent given
   `agents/boss-verifier.md`) with the artifact path, the role's agent file from the table in
   `references/contract-verification.md`, and the checker output.
4. Append the results to `.boss/<feature>/verification.md`, unless the user asked for no file changes.
5. Report each artifact's verdict and every failing requirement with its evidence. Fix nothing: name the
   entry that would (`/boss:pm` for `prd.md`, `/boss:qa` for `qa-report.md`, and so on). End with:

   ```
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   ```

## Examples

```
/boss:verify
/boss:verify user-auth
```
