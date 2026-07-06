---
name: loop-execution
description: Use when executing an existing HOTL workflow file — reads steps, loops until success criteria met, auto-approves low-risk gates, pauses at high-risk gates.
---

# HOTL Loop Execution

## Overview

Execute an existing HOTL workflow file autonomously. Canonical workflows live at `docs/plans/YYYY-MM-DD-<slug>-workflow.md`, with legacy root `hotl-workflow-<slug>.md` still accepted during migration. Loop on steps with success criteria. Auto-approve low-risk gates. Always pause for high-risk gates.

`governed-execution` is the preferred new router for host-native or fallback runs. This skill remains the canonical autonomous state machine and a supported explicit compatibility profile. When invoked through the router, use the selected driver for lifecycle calls and require a sufficient evidence receipt before completion.

**Announce:** "Starting HOTL loop execution. Looking for workflow file..."

## Workflow File Resolution

Resolve which workflow file to execute:

1. If the user specified a filename → use that file
2. Else, glob for canonical workflows in `docs/plans/*-workflow.md`:
   - **One match** → use it automatically
   - **Multiple matches** → if one is clearly the newest revision for the same semantic slug, prefer it; otherwise list them and ask the user to pick
3. If no canonical matches, glob for legacy `hotl-workflow*.md` in project root:
   - **One match** → use it automatically
   - **Multiple matches** → list them and ask the user to pick
4. **No matches** → see "What to Do If No Workflow Found" below

### Interrupted Run Detection

After resolving the workflow file, locate interrupted runs **before** Branch/Worktree Preflight. Use `scripts/hotl-locate-run.sh --workflow <workflow-file>` when available. This helper scans the current checkout, linked git worktrees, and HOTL's default `.hotl-worktrees/<repo>/` directory, so it can find state created inside an isolated execution worktree even when the new session starts from the authoring checkout.

If the helper is unavailable, manually scan these locations for `.hotl/state/*.json` and match `workflow_path` or `source_workflow_path` against the resolved workflow:
1. Current checkout
2. `git worktree list --porcelain` roots for the repo
3. `$(dirname <repo-root>)/.hotl-worktrees/$(basename <repo-root>)/*`

- **One interrupted run found** → ask: "Found an interrupted run (step N/M). Resume from step N, or start fresh?"
- **Multiple interrupted runs found** → list all with run_id, step progress, branch, age. Ask which to resume or start fresh. **Never silently choose.**
- **No interrupted runs** → proceed normally (new run)

If the user chooses resume, do not run Branch/Worktree Preflight again. Load the matched sidecar, change into its recorded `execution_root`, and follow `skills/resuming/SKILL.md` with the original `run_id`.

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

## HOTL Execution State Machine

This is the canonical HOTL execution state machine. Other execution modes (e.g., subagent-execution) reference this spec and define only their differences.

