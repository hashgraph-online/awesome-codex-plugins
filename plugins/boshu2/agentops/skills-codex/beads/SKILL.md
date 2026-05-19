---
name: beads
description: 'Track issues with bd/br, triage with bv, and convert plans to beads.'
---

# Beads - Persistent Task Memory for AI Agents

Graph-based issue tracker that survives conversation compaction.

## Overview

**bd** and **br (beads_rust)** replace markdown task lists with a dependency-aware graph stored in git. **bv** adds graph-aware triage using PageRank and betweenness centrality.

**Key Distinction**:
- **bd/br**: Multi-session work, dependencies, survives compaction, git-backed
- **bv**: Graph analysis, priority triage, bottleneck detection, parallel execution planning
- **In-session tracking**: Single-session tasks, status tracking, conversation-scoped (harness-native)

**Decision Rule**: If resuming in 2 weeks would be hard without bd, use bd.

**br vs bd**: br is the Rust rewrite. Commands are the same except: br never auto-commits (git is your job), and `bd sync` becomes `br sync --flush-only`. Use whichever is installed.

**bv safety**: NEVER run bare `bv` — it launches interactive TUI and blocks the terminal. Always use `--robot-*` flags.

## Operating Rules

- Treat live `bd` reads as authoritative. Use `bd show`, `bd ready`, `bd list`, and `bd export` to inspect current tracker state. Do not treat `.beads/issues.jsonl` as the primary decision source when live `bd` data is available.
- Treat `.beads/issues.jsonl` as a git-friendly export artifact. If the repo tracks `.beads/issues.jsonl` and you mutate tracker state, refresh it explicitly with `bd export -o .beads/issues.jsonl`.
- After closing or materially updating a child issue, reconcile the open parent in the same session. Update stale "remaining gap" notes immediately, and close the parent when the child resolved the parent's last real gap.
- Before closing a child issue, include scoped closure proof in the `bd close --reason` text.
  Name the touched files or explicit no-file evidence artifact, validation command(s), and parent
  reconciliation outcome. Do not use generic closure reasons such as "done" or "implemented" for child beads.
- If `bd ready` returns a broad umbrella issue, do not implement directly against vague parent wording. First narrow the remaining gap into an execution-ready child issue, then land the child and reconcile the parent.
- Normalize stale queue items instead of silently skipping them. Rewrite broad or partially absorbed beads to the actual remaining gap.
- Use this post-mutation sequence when tracker state changed:

```bash
bd ...                              # mutate tracker state
bd export -o .beads/issues.jsonl    # if tracked in git
bd vc status
bd dolt commit -m "..."             # if tracker changes are pending
bd dolt push                        # only if a Dolt remote is configured
```

## Prerequisites

- **bd CLI**: Version 0.34.0+ installed and in PATH
- **Git Repository**: Current directory must be a git repo
- **Initialization**: `bd init` run once (humans do this, not agents)

## Examples

### Skill Loading from $vibe

**User says:** `$vibe`

**What happens:**
1. Agent loads beads skill automatically via dependency
2. Agent calls `bd show <id>` to read issue metadata
3. Agent links validation findings to the issue being checked
4. Output references issue ID in validation report

**Result:** Validation report includes issue context, no manual bd lookups needed.

### Skill Loading from $implement

**User says:** `$implement ag-xyz-123`

**What happens:**
1. Agent loads beads skill to understand issue structure
2. Agent calls `bd show ag-xyz-123` to read issue body
3. Agent checks dependencies with bd output
4. Agent closes issue with `bd close ag-xyz-123` after completion

**Result:** Issue lifecycle managed automatically during implementation.

## br (beads_rust) Quick Reference

br is the Rust rewrite of bd. Commands match bd except git handling is explicit.

```bash
# Lifecycle
br create "Title" -p 1 -t task       # Create (priority 0-4)
br update <id> --status in_progress  # Claim work
br close <id> --reason "Done"        # Complete
br ready --json                      # Actionable work (not blocked)
br list --json                       # All issues
br show <id> --json                  # Issue details

# Dependencies
br dep add <child> <parent>          # child depends on parent
br dep cycles                        # MUST be empty
br dep tree <id>                     # Visualize dependencies

# Sync (EXPLICIT — never automatic)
br sync --flush-only                 # DB → JSONL (before git commit)
br sync --import-only                # JSONL → DB (after git pull)
```

