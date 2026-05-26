# STATE.md Ownership Contract

> Defines who can read and write `<state-dir>/STATE.md` and under what conditions.
> Referenced by: wave-executor, session-end, session-start, evolve.

## Schema

```yaml
---
schema-version: 1
session-type: feature|deep|housekeeping|none
branch: <current branch>
issues: [<issue numbers>]
started_at: <ISO 8601 with timezone>
status: active|paused|completed|idle
current-wave: <N>
total-waves: <N>
# Optional fields (schema-version 1, additive for backward-compat):
updated: <ISO 8601 UTC>      # last write timestamp, touched by any writer
session: <session-id>        # <branch>-<YYYY-MM-DD>-<HHmm>, set Pre-Wave 1b
session-start-ref: <sha>     # git ref at session start
---
```

### Required vs. optional fields

- `schema-version`, `session-type`, `branch`, `issues`, `started_at`, `status`, `current-wave`, `total-waves` — **required** in every session-owned STATE.md.
- `updated`, `session`, `session-start-ref` — **optional**. Added by #184. STATE.md files without these fields remain valid and should be treated as `updated: null` / `session: null`. Writers SHOULD populate these fields but readers MUST tolerate their absence.

The `session-type: none` + `status: idle` combination is used only for bootstrap-scaffolded placeholder files (no active session).

### Body Sections

| Section | Purpose | Updated by |
|---------|---------|------------|
| `## Current Wave` | Next wave to execute | wave-executor (post-wave) |
| `## Wave History` | Completed wave records | wave-executor (post-wave) |
| `## Deviations` | Plan adaptation log | wave-executor (step 3) |

Wave History lines MAY include a `→ issue #NNN` suffix (or `→ existing #NNN` when a duplicate was detected) for SPIRAL/FAILED agents, linking to the auto-created carryover issue (#261). This is optional and backward-compatible; readers that do not recognize the notation can skip it. Session-end Phase 1.6 uses the presence of this suffix to decide whether to retro-file a carryover as a fallback safety net.

## Ownership Model

| Skill | Access | Operations |
|-------|--------|------------|
| **wave-executor** | Read + Write (owner) | Creates STATE.md (Pre-Wave 1b), updates after each wave (current-wave, Wave History, Deviations) |
| **session-end** | Read + Status-only write | Reads for metrics extraction (Phase 1.7), sets `status: completed` (Phase 3.4). Exception: only field modified is `status` in frontmatter. |
| **session-start** | Read + conditional reset | Reads for continuity checks (Phase 1.5): inspects `status` field to detect crashed/paused sessions. May reset STATE.md to idle at the boundary between a completed session and a new session — only when prior `status: completed`. The reset clears `current-wave` (→ 0), sets `status: idle`, demotes `## Wave History` into `## Previous Session`, and empties `## Deviations`. Never resets on `active` or `paused` (those paths are user-interactive). |
| **evolve** | Read-only | Reads `## Deviations` section for deviation pattern extraction (Step 2.2, pattern 5) |

## Guards

### Branch Validation

Before reading STATE.md, verify the `branch` field matches the current branch:

```bash
STATE_BRANCH=$(grep '^branch:' <state-dir>/STATE.md | sed 's/branch: *//')
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$STATE_BRANCH" != "$CURRENT_BRANCH" ]]; then
  # STATE.md belongs to a different branch — treat as stale
  echo "⚠ STATE.md is from branch '$STATE_BRANCH' but current branch is '$CURRENT_BRANCH'. Ignoring."
fi
```

### Schema Version

The `schema-version` field enables future migration. Current version: `1`. If a skill reads a STATE.md with an unrecognized schema-version, it should warn and proceed with best-effort parsing rather than failing.

## Concurrency

STATE.md is NOT safe for concurrent access. Only one session should be active per branch at a time. If session-start detects `status: active`, it prompts the user to resume or start fresh (which overwrites the stale STATE.md).

- **Discovery grep-verification** — distributional claims in W1 outputs (e.g., "N of M callers", "100% adopt pattern X") MUST quote the executed grep + file scope + count. See [`../../.claude/rules/parallel-sessions.md`](../../.claude/rules/parallel-sessions.md) § PSA-006.
