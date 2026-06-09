# Swarm Local Mode: Runtime-Aware Detailed Execution

## Context Budget Rule

> **Workers write results to disk. The orchestrator reads only thin status files.**
>
> When N workers finish, their full output (file reads, tool calls, reasoning) must NOT flood back into the orchestrator context. This is the #1 cause of context explosion in multi-wave epics.

**Result protocol:**
1. Workers write `.agents/swarm/results/<task-id>.json` on completion
4. Task tool return values are acknowledged but NOT parsed for work details

```bash
# Orchestrator creates result directory before spawning
mkdir -p .agents/swarm/results
```

## Step 2a: Pre-Wave Gate Snapshot (Lead Protocol)

Before spawning any wave whose validation ends at a repo-level CI gate, snapshot the pre-existing FAIL set so post-wave triage can mechanically distinguish swarm-introduced failures from stale breakage on `main`.

```bash
# Before spawn
scripts/pre-push-gate.sh --fast 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E "^FAIL  " | sort > /tmp/pre-wave-fails.txt

# After cleanup
scripts/pre-push-gate.sh --fast 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E "^FAIL  " | sort > /tmp/post-wave-fails.txt

# Swarm-introduced failures (only present post-wave)
comm -13 /tmp/pre-wave-fails.txt /tmp/post-wave-fails.txt
```

The output of the final `comm` is the authoritative diff. Failures in `/tmp/pre-wave-fails.txt` that remain in `/tmp/post-wave-fails.txt` are pre-existing and should be filed as a separate follow-up rather than fixed inline, which keeps the wave's scope honest.

Skip this step when `main` is mandated green before spawn (stricter protocol) or when the wave's validation does not run the gate.

Origin: internal learning note `2026-04-15-pre-wave-gate-snapshot` captured during swarm validation.

## Step 2b: Pre-Spawn Worktree Setup (Multi-Epic Waves)

> **Skip this step** for single-epic waves or when `--no-worktrees` is set.
> **Required** for multi-epic dispatch or when `--worktrees` is set.

Evidence: shared-worktree multi-epic dispatch produced build breaks and algorithm duplication (`.agents/evolve/dispatch-comparison.md`).

### Claude-Native Isolation (preferred when available)

If running in Codex runtime with modern agent definitions, prefer declarative isolation first:

1. Confirm teammate profiles with `codex agents`
2. Use teammate definitions that set `isolation: worktree`
3. For long-running workers, set `background: true`

Only fall back to manual `git worktree` management when declarative isolation is unavailable.

### Detection

```bash
# Multi-epic: check if tasks span more than one epic prefix
# If wave tasks have subjects like "[ol-527] ..." and "[ol-531] ...", use worktrees.
# Single-epic: tasks share one prefix (e.g., all ol-527.*) → shared worktree OK.
```

### Create Worktrees

```bash
# For each epic ID in the wave:
git worktree add /tmp/swarm-<epic-id> -b swarm/<epic-id>
```

Track the mapping:
```
epic_worktrees = {
  "<epic-id>": "/tmp/swarm-<epic-id>",
  ...
}
```

Also record worker ownership for deterministic routing and conflict arbitration:
```
owner_worktrees = {
  "worker-<task-id>": "/tmp/swarm-<epic-id>",
  ...
}
```

### Runtime `worktreePath` Contract (Ownership-Aware Isolation)

When using declarative isolation (`isolation: worktree`), the lead must verify each spawned worker reports a `worktreePath` and that it matches `owner_worktrees`.

1. At spawn time, record expected owner -> path mapping (`owner_worktrees`).
2. On worker completion, read runtime Task result and extract `worktreePath`.
3. Validate:
   - `worktreePath` exists on disk
   - `worktreePath` equals the expected path for that worker
   - File ownership still maps to a single worker/worktree for that wave
4. If `worktreePath` is missing or mismatched, treat isolation as failed:
   - abort overlapping-file parallel merge flow
   - requeue conflicting tasks into a serialized fix-up order
   - proceed only after ownership/worktree mapping is unambiguous

Example verification:
```bash
test -n "$worktreePath" && test -d "$worktreePath" && git -C "$worktreePath" rev-parse --is-inside-work-tree
```

### Inject into Worker Prompts

Each worker prompt must include:
```
WORKING DIRECTORY: /tmp/swarm-<epic-id>

All file reads, writes, and edits MUST use absolute paths rooted at /tmp/swarm-<epic-id>.
Do NOT operate on the main repo directly.
Result file: write to <main-repo>/.agents/swarm/results/<task-id>.json (always main repo path).
```

