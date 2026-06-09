---
name: crank
description: "Run crank."
---
# $crank - Autonomous Epic Execution (Codex Native)

> **Quick Ref:** Execute every open issue in an epic via wave-based workers using `spawn_agent`, `wait_agent`, `send_input`, and `close_agent`. Output: closed issues + final validation.

**You must execute this workflow. Do not just describe it.**

## Architecture

```text
Crank (lead agent)
    |
    +-> bd ready (current wave)
    |
    +-> Build a wave task packet
    |
    +-> spawn_agent per issue (worker or explorer role)
    |
    +-> wait_agent for all worker ids
    |
    +-> Validate results + bd update
    |
    +-> Loop until epic DONE
```

## Backend Rules

1. Prefer Codex session agents when `spawn_agent` is available.
2. Use `agent_type=worker` for implementation agents and `agent_type=explorer` for discovery agents when the runtime exposes roles.
3. Use `send_input` only for short steering or retry prompts.
4. Use `close_agent` for stalled or unnecessary agents.
5. Never depend on legacy CSV fan-out or host-task result polling. Use `spawn_agent`, `wait_agent`, `send_input`, and `close_agent` instead.

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), ensure startup context
before the first wave:

```bash
ao codex ensure-start 2>/dev/null || true
```

`ao codex ensure-start` is the single startup guard for Codex skills. It records
startup once per thread and skips duplicate startup automatically. Leave
`ao codex ensure-stop` to closeout skills after the implementation wave ends.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--test-first` | off | SPEC -> TEST -> IMPL wave sequence. Workers classify tests by pyramid level (L0-L3) per the test pyramid standard (`test-pyramid.md` in the standards skill). When `$plan` includes `test_levels` metadata, carry it into `metadata.validation.test_levels`. |

## Global Limits

**MAX_EPIC_WAVES = 50** (hard limit). Typical epics use 5-10 waves.

## Completion Enforcement (Sisyphus Rule)

After each wave, output one of:
- `<promise>DONE</promise>` - epic complete, all issues closed
- `<promise>BLOCKED</promise>` - cannot proceed, with reason
- `<promise>PARTIAL</promise>` - incomplete, with remaining items

Never claim completion without the marker.

## Node Repair Operator

When a task fails during wave execution, classify as **RETRY** (transient — re-add with adjustment, max 2), **DECOMPOSE** (too complex — split into sub-issues, terminal), or **PRUNE** (blocked — escalate immediately). Budget: 2 per task.

**Mutation logging on failure:** DECOMPOSE logs `task_removed` + `task_added` per sub-task. PRUNE logs `task_removed`. RETRY logs nothing (task identity unchanged).

## Execution Steps

Given `$crank [epic-id | .agents/rpi/execution-packet.json | plan-file.md | "description"]`:

### Step 0: Load Knowledge Context

```bash
if command -v ao &>/dev/null; then
    ao lookup --query "<epic-title>" --limit 5 2>/dev/null || true
    ao ratchet status 2>/dev/null || true
fi
```

**Apply retrieved knowledge:** If learnings are returned, check each for applicability to this epic. For applicable learnings, treat as implementation constraints and cite by filename. Record citations with the correct type: `ao metrics cite "<path>" --type applied` when the learning influenced a decision, or `--type retrieved` when loaded but not referenced.

**Section evidence:** When lookup results include `section_heading`, `matched_snippet`, or `match_confidence` fields, prefer the matched section over the whole file — it pinpoints the relevant portion. Higher `match_confidence` (>0.7) means the section is a strong match; lower values (<0.4) are weaker signals. Use the `matched_snippet` as the primary context rather than reading the full file.

### Step 0.5: Detect Tracking Mode

```bash
if bd ready --json >/dev/null 2>&1 && bd list --type epic --status open --json >/dev/null 2>&1; then
    TRACKING_MODE="beads"
else
    TRACKING_MODE="tasklist"
fi
```

### Step 0.6: Initialize Shared Task Notes

Create the shared notes file for cross-wave context persistence. See `references/shared-task-notes.md` for the full pattern.

```bash
mkdir -p .agents/crank
cat > .agents/crank/SHARED_TASK_NOTES.md <<EOF
# Shared Task Notes — Epic ${EPIC_ID:-unknown}

> Cross-wave context for workers. Read before starting. Report discoveries in task output.
> Maintained by the crank orchestrator — workers do NOT write to this file directly.

EOF
```

### Step 0.7: Initialize Plan Mutation Audit Trail

Create the JSONL file that tracks every plan mutation during execution. See `references/plan-mutations.md` for the full schema and mutation budget.

```bash
mkdir -p .agents/rpi
: > .agents/rpi/plan-mutations.jsonl