```
1. Resolve workflow file (see above)
2. Parse frontmatter: intent, risk_level, auto_approve, branch, worktree
3. Run Branch/Worktree Preflight (see above)
4. Capture preflight metadata and change into `execution_root`
5. Initialize run via runtime:
   - Run: `hotl-rt init <workflow-file> --executor-mode loop --repo-root <repo-root> --execution-root <execution-root> --source-workflow-path <source-workflow-path> --source-branch <source-branch|null> --source-head <source-head|null> --worktree-path <worktree-path|null> --branch <branch>`
   - This parses the workflow, creates .hotl/state/<run-id>.json with all steps, and initializes .hotl/reports/<run-id>.md
   - Capture the run_id from stdout
   - For every later `hotl-rt step`, `hotl-rt gate`, `hotl-rt finalize`, `scripts/show-codex-current-step.sh`, and `scripts/finalize-codex-summary.sh` call, pass `--run-id <run-id>` or set `HOTL_RUN_ID=<run-id>`
   - Never let the runtime silently choose "the newest run" when multiple runs exist
   - Only after init succeeds should chat output or native plan/progress UI show anything

6. For each step in order:

   a. Start step via runtime:
      - Run: `hotl-rt step N start --run-id <run-id>`
      - This persists step start (status, timestamp, attempts) to state and report
      - Only after the runtime call succeeds should chat show "→ Step N"

   b. Announce: "→ Step N: [name]"

   c. Execute the action (agent implements the work)

   d. Verify via runtime:
      - Run: `hotl-rt step N verify --run-id <run-id>`
      - The runtime runs the verify command, captures stdout/stderr, and atomically transitions the step to done or failed
      - If the verify type is unsupported, the runtime blocks the step with a clear reason
      - For type: browser — `hotl-rt` downgrades to a paused human-review request when browser tooling is unavailable inside the runtime. If the controller has platform browser tooling, perform the browser check before approving or rejecting that pause.
      - For type: human-review — the runtime returns a `human review required: ...` block reason and sets the run status to `paused`; ALWAYS pause for human (never auto-approve)
      - For type: artifact — runtime checks path exists and evaluates assert; for `matches-glob`, `path` must be the directory and `value` must be a filename glob only, so `src/*` is invalid and should be authored as `path: src`

   e. If verify fails (runtime returns non-zero):

      e0. If the runtime output says `blocked: human review required: ...`
         → PAUSE immediately. Do not start later steps or finalize the run.
         → Show the review prompt to the human and ask: "Continue? (yes/no/show-details)"
         → If the human says yes/approve/continue:
             Run: `hotl-rt gate N approved --mode human --run-id <run-id>`
             Then continue to the next step
         → If the human says no/reject:
             Run: `hotl-rt gate N rejected --mode human --run-id <run-id>`
             STOP and surface the report path
         → If the human asks for details:
             Show the relevant test/report context, then wait again
         → Never treat the chat reply alone as persisted approval; the approval is only real after the `hotl-rt gate ...` call succeeds

      f. If loop: false
         → STOP, report to human
         → Run: `hotl-rt step N block --reason "verify failed" --run-id <run-id>` if not already marked failed by verify
         → Show last verify output. Wait for human guidance.

      g. If loop: until [condition]
         → if iterations < max_iterations:
             Run: `hotl-rt step N retry --run-id <run-id>` then `hotl-rt step N start --run-id <run-id>`
             log "↻ Retrying ([n]/[max])...", retry the action
         → if iterations = max_iterations: STOP
             Report: "Step N reached max iterations ([max]). [condition] not met."
             Show last verify output. Wait for human guidance.

      h. On step completion (verify passed):
      - The runtime has already persisted the done status
      - Update the workflow checkbox to [x]
      - Only after the runtime confirms success should chat show "✓ Step N"

   i. If gate: human
      → if auto_approve: true AND risk_level != high:
          Run: `hotl-rt gate N approved --mode auto --run-id <run-id>`
          log "⚡ Auto-approved: Step N gate (risk: [risk_level])"
          continue
      → else:
          PAUSE. Show summary of what was done in this step.
          Ask: "Gate reached at Step N. Continue? (yes/no/show-details)"
          Wait for human response.
          Run: `hotl-rt gate N approved --mode human --run-id <run-id>` or `hotl-rt gate N rejected --mode human --run-id <run-id>`

   j. If gate: auto
      → Run: `hotl-rt gate N approved --mode auto --run-id <run-id>`
      → always continue, log "⚡ Auto-approved: Step N gate"

6. All steps complete:
   → Run review checkpoint (see Review Checkpoints below)
   → Invoke hotl:verification-before-completion skill
   → For Codex final summaries, run: `scripts/finalize-codex-summary.sh <run-id>` (or set `HOTL_RUN_ID`)
   → For Claude Code/Cline, run: `hotl-rt finalize --json --run-id <run-id>`, write the payload to a temp file, then render it with: `scripts/render-execution-summary.sh --platform <claude|cline> <summary-json-file>`
   → Do not freehand the final summary when the renderer is available
   → The rendered summary must be shown as visible chat output in the final response; do not paraphrase it away
   → After rendering the final summary, if the run used git isolation or the user asks what to do with the execution checkout, invoke `hotl:finishing-a-development-branch` with the same `run_id`
   → Never silently merge, publish, keep, or discard the execution branch/worktree
```

## Execution State Persistence

All state persistence is handled by the `hotl-rt` shared runtime (`runtime/hotl-rt`). Agents do not manage state files directly.

The runtime owns:
- `.hotl/state/<run-id>.json` — authoritative machine state (created by `hotl-rt init`, updated by `hotl-rt step/gate/finalize`)
- `.hotl/reports/<run-id>.md` — durable Markdown report (initialized at init, updated incrementally, finalized at finalize)

The sidecar also records the execution location for the run: `repo_root`, `execution_root`, `workflow_path`, `source_workflow_path`, `worktree_path`, and `executor_mode`.

Run ID format: `<slug>-<YYYYMMDDTHHMMSSZ>` (e.g., `add-auth-20260320T212315Z`).

Workflow checkboxes (`- [x]`) are a human-visible mirror updated by the agent on step completion. The sidecar is the source of truth.

Operational rule: `hotl-rt` calls happen before the corresponding chat log or Codex native plan/progress update. Native progress UI is never a substitute for the runtime-managed artifacts.

Concurrency rule: after `hotl-rt init` returns a run id, pin every later runtime/helper call to that run id. Do not rely on "latest file in .hotl/state" when more than one run exists.

See `skills/resuming/SKILL.md` for the full sidecar schema, stale run detection, and verify-first resume flow.

### Path Resolution

To find `hotl-rt` and HOTL scripts (`document-lint.sh`, `hotl-locate-run.sh`, `render-execution-summary.sh`, etc.), resolve in this order:

1. **Session context (Claude Code):** the session-start hook injects the plugin base path — use it to construct full paths like `bash <plugin-path>/runtime/hotl-rt init <workflow-file>`
2. **Codex native-skills install:** resolve from `~/.codex/hotl/runtime/hotl-rt` and `~/.codex/hotl/scripts/`
3. **Codex plugin install:** resolve from `~/.codex/plugins/hotl-source/runtime/hotl-rt` and `~/.codex/plugins/hotl-source/scripts/`
4. **Codex plugin cache fallback:** resolve from `~/.codex/plugins/cache/codex-plugins/hotl/*/runtime/hotl-rt` and `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/`
5. **Cline:** resolve from `~/Documents/Cline/Scripts/hotl-rt` and `~/Documents/Cline/Scripts/`
6. **Working in the hotl-plugin repo itself:** use `./runtime/hotl-rt` and `./scripts/`

The same resolution applies to all HOTL scripts under `scripts/`.

**Dependency: `jq`.** `hotl-rt` requires `jq` for JSON state management. If `hotl-rt` fails with a `jq not found` error:
1. Show the user the platform-specific install command from the error output
2. Fall back to inline execution — run steps with per-step chat logs and manual checkbox updates, but without state persistence (`.hotl/state/`), durable reports (`.hotl/reports/`), or deterministic summary rendering
3. Note in the final output that the run was not state-managed due to missing `jq`

## Execution Report

Execution report output must conform to `docs/contracts/execution-report-output.md`. The contract defines the durable report format (metadata, summary table, event log), execution status vocabulary, final summary semantics, platform rendering tables, and the deterministic renderer reference.

The `hotl-rt` runtime writes the durable report to `.hotl/reports/<run-id>.md` incrementally. The report survives app rendering quirks and provides a reliable post-run artifact for debugging, trust, and resume.

Reference `report_path` in user-facing pause, blocked, resume, and completion responses so the durable report is always discoverable.

When a `verify: human-review` step pauses, the response must include the `report_path` and make it clear that the run is paused pending approval, not failed.

If the workflow sets `report_detail: full`, successful verify output must also be included in the durable report, not only failures.

## Review Checkpoints

Record `git rev-parse HEAD` as the review base at run start and after each review.

### At Final Completion

After all steps have passed verification, before `hotl-rt finalize`:
1. A final review is required unless the most recent review already covers all current changes and no code changed afterward
2. Invoke `requesting-code-review` with review type: final
   - Review base: branch point or last review base, whichever is more recent
3. When findings return, invoke `receiving-code-review`
   - Follow Verify → Evaluate → Respond → Implement
4. Resolve all BLOCK findings before finalizing
5. If fixes after the last review changed scope, constraints, or risk_level, request a scoped follow-up review before completing

### At Intermediate Gates (Conditional)

At intermediate `gate: human` steps, request review only when:
- risk_level is high
- The gate covers cross-module or feature-scale changes
- Multiple steps have completed since the last review

When triggered, scope the review to steps completed since the last review checkpoint, not the entire run. Use review type: checkpoint.

Do not request review at every gate by default.

### Review Ordering

Review happens:
1. After step verification is complete
2. Before `verification-before-completion`
3. Before `hotl-rt finalize` / any "done" claim

## Safety Rules

- `risk_level: high` in frontmatter **always** forces human approval at `gate: human` steps, even if `auto_approve: true`
- Never skip a `gate: human` on steps with security-sensitive keywords (auth, encrypt, secret, key, password, token, permission, role, billing)
- On STOP: always show the failing verify output so human can diagnose

## Live Execution Behavior

Report format, status vocabulary, final summary semantics, and platform rendering tables for final artifacts are defined in `docs/contracts/execution-report-output.md`. This section covers runtime behavior that is executor-owned: live step visibility, progress updates, and verbose mode.

### Final Summary (mandatory)

Every execution run MUST end with a visible final summary in chat. A prose recap alone is not compliant.

For Codex final summaries:
- MUST use `scripts/finalize-codex-summary.sh` when available
- MUST include the rendered compact list in the final response as visible chat text
- MUST keep the rendered step lines intact; do not paraphrase, omit, or replace them with narrative
- MAY add a short prose recap after the rendered summary, but not instead of it

If the Codex helper is unavailable, fall back to `hotl-rt finalize --json` plus `scripts/render-execution-summary.sh --platform codex ...`, then emit that renderer output directly.

### Platform Rendering

Final artifacts must follow `docs/contracts/execution-report-output.md`:

| Platform | Final summary rendering |
|---|---|
| Codex | Compact list in chat. Wide markdown tables are not acceptable here. |
| Claude Code | Markdown table in chat. |
| Cline | Markdown table in chat. |

Status vocabulary for final summaries includes `✓ Done`, `⚡ Auto-approved`, `✓ Approved`, `✗ Failed`, and `✗ Blocked`.

Iterations means attempt count only. For tables, the `Iterations` column is a number only or `-` for gates. Never put test counts in `Iterations`; test counts belong in `Status`.

In the Codex compact list, keep the step name first and inline status detail after ` - `. Include the status word on every line and always include iteration count details such as `Done (1 attempt)`, `Done (3 attempts)`, or `Approved (1 attempt)`.

### Platform Live Step Visibility

| Platform | Live step visibility |
|---|---|
| Codex | Native progress card (primary). Per-step chat logs as fallback. |
| Claude Code | Per-step one-line chat logs |
| Cline | Per-step one-line chat logs |

### Live Step Visibility (mandatory)

Every execution run MUST provide live step visibility — the user must see which step is currently executing and which are done. This is not optional on any platform.

### Codex Native Progress (mandatory with fallback)

When running in the Codex app, the executor MUST use the native plan/progress UI as the primary live step visibility surface:

- MUST initialize the native progress card immediately after run setup (step 4 of the state machine)
- MUST update it on every step transition — exactly one step `in_progress` at a time
- MUST keep the native card high-level: major workflow steps only, not retries or verify substeps
- If the native progress tool is unavailable or errors, MUST immediately switch to per-step chat logs for the remainder of the run. Do not silently drop visibility.
- Native progress never replaces the final chat summary, durable report, or sidecar state
- If Codex needs an explicit readout of the active workflow step, use `scripts/show-codex-current-step.sh` to print the current step number, name, status, and attempts from the active run without mutating state

On platforms without native progress (Claude Code, Cline), the executor MUST use per-step chat logs for live visibility.

### Per-Step Log (default, always shown)

After each step, log one line:
```
✓ Step 1: Write failing tests
✓ Step 2: Implement auth logic (3 attempts)
⚡ Step 3: Security review gate (auto-approved)
✓ Step 4: Update docs
```

### Verbose Progress View (opt-in)

When verbose mode is enabled, print a compact step list at each step transition (before starting a step, after a step completes/fails/auto-approves):

```
  ✓ Step 1: Write failing tests
  ✓ Step 2: Implement feature
  → Step 3: Run full test suite (attempt 1/3)
  · Step 4: Update docs
  · Step 5: Human review
```

**Symbols:**
- `✓` — completed
- `→` — current step (include attempt info if looping)
- `·` — pending
- `⚡` — auto-approved gate
- `✗` — blocked/failed

Include short result details only when useful (test counts on completed steps, attempt progress on current step, failure reason on blocked steps).

### Verbose Mode Precedence

1. **Executor invocation override wins** — user says "run with verbose progress"
2. **Workflow frontmatter** — `progress: verbose`
3. **Default** — non-verbose (per-step log only, no full list)

## What to Do If No Workflow Found

If no canonical `docs/plans/*-workflow.md` or legacy `hotl-workflow*.md` is found:
"No workflow file found. Would you like to:
1. Create one from a design doc (`$hotl:writing-plans` in Codex, `/hotl:write-plan` in Claude Code)
2. Use a workflow template from the plugin (`workflows/feature.md`, `workflows/bugfix.md`, `workflows/refactor.md`)"
