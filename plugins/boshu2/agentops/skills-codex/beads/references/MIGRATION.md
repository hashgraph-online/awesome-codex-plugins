
<!-- TOC: Philosophy | THE EXACT PROMPT | Decision Tree | Command Map | Transform Patterns | Validation Loop | Risk Tiers | References -->

# bd → br Migration

> **Core Philosophy:** One behavioral change, mechanical transforms. The ONLY difference is git handling—everything else is find-replace.

## Why This Matters

Incomplete migrations leave broken docs. Agents follow stale `bd sync` instructions, expect auto-commit, and lose work. This skill ensures **complete, verified migrations**.

---

## THE EXACT PROMPT — Single File Migration

```
Migrate this file from bd (beads) to br (beads_rust).

Apply transforms IN THIS ORDER (order matters):
1. Section headers: "bd (beads)" → "br (beads_rust)"
2. Add non-invasive note after beads section header
3. Commands: `bd X` → `br X` for ready/list/show/create/update/close/dep/stats
4. Sync command: `bd sync` → `br sync --flush-only`
5. Add git steps after EVERY sync:
   git add .beads/
   git commit -m "sync beads"
6. Issue IDs: bd-### → br-### in thread_ids, subjects, reasons, commits
7. Links: beads_viewer → beads_rust (if present)

Remove completely:
- Daemon references
- Auto-commit assumptions
- Hook installation mentions
- RPC mode

Keep unchanged:
- SQLite/WAL cautions
- bv integration
- Priority system (P0-P4)

VERIFY after editing:
grep -c '`bd ' file.md     # Must be 0
grep -c 'bd sync' file.md  # Must be 0
grep -c 'br sync --flush-only' file.md  # Must be > 0
```

### Why This Prompt Works

- **Ordered transforms**: Dependencies exist (sync must change before adding git steps)
- **Explicit removals**: Daemon/RPC don't exist in br—leaving them confuses agents
- **Keep list**: Prevents accidental removal of still-valid patterns
- **Built-in verification**: Grep commands catch missed transforms
- **No degrees of freedom**: This is a LOW freedom task—exact transforms required

---

## Decision Tree: What Are You Migrating?

```
What are you migrating?
│
├─ Single file (AGENTS.md)
│  │
│  └─ Follow THE EXACT PROMPT above
│     Use: ./scripts/verify-migration.sh file.md
│
├─ Multiple files (batch)
│  │
│  ├─ <10 files → Sequential: apply prompt to each
│  │
│  └─ 10+ files → Parallel subagents
│     Batch ~10 files per agent
│     See: [BULK.md](references/BULK.md)
│
└─ Verify existing migration
   │
   └─ Run: ./scripts/find-bd-refs.sh /path
      Any output = incomplete migration
```

---

## The One Behavioral Difference

```
┌─────────────────────────────────────────────────────────────────┐
│                    bd (Go)              br (Rust)               │
├─────────────────────────────────────────────────────────────────┤
│  bd sync                     →    br sync --flush-only          │
│  (auto-commits to git)            (exports JSONL only)          │
│                                                                 │
│                              +    git add .beads/               │
│                              +    git commit -m "..."           │
└─────────────────────────────────────────────────────────────────┘

Everything else is literally s/bd/br/g
```

---

## Command Map

| bd | br | Change Type |
|----|-----|-------------|
| `br ready` | `br ready` | Name only |
| `br list` | `br list` | Name only |
| `bd show <id>` | `br show <id>` | Name only |
| `br create` | `br create` | Name only |
| `bd update` | `br update` | Name only |
| `bd close` | `br close` | Name only |
| `br dep add` | `br dep add` | Name only |
| `bd stats` | `br stats` | Name only |
| `bd sync` | `br sync --flush-only` + git | **BEHAVIORAL** |

---

## Transform Patterns

### Pattern 1: The Non-Invasive Note

**Add immediately after any beads section header:**

```markdown
**Note:** `br` is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.
```

### Pattern 2: Sync Command Transform

**Before:**
```bash
bd sync
```

**After:**
```bash
br sync --flush-only
git add .beads/
git commit -m "sync beads"
```

### Pattern 3: Session End Transform

**Before:**
```bash
git add <files>
bd sync
git push
```

**After:**
```bash
git add <files>
br sync --flush-only
git add .beads/
git commit -m "..."
git push
```

### Pattern 4: Issue ID Transform

**Before:**
```markdown
thread_id: bd-123
subject: [bd-123] Feature implementation
reason: bd-123
```

**After:**
```markdown
thread_id: br-123
subject: [br-123] Feature implementation
reason: br-123
```

---

## Validation Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                     VALIDATION IS MANDATORY                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Apply transforms                                            │
│                    ↓                                            │
│  2. Run verification:                                           │
│     ./scripts/verify-migration.sh file.md                       │
│                    ↓                                            │
│  3. If FAIL → read error → fix specific issue → goto 2          │
│                    ↓                                            │
│  4. Only proceed when PASS                                      │
│                                                                 │
│  ⚠️ Never skip verification. Incomplete migrations break agents.│
└─────────────────────────────────────────────────────────────────┘

# Complete Transform Reference

## Table of Contents
- [Section Headers](#section-headers)
- [Command Transforms](#command-transforms)
- [Workflow Transforms](#workflow-transforms)
- [Session Protocol](#session-protocol)
- [Landing the Plane](#landing-the-plane)
- [Agent Mail Integration](#agent-mail-integration)
- [Full File Example](#full-file-example)

---

## Section Headers

| Before | After |
|--------|-------|
| `## Issue Tracking with bd (beads)` | `## Issue Tracking with br (beads_rust)` |
| `## Beads (bd)` | `## Beads (br)` |
| `## Beads (bd) — Dependency-Aware Issue Tracking` | `## Beads (br) — Dependency-Aware Issue Tracking` |
| `[beads_viewer](https://...)` | `[beads_rust](https://github.com/Dicklesworthstone/beads_rust)` |

