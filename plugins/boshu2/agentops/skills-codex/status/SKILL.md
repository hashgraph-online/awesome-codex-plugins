---
name: status
description: "Show AgentOps project status."
---
# $status — Workflow Dashboard

> **Purpose:** Single-screen overview of your current state. What am I working on? What happened recently? What should I do next?

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

**CLI dependencies:** br, ao, gt — all optional. Shows what's available, skips what isn't.

---

## Quick Start

```bash
$status              # Full dashboard
$status --json       # Machine-readable JSON output
$status --recover    # Post-compaction recovery mode (absorbed $recover)
```

---

## Post-compaction recovery mode (absorbed `$recover`, 2026-07-07)

Fires for the retired `$recover` skill's triggers — "recover", "recover session
context", post-compaction re-orientation. Same gather as the dashboard plus the
continuation surfaces, in this order:

1. Run the full dashboard gather (Step 1 below).
2. Read the newest `.agents/handoff/*.md` (the write-side counterpart — see the
   handoff skill) and `.agents/rpi/execution-packet.json` if present.
3. Re-read `AGENTS.md` before resuming any claimed bead (two-correction rule
   applies after compaction).
4. Report: what was in flight, the exact next action, and any claimed-but-unfinished
   beads (`ao beads exec list --status in_progress`).

The old skill's deep-recovery walkthrough survives at
`references/recovery-playbook.md` (mirrored from the source skill).

---

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), ensure startup context
before gathering the dashboard:

```bash
ao codex ensure-start 2>/dev/null || true
```

`ao codex ensure-start` is the single startup guard for Codex skills. It records
startup once per thread and skips duplicate startup automatically. Leave
`ao codex ensure-stop` to dedicated closeout skills such as `$validate`,
`$post-mortem`, or `$handoff`.

---

## Execution Steps

### Step 1: Gather State (Parallel)

Run ALL of the following in parallel bash calls for speed:

**Call 1 — RPI + Ratchet + Task State:**
```bash
# Current ratchet phase
if [ -f .agents/ao/chain.jsonl ]; then
  tail -1 .agents/ao/chain.jsonl 2>/dev/null
else
  echo "NO_CHAIN"
fi

# Ratchet status via CLI
if command -v ao &>/dev/null; then
  ao ratchet status --json 2>/dev/null || echo "RATCHET_UNAVAILABLE"
  ao task-status --json 2>/dev/null || echo "TASK_STATUS_UNAVAILABLE"
fi
```

**Call 2 — Beads / Epic State:**
```bash
if ao beads exec ready --json >/dev/null 2>&1 && ao beads exec list --type epic --status open --json >/dev/null 2>&1; then
  echo "=== EPIC ==="
  ao beads exec list --type epic --status open 2>/dev/null | head -5
  echo "=== IN_PROGRESS ==="
  ao beads exec list --status in_progress 2>/dev/null | head -5
  echo "=== READY ==="
  ao beads exec ready 2>/dev/null | head -5
  echo "=== TOTAL ==="
  ao beads exec list 2>/dev/null | wc -l
else
  echo "AO_DEGRADED_OR_UNAVAILABLE"
fi
```

**Call 3 — Knowledge Flywheel:**
```bash
# Learnings count
echo "LEARNINGS=$(ls .agents/learnings/ 2>/dev/null | wc -l | tr -d ' ')"
echo "PATTERNS=$(ls .agents/patterns/ 2>/dev/null | wc -l | tr -d ' ')"
echo "PENDING=$(ls .agents/forge/ 2>/dev/null | wc -l | tr -d ' ')"

# Flywheel health + badge
if command -v ao &>/dev/null; then
  ao metrics flywheel status 2>/dev/null || echo "FLYWHEEL_UNAVAILABLE"
  ao badge 2>/dev/null || echo "BADGE_UNAVAILABLE"
fi
```

