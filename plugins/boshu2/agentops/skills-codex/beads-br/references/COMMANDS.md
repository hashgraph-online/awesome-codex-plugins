# br Command Reference

Resolve the live ledger before direct `br` use:

```bash
export BEADS_DIR="$(ao beads dir)"
```

## Global Flags

| Flag | Description |
|------|-------------|
| `--json` | JSON output (machine-readable) — **ALWAYS use for agents** |
| `--quiet` / `-q` | Suppress output |
| `--verbose` / `-v` | Increase verbosity (-vv for debug) |
| `--no-color` | Disable colored output |
| `--db <path>` | Override database path |
| `--actor <name>` | Set actor for audit trail |
| `--lock-timeout <ms>` | SQLite busy timeout |
| `--no-db` | JSONL-only mode (skip DB) |
| `--allow-stale` | Bypass freshness check |
| `--no-auto-flush` | Skip auto-export after mutations |
| `--no-auto-import` | Skip auto-import before reads |

---

## Issue Lifecycle

```bash
BEADS_DIR="$(ao beads dir)" br create "Title" -p 1 --type bug --json
BEADS_DIR="$(ao beads dir)" br q "Quick note"
BEADS_DIR="$(ao beads dir)" br show ag-abc123 --json
BEADS_DIR="$(ao beads dir)" br update ag-abc123 --priority 0 --json
BEADS_DIR="$(ao beads dir)" br close ag-abc123 --reason "Done"
BEADS_DIR="$(ao beads dir)" br reopen ag-abc123
BEADS_DIR="$(ao beads dir)" br delete ag-abc123
```

### Create Options

```bash
BEADS_DIR="$(ao beads dir)" br create "Title" \
  --priority 1 \           # 0-4 scale
  --type task \            # task, bug, feature, etc.
  --assignee "user@..." \  # Optional assignee
  --json \
  --description "..."      # Detailed description
```

### Update Options

```bash
BEADS_DIR="$(ao beads dir)" br update ag-abc123 \
  --title "New title" \
  --priority 0 \
  --status in_progress \   # open, in_progress, closed
  --assignee "new@..." \
  --json
```

---

## Querying

```bash
BEADS_DIR="$(ao beads dir)" br list --json
BEADS_DIR="$(ao beads dir)" br list --status open --json
BEADS_DIR="$(ao beads dir)" br list --priority 0-1 --json
BEADS_DIR="$(ao beads dir)" br list --assignee alice --json

BEADS_DIR="$(ao beads dir)" br ready --json

BEADS_DIR="$(ao beads dir)" br blocked --json

BEADS_DIR="$(ao beads dir)" br search "authentication"
BEADS_DIR="$(ao beads dir)" br stale --days 30 --json
BEADS_DIR="$(ao beads dir)" br count --by status --json
```

---

## Dependencies

```bash
BEADS_DIR="$(ao beads dir)" br dep add ag-child ag-parent
BEADS_DIR="$(ao beads dir)" br dep remove ag-child ag-parent
BEADS_DIR="$(ao beads dir)" br dep list ag-abc123
BEADS_DIR="$(ao beads dir)" br dep tree ag-abc123
BEADS_DIR="$(ao beads dir)" br dep cycles
```

**Critical:** `br dep cycles` must return empty. Circular dependencies break the graph.

---

## Labels

```bash
BEADS_DIR="$(ao beads dir)" br label add ag-abc123 backend auth
BEADS_DIR="$(ao beads dir)" br label remove ag-abc123 urgent
BEADS_DIR="$(ao beads dir)" br label list ag-abc123
BEADS_DIR="$(ao beads dir)" br label list-all
```

---

## Comments

```bash
BEADS_DIR="$(ao beads dir)" br comments add ag-abc123 "Found root cause"
BEADS_DIR="$(ao beads dir)" br comments list ag-abc123
```

---

## Sync

**Sync is always explicit. br NEVER auto-commits.**

```bash
BEADS_DIR="$(ao beads dir)" br sync --flush-only
BEADS_DIR="$(ao beads dir)" br sync --import-only
BEADS_DIR="$(ao beads dir)" br sync --status
```

### Workflow

```bash
# After making changes:
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: update issues"

# After pulling:
git pull
BEADS_DIR="$(ao beads dir)" br sync --import-only
```

---

## System

```bash
BEADS_DIR="$(ao beads dir)" br doctor
BEADS_DIR="$(ao beads dir)" br stats
BEADS_DIR="$(ao beads dir)" br config --list
BEADS_DIR="$(ao beads dir)" br config --get id.prefix
BEADS_DIR="$(ao beads dir)" br config --set defaults.priority=1
br version                           # Show version
br upgrade                           # Self-update (if enabled)
```

---

## JSON Output Examples

```bash
# Get first ready issue
BEADS_DIR="$(ao beads dir)" br ready --json | jq '.[0]'

# Filter high priority
BEADS_DIR="$(ao beads dir)" br list --json | jq '.issues[]? | select(.priority <= 1)'

# Get specific issue
BEADS_DIR="$(ao beads dir)" br show ag-abc123 --json | jq 'if type=="array" then (.[0] // {}) else . end | .title'
```
