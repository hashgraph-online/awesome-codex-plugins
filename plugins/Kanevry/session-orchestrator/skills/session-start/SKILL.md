---
name: session-start
user-invocable: false
tags: [orchestration, initialization, analysis, alignment]
model: inherit
model-preference: opus
model-preference-codex: gpt-5.4
model-preference-cursor: claude-opus-4-6
description: >
  Use this skill when initializing a session for any project repo. Autonomously analyzes git state,
  VCS issues, SSOT files, branches, environment, and cross-repo status. Then presents
  structured findings with recommendations for user alignment before creating a wave plan.
  Triggered by /session [housekeeping|feature|deep] command.
---

# Session Start Skill

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). All references to `CLAUDE.md` in this skill resolve via that precedence rule.

## Soul

Before anything else, read and internalize `soul.md` in this skill directory. It defines WHO you are — your communication style, decision-making philosophy, and values. Every interaction in this session should reflect this identity. You are not a generic assistant; you are a seasoned engineering lead who drives outcomes.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 1: Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`.

## Phase 1.2: Session Lock Acquire (#330)

> Skip this phase if `persistence` config is `false`.

Acquire a distributed session-lock to detect parallel sessions in the same repo before initializing STATE.md. This prevents two concurrent Claude/Codex sessions from stomping each other's wave state and metrics writes.

```javascript
import { acquire, forceAcquire } from 'scripts/lib/session-lock.mjs';
const result = acquire({ sessionId, mode: sessionType, ttlHours: 4, repoRoot: process.cwd() });
```

Where `sessionId` is the session identifier derived from the session type and timestamp (e.g. `main-2026-05-08-deep-1`), and `sessionType` is the session mode (`housekeeping`, `feature`, or `deep`).

### Decision flow

1. **`result.ok === true`** → lock is held. Continue to Phase 1.5 (Session Continuity). The lock must be released in session-end.

2. **`result.ok === false`** with `reason === 'active'**:
   - Another Claude/Codex session holds an active lock in this repo.
   - Present a choice via `AskUserQuestion`:
     ```js
     AskUserQuestion({
       questions: [{
         question: `Another session lock is active in this repo (started ${ageHours}h ago, mode=${existingLock.mode}, host=${existingLock.host}, pid=${existingLock.pid}). How should I proceed?`,
         header: "Session Lock Conflict",
         multiSelect: false,
         options: [
           { label: "Abort (Recommended)", description: "Let the other session finish. Safe default — prevents metrics and wave-state corruption." },
           { label: "Force-take the lock", description: "Overwrites the active lock. ONLY use if you are certain the other session is no longer running." },
         ],
       }],
     });
     ```
   - **Codex CLI / Cursor IDE fallback (numbered Markdown list):**
     ```
     Session lock conflict — active lock detected (started <ageHours>h ago, mode=<mode>, host=<host>, pid=<pid>).
     1. Abort (Recommended) — let the other session finish.
     2. Force-take the lock — ONLY if the other session is known dead.
     Reply with the number of your choice.
     ```
   - On **Abort**: exit session-start cleanly with a brief stderr note (`session-lock: aborted — active lock held by session_id=<id>`). Do NOT initialize STATE.md.
   - On **Force-take**: call `forceAcquire({ sessionId, mode: sessionType, ttlHours: 4, repoRoot: process.cwd() })`. After Phase 1.5 initializes STATE.md, append a deviation via `appendDeviation()`:
     `Force-took session lock from session_id=<existingLock.session_id>, age=<ageHours>h, mode=<existingLock.mode>, pid=<existingLock.pid>`. Continue.

3. **`result.ok === false`** with `reason === 'stale-pid-dead'` or `'stale-pid-alive'**:
   - A stale lock was found (TTL expired). Likely left behind by a session that crashed or was force-killed.
   - Present a choice via `AskUserQuestion`:
     ```js
     AskUserQuestion({
       questions: [{
         question: `Stale session lock found (started ${ageHours}h ago, ttl=${existingLock.ttl_hours}h). Process pid=${existingLock.pid} on host=${existingLock.host} is ${reason === 'stale-pid-dead' ? 'confirmed dead' : 'still running or status unknown'}. Reclaim the lock?`,
         header: "Stale Session Lock",
         multiSelect: false,
         options: [
           { label: "Reclaim (Recommended)", description: "Overwrite the stale lock and continue. Safe when the previous session is no longer active." },
           { label: "Abort — investigate manually", description: "Stop here. Inspect .orchestrator/session.lock before proceeding." },
         ],
       }],
     });
     ```
   - **Codex CLI / Cursor IDE fallback (numbered Markdown list):**
     ```
     Stale session lock found (started <ageHours>h ago, ttl=<ttlHours>h, pid=<pid> on <host>).
     1. Reclaim (Recommended) — overwrite stale lock and continue.
     2. Abort — investigate .orchestrator/session.lock manually.
     Reply with the number of your choice.
     ```
   - On **Reclaim**: call `forceAcquire({ sessionId, mode: sessionType, ttlHours: 4, repoRoot: process.cwd() })`. After Phase 1.5 initializes STATE.md, append a deviation:
     `Stale-lock reclaim: replaced lock from session_id=<existingLock.session_id>, age=<ageHours>h, pid=<existingLock.pid>`. Continue.
   - On **Abort**: exit cleanly.

4. **`result.ok === false`** with `reason === 'fs-error'**:
   - Filesystem error when writing the lock file. Log `⚠ session-lock: acquire failed — <error>. Continuing without lock (degraded mode).` and proceed without a lock. Do NOT block the session for a transient FS error.