# Budget counters
MUTATION_TASK_ADDED=0
MUTATION_TASK_ADDED_LIMIT=5
MUTATION_TASK_REORDERED=0
MUTATION_TASK_REORDERED_LIMIT=3
```

**Helper function:**

```bash
log_plan_mutation() {
    local mutation_type="$1" task_id="$2" before="$3" after="$4"
    local ts
    ts=$(date -Iseconds)

    if [[ "$mutation_type" == "task_added" ]]; then
        MUTATION_TASK_ADDED=$((MUTATION_TASK_ADDED + 1))
        if [[ $MUTATION_TASK_ADDED -gt $MUTATION_TASK_ADDED_LIMIT ]]; then
            echo "WARN: task_added budget exceeded ($MUTATION_TASK_ADDED/$MUTATION_TASK_ADDED_LIMIT). Consider re-running $plan."
        fi
    elif [[ "$mutation_type" == "task_reordered" ]]; then
        MUTATION_TASK_REORDERED=$((MUTATION_TASK_REORDERED + 1))
        if [[ $MUTATION_TASK_REORDERED -gt $MUTATION_TASK_REORDERED_LIMIT ]]; then
            echo "WARN: task_reordered budget exceeded ($MUTATION_TASK_REORDERED/$MUTATION_TASK_REORDERED_LIMIT)."
        fi
    fi

    echo "{\"timestamp\":\"$ts\",\"wave\":$wave,\"task_id\":\"$task_id\",\"mutation_type\":\"$mutation_type\",\"before\":$before,\"after\":$after}" \
        >> .agents/rpi/plan-mutations.jsonl
}
```

**Mutation types:** `task_added`, `task_removed`, `task_reordered`, `scope_changed`, `dependency_changed`.

### Step 1: Identify the Execution Target

**Beads mode:**
- If epic ID provided: use it directly
- If no epic ID: `bd list --type epic --status open 2>/dev/null | head -5`

**Execution-packet/file mode:**
- If the input is `.agents/rpi/execution-packet.json`, read `objective`, `epic_id`, `tracker_mode`, `done_criteria`, and `validation_commands`
- If `epic_id` exists inside the execution packet, keep that epic as the execution spine
- If `epic_id` is absent, keep the packet `objective` as the execution spine and continue in file-backed mode instead of inventing an epic ID
- For other plan files, read the plan file and extract tasks

### Step 1.5: Branch Isolation Gate

Before wave-1 commit, refuse to crank on `main`/`master`. Cut `crank/<epic-id>` to prevent parallel-session reset clobbers. See [references/branch-isolation.md](references/branch-isolation.md) for the gate script and override flag.

### Step 2: Load Execution Details

**Beads mode:**

```bash
bd show <epic-id> 2>/dev/null
```

**Execution-packet/file mode:**
- Read the packet or plan file into local state for the current objective
- Preserve the same objective across retries; do not narrow to one slice from `bd ready`

### Step 3: List Ready Work for the Current Wave

**Beads mode:**

```bash
bd ready 2>/dev/null
```

`bd ready` returns all unblocked issues - these can run in parallel.

**Execution-packet/file mode:**
- Read remaining tasks from `.agents/rpi/execution-packet.json` or the plan file
- Execute against the packet objective until the plan-backed work is done, blocked, or the retry budget is exhausted

### Step 3a: Pre-flight Checks

1. Verify there are ready issues. Empty list is an error unless the epic is already complete.
2. If 3+ issues are ready, check `.agents/council/` for pre-mortem evidence.
3. If tracking mode is `beads` and `scripts/bd-audit.sh` exists, run the backlog audit before spawning workers.
4. If bd-audit flags backlog hygiene issues, stop and clean them up before continuing. Use `--skip-audit` only when you intentionally want to bypass that gate.
5. For every string being modified, grep the codebase for stale cross-references.

### Step 3b: Language Standards Injection

Detect project language (`go.mod` -> Go, `pyproject.toml` -> Python, etc.) and read applicable standards from `$standards`. Include a Testing section in worker prompts.

### Step 4: Execute the Wave with Codex Session Agents

Crank follows the FIRE loop for each wave:
- **FIND:** locate the next ready set
- **IGNITE:** spawn workers
- **REAP:** wait, validate, and merge results
- **ESCALATE:** retry or block when needed

#### 4a: Load Shared Task Notes

Read cross-wave context to include in worker prompts:

```bash
SHARED_NOTES=""
if [ -f .agents/crank/SHARED_TASK_NOTES.md ]; then
    SHARED_NOTES=$(cat .agents/crank/SHARED_TASK_NOTES.md)
