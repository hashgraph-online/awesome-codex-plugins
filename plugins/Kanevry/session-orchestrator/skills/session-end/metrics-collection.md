# Phase 1.7: Metrics Collection

> Sub-file of the session-end skill. Executed as part of Phase 1 when `persistence` is enabled.
> For the full session close-out flow, see `SKILL.md`.

### 1.7 Metrics Collection

> Gate: Only run if `persistence` is enabled in Session Config.

Finalize session metrics by reading the wave data accumulated during execution:

1. Read `<state-dir>/STATE.md` Wave History to extract per-wave data: agent counts, statuses, files changed

> **Graceful degradation:** If STATE.md is missing expected fields (no Wave History, missing frontmatter keys, malformed YAML), degrade gracefully: report what is available, skip metrics fields that cannot be parsed. Do NOT fail the session close because STATE.md is incomplete — a crashed session may leave partial STATE.md behind.

2. Compute session totals:
   - `total_duration_seconds`: from `started_at` to now (ISO 8601 diff)
   - `total_waves`: count of completed waves
   - `total_agents`: sum of agents across all waves
   - `total_files_changed`: unique files changed across entire session (from `git diff --stat`)
   - `agent_summary`: `{complete: N, partial: N, failed: N, spiral: N}`
3. Read `.orchestrator/metrics/events.jsonl` **once** and build both event aggregates in a single pass. If the file does not exist, treat both aggregates as zero events (omit both fields per the rules below) — do NOT fail the session close.

   Filter all lines where `session == <session_id>`, then partition by `event` value:

   ```bash
   jq -s --arg sid "$SESSION_ID" '
     [.[] | select(.session == $sid)]
     | {
         stagnation: [.[] | select(.event == "stagnation_detected")],
         grounding:  [.[] | select(.event == "orchestrator.grounding.injected")]
       }
   ' .orchestrator/metrics/events.jsonl
   ```

   From the `stagnation` array, aggregate into `stagnation_events`:
   - `total`: count of entries in the array
   - `by_pattern`: count by `pattern` value (omit zero-valued keys)
   - `by_error_class`: count by `error_class` value (omit zero-valued keys; omit entire sub-object if all entries lack `error_class` — only `error-echo` records carry one)
   - `by_source`: count by `source` value — `coordinator` (post-wave review) vs `tail` (the `wave-transcript-tail` monitor, #1114). Same rule: omit zero-valued keys; omit the entire sub-object when no entry carries `source` (pre-#1114 records do not).
   - `files`: unique list of non-null `file` values (deduplicated)
   - **Omit the entire `stagnation_events` field if `total == 0`** (keeps historical entries clean).

   From the `grounding` array, aggregate into `grounding_injections`:
   - `count`: total number of entries in the array
   - `files`: deduplicated list of unique file paths from the entries (sort alphabetically)
   - `total_lines`: sum of `lines` field across all entries
   - **Omit the entire `grounding_injections` field if `count == 0`** (matches stagnation_events pattern to keep historical entries clean).

   > **Per-category zero-match rule:** If the `stagnation` array is empty but the `grounding` array is non-empty (or vice versa), omit only the zero-match field — the other field is still populated normally. The single read handles both cases; no second file read is needed.
4. Prepare the JSONL entry (written in Phase 3.7) by **constructing it programmatically** — DO NOT manually hand-compose ISO timestamp strings. The `completed_at` value MUST come from `new Date().toISOString()` to prevent issue #540-class corruption (e.g., `.3NZ` malformed-fraction inputs that bypass `Date.parse`-only validators). The validator at `scripts/lib/session-schema/validator.mjs` rejects any timestamp that does not match the canonical `YYYY-MM-DDTHH:MM:SS[.SSS]Z` regex.

   Use this snippet pattern (adapt the field values from the session's in-memory state, but keep `new Date().toISOString()` for `completed_at` literally):

   ```bash
   # Issue #540: completed_at is constructed programmatically — DO NOT manually
   # edit the ISO timestamp string. Use the snippet as-is to prevent .3NZ-class
   # corruption.
   METRICS_ENTRY=$(node --input-type=module -e "
   const entry = {
     session_id: '<branch>-<YYYY-MM-DD>-<HHmm>',
     session_type: '<type>',
     platform: '<claude|codex>',
     started_at: '<ISO 8601 from STATE.md frontmatter started_at — already canonical>',
     completed_at: new Date().toISOString(),  // canonical YYYY-MM-DDTHH:MM:SS.SSSZ
     duration_seconds: <N>,
     total_waves: <N>,
     total_agents: <N>,
     total_files_changed: <N>,
     agent_summary: {complete: <N>, partial: <N>, failed: <N>, spiral: <N>},
     waves: [/* {wave, role, agent_count, files_changed, quality, agent_count_planned?, agent_count_started?, agent_count_completed?, planned_files_count?, over_delivery_ratio?} */],
     // effectiveness is CONSTRUCTED EXPLICITLY (#773) — NOT left as an optional
     // field for the coordinator to remember. Leaving it optional is exactly how
     // the carryover=0 blind spot recurred (41/41 records read carryover:0).
     // `carryover` = the Phase 1.65 gate carry-list length (see counting rules
     // below), NOT the raw Phase 1.2+1.3 candidate count.
     effectiveness: {
       planned_issues: <N>,
       completed: <N>,
       carryover: <N>,   // = Phase 1.65 gate carry-list length (see rules below)
       emergent: <N>,
       completion_rate: <0.0-1.0>,
       // override_ratio: <0.0-1.0>,  // OPTIONAL (#730/H5) — add ONLY when Phase 2.6 ran; OMIT otherwise (absent = "not measured")
     },
     // Handover-gate open-question telemetry (#773) — top-level, additive,
     // non-negative integers. OMIT (do not write 0) when the gate did not run an
     // interactive triage (fail-open skip / headless / fast-path): absent = "not
     // measured", 0 = "measured zero".
     open_questions_asked: <N>,      // surfaced in Phase 1.65 AUQ Call 2
     open_questions_answered: <N>,   // operator answered
     open_questions_deferred: <N>,   // left `- [ ]`, roundtripped to next session
     // Other optional fields below — populate per the Conditional Fields rules at
     // the bottom of this file; OMIT (do not write null) when the gating
     // condition is not met.
   };
   process.stdout.write(JSON.stringify(entry));
   ")
   ```

   **Canonical JSONL schema** (for field reference — populated by the snippet above):
   ```json
   {
     "session_id": "<branch>-<YYYY-MM-DD>-<HHmm>",
     "session_type": "<type>",
     "platform": "<claude|codex>",
     "started_at": "<canonical ISO 8601 from STATE.md>",
     "completed_at": "<canonical ISO 8601 from new Date().toISOString()>",
     "duration_seconds": N,
     "total_waves": N,
     "total_agents": N,
     "total_files_changed": N,
     "agent_summary": {"complete": N, "partial": N, "failed": N, "spiral": N},
     "waves": [
       {"wave": 1, "role": "Discovery", "agent_count": N, "files_changed": N, "quality": "pass|fail|skip", "agent_count_planned": N, "agent_count_started": N, "agent_count_completed": N, "planned_files_count": N, "over_delivery_ratio": 0.0},
       ...
     ],
     "discovery_stats": {
       "probes_run": N,
       "findings_raw": N,
       "findings_verified": N,
       "false_positives": N,
       "user_dismissed": N,
       "issues_created": N,
       "by_category": {
         "code": {"findings": N, "actioned": N},
         "infra": {"findings": N, "actioned": N},
         "ui": {"findings": N, "actioned": N},
         "arch": {"findings": N, "actioned": N},
         "session": {"findings": N, "actioned": N}
       }
     },
     "review_stats": {
       "total_findings": N,
       "high_confidence": N,
       "auto_fixed": N,
       "manual_required": N
     },
     "effectiveness": {
       "planned_issues": N,
       "completed": N,
       "carryover": N,
       "emergent": N,
       "completion_rate": 0.0,
       "override_ratio": 0.0
     },
     "open_questions_asked": N,
     "open_questions_answered": N,
     "open_questions_deferred": N,
     "grounding_injections": {
       "count": N,
       "files": ["..."],
       "total_lines": M
     },
     "stagnation_events": {
       "total": N,
       "by_pattern": {"error-echo": N, "turn-key-repetition": N, "pagination-spiral": N, "psa007-git-write": N, "status-partial": N},
       "by_source": {"coordinator": N, "tail": N},
       "by_error_class": {"edit-format-friction": N, "scope-denied": N, "command-blocked": N, "other": N},
       "files": ["<relative path>", "..."]
     }
   }
   ```

   > **ISO-8601 canonical format (#540):** `started_at`, `completed_at`, and `lease_acquired_at` MUST match the regex `/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/`. The validating writer (`scripts/emit-session.mjs`) rejects any non-canonical form. Use `new Date().toISOString()` (Node-native, always canonical) — never hand-edit fractional digits or timezone suffixes.

> The `session_id` uses `<HHmm>` from the `started_at` timestamp to ensure uniqueness when multiple sessions run on the same branch in one day.

> **Conditional fields:**
> - `discovery_stats`: populated ONLY when `discovery-on-close: true` in Session Config AND Phase 1.5 executed successfully. Source: the stats object returned by the discovery skill (see discovery skill Phase 4.6 for schema). When discovery runs in **embedded mode** (Phases 0-4 only), `user_dismissed`, `issues_created`, and `actioned` per category will always be `0` — embedded mode does not perform user triage (Phase 5) or issue creation (Phase 6).
> - `review_stats`: populated ONLY when Phase 1.8 dispatched the session-reviewer agent AND it returned findings. Source: the session-reviewer's output summary.
> - `effectiveness`: ALWAYS populated from Phase 1 plan verification results, and CONSTRUCTED EXPLICITLY in the METRICS_ENTRY snippet (#773) — never deferred to a "remember to add" optional step (that omission is how `carryover: 0` slipped past 41 records). `completion_rate` = `completed / planned_issues` (0.0-1.0, where 0.0 means nothing was completed). **`carryover` counting rule (#773):** `carryover` is the **length of the Phase 1.65 gate carry-list** — `autoCarry` ∪ the middle-band `ask` items the operator LEFT SELECTED ∪ the answered-question `impliesWork: true` candidates — NOT the raw Phase 1.2+1.3 candidate count. On the fail-open skip (gate disabled / headless / AUQ unavailable), EVERY candidate carries, so `carryover` = the full candidate-list length. Count the gate's OUTPUT (what reaches Phase 5 Step 3 filing), not its INPUT.
> - `effectiveness.override_ratio` (#730/H5): OPTIONAL nested field = `overridden_findings / max(total_findings_surfaced, 1)` (float 0.0-1.0). Populate ONLY when Phase 2.6 (Broken-Window Budget) ran this session (`broken-window-budget.enabled: true`). OMIT (do NOT write null/0) otherwise — **absent = "not measured"**, `0.0` = "measured, nothing overridden". `overridden_findings` = the summed `count` of the `orchestrator.finding.overridden` events emitted this session; `total_findings_surfaced` = every MED/LOW+ finding surfaced across Phase 1.8 + wave reviewers.
> - `waves[].agent_count_planned` / `waves[].agent_count_started` / `waves[].agent_count_completed` (#724/#1115): OPTIONAL per-wave fields, sourced from `wave-loop.md` § Capture wave metrics step 7 — mirror its definitions exactly, do not re-derive them here. `agent_count_planned` = agents named in the session plan for this wave. `agent_count_started` = distinct agents whose `agent-<id>.meta.json` sidecar is present, after any silent-drop re-dispatch — NOT "produced a tool-result" (under background dispatch the launch ack is a result and would count an agent that never ran). `agent_count_completed` = distinct agents whose task-notification (`<status>completed</status>`) arrived. Omit each field when the wave did not measure it — **absent = "not measured"**, never zero-fill; `0` would read as "measured, no agent started", which is the opposite of an unmeasured wave. The two gaps carry the diagnosis: `agent_count_planned > agent_count_started` after re-dispatch is a persistent silent drop, `agent_count_started > agent_count_completed` at wave end is an agent that started and never returned. Both are also logged to STATE.md `## Deviations` by wave-loop.md, so a record and a deviation entry should agree.
> - `waves[].planned_files_count` / `waves[].over_delivery_ratio` (#730/H4): OPTIONAL per-wave fields, populated from STATE.md Wave History headers of the form `(planned <P> files → actual <A>, over-delivery <R>)` (written by wave-executor §3a since #730/H4); omit when absent (pre-#730 sessions / grounding-check: false).
> - `waves[].suite_passed` / `waves[].suite_failed` / `waves[].suite_platform` (#944): OPTIONAL per-wave fields. Omit all three when absent — absent = "not measured", `suite_failed: 0` = "measured, zero failures".
>   **`suite_passed` / `suite_failed`: read the event FIRST, the STATE.md header only as fallback (#966 step 3).** Since #954/#967 the between-waves gate wrapper `scripts/run-quality-gate.mjs` emits `orchestrator.quality_gate.{passed,failed}` with a machine-measured `counts: {passed, failed, total}` AND the `wave_number` it resolved from the `wave-scope.json` sidecar, so per-wave attribution needs no wall-clock window join. Payload fields are flat at the record's top level; for each wave `N` of this session:
>
>   ```bash
>   jq -c --argjson w N --arg s "<semantic_session_id>" '
>     select(.event | startswith("orchestrator.quality_gate."))
>     | select(.semantic_session_id == $s and .wave_number == $w and .counts != null)
>     | .counts' .orchestrator/metrics/events.jsonl | tail -1
>   ```
>
>   Filtering by `semantic_session_id` is mandatory — `events.jsonl` accumulates across sessions and every past session also had a wave `N`. Take the LAST matching record (the wave's final gate run); `counts.passed` → `suite_passed`, `counts.failed` → `suite_failed`. No match = the field was not measured for that wave → omit, never zero-fill (the producer already omits `counts` rather than zero-filling when a run fail-fast'd before the test gate).
>   **Fallback, still live:** when no event matches, fall back to the STATE.md Wave History header `— suite <passed>/<failed> on <platform>` (written by wave-executor §3a since #944). Three cases genuinely need it: pre-#954 sessions, a gate run outside the `run-quality-gate.mjs` wrapper, and the `verification-auto-fix` producer in `scripts/lib/quality-gate.mjs`, which emits `counts` but no `wave_number` (its records are mid-wave retries, so not matching the selector is correct).
>   **`suite_platform` has no event source at all** and is read from the STATE.md header, unchanged. **Remaining work to retire the prose path fully:** (1) carry the platform on the gate event payload; (2) once a session has landed with the event path green and no fallback hits, drop the hand-written trio from `wave-loop.md` step 7. Until both hold, the trio stays written — deleting the writer before the reader is proven loses the numbers for sessions in flight.
> - `open_questions_asked` / `open_questions_answered` / `open_questions_deferred` (#773): the three open-question counts from the Phase 1.65 gate's AUQ Call 2 (identical to the `questions_*` payload fields on the `orchestrator.handover.gated` event). Top-level, additive, non-negative integers. Populate ONLY when the gate ran an interactive triage ("Closen + Triage" path). OMIT all three (do NOT write `0`) when the gate was skipped (fail-open / headless / disabled) or took the fast-path — absent = "not measured", `0` = "measured, zero questions". Validator accepts absent/null/non-negative-integer.
> - `stagnation_events`: populated ONLY when ≥1 stagnation event was logged to `events.jsonl` during this session. When `total == 0`, the field is omitted from the JSONL entry.
> - `grounding_injections`: populated ONLY when ≥1 `orchestrator.grounding.injected` event was logged to `events.jsonl` during this session. When `count == 0`, the field is omitted from the JSONL entry.
> - `memory_cleanup_at`: **derived by the writer, not supplied by the coordinator.** `scripts/emit-session.mjs` sets it to `completed_at` whenever an `orchestrator.memory.cleanup_completed` event for THIS session sits in `events.jsonl` — emitted by every `/memory-cleanup` run in ANY mode (dry-run, apply-pending, OR healthy no-op). **A no-op is still a cleanup; it still emits, so the cadence marker (`readDreamSignals` → `lastCleanupAt`) still advances and `shouldDispatchAutoDream` does not fire a false nudge.** No event → field absent (never `null`). An explicit value already on the record wins and is not overwritten. Do NOT hand-call `stampMemoryCleanup()` here — the coordinator-supplied-boolean form was removed on 2026-08-17 after it silently failed for a real cleanup on 2026-08-14. (#699)
