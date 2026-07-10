# br Configuration

## Configuration Precedence (High to Low)

1. **CLI flags** (highest priority)
2. **Environment variables**
3. **Project config**: `_beads/config.yaml` in the resolved private ledger
4. **User config**: `~/.config/beads/config.yaml`
5. **Defaults** (lowest priority)

---

## Example Config File

```yaml
# _beads/config.yaml

# Issue ID prefix (default: "bd")
id:
  prefix: "myproject"

# Default values for new issues
defaults:
  priority: 2        # P2 = MEDIUM (0-4 scale)
  type: "task"
  assignee: "team@example.com"

# Output formatting
output:
  color: true
  date_format: "%Y-%m-%d"

# Sync behavior
sync:
  auto_import: false
  auto_flush: false
  branch: beads-sync  # Use dedicated sync branch
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BEADS_DB` | Override database path |
| `BEADS_JSONL` | Override JSONL path (requires `--allow-external-jsonl`) |
| `RUST_LOG` | Logging level (debug, info, warn, error) |

---

## Config Commands

```bash
BEADS_DIR="$(ao beads dir)" br config --list
BEADS_DIR="$(ao beads dir)" br config --get id.prefix
BEADS_DIR="$(ao beads dir)" br config --set defaults.priority=1
```

---

## Storage Paths

AgentOps stores live tracker data in the resolved private `_beads/` ledger:

```
_beads/
├── beads.db        # SQLite database (primary storage)
├── beads.db-shm    # SQLite shared memory (WAL mode)
├── beads.db-wal    # SQLite write-ahead log
├── issues.jsonl    # JSONL export (for git)
├── config.yaml     # Project configuration
└── metadata.json   # Workspace metadata
```
