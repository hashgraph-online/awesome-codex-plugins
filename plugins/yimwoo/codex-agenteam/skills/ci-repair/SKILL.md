---
name: ci-repair
description: Fix CI failures by fetching GitHub Actions logs, dispatching dev to fix, verifying locally, and pushing.
---

# AgenTeam CI Repair

Fix a CI failure on a pull request. Fetches the failure context from
GitHub Actions, dispatches the dev role with bounded logs, verifies
the fix locally, and pushes only if verification passes.

GitHub Actions only. The workflow is a bounded, resumable
monitor → diagnose → repair → verify loop.

## Loop Contract

- Defaults: `max_repair_cycles: 3`, `max_elapsed_minutes: 90`, and a
  five-minute CI polling interval. User-supplied lower budgets win.
- Persist every cycle in `.agenteam/ci-repair/pr-<pr_number>.json`, keyed by
  `head_sha`. Record the run ID, failed jobs, repair attempt, local verification,
  pushed SHA, last heartbeat, and stop reason.
- Emit a heartbeat while waiting for a role or CI. If the host cannot remain
  active, schedule a follow-up/automation and stop cleanly instead of holding a
  silent blocking wait.
- Before replaying a repair after restart, compare the checkpoint head SHA and
  current PR head. Never repeat a completed repair for the same SHA.
- Stop explicitly on success, exhausted cycle/elapsed budget, changed PR head,
  unavailable evidence, or required human approval.

## Process

### 1. Accept Input

Get the PR reference from the user:
- PR number: `$ateam:ci-repair #42`
- Branch name: `$ateam:ci-repair feature/add-auth`
- Nothing: use the current branch

### 2. Resolve PR

Resolve the input to a canonical tuple: `pr_number`, `pr_url`,
`pr_branch`, `head_sha`.

**If PR number given:**
```bash
gh pr view <number> --json number,url,headRefName,headRefOid
```

**If branch given or current branch:**
```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)  # if no input
gh pr list --head <branch> --json number,url,headRefName,headRefOid --limit 1
```

If no PR found: "No PR found for branch `<branch>`. Push and create
a PR first, then retry." Stop.

Extract:
- `pr_number` from `number`
- `pr_url` from `url`
- `pr_branch` from `headRefName`
- `head_sha` from `headRefOid`

### 3. Check CI Status

Get the latest CI run for the PR's current head commit:

```bash
gh run list --commit <head_sha> --limit 5 \
  --json status,conclusion,databaseId,name,createdAt
```

Check the **latest run for this exact commit**:

- **`failure`** → proceed to fetch context (step 4)
- **`success`** → "CI is passing on the current head commit. No
  repair needed." Stop.
- **`in_progress`** or **`queued`** → Persist the run ID and heartbeat, then
  monitor it within the elapsed budget. Poll no more frequently than the
  configured interval. If this invocation cannot keep monitoring, arrange a
  follow-up and stop with reason `ci_wait_scheduled`.
- **No runs found** → "No CI runs found for commit `<head_sha>`.
  Push or re-run CI, then retry." Stop.

### 4. Fetch Failure Context

Get structural info (which jobs/steps failed):

```bash
gh run view <run-id> --json jobs
```

Get truncated logs for failed steps:

```bash
gh run view <run-id> --log-failed 2>/dev/null | tail -400
```

**Context budget:**
- Max 3 failed jobs included
- Max 100 lines per failed step
- Max 400 total log lines
- If exceeded: prefer the most recent failed step and the final
  error-bearing lines
- If logs unavailable (permissions, expired): fall back to structural
  info only (job name, step name, exit code)

**Format the failure summary:**

```
## CI Failure Summary

**PR:** #<number> (<branch>)
**Run:** <run-url>
**Commit:** <head_sha>
**Status:** failure

### Failed Job: <job-name> (<runner>)

**Failed Step:** <step-name> (exit code <N>)

<step log output, last 100 lines>
```

If multiple jobs failed, include up to 3, each with their failed
step logs.

### 5. Git Preflight and Branch Checkout