### Merge-Back After Validation

After each worker's task passes validation:
```bash
# From main repo:
git merge --no-ff swarm/<epic-id> -m "chore: merge swarm/<epic-id>"
git worktree remove /tmp/swarm-<epic-id>
git branch -d swarm/<epic-id>
```

Merge order must respect task blockedBy dependencies.

---

## Step 3: Spawn Workers

Use whatever multi-agent primitives your runtime provides to spawn parallel workers. Each worker receives a pre-assigned task in its prompt.

### Model Selection

Workers should use **sonnet** (not opus) to minimize cost. The orchestrator (lead) stays on opus for coordination and validation.

When spawning via the Task tool, pass `model: "sonnet"`. When spawning via native teams, teammates inherit from the session model unless overridden — set `COUNCIL_CLAUDE_MODEL=sonnet` or use `model: "sonnet"` in the Task call. For longer tasks, prefer teammate profiles with `background: true`.

| Role | Model | Rationale |
|------|-------|-----------|
| Lead/orchestrator | opus (session default) | Coordination, validation, state management |
| Workers | sonnet | Focused single-task execution, 3-5x cheaper |
| Explorers | sonnet | Read-only search tasks |

### Spawn Protocol

For each ready task:

1. **Pre-assign** — Mark the task owned by `worker-<task-id>` before spawning (prevents race conditions)
2. **Spawn** — Create a parallel subagent with the worker prompt (see below)
3. **Track** — Map `worker-<task-id>` to agent handle for waits/retries/cleanup

All workers in a wave spawn in parallel. New team/agent-group per wave = fresh context (Ralph Wiggum preserved).

### Worker Prompt Template

