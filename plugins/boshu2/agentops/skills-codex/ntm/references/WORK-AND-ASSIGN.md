# `ntm work` & `ntm assign` — Comprehensive Command Reference

Covers intelligent work distribution (`ntm work`) and task-to-agent assignment (`ntm assign`) families.
Sources are cited as `file:line` shorthand; all paths are under `/dp/ntm/internal/cli/`.

## Contents

- [Overview](#overview) — design philosophy and interaction model
- [ntm work subcommands](#ntm-work-subcommands) — observation & planning via bv/beads graph
  - [triage](#triage) — prioritized recommendations with caching
  - [alerts](#alerts) — drift + proactive issue detection
  - [search](#search) — semantic search for issues
  - [impact](#impact) — blast radius analysis
  - [next](#next) — top recommendation only
  - [history](#history) — bead-to-commit correlation
  - [forecast](#forecast) — ETA prediction with dependency analysis
  - [graph](#graph) — dependency graph export
  - [label-health](#label-health) — health metrics per label
  - [label-flow](#label-flow) — cross-label bottleneck analysis
  - [burndown](#burndown) — sprint progress tracking
  - [queue-dry](#queue-dry) — prove no-ready-work states before ideating
- [ntm assign subcommands](#ntm-assign-subcommands) — pushing work onto panes
  - [Core modes](#core-invocation) — auto vs. interactive, direct pane, clear, watch
  - [Strategies](#strategies) — comparison table and selection guide
  - [Agent-type filters](#agent-type-filters)
  - [Prompt templates](#prompt-templates)
  - [Clear operations](#clear-operations)
  - [Watch mode (continuous auto-assignment)](#watch-mode-continuous-auto-assignment)
  - [Reassignment (move between agents)](#reassignment-move-bead-between-agents)
  - [Retry failed assignments](#retry-failed-assignments)
- [Interaction patterns](#interaction-patterns) — `--from-bv`, file reservations, robot wrappers
- [Flag index](#flag-index)

---

## Overview

### `ntm work` — Observation & Planning

The `ntm work` family provides **read-only** analysis of work using the bv (beads-view) dependency graph:

- **triage**: sorted recommendations with prioritization scores
- **alerts**: real-time drift and proactive issue detection
- **search**: semantic search over issue corpus
- **impact**: which issues are affected by file modifications
- **history**: bead event tracking and commit correlation
- **forecast**: ETA prediction considering dependencies
- **label-health**: velocity, staleness, blockage metrics per label
- **graph**: export dependency graph for external tools
- **queue-dry**: determine whether "no work" is real, stale coordination state, or a prompt for guarded ideation

All output is derived from cached bv analysis (cache TTL: 30s, `work.go:204-246`).

### `ntm assign` — Action (Pushing Work)

The `ntm assign` family **executes assignments**, pushing beads to agent panes:

- **normal mode** (`ntm assign session`): interactive recommendations → confirmation → execution
- **auto mode** (`--auto`): no confirmation, just execute
- **direct pane mode** (`--pane=N`): bypass strategy, assign to specific pane
- **watch mode** (`--watch`): continuous polling for completions, auto-reassign unblocked beads
- **clear mode** (`--clear`): remove assignments and release file reservations
- **reassign mode** (`--reassign`): move bead from one agent to another
- **retry mode** (`--retry`): re-queue failed assignments

---

## `ntm work` Subcommands

### `triage`

Get complete triage analysis with caching. Source: `work.go:54-99`.

```bash
ntm work triage                           # Default: full triage with top 10 recommendations
ntm work triage --by-label                # Group results by label
ntm work triage --by-track                # Group results by execution track
ntm work triage --quick                   # Show only quick wins
ntm work triage --health                  # Include project health metrics
ntm work triage --limit 20                # Override default limit (10)
ntm work triage --format=json             # Full JSON output
ntm work triage --format=markdown         # Compact markdown (50% token savings)
ntm work triage --format=markdown --compact # Ultra-compact markdown without scores
ntm work triage --json                    # Alias for --format=json
```

**Flags:**
- `--by-label` (bool): Group recommendations by label
- `--by-track` (bool): Group recommendations by execution track
- `--limit/-n` (int, default: 10): Maximum recommendations to display
- `--quick` (bool): Show only quick wins (filtered set)
- `--health` (bool): Include project health distribution and graph metrics
- `--format` (string): Output format — `json`, `markdown`, or `auto`
- `--compact` (bool): With `--format=markdown`, omit scores and use shorter format

**Output formats:**
- **Terminal (default)**: human-friendly with score bars, reasoning, and actions
- **JSON**: full structured data including all metadata
- **Markdown**: token-efficient, suitable for context-limited LLMs (Claude in limited context)

Results are cached for 30 seconds (`work.go:204-233`). Grouped views (by-label, by-track) call bv directly and are not cached yet.

### `alerts`

Display drift alerts (reachability failures) and proactive issue alerts (stale, blocked). Source: `work.go:101-131`.

```bash
ntm work alerts                           # All alerts
ntm work alerts --critical-only           # Only critical severity
ntm work alerts --type=stale_issue        # Filter by type
ntm work alerts --label=backend           # Filter by label
ntm work alerts --json                    # Output as JSON
```

**Flags:**
- `--critical-only` (bool): Show only critical alerts
- `--type` (string): Filter by alert type (e.g., `stale_issue`, `drift`)
- `--label` (string): Filter by label

**Alert types returned** (`work.go:376-388`):
- `type`: alert classification (drift, stale_issue, etc.)
- `severity`: critical, warning, or info
- `issue_id`: optional associated bead ID
- `labels`: optional issue tags

### `search`

Semantic search for issues using bv's vector-based indexing. Source: `work.go:133-161`.

```bash
ntm work search "JWT authentication"
ntm work search "rate limiting" --limit=20
ntm work search "database migration" --mode=hybrid
ntm work search "API endpoints" --json
```

**Flags:**
- `--limit/-n` (int, default: 10): Maximum results to return
- `--mode` (string, default: `text`): Search mode — `text` or `hybrid`

**Result format** (`work.go:491-504`):
- `id`: bead ID
- `title`: issue title
- `score`: relevance score (0.0-1.0)
- `status`: open, closed, in_progress, etc.
- `priority`: P0-P4 if available
- `snippet`: brief excerpt from issue description

### `impact`

Analyze which beads are impacted by modifying specific files. Helps assess change blast radius. Source: `work.go:163-182`.

```bash
ntm work impact src/auth/*.go
ntm work impact internal/api/users.go internal/api/auth.go
ntm work impact "**/*_test.go"
ntm work impact src/auth/*.go --json
```

**Arguments:**
- `<paths...>`: File paths or glob patterns

**Result format** (`work.go:579-592`):
- `file`: matched file path
- `impacted_ids`: list of bead IDs affected by changes
- `total_impact`: count of impacted beads
- `direct_impact`: count of directly referenced beads
- `total_beads`: aggregate across all paths
- `unique_beads`: deduplicated count

### `next`

Display the single highest-priority recommendation. Equivalent to `bv -robot-next` with cached data. Source: `work.go:184-201`.

```bash
ntm work next
ntm work next --json
```

Returns one `TriageRecommendation` with ID, title, score, reasons, and suggested action.

### `history`

Show bead-to-commit correlations and event milestones. Source: `work.go:747-764`.

```bash
ntm work history
ntm work history --json
```

**Result format** (`work.go:882-918`):
- `stats`: total beads, commits, correlated count
- `histories`: per-bead event timeline and commit references
- `commit_index`: hash → metadata mapping

### `forecast`

Predict completion times (ETA) with dependency-aware scheduling. Source: `work.go:766-790`.

```bash
ntm work forecast                         # All open issues
ntm work forecast ntm-123                 # Specific issue
ntm work forecast --json
```

**Result format** (`work.go:920-934`):
- `id`: bead ID
- `title`: issue title
- `estimated_eta`: predicted completion timestamp
- `confidence_level`: prediction confidence (0.0-1.0)
- `dependency_count`: how many dependencies exist
- `critical_path`: boolean, true if on longest path
- `blocking_factors`: reasons for delays

### `graph`

Export dependency graph for visualization. Source: `work.go:792-816`.

```bash
ntm work graph                            # Default: JSON format
ntm work graph --format=json
ntm work graph --format=dot               # Graphviz format
ntm work graph --format=mermaid           # Mermaid diagram syntax
```

**Formats:**
- `json`: Full graph structure with nodes and edges
- `dot`: Graphviz digraph format (pipe to `dot` for image generation)
- `mermaid`: Markdown-embedded diagram syntax (Mermaid syntax)

### `label-health`

Health metrics per label: velocity, staleness, blocked count. Source: `work.go:818-836`.

```bash
ntm work label-health
ntm work label-health --json
```

**Metrics** (`work.go:952-958`):
- `label`: label name
- `health_level`: healthy, warning, or critical
- `velocity_score`: completion speed metric (0.0-1.0)
- `staleness`: age of oldest open issue (0.0-1.0, higher = staler)
- `blocked_count`: number of blocked beads in this label

### `label-flow`

Cross-label dependency flows and bottleneck identification. Source: `work.go:838-856`.

```bash
ntm work label-flow
ntm work label-flow --json
```

**Result format** (`work.go:962-974`):
- `flow_matrix`: map[from-label]map[to-label]count
- `dependencies`: list of `{from, to, count, weight}` edges (sorted by count desc)
- `bottleneck_labels`: labels with high incoming dependencies

### `burndown`

Sprint burndown with scope changes and at-risk items. Source: `work.go:858-878`.

```bash
ntm work burndown sprint-1
ntm work burndown current
ntm work burndown sprint-2 --json
```

**Arguments:**
- `<sprint>`: Sprint identifier (name or slug)

**Result format** (`work.go:977-1006`):
- `progress`: total_points, completed_points, percent_complete, days_remaining
- `scope_changes`: `[{timestamp, action, issue_id, points}]` (added/removed/modified)
- `at_risk`: `[{id, title, risk, reasons}]` (behind_schedule, blocked, scope_creep)

### `queue-dry`

Use when `ao beads exec ready --json` and `bv --robot-triage` appear empty or when a swarm is
about to stop for lack of work. Treat it as a **guarded transition**, not an
idea generator to run by habit.

```bash
# 1. Prove ready work is actually empty using the native sources.
ao beads exec ready --json
bv --robot-triage | jq '.quick_ref'

# 2. Diagnose the dry queue.
ntm work queue-dry --format=json | jq '{queue_dry, evidence, recommendations, warnings}'
ntm work queue-dry --format=markdown

# 3. Preview future work only after the dry queue is confirmed.
ntm work queue-dry --ideate --format=json | jq '.ideation.guard'
ntm work queue-dry --ideate --format=markdown

# 4. Mutate Beads only after reviewing the preview and guard.
ntm work queue-dry --ideate --create-beads --yes --plan-version="$(git rev-parse --short HEAD)"
br dep cycles --json
bv --robot-triage | jq '.quick_ref'
br sync --flush-only
```

Operational rules:

- If `queue_dry=false`, stop the queue-dry flow and claim the ready work instead.
- If `warnings` mention degraded Agent Mail, CASS, CM, or Beads health, keep the
  flow non-mutating unless the human explicitly accepts the stale-source risk.
- `--force` is for previewing despite ready work or degraded state; it is not a
  shortcut to create beads.
- Creation remains Beads-owned. Never edit `.beads/*.jsonl` directly.
- A dry queue can be a real finish signal. Do not manufacture work merely to keep
  panes busy.

---

## `ntm assign` Subcommands

`ntm assign` is a single command with multiple modes selected by flags. Source: `assign.go:88-232`.

### Core Invocation

```bash
ntm assign [session]                      # Show interactive recommendations
ntm assign myproject --auto                # Execute without confirmation
ntm assign myproject --strategy=quality    # Change strategy
ntm assign myproject --beads=bd-1,bd-2     # Assign specific beads only
ntm assign myproject --limit=5             # Limit to 5 assignments
ntm assign myproject --cc-only             # Only assign to Claude agents
ntm assign myproject --agent=codex         # Only assign to Codex agents
ntm assign myproject --dry-run             # Preview mode (synonym for no --auto)
ntm assign myproject --json                # Output as JSON
```

**Positional args:**
- `[session]` (optional): Named tmux session. Auto-detected if not specified.

### Core Flags

| Flag | Type | Default | Source | Purpose |
|------|------|---------|--------|---------|
| `--auto` | bool | false | `assign.go:182` | Execute assignments without confirmation |
| `--strategy` | string | `balanced` | `assign.go:183` | Assignment strategy (see table below) |
| `--beads` | string | `""` | `assign.go:184` | Comma-separated bead IDs to assign (restricts pool) |
| `--limit/-n` | int | 0 (unlimited) | `assign.go:185` | Maximum assignments to execute |
| `--dry-run` | bool | false | `assign.go:201` | Preview mode (alias for no `--auto`) |
| `--verbose/-v` | bool | false | `assign.go:198` | Show detailed scoring and decision logs |
| `--quiet/-q` | bool | false | `assign.go:199` | Suppress non-essential output |
| `--timeout` | duration | 30s | `assign.go:200` | Timeout for external calls (bv, br, Agent Mail) |
| `--reserve-files` | bool | true | `assign.go:202` | Reserve file paths via Agent Mail before assignment |
| `--json` | bool | false | (root) | Output as JSON (set globally) |

### Strategies

Source: `assign.go:88-108`, `/dp/ntm/internal/config/config.go:1215-1225`.

| Strategy | When to Use | Optimizes For | Notes |
|----------|-------------|---------------|-------|
| **balanced** (default) | General purpose, mixed workloads | Evenly distributed workload | Spreads work to avoid over-loading any one agent |
| **speed** | Quick iteration, time-critical | Fast task completion | Assigns to any idle agent immediately, minimal overhead |
| **quality** | Code review, careful work, refactoring | Agent-task match quality | Matches tasks to agents with best capability scores for the task type |
| **dependency** | Feature work with blockers, unblocking chains | Unblocking downstream work | Prioritizes beads that unblock other work, unblocking velocity |
| **round-robin** | Deterministic, reproducible distribution | Even allocation without scoring | Simple rotation through agents, no capability weighting |

**Parsed via** `ParseStrategy` (`assign.go` and `/dp/ntm/internal/assign/matcher.go:28-42`).
Valid strings: `balanced`, `speed`, `quality`, `dependency`, `round-robin`, `roundrobin`, `rr`.

### Agent-Type Filters

Source: `assign.go:187-191`.

| Flag | Agent Type | Example | Notes |
|------|------------|---------|-------|
| `--agent=<type>` | string | `--agent=claude` | Filter by type: `claude`, `codex`, `gemini` |
| `--cc-only` | bool | Alias for `--agent=claude` | Only assign to Claude agents |
| `--cod-only` | bool | Alias for `--agent=codex` | Only assign to Codex agents |
| `--gmi-only` | bool | Alias for `--agent=gemini` | Only assign to Gemini agents |

Multiple flags can be combined: `--cc --cod` assigns to Claude or Codex agents.

### Prompt Templates

Source: `assign.go:193-195`.

| Flag | Type | Purpose | Source |
|------|------|---------|--------|
| `--template` | string (default: `impl`) | Built-in template | `assign.go:194` |
| `--template-file` | string | Custom template file path | `assign.go:195` |

**Built-in templates:**
- `impl`: "Work on bead {BEAD_ID}: {TITLE}. Check dependencies first."
- `review`: "Review and verify bead {BEAD_ID}: {TITLE}. Run tests if applicable."
- `custom`: Load from `--template-file` path

Template variables:
- `{BEAD_ID}`: the bead identifier
- `{TITLE}`: the bead title
- `{PRIORITY}`: the priority level
- `{STATUS}`: the current status

### Direct Pane Assignment

Bypass strategy matching, assign a bead directly to a specific pane. Source: `assign.go:204-208`.

```bash
ntm assign myproject --pane=3 --beads=bd-123                    # Assign to pane 3
ntm assign myproject --pane=3 --beads=bd-123 --prompt="Focus on API changes"
ntm assign myproject --pane=0 --beads=bd-123 --force            # Force even if busy
ntm assign myproject --pane=2 --beads=bd-123 --ignore-deps      # Skip dep checks
```

**Flags:**
- `--pane` (int, default: -1): Target pane index (-1 = disabled)
- `--force` (bool): Force assignment even if pane is busy
- `--ignore-deps` (bool): Skip dependency validation checks
- `--prompt` (string): Custom prompt for this assignment (overrides template)

When `--pane` is specified, `--beads` is required and only those beads are assigned to that pane.

### Clear Operations

Remove assignments and release file reservations. Source: `assign.go:210-213`.

```bash
ntm assign myproject --clear bd-xyz                          # Clear single bead
ntm assign myproject --clear bd-xyz,bd-abc,bd-def            # Clear multiple (CSV)
ntm assign myproject --clear-pane=3                          # Clear all for pane 3 (agent crashed)
ntm assign myproject --clear-failed                          # Clear all failed assignments
ntm assign myproject --clear bd-xyz --force                  # Force clear completed assignment
```

**Flags:**
- `--clear` (string): Comma-separated bead IDs to clear
- `--clear-pane` (int, default: -1): Clear all assignments for a pane (-1 = disabled)
- `--clear-failed` (bool): Clear all assignments marked as failed
- `--force` (bool): With `--clear`, also remove completed assignments (default: only remove queued)

Clear operations are synchronous and release Agent Mail file reservations immediately.

### Watch Mode (Continuous Auto-Assignment)

Monitor for task completions and automatically assign newly unblocked beads to idle agents.
Source: `assign.go:215-220`, `work.go:411-528`.

```bash
ntm assign myproject --watch                               # Watch with defaults
ntm assign myproject --watch --strategy=dependency          # Use dependency strategy
ntm assign myproject --watch --limit=2                      # Max 2 assignments per cycle
ntm assign myproject --watch --stop-when-done               # Exit when all work done
ntm assign myproject --watch --delay=5s                     # 5s delay between assignments
ntm assign myproject --watch --watch-interval=10s           # Poll every 10 seconds
ntm assign myproject --watch --auto-reassign=false          # Disable auto-reassign
```

**Flags:**
- `--watch` (bool): Enable watch mode
- `--watch-interval` (duration, default: 30s): How often to check for completions
- `--auto-reassign` (bool, default: true): Auto-assign newly unblocked beads
- `--stop-when-done` (bool): Exit when no more beads are ready for assignment
- `--delay` (duration, default: 0): Delay between consecutive assignments

**Watch mode flow** (`assign.go:414-528`):
1. Initial assignment pass (same as normal mode, but with `--quiet`)
2. Enter polling loop, checking for completion every `--watch-interval`
3. When beads are completed, release blockages and check for newly unblocked work
4. Auto-reassign unblocked beads to idle agents (if `--auto-reassign`)
5. Optional: Press F12 for attention-aware dashboard overlay (if in tmux)
6. Graceful shutdown on Ctrl+C or SIGTERM

Watch mode maintains a summary of total assignments and session activity.

### Reassignment (Move Bead Between Agents)

Move an already-assigned bead from one agent to another. Useful when an agent is stuck or to redistribute.
Source: `assign.go:222-225`.

```bash
ntm assign myproject --reassign bd-xyz --to-pane=4              # Move to specific pane
ntm assign myproject --reassign bd-xyz --to-type=codex          # Move to idle codex agent
ntm assign myproject --reassign bd-xyz --to-pane=4 --prompt="Continue work"
ntm assign myproject --reassign bd-xyz --to-pane=4 --force      # Force even if busy
```

**Flags:**
- `--reassign` (string): Bead ID to move (required)
- `--to-pane` (int, default: -1): Target pane (-1 = not set)
- `--to-type` (string): Target agent type; auto-selects idle agent of this type
- `--prompt` (string): Custom prompt for reassignment
- `--force` (bool): Force assignment even if target pane is busy

Either `--to-pane` or `--to-type` must be specified. If both are set, `--to-pane` takes precedence.

### Retry Failed Assignments

Re-queue failed assignments to idle agents. Source: `assign.go:227-229`.

```bash
ntm assign myproject --retry bd-xyz                              # Retry one bead
ntm assign myproject --retry-failed                              # Retry all failed
ntm assign myproject --retry bd-xyz --to-pane=4                  # Retry to specific pane
ntm assign myproject --retry-failed --to-type=claude             # Retry all to Claude agents
```

**Flags:**
- `--retry` (string): Bead ID to retry
- `--retry-failed` (bool): Retry all beads marked as failed
- `--to-pane` (int, default: -1): Target pane for retry
- `--to-type` (string): Target agent type for retry

Failed beads are re-queued with fresh assignments and retransmitted to agents.

---

## Interaction Patterns

### Bv Integration (`--from-bv` Pattern)

Both `ntm work` and `ntm assign` use bv (Beads View) as the authority for work prioritization.

- `ntm work triage` calls `bv.GetTriage(dir)` with 30-second caching (`work.go:236-239`).
- `ntm assign` uses BV for dependency-aware matching (`assign.go:322-324`).
- Fallback to `bd-ready` data when BV is unavailable.

BV is optional but strongly recommended for dependency-aware assignment.

### Queue-Dry Gate

Before broad reassignment, check whether the backlog is genuinely ready:

```bash
ao beads exec ready --json
bv --robot-triage | jq '.quick_ref'
ntm work queue-dry --format=json | jq '{queue_dry, evidence, recommendations}'
```

If ready work exists, assign it. If no work exists and queue-dry says it is safe
to stand down, stop the swarm instead of dispatching generic "keep going" prompts.
Only use `--ideate --create-beads --yes` after the preview has a clear guard and
the operator wants new Beads work created.

### Pressure-Aware Assignment

Large swarms can fail by overfeeding healthy-looking agents: build hosts saturate,
provider quotas drain, and coordination queues turn stale. Before bulk assigning:

```bash
ntm --robot-snapshot --robot-verbosity=terse
ntm --robot-agent-health=<session>
ntm --robot-rch-status
ntm --robot-quota-status
```

Decision rule:

- If resource pressure or quota pressure is high, lower `--limit`, use a narrower
  domain filter, or wait for active builds to finish.
- Prefer `--strategy=dependency` when blockers dominate, `--strategy=quality`
  when agent capability matters, and `--strategy=balanced` when many panes are idle.
- Re-check reservations before pushing assignments into a hot directory.

### File Reservations (Agent Mail)

When `--reserve-files=true` (default), `ntm assign` reserves code paths via Agent Mail before pushing work.

- Prevents concurrent edits to the same files.
- Releases reservations when assignment completes or is cleared.
- Configurable per assignment command via `--reserve-files` flag (`assign.go:202`).

### Robot Mode Wrappers

The robot mode layer (`--robot-*` flags in `root.go`) can invoke `ntm work` and `ntm assign` actions
as part of larger automation workflows. See **ROBOT-MODE.md** for `--robot-send`, `--robot-assign`,
`--robot-route`, and `--robot-bulk-assign` details.

---

## Flag Index

### Global Flags (Inherited by `ntm work` and `ntm assign`)

| Flag | Type | Source | Purpose |
|------|------|--------|---------|
| `--json` | bool | `root.go` | Output as JSON (all subcommands) |
| `--no-color` | bool | `root.go` | Disable ANSI colors |
| `--redact` | string | `root.go` | Redaction mode override |

### `ntm work` Flags (by Subcommand)

**triage** (`work.go:55-98`):
- `--by-label`, `--by-track`, `--limit`/`-n`, `--quick`, `--health`, `--format`, `--compact`

**alerts** (`work.go:102-130`):
- `--critical-only`, `--type`, `--label`

**search** (`work.go:134-160`):
- `--limit`/`-n`, `--mode`

**impact** (`work.go:164-181`):
- (positional arguments only; no flags)

**next** (`work.go:185-200`):
- (no flags)

**history** (`work.go:748-763`):
- (no flags)

**forecast** (`work.go:767-789`):
- (optional positional: issue-id)

**graph** (`work.go:793-815`):
- `--format` (json, dot, mermaid)

**label-health** (`work.go:819-835`):
- (no flags)

**label-flow** (`work.go:839-855`):
- (no flags)

**burndown** (`work.go:859-877`):
- (required positional: sprint name)

**queue-dry**:
- `--format` (`text`, `json`, `markdown`)
- `--ideate` (render a non-mutating roadmap when the queue is dry)
- `--create-beads` + `--yes` (mutate Beads from the reviewed plan)
- `--plan-version` (audit token for the reviewed plan)
- `--stale-hours`, `--max-stale`, `--commits`, `--sync-lag-minutes` (tune evidence collection)
- `--include-next-best` (include additional candidates in the roadmap)
- `--force` (preview despite ready work/degraded state; do not use casually)

### `ntm assign` Flags

See [Flag Index](#flag-index) above and in this document.
All flags are registered in `assign.go:182-229`.

---

## Examples

### Work Observation Workflow

```bash
# 1. Triage: what's the backlog?
ntm work triage --by-label --health

# 2. Search: find related issues
ntm work search "JWT validation" --limit 5

# 3. Impact: understand change blast radius
ntm work impact src/auth/*.go

# 4. Next: top recommendation
ntm work next

# 5. Forecast: when will issues be resolved?
ntm work forecast

# 6. Label health: which areas need attention?
ntm work label-health
```

### Assignment Workflow (Interactive)

```bash
# 1. Preview recommendations
ntm assign myproject --strategy=dependency

# 2. Confirm and execute
# ... (prompt appears)

# 3. Watch mode for continuous assignment
ntm assign myproject --watch --strategy=dependency --stop-when-done
```

### Assignment Workflow (Automated)

```bash
# 1. Get recommendations in JSON
ntm assign myproject --json > assignments.json

# 2. Execute with auto confirmation
ntm assign myproject --auto --strategy=quality --limit 3

# 3. Direct pane assignment (bypass matching)
ntm assign myproject --pane=2 --beads=bd-123 --force

# 4. Clear failed assignments
ntm assign myproject --clear-failed

# 5. Reassign stuck bead
ntm assign myproject --reassign bd-456 --to-type=claude
```

---

## Caveats & Undocumented Behaviors

### Not Yet Found in Source

- Strategy-specific documentation beyond brief descriptions in the long form.
- Detailed capability matrix weighting for quality strategy.
- Exact scoring formula for balanced strategy (likely weighted combination).

### Known Limitations

- `ntm work` grouped views (by-label, by-track) are not cached yet; each call invokes bv.
- `--from-bv` pattern is internal to the assign/work layer; no explicit CLI flag.
- Robot mode wrappers (`--robot-assign`, `--robot-route`) are documented separately in ROBOT-MODE.md.

---
