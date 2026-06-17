# Beads Anti-Patterns

Hard-won lessons from production beads usage. Avoid these mistakes.

---

## Critical Anti-Patterns

### 1. Treating `.beads/issues.jsonl` as the Canonical Tracker

**DON'T**: Use `.beads/issues.jsonl` as your primary source for what is ready or what notes say when live `bd` commands are available

```bash
# WRONG
jq '.[] | select(.status=="open")' .beads/issues.jsonl
```

**DO**: Use live `bd` queries first

```bash
# CORRECT
br ready --json
bd show <id> --json
```

**Why it breaks**:
- Export files can lag behind live tracker state
- Autonomous runs make bad routing decisions when they trust stale JSONL
- Parent notes and status can already be reconciled in Dolt even if the export was not refreshed

---

### 2. Molecule-Style Issue IDs

**DON'T**: Create issues with dot-separated hierarchical IDs

```bash
# WRONG - These IDs corrupt the database
code-map-validation.calculate-coverage
etl-throughput-optimization.enable-parallel-sync
kagent-openwebui-bridge.admin-functions
```

**DO**: Use standard `prefix-xxxx` format

```bash
# CORRECT - Standard beads ID format
ap-7tc6
ap-euoy
ap-cr7k
```

**Why it breaks**:
- bd expects IDs in `prefix-hash` format
- Dot-separated IDs fail prefix validation during import
- JSONL-based repair via `bd doctor --fix --source=jsonl` errors with "invalid suffix"
- Database becomes corrupted, requiring full rebuild

**Root cause**: Early formula/molecule templates created non-standard IDs. This was a design mistake.

**Fix**: If you have molecule-style IDs, filter them out or rebuild:
```bash
# Filter to standard format only
grep -E '"id":"[a-z]+-[a-z0-9]+' .beads/issues.jsonl > clean.jsonl
mv clean.jsonl .beads/issues.jsonl
bd doctor --fix --source=jsonl --yes
```

---

### 3. Prefix Proliferation

**DON'T**: Mix multiple prefixes in one database

```bash
# WRONG - Multiple prefixes in same .beads/
code-map-validation
etl-throughput-optimization
kagent-openwebui-bridge
ap-1234
```

**DO**: One prefix per beads database

```bash
# CORRECT - Single prefix
ap-1234
ap-5678
ap-abcd
```

**Why it breaks**:
- JSONL-based repair fails with "prefix mismatch detected"
- Database configured for one prefix rejects others
- Cross-prefix dependencies don't resolve correctly

**Root cause**: Formulas/molecules created issues with their own prefixes instead of the database's prefix.

**Fix**: Enforce single prefix policy:
```bash
# Check for prefix violations
grep -o '"id":"[^-]*' .beads/issues.jsonl | sort -u
# Should show only ONE prefix
```

---

### 4. Assuming Tracked JSONL Stays Synced Automatically

**DON'T**: Mutate tracker state and assume `.beads/issues.jsonl` will stay current by itself

```bash
# WRONG
bd update ap-1234 --notes "Remaining gap narrowed to CLI parity"
# keep working without exporting tracked JSONL
```

**DO**: Refresh the tracked export explicitly after tracker writes

```bash
# CORRECT
bd update ap-1234 --notes "Remaining gap narrowed to CLI parity"
bd export -o .beads/issues.jsonl   # if tracked
```

**Why it matters**:
- The export is a git artifact, not a guaranteed live mirror
- Git history becomes misleading when tracked exports are stale
- Other agents may diff the export and see outdated state

---

### 5. Closing Child Issues Without Reconciling the Parent

**DON'T**: Close a child bead and leave the parent's stale "remaining gap" notes untouched

```bash
# WRONG
bd close pl-vnu.4 --reason "Fixed the exact remaining gap"
# parent still says the gap is open
```

**DO**: Reconcile the open parent in the same session

```bash
# CORRECT
bd close <child-id> --reason "Closed concrete remaining gap"
bd show <parent-id>
bd update <parent-id> --notes "Remaining gap now ..."
# or bd close <parent-id> when nothing real remains
```

**Why it matters**:
- Stale parent notes create false backlog
- `br ready` can surface umbrella work that is already effectively done
- Autonomous loops lose trust in tracker state

---

### 6. Implementing Broad Parent Beads Directly

**DON'T**: Take a broad umbrella bead from `br ready` and implement against the vague parent wording

```bash
# WRONG
bd show pl-vnu.5
# immediately code against the parent without narrowing the remaining gap
```

**DO**: Identify the concrete gap, create or update a narrower child bead, and execute against that child

**Why it matters**:
- Broad parents hide multiple possible gaps
- Acceptance criteria are usually too coarse for reliable execution
- Parent reconciliation becomes impossible if execution never targeted the real remaining gap

---

### 7. Mayor Implementing Instead of Dispatching

**DON'T**: Mayor role edits code directly

```bash
# WRONG - Mayor implementing
cd ~/gt/ai_platform/mayor/rig
vim services/etl/app/main.py  # NO!
```

**DO**: Mayor dispatches to polecats

```bash
# CORRECT - Mayor dispatches
gt sling ap-1234 ai_platform
# Polecat does the work, Mayor monitors
gt convoy list  <!-- FUTURE: gt convoy not yet implemented -->
```

