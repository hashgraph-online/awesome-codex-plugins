# br Integration Patterns

## bv (Beads Viewer) Integration

bv is a graph-aware triage engine for beads.

**CRITICAL:** Never run bare `bv` — it launches interactive TUI and blocks the session.

```bash
# Always use --robot-* flags:
bv --robot-triage        # Full triage with recommendations
bv --robot-next          # Single top pick
bv --robot-plan          # Parallel execution tracks
bv --robot-insights      # Graph metrics (PageRank, cycles, etc.)
```

### Check Graph Health

```bash
bv --robot-insights | jq '.Cycles'       # Must be empty
bv --robot-insights | jq '.bottlenecks'  # Find blocking issues
```

---

## MCP Agent Mail Integration

Use bead IDs as coordination threads for multi-agent work:

### Mapping Cheat Sheet

| Concept | Value |
|---------|-------|
| Mail `thread_id` | `ag-###` or the full bead id |
| Mail subject | `[ag-###] ...` |
| File reservation `reason` | `ag-###` |
| Commit messages | Include the bead id for traceability |

### Agent Mail Workflow

```python
# 1. Reserve files for bead
file_reservation_paths(..., reason="ag-123")

# 2. Announce work in thread
send_message(..., thread_id="ag-123", subject="[ag-123] Starting...")

# 3. Do work...

# 4. Close bead when done
BEADS_DIR="$(ao beads dir)" br close ag-123 --reason "Completed"

# 5. Release reservations
release_file_reservations(...)
```

---

## Multi-Agent Coordination

When multiple agents work on the same project:

1. **Use Agent Mail file reservations** to avoid conflicts
2. **Use bead ID as thread_id** for communication
3. **Check `BEADS_DIR="$(ao beads dir)" br ready --json`** to see unblocked work
4. **Close beads when done** to unblock dependents

### Finding Parallel Work

```bash
# Get parallel execution tracks
bv --robot-plan

# Multiple agents can work on independent branches of the dependency graph
```

---

## Standard Agent Workflow

```bash
# 1. Find work
BEADS_DIR="$(ao beads dir)" br ready --json

# 2. Claim work
BEADS_DIR="$(ao beads dir)" br update ag-abc123 --claim --actor "$(git config user.email)" --json

# 3. Do work...

# 4. Complete
BEADS_DIR="$(ao beads dir)" br close ag-abc123 --reason "Implemented feature X"

# 5. Sync the private tracker repo
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A
git -C "$(ao beads dir)" commit -m "tracker: close ag-abc123"
git -C "$(ao beads dir)" push
```

---

## Session Ending Pattern

Before ending any session:

```bash
git pull --rebase
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: update issues" && git -C "$(ao beads dir)" push
git push
git status  # MUST show "up to date with origin"
```

---

## Creating Good Beads

```bash
BEADS_DIR="$(ao beads dir)" br create "Title that explains the task" \
  --type task \
  --priority 1 \
  --json \
  --description "Detailed description with acceptance criteria"
```

Include in descriptions:
- Clear scope
- Acceptance criteria
- Dependencies (add separately via `br dep add`)
- Context for "future self"

---

## Differences from bd (Go beads)

| Aspect | br (Rust) | bd (Go) |
|--------|-----------|---------|
| Git operations | **Never** (explicit) | Auto-commit, hooks |
| Storage | SQLite + JSONL | Dolt/SQLite |
| Background daemon | **No** | Yes |
| Hook installation | **Manual** | Automatic |
| Complexity | Focused | Feature-rich |

### What br Does NOT Support (by design)

- Automatic git commits
- Git hook installation
- Background daemon/RPC
- Dolt backend
- Linear/Jira sync
- Web UI (use bv for TUI)
- Multi-repo sync
- Real-time collaboration
