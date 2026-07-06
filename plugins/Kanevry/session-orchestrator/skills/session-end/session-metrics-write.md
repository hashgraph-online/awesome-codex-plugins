# Phase 3.7: Write Session Metrics

> Sub-file of the session-end skill. Executed as part of Phase 3 (Documentation Updates) when `persistence` is enabled.
> For the full session close-out flow, see `SKILL.md`.

### 3.7 Write Session Metrics

> Gate: Only run if `persistence` is enabled in Session Config.
>
> This step writes the session JSONL entry, verifies it, then optionally mirrors the session summary to the configured Obsidian vault via `scripts/vault-mirror.mjs`.

> **MANDATORY WRITE PATH (#400):** ALL session closes — including coord-direct sessions, housekeeping, express-path, and autopilot runs — MUST write the JSONL metrics entry exclusively via `node scripts/emit-session.mjs`. **Hand-composing JSON and appending it directly to `sessions.jsonl` is forbidden.** `emit-session.mjs` calls `validateSession` from `scripts/lib/session-schema.mjs` (the schema authority) before appending and stamps `schema_version: 1`. Entries that bypass this path skip validation and produce malformed records with missing required fields (`waves[]`, `agent_summary`) or unresolved legacy field names (`waves_completed`, `files_changed`, `planned_issues` at top-level instead of under `effectiveness`).
>
> Minimal invocation:
> ```bash
> printf '%s' "$METRICS_ENTRY" | node "$PLUGIN_ROOT/scripts/emit-session.mjs" --file .orchestrator/metrics/sessions.jsonl
> ```
> See step 2 below for the full invocation including exit-code handling.

1. Ensure `.orchestrator/metrics/` directory exists: `mkdir -p .orchestrator/metrics`

1-pre. **`memory_cleanup_at` always-stamp (#699)** — Before emitting the record, if `/memory-cleanup` ran THIS session in any mode (dry-run, apply-pending, OR healthy no-op), stamp `memory_cleanup_at = completed_at` on the record using `stampMemoryCleanup()` from `scripts/lib/memory-cleanup-stamp.mjs`:

   ```js
   import { stampMemoryCleanup } from '../../scripts/lib/memory-cleanup-stamp.mjs';

   // ranCleanup: true when /memory-cleanup ran this session (ANY outcome)
   metricsEntry = stampMemoryCleanup(metricsEntry, {
     ranCleanup: ranMemoryCleanupThisSession, // boolean
     completedAt: metricsEntry.completed_at,
   });
   ```

   **Contract:** A no-op run (MEMORY.md already healthy, no files mutated) is still a cleanup — `memory_cleanup_at` MUST be stamped. This advances `readDreamSignals` → `lastCleanupAt` in `auto-dream.mjs` so `shouldDispatchAutoDream` does not fire a false nudge. When `/memory-cleanup` did not run, omit the field entirely (do NOT set null). The helper is no-throw and pure — it returns the record unchanged on bad inputs.

   > **#701.2 DOC NOTE — `completed_at >= started_at` guard:** This invariant is enforced mechanically by `scripts/emit-session.mjs`. The writer applies `clampTimestampsMonotonic()` (from `scripts/lib/session-schema/timestamps.mjs`) before `validateSession()`, clamping any inversion of `completed_at < started_at` to `started_at` and recording forensics in `_clamped: true` / `_original_completed_at`. Previously-inverted entries (e.g. `main-2026-06-21-session-4`) are already corrected. **No per-session coordinator action is needed** — the writer enforces the invariant at write time. Do not add defensive clamping logic here; the canonical guard lives in `emit-session.mjs`.

1a. **Token Rollup (#644)** — before emitting the JSONL record, aggregate token usage from `subagents.jsonl` and merge the three token fields onto the in-memory `$METRICS_ENTRY` JSON object. The join key is the session's UUID (`session_id` / `parent_session_id` on subagents.jsonl — the UUID form, not the semantic slug).

   **Semantics:** `null` totals mean "no token data was captured for this session" — this is NOT the same as zero cost. Do NOT coerce null to 0 when displaying or summing across sessions.

   Example (coordinator pseudo-code — adapt to your shell/JS context):

   ```js
   // Available from scripts/lib/session-token-rollup.mjs
   import { rollupSessionTokens } from '../../scripts/lib/session-token-rollup.mjs';

   const rollup = rollupSessionTokens({ parentSessionId: SESSION_UUID });
   // rollup: { total_token_input, total_token_output, subagents_with_tokens, matched_records }
   // Merge into the record — all three fields are optional in schema v1 (additive).
   metricsEntry.total_token_input   = rollup.total_token_input;   // number | null
   metricsEntry.total_token_output  = rollup.total_token_output;  // number | null
   metricsEntry.subagents_with_tokens = rollup.subagents_with_tokens; // number (0 when no coverage)
   ```

   Or, from a bash context, call the rollup via a helper node invocation and `jq`-merge the three fields into `$METRICS_ENTRY` before step 2:

   ```bash
   ROLLUP_JSON=$(node -e "
     import('$(dirname "$0")/../scripts/lib/session-token-rollup.mjs').then(m => {
       const r = m.rollupSessionTokens({ parentSessionId: process.env.SESSION_UUID });
       process.stdout.write(JSON.stringify(r));
     });
   " 2>/dev/null) || ROLLUP_JSON='{}'

   # Merge token fields into METRICS_ENTRY (null for fields absent from rollup)
   METRICS_ENTRY=$(printf '%s' "$METRICS_ENTRY" | jq \
     --argjson r "${ROLLUP_JSON:-{}}" \
     '. + {
       total_token_input:    ($r.total_token_input // null),
       total_token_output:   ($r.total_token_output // null),
       subagents_with_tokens: ($r.subagents_with_tokens // 0)
     }')
   ```

   **If the rollup call fails** (e.g., `subagents.jsonl` absent, parse error), set all three fields to `null` / `0` and continue — the rollup is non-blocking. A session without token data still writes cleanly.

2. Append the prepared JSONL entry (from Phase 1.7, now including token fields from step 1a) via the validating writer `scripts/emit-session.mjs` (issue #249):
   ```bash
   printf '%s' "$METRICS_ENTRY" | node "$PLUGIN_ROOT/scripts/emit-session.mjs" --file .orchestrator/metrics/sessions.jsonl
   EMIT_EXIT=$?
   if [[ $EMIT_EXIT -eq 1 ]]; then
     echo "ERROR: session-end validation failed — entry rejected by scripts/emit-session.mjs. See stderr above. Session metrics NOT written." >&2
     exit 1
   elif [[ $EMIT_EXIT -ne 0 ]]; then
     echo "ERROR: scripts/emit-session.mjs failed with exit $EMIT_EXIT. Session metrics NOT written." >&2
     exit 1
   fi
   ```
   `scripts/emit-session.mjs` calls `validateSession` from `scripts/lib/session-schema.mjs` before appending, stamps `schema_version: 1` if absent, and uses `appendJsonl` (atomic for lines < PIPE_BUF). Exit 1 on validation error, exit 2 on I/O error — block session close in both cases so malformed metrics can never reach disk.

   **`autopilot_run_id` (additive, optional, #300):** when this session was launched by `/autopilot`, the wave-executor `sessionRunner` callback passes `args.autopilotRunId` from `runLoop`. session-end MUST persist that value as a top-level field on the JSONL record:

   ```json
   {"schema_version":1,"session_id":"…","autopilot_run_id":"main-2026-04-25-1432-autopilot",...}
   ```

   Manual sessions either omit the field or write `null` — both are treated identically per the v1 additive convention. Readers must NOT distinguish "missing" from "null" semantically. `validateSession` does not require this field; it passes through unknown keys unchanged.
3. The writer creates the file if it does not exist.
4. Verify: read back the last line to confirm valid JSON (sanity check; validation already ran):
   ```bash
   tail -1 .orchestrator/metrics/sessions.jsonl | jq . > /dev/null || {
     echo "ERROR: last sessions.jsonl line is not valid JSON — manual fix required" >&2; exit 1;
   }
   ```
5. **Vault Mirror** — mirror the session entry to the Obsidian vault (if configured):

   ```bash
   VM_ENABLED=$(echo "$CONFIG" | jq -r '."vault-integration".enabled // false')
   VM_MODE=$(echo "$CONFIG" | jq -r '."vault-integration".mode // "warn"')

   if [[ "$VM_ENABLED" == "true" && "$VM_MODE" != "off" ]]; then
     # Resolve vault directory: config field takes precedence, env var as fallback
     VM_DIR=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-dir" // empty')
     : "${VM_DIR:=$VAULT_DIR}"

     # Quality-gate thresholds (PRD F1.2). Defaults match
     # scripts/vault-mirror.mjs (400 chars / 0.5 confidence). The nested key
     # path `vault-mirror.quality.*` is owned by the I6 config parser; this
     # site is a read-only consumer.
     VM_QUALITY_NARRATIVE=$(echo "$CONFIG" | jq -r '."vault-mirror".quality."min-narrative-chars" // 400')
     VM_QUALITY_CONFIDENCE=$(echo "$CONFIG" | jq -r '."vault-mirror".quality."min-confidence" // 0.5')
     VM_VAULT_NAME=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-name" // empty')

     VM_OUTPUT=$(node "$PLUGIN_ROOT/scripts/vault-mirror.mjs" \
       --vault-dir "$VM_DIR" \
       --source .orchestrator/metrics/sessions.jsonl \
       --kind session \
       --session-id "$SESSION_ID" \
       ${VM_VAULT_NAME:+--vault-name "$VM_VAULT_NAME"} \
       --quality-min-narrative-chars "$VM_QUALITY_NARRATIVE" \
       --quality-min-confidence "$VM_QUALITY_CONFIDENCE" 2>&1)
     VM_EXIT=$?

     # Surface script output so user can see skipped-handwritten results
     if [[ -n "$VM_OUTPUT" ]]; then
       echo "$VM_OUTPUT"
     fi

     if [[ $VM_EXIT -ne 0 ]]; then
       if [[ "$VM_MODE" == "strict" ]]; then
         echo "ERROR: vault-mirror failed (exit $VM_EXIT) — session close blocked (vault-integration.mode=strict)"
         echo "Fix the vault mirror issue or set vault-integration.mode: warn to downgrade to a warning."
         exit 1
       else
         # mode: warn (default) — surface warning but do not block
         echo "WARNING: vault-mirror exited $VM_EXIT — session metrics were NOT mirrored to the vault. Set vault-integration.mode: strict to block on this error."
       fi
     else
       # Parse the destination path from the script's JSON output (one JSON line per action)
       VM_DEST=$(echo "$VM_OUTPUT" | jq -r 'select(.action == "created" or .action == "updated") | .path' 2>/dev/null | head -1)
       if [[ -n "$VM_DEST" ]]; then
         echo "Mirrored session summary to $VM_DEST"
       fi

       # Quality gate summary (PRD F1.2): count entries skipped because they
       # failed the quality filter, so the operator can tune thresholds.
       VM_QUALITY_SKIP=$(echo "$VM_OUTPUT" | jq -rc 'select(.action == "skipped-quality-low")' 2>/dev/null | wc -l | tr -d ' ')
       if [[ "${VM_QUALITY_SKIP:-0}" -gt 0 ]]; then
         echo "vault-mirror: ${VM_QUALITY_SKIP} entry/entries skipped by quality gate (set vault-mirror.quality.min-narrative-chars / min-confidence to tune)"
       fi
     fi

     # ── Durable Narrative Mirror (#675) ────────────────────────────────────
     # Sibling of the session-mirror above, gated on the SAME vault-integration
     # gate ($VM_ENABLED / $VM_MODE checked at the top of this block). Reads this
     # repo's `.claude/STATE.md`, extracts the DURABLE narrative — `## Wave History`,
     # `## Deviations`, `## What Not To Retry`, plus the mission-status rollup — and
     # idempotently writes a generator-owned per-repo file at
     # `<vault-dir>/01-projects/<repo-slug>/_session-narrative.md`, so a reviewer
     # or stand-in can read PER REPO what was done, what failed, and what not to
     # retry WITHOUT opening the repo.
     #
     # Idempotent + safe: NEVER touches `_overview.md` or any hand-authored file
     # (marker-guarded via `session-orchestrator-vault-status-narrative@1`). A
     # re-run with no STATE.md change returns `skipped-noop`; an existing
     # non-generator file returns `skipped-handwritten`; absent STATE.md returns
     # `skipped-no-statemd`. The helper ALSO self-no-ops (`skipped-vault-disabled`)
     # when vault-integration is off — this gate is defense-in-depth, not the sole
     # gate. Non-blocking: a failure surfaces a warning and never blocks close,
     # using the same strict/warn degradation idiom as the vault-mirror step above.
     NM_OUTPUT=$(node -e "
       import('$PLUGIN_ROOT/scripts/lib/vault-status/narrative-mirror.mjs').then(async (m) => {
         const r = await m.mirrorNarrative({ repoRoot: process.cwd() });
         process.stdout.write(JSON.stringify(r));
       }).catch((e) => { process.stderr.write(String(e && e.message || e)); process.exit(3); });
     " 2>&1)
     NM_EXIT=$?

     if [[ $NM_EXIT -ne 0 ]]; then
       if [[ "$VM_MODE" == "strict" ]]; then
         echo "ERROR: narrative-mirror failed (exit $NM_EXIT) — session close blocked (vault-integration.mode=strict): $NM_OUTPUT"
         echo "Fix the narrative mirror issue or set vault-integration.mode: warn to downgrade to a warning."
         exit 1
       else
         # mode: warn (default) — surface warning but do not block
         echo "WARNING: narrative-mirror exited $NM_EXIT — durable per-repo narrative was NOT mirrored to the vault. Set vault-integration.mode: strict to block on this error."
       fi
     else
       # Surface the JSON result so the operator can see skipped-* / written outcomes.
       NM_ACTION=$(echo "$NM_OUTPUT" | jq -r '.action // empty' 2>/dev/null)
       NM_PATH=$(echo "$NM_OUTPUT" | jq -r '.path // empty' 2>/dev/null)
       if [[ "$NM_ACTION" == "written" && -n "$NM_PATH" ]]; then
         echo "Mirrored durable session narrative to $NM_PATH"
       elif [[ -n "$NM_ACTION" ]]; then
         echo "narrative-mirror: $NM_ACTION${NM_PATH:+ ($NM_PATH)}"
       fi
     fi
   fi
   ```

   > **Repo name** is derived internally: `mirrorNarrative` defaults the per-repo slug + frontmatter `repo:` field to `path.basename(repoRoot)` when `repo` is omitted, so the call needs only `repoRoot: process.cwd()` — no shell-var plumbing. (Pass an explicit `repo:` only to override the derived basename.) The narrative mirror shares vault-dir resolution with `mirrorNarrative` itself (it reads Session Config internally), so no separate `--vault-dir` plumbing is needed here.

   **Behaviour matrix:**

   | `enabled` | `mode`  | Result |
   |-----------|---------|--------|
   | `false` or missing | any | Skip entirely — no-op, no output |
   | `true` | `off`   | Skip entirely — no-op, no output |
   | `true` | `warn`  | Run mirror; on failure surface a warning but do NOT block close |
   | `true` | `strict` | Run mirror; on failure block session close with an error message |

   > **Hand-written note protection:** `vault-mirror.mjs` checks for a `_generator: session-orchestrator-vault-mirror@1` marker before overwriting any existing file. When it skips an existing hand-written note it emits a JSON line `{"action":"skipped-handwritten","path":"<path>","kind":"<kind>","id":"<id>"}` — the step above surfaces this output so the user can see the result. Action names: `created`, `updated`, `skipped-noop`, `skipped-handwritten`, `skipped-collision-resolved`, `skipped-invalid` (entry failed required-field validation, or the mapper crashed rendering an otherwise-parseable record — the latter case carries `reason: "mapper-crash"`, #718), `skipped-quality-low` (entry failed quality gate — PRD F1.2; line carries a `reason` field).