### Cross-host behaviour

When `existingLock.host !== os.hostname()`, PID liveness cannot be checked (`pidAlive: null`). In this case:
- For `reason === 'active'`: the recommendation is **Abort** — cross-host locks cannot be verified as dead.
- For stale reasons: the recommendation is still **Reclaim** only if TTL is clearly expired (>2× ttl_hours). Otherwise default to **Abort**.
- **Never auto-reclaim cross-host locks** under any circumstance — always present the AUQ and let the user decide.
- The AUQ question text for cross-host cases should note: `"(cross-host — PID liveness cannot be verified)"`.

## Phase 1.5: Session Continuity

> Skip this phase if `persistence` config is `false`.

Check for `<state-dir>/STATE.md` in the project root:

> Where `<state-dir>` is `.claude/` under Claude Code or `.codex/` under Codex CLI. See `skills/_shared/platform-tools.md` for details.

> **Ownership Reference:** See `skills/_shared/state-ownership.md` for the STATE.md ownership contract, schema, and guards.

Before reading STATE.md contents, validate the branch field:
- If STATE.md's `branch` does not match `git rev-parse --abbrev-ref HEAD`, log: "⚠ STATE.md from branch [X], current branch is [Y] — treating as stale." Skip to step 2 (treat as if STATE.md does not exist).

1. **STATE.md exists** — read it and inspect the `status` field:
   - `status: active` — previous session crashed or was interrupted. Use the AskUserQuestion tool to present: "Found unfinished session from [started_at]. [N] waves completed. Resume or start fresh?" with options to resume the previous plan or start a new session. After a resume choice, proceed to **Snapshot Recovery** subsection below.
   - `status: paused` — session was intentionally paused. Use AskUserQuestion to offer resuming from the pause point or starting fresh. After a resume choice, proceed to **Snapshot Recovery** subsection below.
   - `status: completed` — previous session ended cleanly. Note the summary for context (what was done, what was deferred), then **render the Recommendations Banner** (see subsection below) and **reset STATE.md to idle** before any new session state is written (see "Idle Reset" below). Continue with normal initialization.
2. **STATE.md does not exist** — first session or persistence was previously off. Continue normally.

### Recommendations Banner (Epic #271 Phase A)

> Runs on the `status: completed` branch only, BEFORE Idle Reset archives the fields. Silent no-op on other branches.

Read the 5 optional v1.1 Recommendation fields from STATE.md frontmatter via `parseRecommendations` (from `scripts/lib/state-md.mjs`). The writer is session-end Phase 3.7a (see `skills/session-end/SKILL.md`).

```bash
node --input-type=module -e "
import {readFileSync} from 'node:fs';
import {parseStateMd, parseRecommendations} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
import {isValidMode} from '${PLUGIN_ROOT}/scripts/lib/recommendations-v0.mjs';
import {appendFileSync, mkdirSync} from 'node:fs';

const SWEEP_LOG = '.orchestrator/metrics/sweep.log';
function logWarn(event, detail) {
  try {
    mkdirSync('.orchestrator/metrics', {recursive: true});
    appendFileSync(SWEEP_LOG, JSON.stringify({timestamp: new Date().toISOString(), event, detail}) + '\n');
  } catch {}
}

const parsed = parseStateMd(readFileSync('<state-dir>/STATE.md', 'utf8'));
if (!parsed) process.exit(0);
const rec = parseRecommendations(parsed.frontmatter);
if (!rec) process.exit(0); // pre-v1.1 STATE.md — graceful silent no-banner (AC3)

// AC4: type-mismatch in top-priorities — field-level null from parser; still render other fields
if (rec.priorities === null && Object.prototype.hasOwnProperty.call(parsed.frontmatter, 'top-priorities')) {
  logWarn('state-md-type-mismatch', {field: 'top-priorities', got: typeof parsed.frontmatter['top-priorities']});
}

// AC4: partial fields — warn but still render available ones
const missingCount = [rec.mode, rec.priorities, rec.carryoverRatio, rec.completionRate, rec.rationale].filter((x) => x === null).length;
if (missingCount > 0 && missingCount < 5) {
  logWarn('state-md-partial-recommendation', {missing: missingCount});
}

const modeOk = rec.mode && isValidMode(rec.mode);
const mode = modeOk ? rec.mode : '(unknown-mode)';
const rationale = rec.rationale || '(no rationale)';
const pct = (x) => (x === null ? '—' : Math.round(x * 100) + '%');
console.log('📋 Previous session recommended: ' + mode + ' — ' + rationale + ' (completion: ' + pct(rec.completionRate) + ', carryover: ' + pct(rec.carryoverRatio) + ')');
if (Array.isArray(rec.priorities) && rec.priorities.length > 0) {
  console.log('  Suggested issues: ' + rec.priorities.map((id) => '#' + id).join(', '));
}
"
```

**Behavior matrix (AC1/AC3/AC4):**
- All 5 fields present + valid → banner line + suggested-issues line (if priorities non-empty).
- Field(s) absent entirely → no banner (graceful no-op, no WARN).
- 1–4 fields present (partial) → banner renders with `—` for missing, WARN `state-md-partial-recommendation` to sweep.log.
- `top-priorities` is not an array (type-mismatch) → treated as null, WARN `state-md-type-mismatch` to sweep.log, other fields still render.
- Unknown `recommended-mode` value → banner shows `(unknown-mode)` instead of the string.