fi
```

If `SHARED_NOTES` exceeds ~50 lines, summarize older waves (keep last 3 in full detail, preserve `[CRITICAL]` entries).

#### 4b: Build a Wave Task Packet

Create one packet per ready issue. Do not use CSV fan-out.

```bash
mkdir -p .agents/crank
cat > ".agents/crank/wave-${wave}-tasks.json" << EOF
{
  "wave": $wave,
  "epic_id": "$EPIC_ID",
  "tasks": [
    {
      "issue_id": "bd-123",
      "subject": "Short issue summary",
      "description": "Issue details and acceptance criteria",
      "files": ["path/to/file.go"],
      "validation_cmd": "go test ./...",
      "metadata": {
        "issue_type": "feature"
      }
    }
  ]
}
EOF
```

Each task packet must include `metadata.issue_type`.

#### 4c: Pre-spawn File Conflict Check

```text
wave_tasks = [tasks from packet]
all_files = {}
for task in wave_tasks:
    for f in task.files:
        if f in all_files:
            CONFLICT -> serialize into sub-waves
        all_files[f] = task.id
```

Display an ownership table before spawning workers. If conflicts exist, split into sub-waves and keep file ownership disjoint.

#### 4c.1: Parallel-Wave Isolation (wave size ≥ 2)

For waves with 2+ workers, three tiers prevent sibling-worker clobber without re-introducing worktree sprawl. Read [references/parallel-wave-isolation.md](references/parallel-wave-isolation.md) for the full tier definitions, the worker prompt template, the `preflight-swarm.sh` escalation criterion, and the `check-worktree-disposition.sh` cleanup gate.

Tier 1 (always): inject the branch-isolation prompt rule (worker's first git op = `git checkout -b feat/<epic>-<slug> origin/main`; never `git switch`, `stash pop`, `reset --hard`).
Tier 2 (escalate on `preflight-swarm.sh` non-zero): ephemeral per-worker worktree.
Tier 3 (wave-end): `scripts/check-worktree-disposition.sh` flags stragglers.

#### 4d: Spawn Workers

Spawn one agent per issue. Prefer `worker` roles for implementation and `explorer` roles for file discovery when the runtime exposes `agent_type`.

```text
spawn_agent(
  agent_type="worker",
  message="You are worker-<issue-id>.

Assignment: <subject>

<description>

---
Context from prior waves (read before starting):
<SHARED_NOTES content, or 'First wave — no prior context.' if empty>

---

FILE MANIFEST (files you are permitted to modify):
<list of files>

Rules:
1. Stay within your assigned files
2. Run validation: <validation_cmd>
3. Keep your response short
4. Write any durable notes to .agents/crank/results/<issue-id>.md or .agents/crank/results/<issue-id>.json
5. DISCOVERY REPORTING: If you discover codebase quirks, failed approaches,
   convention requirements, or dependency constraints, include a section in your
   output titled '## Discoveries' with one bullet per finding.

Use the repo's current Codex primitives only."
)
```

If a task is missing its file manifest, spawn a short-lived `explorer` agent first:

```text
spawn_agent(
  agent_type="explorer",
  message="You are explorer-<issue-id>.

Task: identify the files that must be created or modified for this issue.
Return a JSON array of paths only."
)
```

#### 4e: Wait for Workers

```text
wait_agent(targets=["agent-id-1", "agent-id-2"])
```

If a worker needs a short correction, use `send_input(target=..., message=...)`.

If a worker stalls or is no longer needed, use `close_agent(target=...)`.

### Step 5: Verify and Sync

**External Gate Enforcement:** After each worker completes, the orchestrator (not the worker) runs the gate command. Workers must not declare their own completion. See `references/external-gate-protocol.md`.

For each completed worker:

1. PASS -> close the issue.
2. FAIL -> log the failure, keep the issue open, and retry only if the issue is still within the retry budget.
3. BLOCKED -> mark blocked with the reason and continue the wave.

Update beads with evidence:

```bash
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null | head -10 | tr '\n' ' ' | sed 's/ $//')
bd close "$issue_id" --reason "commit:${COMMIT_SHA} files:[${CHANGED_FILES}]" 2>/dev/null
bd update "$issue_id" --status blocked --append-notes "Wave $wave FAIL: $reason" 2>/dev/null
```

### Step 5.5: Wave Acceptance Check

After all workers complete:
1. Compute `git diff` for the wave.
2. Run project-level tests appropriate to the wave.
3. If tests fail, identify which worker's changes broke things and requeue only that work.
4. **CI-Policy Parity Gate (conditional).** If the wave diff touches `.github/workflows/*.yml`, run `bash scripts/validate-ci-policy-parity.sh`; on non-zero exit treat the wave verdict as **FAIL** and surface the drift report. Trigger pattern (narrow — workflow YAML only):
   ```bash
   if git diff --name-only "$WAVE_START_SHA" HEAD -- | grep -qE '^\.github/workflows/.*\.ya?ml$'; then
       bash scripts/validate-ci-policy-parity.sh || exit 1
   fi
   ```
   See [references/wave-patterns.md](references/wave-patterns.md) "CI-Policy Parity Gate" for the worked example and the soc-lmww1 / commit `c587b361` motivation.

### Step 5.7: Wave Checkpoint

```bash
FILES_CHANGED_JSON="${FILES_CHANGED_JSON:-$(git diff --name-only "${WAVE_START_SHA:-HEAD~1}..HEAD" | jq -R -s -c 'split("\n")[:-1]')}"
GIT_SHA="$(git rev-parse HEAD)"

cat > ".agents/crank/wave-${wave}-checkpoint.json" << EOF
{
  "schema_version": 1,
  "wave": $wave,
  "epic_id": "$EPIC_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "tasks_completed": ${TASKS_COMPLETED_JSON:-[]},
  "tasks_failed": ${TASKS_FAILED_JSON:-[]},
  "files_changed": $FILES_CHANGED_JSON,
  "git_sha": "$GIT_SHA",
  "acceptance_verdict": "${ACCEPTANCE_VERDICT:-WARN}",
  "commit_strategy": "${COMMIT_STRATEGY:-wave-batch}",
  "mutations_this_wave": $(grep -c "\"wave\":${wave}" .agents/rpi/plan-mutations.jsonl 2>/dev/null || echo 0),
  "total_mutations": $(wc -l < .agents/rpi/plan-mutations.jsonl 2>/dev/null | tr -d ' '),
  "mutation_budget": {
    "task_added": {"used": ${MUTATION_TASK_ADDED:-0}, "limit": 5},
    "task_reordered": {"used": ${MUTATION_TASK_REORDERED:-0}, "limit": 3}
  }
}
EOF

bash skills-codex/crank/scripts/validate-wave-checkpoint.sh ".agents/crank/wave-${wave}-checkpoint.json"
```

Do not copy or consume the checkpoint downstream until validation passes. The validator fails closed when `git_sha` does not resolve in the current repo, `timestamp` is invalid or more than 5 minutes in the future, or required checkpoint fields are missing/malformed.

### Step 5.8: Update Shared Task Notes

Harvest discoveries from completed workers and append to the shared notes file:

```bash
WAVE_DISCOVERIES=""
for result_file in .agents/crank/results/*; do
    if [ -f "$result_file" ]; then
        DISCOVERIES=$(sed -n '/^## Discoveries/,/^## /{ /^## Discoveries/d; /^## /d; p; }' "$result_file" 2>/dev/null)
        if [ -n "$DISCOVERIES" ]; then
            WAVE_DISCOVERIES="${WAVE_DISCOVERIES}${DISCOVERIES}\n"
        fi
    fi
done

if [ -n "$WAVE_DISCOVERIES" ]; then
    cat >> .agents/crank/SHARED_TASK_NOTES.md <<EOF

## Wave ${wave} ($(date -Iseconds))
$(echo -e "$WAVE_DISCOVERIES")
EOF
fi
```

**Capture:** Failed approaches, codebase quirks, convention discoveries, dependency notes.
**Skip:** Full error logs, implementation details, task status.

### Step 5.9: Log Plan Mutations

After processing wave results, log mutations for any plan changes. Call `log_plan_mutation` for each:

- **DECOMPOSE:** `task_removed` for original, `task_added` for each sub-task
- **PRUNE:** `task_removed` with block reason
- **Scope change:** `scope_changed` when file manifest updated after exploration
- **Dependency discovered:** `dependency_changed` when blocked-by list modified
- **Wave reassignment:** `task_reordered` when task moves between waves

```bash
# Example: task decomposed into sub-tasks
log_plan_mutation "task_removed" "$decomposed_id" \
    "{\"subject\":\"$ORIGINAL_SUBJECT\",\"status\":\"decomposed\"}" "null"
log_plan_mutation "task_added" "$sub_id" "null" \
    "{\"subject\":\"$SUB_SUBJECT\",\"reason\":\"Split from $decomposed_id\"}"

# Example: scope change after exploration
log_plan_mutation "scope_changed" "$task_id" \
    "{\"files\":$ORIGINAL_FILES}" \
    "{\"files\":$UPDATED_FILES,\"reason\":\"$REASON\"}"
```

Mutations are append-only to `.agents/rpi/plan-mutations.jsonl`. Read by `$post-mortem` for drift analysis.

### Step 6: Commit Wave Results

**Lead-only commit** - workers write files, lead validates and commits once per wave:

```bash
for f in $WORKER_FILES_CHANGED; do
    git add -- "$f"
done
git commit -m "feat(<scope>): wave $wave - $COMPLETED_COUNT issues completed"
```

### Step 7: Loop or Complete

```bash
wave=$((wave + 1))

if [[ $wave -ge 50 ]]; then
    echo "<promise>BLOCKED</promise>"
    echo "Global wave limit (50) reached."
    exit 1
fi

REMAINING=$(bd ready 2>/dev/null | wc -l)
if [[ $REMAINING -eq 0 ]]; then
    ALL_CLOSED=$(bd children "$EPIC_ID" 2>/dev/null | grep -c "CLOSED" || echo 0)
    ALL_TOTAL=$(bd children "$EPIC_ID" 2>/dev/null | wc -l || echo 0)

    if [[ $ALL_CLOSED -eq $ALL_TOTAL ]]; then
        echo "<promise>DONE</promise>"
    else
        echo "<promise>BLOCKED</promise>"
        echo "No ready issues but $((ALL_TOTAL - ALL_CLOSED)) issues remain unclosed."
    fi
else
    # Continue to next wave - return to Step 3
fi
```

### Step 8: Final Validation

When the epic is DONE:

```bash
$vibe validate the completed epic
```

### Step 8.5: Archive Shared Task Notes

Move the shared notes to an archive after epic completion:

```bash
if [ -f .agents/crank/SHARED_TASK_NOTES.md ]; then
    mkdir -p .agents/crank/archives
    mv .agents/crank/SHARED_TASK_NOTES.md \
       ".agents/crank/archives/SHARED_TASK_NOTES-${EPIC_ID:-unknown}-$(date +%Y%m%d-%H%M%S).md"
fi
```

## Retry Policy

- Max 2 retries per issue across all waves
- On third failure: mark BLOCKED and continue with remaining issues
- Track retries with `bd comments add "$issue_id" "retry $N: $reason"`

## Failure Recovery

| Scenario | Action |
|----------|--------|
| Worker timeout | Mark BLOCKED, log reason, continue wave |
| Test failure | Identify breaking change, retry once |
| All workers fail | `<promise>BLOCKED</promise>` with diagnostics |
| File conflict detected | Split into sub-waves, re-run |

## Reference Documents

- [references/de-sloppify.md](references/de-sloppify.md) - cleanup pass after implementation waves
- [references/parallel-wave-isolation.md](references/parallel-wave-isolation.md) - branch-isolation rule + conditional ephemeral worktrees + cleanup gate for parallel waves
- [references/plan-mutations.md](references/plan-mutations.md) - plan mutation audit trail for drift analysis
- [references/shared-task-notes.md](references/shared-task-notes.md) - cross-wave context persistence
- [references/commit-strategies.md](references/commit-strategies.md) - per-task vs wave-batch commits
- [references/contract-template.md](references/contract-template.md) - contract template for worker specs
- [references/failure-recovery.md](references/failure-recovery.md) - escalation and retry logic
- [references/failure-taxonomy.md](references/failure-taxonomy.md) - failure classification
- [references/fire.md](references/fire.md) - FIRE loop specification
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md) - Ralph Wiggum loop contract
- [references/taskcreate-examples.md](references/taskcreate-examples.md) - task creation examples
- [references/team-coordination.md](references/team-coordination.md) - worker coordination details
- [references/worker-specs.md](references/worker-specs.md) - per-worker model/tool/prompt specs
- [references/external-gate-protocol.md](references/external-gate-protocol.md) - external gate protocol for wave validation
- [references/test-first-mode.md](references/test-first-mode.md) - test-first wave sequence
- [references/troubleshooting.md](references/troubleshooting.md) - common issues and fixes
- [references/uat-integration-wave.md](references/uat-integration-wave.md) - UAT integration wave patterns
- [references/wave-patterns.md](references/wave-patterns.md) - acceptance checks and checkpoints
- [references/gc-pool-dispatch.md](references/gc-pool-dispatch.md) - gc pool worker dispatch
- [references/wave1-spec-consistency-checklist.md](references/wave1-spec-consistency-checklist.md) - Wave 1 spec consistency checklist
- [references/worktree-per-worker.md](references/worktree-per-worker.md) - worktree isolation pattern

<!-- Lifecycle integration wired: 2026-03-28. See skills/crank/SKILL.md for canonical -->
