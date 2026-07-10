---
name: crank
description: "Execute implementation waves."
---
# $crank - Autonomous Epic Execution (Codex Native)

> **Quick Ref:** Execute every open issue in an epic via wave-based workers using `spawn_agent`, `wait_agent`, `send_input`, and `close_agent`. Output: closed issues + final validation.

**You must execute this workflow. Do not just describe it.**

Each slice runs the canonical narrow-waist micro-cycle: its acceptance test authored RED before code is the slice contract, and refactor-under-green is its own wave, never optional (see references/wave-patterns.md) — a refactor wave must change no test (test-first ordering alone is not the quality lever; refactor-after-green is).

## Architecture

```text
Crank (lead agent)
    |
    +-> ao beads exec ready (current wave)
    |
    +-> Build a wave task packet
    |
    +-> spawn_agent per issue (worker or explorer role)
    |
    +-> wait_agent for all worker ids
    |
    +-> Validate results + ao beads exec update
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

**Feed the orchestrator's re-plan loop — don't swallow findings into a silent retry.** When run under `$rpi`, surface what a wave proved or broke UP to the orchestrator. A failed or surprising wave (a `PARTIAL`/`BLOCKED` marker) is *re-plan input*, not just a retry target: per the [`$rpi` Agile Re-Plan Loop](../rpi/SKILL.md#agile-re-plan-loop-the-anti-waterfall-rule), the *remaining* waves may be refactored, inserted, dropped, or reordered before the next runs. Re-cranking the same objective forever instead of letting the remaining plan change is the waterfall anti-pattern.

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
if ao beads exec ready --json >/dev/null 2>&1 && ao beads exec list --type epic --status open --json >/dev/null 2>&1; then
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
- If no epic ID: `ao beads exec list --type epic --status open 2>/dev/null | head -5`

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
br show <epic-id> 2>/dev/null
```

**Execution-packet/file mode:**
- Read the packet or plan file into local state for the current objective
- Preserve the same objective across retries; do not narrow to one slice from `ao beads exec ready`

### Step 3: List Ready Work for the Current Wave

**Beads mode:**

```bash
br ready 2>/dev/null
```

`ao beads exec ready` returns all unblocked issues - these can run in parallel.

**Execution-packet/file mode:**
- Read remaining tasks from `.agents/rpi/execution-packet.json` or the plan file
- Execute against the packet objective until the plan-backed work is done, blocked, or the retry budget is exhausted

### Step 3a: Pre-flight Checks

