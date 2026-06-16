---
name: beads
description: "Run beads."
---

# Beads - Persistent Task Memory for AI Agents

Graph-based issue tracker that survives conversation compaction.

## Overview

**br (beads_rust)** replaces markdown task lists with a dependency-aware graph stored in git. **bv** adds graph-aware triage using PageRank and betweenness centrality. `bd`/Dolt is legacy unless a repository explicitly opts into it.

**Key Distinction**:
- **br**: Multi-session work, dependencies, survives compaction, git-backed
- **bv**: Graph analysis, priority triage, bottleneck detection, parallel execution planning
- **In-session tracking**: Single-session tasks, status tracking, conversation-scoped (harness-native)

**Decision Rule**: If resuming in 2 weeks would be hard without persistent issues, use br.

**br vs legacy bd**: br is the current default. It never auto-commits; sync explicitly with `br sync --flush-only`, then commit the exported JSONL in the tracker repo or configured issue directory.

**bv safety**: NEVER run bare `bv` — it launches interactive TUI and blocks the terminal. Always use `--robot-*` flags.

## Operating Rules

- Treat live `br` reads as authoritative. Use `br show`, `br ready`, and `br list` to inspect current tracker state. Do not treat JSONL exports as the primary decision source when live `br` data is available.
- Treat the configured issues JSONL as a git-friendly export artifact. If you mutate tracker state, refresh it explicitly with `br sync --flush-only`.
- After closing or materially updating a child issue, reconcile the open parent in the same session. Update stale "remaining gap" notes immediately, and close the parent when the child resolved the parent's last real gap.
- Before closing a child issue, include scoped closure proof in the `br close --reason` text.
  Name the touched files or explicit no-file evidence artifact, validation command(s), and parent
  reconciliation outcome. Do not use generic closure reasons such as "done" or "implemented" for child beads.
- If `br ready` returns a broad umbrella issue, do not implement directly against vague parent wording. First narrow the remaining gap into an execution-ready child issue, then land the child and reconcile the parent.
- Normalize stale queue items instead of silently skipping them. Rewrite broad or partially absorbed beads to the actual remaining gap.
- Use this post-mutation sequence when tracker state changed:

```bash
br ...                              # mutate tracker state
br sync --flush-only                # export DB -> JSONL
git add <issues-jsonl-or-dir>
git commit -m "Update issues"       # if tracker changes are pending
git push                            # tracker remote, when configured
```

## Prerequisites

- **br CLI**: Installed and in PATH
- **Git Repository**: Current directory must be a git repo
- **Initialization**: `br init` run once (humans do this, not agents)

## Examples

### Skill Loading from $validate

**User says:** `$validate`

**What happens:**
1. Agent loads beads skill automatically via dependency
2. Agent calls `br show <id>` to read issue metadata
3. Agent links validation findings to the issue being checked
4. Output references issue ID in validation report

**Result:** Validation report includes issue context, no manual br lookups needed.

### Skill Loading from $implement

**User says:** `$implement ag-xyz-123`

**What happens:**
1. Agent loads beads skill to understand issue structure
2. Agent calls `br show ag-xyz-123` to read issue body
3. Agent checks dependencies with br output
4. Agent closes issue with `br close ag-xyz-123` after completion

**Result:** Issue lifecycle managed automatically during implementation.

## br (beads_rust) Quick Reference

br is the current tracker CLI; the binary self-describes (`br --help`). Full command surface: [references/BR_REFERENCE.md](references/BR_REFERENCE.md). Doctrine: sync is EXPLICIT, never automatic — `br sync --flush-only` (DB → JSONL, before git commit) / `br sync --import-only` (JSONL → DB, after git pull); session ends with pull-rebase → flush → commit the tracker JSONL/directory → push.

## bv Graph Triage

NEVER run bare `bv`. Always use `--robot-*` flags (`--robot-triage`, `--robot-next`, `--robot-plan`, `--robot-insights`, `--robot-priority`, `--robot-alerts` — selection guide in [references/BV_TRIAGE.md](references/BV_TRIAGE.md)).

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
5. Wire dependencies with `br dep add`. Do not hand-edit JSONL or
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

Symptom → fix table (command not found, not-a-git-repo, init missing, ID prefix errors, `bv` hangs, dependency cycles, sync direction confusion): [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md). The two most common: a hung `bv` means a robot flag was omitted; br sync confusion means the direction (`--flush-only` vs `--import-only`) wasn't specified.

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
