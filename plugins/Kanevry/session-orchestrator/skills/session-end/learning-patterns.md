# Phases 3.5a + 3.6: Learning Extraction and Memory Cleanup

> Sub-file of the session-end skill. Executed as part of Phase 3 (Documentation Updates) when `persistence` is enabled.
> For the full session close-out flow, see `SKILL.md`.

### 3.5a Learning Extraction

> Gate: Only run if `persistence` is enabled in Session Config.

Analyze the completed session to extract reusable learnings for future sessions.

**What to extract:**
- **Fragile files**: use `git log --name-only --format="" $SESSION_START_REF..HEAD | sort | uniq -c | sort -rn | head -10` to find files changed most frequently across commits this session. Files appearing in 3+ commits are candidates for fragile-file learnings. Cross-reference with `<state-dir>/STATE.md` Wave History to correlate with specific waves.
- **Effective sizing**: actual agent count vs. planned — what worked for this complexity level
- **Recurring issues**: same issue type appearing across waves (e.g., type errors, missing imports)
- **Scope guidance**: was the scope too large/small? How many issues fit comfortably in one session?
- **Deviation patterns**: read the `## Deviations` section from `<state-dir>/STATE.md` — were there plan adaptations? What triggered them? Extract as `deviation-pattern` type if a pattern emerges across sessions (e.g., "scope expansion during Impl-Core is common for this project")

**Learning format** (append each as one JSONL line to `.orchestrator/metrics/learnings.jsonl`):
```json
{
  "schema_version": 1,
  "id": "<uuid-v4>",
  "type": "fragile-file|effective-sizing|recurring-issue|scope-guidance|deviation-pattern|stagnation-class-frequency",
  "subject": "<what the learning is about>",
  "insight": "<the actionable insight>",
  "evidence": "<what happened this session>",
  "confidence": 0.5,
  "source_session": "<session_id>",
  "created_at": "<ISO 8601>",
  "expires_at": "<ISO 8601 + learning-expiry-days (default: 30)>"
}
```

**Schema versioning** (`schema_version`, introduced 2026-04):
- All new records MUST carry `schema_version: 1`. `scripts/lib/learnings.mjs` auto-stamps missing values on append/rewrite so callers can omit the field safely.
- Records without `schema_version` are treated as `schema_version: 0` (pre-versioning legacy). They are read and validated successfully for backward compat, but the reader emits a one-line WARN to stderr flagging the missing tag.
- Both `schema_version: 0` and `schema_version: 1` pass `validateLearning`. Any other value is rejected.

**Confidence updates for existing learnings:**
Before writing new learnings, read `.orchestrator/metrics/learnings.jsonl` and check for existing entries with the same `type` + `subject` (exact string match on both fields):
- If this session **confirms** an existing learning: note the update — increment `confidence` by +0.15 (cap at 1.0) and reset `expires_at` to current date + `learning-expiry-days` (default: 30)
- If this session **contradicts** an existing learning: note the update — decrement `confidence` by -0.2
- If no existing match: note as a new learning with confidence 0.5

**File I/O strategy:** Track all updates in memory during extraction. Do NOT modify `learnings.jsonl` here — Phase 3.6 handles the actual file write. Pass these data structures to Phase 3.6:
- `confidence_updates`: list of `{id: "<existing_learning_id>", operation: "confirm"|"contradict"}`
- `new_learnings`: list of complete learning objects (all JSONL fields per the format above)

> ⚠️ **NEVER point a validating writer at the live store to "test" it.** `rewriteLearnings` performs an atomic, destructive replace — validating the input does NOT protect the file that is being overwritten. On 2026-07-02 a coordinator probe ran the validator against the live `learnings.jsonl` and the subsequent atomic rewrite replaced 107 entries with 3; because the store is gitignored there was no VCS restore (recovered only via the `.bak` sidecar + vault-mirror). To probe a live store safely, use the dry-run path — `rewriteLearnings(file, entries, { dryRun: true })` validates the batch and returns the validated entries but writes NOTHING (no rewrite, no `.bak`). Since #721, a real `rewriteLearnings` also snapshots the current file to `${file}.bak-<ISO>` (keep 3) before the rename, so an accidental overwrite is recoverable — but the dry-run path is still the correct tool for a probe.

**Subject matching:** Match on exact `type` + `subject` string equality. For `fragile-file`, `subject` is the file path. For other types, use a short canonical identifier (e.g., `type-errors-in-api`, `scope-too-large`, `missing-imports`).

### 3.6 Memory Cleanup & Learnings Write

> Gate: Only run if `persistence` is enabled in Session Config.

1. Count session memory files matching `session-*.md` in the memory directory
2. If count exceeds `memory-cleanup-threshold` (default: 5), suggest:
   "You have [N] session memory files. Consider running `/memory-cleanup` to consolidate."
3. This is a suggestion only — not blocking
4. **Write learnings** to `.orchestrator/metrics/learnings.jsonl` (if file exists or new learnings were extracted):
   a. Read all existing lines from `learnings.jsonl` (if exists)
   b. Apply confidence updates from Phase 3.5a (confirmed: +0.15 capped at 1.0 AND reset `expires_at` to current date + `learning-expiry-days` (default: 30); contradicted: -0.2)
   c. Append new learnings from Phase 3.5a (those with no existing match)
   d. **Passive decay (#89)** — for every existing learning NOT touched this session (i.e., not in the set of learnings confirmed or contradicted in Phase 3.5a, and not newly appended in step c), subtract `learning-decay-rate` (from Session Config, default `0.05`) from its `confidence`. Clamp to 0.0 (do not produce negative values). The prune step in `e` will remove any entry that fell to `confidence <= 0.0`. Decay does NOT reset `expires_at` — let decayed entries continue to age naturally. If `learning-decay-rate` is `0.0`, skip this step entirely (opt-out).

      | Sessions since last touch | Confidence (starting 0.5, decay 0.05) | Status |
      |---|---|---|
      | 0 | 0.50 | active |
      | 5 | 0.25 | active |
      | 9 | 0.05 | active |
      | 10 | 0.00 | pruned next write |

   e. Prune: remove entries where `expires_at` < current date OR `confidence` <= 0.0
   f. Consolidate duplicates (same `type` + `subject`): keep the one with highest confidence
   g. Write the entire result back to `learnings.jsonl` (atomic rewrite with `>`, not append with `>>`)
   h. If no existing file and no new learnings: skip
