# Troubleshooting Guide

Common issues encountered when using bd and how to resolve them.

**See also**: [ANTI_PATTERNS.md](ANTI_PATTERNS.md) for preventable mistakes.

## Interface-Specific Troubleshooting

**MCP tools (local environment):**
- Older docs referenced daemon-management commands, but the installed CLI in this workspace does not expose them
- If MCP tools fail, confirm the selected database with `bd info --json`
- Prefer live `bd` reads over `.beads/issues.jsonl` when deciding what is true right now
- If local state looks stale, run `bd doctor --json` or `bd doctor --fix --source=jsonl --yes`

**CLI (web environment or local):**
- Use direct `bd` commands (`ready`, `show`, `update`, `close`) without daemon/no-daemon toggles
- Web environment: Install via `npm install -g @beads/cli`
- Web environment: Initialize via `bd init <prefix>` before first use

**Most issues below apply to both interfaces** - the underlying database, JSONL export, and Dolt VC behavior are the same.
Treat `.beads/issues.jsonl` as an export artifact, not the canonical state source, whenever live `bd` queries are available.

## Contents

- [Database Out of Sync / Prefix Mismatch](#database-out-of-sync--prefix-mismatch)
- [Molecule-Style ID Corruption](#molecule-style-id-corruption)
- [Dependencies Not Persisting](#dependencies-not-persisting)
- [Status Updates Not Visible](#status-updates-not-visible)
- [Daemon Commands Missing](#daemon-commands-missing)
- [Database Errors on Cloud Storage](#database-errors-on-cloud-storage)
- [JSONL File Not Created](#jsonl-file-not-created)
- [`bd dolt push` Fails Because No Remote Is Configured](#bd-dolt-push-fails-because-no-remote-is-configured)
- [Version Requirements](#version-requirements)

---

## Database Out of Sync / Prefix Mismatch

### Symptom
```bash
br list
# Error: Database out of sync with JSONL.

# Current CLI repair path:
bd doctor --fix --source=jsonl --yes
```

### Root Cause
Multiple prefixes accumulated in the JSONL file, but the database is configured for a single prefix. This typically happens when:
1. Formula/molecule templates created issues with their own prefixes
2. Issues were manually added with wrong prefixes
3. JSONL files from different projects were merged

### Resolution

**Option 1: Filter to single prefix (preserves valid data)**
```bash
cd .beads
cp issues.jsonl issues.jsonl.bak

# Keep only issues with correct prefix (e.g., ap-)
grep -E '"id":"ap-' issues.jsonl.bak > issues.jsonl

# Rebuild database state from JSONL
bd doctor --fix --source=jsonl --yes
```

**Option 2: Normalize IDs, then rebuild**
```bash
# Current CLI does not expose the old rename-on-import repair path.
# Fix the JSONL contents first, then rebuild from JSONL.
grep -E '"id":"[a-z]+-[a-z0-9]+"' issues.jsonl > clean.jsonl
mv clean.jsonl issues.jsonl
bd doctor --fix --source=jsonl --yes
```

**Option 3: Nuclear rebuild**
```bash
rm -rf .beads/*.db
bd doctor --fix --source=jsonl --yes
```

### Prevention
- **Single prefix per database**: Never create issues with different prefixes
- **Formula discipline**: Ensure formulas use parent epic's prefix
- **Regular audits**: `grep -o '"id":"[^-]*' .beads/issues.jsonl | sort -u`

---

## Molecule-Style ID Corruption

### Symptom
```bash
# Historical docs mention a removed rename-on-import repair path,
# but the current CLI repairs from JSONL via `bd doctor`.
bd doctor --fix --source=jsonl --yes
```

### Root Cause
Issues were created with dot-hierarchical IDs like:
- `code-map-validation.calculate-coverage`
- `etl-throughput-optimization.enable-parallel-sync`

These don't match the standard `prefix-hash` format and can't be renamed.

### Resolution

**Filter out malformed IDs**:
```bash
cd .beads
cp issues.jsonl issues.jsonl.bak

# Keep only standard format IDs (prefix-alphanumeric, no dots)
grep -E '"id":"[a-z]+-[a-z0-9]+"' issues.jsonl.bak > issues.jsonl

# Check what was removed
diff <(wc -l < issues.jsonl.bak) <(wc -l < issues.jsonl)

# Rebuild from the cleaned JSONL file
rm -f *.db
bd doctor --fix --source=jsonl --yes
```

**Full reset** (if too corrupted):
```bash
rm -rf .beads/
bd init --prefix=ap
```

### Prevention
- **Never use dots in IDs**: IDs must be `prefix-hash` format
- **Audit formula outputs**: Check that spawned issues have correct format
- **Reject molecule templates that create custom prefixes**

---

## Dependencies Not Persisting

### Symptom
```bash
br dep add issue-2 issue-1 --type blocks
# Reports: ✓ Added dependency
bd show issue-2
# Shows: No dependencies listed
```

### Root Cause (Fixed in v0.15.0+)
This was a **bug in bd** (GitHub issue #101) where the daemon ignored dependencies during issue creation. **Fixed in bd v0.15.0** (Oct 21, 2025).

### Resolution

**1. Check your bd version:**
```bash
bd version
```

**2. If version < 0.15.0, update bd:**
```bash
# Via Homebrew (macOS/Linux)
brew upgrade bd

# Via go install
go install github.com/steveyegge/beads/cmd/bd@latest

# Via package manager
# See https://github.com/steveyegge/beads#installing
```

**3. Re-check local state after upgrade:**
```bash
bd info --json
bd doctor --check=validate --json
```

**4. Test dependency creation:**
```bash
br create "Test A" -t task
br create "Test B" -t task
br dep add <B-id> <A-id> --type blocks
bd show <B-id>
# Should show: "Depends on (1): → <A-id>"
```

### Still Not Working?

If dependencies still don't persist after updating:

1. **Confirm you're using the expected database:**
   ```bash
   bd info --json
   ```

2. **Repair from JSONL if the local state looks stale:**
   ```bash
   bd doctor --fix --source=jsonl --yes
   ```

3. **Check JSONL file:**
   ```bash
   cat .beads/issues.jsonl | jq '.dependencies'
   # Should show dependency array
   ```

4. **Report to beads GitHub** with:
   - `bd version` output
   - Operating system
   - Reproducible test case

---

## Status Updates Not Visible

### Symptom
```bash
bd update issue-1 --status in_progress
# Reports: ✓ Updated issue: issue-1
bd show issue-1
# Shows unexpected or stale data
```

### Root Cause
Usually one of three things is happening:
- `bd` is pointed at a different database than you expect
- Local state is stale after pull/rebase or manual JSONL edits
- Dolt working-set changes have not been inspected yet
- You refreshed or read `.beads/issues.jsonl` instead of checking live `bd show`/`br ready`

### Resolution

**Option 1: Check which database bd is using**
```bash
bd info --json
```

**Option 2: Repair local state from JSONL**
```bash
bd doctor --fix --source=jsonl --yes
```

**Option 3: Inspect Dolt state**
```bash
bd vc status
```

**Option 4: Refresh the tracked export after tracker writes**
```bash
bd export -o .beads/issues.jsonl
```

**Important**:
- Use `bd show <id>` to confirm current issue truth
- Use `.beads/issues.jsonl` for export parity or repair workflows, not as the first read path

### When This Usually Happens

- After moving between worktrees or clones
- After hand-editing `.beads/issues.jsonl`
- After restoring from backup or recovering a Dolt database

---

## Daemon Commands Missing

### Symptom
```bash
<historical daemon command>
# Error: unknown command "daemon" for "bd"
```

### Root Cause
These references describe an older bd command surface. The installed CLI in this
workspace does not expose daemon-management commands.

### Resolution

```bash
# Inspect the active database
bd info --json

# Check health / repair local state
bd doctor --json
bd doctor --fix --source=jsonl --yes

# Inspect Dolt working state when needed
bd vc status
```

---

## Database Errors on Cloud Storage

### Symptom
```bash
# In directory: /Users/name/Google Drive/...
bd init myproject
# Error: disk I/O error (522)
# OR: Error: database is locked
```

### Root Cause
**SQLite incompatibility with cloud sync filesystems.**

Cloud services (Google Drive, Dropbox, OneDrive, iCloud) don't support:
- POSIX file locking (required by SQLite)
- Consistent file handles across sync operations
- Atomic write operations

This is a **known SQLite limitation**, not a bd bug.

### Resolution

**Move bd database to local filesystem:**

```bash
# Wrong location (cloud sync)
~/Google Drive/My Work/project/.beads/  # ✗ Will fail

# Correct location (local disk)
~/Repos/project/.beads/                 # ✓ Works reliably
~/Projects/project/.beads/              # ✓ Works reliably
```

**Migration steps:**

1. **Move project to local disk:**
   ```bash
   mv ~/Google\ Drive/project ~/Repos/project
   cd ~/Repos/project
   ```

2. **Re-initialize bd (if needed):**
   ```bash
   bd init myproject
   ```

3. **Restore from backup (if you have one):**
   ```bash
   bd backup restore /path/to/backup-dir
   ```

**Alternative: Use global `~/.beads/` database**

If you must keep work on cloud storage:
```bash
# Don't initialize bd in cloud-synced directory
# Use global database instead
cd ~/Google\ Drive/project
br create "My task"
# Uses ~/.beads/default.db (on local disk)
```

**Workaround limitations:**
- No per-project database isolation
- All projects share same issue prefix
- Manual tracking of which issues belong to which project

**Recommendation:** Keep code/projects on local disk, sync final deliverables to cloud.

---

## JSONL File Not Created

### Symptom
```bash
bd init myproject
br create "Test" -t task
ls .beads/
# Only shows: .gitignore, myproject.db
# Missing: issues.jsonl
```

### Root Cause
Cloud-synced filesystems can delay writes, and older docs incorrectly assumed a
daemon step would create `issues.jsonl`.

### Resolution

**Write a JSONL snapshot explicitly:**
```bash
bd export -o .beads/issues.jsonl
ls .beads/issues.jsonl
# ✓ File created

# Create issues normally
br create "Task 1" -t task
cat .beads/issues.jsonl
# ✓ Shows task data
```

**Why this matters:**
- `bd init` sets up the database, not necessarily a JSONL snapshot
- `bd export` writes the JSONL file explicitly
- `bd doctor --fix --source=jsonl --yes` can rebuild database state from JSONL if needed
- Agents should still trust live `bd` queries first; the JSONL file is a snapshot artifact

**Pattern for batch scripts:**
```bash
#!/bin/bash
# Batch import script

bd init myproject
bd export -o .beads/issues.jsonl

for item in "${items[@]}"; do
    br create "$item" -t feature
done

# Query results
bd stats
```

---

## Version Requirements

### Minimum Version for Dependency Persistence

**Issue:** Dependencies created but don't appear in `bd show` or dependency tree.

**Fix:** Upgrade to **bd v0.15.0+** (released Oct 2025)

**Check version:**
```bash
bd version
# Should show: bd version 0.15.0 or higher
```

**If using MCP plugin:**
```bash
# Update Codex beads plugin
claude plugin update beads
```

### Breaking Changes

**v0.15.0:**
- MCP parameter names changed from `from_id/to_id` to `issue_id/depends_on_id`
- Dependency creation now persists correctly in the current CLI workflow

**v0.14.0:**
- Daemon architecture changes
- Auto-sync behavior changed, but agents should still explicitly export tracked `.beads/issues.jsonl` after tracker mutations

---

## `bd dolt push` Fails Because No Remote Is Configured

### Symptom
```bash
bd dolt push
# Error indicates no Dolt remote is configured
```

### Root Cause
The tracker repository has local Dolt state, but no remote has been configured for push.

### Resolution

**Always separate local tracker durability from remote tracker sync:**
```bash
bd vc status
bd dolt commit -m "tracker: reconcile parent after child closure"   # if pending

# Only run push if a remote is configured
bd dolt remote list
bd dolt push
```

**Workflow rule**:
- Tracker commit required: pending Dolt changes exist
- Tracker push possible: a remote is configured
- Tracker push unavailable: no remote configured, report this as informational

**Do not** treat missing remote as a failed issue workflow when local tracker commits succeeded.

---

## MCP-Specific Issues

### Dependencies Created Backwards

**Symptom:**
Using MCP tools, dependencies end up reversed from intended.

**Example:**
```python
# Want: "task-2 depends on task-1" (task-1 blocks task-2)
beads_add_dependency(issue_id="task-1", depends_on_id="task-2")
# Wrong! This makes task-1 depend on task-2
```

**Root Cause:**
Parameter confusion between old (`from_id/to_id`) and new (`issue_id/depends_on_id`) names.

**Resolution:**

**Correct MCP usage (bd v0.15.0+):**
```python
# Correct: task-2 depends on task-1
beads_add_dependency(
    issue_id="task-2",        # Issue that has dependency
    depends_on_id="task-1",   # Issue that must complete first
    dep_type="blocks"
)
```

**Mnemonic:**
- `issue_id`: The issue that **waits**
- `depends_on_id`: The issue that **must finish first**

**Equivalent CLI:**
```bash
br dep add task-2 task-1 --type blocks
# Meaning: task-2 depends on task-1
```

**Verify dependency direction:**
```bash
bd show task-2
# Should show: "Depends on: task-1"
# Not the other way around
```

---

## Getting Help

### Debug Checklist

Before reporting issues, collect this information:

```bash
# 1. Version
bd version

# 2. Database location
bd info --json
echo $PWD/.beads/*.db
ls -la .beads/

# 3. Git status
git status
git log --oneline -1

# 4. JSONL contents (for dependency issues)
cat .beads/issues.jsonl | jq '.' | head -50
```

### Report to beads GitHub

If problems persist:

1. **Check existing issues:** https://github.com/steveyegge/beads/issues
2. **Create new issue** with:
   - bd version (`bd version`)
   - Operating system
   - Debug checklist output (above)
   - Minimal reproducible example
   - Expected vs actual behavior

### Codex Skill Issues

If the **bd-issue-tracking skill** provides incorrect guidance:

1. **Check skill version:**
   ```bash
   ls -la beads/
   head -20 beads/SKILL.md
   ```

2. **Report via Codex feedback** or user's GitHub

---

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| Dependencies not saving | Upgrade to bd v0.15.0+ |
| Status updates lag | Run `bd info --json`, then `bd doctor --fix --source=jsonl --yes` if state is stale |
| Daemon command missing | Current CLI has no daemon command; use `bd info` and `bd doctor` instead |
| Database errors on Google Drive | Move to local filesystem |
| JSONL file missing | Write it explicitly: `bd export -o .beads/issues.jsonl` |
| `bd dolt push` has no remote | Commit locally if needed and report push as unavailable/informational |
| Dependencies backwards (MCP) | Update to v0.15.0+, use `issue_id/depends_on_id` correctly |

---

## Related Documentation

- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [Dependencies Guide](DEPENDENCIES.md) - Understanding dependency types
- [Workflows](WORKFLOWS.md) - Step-by-step workflow guides
- [beads GitHub](https://github.com/steveyegge/beads) - Official documentation
