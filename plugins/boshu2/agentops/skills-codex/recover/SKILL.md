---
name: recover
description: "Recover blocked or failed work."
---
# $recover — Context Recovery After Compaction

> **Purpose:** Help you get back up to speed after context compaction. Detects in-progress work (RPI runs, evolve cycles), loads relevant knowledge, summarizes what you were doing and what's next, and prefers the explicit Codex hookless lifecycle path when applicable.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

**CLI dependencies:** gt, ao, br — all optional. Shows what's available, skips what isn't.

---

## Quick Start

```bash
$recover              # Full recovery dashboard
$recover --json       # Machine-readable JSON output
ao codex status       # Codex hookless lifecycle health
ao codex ensure-start # Rebuild startup context explicitly in Codex
```

---

## Execution Steps

### Step 1: Detect In-Progress Sessions (Parallel)

Run ALL of the following in parallel bash calls:

**Call 1 — RPI Phased State:**
```bash
if [ -f .agents/rpi/phased-state.json ]; then
  echo "=== RPI_STATE ==="
  cat .agents/rpi/phased-state.json
else
  echo "RPI_STATE=NONE"
fi
```

**Call 2 — Evolve Cycle History:**
```bash
if [ -f .agents/evolve/cycle-history.jsonl ]; then
  echo "=== EVOLVE_STATE ==="
  tail -3 .agents/evolve/cycle-history.jsonl
else
  echo "EVOLVE_STATE=NONE"
fi
```

**Call 3 — Git Recent Changes:**
```bash
echo "=== GIT_STATUS ==="
git status --short

echo "=== GIT_LOG ==="
git log --oneline -5

echo "=== GIT_BRANCH ==="
git branch --show-current
```

**Call 4 — Work Queue State:**
```bash
if br ready --json >/dev/null 2>&1 && br list --type epic --status open --json >/dev/null 2>&1; then
  echo "=== IN_PROGRESS ==="
  br list --status in_progress 2>/dev/null | head -3
  echo "=== READY ==="
  br ready 2>/dev/null | head -3
else
  echo "BR_DEGRADED_OR_UNAVAILABLE"
fi
```

**Call 5 — Knowledge and Messages:**
```bash
# Knowledge artifacts
echo "=== KNOWLEDGE_COUNT ==="
echo "Learnings=$(ls .agents/learnings/ 2>/dev/null | wc -l | tr -d ' ')"
echo "Patterns=$(ls .agents/patterns/ 2>/dev/null | wc -l | tr -d ' ')"

# Inbox if gt available
if command -v gt &>/dev/null; then
  echo "=== MESSAGES ==="
  gt mail inbox 2>/dev/null | head -3
else
  echo "GT_UNAVAILABLE"
fi
```

**Call 6 — Codex Lifecycle (if available):**
```bash
if command -v ao &>/dev/null; then
  echo "=== CODEX_STATUS ==="
  ao codex status --json 2>/dev/null || echo "CODEX_STATUS=UNAVAILABLE"
else
  echo "AO_UNAVAILABLE"
fi
```

### Step 2: Load Context from Knowledge Base

If RPI state detected, run:
```bash
if command -v ao &>/dev/null; then
  ao lookup --query "rpi recovery context" --limit 5 2>/dev/null || true
fi
```

**Apply retrieved knowledge:** If learnings are returned, check each for applicability to the recovery context. Cite applicable learnings by filename and record: `ao metrics cite "<path>" --type applied 2>/dev/null || true`

If Codex hookless mode is detected, also ensure startup context once for the current thread:

```bash
ao codex ensure-start 2>/dev/null || true
```

### Step 3: Parse and Summarize Session State

Extract from collected data:

1. **RPI Detection:** If `.agents/rpi/phased-state.json` exists:
   - Extract `goal`, `epic_id`, `phase`, `cycle`, `started_at`
   - Map phase number to phase name (1=research, 2=plan, 3=implement, 4=validate)
   - Show elapsed time since started_at