1. Verify there are ready issues. Empty list is an error unless the epic is already complete.
2. If 3+ issues are ready, check `.agents/council/` for pre-mortem evidence.
3. If tracking mode is `beads` and the legacy-named `scripts/bd-audit.sh` exists, run the backlog audit before spawning workers.
4. If the backlog audit flags hygiene issues, stop and clean them up before continuing. Use `--skip-audit` only when you intentionally want to bypass that gate.
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
br close "$issue_id" --reason "commit:${COMMIT_SHA} files:[${CHANGED_FILES}]" 2>/dev/null
br update "$issue_id" --status blocked 2>/dev/null
br comments add "$issue_id" "Wave $wave FAIL: $reason" 2>/dev/null
```

### Step 5.5: Wave Acceptance Check

After all workers complete:
1. Compute `git diff` for the wave.
2. Run project-level tests appropriate to the wave.
3. If tests fail, identify which worker's changes broke things and requeue only that work.
4. **Orchestrator's own diff-read (mandatory anti-green-washing check).** Before counting a slice/wave as accepted, the orchestrator itself reads the actual wave diff and compares it with each closed slice's declared scope and claim. A green `<promise>DONE</promise>` plus passing evidence JSON is a claim, not proof; an out-of-scope or claim-mismatched diff sets the wave verdict to **FAIL** and surfaces the file list. See [references/wave-patterns.md](references/wave-patterns.md) "Wave Acceptance Check" Step 3.5.
5. **CI-Policy Parity Gate (conditional).** If the wave diff touches `.github/workflows/*.yml`, run `bash scripts/validate-ci-policy-parity.sh`; on non-zero exit treat the wave verdict as **FAIL** and surface the drift report. Trigger pattern (narrow — workflow YAML only):
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

### Step 6.5: Land to main (direct-main + pawl)

THIS repo lands by **direct push to main** — PR-per-bead is retired (external-repo variant below). Land each bead from its own worktree:

1. **Gate:** `ao gate check --fast --scope head` — the local cockpit gate (also the pre-push hook; run it manually to fail fast).
2. **Review:** `REVIEWER=agy bash scripts/pawl-review.sh <bead> --scope head --author-family codex` — the cross-family refuter against the commit. Codex-runtime authors need BOTH halves: `--author-family codex` (default is `claude`; omitting it silently permits a same-family codex bind) AND a non-codex `REVIEWER` (the default reviewer IS codex, which the declared family then excludes — without the override the script exits 2). **CONFIRMED (exit 0) writes the commit-bound verdict the pre-push gate requires; no CONFIRMED verdict ⇒ the bead does NOT land** (no verdict = not done). **REFUTED (exit 3) -> AUTO-REDO** the named defects and re-gate; escalate to a human only on a circuit-breaker trip (max-attempts / time / cost / oscillation), door stays closed.
3. **Land:** `bash scripts/pawl-land.sh <bead>` — fetch + rebase onto `origin/main`, restamp the verdict onto the post-rebase feat, single-shot push.
4. **Close on landed-only:** `ao beads exec close` a child bead ONLY after its commit is an ancestor of `origin/main` (`git fetch origin main && git merge-base --is-ancestor <feat-sha> origin/main`), never on a log line or batch `br --json` query. Never close a parent epic before EVERY child is landed (`scripts/check-epic-children-closed.sh <epic>`).

**Close checkpoint — a closed bead is a sensor reading, not a checkbox (age-cysr).** The close is the loop's highest-signal, membrane-verified evidence ([the flywheel](../../docs/architecture/the-flywheel.md)). On EVERY close answer two questions before moving on: (1) what did completing this bead teach? (one line — usually "nothing new", and that's fine); (2) does it CONTRADICT an assumption the remaining plan depends on? If **no** → proceed to the next bead. If **yes** (a falsified plan assumption) → re-plan the remaining slices NOW, not at the wave boundary: invoke `$discovery` as the re-plan engine over the remaining DAG (split / re-order / add / drop beads) and record the trigger in the close reason (`replan: <falsified assumption>`). **Anti-thrash guard:** the trigger is a falsified plan assumption ONLY — most closes teach nothing; never re-plan on mere surprise, difficulty, or a new idea (park those for `$post-mortem`). **Andon bound:** a re-plan that would rework the same remaining DAG a 3rd time escalates to the human instead of re-planning again.

**Multi-lane serialization + by-hand land.** When several lanes land onto a hot `main` at once, or when you land by hand via the `ao pawl review` CLI (which sets `PAWL_UNTRUSTED_REPO=1` and SKIPS auto-bind, so the sealed bind is manual), follow the serialized land-token discipline + the exact `[feat, #trivial-bind]` command sequence in [references/land-protocol.md](references/land-protocol.md) — one land at a time across lanes, `ao provenance emit-verdict` for the sealed bind (never a hand-appended ledger edge), and `git merge-base --is-ancestor` before every `ao beads exec close`.

**External-repo variant (PR flow).** When targeting an external repo where you cannot push `main`, the land half becomes a PR: prepare it with `$pr-prep`, then reconcile with `scripts/reconcile-pr.sh <pr> <bead> [--epic <epic>]` (verifies the CONFIRMED pawl verdict via `scripts/pawl-verdict.sh check`, merges `gh pr merge --squash --admin`, closes on confirmed `MERGED`). External targets only — never for landing AgentOps' own beads.

### Step 7: Loop or Complete

```bash
wave=$((wave + 1))

if [[ $wave -ge 50 ]]; then
    echo "<promise>BLOCKED</promise>"
    echo "Global wave limit (50) reached."
    exit 1
fi

REMAINING=$(ao beads exec ready 2>/dev/null | wc -l)
if [[ $REMAINING -eq 0 ]]; then
    OPEN_TOTAL=$(ao beads exec list --status open 2>/dev/null | wc -l || echo 0)
    IN_PROGRESS_TOTAL=$(ao beads exec list --status in_progress 2>/dev/null | wc -l || echo 0)

    if [[ $((OPEN_TOTAL + IN_PROGRESS_TOTAL)) -eq 0 ]]; then
        echo "<promise>DONE</promise>"
    else
        echo "<promise>BLOCKED</promise>"
        echo "No ready issues but $((OPEN_TOTAL + IN_PROGRESS_TOTAL)) issues remain open or in progress."
    fi
else
    # Continue to next wave - return to Step 3
fi
```

### Step 8: Final Validation

When the epic is DONE:

```bash
$validate validate the completed epic
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
- Track retries with `br comments add "$issue_id" "retry $N: $reason"`

## Failure Recovery

| Scenario | Action |
|----------|--------|
| Worker timeout | Mark BLOCKED, log reason, continue wave |
| Test failure | Identify breaking change, retry once |
| All workers fail | `<promise>BLOCKED</promise>` with diagnostics |
| File conflict detected | Split into sub-waves, re-run |

## Output Specification

**Format:** committed code plus a markdown progress/closeout summary to stdout; per-slice [slice-validation](../../docs/templates/slice-validation.md) roll-ups.
**Files:** reads `.agents/rpi/execution-packet.json`; writes wave/slice results under `.agents/swarm/results/`; closes beads via `ao beads exec close` in the resolved bead ledger.
**Exit signal:** `<promise>DONE</promise>` (all slices accepted) · `<promise>PARTIAL</promise>` (retry the same objective) · `<promise>BLOCKED</promise>` (manual intervention).

## Related skills

- $using-atm — out-of-session ATM substrate for long-running $crank waves over a bead queue.

## Reference Documents

- [references/de-sloppify.md](references/de-sloppify.md) - cleanup pass after implementation waves
- [references/parallel-wave-isolation.md](references/parallel-wave-isolation.md) - branch-isolation rule + conditional ephemeral worktrees + cleanup gate for parallel waves
- [references/plan-mutations.md](references/plan-mutations.md) - plan mutation audit trail for drift analysis
- [references/shared-task-notes.md](references/shared-task-notes.md) - cross-wave context persistence
- [references/commit-strategies.md](references/commit-strategies.md) - per-task vs wave-batch commits
- [references/contract-template.md](references/contract-template.md) - contract template for worker specs
- [references/failure-recovery.md](references/failure-recovery.md) - escalation and retry logic
- [references/land-protocol.md](references/land-protocol.md) - serialized multi-lane land protocol: land-token, the [feat, #trivial-bind] sequence, stale-bind drop, failure playbook
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
- [references/ship-loop-anti-patterns.md](references/ship-loop-anti-patterns.md) - absorbed ship-loop anti-pattern catalog (ag-s43tg)

<!-- Lifecycle integration wired: 2026-03-28. See skills/crank/SKILL.md for canonical -->