Before dispatching dev, ensure a clean state on the correct branch.

1. **Preflight:**
   ```bash
   bash <plugin-dir>/scripts/git-isolate.sh preflight
   ```
   - `not-a-git-repo` → stop. CI repair requires git.
   - `dirty-worktree` → stop. Tell user: "Uncommitted changes
     detected. Stash or commit before CI repair to avoid staging
     unrelated files."
   - `detached-head` → stop. Tell user: "Detached HEAD. Checkout
     a branch before CI repair."

2. **Checkout the PR branch:**
   ```bash
   git fetch origin <pr_branch>
   git checkout <pr_branch>
   git pull origin <pr_branch>
   ```
   If already on the PR branch and up to date, skip checkout.

3. **Record repair baseline:**
   ```bash
   REPAIR_BASELINE=$(git rev-parse HEAD)
   ```
   Used in step 8 to commit only the repair changes.

### 6. Dispatch Dev

Dispatch the dev role as a subagent with:
- The CI failure summary (from step 4) as primary context
- Instruction: "Fix the CI failure described above. Only modify files
  needed to resolve the failing test/check. Do not refactor or add
  features beyond the fix."

Append systematic debugging guidance directly to the dev prompt:
"Use a systematic debugging approach: reproduce the failure locally
if possible, identify the root cause from the CI logs, then fix.
Do not guess — trace the error."

**Note:** The `hotl-skills` adapter is NOT used for standalone CI
repair invocations — it requires a `--run-id` with pipeline state
that doesn't exist here. Debugging guidance is injected directly
into the prompt instead.

### 7. Local Verification

After dev completes the fix, run local verification:

```bash
python3 <runtime>/agenteam_rt.py final-verify-plan
```

This returns the project's verify commands (auto-detected or
configured).

- **Verify commands found:** Run each command. If ALL pass → proceed
  to push (step 8). If ANY fail → do NOT push. Show failure output.
  Tell user: "Local verification failed. The fix may be incomplete."
  Stop.
- **No verify commands found:** Tell user: "No local verification
  available. The fix is unverified locally. Push anyway? (yes/no)"
  Do NOT silently push unverified fixes. Wait for explicit user
  confirmation.

### 8. Push and Report

Only if local verify passed (or user confirmed unverified push):

Always re-read `headRefOid` immediately before committing and pushing. It must equal
the checkpoint's expected head SHA; otherwise stop with `head_changed` so a
concurrent contributor's update is never overwritten.

```bash
# Commit only files changed since repair baseline
git diff --name-only $REPAIR_BASELINE | xargs git add
git commit -m "[ateam:ci-repair] Fix CI failure in <failed-step>"
git push origin <pr_branch>
```

If no files changed since baseline: "Dev made no changes. The fix
may require a different approach." Do NOT create an empty commit.
Stop.

**Success report:**
```
CI repair pushed to <pr_branch>.
- Fixed: <brief description of what dev changed>
- Files changed: <list of files modified since baseline>
- Local verify: passed (or: unverified — user confirmed)
- PR: <pr_url>
- CI will re-run automatically.
```

After pushing, store the new head SHA and return to step 3. Continue the bounded
loop until CI succeeds or `max_repair_cycles`/`max_elapsed_minutes` is reached.
Each new failing SHA gets its own diagnostic and repair record; the same SHA is
never repaired twice after a successful local verification and push.

**Failure report (local verify failed):**
```
CI repair NOT pushed — local verification failed.
- Failure: <verify output excerpt>
- The fix may be incomplete. Review and retry with:
  $ateam:ci-repair <pr_number>
```

## Error Handling

- If `gh` CLI is not installed: show install instructions and stop
- If `gh` is not authenticated: tell user to run `gh auth login`
- If the PR branch doesn't exist locally or remotely: show error
- If the CI run has no log access (private repo, expired logs):
  fall back to structural info only
- If dev makes no changes: report and stop (don't empty-commit)
- If push fails (permissions, protected branch): show error and
  suggest manual push

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin: `<plugin-install-path>/runtime/agenteam_rt.py`
