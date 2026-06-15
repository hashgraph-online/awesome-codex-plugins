# CLI Command Reference

**For:** AI agents and developers using bd command-line interface
**Version:** 0.21.0+

## Quick Navigation

- [Basic Operations](#basic-operations)
- [Issue Management](#issue-management)
- [Dependencies & Labels](#dependencies--labels)
- [Filtering & Search](#filtering--search)
- [Advanced Operations](#advanced-operations)
- [Database Management](#database-management)

## Basic Operations

### Check Status

```bash
# Inspect the active database
bd info --json
bd info --schema --json
```

### Find Work

```bash
# Find ready work (no blockers)
br ready --json

# Find stale issues (not updated recently)
bd stale --days 30 --json                    # Default: 30 days
bd stale --days 90 --status in_progress --json  # Filter by status
bd stale --limit 20 --json                   # Limit results
```

## Issue Management

### Create Issues

```bash
# Basic creation
# IMPORTANT: Always quote titles and descriptions with double quotes
br create "Issue title" -t bug|feature|task -p 0-4 -d "Description" --json

# Create with explicit ID (for parallel workers)
br create "Issue title" --id worker1-100 -p 1 --json

# Create with labels (--labels or --label work)
br create "Issue title" -t bug -p 1 -l bug,critical --json
br create "Issue title" -t bug -p 1 --label bug,critical --json

# Examples with special characters (all require quoting):
br create "Fix: auth doesn't validate tokens" -t bug -p 1 --json
br create "Add support for OAuth 2.0" -d "Implement RFC 6749 (OAuth 2.0 spec)" --json

# Create multiple issues from markdown file
br create -f feature-plan.md --json

# Create epic with hierarchical child tasks
br create "Auth System" -t epic -p 1 --json         # Returns: bd-a3f8e9
br create "Login UI" -p 1 --json                     # Auto-assigned: bd-a3f8e9.1
br create "Backend validation" -p 1 --json           # Auto-assigned: bd-a3f8e9.2
br create "Tests" -p 1 --json                        # Auto-assigned: bd-a3f8e9.3

# Create and link discovered work (one command)
br create "Found bug" -t bug -p 1 --deps discovered-from:<parent-id> --json
```

### Update Issues

```bash
# Update one or more issues
bd update <id> [<id>...] --status in_progress --json
bd update <id> [<id>...] --priority 1 --json

# Edit issue fields in $EDITOR (HUMANS ONLY - not for agents)
# NOTE: This command is intentionally NOT exposed via the MCP server
# Agents should use 'bd update' with field-specific parameters instead
bd edit <id>                    # Edit description
bd edit <id> --title            # Edit title
bd edit <id> --design           # Edit design notes
bd edit <id> --notes            # Edit notes
bd edit <id> --acceptance       # Edit acceptance criteria
```

### Close/Reopen Issues

```bash
# Complete work (supports multiple IDs)
bd close <id> [<id>...] --reason "Done" --json

# Reopen closed issues (supports multiple IDs)
bd reopen <id> [<id>...] --reason "Reopening" --json
```

### View Issues

```bash
# Show dependency tree
br dep tree <id>

# Get issue details (supports multiple IDs)
bd show <id> [<id>...] --json
```

## Dependencies & Labels

### Dependencies

```bash
# Link discovered work (old way - two commands)
br dep add <discovered-id> <parent-id> --type discovered-from

# Create and link in one command (new way - preferred)
br create "Issue title" -t bug -p 1 --deps discovered-from:<parent-id> --json
```

### Labels

```bash
# Label management (supports multiple IDs)
bd label add <id> [<id>...] <label> --json
bd label remove <id> [<id>...] <label> --json
bd label list <id> --json
bd label list-all --json
```

## Filtering & Search

### Basic Filters

```bash
# Filter by status, priority, type
br list --status open --priority 1 --json               # Status and priority
br list --assignee alice --json                         # By assignee
br list --type bug --json                               # By issue type
br list --id bd-123,bd-456 --json                       # Specific IDs
```

### Label Filters

```bash
# Labels (AND: must have ALL)
br list --label bug,critical --json

# Labels (OR: has ANY)
br list --label-any frontend,backend --json
```

### Text Search

```bash
# Title search (substring)
br list --title "auth" --json

# Pattern matching (case-insensitive substring)
br list --title-contains "auth" --json                  # Search in title
br list --desc-contains "implement" --json              # Search in description
br list --notes-contains "TODO" --json                  # Search in notes
```

### Date Range Filters

```bash
# Date range filters (YYYY-MM-DD or RFC3339)
br list --created-after 2024-01-01 --json               # Created after date
br list --created-before 2024-12-31 --json              # Created before date
br list --updated-after 2024-06-01 --json               # Updated after date
br list --updated-before 2024-12-31 --json              # Updated before date
br list --closed-after 2024-01-01 --json                # Closed after date
br list --closed-before 2024-12-31 --json               # Closed before date
```

### Empty/Null Checks

```bash
# Empty/null checks
br list --empty-description --json                      # Issues with no description
br list --no-assignee --json                            # Unassigned issues
br list --no-labels --json                              # Issues with no labels
```

### Priority Ranges

```bash
# Priority ranges
br list --priority-min 0 --priority-max 1 --json        # P0 and P1 only
br list --priority-min 2 --json                         # P2 and below
```

### Combine Filters

```bash
# Combine multiple filters
br list --status open --priority 1 --label-any urgent,critical --no-assignee --json
```

## Global Flags

Global flags work with any bd command and must appear **before** the subcommand.

### Sandbox Mode

**Auto-detection (v0.21.1+):** bd automatically detects sandboxed environments and enables sandbox mode.

When detected, you'll see: `ℹ️  Sandbox detected, using direct mode`

**Manual override:**

```bash
# Explicitly enable sandbox mode
bd --sandbox <command>
```

**What it does:**
- Disables auto-sync while the command runs
- Keeps the command isolated from background state reconciliation

**When to use:** Sandboxed worker environments or restricted automation where you want side-effect-limited execution.

### Staleness Control

```bash
# Skip staleness check (emergency escape hatch)
bd --allow-stale <command>

# Example: access database even if out of sync with JSONL
bd --allow-stale ready --json
bd --allow-stale list --status open --json
```

**Shows:** `⚠️  Staleness check skipped (--allow-stale), data may be out of sync`

**⚠️ Caution:** May show stale or incomplete data. Use only when stuck and other options fail.

### Force JSONL Repair

```bash
# Rebuild database state from the current JSONL source of truth
bd doctor --fix --source=jsonl --yes
```

**When to use:** Local beads state looks stale or inconsistent after pull/rebase or after manual JSONL edits.

**Note:** The current CLI in this workspace does not expose the older import subcommand.

### Other Global Flags

```bash
# JSON output for programmatic use
bd --json <command>

# Sandbox mode
bd --sandbox <command>

# Custom database path
bd --db /path/to/.beads/beads.db <command>

# Custom actor for audit trail
bd --actor alice <command>
```

**See also:**
- [TROUBLESHOOTING.md - Sandboxed environments](TROUBLESHOOTING.md#sandboxed-environments-codex-claude-code-etc) for detailed sandbox troubleshooting
- `bd doctor --json` for health checks and `bd vc status` for Dolt inspection

## Advanced Operations

### Cleanup

```bash
# Clean up closed issues (bulk deletion)
bd admin cleanup --force --json                                   # Delete ALL closed issues
bd admin cleanup --older-than 30 --force --json                   # Delete closed >30 days ago
bd admin cleanup --dry-run --json                                 # Preview what would be deleted
bd admin cleanup --older-than 90 --cascade --force --json         # Delete old + dependents
```

### Duplicate Detection & Merging

```bash
# Find and merge duplicate issues
bd duplicates                                          # Show all duplicates
bd duplicates --auto-merge                             # Automatically merge all
bd duplicates --dry-run                                # Preview merge operations

# Merge specific duplicate issues
bd merge <source-id...> --into <target-id> --json      # Consolidate duplicates
bd merge bd-42 bd-43 --into bd-41 --dry-run            # Preview merge
```

### Compaction (Memory Decay)

```bash
# Agent-driven compaction
bd admin compact --analyze --json                           # Get candidates for review
bd admin compact --analyze --tier 1 --limit 10 --json       # Limited batch
bd admin compact --apply --id bd-42 --summary summary.txt   # Apply compaction
bd admin compact --apply --id bd-42 --summary - < summary.txt  # From stdin
bd admin compact --stats --json                             # Show statistics

# Legacy AI-powered compaction (requires ANTHROPIC_API_KEY)
bd admin compact --auto --dry-run --all                     # Preview
bd admin compact --auto --all --tier 1                      # Auto-compact tier 1

# Restore compacted issue from git history
bd restore <id>  # View full history at time of compaction
```

### Rename Prefix

```bash
# Rename issue prefix (e.g., from 'knowledge-work-' to 'kw-')
bd rename-prefix kw- --dry-run  # Preview changes
bd rename-prefix kw- --json     # Apply rename
```

## Database Management

### Export/Repair

```bash
# Export a JSONL snapshot
bd export -o backup.jsonl

# Rebuild database state from JSONL when local state is stale
bd doctor --fix --source=jsonl --yes

# Restore from a backup directory created by `bd backup`
bd backup restore /path/to/backup-dir

# Inspect or commit Dolt state when using the Dolt backend
bd vc status
bd vc commit -m "Repair beads state"
```

**Current CLI note:**

- Older docs referenced removed import/sync commands, but the installed CLI in this workspace does not expose them.
- Prefer automatic JSONL sync for normal work, `bd doctor --fix --source=jsonl` for repairs, and `bd backup restore` for recovery from backups.

**When to use:**
- Use `allow` (default) for daily imports and auto-sync
- Use `resurrect` when importing from databases with deleted parents
- Use `strict` for controlled imports requiring guaranteed parent existence
- Use `skip` rarely - only for selective imports

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for repair paths and [ANTI_PATTERNS.md](ANTI_PATTERNS.md) for state-management pitfalls.

### Migration

```bash
# Migrate databases after version upgrade
bd migrate                                             # Detect and migrate old databases
bd migrate --dry-run                                   # Preview migration
bd migrate --cleanup --yes                             # Migrate and remove old files

# AI-supervised migration (check before running bd migrate)
bd migrate --inspect                                   # Show migration plan for AI agents (human-readable)
bd upgrade status --json                               # Get current bd and schema version as JSON
bd status --json                                       # Get issue database summary as JSON
```

**Migration workflow for AI agents:**

1. Run `bd upgrade status --json` and `bd status --json` for machine-readable version and database health.
2. Run `bd migrate --inspect` to see pending migrations and warnings. Treat this output as human-readable unless the installed `bd` help proves otherwise.
3. Check for `missing_config` (like issue_prefix).
4. Review migration safety invariants before applying migrations.
5. If warnings exist, fix config issues first, then run `bd migrate` safely.

**Migration safety invariants:**

- **required_config_present**: Ensures issue_prefix and schema_version are set
- **foreign_keys_valid**: No orphaned dependencies or labels
- **issue_count_stable**: Issue count doesn't decrease unexpectedly

These invariants prevent data loss and would have caught issues like GH #201 (missing issue_prefix after migration).

### Database Inspection / Health

The current CLI in this workspace does not expose daemon-management commands.
Use database inspection, health, and Dolt VC commands instead.

```bash
# Inspect the active database
bd info --json

# Check health or repair from JSONL
bd doctor --json
bd doctor --fix --source=jsonl --yes

# Inspect Dolt state when using the Dolt backend
bd vc status
```

### Sync / VC Operations

```bash
# Inspect the Dolt working set (optional)
bd vc status

# Create a Dolt commit when you need one explicitly
bd vc commit -m "Update issue state"

# Export a JSONL snapshot on demand
bd export -o backup.jsonl
```

## Issue Types

- `bug` - Something broken that needs fixing
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature composed of multiple issues (supports hierarchical children)
- `chore` - Maintenance work (dependencies, tooling)

**Hierarchical children:** Epics can have child issues with dotted IDs (e.g., `bd-a3f8e9.1`, `bd-a3f8e9.2`). Children are auto-numbered sequentially. Up to 3 levels of nesting supported.

## Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (nice-to-have features, minor bugs)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

## Dependency Types

- `blocks` - Hard dependency (issue X blocks issue Y)
- `related` - Soft relationship (issues are connected)
- `parent-child` - Epic/subtask relationship
- `discovered-from` - Track issues discovered during work

Only `blocks` dependencies affect the ready work queue.

**Note:** When creating an issue with a `discovered-from` dependency, the new issue automatically inherits the parent's `source_repo` field.

## Output Formats

### JSON Output (Recommended for Agents)

Always use `--json` flag for programmatic use:

```bash
# Single issue
bd show bd-42 --json

# List of issues
br ready --json

# Operation result
br create "Issue" -p 1 --json
```

### Human-Readable Output

Default output without `--json`:

```bash
br ready
# bd-42  Fix authentication bug  [P1, bug, in_progress]
# bd-43  Add user settings page  [P2, feature, open]
```

## Common Patterns for AI Agents

### Claim and Complete Work

```bash
# 1. Find available work
br ready --json

# 2. Claim issue
bd update bd-42 --status in_progress --json

# 3. Work on it...

# 4. Close when done
bd close bd-42 --reason "Implemented and tested" --json
```

### Discover and Link Work

```bash
# While working on bd-100, discover a bug

# Old way (two commands):
br create "Found auth bug" -t bug -p 1 --json  # Returns bd-101
br dep add bd-101 bd-100 --type discovered-from

# New way (one command):
br create "Found auth bug" -t bug -p 1 --deps discovered-from:bd-100 --json
```

### Batch Operations

```bash
# Update multiple issues at once
bd update bd-41 bd-42 bd-43 --priority 0 --json

# Close multiple issues
bd close bd-41 bd-42 bd-43 --reason "Batch completion" --json

# Add label to multiple issues
bd label add bd-41 bd-42 bd-43 urgent --json
```

### Session Workflow

```bash
# Start of session
br ready --json  # Find work

# During session
br create "..." -p 1 --json
bd update bd-42 --status in_progress --json
# ... work ...

# End of session (IMPORTANT!)
bd export -o .beads/issues.jsonl  # If this repo tracks the export artifact
bd vc status
bd dolt commit -m "Refresh tracker state"  # If Dolt changes are pending
bd dolt push  # Only if a Dolt remote is configured
```

**Always finish with your normal git commit/push workflow.** Treat live `bd` queries as canonical state and refresh `.beads/issues.jsonl` explicitly when the repo tracks it.

## See Also

- [WORKFLOWS.md](WORKFLOWS.md) - Step-by-step bd usage patterns and checklists
- [BOUNDARIES.md](BOUNDARIES.md) - When to use bd vs Task tools
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Error resolution and repair commands
- [ANTI_PATTERNS.md](ANTI_PATTERNS.md) - Failure modes to avoid
- [AGENTS.md](../../../AGENTS.md) - Repo-level agent workflow guide
- [README.md](../../../README.md) - User-facing project overview