**Session ending pattern (br):**
```bash
git pull --rebase
br sync --flush-only
git add .beads/ && git commit -m "Update issues"
git push
```

## bv Graph Triage

NEVER run bare `bv`. Always use `--robot-*` flags.

| Command | Use When |
|---------|----------|
| `bv --robot-triage` | What should I work on? Full recommendations + blockers + health |
| `bv --robot-next` | Just the single top pick |
| `bv --robot-plan` | What can run concurrently? Parallel execution tracks |
| `bv --robot-insights` | Deep analysis: metrics, cycles, density, k-core |
| `bv --robot-priority` | Am I prioritizing wrong? Misalignment detection |
| `bv --robot-alerts` | Stale issues, blocking cascades, priority mismatches |

**Key metrics:** PageRank = everything depends on this (fix first). Betweenness = bottleneck (blocks multiple paths). High both = critical bottleneck, drop everything.

## Plan-to-Beads Workflow

Convert a markdown plan into fully dependency-wired beads:

1. Read the full plan, AGENTS.md, README, linked intent issue, and acceptance criteria.
2. Create beads with `br create` for each issue, including full context in the description.
3. For every feature, bug, or product-facing behavior, include a fenced `gherkin`
   block or link to a filled intent issue. Mechanical chores may omit Gherkin
   only when their acceptance criteria are fully command/file based.
4. Include the `hexagon:` boundary block from
   `docs/architecture/intent-to-loop-hexagon.md` for substantial beads:
   inbound port, bounded context, adapters, context packet, and done state.
5. Wire dependencies with `br dep add` / `bd dep add`. Do not hand-edit JSONL or
   database files.
6. Polish iteratively (usually 6-9 passes) until steady-state. Check for lost
   features, oversimplification, missing tests, unclear boundaries, missing e2e
   coverage, and weak logging.
7. Validate: `br dep cycles` must be empty; run `bv --robot-insights` for graph
   health; use `bv --robot-next` for the first bead. Never run bare `bv`.
8. Sync explicitly before commit: `br sync --flush-only`, then `git add .beads/`
   and commit tracker changes when appropriate.

Beads should be so detailed that a fresh agent can implement without consulting
the original plan. Ready-to-implement beads have clear scope, explicit
dependencies, BDD or mechanical acceptance, unit/e2e test expectations, detailed
logging expectations, a named done state, and no dependency cycles.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| bd/br command not found | CLI not installed or not in PATH | Install bd: `brew install bd` or check PATH |
| "not a git repository" error | bd requires git repo, current dir not initialized | Run `git init` or navigate to git repo root |
| "beads not initialized" error | .beads/ directory missing | Human runs `bd init --prefix <prefix>` once |
| Issue ID format errors | Wrong prefix or malformed ID | Check rigs.json for correct prefix |
| `bv` hangs | TUI launched without robot flag | Always use `--robot-*` flags |
| Cycles detected | Circular dependency | `br dep remove` to break cycle |
| br sync confusion | Missing `--flush-only` or `--import-only` | Always specify direction explicitly |

## Reference Documents

- [references/ANTI_PATTERNS.md](references/ANTI_PATTERNS.md)
- [references/BOUNDARIES.md](references/BOUNDARIES.md)
- [references/BR_REFERENCE.md](references/BR_REFERENCE.md)
- [references/BV_TRIAGE.md](references/BV_TRIAGE.md)
- [references/CLI_REFERENCE.md](references/CLI_REFERENCE.md)
- [references/DEPENDENCIES.md](references/DEPENDENCIES.md)
- [references/INTEGRATION_PATTERNS.md](references/INTEGRATION_PATTERNS.md)
- [references/ISSUE_CREATION.md](references/ISSUE_CREATION.md)
- [references/MIGRATION.md](references/MIGRATION.md)
- [references/MOLECULES.md](references/MOLECULES.md)
- [references/PATTERNS.md](references/PATTERNS.md)
- [references/PLAN_TO_BEADS.md](references/PLAN_TO_BEADS.md)
- [references/RESUMABILITY.md](references/RESUMABILITY.md)
- [references/ROUTING.md](references/ROUTING.md)
- [references/STATIC_DATA.md](references/STATIC_DATA.md)
- [references/tracker-migration-and-triage.md](references/tracker-migration-and-triage.md)
- [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)
- [references/WORKFLOWS.md](references/WORKFLOWS.md)