Every worker receives this prompt (adapt to your runtime's spawn mechanism):

```
You are worker-<task-id>.

Your Assignment: Task #<id>: <subject>
<description>

FILE MANIFEST (files you are permitted to modify):
<list of files from plan — one per line>

You MUST NOT modify files outside this manifest. If you need to read other files for context, that is fine.
If your task requires modifying a file not in this manifest, write a blocked result instead.

Instructions:
1. Execute your pre-assigned task independently — create/edit files as needed, verify your work
2. Write your result to .agents/swarm/results/<task-id>.json (see format below)
3. Send a SHORT completion signal to the lead (under 100 tokens)
4. If blocked, write blocked result to same path and signal the lead

RESULT FILE FORMAT (MANDATORY — write this BEFORE sending any signal):

On success:
{"type":"completion","issue_id":"<task-id>","status":"done","detail":"<one-line summary max 100 chars>","artifacts":["path/to/file1","path/to/file2"],"worktreePath":"<absolute-worktree-path-or-empty>"}

If blocked:
{"type":"blocked","issue_id":"<task-id>","status":"blocked","detail":"<reason max 200 chars>","worktreePath":"<absolute-worktree-path-or-empty>"}

CONTEXT BUDGET RULE:
Your message to the lead must be under 100 tokens.
Do NOT include file contents, diffs, or detailed explanations in messages.
The result JSON file IS your full report. The lead reads the file, not your message.

CONDITIONAL PREFLIGHT CHECKS (keyed on task + manifest):

1) Flag-collision preflight — Task says "add --<name> flag" AND manifest touches a cobra file:
   Before writing the registration, grep the target file and parent command for the name.
   On collision, pick an alternative and note it in your result.detail.
   Example: grep -nE '"(<name>)"' <target.go> <parent_cmd.go>
   Source: .agents/learnings/2026-04-15-swarm-flag-collision-preflight.md

2) Codex parity audit — Manifest includes any file under `skills-codex/`:
   After edits, run: bash scripts/audit-codex-parity.sh --skill <skill>
   Resolve all CLAUDE_PRIMITIVE_LEAKAGE and residual-mixed-runtime-marker findings
   (substitute runtime-agnostic terms) before reporting done.
   Source: .agents/learnings/2026-04-15-codex-mirror-runtime-string-lint.md

3) Post-edit sync-script runs — Apply drift in your worktree so the lead's cherry-pick
   lands it atomically. Workers still do NOT commit.
   (a) Manifest has `cli/cmd/ao/*.go` AND task adds a cobra flag:
       scripts/generate-cli-reference.sh && git diff --exit-code cli/docs/COMMANDS.md
   (b) Manifest has any `skills-codex/` file:
       bash scripts/regen-codex-hashes.sh && git diff --exit-code skills-codex/
   If the diff is non-empty after the script runs, that IS the sync artifact — leave it
   staged in the worktree and list the touched paths in result.artifacts.
   Source: .agents/learnings/2026-04-15-post-wave-sync-scripts-are-in-scope.md

4) CI-policy parity preflight — Manifest includes any `.github/workflows/*.yml` file:
   The lead's wave-acceptance step runs `bash scripts/validate-ci-policy-parity.sh`
   when workflow YAML changes are detected. Before signaling done:
   - If you added/renamed a job in validate.yml, also update `summary.needs:` AND
     the `### CI Jobs and What They Check` table in `AGENTS.md` (mark `(non-blocking)`
     if the job has `continue-on-error: true`).
   - Sanity-run locally: `bash scripts/validate-ci-policy-parity.sh` should exit 0.
   - If you cannot align all three surfaces (e.g., AGENTS.md is outside your manifest),
     write a blocked result with `SCOPE-ESCAPE: AGENTS.md needed for CI parity`.
   Motivation: commit c587b361 was a manual fix after soc-lmww1 drifted the three
   surfaces. This preflight prevents recurrence at worker time, not just wave time.
   See skills/crank/references/wave-patterns.md "CI-Policy Parity Gate".

Rules:
- Work only on YOUR pre-assigned task
- Do NOT claim other tasks
- Do NOT message other workers
- Do NOT run git add, git commit, or git push — the lead commits
```

> **Scope-Escape Protocol:** When a worker needs to modify files outside its manifest:
>
> 1. Write a blocked result: `{"type":"blocked","issue_id":"<id>","status":"blocked","detail":"SCOPE-ESCAPE: <file> needed because <reason>"}`
> 2. Do NOT modify the out-of-scope file or work around the constraint
> 3. The lead evaluates scope-escape requests between waves and either adds the file to a future wave's manifest or rejects with guidance

> **Orchestrator note — populating the FILE MANIFEST:** When building each worker prompt, replace
> `<list of files from plan — one per line>` with the explicit file paths assigned to that task in
> your plan. Pull these from the task's `metadata.files` field if present, or derive them from the
> task description during planning. Example populated manifest:
>
> ```
> FILE MANIFEST (files you are permitted to modify):
> src/middleware/auth.py
> tests/test_auth.py
> ```
>
> If the plan does not yet enumerate files, add a planning step to identify them before spawning
> workers. An empty or missing manifest is a signal to pause and plan further — not to let workers
> operate unconstrained.

## Race Condition Prevention

to a specific worker BEFORE spawning. This prevents:
- Two workers claiming the same task
- Non-deterministic assignment order

Workers only transition their assigned task: in_progress -> completed.

## Git Commit Policy

**Workers MUST NOT commit.** The team lead is the sole committer.

| Actor | Git Permissions |
|-------|----------------|
| Team lead (mayor) | git add, commit, push |
| Workers | Read-only git. Write files only. |

**Rationale:**
- Workers share a worktree (per native teams semantics research)
- Concurrent git add/commit from multiple workers corrupts the index
- Lead-only commits ensure atomic, reviewable changesets per wave

**Worker instructions:** Include in every worker prompt:
"Do NOT run git add, git commit, or git push. Write your result to .agents/swarm/results/<task-id>.json, then send a short signal (under 100 tokens) via your runtime channel. The team lead reads result files, not messages."

### Wave Commit Cadence

**Best practice: one commit per completed wave** (not one massive commit for the entire swarm run).

| Cadence | When to use | Commit message format |
|---------|-------------|----------------------|
| **Per wave** (default) | Standard swarm execution | `chore(wave-N): close ag-xxxx, ag-yyyy` |
| **Per task** (`--per-task-commits`) | When per-task attribution is required (audits, blame tracking) | `chore(ag-xxxx): <task subject>` |
| **End of swarm** | Never recommended — loses wave attribution and makes rollback harder | - |

**Why per-wave:** Each wave is an atomic unit of parallel work. A single commit per wave provides:
- Clean rollback boundary (revert one wave without touching others)
- Clear attribution of which wave introduced a change
- Issue IDs in commit message for traceability

**Commit message convention:**
```
chore(wave-1): close ag-1234, ag-1235

- ag-1234: Add authentication middleware
- ag-1235: Create user model schema
```

The lead commits after all tasks in a wave pass validation (Step 4a), before spawning the next wave.

## Step 4: Wait for Completion

Wait for all workers to signal completion using your runtime's wait mechanism. Workers write result files to disk and send a minimal signal.

**Result data** — always read from disk, never from agent messages:

Check `.agents/swarm/results/<task-id>.json` for each worker. These are ~200 bytes each. Do NOT parse agent messages or return values for work details — they contain the worker's full conversation (5-20K tokens per worker) and will explode the lead's context.

**CRITICAL**: Do NOT mark complete yet — validation required first.

## Step 4a: Validate Before Accepting (MANDATORY)

> **TRUST ISSUE**: Agent completion claims are NOT trusted. Verify then trust.

**The Validation Contract**: Before marking any task complete, Mayor MUST run validation checks. See `skills/shared/validation-contract.md` for full specification.

**Validation flow:**

```
<task-notification> arrives
        |
        v
    RUN VALIDATION
        |
    +---+---+
    |       |
  PASS    FAIL
    |       |
    v       v
 complete  retry/escalate
```

**For each completed task notification:**

1. **Check task metadata for validation requirements:**
   ```
   ```

2. **Execute validation checks (in order):**

   | Check Type | Command | Pass Condition |
   |------------|---------|----------------|
   | `files_exist` | `ls -la <paths>` | All files exist |
   | `command` | Run specified command | Exit code 0 |
   | `content_check` | `grep <pattern> <file>` | Pattern found |
   | `tests` | `<test_command>` | Tests pass |
   | `lint` | `<lint_command>` | No errors |

3. **On validation PASS:**
   ```
   ```

4. **On validation FAIL:**
   - Increment retry count for task
   - If retries < MAX_RETRIES (default: 3): send a follow-up message to the worker via your runtime's messaging mechanism: "Validation failed: <specific failure>. Fix and retry."
   - If retries >= MAX_RETRIES: mark task as blocked and escalate to user

**Minimal validation (when no metadata):**

If task has no explicit validation requirements, apply default checks:

```bash
# Check that worker wrote the expected files
git status --porcelain  # Should show unstaged changes from worker

# Check for obvious failures in recent output
# (agent should not have ended with errors)
```

**Example task with validation metadata:**

```
  subject="Add authentication middleware",
  description="...",
  metadata={
    "validation": {
      "files_exist": ["src/middleware/auth.py", "tests/test_auth.py"],
      "command": "pytest tests/test_auth.py -v",
      "content_check": {"file": "src/middleware/auth.py", "pattern": "def authenticate"}
    }
  }
)
```

## Step 5: Review & Finalize

When workers complete AND pass validation:
1. Check git status for changes (workers wrote files but did not commit)
2. Review diffs
3. Run any additional tests/validation
4. Team lead commits all changes for the wave (sole committer)

## Step 5a: Post-Merge Naming Cleanup

After merging worker output, scan for scaffolding-era naming conventions introduced by parallel workers (e.g., `TestCov_` prefixes, `cov*_test.go` file names). Rename to follow project conventions. Run `go vet ./...` (or equivalent linter) to catch naming inconsistencies before committing.

## Step 5b: Cleanup

After wave completes:

```bash
# Clean up result files from this wave (prevent stale reads in next wave)
rm -f .agents/swarm/results/*.json
```

Shut down all workers via your runtime's cleanup mechanism. Then clean up the agent group/team.

### Reaper Cleanup Pattern

Cleanup MUST succeed even on partial failures:

1. Request graceful shutdown for each worker
2. Wait up to 30s for acknowledgment
3. If any worker doesn't respond, log warning, proceed anyway
4. Always run cleanup — lingering agents pollute future sessions

### Timeout Configuration

| Timeout | Default | Description |
|---------|---------|-------------|
| Worker timeout | 180s | Max time for worker to complete its task |
| Shutdown grace period | 30s | Time to wait for shutdown acknowledgment |
| Wave timeout | 600s | Max time for entire wave before forced cleanup |

## Step 6: Repeat if Needed

If more tasks remain:
2. Spawn a NEW wave worker set (new sub-agents or new team) for fresh context
3. Execute the next wave
4. Continue until all done

## Partial Completion

**Worker timeout:** 180s (3 minutes) default per worker.

**Timeout behavior:**
1. Log warning: "Worker {name} timed out on task {id}"
2. Mark task as failed with reason "timeout"
3. Add to retry queue for next wave
4. Continue with remaining workers

**Quorum:** Swarm does not require quorum -- each worker is independent.
Each completed task is accepted individually.
