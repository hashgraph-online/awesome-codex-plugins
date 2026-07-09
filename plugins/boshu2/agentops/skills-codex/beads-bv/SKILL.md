---
name: beads-bv
description: Graph-aware task triage with bv and br —
---
# beads-bv — Graph-Aware Triage

<!-- TOC: Robot Mode | Commands | Workflow | Scoping | Metrics | br | Troubleshooting | References -->

> **Core Insight:** Your backlog is a directed graph. PageRank finds what everything depends on. Betweenness finds bottlenecks. The math knows your priorities better than your gut.

## CRITICAL: Robot Mode Only

```bash
bv                    # WRONG — launches TUI, blocks terminal
bv --robot-triage     # CORRECT — JSON output for agents
```

**NEVER run bare `bv` in agent contexts.**

---

## Commands

### Core (Start Here)

| Command | Returns | Use When |
|---------|---------|----------|
| `--robot-triage` | THE MEGA-COMMAND: recommendations + blockers + health | What should I work on? |
| `--robot-next` | Single top pick + claim command | Just the one thing |
| `--robot-plan` | Parallel execution tracks with `unblocks` | What can run concurrently? |
| `--robot-insights` | All metrics + cycles + density + k-core + slack | Deep analysis |
| `--robot-priority` | Priority misalignments with confidence | Am I prioritizing wrong? |

### Labels & Health

| Command | Returns | Use When |
|---------|---------|----------|
| `--robot-label-health` | Per-label: health_level, velocity, staleness | Which domain is struggling? |
| `--robot-label-flow` | Cross-label dependencies, bottleneck_labels | Inter-team blockers |
| `--robot-label-attention` | Attention-ranked labels | Where to focus? |
| `--robot-alerts` | Stale issues, blocking cascades, priority mismatches | What's rotting? |
| `--robot-suggest` | Duplicates, missing deps, cycle breaks | Hygiene |

### History & Correlation

| Command | Returns | Use When |
|---------|---------|----------|
| `--robot-history` | Bead-to-commit correlations | Change tracking |
| `--robot-causality <id>` | Timeline, blockers, insights | Why did this take so long? |
| `--robot-related <id>` | File/commit overlap, clusters | What's connected? |
| `--robot-file-beads <path>` | Beads that touched a file | Code ownership |

### Time-Travel & Search

| Command | Returns | Use When |
|---------|---------|----------|
| `--robot-diff --diff-since <ref>` | New/closed/modified since ref | What changed? |
| `--as-of <ref>` | Historical point-in-time | Time-travel |
| `--robot-search` | Search results as JSON | Find beads |
| `--search-mode hybrid` | Text + graph ranking | Smart search |

**Full command reference:** [COMMANDS.md](references/COMMANDS.md)

---

## Workflow

```bash
# 1. What should I work on?
bv --robot-triage | jq '.recommendations[0]'

# 2. Claim it
BEADS_DIR="$(ao beads dir)" br update ag-123 --status in_progress

# 3. Do the work...

# 4. Done
BEADS_DIR="$(ao beads dir)" br close ag-123 --reason "Implemented in abc123"

# 5. Next
bv --robot-triage
```

---

## Scoping & Filtering

```bash
bv --robot-plan --label backend              # Scope to label's subgraph
bv --robot-insights --as-of HEAD~30          # Historical point-in-time
bv --recipe actionable --robot-plan          # Only unblocked items
bv --recipe high-impact --robot-triage       # Top PageRank scores
bv --robot-triage --robot-triage-by-track    # Group by parallel streams
bv --robot-triage --robot-triage-by-label    # Group by domain
bv --robot-alerts --severity=critical        # Filter alerts
```

---

## Key Metrics

| Metric | High Score Means |
|--------|------------------|
| **PageRank** | Everything depends on this — fix first |
| **Betweenness** | Bottleneck — blocks multiple paths |
| **Cycles** | **Broken graph — fix immediately** |
| **K-Core** | Structural strength (core membership) |
| **Articulation** | Cut vertex — removal disconnects graph |

### Decision Matrix

| Pattern | Meaning | Action |
|---------|---------|--------|
| High PageRank + High Betweenness | Critical bottleneck | Drop everything, fix this |
| High PageRank + Low Betweenness | Foundation piece | Important but not blocking |
| Low PageRank + High Betweenness | Unexpected chokepoint | Investigate why |

**Full metrics:** [METRICS.md](references/METRICS.md)

---

## br Essentials

```bash
BEADS_DIR="$(ao beads dir)" br ready --json                  # What's unblocked?
BEADS_DIR="$(ao beads dir)" br create "Title" -d "desc"      # New issue
BEADS_DIR="$(ao beads dir)" br update ag-123 --status in_progress   # Working on this
BEADS_DIR="$(ao beads dir)" br close ag-123 --reason "Done"  # Done
BEADS_DIR="$(ao beads dir)" br dep add ag-123 ag-456         # Add dependency
BEADS_DIR="$(ao beads dir)" br dep remove ag-123 ag-456      # Break cycle
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `bv` hangs | TUI launched | Use `--robot-*` flags |
| Cycles detected | Circular dependency | `br dep remove` to break |
| Phase 2 timeout | Large graph (>500 nodes) | Check `status` field |
| Empty metric maps | Phase 2 still running | Check `status` flags |
| Inconsistent outputs | Different data | Compare `data_hash` |

---

## Validation

```bash
# Tools working?
bv --robot-triage >/dev/null && BEADS_DIR="$(ao beads dir)" br list >/dev/null && echo "OK"

# Graph healthy?
bv --robot-insights | jq '{cycles: .Cycles, density: .density}'
# cycles must be [], density < 0.3 is healthy
```

---

## References

| Need | Read |
|------|------|
| All robot commands + flags | [COMMANDS.md](references/COMMANDS.md) |
| All metrics explained | [METRICS.md](references/METRICS.md) |
| jq recipes, morning triage | [RECIPES.md](references/RECIPES.md) |
