# br Troubleshooting

## The Doctor Command

```bash
BEADS_DIR="$(ao beads dir)" br doctor
```

Checks:
- Database integrity
- Schema version
- JSONL sync status
- Configuration validity
- Path permissions

---

## Common Errors and Fixes

### "Database locked"

```bash
# Check for other br processes
pgrep -f "br "

# Force close and retry
BEADS_DIR="$(ao beads dir)" br sync --status
```

### "Issue not found"

```bash
# Check if issue exists
BEADS_DIR="$(ao beads dir)" br list --json | jq '.issues[]? | select(.id == "ag-abc123")'

# Check for similar IDs
BEADS_DIR="$(ao beads dir)" br list --json | jq '.issues[]?.id' | grep -i "abc"
```

### "Prefix mismatch"

```bash
# Check your prefix
BEADS_DIR="$(ao beads dir)" br config --get id.prefix

# Import with validation skip (careful!)
BEADS_DIR="$(ao beads dir)" br sync --import-only --skip-prefix-validation
```

### Worktree Error

If you get `failed to create worktree: 'main' is already checked out`:

```bash
git branch beads-sync main
git push -u origin beads-sync
BEADS_DIR="$(ao beads dir)" br config set sync.branch beads-sync
```

Always use a dedicated sync branch that you never check out directly.

### Check Sync Branch Configuration

```bash
BEADS_DIR="$(ao beads dir)" br config get sync.branch  # Should NOT be your current branch
git branch                                             # Verify sync branch exists
git ls-remote --heads origin beads-sync                # Verify on remote
```

`br sync --flush-only` exports to JSONL only (no git operations); bare
`br sync` (without `--flush-only`/`--import-only`) is an anti-pattern here —
git is always your job.

### Sync Issues After Git Merge

```bash
# 1. Check for JSONL merge conflicts
git -C "$(ao beads dir)" status

# 2. If conflicts, resolve manually then:
BEADS_DIR="$(ao beads dir)" br sync --import-only

# 3. If database seems stale:
BEADS_DIR="$(ao beads dir)" br doctor
```

---

## Common Problems

| Problem | Diagnosis | Fix |
|:--------|:----------|:----|
| Worktree errors | `br config get sync.branch` returns current branch | Create dedicated sync branch (above) |
| Sync branch missing on remote | `git ls-remote --heads origin beads-sync` empty | `git push -u origin beads-sync` |
| br not found | `which br` returns nothing | Install beads_rust, add to PATH |
| Cycles in graph | `br dep cycles` not empty | Review dependencies, remove cycle |
| bv shows nothing | No beads created | Run `br list` to verify |

---

## Debugging

```bash
# Verbose output
BEADS_DIR="$(ao beads dir)" br -v list

# Debug output
BEADS_DIR="$(ao beads dir)" br -vv list

# Check RUST_LOG for detailed logs
RUST_LOG=debug BEADS_DIR="$(ao beads dir)" br list
```

---

## Quick Health Check

```bash
BEADS_DIR="$(ao beads dir)" br doctor
BEADS_DIR="$(ao beads dir)" br dep cycles
BEADS_DIR="$(ao beads dir)" br config --list
which br                     # Verify br is installed
```