---

## Command Transforms

### Simple Renames (No Behavioral Change)

```bash
# Before → After (all identical except name)
br ready              → br ready
br list               → br list
br list --status=open → br list --status=open
bd show <id>          → br show <id>
br create             → br create
br create --title="..." --type=task --priority=2 → br create --title="..." --type=task --priority=2
bd update <id>        → br update <id>
bd update <id> --status=in_progress → br update <id> --status=in_progress
bd close <id>         → br close <id>
bd close <id> --reason="Done" → br close <id> --reason="Done"
br dep add            → br dep add
bd stats              → br stats
```

### Sync Transform (BEHAVIORAL CHANGE)

**Before:**
```bash
bd sync               # Commits and pushes
```

**After:**
```bash
br sync --flush-only  # Exports only
git add .beads/       # YOU stage
git commit -m "..."   # YOU commit
```

---

## Workflow Transforms

### Basic Workflow

**Before:**
```markdown
1. **Start**: Run `br ready` to find actionable work
2. **Claim**: Use `bd update <id> --status=in_progress`
3. **Work**: Implement the task
4. **Complete**: Use `bd close <id>`
5. **Sync**: Always run `bd sync` at session end
```

**After:**
```markdown
1. **Start**: Run `br ready` to find actionable work
2. **Claim**: Use `br update <id> --status=in_progress`
3. **Work**: Implement the task
4. **Complete**: Use `br close <id>`
5. **Sync**: Run `br sync --flush-only` then manually commit `.beads/`
```

### Agent Workflow with Commands

**Before:**
```markdown
### Agent workflow:

1. `br ready` to find unblocked work.
2. Claim: `bd update <id> --status in_progress`.
3. Implement + test.
4. Close when done.
5. Commit `.beads/` in the same commit as code changes.
```

**After:**
```markdown
### Agent workflow:

1. `br ready` to find unblocked work.
2. Claim: `br update <id> --status in_progress`.
3. Implement + test.
4. Close when done.
5. Sync and commit:
   ```bash
   br sync --flush-only
   git add .beads/
   git commit -m "..."
   ```
```

---

## Session Protocol

### Before
```bash
git status              # Check what changed
git add <files>         # Stage code changes
bd sync                 # Commit beads changes
git commit -m "..."     # Commit code
bd sync                 # Commit any new beads changes
git push                # Push to remote
```

### After
```bash
git status              # Check what changed
git add <files>         # Stage code changes
br sync --flush-only    # Export beads to JSONL (no git ops)
git add .beads/         # Stage beads changes
git commit -m "..."     # Commit everything
git push                # Push to remote
```

---

## Landing the Plane

### Before
```bash
git pull --rebase
bd sync
git push
git status  # MUST show "up to date with origin"
```

### After
```bash
git pull --rebase
br sync --flush-only    # Export beads to JSONL (no git ops)
git add .beads/         # Stage beads changes
git commit -m "sync beads"  # Commit beads
git push
git status  # MUST show "up to date with origin"
```

---

## Agent Mail Integration

### Thread ID Convention