**Call 4 — Recent Activity + Git:**
```bash
# Recent sessions
if [ -d .agents/ao/sessions ]; then
  ls -t .agents/ao/sessions/*.md 2>/dev/null | head -3
else
  echo "NO_SESSIONS"
fi

# Recent council verdicts
ls -lt .agents/council/ 2>/dev/null | head -4

# Git state
echo "=== GIT ==="
git branch --show-current 2>/dev/null
git log --oneline -3 2>/dev/null
git status --short 2>/dev/null | head -5
```

**Call 5 — Inbox:**
```bash
if command -v gt &>/dev/null; then
  gt mail inbox 2>/dev/null | head -5
else
  echo "GT_UNAVAILABLE"
fi
```

**Call 6 — Session Quality Signals:**
```bash
if [ -f .agents/signals/session-quality.jsonl ]; then
  tail -10 .agents/signals/session-quality.jsonl
else
  echo "NO_SIGNALS"
fi
```

### Step 2: Render Dashboard

Assemble gathered data into this format. Use Unicode indicators for visual clarity:

- Pass/healthy: `[PASS]`
- Warning/partial: `[WARN]`
- Fail/missing: `[FAIL]`
- Progress: `[3/7]` with bar `███░░░░`

```
══════════════════════════════════════════════════
  Workflow Dashboard
══════════════════════════════════════════════════

RPI PROGRESS
  Phase: <current phase from chain.jsonl: research | plan | implement | validate | idle>
  Gate:  <last completed gate or "none">
  ─────────────────────────────────
  research ── plan ── implement ── validate
     <mark current position with arrow or highlight>

ACTIVE EPIC
  <epic title and ID, or "No active epic">
  Progress: <completed>/<total> issues  <progress bar>
  In Progress: <list in-progress issues, max 3>

READY TO WORK
  <top 3 unblocked issues from br ready>
  <or "No ready issues — create work with $plan">

RECENT VALIDATIONS
  <last 3 council reports with verdict>
  <format: date  verdict  target>
  <or "No recent validations">

KNOWLEDGE FLYWHEEL
  Learnings: <count>  Patterns: <count>  Pending: <count>
  Health: <flywheel status or "ao not installed">
  Badge: <ao badge output or omit if unavailable>

TASK MATURITY
  <ao task-status summary: active tasks with CASS maturity levels, or omit if unavailable>

RECENT SESSIONS
  <last 3 session summaries with dates>
  <or "No session history">

GIT STATE
  Branch: <current branch>
  Recent: <last 3 commits, one-line>
  Changes: <uncommitted file count or "clean">

INBOX
  <message count or "No messages" or "gt not installed">

SESSION QUALITY SIGNALS
  <last 10 entries from .agents/signals/session-quality.jsonl as table>
  | Timestamp | Signal | Detail | Session |
  |-----------|--------|--------|---------|
  <parsed from JSON lines: .timestamp, .signal, .detail, .session>
  <or "No quality signals recorded." if file missing or empty>

──────────────────────────────────────────────────
SUGGESTED NEXT ACTION
  <state-aware suggestion — see Step 3>
──────────────────────────────────────────────────

QUICK COMMANDS
  $research     Deep codebase exploration
  $plan         Decompose epic into issues
  $pre-mortem   Validate plan before coding
  $implement    Execute a single issue
  $crank        Autonomous epic execution
  $post-mortem  Full close-out and learnings
  $validate     Targeted code review
══════════════════════════════════════════════════
```

### Step 3: Suggest Next Action (State-Aware)

Evaluate state top-to-bottom. Use the FIRST matching condition:

| Priority | Condition | Suggestion |
|----------|-----------|------------|
| 1 | No ratchet chain exists | "Start with `quickstart` or `$research` to begin a workflow" |
| 2 | Research done, no plan | "Run `$plan` to decompose research into actionable issues" |
| 3 | Plan done, no pre-mortem | "Run `$pre-mortem` to validate the plan before coding" |
| 4 | Issues in-progress | "Continue working: `$implement <issue-id>` or `$crank` for autonomous execution" |
| 5 | Ready issues available | "Pick up next issue: `$implement <first-ready-id>`" |
| 6 | Uncommitted changes | "Review recent work: `$validate`" |
| 7 | Implementation done, no vibe | "Run `$validate` for final close-out" |
| 8 | Recent WARN/FAIL verdict | "Address findings in `<report-path>`, then re-run `$validate`" |
| 10 | Vibe passed, no post-mortem | "Run `$validate` to complete closeout and extract learnings" |
| 11 | Pending knowledge items | "Promote learnings: `ao pool list --status pending --json`, then `ao pool stage <id>` and `ao pool promote <id>`" |
| 12 | Clean state, nothing pending | "All clear. Start with `$research` or `$plan` to find new work" |

