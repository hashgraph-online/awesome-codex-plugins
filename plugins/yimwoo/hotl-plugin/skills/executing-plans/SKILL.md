---
name: executing-plans
description: Use when executing an implementation plan linearly with explicit human checkpoints between batches of tasks.
---

# Executing Plans (Linear with Checkpoints)

Execute the plan task by task. Pause after every 3 tasks for human review.

This remains the explicit manual-checkpoint profile. New host-native or fallback runs may enter through `governed-execution`; when they do, use its selected driver for lifecycle calls, sensitive-action decisions, budgets, receipts, and reconciliation while preserving every checkpoint in this skill.

## Workflow File Resolution

Resolve which workflow file to execute:

1. If the user specified a filename → use that file
2. Else, glob for canonical workflows in `docs/plans/*-workflow.md`:
   - **One match** → use it automatically
   - **Multiple matches** → if one is clearly the newest revision for the same semantic slug, prefer it; otherwise list them and ask the user to pick
3. If no canonical matches, glob for legacy `hotl-workflow*.md` in project root:
   - **One match** → use it automatically
   - **Multiple matches** → list them and ask the user to pick
4. **No matches** → stop and ask the user to create or name a workflow file

## Branch/Worktree Preflight

After resolving the workflow file, run this preflight **before executing any steps**:

```
1. Is this a git repo with at least one commit?
   - No  → log "Skipping branch setup (no git history)" → proceed to step execution
   - Yes → continue

2. Check for uncommitted changes
   - First, exclude HOTL-owned transient artifacts from the dirty check:
     • docs/plans/*-workflow.md (canonical workflow files)
     • hotl-workflow-*.md (legacy workflow files)
     • docs/designs/*.md (canonical design docs from brainstorming)
     • docs/plans/*-design.md, docs/plans/*-plan.md (legacy design docs from brainstorming)
     • .hotl/ (runtime state, reports, cache)
   - If only HOTL artifacts are dirty → treat as clean, continue
   - If non-HOTL dirty files exist:
     • If dirty_worktree: allow in workflow frontmatter → proceed without prompting
     • Otherwise → HARD-FAIL. Tell the user which non-HOTL files are dirty. Offer choices:
       a. Clean up manually, then re-run
       b. Stash manually, then re-run
       c. Explicitly approve HOTL to stash and continue
   - Clean → continue

3. Determine branch name
   - If branch: field exists in workflow frontmatter → use it
   - Otherwise → derive `hotl/<slug>` from the workflow filename
     • Canonical: strip `YYYY-MM-DD-` prefix and `-workflow.md` suffix from `docs/plans/YYYY-MM-DD-<slug>-workflow.md`
     • Legacy: strip `hotl-workflow-` prefix and `.md` suffix from `hotl-workflow-<slug>.md`

4. Capture authoring origin
   - Record the current branch name (if any) and current `HEAD` commit as the workflow's authoring origin
   - If the current branch is neither `main` nor `master`, and the workflow frontmatter does not already set `branch:` or `worktree:`, PAUSE and ask:
     a. Continue on the current branch in this checkout
        → set `branch: <current-branch>` and `worktree: false`
     b. Use HOTL's isolated execution branch/worktree (recommended)
        → leave `worktree: true` and let HOTL derive `hotl/<slug>` unless the user wants a custom branch name
     c. Use a custom execution branch
        → set `branch: <user-branch>` and keep worktree isolation unless the user explicitly opts out
   - Explain clearly: the authoring checkout and the execution checkout can differ. HOTL can execute in a separate worktree while leaving the current checkout untouched

5. Determine isolation mode
   - If `worktree: host` in frontmatter → stay on the current checkout's current feature branch exactly as provided by the host tool; reject `main` and `master`
   - If `worktree: false` in frontmatter → stay in the current checkout and use a dedicated branch there
   - If the current checkout is already a named linked git worktree, and the workflow frontmatter does not set `branch:` or `worktree:`, use host mode automatically to avoid stacking another worktree
   - Otherwise → use an isolated git worktree by default

6. Check if the target branch/worktree already exists locally
   - Current helper behavior: existing branch/worktree collisions are a hard stop, not an interactive reuse/recreate flow
   - If the helper reports an existing branch/worktree conflict, stop and ask the user whether to reuse manually, delete+recreate manually, or abort
   - Does not exist → create (no prompt)

7. Resolve the execution root with `scripts/hotl-prepare-execution-root.sh <workflow-file> --executor-mode <mode>`
   - The helper returns JSON with: `branch`, `repo_root`, `execution_root`, `workflow_path`, `source_workflow_path`, `source_branch`, `source_head`, `worktree_path`
   - By default it creates a linked git worktree for the branch, copies the current workflow into that worktree, and returns that worktree as `execution_root`
   - If `worktree: false` in frontmatter → create/switch to the dedicated branch in the current checkout and return the repo root as `execution_root`
   - If `worktree: host` in frontmatter → keep the current branch and return the current checkout as `execution_root`; if `branch:` is set, it must match the current branch
   - If `branch:` matches the currently checked-out branch while worktree isolation is still enabled, the helper must STOP with a clear message telling the user to set `worktree: false` or `worktree: host` for same-branch continuity
8. Change into `execution_root`
   - Every later git command, runtime call, Codex helper call, and review command for this run MUST execute from that directory
```