**Before:**
```markdown
- Mail `thread_id`: `bd-###`
- Mail subject: `[bd-###] ...`
- File reservation `reason`: `bd-###`
- Commit messages: Include `bd-###` for traceability
```

**After:**
```markdown
- Mail `thread_id`: `br-###`
- Mail subject: `[br-###] ...`
- File reservation `reason`: `br-###`
- Commit messages: Include `br-###` for traceability
```

### Typical Agent Flow

**Before:**
```markdown
1. **Pick ready work (Beads):**
   ```bash
   br ready --json
   ```

2. **Reserve edit surface (Mail):**
   ```
   file_reservation_paths(..., reason="bd-123")
   ```

3. **Announce start (Mail):**
   ```
   send_message(..., thread_id="bd-123", subject="[bd-123] Start: <title>")
   ```
```

**After:**
```markdown
1. **Pick ready work (Beads):**
   ```bash
   br ready --json
   ```

2. **Reserve edit surface (Mail):**
   ```
   file_reservation_paths(..., reason="br-123")
   ```

3. **Announce start (Mail):**
   ```
   send_message(..., thread_id="br-123", subject="[br-123] Start: <title>")
   ```
```

---

## Full File Example

### Before (Complete Section)

```markdown
## Issue Tracking with bd (beads)

All issue tracking goes through **bd**. No other TODO systems.

Key invariants:
- `.beads/` is authoritative state and **must always be committed** with code changes.
- Do not edit `.beads/*.jsonl` directly; only via `bd`.

### Basics

Check ready work:
```bash
br ready --json
```

### Essential Commands

```bash
br ready              # Show issues ready to work
br list --status=open # All open issues
br create --title="..." --type=task --priority=2
bd update <id> --status=in_progress
bd close <id> --reason="Completed"
bd sync               # Commit and push changes
```

### Session End Checklist

```bash
git status
git add <files>
bd sync
git commit -m "..."
git push
```
```

### After (Complete Section)

```markdown
## Issue Tracking with br (beads_rust)

All issue tracking goes through **br** (beads_rust). No other TODO systems.

**Note:** `br` is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.

Key invariants:
- `.beads/` is authoritative state and **must always be committed** with code changes.
- Do not edit `.beads/*.jsonl` directly; only via `br`.

### Basics

Check ready work:
```bash
br ready --json
```

### Essential Commands

```bash
br ready              # Show issues ready to work
br list --status=open # All open issues
br create --title="..." --type=task --priority=2
br update <id> --status=in_progress
br close <id> --reason="Completed"
br sync --flush-only  # Export to JSONL (no git ops)
```

### Session End Checklist