### Step 4: JSON Output (--json flag)

If the user passed `--json`, output all dashboard data as structured JSON instead of the visual dashboard:

```json
{
  "rpi": {
    "phase": "implement",
    "last_gate": "plan",
    "chain_entries": 3
  },
  "epic": {
    "id": "ag-042",
    "title": "Epic title",
    "progress": { "completed": 3, "total": 7, "in_progress": ["ag-042.2"] }
  },
  "ready_issues": ["ag-042.4", "ag-042.5"],
  "validations": [
    { "date": "2026-02-09", "verdict": "PASS", "target": "src/auth/" }
  ],
  "flywheel": {
    "learnings": 12,
    "patterns": 5,
    "pending": 2,
    "health": "healthy"
  },
  "sessions": [
    { "date": "2026-02-09", "file": "session-abc.md" }
  ],
  "git": {
    "branch": "main",
    "uncommitted_count": 3,
    "recent_commits": ["abc1234 fix: thing", "def5678 feat: other"]
  },
  "inbox": { "count": 0 },
  "session_quality_signals": [
    { "timestamp": "2026-03-31T14:22:00Z", "signal": "drift", "detail": "3 corrections in 5min", "session": "abc123" }
  ],
  "suggestion": {
    "priority": 5,
    "message": "Continue working: $implement ag-042.2"
  }
}
```

Render this with a single code block. No visual dashboard when `--json` is active.

---

## Examples

### Checking Status Mid-Epic

**User says:** `$status`

**What happens:**
1. Agent runs 5 parallel bash calls to gather all state
2. Agent reads ratchet chain showing "implement" phase
3. Agent queries beads showing epic ag-042 with 3/7 issues completed
4. Agent finds 2 in-progress issues and 4 ready issues
5. Agent lists recent council verdict: PASS on src/auth/
6. Agent checks flywheel showing 12 learnings, 5 patterns, 2 pending
7. Agent renders dashboard with progress bars and suggests: "Continue working: $implement ag-042.2"

**Result:** Full single-screen dashboard showing mid-epic progress with actionable next step.

### Status in Clean State

**User says:** `$status`

**What happens:**
1. Agent gathers all state in parallel
2. Agent finds no ratchet chain exists (.agents/ao/chain.jsonl missing)
3. Agent finds no open epics or in-progress issues
4. Agent shows clean git state, recent commits only
5. Agent finds no recent validations
6. Agent suggests: "All clear. Start with $research or $plan to find new work"

**Result:** Dashboard confirms clean slate, points user to workflow entry points.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Shows "AO_DEGRADED_OR_UNAVAILABLE" or "AO_UNAVAILABLE" | `ao` CLI not installed or not in PATH | Install `ao` (it resolves the bead tracker — br/beads_rust — via `ao beads exec`). Skill gracefully degrades by showing available state only. |
| Ratchet phase shows stale data | Old chain.jsonl not cleaned up | Check timestamp of `.agents/ao/chain.jsonl`. If stale, delete it or run `$validate` to complete cycle and reset state. |
| Suggested action doesn't match intent | State-aware rules didn't capture edge case | Review priority table in Step 3. May need to refine conditions. Use `--json` to inspect raw state and debug rule matching. |
| JSON output malformed | Parallel bash calls returned unexpected format | Check each bash call individually. Ensure jq parsing works on actual data. Validate JSON structure with `jq .` before returning to user. |

## Local Resources

### scripts/

- `scripts/validate.sh`