2. **Evolve Detection:** If `.agents/evolve/cycle-history.jsonl` exists:
   - Read last entry for most recent cycle
   - Extract `goals_fixed`, `result`, `timestamp`
   - Show latest cycle summary

3. **Recent Work:** From git log:
   - Last 3 commits (extracted in Call 3)
   - Uncommitted changes count

4. **Pending Work:** From beads:
   - In-progress issues (up to 3)
   - Ready issues count

5. **Knowledge State:**
   - Total learnings and patterns available
   - Unread messages count if gt available

### Step 4: Render Recovery Dashboard

Assemble gathered data into this format:

```
══════════════════════════════════════════════════════════════
  Context Recovery Dashboard
══════════════════════════════════════════════════════════════

IN-PROGRESS RPI RUN
  Epic: <epic_id>
  Goal: <first 80 chars of goal>
  Phase: <phase name: research | plan | implement | validate>
  Cycle: <cycle #>
  Started: <time ago (e.g., "2 hours ago")>
  Status: <PHASE_START | IN_PROGRESS | READY_FOR_GATE | ...>

  ─ Next Step: <state-aware suggestion from Step 5>

OR

RECENT EVOLVE CYCLE (IF NO RPI)
  Cycle: <cycle #>
  Latest Goal: <goal_id or summary>
  Result: <result>
  Items Completed: <count or "—">
  Timestamp: <time ago>

  ─ Next Step: <state-aware suggestion from Step 5>

OR

[NO ACTIVE SESSION]
  No RPI run or evolve cycle in progress.
  Last activity: <time of last commit or "unknown">

IN-PROGRESS WORK
  <list up to 3 in-progress issues with IDs>
  <or "No in-progress work">

READY TO WORK
  <count of ready issues>
  <or "No ready issues">

RECENT COMMITS
  <last 3 commits>

PENDING CHANGES
  <uncommitted file count or "clean">

KNOWLEDGE AVAILABLE
  Learnings: <count>  Patterns: <count>

INBOX
  <message count or "No messages" or "gt not installed">

──────────────────────────────────────────────────────────────
SUGGESTED NEXT ACTION
  <state-aware command from Step 5>
──────────────────────────────────────────────────────────────

QUICK COMMANDS
  $status       Current workflow dashboard
  $research     Deep codebase exploration
  $plan         Decompose work into issues
  $implement    Execute a single issue
  $crank        Autonomous epic execution
  $validate   Full close-out and learnings
══════════════════════════════════════════════════════════════
```

### Step 5: Suggest Next Action (State-Aware)

Evaluate context top-to-bottom. Use the FIRST matching condition:

| Priority | Condition | Suggestion |
|----------|-----------|------------|
| 1 | RPI run in-progress + phase=research | "Continue research: `$research` or `$plan` if ready" |
| 2 | RPI run in-progress + phase=plan | "Review plan: `$pre-mortem` to validate before coding" |
| 3 | RPI run in-progress + phase=implement | "Resume implementation: `$implement <next-issue-id>`" |
| 4 | RPI run in-progress + phase=validate | "Complete cycle: `$validate` to extract learnings and close out" |
| 5 | Evolve cycle in-progress | "Continue autonomous improvements: `$evolve --resume`" |
| 6 | In-progress issues exist | "Continue work: `$implement <issue-id>`" |
| 8 | Ready issues available | "Pick next issue: `$implement <first-ready-id>`" |
| 9 | Uncommitted changes | "Review recent work: `$validate`" |
| 10 | Clean state, nothing pending | "Session recovered. Start with `$status` to plan next work" |

### Step 6: JSON Output (--json flag)

If the user passed `--json`, output all recovery data as structured JSON:

```json
{
  "session_type": "rpi|evolve|none",
  "rpi": {
    "epic_id": "ag-l2pu",
    "goal": "Implement...",
    "phase": 2,
    "phase_name": "plan",
    "cycle": 1,
    "started_at": "2026-02-15T14:33:36-05:00",
    "elapsed_minutes": 120
  },
  "evolve": {
    "cycle": 3,
    "result": "improved",
    "goals_fixed": ["goal1", "goal2"],
    "timestamp": "2026-02-15T22:00:00-05:00"
  },
  "work_state": {
    "in_progress_count": 3,
    "in_progress_issues": ["ag-042.1", "ag-042.2"],
    "ready_count": 5,
    "uncommitted_changes": 2
  },
  "git": {
    "branch": "main",
    "recent_commits": [
      "7de51c8 feat: wave 2 — structural assertions",
      "25004f8 fix: replace per-wave vibe gate"
    ]
  },
  "knowledge": {
    "learnings_count": 12,
    "patterns_count": 5
  },
  "inbox": {
    "unread_count": 0
  },
  "suggestion": {
    "priority": 4,
    "message": "Resume implementation: $implement ag-042.1"
  }
}
```

Render this with a single code block. No visual dashboard when `--json` is active.

---

## Examples

### Recovery After Compaction Mid-RPI

**User says:** `$recover`

**What happens:**
1. Agent runs 5 parallel bash calls to gather state
2. Agent detects RPI run in phased-state.json (phase=2, epic ag-l2pu)
3. Agent runs `ao lookup --query "rpi recovery context"` to load relevant knowledge
4. Agent shows goal, current phase (plan), cycle 1, started 2 hours ago
5. Agent lists 2 in-progress issues and 3 ready issues
6. Agent shows clean git state, recent commit
7. Agent suggests: "Review plan: `$pre-mortem` to validate before coding"

**Result:** Dashboard confirms in-progress RPI session, loads context, suggests next step.

### Recovery After Compaction With Evolve Cycle

**User says:** `$recover`

**What happens:**
1. Agent gathers state in parallel
2. Agent finds no RPI run
3. Agent detects evolve cycle (most recent: cycle 3, result "improved", goals_fixed=["goal1", "goal2"])
4. Agent shows timestamp (1 hour ago), items_completed (8)
5. Agent loads knowledge with `ao lookup --query "evolve cycle recovery"`
6. Agent suggests: "Continue autonomous improvements: `$evolve --resume`"

**Result:** Dashboard confirms evolve cycle, shows progress, offers resume command.

### Recovery in Clean State (No Active Session)

**User says:** `$recover`

**What happens:**
1. Agent gathers state in parallel
2. Agent finds no RPI run, no evolve cycle
3. Agent shows last 3 commits only
4. Agent finds no in-progress work, no ready issues
5. Agent shows 12 learnings available from knowledge base
6. Agent suggests: "Session recovered. Start with `$status` to plan next work"

**Result:** Dashboard confirms clean state, points user to entry points.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Shows "BR_DEGRADED_OR_UNAVAILABLE" or "GT_UNAVAILABLE" | CLI tools not installed or not in PATH | Install or expose `br` (beads_rust) or `gt`. Skill gracefully degrades by showing available state only. |
| RPI state shows wrong phase | Stale phased-state.json not updated | Check timestamp of `.agents/rpi/phased-state.json`. If stale, it may be from a previous run. Run `$status` to verify current phase. |
| Evolve history shows wrong cycle | Old cycle-history.jsonl entries not pruned | Tail -3 shows most recent entries. Check all entries with `tail -20 .agents/evolve/cycle-history.jsonl`. |
| Knowledge injection fails silently | ao CLI not installed or no knowledge artifacts | Ensure ao installed: `brew install ao`. If no learnings exist, run `$validate` to seed the knowledge base. |
| Suggested action doesn't match context | State-aware rules didn't capture edge case | Use `--json` to inspect raw state and verify which condition matched. Review priority table in Step 5. |
| JSON output malformed | Parallel bash calls returned unexpected format | Check each bash call individually. Ensure jq parsing works on actual data. Validate JSON structure before returning to user. |

## Local Resources

### scripts/

- `scripts/validate.sh`