The reader does NOT mutate STATE.md — it is a pure observer. Idle Reset (subsection below) is the only code path that modifies the file on the `completed` branch.

### Idle Reset (completed-branch only)

When (and only when) the prior `status` is `completed`, rewrite STATE.md to a clean idle state before Phase 1b (Initialize STATE.md) runs. This prevents the next agent from reading a stale "completed" banner at session-start, while preserving the prior session's record in a demoted archive block.

Reset rules — applies ONLY on the `completed` branch. Do NOT perform this reset on `active` or `paused`; those paths stay user-interactive via AskUserQuestion.

1. Set frontmatter `status: idle`.
2. Clear `current-wave` (set to `0`).
3. Move the existing `## Wave History` body into a new `## Previous Session` archive section (retain the record, but demote it below the new session's live state). Remove the original `## Wave History` section — wave-executor will recreate it on the next wave.
4. Clear `## Deviations` (leave the heading with an empty body so the schema is preserved).
5. Leave other frontmatter fields (`schema-version`, `session-type`, `branch`, `issues`, `started_at`, `total-waves`) intact until Phase 1b overwrites them with the new session's values.
6. **v1.1 Recommendation-field archival (Epic #271 Phase A, AC2):** If ANY of the 5 Recommendation fields (`recommended-mode`, `top-priorities`, `carryover-ratio`, `completion-rate`, `rationale`) is present in the frontmatter, remove them from the frontmatter via `updateFrontmatterFields(contents, {field: null, ...})` (null value deletes the key). Then prepend a readable block (NOT YAML) to the `## Previous Session` body:

   ```markdown
   ### Recommendations (archived from v1.1 frontmatter)
   - **Recommended mode:** <mode>
   - **Rationale:** <rationale>
   - **Completion rate:** <XX%>
   - **Carryover ratio:** <XX%>
   - **Top priorities:** #<id>, #<id>, …  _(or "none")_
   ```

   Omit individual bullets for null-valued fields. If all 5 are null (i.e., `parseRecommendations` returned non-null but every field is null after type-coercion), skip the archival block entirely.

Rationale: `/close` intentionally keeps STATE.md as a record so the next session-start can read it. This reset completes that contract by demoting the record before new session state is written, so a fresh session never appears "already completed". The Recommendation archival (rule 6) preserves the session-to-session handoff in a human-readable form after the Recommendations Banner has rendered — Phase B's Mode-Selector will read the LIVE frontmatter of the current session and does not need the archived copy, so this is purely informational for humans browsing STATE.md history.

### Snapshot Recovery (#196)

Applies ONLY after the user chose to **resume** from the `active`/`paused` branch above. Skip entirely on the `completed` branch (snapshots for completed sessions are GC'd by session-end, not offered for recovery) and on the "start fresh" path of an `active`/`paused` prompt (starting fresh implies abandoning any snapshot).

```js
import { listSnapshots, deleteSnapshot } from '$PLUGIN_ROOT/scripts/lib/coordinator-snapshot.mjs';

const snaps = await listSnapshots({ sessionId: '<sessionId from STATE.md>' });
```

If `snaps.length === 0` → no snapshots to recover; continue to the Current-Task Banner.

If `snaps.length >= 1` → present the following choice:

**Claude Code (AskUserQuestion):**

```js
AskUserQuestion({
  questions: [{
    question: `Found ${snaps.length} coordinator snapshot(s) from the resumed session (latest from ${humanAgeOf(snaps[0].createdAt)}). Recover, keep as backup, or discard?`,
    header: "Snapshot",
    multiSelect: false,
    options: [
      { label: "Recover (diff vs current tree) (Recommended)", description: "Apply the latest snapshot back onto the working tree. You will see a diff and can unstage unwanted changes before committing." },
      { label: "Keep as backup", description: "Leave refs/so-snapshots/* in place untouched. You can recover manually later via `git stash apply $(git rev-parse <ref>)`." },
      { label: "Discard all", description: "Delete all refs/so-snapshots/<sessionId>/* immediately via deleteSnapshot." },
    ],
  }],
});
```

**Codex CLI / Cursor IDE fallback (numbered Markdown list):**

```markdown
Snapshot recovery options:

1. **Recover (Recommended)** — Apply the latest snapshot back onto the working tree. You will see a diff and can unstage unwanted changes before committing.
2. **Keep as backup** — Leave the refs in place untouched. You can recover manually later.
3. **Discard all** — Delete all refs/so-snapshots/<sessionId>/* immediately.

Reply with the number of your choice.
```

On user choice:
- **Recover** → `git stash apply <snaps[0].sha>` (use apply, not pop — leaves the ref intact in case the user changes their mind). Then show the resulting `git diff --stat` so the user sees what landed.
- **Keep as backup** → no-op. Log in the Session Overview: `Snapshot(s) retained: <N>. Recover manually with \`git stash apply <sha>\`.`
- **Discard all** → for each snapshot in `snaps`, call `deleteSnapshot({refName: snap.ref})`. Log count.

Snapshot age (`humanAgeOf`) is derived from `snap.createdAt` (ISO 8601 from `git for-each-ref --format='%(committerdate:iso8601)'`). A simple inline helper:

```js
function humanAgeOf(iso) {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
```

### Current-Task Banner (#184)

After the continuity checks above, render a one-line banner showing the current task from STATE.md. This gives the user an immediate "where am I" signal before the rest of the session overview loads.

```bash
node --input-type=module -e "
import {readFileSync} from 'node:fs';
import {readCurrentTask} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
try {
  const t = readCurrentTask(readFileSync('<state-dir>/STATE.md', 'utf8'));
  if (t) console.log('Current task: ' + t.description);
} catch {}
"
```

Skip silently when STATE.md is absent or unreadable. The banner is informational, not load-bearing.

Also read `<state-dir>/STATUS.md` if it exists for additional project-level context.

## Phase 1.6: Metrics Initialization

> Skip if `persistence` config is `false`.

1. Ensure '.orchestrator/metrics/' directory exists in the project root (create if missing). For backward compatibility with pre-v2.0 sessions, also check the platform's legacy metrics directory (`<state-dir>/metrics/` where `<state-dir>` is `.claude/`, `.codex/`, or `.cursor/` per platform).
2. If '.orchestrator/metrics/sessions.jsonl' exists, count lines to determine number of previous sessions. If not found, check `<state-dir>/metrics/sessions.jsonl` as a platform-specific legacy fallback.
3. Store the count for display in Phase 7 — this feeds the Historical Trends section

## Phase 2: Git Analysis (parallel)

Run these checks as ONE parallel Bash block — background the independent git ops with `&` and `wait`:

```bash
# Independent ops — launch in parallel, collect output via tmpfiles
git branch -a > /tmp/so-branches.$$ &
git log --oneline -N > /tmp/so-commits.$$ &        # N from Session Config `recent-commits` (default 20)
git status --short > /tmp/so-status.$$ &
git log origin/main..HEAD --oneline > /tmp/so-ahead.$$ &
wait
# Then read the 4 tmpfiles in a single step and derive: branch state, recent commits,
# unpushed/uncommitted, open branches. Clean up tmpfiles once derivations are done:
rm -f /tmp/so-branches.$$ /tmp/so-commits.$$ /tmp/so-status.$$ /tmp/so-ahead.$$
```

Checks to run (derived from the collected output):

1. **Branch state**: current branch (from `branch -a`), ahead/behind origin (from `ahead` tmpfile)
2. **Recent commits**: parse `commits` tmpfile — identify last session's work by commit patterns
3. **Unpushed/uncommitted**: `status` tmpfile + `ahead` tmpfile combined
4. **Open branches**: parse `branch -a` tmpfile, identify which are mergeable to develop/main
5. **Stale branches**: run AFTER the parallel block — requires iterating over branches (depends on `branch -a` output). Use `git log -1 --format=%ct <branch>` per branch; flag those with no commits in more than `stale-branch-days` (default: 7) days.

**Rationale:** The 4 independent ops are I/O-bound — running them in parallel cuts Phase 2 wall-clock from ~500ms to ~150ms. The stale-branches check depends on the branch list, so it runs after `wait`.

## Phase 2.5: Docs Planning (Docs-Orchestrator Integration)

> Skip this phase if `docs-orchestrator.enabled` config is not `true` (default: `false`).

Reads the `docs-orchestrator` config fields, auto-detects which audiences (user/dev/vault) are affected by the current scope using signals from Phases 2–5, confirms the selection with the user via AskUserQuestion, and emits a `### Docs Planning Result (Phase 2.5)` block into the conversation context. That block is the **MANDATORY contract** consumed by session-plan Step 1.8 to seed Docs-role tasks. Audience → file-pattern mapping is the authoritative source at `skills/docs-orchestrator/audience-mapping.md`. Contains non-overlap discipline rules (paths owned by `vault-mirror` and `daily` are off-limits).

**See `phase-2-5-docs-planning.md` for full details.**

## Phase 2.6: Steering Docs Loading

> Skip this phase silently when `.orchestrator/steering/` does not exist in the project root. This mirrors Phase 2.5's silent-no-op pattern — backward compatibility with repos that have not yet scaffolded steering docs.

Check for the steering directory and load all three docs if present:

```bash
STEERING_DIR=".orchestrator/steering"
if [ -d "$STEERING_DIR" ]; then
  PRODUCT_MD=""
  TECH_MD=""
  STRUCTURE_MD=""
  [ -f "$STEERING_DIR/product.md" ]   && PRODUCT_MD=$(cat "$STEERING_DIR/product.md")
  [ -f "$STEERING_DIR/tech.md" ]      && TECH_MD=$(cat "$STEERING_DIR/tech.md")
  [ -f "$STEERING_DIR/structure.md" ] && STRUCTURE_MD=$(cat "$STEERING_DIR/structure.md")
fi
```

When at least one file is non-empty, inject the following **Steering Context** banner into the conversation context before Phase 3. This gives Phase 3 (VCS Deep Dive) and subsequent phases stable product/tech/structure facts without re-reading CLAUDE.md:

```
--- Steering Context ---
[product.md contents — mission, target users, in-scope, out-of-scope]
[tech.md contents — stack, commands, constraints]
[structure.md contents — directory map, inventory, key skills]
--- End Steering Context ---
```

If `.orchestrator/steering/` is absent or all three files are empty, proceed directly to Phase 3 with no banner and no warning. Do not treat missing steering docs as an error.

**See `.orchestrator/steering/{product,tech,structure}.md` for file contents.**

## Phase 2.7: GitLab Portfolio Snapshot (#41)

> Skip this phase if `gitlab-portfolio.enabled` is not `true` in Session Config (default: `false`). Also skip silently when `vault-integration.enabled` is `false` or `vault-integration.vault-dir` is absent.

When active, this phase surfaces a compact portfolio health banner at session-start without writing any file. It runs in **dry-run mode only** — the full write path is reserved for the `/portfolio` command.

### Config check

```bash
PORTFOLIO_ENABLED=$(echo "$CONFIG" | jq -r '."gitlab-portfolio".enabled // false')
VAULT_ENABLED=$(echo "$CONFIG" | jq -r '."vault-integration".enabled // false')
VAULT_DIR=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-dir" // empty')
PORTFOLIO_MODE=$(echo "$CONFIG" | jq -r '."gitlab-portfolio".mode // "warn"')

if [ "$PORTFOLIO_ENABLED" != "true" ] || [ "$VAULT_ENABLED" != "true" ] || [ -z "$VAULT_DIR" ]; then
  exit 0  # silent no-op
fi
if [ "$PORTFOLIO_MODE" = "off" ]; then
  exit 0  # silent no-op
fi
```

### Dispatch

Invoke `scripts/lib/gitlab-portfolio/cli.mjs` in dry-run mode (same orchestrator used by `/portfolio`):

```bash
node scripts/lib/gitlab-portfolio/cli.mjs \
  --vault-dir "$VAULT_DIR" \
  --dry-run \
  --session-start-snapshot   # instructs cli.mjs to emit the compact JSON summary for banner rendering
```

The CLI emits a single-line JSON to stdout:

```json
{ "repos": 16, "openIssues": 42, "critical": 3, "stale": 5, "lastRefresh": "2026-05-16T08:00:00Z" }
```

### Banner rendering

Parse the JSON and render the banner into the Session Overview:

```
📊 Portfolio: 16 repos · 42 open issues · 3 critical · 5 stale (>30d)
    Last refresh: 2026-05-16 08:00 UTC
    Run /portfolio to refresh.
```

### Failure behavior

Governed by the `mode` field from `gitlab-portfolio:` config:

- `warn` (default): if the CLI exits non-zero or emits invalid JSON, append `⚠ partial (<X>/<N> repos failed)` to the banner and continue session-start normally. Do NOT halt.
- `strict`: if the CLI fails, emit a single-line banner `❌ portfolio snapshot failed — run /portfolio for details` into the Session Overview. Do NOT halt session-start — session-start must never be blocked by portfolio failures.
- `off`: silent no-op (already handled by the config check above).

### Performance budget

Must complete within **8 seconds** for portfolios of ≤16 repos (matches the D3 timeout used by vault-staleness and CI-status probes). If the CLI has not exited after 8 seconds, terminate it, skip banner rendering, and emit a single WARN line to `.orchestrator/metrics/sweep.log`:

```json
{"timestamp":"<ISO>","event":"portfolio-snapshot-timeout","detail":{"timeout_ms":8000}}
```

Proceed to Phase 3 without blocking.

### Cross-reference

See `commands/portfolio.md` for the `/portfolio` command (full write path, `--dry-run`, `--repo` single-repo testing).

## Phase 3: VCS Deep Dive (parallel)

> **VCS Reference:** Detect the VCS platform per the "VCS Auto-Detection" section of the gitlab-ops skill.
> Use CLI commands per the "Common CLI Commands" section. For cross-project queries, see "Dynamic Project Resolution."

Using the detected VCS CLI, query (reading `issue-limit` from Session Config, default: 50):

1. **Open issues** — categorize by priority and status labels
2. **Recently closed** — what was done since last session
3. **Milestones** — active sprint status
4. **Open MRs/PRs** — anything waiting for review/merge
5. **Pipeline/CI status** — is CI green?

Group issues by:
- `priority:critical` / `priority:high` — must-address
- `status:ready` — ready to work on
- Session-type relevance (housekeeping tasks vs feature tasks vs deep-work tasks)

## Phase 4: SSOT & Environment Check

1. **SSOT freshness**: for each file in `ssot-files` config, check last modified date. Flag if older than `ssot-freshness-days` (default: 5) days.
2. **Quality baseline**: Run Baseline quality checks per the quality-gates skill. Commands are resolved in this order (issue #183):
   a. `.orchestrator/policy/quality-gates.json` — preferred source when present.
   b. Session Config `test-command` / `typecheck-command` / `lint-command` — fallback.
   c. Hardcoded defaults: `pnpm test --run`, `tsgo --noEmit`, `pnpm lint`.
   Before running, perform a **command-availability check**: for each resolved command, extract the binary (first token) and run `command -v <binary>`. If absent, skip that check and log `⚠ Quality baseline: <binary> not found — skipping <variant>`. Report results but do not block the session.
3. **Pencil design status**: if `pencil` is configured, verify the `.pen` file exists at the configured path. Report: "Pencil design configured at [path] — design-code alignment reviews will run after Impl-Core and Impl-Polish waves." If file not found, warn: "Pencil path configured but file not found at [path]."
4. **Plugin freshness**: Determine the session-orchestrator plugin directory (navigate up from this skill's base directory to the plugin root). Run `git -C <plugin-dir> log -1 --format="%ci"` to get the last commit date. If older than `plugin-freshness-days` (default: 30) days, flag a warning in the Session Overview: `"⚠ Session Orchestrator plugin last updated [N] days ago — consider pulling the latest version."` Non-blocking — present in overview, don't halt.

   Additionally, if `.orchestrator/bootstrap.lock` exists in the current repo, invoke the bootstrap-lock-freshness probe (`scripts/lib/bootstrap-lock-freshness.mjs`) to check lock age and plugin-version drift. Pass `currentPluginVersion` read from `$PLUGIN_ROOT/package.json` so version comparison is live. When severity is `warn` or `alert`, render an additional banner alongside the plugin-freshness warning:
   - **warn** (age 30–89d or non-parseable version mismatch): `"⚠ bootstrap.lock: age=<N>d, plugin-version=<lock-ver> (current=<plugin-ver>) — consider re-running /bootstrap --retroactive to refresh."`
   - **alert** (age ≥90d, unparseable, missing, or major plugin-version mismatch): `"⚠ bootstrap.lock: <message> — re-run /bootstrap --retroactive is strongly recommended."`
   - **info-only version mismatch** (patch or minor version only): `"ℹ bootstrap.lock: plugin-version=<lock-ver> (current=<plugin-ver>) — minor drift only, no action required."`
   - **legacy lock without plugin-version** (soft signal only): `"ℹ bootstrap.lock: lock predates plugin-version field; consider /bootstrap --retroactive to refresh."`

   Additionally, if `.orchestrator/metrics/vault-staleness.jsonl` exists in the current repo (vault-integration enabled), read the most recent line via `scripts/lib/vault-staleness-banner.mjs` (`checkVaultStaleness({repoRoot})`). When `stale_count > 0`, render a banner alongside the bootstrap-lock warning:
   - **warn** (`stale_count > 0`, max `delta_hours <= 48`): `"⚠ vault-staleness: <N> projects stale (max delta: <X>h) — last run <timestamp>."`
   - **alert** (`stale_count > 0`, max `delta_hours > 48`): `"⚠ vault-staleness: <N> projects stale (max delta: <X>h) — Clank-Vault-Sync cron likely broken, see agents/vault#70 fix pattern."`

   The helper returns `null` (silent no-op) when the JSONL is absent, malformed, or `stale_count === 0`. Skip silently in those cases — do not block the session.

   Additionally, if the current repo has a configured `origin` remote and `glab` (GitLab) or `gh` (GitHub) is available, invoke the CI-status probe (`scripts/lib/ci-status-banner.mjs`) via `checkCiStatus({ repoRoot: process.cwd() })`. The helper returns `null` (silent no-op) when no VCS remote, no CLI tool, parse failure, or CLI timeout (8s default). When `result.status === 'red'`, render a banner alongside the bootstrap-lock and vault-staleness warnings:
   - **Red** (`status === 'red'`): `"🚨 CI RED on HEAD (pipeline #<currentPipelineId>) — last green: #<lastGreen.pipelineId> (commit <SHA-7>, <redCount> pipelines ago). Failing job: <failingJobName>"`
   - **Green** or **unknown**: silent (no banner) — informational only.

   The banner is non-blocking — display in the Session Overview, do not halt the session. If `ci-status-banner.mjs` is absent (pre-#369 plugin install), skip silently.

   All banners are non-blocking — display in the Session Overview, do not halt the session. If `bootstrap-lock-freshness.mjs` is absent (pre-#186 plugin install), skip silently.

## Phase 4.5: Resource Health (v3.1.0)

> Skip this phase if `resource-awareness: false` in Session Config.

Reads `.orchestrator/host.json` and runs a live resource snapshot via `resource-probe.mjs`. Computes a `green`/`warn`/`critical` verdict against configurable thresholds (RAM, CPU, concurrent Claude processes, SSH). On `warn`/`critical`, presents an AskUserQuestion prompt to apply the recommended `agents-per-wave` cap or proceed at the user's own risk. The cap is forwarded to session-plan as an in-session override.

**See `phase-4-5-resource-health.md` for full details.**

## Phase 5: Cross-Repo Status (if configured)

For each repo in `cross-repos`:
1. `cd ~/Projects/<repo> && git log --oneline -5 && git status --short`
2. Check for open issues that reference this repo
3. Note any branches that should be merged

## Phase 6: Pattern Recognition

Look across the gathered data for:
- **Recurring patterns**: same types of issues appearing repeatedly → suggest standardization
- **Blocking chains**: issues blocked by other issues across repos
- **Quick wins**: low-effort issues that could be closed alongside main work
- **Staleness**: issues open longer than `stale-issue-days` (default: 30) days without progress → flag for triage
- **Synergies**: issues that share code paths and can be combined

## Phase 6.5: Memory Recall

> Skip this phase if `persistence` config is `false`.

> **Platform Note:** Session memory files at `~/.claude/projects/` are a Claude Code feature. On Codex CLI and Cursor IDE, skip this phase — per-project memory persistence is not available on those platforms.

Surface context from previous sessions:

1. Look for session memory files at `~/.claude/projects/<project>/memory/session-*.md`
2. Read the 2–3 most recent files (by filename date, newest first)
3. Extract relevant context: what was accomplished, what was carried over as unfinished, what patterns or warnings were noted
4. If the `memory-cleanup-threshold` has been reached (number of session-*.md files >= threshold), include a note in the Session Overview: "Consider running `/memory-cleanup` — [N] session memory files accumulated."
5. Incorporate surfaced context into the Session Overview under a **Previous Sessions** subsection (e.g., recent accomplishments, deferred items, recurring patterns)

## Phase 6.6: Project Intelligence

> Skip if `persistence` config is `false` or `.orchestrator/metrics/learnings.jsonl` does not exist. If the canonical file is absent and a legacy `<state-dir>/metrics/learnings.jsonl` still exists, do not read it — direct the user to run `scripts/migrate-legacy-learnings.sh` once to migrate.

Read `.orchestrator/metrics/learnings.jsonl` and surface active learnings (confidence > 0.3, not expired):

1. Apply cap + rank (#88): sort active learnings by `confidence` DESC, then `created_at` DESC as tiebreaker. Slice to the first `learnings-surface-top-n` entries (default 15). Only the surfaced subset is used for the grouping below. Record the full pre-cap active count `M` (confidence > 0.3, not expired) and the surfaced count `N` for the Surface Health section.
2. Group learnings by type:
   - **Fragile files**: "These files have been problematic: [list with confidence scores]"
   - **Effective sizing**: "Previous sessions suggest [N] agents for [scope type]"
   - **Recurring issues**: "Watch for: [issue patterns with frequency]"
   - **Scope guidance**: "Sessions with [N] issues typically [outcome]"

### Surface health

Present a Surface Health block immediately after the per-type grouping, before the Project Intelligence section. Use the values computed in step 1 (`M` = active count pre-cap, `N` = surfaced count = `learnings-surface-top-n`):

1. Compute confidence buckets across the full active set (M entries, confidence > 0.3, not expired):
   - **High** (≥ 0.7): count entries with `confidence >= 0.7`
   - **Medium** (0.5–0.69): count entries with `confidence >= 0.5 and < 0.7`
   - **Low** (< 0.5, above filter threshold): count entries with `confidence > 0.3 and < 0.5`

2. Present the block using this template (substitute `{M}`, `{N}`, `{M - N}`, bucket counts, oldest values, and paths):

   ```
   **Project Intelligence — Surface Health**
   Active learnings: {M}  (high: {high-count} / medium: {med-count} / low: {low-count})
   Surfaced this session: {N}  |  Suppressed: {M - N}
   Oldest surfaced: {oldest-created_at ISO 8601} ({relative-age} days ago)
   Source file: .orchestrator/metrics/learnings.jsonl
   Vault mirror: {vault-dir value from Session Config, or "not enabled" if absent/empty}
   ```

3. Oldest surfaced entry: find the entry among the top-N surfaced learnings with the smallest `created_at` value. Display the raw ISO 8601 timestamp and compute relative age as `floor((current_date - created_at) / 86400)` days.

4. Vault mirror: read `vault-integration.vault-dir` from Session Config (`echo "$CONFIG" | jq -r '."vault-integration"."vault-dir" // empty'`). If the value is absent or empty, print `"not enabled"`.

5. **Conditional advisory** — print the following line only when `{M - N} > {N}` (i.e., suppressed count exceeds surfaced count):
   > ⚠ More learnings are suppressed ({M - N}) than surfaced ({N}). Consider raising `learnings-surface-top-n` in Session Config or running `/evolve review` to prune low-value entries.
   Do NOT print the advisory when `{M - N} <= {N}`.

3. Include a **Project Intelligence** section in the Phase 7 presentation:
   ```
   ## Project Intelligence (from [N] learnings)
   - Fragile: [files] (confidence: [X])
   - Sizing: [recommendation]
   - Watch: [recurring issues]
   - Scope: [guidance]
   ```
   If no active learnings exist, display: "No project intelligence yet — learnings accumulate after 2+ sessions."

4. **Effectiveness analysis** (requires 5+ sessions in `sessions.jsonl`):

   > Skip if `.orchestrator/metrics/sessions.jsonl` does not exist or has fewer than 5 entries.

   Read `.orchestrator/metrics/sessions.jsonl` and compute:
   - **Completion rate trend**: average `effectiveness.completion_rate` over last 5 sessions
     - If < 0.6: "Completion rate is [X]%. Consider reducing scope or using deep sessions."
     - If > 0.9: "Consistently high completion. Current scope sizing works well."
   - **Discovery probe value**: for sessions with `discovery_stats`, check each category in `by_category`:
     - If `findings == 0` across 3+ sessions: "Probe category '[X]' has produced no findings in [N] sessions. Consider excluding via `discovery-probes` config."
     - If `findings > 5` consistently but issues are rarely created from that category: "Probe category '[X]' generates many findings ([avg]) but few lead to issues. Consider raising `discovery-severity-threshold` or `discovery-confidence-threshold`."
   - **Carryover pattern**: if `effectiveness.carryover / planned_issues > 0.3` across 3+ sessions:
     "High carryover rate ([X]%). Consider: smaller scope, longer sessions (deep), or splitting across sessions."

   If fewer than 5 sessions exist: "Effectiveness analysis: not enough data yet ([N]/5 sessions)."

   Include effectiveness insights in the **Project Intelligence** section of the Phase 7 presentation:
   ```
   ## Project Intelligence (from [N] learnings, [M] sessions)
   - Fragile: [files] (confidence: [X])
   - Sizing: [recommendation]
   - Watch: [recurring issues]
   - Scope: [guidance]
   - Effectiveness: [completion rate trend, probe value, carryover pattern]
   ```

## Phase 7: Research (session type dependent)

> **Note:** Implementation-specific research (library APIs, best practices for specific code changes) is deferred to session-plan, which knows the exact scope. Session-start focuses on state analysis.

**For `feature` and `deep` sessions:**
- Check SSOT files for established patterns relevant to the recommended focus
- Review any tech stack changes since last session (dependency updates, new tooling)
- ALWAYS verify current state in actual code — never assume based on memory or SSOT alone

**For `housekeeping` sessions:**
- Focus on git cleanup, documentation currency, CI health
- Skip deep research — prioritize operational tasks
- Run token efficiency check: `bash "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/token-audit.sh"` and include findings in Session Overview. Flag any HIGH/WARN items as recommended housekeeping tasks.

## Phase 7.5: Mode-Selector Pre-Pass (Epic #271 Phase B-2)

> Skip this phase if `persistence` config is `false`, or if the entire Phase 6.6 block was skipped.
> This is the **first wired invocation point** of `selectMode` (previously documented as "None wired" in `skills/mode-selector/SKILL.md` — Phase C `/autopilot` is the second, reserved for #277).

Run immediately before Phase 8 so the Mode-Selector recommendation can influence the AUQ option ordering.

Invokes `buildLiveSignals` (single SSOT for the signals shape) then `selectMode(signals)` (pure function, never throws). Renders a `📊` banner when confidence ≥ 0.5, an informational banner when < 0.5, and no banner when confidence = 0.0. High-confidence output pre-selects an AUQ option in Phase 8 — see Step 4 AUQ Option Ordering Protocol. After Phase 8 collects the user's mode choice, writes a `mode-selector-accuracy` learning to `learnings.jsonl` (Step 6, Phase B-4). All failure paths are graceful no-ops logged to `sweep.log`. See `phase-7-5-mode-selector.md` § Context-Pressure Annotation (#332) for context-pressure handling.

**See `phase-7-5-mode-selector.md` for full details.**

## Phase 8: Structured Presentation & Q&A

Read `presentation-format.md` in this skill directory for the output structure, templates, and AskUserQuestion examples.

Present your findings following that structure. Key rules:
- **MANDATORY: Use a structured choice flow** — AskUserQuestion on Claude Code, numbered Markdown options on Codex/Cursor
- Always include your recommendation as the first option with "(Recommended)" in the label

### Phase 8.5: Express Path Evaluation (#214)

After the user confirms session type and scope, evaluate whether the Express Path applies. Activation requires ALL three: `express-path.enabled: true` in Session Config (default: `true` — when `express-path.enabled: false`, this evaluation is skipped entirely and the normal 5-wave session-plan flow runs), session type `housekeeping`, and scope ≤ 3 sequential issues. The 13 prior coordinator-direct sessions in `CLAUDE.md` (or `AGENTS.md` on Codex CLI; 2026-04 series) were all running this pattern implicitly — this phase codifies what was already proven to work.

When all conditions are met, emits the banner:
```
Express path activated — <N> tasks, coordinator-direct, no inter-wave checks.
```
Then executes tasks coordinator-direct (bypassing session-plan and wave-executor) and logs a Deviations entry in STATE.md. Silent no-op when any condition fails — proceeds normally to Phase 9.

**See `phase-8-5-express-path.md` for full details.**

## Phase 9: Handoff to Session Plan

After user alignment:
1. Invoke the **session-plan** skill with the agreed scope
2. The session-plan skill will decompose tasks into waves and present the execution plan

## Anti-Patterns

- **DO NOT** skip Phase 1 and jump straight to analysis — Session Config drives everything, missing it means wrong defaults
- **DO NOT** present raw data dumps without recommendations — the user expects opinionated analysis, not a wall of text
- **DO NOT** assume issue status from titles or labels alone — always check the actual VCS API for current state
- **DO NOT** run blocking quality gates (Full Gate) during session-start — that's the Quality wave's job. Baseline checks (non-blocking, informational) in Phase 4 are fine.

## Critical Rules

- **NEVER make assumptions** about code state based on memory or docs — always verify in actual files
- **NEVER skip the Q&A phase** — the user MUST confirm direction before wave planning
- **ALWAYS use `run_in_background: false`** for parallel subagent work — wait for completion
- **ALWAYS check `.env` or `.env.local`** for VCS host, API keys, and service URLs
- **ALWAYS present options with pros/cons and a clear recommendation** — never just list facts
- **ALWAYS update VCS issue status** when claiming work — use the issue update command per the "Common CLI Commands" section of the gitlab-ops skill
- **For Pencil designs**: use the `filePath` parameter, work only on new designs, treat completed ones as done
- **For cross-repo work**: always check the actual state of related repos, don't assume from memory

## Sub-File Reference

| File | Purpose |
|------|---------|
| `soul.md` | Identity and communication principles |
| (inline) Phase 1.2 | Session Lock Acquire — `acquire()` call, active/stale/cross-host AUQ flows, `forceAcquire()` on user consent, deviation note wiring |
| `presentation-format.md` | Phase 8 output templates and AskUserQuestion examples |
| `phase-2-5-docs-planning.md` | Phase 2.5 full procedural body — docs-orchestrator config, audience detection, AUQ confirmation, result block emission, non-overlap rules |
| (inline) Phase 2.6 | Steering docs gate + load — reads `.orchestrator/steering/{product,tech,structure}.md`; silent no-op when directory absent |
| (inline) Phase 2.7 | GitLab Portfolio Snapshot — dry-run aggregation banner; gated on `gitlab-portfolio.enabled: true` + `vault-integration.enabled: true`; dispatches `scripts/lib/gitlab-portfolio/cli.mjs --dry-run`; 8s timeout; never blocks session-start |
| `phase-4-5-resource-health.md` | Phase 4.5 full procedural body — resource probe, adaptive thresholds table, AUQ presentation, session-plan cap handoff |
| `phase-7-5-mode-selector.md` | Phase 7.5 full procedural body — buildLiveSignals, selectMode invocation, banner rendering, AUQ ordering protocol, graceful no-op rules, accuracy learning write |
| `phase-8-5-express-path.md` | Phase 8.5 full procedural body — activation conditions, banner, coordinator-direct execution, STATE.md logging, condition examples table |