**Rules:**
- No auto-stash. Hidden state mutation weakens governance.
- Existing branch/worktree collisions do not currently auto-prompt; treat them as a stop-and-ask condition until interactive reuse/recreate is implemented.
- Non-git repos skip entirely — HOTL works without git ceremony.
- Run HOTL structural lint (`scripts/document-lint.sh`) automatically on the workflow file before any git mutation or step execution. If lint fails, STOP and show all errors. If lint passes, continue silently.

## Typed Verification

The `verify` field supports 4 types. A scalar string is shorthand for `type: shell`. If `verify` is a list, ALL checks must pass.

- **type: shell** — run command, check exit code, capture stdout/stderr
- **type: browser** — use browser tooling with url+check; if unavailable, downgrade to type: human-review with check text as prompt
- **type: human-review** — `hotl-rt step N verify` returns a `human review required: ...` block reason and pauses the run; show the prompt, wait for approval, then persist it with `hotl-rt gate N approved|rejected --mode human` (never auto-approve)
- **type: artifact** — check path exists, evaluate assert (kind: exists | contains | matches-glob)
  For `matches-glob`, `path` must be the directory and `value` must be a filename glob only; values like `src/*` are invalid and should be authored as `path: src`

## Execution State Persistence

All state persistence is handled by the `hotl-rt` shared runtime (`runtime/hotl-rt`). This executor calls `hotl-rt` for all state transitions:

- `hotl-rt init <workflow-file> --executor-mode executing-plans ...` — at run start
- `hotl-rt step N start --run-id <run-id>` — before each step
- `hotl-rt step N verify --run-id <run-id>` — after each step's action
- `hotl-rt step N retry --run-id <run-id>` / `hotl-rt step N block --reason "..." --run-id <run-id>` — on failure
- `hotl-rt gate N approved|rejected --run-id <run-id>` — at gate steps
- `hotl-rt finalize --json --run-id <run-id>` — at run completion

The runtime owns `.hotl/state/<run-id>.json` and `.hotl/reports/<run-id>.md`. Agents do not manage these files directly. Runtime calls happen before the corresponding chat or progress UI update.

Use the same HOTL runtime and script path resolution order defined in `skills/loop-execution/SKILL.md`. Do not assume `runtime/` or `scripts/` exist in the user's project checkout.

To resume an interrupted executing-plans run, use the host tool's native resume entry point.
- **Codex:** ask me to use `$hotl:resuming` on the workflow file
- **Claude Code:** `/hotl:resume <workflow-file>`

## Process

1. Resolve and read the workflow (see above)
2. Run Branch/Worktree Preflight (see above), capture its JSON result, and change into `execution_root`
3. Run `hotl-rt init <workflow-file> --executor-mode executing-plans --repo-root <repo-root> --execution-root <execution-root> --source-workflow-path <source-workflow-path> --source-branch <source-branch|null> --source-head <source-head|null> --worktree-path <worktree-path|null> --branch <branch>` to initialize state and report
4. Capture the run id from stdout, then pass `--run-id <run-id>` (or set `HOTL_RUN_ID=<run-id>`) on every later runtime/helper call for this run
5. Execute tasks in order, 3 at a time:
   - `hotl-rt step N start --run-id <run-id>` before each step
   - Execute the action
   - `hotl-rt step N verify --run-id <run-id>` to run typed verification
   - If verify reports `human review required: ...`, pause and do not continue until `hotl-rt gate N approved|rejected --mode human --run-id <run-id>` succeeds
   - On failure: `hotl-rt step N retry --run-id <run-id>` or `hotl-rt step N block --reason "..." --run-id <run-id>`
   - On gate: `hotl-rt gate N approved|rejected --run-id <run-id>`
6. After each batch: run review checkpoint (see below), then show what was done, ask "Continue to next batch?"
7. On failure: stop and report — never silently skip a failed step
8. When complete: run final review checkpoint (see below), invoke `hotl:verification-before-completion`, then `hotl-rt finalize --json --run-id <run-id>`, render the final summary via `scripts/render-execution-summary.sh`, and if git isolation was used (or the user asks what to do next) invoke `hotl:finishing-a-development-branch` with the same `run_id`

## Review Checkpoints

Record `git rev-parse HEAD` as the review base before starting each batch.

### After Each Batch

After all steps in the batch have passed verification:
1. Invoke `requesting-code-review` to dispatch the `code-reviewer` agent
   - Review type: checkpoint
   - Review base: the recorded pre-batch HEAD
   - Steps reviewed: the batch step numbers
2. When findings return, invoke `receiving-code-review`
   - Follow Verify → Evaluate → Respond → Implement
3. Resolve all BLOCK findings before proceeding to the next batch

### Before Final Completion

A final review is required unless the most recent review already covers all current changes and no code changed afterward.

1. Invoke `requesting-code-review` with review type: final
   - Review base: branch point or last review base, whichever is more recent
2. When findings return, invoke `receiving-code-review`
3. Resolve all BLOCK findings before finalizing
4. If fixes after the last review changed scope, constraints, or risk_level, request a scoped follow-up review before completing

Review happens after step verification, before `verification-before-completion`, before `hotl-rt finalize`.

Use this over `loop-execution` when you want explicit human checkpoints at every stage rather than auto-approve.

## Reporting

Execution report output must conform to `docs/contracts/execution-report-output.md`. This is the canonical reporting contract from `skills/loop-execution/SKILL.md`. Live step visibility follows the same rules as `skills/loop-execution/SKILL.md` — per-step chat logs on all platforms, deterministic renderer for final summary.
