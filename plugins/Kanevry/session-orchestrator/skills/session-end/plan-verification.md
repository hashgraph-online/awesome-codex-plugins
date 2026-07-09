# Phase 1: Plan Verification

> Sub-file of the session-end skill. Executed as the first phase of session close-out.
> For quality gates, documentation, commit, and reporting, see `SKILL.md`.

Read back the session plan that was agreed at the start. For EACH planned item:

### SESSION_START_REF accessor

> Referenced by Phase 3.2 (Docs Verification) and Phase 1.1a (File-Level Grounding). Canonical definition lives here.

Read `session-start-ref` from STATE.md frontmatter. If the field is missing (older session or persistence disabled), fall back to `git diff --name-only origin/main...HEAD` (compares current HEAD against origin/main rather than a pinned SHA). The fallback is less precise but functional. Always prefer the pinned SHA when available.

```bash
SESSION_START_REF=$(node --input-type=module -e "
import {readFileSync} from 'node:fs';
import {parseFrontmatter} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
const fm = parseFrontmatter(readFileSync('<state-dir>/STATE.md', 'utf8'));
process.stdout.write(fm['session-start-ref'] ?? '');
" 2>/dev/null)
# Fallback when field absent
[ -z "$SESSION_START_REF" ] && SESSION_START_REF="origin/main"
```

### 1.1 Done Items
- **Verify with evidence**: read the changed files, check git diff, run relevant test
- Confirm acceptance criteria are met
- Mark as completed

### 1.1a File-Level Grounding

> Gate: skip this entire sub-phase if `grounding-check: false` in Session Config (default: `true`). Informational — does NOT block the session close on its own.