```bash
git status
git add <files>
br sync --flush-only
git add .beads/
git commit -m "..."
git push
```
```

---

## Quick Search

```bash
# Find specific transform patterns
grep -i "session" references/TRANSFORMS.md
grep -i "landing" references/TRANSFORMS.md
grep -i "agent mail" references/TRANSFORMS.md
```

# Common Pitfalls & Fixes

## Table of Contents
- [Critical Pitfalls](#critical-pitfalls)
- [Transform Pitfalls](#transform-pitfalls)
- [Verification Pitfalls](#verification-pitfalls)
- [Bulk Migration Pitfalls](#bulk-migration-pitfalls)
- [Quick Diagnostics](#quick-diagnostics)

---

## Critical Pitfalls

### 1. Forgetting Manual Git Steps (THE BIG ONE)

**Symptom:** Work appears lost after session end.

**Cause:** Agent followed migrated docs but docs didn't include git steps after `br sync --flush-only`.

**Detection:**
```bash
# Find files with sync but no git add
for f in /data/projects/*/AGENTS.md; do
  if grep -q 'br sync --flush-only' "$f" && ! grep -q 'git add .beads/' "$f"; then
    echo "MISSING GIT STEPS: $f"
  fi
done
```

**Fix:** After EVERY `br sync --flush-only`, add:
```bash
git add .beads/
git commit -m "sync beads"
```

---

### 2. Incomplete Sync Transform

**Symptom:** `br sync` fails or behaves unexpectedly.

**Cause:** Transformed `bd sync` to `br sync` but forgot `--flush-only` flag.

**Detection:**
```bash
grep -n 'br sync[^-]' file.md
grep -n 'br sync$' file.md
```

**Fix:** `br sync` → `br sync --flush-only`

---

### 3. Mixed Terminology in Same File

**Symptom:** Confusing docs with both `bd-123` and `br-123` references.

**Cause:** Partial migration, missed some issue ID references.

**Detection:**
```bash
# Check for both patterns in same file
if grep -q 'bd-[0-9]' file.md && grep -q 'br-[0-9]' file.md; then
  echo "MIXED IDs in file.md"
fi
```

**Fix:** Search comprehensively:
```bash
grep -n 'bd-[0-9]' file.md
# Transform all to br-###
```

---

## Transform Pitfalls

### 4. Missing Non-Invasive Note

**Symptom:** Readers follow br commands but expect auto-commit behavior.

**Cause:** Forgot to add the critical behavioral note.

**Detection:**
```bash
# Files with br commands but no note
if grep -q '`br ' file.md && ! grep -q 'non-invasive' file.md; then
  echo "MISSING NOTE: $f"
fi
```

**Fix:** Add after section header:
```markdown
**Note:** `br` is non-invasive and never executes git commands. After `br sync --flush-only`, you must manually run `git add .beads/ && git commit`.
```

---

### 5. Daemon/Hook References Left Behind

**Symptom:** Docs mention "daemon" or "hooks" that don't exist in br.

**Cause:** Failed to remove bd-specific content.

**Detection:**
```bash
grep -in 'daemon\|hook\|rpc' file.md
```

**Fix:** Remove these sections entirely (not transform—DELETE).

---

### 6. Incomplete Pattern Search

**Symptom:** Some bd references remain after "complete" migration.

**Cause:** bd references appear in unexpected places:
- Inline code: `` `bd` ``
- Code blocks inside examples
- Mapping tables
- P0 workflow sections
- Agent Mail examples

**Detection (comprehensive):**
```bash
grep -E '(br ready|br list|bd show|br create|bd update|bd close|bd sync|br dep|bd stats|bd-[0-9]|\`bd )' file.md
```

**Fix:** Search with ALL patterns, not just common ones.

---

## Verification Pitfalls

### 7. False Positive in Verification

**Symptom:** Verification passes but file still has issues.

**Cause:** Verification only checks specific patterns, misses edge cases.

**Example missed patterns:**
```markdown
Use bd for issue tracking    # No backticks, not caught
The bd tool is deprecated    # Prose reference, not caught
```

**Fix:** Add prose check:
```bash
grep -i '\bbd\b' file.md | grep -v '`bd' | grep -v 'br'
```

---

### 8. False Negative in Verification

**Symptom:** Verification fails but file is actually correct.

**Cause:** File legitimately has no beads section (verification expects br patterns).

**Detection:**
```bash
# Check if file actually has beads content
grep -q 'beads\|\.beads\|br ' file.md && echo "Has beads"
```

**Fix:** Skip verification for files without beads sections.

---

## Bulk Migration Pitfalls

### 9. Parallel Agent File Conflicts

**Symptom:** File corrupted or has duplicate content.

**Cause:** Two agents edited same file simultaneously.

**Prevention:**
- Strict batching—no file in multiple batches
- Sequential verification between batches

**Recovery:**
```bash
git checkout -- /path/to/corrupted/file.md
# Re-run migration for this file only
```

---

### 10. Batch Size Too Large

**Symptom:** Agent context overflow, incomplete migrations.

**Cause:** >15 files per batch exceeds practical context.

**Fix:** Max 10 files per subagent batch.

---

### 11. Not Verifying Between Batches

**Symptom:** Later batches build on broken earlier batches.

**Cause:** Proceeded without verification.

**Fix:** ALWAYS verify before next batch:
```bash
./scripts/verify-migration.sh /path/to/batch/*.md
```

---

## Quick Diagnostics

### Comprehensive Health Check

```bash
#!/usr/bin/env bash
file="$1"

echo "=== Checking: $file ==="

# Should be 0
echo -n "bd commands: "
grep -c '`bd ' "$file" 2>/dev/null || echo "0"

echo -n "bd sync: "
grep -c 'bd sync' "$file" 2>/dev/null || echo "0"

echo -n "bd-### IDs: "
grep -c 'bd-[0-9]' "$file" 2>/dev/null || echo "0"

# Should be > 0 if file has beads sections
echo -n "br sync --flush-only: "
grep -c 'br sync --flush-only' "$file" 2>/dev/null || echo "0"

echo -n "git add .beads/: "
grep -c 'git add .beads/' "$file" 2>/dev/null || echo "0"

echo -n "non-invasive note: "
grep -c 'non-invasive' "$file" 2>/dev/null || echo "0"

# Should be 0
echo -n "daemon refs: "
grep -ci 'daemon' "$file" 2>/dev/null || echo "0"

echo -n "hook refs: "
grep -ci '\bhook\b' "$file" 2>/dev/null || echo "0"
```

### One-Liner Status

```bash
# Quick pass/fail for file
grep -q '`bd ' file.md && echo "FAIL: bd refs remain" || echo "PASS: no bd refs"
```
