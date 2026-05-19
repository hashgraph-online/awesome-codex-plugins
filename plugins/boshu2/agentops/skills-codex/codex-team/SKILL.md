---
name: codex-team
description: 'Coordinate multiple Codex agents.'
---
# Codex Team

The lead orchestrates, Codex agents execute. Each agent gets one focused task. The team lead prevents file conflicts before spawning — the orchestrator IS the lock manager.

For verified Codex CLI commands and flags, see `../shared/references/codex-cli-verified-commands.md` when this skill falls back to `$swarm`.

## When to Use

- You have 2+ tasks (bug fixes, implementations, refactors)
- Tasks are well-scoped with clear instructions
- You want Codex execution with predictable isolation
- You may be in Claude or Codex runtime (skill auto-selects backend)

**Don't use when:** Tasks need tight shared-state coordination. Use `$swarm` for dependency-heavy wave orchestration.

## Backend Selection (MANDATORY)

Select backend in this order:

1. `spawn_agent` available -> **Codex sub-agents** (preferred; enabled by default in current Codex)
2. Codex CLI available -> **Codex CLI via background shell commands** (`codex exec ...`)
3. None of the above -> fall back to `$swarm`

## Pre-Flight (CLI backend only)

```
# REQUIRED before spawning with Codex CLI backend
if ! command -v codex > /dev/null 2>&1; then
  echo "Codex CLI not found. Install: npm i -g @openai/codex"
  # Fallback: use $swarm
fi

# Model availability test (uses the user's configured Codex default)
if ! codex exec --full-auto -C "$(pwd)" "echo ok" > /dev/null 2>&1; then
  echo "Default Codex model unavailable. Falling back to $swarm."
fi
```

## Canonical Command

```bash
codex exec --full-auto -C "$(pwd)" -o <output-file> "<prompt>"
```

Uses the user's default Codex model. Add `-m "<model>"` before `-C` only when you intentionally want to pin a specific model.

Flag order: `--full-auto` -> `-C` -> `-o` -> prompt (insert `-m` before `-C` only when overriding the model).

**Valid flags:** `--full-auto`, `-m`, `-C`, `-o`, `--json`, `--output-schema`, `--add-dir`, `-s`