Compare the files the plan said would be touched against the files actually changed in the session. Catches both **scope creep** (files changed that were not in any agent's prompt scope) and **incomplete coverage** (files in the plan that were never edited).

1. **Planned files** = union of all file paths from agent prompt scopes across all waves. Source: STATE.md Wave History, falling back to the original session plan's per-agent "Files:" specs. Glob patterns are expanded against the working tree at session-start time.
2. **Actual files** = `git diff --name-only $SESSION_START_REF..HEAD`, where `$SESSION_START_REF` comes from the `session-start-ref` field in STATE.md frontmatter. If the field is missing (older session), fall back to `git diff --name-only origin/main...HEAD`.
3. **Compute discrepancies:**
   - **Touched** = files in both Planned and Actual
   - **Unplanned (scope creep)** = files in Actual but not in Planned
   - **Untouched (incomplete coverage)** = files in Planned but not in Actual
4. **Noise reduction filters** (apply before reporting):
   - Test files (`*.test.*`, `*.spec.*`, `**/__tests__/**`) corresponding to a touched production file are reclassified as expected (not scope creep)
   - Generated/lock files (`pnpm-lock.yaml`, `*.lock`, `dist/**`, `node_modules/**`) are excluded from both planned and actual sets
   - The `.claude/`, `.codex/`, and `.cursor/` state directories are excluded — they are session artifacts, not code
5. **Report** in the verification output:
   ```
   File-level grounding:
   - Planned: N files
   - Touched: N files (X% coverage)
   - Unplanned (scope creep): N files [list first 5]
   - Untouched (planned but not edited): N files [list first 5]
   ```
6. **Append to session metrics** (`grounding` field in the Phase 1.7 JSONL entry):
   ```json
   "grounding": {
     "planned": N,
     "touched": N,
     "unplanned": N,
     "untouched": N
   }
   ```
   The metrics field is conditional on `grounding-check: true` — when the gate is off, omit the field entirely (do not write `null`).

### 1.2 Partially Done Items
- Document what was completed and what remains
- Create a VCS issue for the remaining work with:
  - Title: `[Carryover] <original task description>`
  - Labels: `priority:<original>`, `status:ready`
  - Description: what's done, what's left, context for next session
- Link to original issue if applicable

### 1.3 Not Started Items
- Document WHY (blocked? de-scoped? out of time?)
- If still relevant: ensure original issue remains `status:ready`
- If no longer relevant: close with comment explaining why

### 1.3a Optional /goal Backlog-Drain (opt-in — #636)

When `goal-integration.enabled: true` with seam `session-end-backlog`, the close may surface ONE advisory `/goal` command to drain still-relevant §1.2/§1.3 items in-session instead of carrying them over. See `SKILL.md § 1.3a Optional /goal Backlog-Drain` for the full gate conditions, advisory-only contract, and the LM-008 cross-reference — the two files mirror each other; the prose lives in SKILL.md.

### 1.4 Emergent Work
- Tasks that were NOT in the plan but were done (fixes, discoveries)
- Document and attribute to relevant issues
- If new issues were identified: create them on the VCS platform

### Candidate Record Format (#769)

> Since #769, Phases 1.2 / 1.3 (still-relevant) / 1.4 (unfinished emergent) / 1.6 (SPIRAL/FAILED walk) **no longer file `[Carryover]` issues immediately** — they append **carryover candidates** to an in-memory list that the Phase 1.65 Handover Alignment Gate routes, and Phase 5 Step 3 files the gate's carry-list. The authoritative gate prose (routing, AUQ shapes, fail-open) lives in `SKILL.md § 1.65 Handover Alignment Gate` — this subsection documents only the record shape the phases produce.

Each candidate is a plain object with these fields (JS keys are the ones `routeCandidates` / `normalizeCandidate` in `scripts/lib/handover-gate.mjs` read):

| Concept | JS key | Type | Notes |
|---|---|---|---|
| task | `task` | `string` | Task text. Missing/empty → `normalizeCandidate` flags `malformed: true` and routes it to `ask`. |
| source-phase | `sourcePhase` | `'1.2' \| '1.3' \| '1.4' \| '1.6'` | The Phase-1 bucket that emitted the candidate; used to infer `bucket` when absent. |
| origin-issue | `originIssue` | `number \| null` | Origin issue IID, or `null` when there is none. **`null` → auto-carry** (dropping a candidate with no origin issue would be real forgetting; keeps `SKILL.md:853` intact). |
| priority | `priority` | `'critical' \| 'high' \| 'medium' \| 'low' \| null` | `critical`/`high` → auto-carry. `medium`/`low`/`null` (with an origin issue) → middle-band `ask`. |
| bucket | `bucket` | `'partially-done' \| 'not-started' \| 'emergent' \| 'spiral-failed'` | Maps 1.2→`partially-done`, 1.3→`not-started`, 1.4→`emergent`, 1.6→`spiral-failed`. `spiral-failed` → auto-carry. |

**Routing (deterministic, `routeCandidates`):** a candidate lands in `autoCarry` (non-deselectable, gate-summary only) when `priority ∈ {critical, high}` OR `bucket === 'spiral-failed'` OR `originIssue === null`; otherwise it lands in `ask` (the preselected middle-band multiSelect). SPIRAL/FAILED candidates additionally carry a non-schema `_spiral: { kind, context }` annotation on the coordinator's original object — consumed by the deferred `createSpiralCarryoverIssue` call in Phase 5 Step 3 (`routeCandidates` strips it from its normalized copies).

### 1.5 Discovery Scan (if enabled)

Check if `discovery-on-close` is `true` in Session Config. If not configured or `false`, skip this section.

When enabled, invoke the discovery skill in **embedded mode** by dispatching an Explore agent:
```
Agent({
  description: "Discovery embedded scan",
  prompt: "Run discovery probes in embedded mode. Scope: session probes + discovery-probes config. Return findings and stats as a JSON object in a markdown code fence. Do NOT run Phase 4 (triage) or Phase 5 (issue creation) — return after Phase 3.",
  subagent_type: "Explore",
  run_in_background: false
})
```
On Codex CLI / Cursor IDE: execute probes sequentially within the current context (no Agent dispatch).
- Collect verified findings from the discovery output
- Parse the discovery output for the **findings** array and **stats** object (see Parsing callout below)
- Store the stats object for Phase 1.7 metrics collection (`discovery_stats` field)

> **Parsing discovery output:** Search for the first ` ```json ` block in the discovery output. The JSON contains: (1) a **findings** array — objects with `probe`, `category`, `severity`, `confidence`, `file`, `line`, `description`, `recommendation` fields; (2) a **stats** object — with `probes_run`, `findings_raw`, `findings_verified`, `false_positives`, `user_dismissed`, `issues_created`, `by_category`. If JSON parsing fails, log a warning and skip Phase 1.5 — do NOT fail the session close. Store stats as `discovery_stats` in session metrics (Phase 1.7).
- Incorporate findings into issue management:
  - Findings with severity `critical` or `high` → create issues immediately (Phase 5)
  - Findings with severity `medium` or `low` → list in the Final Report under "Discovery Findings (deferred)"
- Report: "Discovery scan: [N] findings ([X] critical/high → issues, [Y] medium/low → deferred)"

### 1.6 Safety Review

> Skip if `persistence` is `false` in Session Config (STATE.md won't exist).

Review safety metrics from the session. This is informational — it does NOT block the session close.

1. Read `<state-dir>/STATE.md` to extract:
   - **Circuit breaker activations**: agents that hit maxTurns (`PARTIAL`), agents that spiraled (`SPIRAL`), agents that failed (`FAILED`)
   - **Worktree status**: which agents used worktree isolation, any fallbacks or merge conflicts
2. Read enforcement hook logs from stderr (if captured): count of scope violations blocked/warned, command violations blocked/warned
3. Summarize:
   ```
   Safety review:
   - Agents: [X] complete, [Y] partial (hit turn limit), [Z] spiral/failed
   - Enforcement: [N] scope violations, [M] command blocks
   - Isolation: [K] agents in worktrees, [J] fallbacks
   ```
4. If any agents were `SPIRAL` or `FAILED`, ensure carryover issues exist (cross-reference with Phase 1.2)

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
3. Prepare the JSONL entry (written in Phase 3.7) by **constructing it programmatically** — DO NOT manually hand-compose ISO timestamp strings. The `completed_at` value MUST come from `new Date().toISOString()` to prevent issue #540-class corruption (e.g., `.3NZ` malformed-fraction inputs). The validator at `scripts/lib/session-schema/validator.mjs` rejects any timestamp that does not match the canonical `YYYY-MM-DDTHH:MM:SS[.SSS]Z` regex.

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
     waves: [/* {wave, role, agent_count, files_changed, quality} */],
     // Optional fields populated per the Conditional Fields rules below.
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
       {"wave": 1, "role": "Discovery", "agent_count": N, "files_changed": N, "quality": "pass|fail|skip"},
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
       "completion_rate": 0.0
     }
   }
   ```

   > **ISO-8601 canonical format (#540):** `started_at`, `completed_at`, and `lease_acquired_at` MUST match the regex `/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/`. The validating writer (`scripts/emit-session.mjs`) rejects any non-canonical form. Use `new Date().toISOString()` (Node-native, always canonical) — never hand-edit fractional digits or timezone suffixes.

> **Effectiveness counting rules** (extract from Phase 1 verification results):
> - `planned_issues`: count of issue numbers listed in `<state-dir>/STATE.md` frontmatter `issues:` array. If the `issues` array is empty (e.g., lifecycle simulation sessions that don't target VCS issues), `planned_issues` = 0 — this is expected, not a bug.
> - `completed`: count of items verified as Done in Phase 1.1 (acceptance criteria met, evidence confirmed)
> - `carryover`: count of items from Phase 1.2 (partially done) + Phase 1.3 (not started but still relevant)
> - `emergent`: count of items documented in Phase 1.4 (work done that was NOT in the original plan)
> - `completion_rate`: `completed / planned_issues`. If `planned_issues` is 0, set `completion_rate` to 1.0 (vacuously complete — no planned work means nothing was left undone).
>
> **Note on lifecycle simulation sessions:** Sessions that perform codebase-wide analysis (lifecycle sims, architecture audits) typically have `planned_issues: 0` because they don't target specific VCS issues. These sessions may produce dozens of fixes but will show `planned_issues: 0, completed: 0` in effectiveness tracking. This is correct behavior — effectiveness tracks issue-level planning accuracy, not session productivity. Session productivity is captured by `total_files_changed` and `total_agents`.

> The `session_id` uses `<HHmm>` from the `started_at` timestamp to ensure uniqueness when multiple sessions run on the same branch in one day.

> **Conditional fields:**
> - `discovery_stats`: populated ONLY when `discovery-on-close: true` in Session Config AND Phase 1.5 executed successfully. Source: the stats object returned by the discovery skill (see discovery skill Phase 3.6 for schema). When discovery runs in **embedded mode** (Phases 0-3 only), `user_dismissed`, `issues_created`, and `actioned` per category will always be `0` — embedded mode does not perform user triage (Phase 4) or issue creation (Phase 5).
> - `review_stats`: populated ONLY when Phase 1.8 dispatched the session-reviewer agent AND it returned findings. Source: the session-reviewer's output summary.
> - `effectiveness`: ALWAYS populated from Phase 1 plan verification results. `completion_rate` = `completed / planned_issues` (0.0-1.0, where 0.0 means nothing was completed).

### 1.8 Session Review

Dispatch the session-reviewer agent to verify implementation quality before the quality gate:

> On Codex CLI, dispatch via the `session-reviewer` agent role defined in `.codex-plugin/agents/session-reviewer.toml`.

1. Invoke `subagent_type: "session-orchestrator:session-reviewer"` with:
   - **Scope**: all files changed this session (from `git diff --name-only` against the base branch)
   - **Context**: the session plan (issues, acceptance criteria) and all wave results from STATE.md
2. Wait for the reviewer's **Verdict**:
   - **PROCEED** — continue to Phase 2
   - **FIX REQUIRED** — address each listed item before proceeding. For quick fixes (<2 min each), fix inline. For larger items, create carryover issues (same as Phase 1.2) and note them as unresolved review findings in the Final Report
