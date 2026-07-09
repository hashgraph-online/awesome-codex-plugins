# Phase 3.2: Docs Verification (docs-orchestrator integration)

> Skip this subsection if `docs-orchestrator.enabled` config is not `true` (default: `false`). Also skip entirely if `docs-orchestrator.mode` is `off`.

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). The Dev audience target listed below resolves to whichever file the repo uses.

## Step 1 — Load docs-tasks SSOT

Read `docs-tasks` from STATE.md frontmatter. This field is written by wave-executor Pre-Wave 1b when `docs-orchestrator.enabled: true` and session-plan emitted a `### Docs Tasks (machine-readable)` block.

Use `scripts/lib/state-md.mjs` to parse the frontmatter safely — do NOT re-implement YAML parsing inline. Example accessor:

```bash
node --input-type=module -e "
import {readFileSync} from 'node:fs';
import {parseFrontmatter} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
const raw = readFileSync('<state-dir>/STATE.md', 'utf8');
const fm = parseFrontmatter(raw);
const tasks = fm['docs-tasks'];
if (!Array.isArray(tasks)) { process.stdout.write('ABSENT'); process.exit(0); }
process.stdout.write(JSON.stringify(tasks));
"
```

**Fallback — missing field:** If `docs-tasks` is absent from frontmatter, attempt to re-parse the session-plan output's `### Docs Tasks (machine-readable)` YAML fenced block from conversation context. This is degraded but functional.

**No tasks found at all:** Log `"ℹ docs-orchestrator enabled but no docs-tasks persisted — skipping verification"` in the session report and skip Phase 3.2 entirely. This is NOT an error.

**Silent-failure guard:** If STATE.md is unreadable, if frontmatter YAML is malformed, or if `docs-tasks` is present but not a list — these MUST produce an explicit error entry in the session final report. Do NOT skip silently:
```
⚠ Phase 3.2: docs-tasks parse error — <reason>. Manual docs verification required.
```

## Step 2 — Read SESSION_START_REF

Read `session-start-ref` from STATE.md frontmatter. Full accessor and fallback chain are documented in `plan-verification.md § SESSION_START_REF accessor`. Summary:
- Primary: `session-start-ref` field in STATE.md frontmatter.
- Fallback: `git diff --name-only origin/main...HEAD` (no specific base SHA).

If `git diff` itself fails (network issue, corrupt repo), log:
```
⚠ Phase 3.2: git diff failed — <stderr>. Docs verification skipped.
```
and skip Phase 3.2. This is an explicit error, not a silent skip.

## Step 3 — Compute changed files

```bash
CHANGED_FILES=$(git diff --name-only "$SESSION_START_REF..HEAD")
```

Cache this list for the per-task loop below. If the command exits non-zero, surface the error per the guard above and skip Phase 3.2.

## Step 4 — Audience → file-pattern reference

The following mini-table mirrors `skills/docs-orchestrator/audience-mapping.md` (authoritative source — consult it for updates):

| Audience | Target file patterns |
|----------|----------------------|
| `user` | `README.md`, `docs/user/**/*.md`, `docs/getting-started.md`, `examples/**/*.md` |
| `dev` | `CLAUDE.md` (or `AGENTS.md` on Codex CLI), `docs/dev/**/*.md`, `docs/adr/**/*.md` |
| `vault` | `<vault>/01-projects/<slug>/context.md`, `<vault>/01-projects/<slug>/decisions.md`, `<vault>/01-projects/<slug>/people.md` |

Each `docs-task` carries its own `target-pattern` field (set during session-plan Step 1.8, derived from the audience-mapping table above). Use `task.target-pattern` as the primary match target; the table above is for human reference and fallback when `target-pattern` is absent.

## Step 5 — Per-task verification loop

For each `task` in `docs-tasks`:

1. **Resolve target:** glob-match `task.target-pattern` against the cached `CHANGED_FILES` list.

2. **Not matched → GAP:**
   - No file matching `task.target-pattern` appears in the diff.
   - Record outcome: `gap`.

3. **Matched → inspect diff:**
   ```bash
   git diff "$SESSION_START_REF..HEAD" -- <matched-file>
   ```
   - **Substantive content change** (non-whitespace, non-comment-only lines added/removed): outcome `ok`.
   - **Whitespace-only or structural-only diff** (no prose or code content changed): outcome `gap`.
   - **File contains `<!-- REVIEW: source needed -->` markers within changed regions:** outcome `partial`. This means content was written but requires human review before release. `partial` does NOT block in strict mode — it is always a warning, by policy choice. Document both the `ok` content and the markers in the report.

4. Record `{id, audience, target-pattern, wave, status: ok|partial|gap}` for the aggregate report.

## Step 6 — Aggregate and report per mode

Read `docs-orchestrator.mode` from Session Config (default: `warn`).

**`mode: warn`** (default, non-blocking):
- Append a subsection to the Phase 6 Final Report (see below).
- `/close` proceeds regardless of gap count.

**`mode: strict`** (surfaces an AUQ on any gap; default = warn + carryover + continue — never hard-blocks):
- If ALL tasks are `ok` or `partial`: proceed — append report, continue close.
- If ANY task is `gap`:
  - **Claude Code:** use `AskUserQuestion` with these options (mark Recommended):
    ```
    Phase 3.2 found documentation gaps. How would you like to proceed?
    1. Warn + carryover and close (Recommended)
    2. Override — close session with gaps (deviations logged)
    ```
  - **Codex CLI / Cursor fallback:** render a numbered Markdown list:
    ```markdown
    ## Phase 3.2: Documentation Gaps Detected (mode=strict)

    Choose one:
    1. **Warn + carryover and close** *(Recommended)*
    2. Override — close session with gaps (deviations will be logged)

    Gap tasks: <list task IDs and target-patterns>
    ```
  - On "Warn + carryover and close": file a carryover issue (labels `carryover`, `priority:high`) titled `[Carryover] Documentation gaps (strict) — <gap-count> tasks` listing the gap task IDs + target-patterns for a follow-up session, log the deviation (below), then append the report and continue the close.
  - On "Override": log a deviation in the `## Deviations` section of STATE.md:
    ```
    - [Phase 3.2] docs-orchestrator strict-mode gaps overridden by user. Tasks: <ids>. Timestamp: <ISO 8601>.
    ```
    Then append the report and proceed with close.

**`mode: off`:** This path is not reached because the Phase gate at the top of 3.2 exits early for `mode: off`. Documented here for completeness.

## Step 7 — Documentation Coverage report block

Emit the following block to be included in Phase 6 Final Report under `### Documentation Coverage (docs-orchestrator)`:

```
### Documentation Coverage (docs-orchestrator)

Mode: <warn|strict>
Tasks verified: <total>

| Task ID | Audience | Target pattern | Wave | Status |
|---------|----------|----------------|------|--------|
| <id>    | <user|dev|vault> | <pattern> | <N> | ✅ ok / ⚠ partial / ❌ gap |
...

Summary: <N> ok, <N> partial (REVIEW markers present — human review needed before release), <N> gap
```

For `partial` tasks, append a note per task:
```
⚠ <target-pattern>: contains <!-- REVIEW: source needed --> markers — content written but not fully source-cited. Review before release.
```

For `gap` tasks in warn mode, append:
```
ℹ Gap tasks were not addressed. No docs-writer output found for these patterns. Consider scheduling in a follow-up session.
```