**DO NOT USE:** `-q`, `--quiet` (don't exist)

## Cross-Project Tasks

When tasks span multiple repos/directories, use `--add-dir` to grant access:

```bash
codex exec --full-auto -C "$(pwd)" --add-dir /path/to/other/repo -o output.md "prompt"
```

The `--add-dir` flag is repeatable for multiple additional directories.

## Progress Monitoring (optional)

Add `--json` to stream JSONL events to stdout for real-time monitoring:

```bash
codex exec --full-auto --json -C "$(pwd)" -o output.md "prompt" 2>/dev/null
```

Key events:
- `turn.started` / `turn.completed` — track progress
- `turn.completed` includes token `usage` field
- No events for 60s → agent likely stuck

## Sandbox Levels

Use `-s` to control the sandbox:

| Level | Flag | Use When |
|-------|------|----------|
| Read-only | `-s read-only` | Judges, reviewers (no file writes needed) |
| Workspace write | `-s workspace-write` | Default with `--full-auto` |
| Full access | `-s danger-full-access` | Only in externally sandboxed environments |

For code review and analysis tasks, prefer `-s read-only` over `--full-auto`.

## Execution

### Step 1: Define Tasks

Break work into focused tasks. Each task = one Codex agent (unless merged).

For multi-agent work that needs interchangeable workers, file reservations, session mail, repeated passes, or tmux-backed coordination, read [references/fungible-agent-coordination.md](references/fungible-agent-coordination.md) before dispatching.

### Step 2: Analyze File Targets (REQUIRED)

**Before spawning, identify which files each task will edit.** Codex agents are headless — they can't negotiate locks or wait turns. All conflict prevention happens here.

For each task, list the target files. Then apply the right strategy:

| File Overlap | Strategy | Action |
|-------------|----------|--------|
| All tasks touch same file | **Merge** | Combine into 1 agent with all fixes |
| Some tasks share files | **Multi-wave** | Shared-file tasks go sequential across waves |
| No overlap | **Parallel** | Spawn all agents at once |

```
# Decision logic (team lead performs this mentally):

tasks = [
  {name: "fix spec_path",    files: ["cmd/zeus.go"]},
  {name: "remove beads field", files: ["cmd/zeus.go"]},
  {name: "fix dispatch counter", files: ["cmd/zeus.go"]},
]

# All touch zeus.go → MERGE into 1 agent
```

```
tasks = [
  {name: "fix auth bug",     files: ["pkg/auth.go"]},
  {name: "add rate limiting", files: ["pkg/auth.go", "pkg/middleware.go"]},
  {name: "update config",    files: ["internal/config.go"]},
]

# Task 1 and 2 share auth.go → MULTI-WAVE (1+3 parallel, then 2)
# Task 3 is independent → runs in Wave 1 alongside Task 1
```

```
tasks = [
  {name: "fix auth",    files: ["pkg/auth.go"]},
  {name: "fix config",  files: ["internal/config.go"]},
  {name: "fix logging", files: ["pkg/log.go"]},
]

# No overlap → PARALLEL (all 3 at once)
```

### Step 3: Spawn Agents

**Strategy: Parallel (no file overlap)**

Codex sub-agent backend (preferred):

```
spawn_agent(message="Fix the null check in pkg/auth.go:validateToken around line 89...")
spawn_agent(message="Add timeout field to internal/config.go:Config struct...")
spawn_agent(message="Fix log rotation in pkg/log.go:rotateLogFile...")
```

Codex CLI backend:

```
codex exec --full-auto -C "$(pwd)" -o .agents/codex-team/auth-fix.md "Fix the null check in pkg/auth.go:validateToken around line 89..." &
auth_pid=$!
codex exec --full-auto -C "$(pwd)" -o .agents/codex-team/config-fix.md "Add timeout field to internal/config.go:Config struct..." &
config_pid=$!
codex exec --full-auto -C "$(pwd)" -o .agents/codex-team/logging-fix.md "Fix log rotation in pkg/log.go:rotateLogFile..." &
logging_pid=$!
```

**Strategy: Merge (same file)**

Combine all fixes into a single agent prompt:

```
spawn_agent(message="Fix these 3 issues in cmd/zeus.go: (1) rename spec_path to spec_location in QUEST_REQUEST payload (2) remove beads field (3) fix dispatch counter increment location")

# CLI equivalent:
codex exec --full-auto -C "$(pwd)" -o .agents/codex-team/zeus-fixes.md \
  "Fix these 3 issues in cmd/zeus.go: \
   (1) Line 245: rename spec_path to spec_location in QUEST_REQUEST payload \
   (2) Line 250: remove the spurious beads field from the payload \
   (3) Line 196: fix dispatch counter — increment inside the loop, not outside"
```

One agent, one file, no conflicts possible.

**Strategy: Multi-wave (partial overlap)**

```
# Wave 1: non-overlapping tasks (sub-agent backend)
spawn_agent(message='Fix null check in pkg/auth.go:89...')
spawn_agent(message='Add timeout to internal/config.go...')

# Wait for Wave 1 (sub-agent backend)
wait_agent(targets=["<id-1>", "<id-2>"], timeout_ms=120000)

# Wave 1: non-overlapping tasks (CLI backend)
codex exec ... -o .agents/codex-team/auth-fix.md "Fix null check in pkg/auth.go:89..." &
auth_pid=$!
codex exec ... -o .agents/codex-team/config-fix.md "Add timeout to internal/config.go..." &
config_pid=$!

# Wait for Wave 1
Poll the background shell handles until both complete, then read the output files.

# Read Wave 1 results — understand what changed
Read `.agents/codex-team/auth-fix.md`.
git diff pkg/auth.go

# Wave 2: task that shares files with Wave 1 (sub-agent backend)
spawn_agent(message='Add rate limiting to pkg/auth.go and pkg/middleware.go. Note: validateToken now has a null check at line 89. Build on current file state.')

# Wave 2: CLI backend equivalent
codex exec ... -o .agents/codex-team/rate-limit.md \
  "Add rate limiting to pkg/auth.go and pkg/middleware.go. \
   Note: pkg/auth.go was recently modified — the validateToken function now has a null check at line 89. \
   Build on the current state of the file." &
rate_limit_pid=$!

Poll the background shell handle until it completes, then read the output file.
```

The team lead synthesizes Wave 1 results and injects relevant context into Wave 2 prompts. Don't dump raw diffs — describe what changed and why it matters for the next task.

### Step 4: Wait for Completion

```
# Sub-agent backend:
wait_agent(targets=["<id-1>", "<id-2>", "<id-3>"], timeout_ms=120000)

# CLI backend:
Poll each background shell handle until completion, then read the output files.
```

### Step 5: Verify Results

- Read output files from `.agents/codex-team/`
- Check `git diff` for changes made by each agent
- Run tests if applicable
- For multi-wave: verify Wave 2 agents built correctly on Wave 1 changes

## Output Directory

```
mkdir -p .agents/codex-team
```

Output files: `.agents/codex-team/<task-name>.md`

## Prompt Guidelines

Good Codex prompts are **specific and self-contained**:

```
# GOOD: Specific file, line, exact change
"Fix in cmd/zeus.go line 245: rename spec_path to spec_location in the QUEST_REQUEST payload struct"

# BAD: Vague, requires exploration
"Fix the spec path issue somewhere in the codebase"
```

Include in each prompt:
- Exact file path(s)
- Line numbers or function names
- What to change and why
- Any constraints (don't touch other files, preserve API compatibility)

For multi-wave Wave 2+ prompts, also include:
- What changed in prior waves (summarized, not raw diffs)
- Current state of shared files after prior edits

## Limits

- **Max agents:** 6 per wave (resource-reasonable)
- **Timeout:** 2 minutes default per agent. Increase with `timeout` param for larger tasks
- **Max waves:** 3 recommended. If you need more, reconsider task decomposition

## Fallback

If Codex is unavailable, delegate to `$swarm` which auto-selects the best available backend (native teams with messaging/redirect/graceful shutdown, or background tasks as last resort):

```
$swarm 
```

> **Note:** `$codex-team` runs Codex CLI processes as background shell commands — this is fine (separate OS processes). For Claude agent orchestration, use `$swarm` which uses your runtime's native multi-agent primitives.

## Quick Reference

| Item | Value |
|------|-------|
| Model | User's configured Codex default (`-m "<model>"` to pin one) |
| Command | `codex exec --full-auto -C "$(pwd)" -o <file> "prompt"` |
| Output dir | `.agents/codex-team/` |
| Max agents/wave | 6 recommended |
| Timeout | 120s default |
| Strategies | Parallel (no overlap), Merge (same file), Multi-wave (partial overlap) |
| Fallback | `$swarm` (runtime-native) |

---

## Examples

### Parallel Execution (No File Overlap)

**User says:** Fix three bugs in auth.go, config.go, and logging.go using `$codex-team`

**What happens:**
1. Agent analyzes file targets (auth.go, config.go, log.go — no overlap)
2. Agent selects PARALLEL strategy
3. Agent spawns three Codex agents (sub-agents if available, else CLI via Bash)
4. All agents execute simultaneously, write to `.agents/codex-team/*.md`
5. Team lead verifies results with `git diff` and tests
6. Team lead commits all changes together

**Result:** Three bugs fixed in parallel with zero file conflicts.

### Merge Strategy (Same File)

**User says:** Fix three issues in zeus.go: rename field, remove unused field, fix counter

**What happens:**
1. Agent analyzes file targets (all three tasks touch zeus.go)
2. Agent selects MERGE strategy
3. Agent combines all three fixes into a single Codex prompt with line-specific instructions
4. Agent spawns ONE Codex agent with merged prompt
5. Agent completes all three fixes in one pass
6. Team lead verifies and commits

**Result:** One agent, one file, no conflicts possible.

### Multi-Wave (Partial Overlap)

**User says:** Fix auth.go, add rate limiting to auth.go + middleware.go, update config.go

**What happens:**
1. Agent identifies overlap: tasks 1 and 2 both touch auth.go
2. Agent decomposes into waves: W1 = task 1 + task 3 (non-overlapping), W2 = task 2
3. Agent spawns Wave 1 agents in parallel, waits for completion
4. Agent reads Wave 1 results, synthesizes context for Wave 2
5. Agent spawns Wave 2 agent with updated file-state context
6. Team lead validates and commits after Wave 2

**Result:** Sequential wave execution prevents conflicts, context flows forward.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Codex CLI not found | `codex` not installed or not on PATH | Run `npm i -g @openai/codex` or use fallback `$swarm` |
| Default Codex model unavailable | Account/config mismatch or unsupported default | Verify `codex exec --full-auto -C "$(pwd)" "echo ok"` works, or pin a supported model with `-m "<model>"` |
| Agents produce file conflicts | Multiple agents editing same file | Use file-target analysis and apply merge or multi-wave strategy |
| Agent timeout with no output | Task too complex or vague prompt | Break into smaller tasks, add specific file:line instructions |
| Output files empty or missing | `-o` path invalid or permission denied | Check `.agents/codex-team/` directory exists and is writable |

## Reference Documents

- [references/fungible-agent-coordination.md](references/fungible-agent-coordination.md)

## Local Resources

### references/

- [references/fungible-agent-coordination.md](references/fungible-agent-coordination.md)

### scripts/

- `scripts/validate.sh`
