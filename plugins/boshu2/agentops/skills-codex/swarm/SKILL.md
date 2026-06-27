---
name: swarm
description: "Dispatch parallel agent lanes."
---
# $swarm

Spawn isolated agents to execute tasks in parallel with Codex session agents. Fresh context per agent.

**Integration modes:**
- **Via `$crank`** - crank creates waves from beads and invokes `$swarm` for each wave
- **Standalone** - direct invocation for ad-hoc parallel work

> **Requires a multi-agent runtime.** Prefer runtime-native Codex session agents. If spawning is unavailable, fall back to sequential execution in the current session.

## Architecture

```text
Lead (this session)
  |
  +-> Identify the wave: tasks with no blockers
  +-> Build explicit file manifests
  +-> Pre-spawn conflict check (file ownership)
  +-> Spawn one worker per task
  +-> Wait for completion
  +-> Validate changes and close or retry tasks
  +-> Repeat if more work remains
```

**Runtime preference:**
1. If `spawn_agent` is available, use Codex session agents.
2. If your runtime exposes `agent_type` roles, use `worker` for execution and `explorer` for file discovery.
3. If spawning is unavailable, execute sequentially and keep the same file-manifest contract.

## Execution

Given `$swarm`:

## Local Mode

In local mode, keep the same file-manifest contract and execute workers sequentially when the runtime cannot spawn agents.

### Step 0: Detect Multi-Agent Capability

Check whether the runtime can spawn agents. If not:

```text
WARN: Multi-agent not available. Executing tasks sequentially in this session.
```

Fall back to serial execution within the current session.

### Step 1: Ensure Tasks Exist

Tasks come from one of:
- `br ready` output
- An explicit task list from `$crank`
- A user-provided description that you decompose first

Each task needs:
- `id` - unique identifier
- `subject` - what to do
- `description` - detailed instructions
- `files` - file manifest for worker ownership
- `validation` - how to verify completion
- `metadata.issue_type` - the canonical task type used by the lead when tracking work

### Step 1.5: Populate File Manifests

If any task is missing a file manifest, spawn explorer agents to identify files. Use the explorer role if your runtime exposes roles:

```text
spawn_agent(message="You are explorer-1.

Task: Given this task, identify all files that will need to be created or modified.
Return a JSON array of file paths only.
Task subject: <subject>
Task description: <description>")
```

Inject the discovered file list back into the task manifest before spawning workers.

### Step 1.6: Advisory Bead Clustering

When tasks come from bd and `scripts/bd-cluster.sh` exists, run `scripts/bd-cluster.sh --json 2>/dev/null || true` before Step 2. Summarize any clusters as consolidation hints only; never run `--apply` here, and keep Step 2's file-manifest and dependency gates authoritative.

### Step 2: Pre-Spawn Conflict Check

**Pre-Spawn Friction Gates:** Before spawning workers, execute all 5 friction gates (base sync, file manifest, dependency graph, misalignment breaker, wave cap). See `references/pre-spawn-friction-gates.md`.

```text
wave_tasks = [tasks with status=pending and no blockers]
all_files = {}
for task in wave_tasks:
    for f in task.files:
        if f in all_files:
            CONFLICT: f claimed by both all_files[f] and task.id
        all_files[f] = task.id
```

On conflict:
- Serialize conflicting workers into separate sub-waves
- Do not spawn overlapping file manifests into the same shared-worktree wave

Display an ownership table before spawning:

```text
File Ownership Map (Wave N):
┌─────────────────────────────┬──────────┬──────────┐
│ File                        │ Owner    │ Conflict │
├─────────────────────────────┼──────────┼──────────┤
│ src/auth/middleware.go      │ task-1   │          │
│ src/api/routes.go           │ task-2   │          │
└─────────────────────────────┴──────────┴──────────┘
Conflicts: 0
```

### Step 3: Spawn Workers

Build one worker prompt per task. Each worker gets a single assignment and a single file manifest.

```text
spawn_agent(message="You are worker-<task-id>.

Assignment: <subject>

<description>

FILE MANIFEST (files you are permitted to modify):
<list of files>

Rules:
1. Stay within your assigned files
2. Run validation: <validation_cmd>
3. Write your result to .agents/swarm/results/<task-id>.json
4. Keep any message back to the lead short

Result file format:
On success:
{\"type\":\"completion\",\"issue_id\":\"<task-id>\",\"status\":\"done\",\"detail\":\"<one-line summary>\",\"artifacts\":[\"path/to/file1\"],\"worktreePath\":\"<absolute-worktree-path-or-empty>\"}

If blocked:
{\"type\":\"blocked\",\"issue_id\":\"<task-id>\",\"status\":\"blocked\",\"detail\":\"<reason>\",\"worktreePath\":\"<absolute-worktree-path-or-empty>\"}

Knowledge artifacts are in .agents/. See .agents/AGENTS.md for navigation.")
```

If your runtime supports `agent_type`, mark these as `worker` agents and keep any file-discovery agents as `explorer`.

### Step 4: Wait and Collect Results

```text
wait_agent(targets=["agent-id-1", "agent-id-2"])
```

Collect worker result files from `.agents/swarm/results/`.

If a worker needs a short correction, use:

```text
send_input(target="agent-id-1", message="Validation failed. Fix the test failure and retry.")
```

If a worker stalls, use:

```text
close_agent(target="agent-id-1")
```

### Step 5: Validate Wave

For each worker result:

1. `PASS` - accept changes
2. `FAIL` - log failure, mark for retry, max 2 retries per task
3. `BLOCKED` - escalate to the lead

After collecting results, run project-level tests appropriate to the wave.

If tests fail, identify which worker's changes caused the break and requeue only that work.

### Step 6: Report Results

Output a wave summary with task status, files changed, and any retries.

### Test File Naming Validation

When workers create test files, validate naming:
- Go: `<source>_test.go` or `<source>_extra_test.go`
- Python: `test_<module>.py` or `<module>_test.py`

### Output Schema Size Guard

When 5+ workers share the same output schema, cache it to `.agents/swarm/output-schema.json` and reference it by path instead of inlining it everywhere.

## Serial Fallback

If spawning is unavailable, execute tasks sequentially:

```text
for task in wave_tasks:
    1. Read task details
    2. Implement changes
    3. Run validation
    4. Record result
```

This is slower but functionally identical.

## Related skills

- $using-atm — out-of-session ATM substrate when a swarm needs persistent panes and human attach/steer.

## Reference Documents

- [references/conflict-recovery.md](references/conflict-recovery.md)
- [references/cold-start-contexts.md](references/cold-start-contexts.md)
- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/local-mode.md](references/local-mode.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)
- [references/validation-contract.md](references/validation-contract.md)
- [references/worker-pitfalls.md](references/worker-pitfalls.md)
- [references/pre-spawn-friction-gates.md](references/pre-spawn-friction-gates.md)
- [references/scope-escape-template.md](references/scope-escape-template.md)
- [references/worker-pre-task-checks.md](references/worker-pre-task-checks.md)
- [references/shared-checkout-discipline.md](references/shared-checkout-discipline.md)
- [references/worktree-isolation.md](references/worktree-isolation.md)
