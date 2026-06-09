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
2. Append the prepared JSONL entry (from Phase 1.7) via the validating writer `scripts/emit-session.mjs` (issue #249):
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

     VM_OUTPUT=$(node "$PLUGIN_ROOT/scripts/vault-mirror.mjs" \
       --vault-dir "$VM_DIR" \
       --source .orchestrator/metrics/sessions.jsonl \
       --kind session \
       --session-id "$SESSION_ID" \
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
   fi
   ```

   **Behaviour matrix:**

   | `enabled` | `mode`  | Result |
   |-----------|---------|--------|
   | `false` or missing | any | Skip entirely — no-op, no output |
   | `true` | `off`   | Skip entirely — no-op, no output |
   | `true` | `warn`  | Run mirror; on failure surface a warning but do NOT block close |
   | `true` | `strict` | Run mirror; on failure block session close with an error message |

   > **Hand-written note protection:** `vault-mirror.mjs` checks for a `_generator: session-orchestrator-vault-mirror@1` marker before overwriting any existing file. When it skips an existing hand-written note it emits a JSON line `{"action":"skipped-handwritten","path":"<path>","kind":"<kind>","id":"<id>"}` — the step above surfaces this output so the user can see the result. Action names: `created`, `updated`, `skipped-noop`, `skipped-handwritten`, `skipped-collision-resolved`, `skipped-invalid` (entry failed required-field validation), `skipped-quality-low` (entry failed quality gate — PRD F1.2; line carries a `reason` field).