**Why it matters**:
- Mayor context is precious (coordinates across rigs)
- Polecat isolation provides 100x context reduction
- Task agent returns ~10KB, polecat status ~100 tokens
- Mayor implementing causes context bloat

**Rule**: If you're Mayor, NEVER edit code. Even "quick fixes" go through `gt sling`.

---

### 8. Stale MR Issue Accumulation

**DON'T**: Let merge request issues pile up

```bash
br list --type=merge-request
# 35 stale MR issues from months ago
```

**DO**: Clean up MRs when branches merge

```bash
# After merge, close the MR issue
bd close ap-mr-123 --reason "Branch merged"

# Regular cleanup
br list --status=open --type=merge-request | while read id; do
    # Check if branch still exists
    git branch -r | grep -q "origin/$branch" || bd close $id --reason "Branch merged/deleted"
done
```

**Why it matters**:
- Stale MRs create noise in `br list`
- `br ready` shows work that doesn't exist
- Database bloat from abandoned tracking issues

---

### 9. Using Short IDs

**DON'T**: Use abbreviated issue IDs

```bash
# WRONG - Ambiguous
bd show 1234
bd close xyz
```

**DO**: Use full prefix-hash IDs

```bash
# CORRECT - Unambiguous
bd show ap-1234
bd close ap-xyz5
```

**Why it matters**:
- Short IDs can match multiple issues
- Cross-rig work requires full IDs for routing
- Gas Town dispatch needs full IDs

---

### 10. Creating Issues Without Context

**DON'T**: Create issues with minimal information

```bash
# WRONG - No context for future agents
br create "Fix the bug"
```

**DO**: Include enough context for resumption

```bash
# CORRECT - Self-contained context
br create "Fix authentication timeout in OAuth flow" \
  --description "Users report 30s timeout during OAuth callback.
Error in services/gateway/oauth.py:142.
Reproduce: Login with Google SSO on slow network.
Fix: Increase timeout or add retry logic." \
  --type bug \
  --priority 1
```

**Why it matters**:
- Issues survive compaction, conversations don't
- Future agent needs full context from issue alone
- 2-week resumption test: Could you restart this work from the issue text?

---

### 11. Treating `bd dolt push` Failure as Mandatory When No Remote Exists

**DON'T**: Fail the workflow just because `bd dolt push` cannot run without a configured remote

```bash
# WRONG
bd dolt push
# no remote configured -> treat entire session as failed
```

**DO**: Distinguish local tracker commits from remote tracker pushes

```bash
bd vc status
bd dolt commit -m "tracker: reconcile parent notes"   # if pending
# Run bd dolt push only if a remote is configured
```

**Why it matters**:
- Local tracker commits can still be valid and required
- Some repos use Dolt only locally
- Missing remote is an informational constraint, not a broken tracker mutation

---

## Database Health Commands

### Check for Problems

```bash
# Check prefix consistency
grep -o '"id":"[^-]*' .beads/issues.jsonl | sort -u

# Check for molecule-style IDs
grep -E '"id":"[^"]+\.[^"]+' .beads/issues.jsonl

# Check issue count
wc -l .beads/issues.jsonl

# Check database vs JSONL sync
bd doctor
```

### Maintenance Commands

```bash
# Weekly cleanup
br list --status=tombstone  # Review tombstones
bd doctor                   # Health check

# Before major work
bd vc status                # Check Dolt state (optional)
br ready                    # Verify ready queue

# After git pull, if local state looks stale
bd doctor --fix --source=jsonl --yes
```

### Nuclear Options

> **WARNING: DESTRUCTIVE OPERATIONS BELOW**
> These commands permanently delete data. Before running:
> 1. Ensure you have a backup: `cp -r .beads/ .beads.backup/`
> 2. Verify you're in the correct directory
> 3. Understand that this cannot be undone

```bash
# Full database rebuild (DESTRUCTIVE)
rm -rf .beads/*.db
bd doctor --fix --source=jsonl --yes

# Complete reset (VERY DESTRUCTIVE)
rm -rf .beads/
bd init --prefix=ap
```

---

## Gas Town Integration Rules

When using beads with Gas Town:

| Role | Can Create Issues | Can Edit Code | Uses |
|------|-------------------|---------------|------|
| Mayor | Yes (HQ beads) | NO | gt sling, gt convoy <!-- FUTURE: gt convoy not yet implemented --> |
| Crew | Yes (rig beads) | Yes | bd commands directly |
| Polecat | Update only | Yes | bd update, bd close |

**Prefix routing**:
- HQ beads: `hq-*` prefix, stored at `~/gt/.beads/`
- Rig beads: Project prefix (e.g., `ap-*`), stored at `~/gt/<rig>/.beads/`

**Creating slingable beads from Mayor**:
```bash
# Mayor can't hook hq- beads to polecats
# Create in rig database instead:
BEADS_DIR=~/gt/ai_platform/mayor/rig/.beads br create --title="Task" --type=task
```

---

## Related

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Error resolution
- [ROUTING.md](ROUTING.md) - Multi-rig prefix routing
- [WORKFLOWS.md](WORKFLOWS.md) - Correct workflow patterns
