---
name: resume
description: Resume an interrupted AgenTeam run with verify-first strategy.
---

# AgenTeam Resume

Resume an interrupted pipeline run. Detects stale runs, verifies the
last incomplete stage before continuing, and lets the user choose how
to proceed.

## Process

### 1. Detect Resumable Runs

```bash
python3 <runtime>/agenteam_rt.py resume-detect
```

Parse the JSON output:

- **No resumable runs** (`resumable_runs` is empty):
  Tell the user: "No interrupted runs found." Stop.

- **One resumable run**:
  Show summary: run_id, task, interrupted stage, last update time.
  Proceed to step 2.

- **Multiple resumable runs**:
  List all with run_id, task, stage, and age (time since last_update).
  Ask the user which to resume. Proceed with their choice.

### 2. Get Resume Plan

```bash
python3 <runtime>/agenteam_rt.py resume-plan --run-id <run_id>
```

This returns a structured plan with all the information needed to
decide how to resume: pipeline_mode, config drift status, interrupted
stage details (verify, gate, baseline), completed and remaining stages.

### 3. Pipeline Mode Check

Read `pipeline_mode` from the resume plan:

- **`standalone`**: Continue with the verify-first flow below (step 4+).

- **`hotl`**: This run was managed by HOTL's execution engine. Tell the
  user: "This is a HOTL-managed run. Resume with `/hotl:resume <workflow-file>`
  instead." Stop. AgenTeam does not resume HOTL-managed runs — HOTL owns
  the step-level state and verify-first logic for those runs.

- **`dispatch-only`**: Dispatch-only runs have no pipeline to resume.
  Tell the user: "Dispatch-only runs have no pipeline to resume.
  Re-assign tasks with `@<Role> <task>`." Stop.

### 4. Config Drift Check

If `config_hash_match` is `false`:
- Warn: "Config has changed since this run started (agenteam.yaml was
  modified). The run will use the original stage definitions from when
  it was created. Continue anyway? (yes/no)"
- If the user says no: stop.
- If yes: continue. Run-scoped commands use state snapshots, so config
  drift is safe — but the user should know.

### 5. Verify-First

Check `interrupted_stage` from the resume plan:

**If `has_verify` is true AND `verify_safe` is true:**

Run the verify command to check if the interrupted work actually
completed:

```bash
bash <plugin-dir>/scripts/verify-stage.sh run "<verify_command>" --cwd "<cwd>"
```

- **Verify passes**: The interrupted stage's work is actually done.
  Transition the stage forward:
  ```bash
  python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
    --stage <stage> --to passed
  ```
  Then follow normal gating flow:
  - If `has_gate` is true: transition to `gated`, present gate to user.
  - If `has_gate` is false: transition to `completed`, continue to
    next stage.

  Emit resume event:
  ```bash
  python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
    --type stage_resumed --stage <stage> \
    --data '{"verify_result": "pass", "action": "advance"}'
  ```

- **Verify fails**: Present choice (step 6).

**If `has_verify` is false OR `verify_safe` is false:**

Skip verify-first. Go directly to choice (step 6).

### 6. Choice

Show the user a resume summary:
- Stage name, current status, last update time
- If verify was run: show the result

Offer three options:

- **Resume persisted attempt (preferred):** Inspect the interrupted stage's
  latest `attempts[]` record. If it has a `thread_id`, continue through the
  runtime harness:
  ```bash
  python3 <runtime>/agenteam_rt.py run --run-id <run_id>
  ```
  The runner issues `codex exec resume <thread_id> -`, preserves the attempt
  chain, and continues the stored retry budget. Do not launch a second agent
  while the recorded PID is live.

- **Re-dispatch:** Use only when no resumable `thread_id` exists and prior
  side effects have been verified. A fresh redispatch requires explicit approval.
  ```bash
  python3 <runtime>/agenteam_rt.py transition --run-id <run_id> \
    --stage <stage> --to dispatched
  python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
    --type stage_resumed --stage <stage> \
    --data '{"verify_result": "fail", "action": "redispatch"}'
  ```
  Then launch subagents and continue the pipeline from this stage.

- **Preserve and replay:** Query the stage baseline without changing the
  checkout:
  ```bash
  python3 <runtime>/agenteam_rt.py stage-baseline --run-id <run_id> \
    --stage <stage> --action rollback
  ```
  If `allowed` is true, save the current diff to
  `.agenteam/runs/<run_id>/<stage>/resume-recovery.patch`. Offer to create a
  new clean branch/worktree from the baseline and replay there. Never discard
  or rewrite the current dirty checkout automatically.
  If `allowed` is false: tell user rollback is not available in this
  isolation mode.

- **Stop**: End the run.
  ```bash
  python3 <runtime>/agenteam_rt.py event append --run-id <run_id> \
    --type run_finished --data '{"status": "stopped"}'
  ```

### 7. Continue Pipeline

After resuming the interrupted stage (via verify-pass advance or
re-dispatch), continue through the remaining stages using the same
standalone pipeline flow from `skills/run/SKILL.md` step 6.

The remaining stages are listed in the resume plan's `remaining_stages`
array. Process each one in order through the standard dispatch → verify
→ gate → handoff flow.

During continuation, report `thread_id`, last heartbeat, heartbeat age, wall
and idle budget remaining, attempt/retry counts, and stop reason. Runtime state
is the source of truth; chat messages are not checkpoints.

## Headless Policy

When `CI=true` or no TTY detected:

- Skip run selection (if multiple, use the most recent stale run)
- Skip config drift confirmation (proceed with warning to stderr)
- Verify-first always runs (if safe)
- If verify passes → continue automatically
- If verify fails → emit `run_finished` with `status: failed` and
  `reason: "resume-verify-failed-headless"`. Do not prompt.
- `stopped` is user-chosen; `failed` is system-determined

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin: `<plugin-install-path>/runtime/agenteam_rt.py`

Resolve scripts:
1. If running from the plugin directory: `./scripts/`
2. If installed as a Codex plugin: `<plugin-install-path>/scripts/`

## Error Handling

- If `resume-detect` fails: show error, suggest checking `.agenteam/state/`
- If `resume-plan` fails (run not found): show error with run_id
- If verify command fails to execute (not just fails the check): show
  error and fall back to choice
- If transition fails (invalid state): show error with current status
  and valid transitions
