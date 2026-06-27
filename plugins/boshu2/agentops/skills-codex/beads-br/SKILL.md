---
name: beads-br
description: Local-first issue tracker (beads_rust) for
---
<!-- TOC: Critical Rules | Quick Workflow | Essential Commands | bv Integration | References -->

# beads-br — Beads Rust Issue Tracker

> **Non-invasive:** br NEVER runs git commands. Sync and commit are YOUR responsibility.

## Critical Rules for Agents

| Rule | Why |
|------|-----|
| **ALWAYS use `--json`** | Structured output for parsing |
| **NEVER run bare `bv`** | Blocks session in TUI mode |
| **Sync is EXPLICIT** | `BEADS_DIR="$(ao beads dir)" br sync --flush-only` after changes |
| **Git is YOUR job** | br never runs git; `_beads/` sync is explicit |
| **No cycles allowed** | `br dep cycles` must return empty |

## Private-ledger repos — the persist_intent port contract

Some repos declare a **private bead ledger** separated from the public source
tree. The agentops repo is the canonical case; an agent that loads only this
skill (without the repo CLAUDE.md) must still honor these invariants:

| Invariant | Rule |
|---|---|
| **Indirection** | Resolve first with `ao beads dir`, then invoke as `BEADS_DIR="$(ao beads dir)" br <cmd>`. A worktree-local ledger path is valid only in the canonical checkout; linked worktrees use git's common dir to reach the canonical private ledger. |
| **Private repo** | `_beads/` is its **own git repository** (separate remote). Sync = `git -C "$(ao beads dir)" push`. |
| **Never leak** | never stage the private ledger from the host repo — bead bodies carry private context; the host repo is public and gitignores the ledger. |
| **bd is retired** | because the bd/Dolt remote-server lane was retired (2026-06-11) — do not run `bd` in a br repo; it appears only in explicitly-marked legacy notes. |
| **Prefix filter** | to prevent cross-project leakage in shared DBs, filter queries by the repo's issue prefix (e.g. `ag-`) before trusting `br ready` output. |

This section is the `persist_intent` port contract: the skill that persists
intent owns the rules that keep that intent private and uncorrupted.

## Quick Workflow

```bash
# 1. Find work
BEADS_DIR="$(ao beads dir)" br ready --json

# 2. Claim it
BEADS_DIR="$(ao beads dir)" br update ag-abc123 --claim --json

# 3. Do work...

# 4. Complete
BEADS_DIR="$(ao beads dir)" br close ag-abc123 --reason "Implemented X"

# 5. Sync to git (EXPLICIT!)
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: close ag-abc123" && git -C "$(ao beads dir)" push
```

## Essential Commands

```bash
# Lifecycle
BEADS_DIR="$(ao beads dir)" br create "Title" -p 1 -t task --json
BEADS_DIR="$(ao beads dir)" br update <id> --claim --json
BEADS_DIR="$(ao beads dir)" br close <id> --reason "Done"
BEADS_DIR="$(ao beads dir)" br reopen <id>

# Querying (always use --json for agents)
BEADS_DIR="$(ao beads dir)" br ready --json
BEADS_DIR="$(ao beads dir)" br list --json
BEADS_DIR="$(ao beads dir)" br blocked --json
BEADS_DIR="$(ao beads dir)" br search "keyword"
BEADS_DIR="$(ao beads dir)" br show <id> --json

# Dependencies
BEADS_DIR="$(ao beads dir)" br dep add <child> <parent>
BEADS_DIR="$(ao beads dir)" br dep cycles
BEADS_DIR="$(ao beads dir)" br dep tree <id>

# Sync (EXPLICIT - never automatic)
BEADS_DIR="$(ao beads dir)" br sync --flush-only
BEADS_DIR="$(ao beads dir)" br sync --import-only

# System
BEADS_DIR="$(ao beads dir)" br doctor
BEADS_DIR="$(ao beads dir)" br config --list
```

## Priority Scale

| Priority | Meaning |
|----------|---------|
| 0 | Critical |
| 1 | High |
| 2 | Medium (default) |
| 3 | Low |
| 4 | Backlog |

## bv Integration

**CRITICAL:** Never run bare `bv` — it launches interactive TUI and blocks.

```bash
# Always use --robot-* flags:
bv --robot-next                      # Single top pick
bv --robot-triage                    # Full triage
bv --robot-plan                      # Parallel execution tracks
bv --robot-insights | jq '.Cycles'   # Check graph health
```

## Agent Mail Coordination

Use bead ID as thread_id for multi-agent coordination:

```python
file_reservation_paths(..., reason="ag-123")
send_message(..., thread_id="ag-123", subject="[ag-123] Starting...")
# Work...
BEADS_DIR="$(ao beads dir)" br close ag-123 --reason "Completed"
release_file_reservations(...)
```

## Session Ending Pattern

```bash
git pull --rebase
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: update issues" && git -C "$(ao beads dir)" push
git push
git status  # Verify clean
```

## Issue-Lifecycle Discipline

Folded from the retired `beads` umbrella (ag-ez7y6) — operating doctrine, not
the command surface above. These keep the tracker graph honest across sessions:

- **Live reads are authoritative.** Treat live `BEADS_DIR="$(ao beads dir)" br show` / `ready` / `list`
  output as the source of truth for current tracker state. Do NOT treat the
  exported `issues.jsonl` as the primary decision source when live `br` data is
  available — the JSONL is a git-friendly export artifact, refreshed on
  `BEADS_DIR="$(ao beads dir)" br sync --flush-only`.
- **Scoped closure proof on every close.** `br close <id> --reason` must name the
  touched files (or explicit no-file evidence artifact), the validation
  command(s) run, and the parent-reconciliation outcome. Never close a child
  bead with a generic reason like "done" or "implemented".
- **Reconcile the parent in the same session.** After closing or materially
  updating a child bead, reconcile the open parent: update stale "remaining gap"
  notes immediately, and close the parent when the child resolved its last real
  gap.
- **Narrow the umbrella issue before implementing.** If `BEADS_DIR="$(ao beads dir)" br ready --json` surfaces a
  broad umbrella bead, do not implement against vague parent wording — first
  narrow the remaining gap into an execution-ready child bead, land the child,
  then reconcile the parent.
- **Normalize stale queue items instead of skipping them.** Rewrite broad or
  partially-absorbed beads to the actual remaining gap rather than silently
  passing over them.

## Anti-Patterns

- Running `br sync` without `--flush-only` or `--import-only`
- Forgetting sync before git commit
- Creating circular dependencies
- Running bare `bv`
- Assuming auto-commit behavior

## Storage

```
_beads/
├── beads.db        # SQLite (primary)
├── issues.jsonl    # Git-friendly export
└── config.yaml     # Optional config
```

## Troubleshooting

```bash
BEADS_DIR="$(ao beads dir)" br doctor       # Full diagnostics
BEADS_DIR="$(ao beads dir)" br dep cycles   # Must be empty
BEADS_DIR="$(ao beads dir)" br config --list
```

**Worktree error** (`'main' is already checked out`):
```bash
git branch beads-sync main
br config set sync.branch beads-sync
```

---

## References

| Topic | File |
|-------|------|
| Full command reference | [COMMANDS.md](references/COMMANDS.md) |
| Configuration details | [CONFIG.md](references/CONFIG.md) |
| Troubleshooting guide | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |
| Multi-agent patterns | [INTEGRATION.md](references/INTEGRATION.md) |
