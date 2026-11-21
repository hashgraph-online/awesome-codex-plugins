---
description: "Boss ship stage: open a pull request for the current branch, or deploy with --deploy. Writes deploy-report.md."
argument-hint: "[feature] [--pr | --deploy] [--platform <name>] [--base <ref>] [--lang <code>]"
allowed-tools: Agent, Task, Skill, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:ship — pull request or deployment (DevOps)

Ships the work and writes `.boss/<feature>/deploy-report.md`. This is the last stage.

**Boss skill directory:** `${CLAUDE_PLUGIN_ROOT}/skill`. Every path below is relative to it. If the line
above still shows a `${...}` variable, you reached this file through the `boss` skill: use that skill's
base directory instead.

## What ship does

Pick the first row that applies.

| Situation                                 | Target                                                                     |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| `--deploy` or `--platform <name>`         | Deploy                                                                     |
| `--pr`, or a git repository with a remote | Pull request                                                               |
| No remote and no deploy flag              | Nothing leaves the machine: the report says "Not deployed" and how to ship |

Invoking `/boss:ship` directly is the user's yes for the target in the table. When the pipeline reaches
`ship` on its own, ask before pushing, opening the pull request or deploying.

## Steps: pull request

1. Settle the feature slug. With no feature name, use the current branch name.
2. Check `.boss/<slug>/qa-report.md`. If it is missing, warn that QA has not run and continue only if
   the user says so.
3. Dispatch the DevOps agent as a subagent: type `boss:boss-devops` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-devops.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   Tell it the target is a pull request (the "Pull Request 模式" section of its file) and give it the
   base (`--base <ref>`, else the default branch). It never pushes to the default branch, stops on a
   conflict or a failing check, and writes `.boss/<slug>/deploy-report.md` with the pull request URL, the
   base and head commits, and each command with its exit code.
4. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require deploy-report.md --only deploy-report.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
5. **Report.** End with exactly these lines, filled in:

   ```
   Stage: ship — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: none; the pull request is open
   ```
6. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Steps: deployment

1. Settle the feature slug and check `qa-report.md` as above.
2. Pick the platform. An existing config wins: `vercel.json` or `.vercel/` (Vercel), `wrangler.toml`
   (Cloudflare), `render.yaml` (Render), `netlify.toml` (Netlify), `railway.json` or `railway.toml`
   (Railway), `fly.toml` (Fly.io). `--platform` overrides it. With neither, recommend one by project
   type as `agents/boss-devops.md` describes, and load the matching `devops/deploy-<platform>` skill.
3. Dispatch the DevOps agent as a subagent: type `boss:boss-devops` in a Claude Code plugin install, else a
   general subagent whose prompt is the text of `agents/boss-devops.md`. Its prompt must state the Boss skill
   directory as an absolute path, the feature folder, the inputs to read and the artifact language.
   It builds, deploys, runs the health check and writes `.boss/<slug>/deploy-report.md`.
4. Apply Gate 2 in `references/quality-gate.md` for web projects: the build succeeds, the service
   answers with HTTP 2xx, Lighthouse performance is at least 80 and API P99 is under 500 ms.
5. **Verify. This step is not optional.** Run `node "${CLAUDE_PLUGIN_ROOT}/skill/scripts/check-artifacts.mjs" .boss/<slug> --require deploy-report.md --only deploy-report.md`, then dispatch the verifier (`boss:boss-verifier`, or a
   general subagent given `agents/boss-verifier.md`) as `references/contract-verification.md` describes.
   Send failures back to the role agent, at most twice. Append the result to `.boss/<slug>/verification.md`.
6. **Report.** End with exactly these lines, filled in:

   ```
   Stage: ship — verified | not verified
   Artifact: <path, or "none">
   Role agent: dispatched | done inline — <why>
   Checker: <passed>/<total> rules, exit <code> | not run — <why>
   Verifier: PASS | FAIL | not run — <why>
   Next: none; the deployment is live
   ```
7. **Stop or continue.** In stage mode, stop here. With `--continue`, `--stop-after`, or inside the full
   pipeline, go on as `references/continuation-chain.md` describes, but only if the stage is verified.

## Examples

```
/boss:ship
/boss:ship --base release/2.4
/boss:ship --deploy
/boss:ship --platform vercel
```
