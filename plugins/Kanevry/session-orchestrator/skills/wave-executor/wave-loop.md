# Wave Execution Loop

> Sub-file of the wave-executor skill. Read by the coordinator during wave dispatch.
> For pre-execution setup, session type behavior, and error recovery, see `SKILL.md`.
> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). Wherever this loop mentions a project's `CLAUDE.md`, the alias rule applies.

## Wave Execution Loop

For each wave, resolve its assigned role(s) from the session plan's role-to-wave mapping:

**Empty waves:** If the session plan shows a wave with 0 agents (role had no tasks), skip it entirely:
1. Log in progress update: `## Wave [N] ([Role]) — Skipped (no tasks)`
2. Update STATE.md: increment `current-wave`, add to Wave History: `### Wave N — [Role] (skipped, no tasks)`
3. Proceed to next wave immediately
4. Do NOT write wave-scope.json for skipped waves

### 0.5. Pre-Dispatch Resource Gate (#193)

Before dispatching agents, the coordinator runs a resource gate to decide whether the wave should proceed as planned, reduce its agent count, or escalate to coordinator-direct. Gated on `$CONFIG["resource-awareness"]` (default: true).

```js
import {evaluateWaveResourceGate, formatGateReport} from "scripts/lib/wave-resource-gate.mjs";

const gate = await evaluateWaveResourceGate({
  config: $CONFIG,
  plannedAgents: <wave's planned agent count>,
  waveRole: "<Discovery|Impl-Core|Impl-Polish|Quality|Finalization>"
});
```

**Act on the decision:**

| Decision | Coordinator action |
|----------|---------------------|
| `proceed` | Dispatch at `gate.agents` (= `plannedAgents`). Include `gate.reasons` in the wave progress update (informational). |
| `reduce` | Dispatch at `gate.agents` (< `plannedAgents`). Log the reduction as a deviation in STATE.md. Include `gate.reasons` in the wave progress update. |
| `coordinator-direct` | Do NOT dispatch subagents. Coordinator executes the wave's tasks directly. Log as a deviation in STATE.md. Continue to `### 1. Dispatch Agents` only for stagnation-pattern detection wording — the section's execution is skipped. |

Reasons MUST appear in the wave's progress update under a "Resource gate:" bullet. Measurements (RAM free GB, CPU %, concurrent sessions) appear verbatim so the user can trust the decision.

Probe failures never block a wave — the gate returns `proceed` with a "probe failed (ignored)" reason and the wave continues at the planned count. A config without `resource-thresholds` (legacy pre-#166) returns `proceed` with `"resource-thresholds missing from config — gate skipped"` — a defensive fallback so the gate never crashes the dispatch loop.

**STATE.md deviation contract (#193):** when the gate returns `reduce` or `coordinator-direct`, append a single timestamped entry to `## Deviations` in `<state-dir>/STATE.md`. Use this exact format so future sessions and the evolve skill can mine for hardware-pattern learnings:

```
- [<ISO 8601 UTC>] Wave N resource-gate <reduce|coordinator-direct>: <gate.reasons[0]>. Measurements: ramFreeGb=<N>, cpuLoadPct=<N>, concurrentSessions=<N>. Planned agents=<M>, dispatched=<gate.agents>.
```

Skip the deviation entry on `proceed`, even when `concurrentSessions` warns — informational reasons belong in the wave progress update, not in deviations.

---

### 1. Dispatch Agents

When `worker-pool.enabled: true` in Session Config, dispatch via `runWavePool()` from `scripts/lib/wave-executor/pool.mjs` with `maxParallel = worker-pool.max-parallel || agents-per-wave`. Else fall back to single-message parallel Agent() dispatch.

**Worker-pool timing note:** when `worker-pool.enabled: true`, per-agent start and end times are recorded individually in subagents.jsonl as workers pull from the cursor at different moments. Wave-level timings (for progress updates and metrics) are computed as first-worker-start to last-worker-finish, not as a uniform fan-out timestamp.

Use the **Agent tool** to dispatch all agents for this wave IN PARALLEL in a SINGLE message.

Read each wave's dispatch metadata from the session plan header (e.g., `(4 agents, parallel, isolation: worktree)`). When the plan specifies `isolation`, use it verbatim. When the plan does not specify, resolve the effective value via `resolveIsolation({ agentCount, sessionType, collisionRisk, configIsolation })` from `scripts/lib/wave-sizing.mjs` — the graduated default (#194) replaces the previous session-type-only switch. Pass the resolved value to each Agent() tool call per `circuit-breaker.md` (omit the parameter when resolved to `none`).

After resolving `isolation`, compute the wave's enforcement via `resolveEnforcement({ isolation, configEnforcement })` (same module) and write it into `wave-scope.json` under `enforcement`. When isolation resolves to `none`, enforcement auto-promotes from `warn` → `strict` unless the user explicitly set `off` — this ensures the scope hook is hard, not informational, when worktree-level isolation is absent.

Before dispatching, verify the wave's agent count does not exceed `$CONFIG.agents-per-wave` — if it does, warn the user and request plan revision.

#### Pre-Dispatch New-Directory Detection (#243)

> **Motivation:** Claude Code's worktree merge-back fails silently when an agent creates a new directory inside the worktree — the new directory is not copied back to the coordinator's working tree (learning `agent-tool-worktree-no-sync-regression`, conf 0.90, 3rd-consecutive observation). The fix is to detect this condition BEFORE resolving isolation and force `isolation: 'none'` so worktree is never used for those agents, eliminating the regression rather than trying to recover from it (learning `wave3-isolation-none-dispatch`, conf 0.75, proven-pattern).

Run this step only when `configIsolation` (read from the Execution Config or `$CONFIG.isolation`) is `'auto'`. If the user explicitly set `configIsolation: 'none'`, skip entirely — user override already achieves the desired outcome. If the user explicitly set `configIsolation: 'worktree'`, honour it but emit an ⚠ warning (see branch 4 below).

```js
import fs from 'fs';
import path from 'path';

// configIsolation: resolved from Execution Config or $CONFIG.isolation (default 'auto')
// agentSpecs: array of agent specifications from the session plan for this wave
//   Each spec has: { subagent_type, fileScope: string[] }  (fileScope = "Files:" entries)

function detectNewDirAgents(agentSpecs, repoRoot) {
  // Returns the count of agents whose scope includes at least one new (non-existent) directory.
  let newDirCount = 0;
  for (const agent of agentSpecs) {
    const willCreateNewDir = (agent.fileScope ?? []).some((scopePath) => {
      // Resolve relative to repo root; handle globs by taking the literal dirname.
      const resolved = path.resolve(repoRoot, scopePath);
      const dir = path.dirname(resolved);
      return !fs.existsSync(dir);
    });
    if (willCreateNewDir) newDirCount++;
  }
  return newDirCount;
}

const repoRoot = process.cwd(); // coordinator CWD restored by Step 2.0 before this wave
const newDirAgentCount = detectNewDirAgents(agentSpecs, repoRoot);

// Branch 1 — no new directories detected, configIsolation: 'auto' → normal resolution path
if (newDirAgentCount === 0 && configIsolation === 'auto') {
  // Proceed to resolveIsolation() unchanged.
}

// Branch 2 — new directories detected, configIsolation: 'auto' → force isolation to 'none'
if (newDirAgentCount > 0 && configIsolation === 'auto') {
  configIsolation = 'none'; // override BEFORE calling resolveIsolation()
  console.warn(
    `⚠ Pre-dispatch: ${newDirAgentCount} agent(s) in this wave will create new directories ` +
    `— isolation forced to 'none' per learning agent-tool-worktree-no-sync-regression (conf 0.90). ` +
    `Reason: Claude Code worktree merge-back fails on new directories (issue #243).`
  );
  // NOTE: resolveEnforcement() will auto-promote 'warn' → 'strict' because isolation resolves
  // to 'none'. The scope hook therefore becomes a hard barrier (not informational) for this wave —
  // document this in the wave progress update so the operator understands enforcement escalated.
}

// Branch 3 — configIsolation: 'none' set explicitly by user → skip detection entirely
if (configIsolation === 'none') {
  // User override respected. No change needed.
}

// Branch 4 — configIsolation: 'worktree' set explicitly by user → honour but warn if new dirs exist
if (configIsolation === 'worktree' && newDirAgentCount > 0) {
  console.warn(
    `⚠ Pre-dispatch: ${newDirAgentCount} agent(s) will create new directories AND ` +
    `isolation is explicitly set to 'worktree'. ` +
    `Known regression: Claude Code merge-back silently drops new directories (issue #243). ` +
    `Override configIsolation to 'none' to avoid data loss.`
  );
  // Proceed with worktree as requested — user accepted the risk.
}

// Branch 5 — configIsolation: 'auto', newDirAgentCount === 0 → no-op (same as Branch 1)
// Explicit for clarity; covered by Branch 1 above.
```

After running this detection block, call `resolveIsolation({ agentCount, sessionType, collisionRisk, configIsolation })` with the (possibly overridden) `configIsolation`. Then call `resolveEnforcement({ isolation, configEnforcement })` as normal — when isolation resolved to `'none'` via Branch 2, enforcement auto-promotes `warn` → `strict`, which MUST be noted explicitly in the wave progress update.

#### Agent-Type Resolution

Each agent in the session plan specifies a `subagent_type`. Use that value directly when dispatching:

```
For each agent in this wave:
  Agent({
    description: "<3-5 word summary>",
    prompt: "<COMPLETE task context including:
      - What to do (specific, measurable)
      - Which files to read/modify (exact paths)
      - Acceptance criteria (how to verify done)
      - Relevant patterns from <state-dir>/rules/
      - VCS issue reference if applicable
      - What NOT to touch (other agents' files)
      >",
    subagent_type: "<from session plan>",   // resolved agent type
    run_in_background: false   // CRITICAL: always false — wait for completion
  })
      - Turn budget and status reporting: "You have a maximum of [maxTurns] turns for this task. If you cannot complete within this budget, report STATUS: partial with what was accomplished and what remains. At the end of your work, report STATUS: done (all acceptance criteria met) or STATUS: partial (some criteria unmet — list which ones)."
```

#### Pre-Dispatch Grounding Injection (#85)

Before dispatching each agent, prepend a line-numbered GROUNDING block to its prompt for any file in the agent's scope that has recent edit-format-friction history. This helps the agent reference edits by line number instead of re-matching exact character spans, reducing Edit-tool retry loops.

**Gate:** `$CONFIG."grounding-injection-max-files" > 0` AND `$CONFIG.persistence == true`. When either condition is false, skip the entire step.

**Per-agent scope** (not per-wave): each agent's file scope comes from its specification in the session plan — the same source used for computing the wave's `allowedPaths` union (see `## Scope Manifest` § 3). An agent with narrow scope gets grounding only for files it will touch.

**Invocation:** for each agent about to be dispatched, call:

    AGENT_FILES="$(printf '%s\n' "${agent_file_scope[@]}")" \
    SESSIONS_JSONL=".orchestrator/metrics/sessions.jsonl" \
    EVENTS_JSONL=".orchestrator/metrics/events.jsonl" \
    MAX_FILES="$(echo "$CONFIG" | jq -r '."grounding-injection-max-files"')" \
    SESSION_ID="<session_id>" WAVE="$wave_num" AGENT_TYPE="<subagent_type>" \
    PERSISTENCE="$(echo "$CONFIG" | jq -r '.persistence')" \
    bash "$PLUGIN_ROOT/scripts/compute-grounding-injection.sh"

Capture stdout as `$GROUNDING_BLOCK`. If empty, dispatch the agent unchanged (legacy behavior).

**Prompt assembly:** when `$GROUNDING_BLOCK` is non-empty, prepend to the agent prompt:

    <GROUNDING_BLOCK>

    Use line numbers above to describe edits precisely instead of re-matching character spans. If a line has changed since this snapshot, re-read the file before editing.

    ---

    <original prompt>

The helper emits one `orchestrator.grounding.injected` event per injected file to `.orchestrator/metrics/events.jsonl` (routed through `scripts/emit-event.mjs` → the canonical `emitEvent()` path). The helper never returns non-zero; any failure (missing jq, missing events.jsonl, unreadable file) results in silent no-op so wave dispatch is never blocked.

**Fallback for agents without explicit file scope:** if the session plan's agent specification does not list a "Files:" scope for an agent, fall back to the wave-level `allowedPaths` (from `wave-scope.json`). If that is also empty, skip injection for that agent.

**Relationship to `### 3c. File-level grounding`:** this pre-dispatch feature is DIFFERENT from the post-wave file-level grounding check. Pre-dispatch grounding injects file content into agent prompts (prevents friction). Post-wave grounding verifies agents stayed within their planned scope (detects scope creep). The two features share no code and run at different times.

#### Pre-Dispatch Untracked-Overlap Check (#180)

Claude Code's Agent tool with `isolation: "worktree"` syncs the agent's worktree back into the coordinator's working tree on completion. If the coordinator holds untracked files inside the agent's scope, the sync silently overwrites them — observed as data loss in the 2026-04-19 deep-drift-check session (4 files, ~700 LoC wiped). See issue #180.

**Apply this check only when dispatching with `isolation: "worktree"`.** For `isolation: "none"` or coordinator-direct execution, skip — there is no merge-back to worry about.

For each worktree-isolated agent about to be dispatched:

```js
import { checkUntrackedOverlap } from '$PLUGIN_ROOT/scripts/lib/pre-dispatch-check.mjs';

const result = checkUntrackedOverlap({
  scope: agentFileScope,        // same array used for `allowedPaths`
  cwd: process.cwd(),
  mode: 'warn',                 // 'warn' (default) | 'block' | 'off'
});

if (result.decision === 'block') {
  // Refuse dispatch. Report result.message to the user.
  // Ask: commit the files, stash them, or rerun with mode=warn to acknowledge.
} else if (result.decision === 'warn') {
  // Print result.message to the wave progress update.
  // Dispatch proceeds, but the coordinator has an audit trail if data loss occurs.
}
```

The helper is stdlib-only and cross-platform. `mode=block` is recommended when the coordinator holds uncommitted work of non-trivial size in the agent's scope — it trades a friction prompt for the guarantee that the merge-back cannot silently overwrite. `mode=warn` keeps the historical behavior and simply records the risk. `mode=off` short-circuits entirely.

This is a downstream backstop: the underlying worktree merge-back strategy lives in the Claude Code harness and is outside this plugin's control. The correct fix (preserve untracked coordinator files during merge-back) must come upstream. Until then, this check is the only defense.

#### Pre-Dispatch Coordinator Snapshot (#196)

Before dispatching agents for this wave, checkpoint any uncommitted coordinator work as a git stash snapshot. This is a backup — it does NOT touch the working tree and does NOT block dispatch on failure.

**Gate:** `$CONFIG.persistence == true`. When `persistence: false`, skip this step entirely.

```js
import { saveSnapshot } from '$PLUGIN_ROOT/scripts/lib/coordinator-snapshot.mjs';

const snap = await saveSnapshot({
  sessionId: '<session_id>',
  waveN: <wave_num>,
  label: 'pre-dispatch',
});

if (!snap.ok) {
  // Non-fatal — log the error in the wave progress update but do not block.
  console.warn(`coordinator-snapshot: snapshot failed (non-fatal): ${snap.error}`);
}
// snap.skipped === true when the working tree is clean; also fine, dispatch continues.
```

The snapshot is stored under `refs/so-snapshots/<sessionId>/wave-<N>-pre-dispatch`. It survives Claude process termination (unlike memory-only state) and is cleaned up by session-end on clean close (see session-end/SKILL.md). Orphaned snapshots from crashed sessions are reclaimed by `gcSnapshots({olderThanDays: 14})`.

See issue #196 for the full rationale. This is complementary to the untracked-overlap check above (#180 is scope-level detection; this is working-tree-level backup).

#### Pre-Dispatch: Frontmatter-Guard Injection (#328)

Before constructing each agent's prompt, decide if the schema snippet must be injected:

1. Compute task vault-scope: `import { detectVaultTaskScope } from 'scripts/lib/frontmatter-guard.mjs'`. Pass the agent's task description + file scope (paths the agent is allowed to write).
2. **If vault-scoped (returns `true`):**
   a. Call `readVaultSchema()` from the same module.
   b. If the schema read returned non-null, call `generateFrontmatterSnippet(schema)` to get a Markdown block.
   c. Prepend the block to the agent's prompt under a clear separator:

      ```
      <FRONTMATTER-GUARD>
      <generated snippet>
      </FRONTMATTER-GUARD>

      <original prompt>
      ```
   d. If `readVaultSchema()` returned `null` (schema source absent), emit stderr WARN `Frontmatter-guard: schema source missing at <path> — agent prompts will not include schema enums`. Continue dispatch without injection (do NOT block).
3. **If not vault-scoped:** dispatch as today, no injection.

Performance note: `readVaultSchema()` caches by file mtime, so repeated calls within a wave are free. The schema read happens at most once per wave-executor run.

Behaviour change: agents writing vault notes now receive the canonical schema enums + per-type examples directly in their prompt context. This eliminates the agent-guessing failure class documented in #328.

#### Structured Reasoning (STATE:/PLAN:) — opt-in via `reasoning-output: true` (#79)

When `$CONFIG.reasoning-output` is `true`, append the following block to every agent prompt. The pattern is adapted from the BitGN PAC Agent's Soft-SGR: short structured transparency lines before tool invocations, without forcing structured output. Leave the block OUT when the flag is `false` (default) — this preserves exact legacy prompt behavior.

```
## Reasoning format

Before every meaningful tool call, emit two single-line markers so the coordinator can trace your thinking:

  STATE: <one-line summary of what you currently know about the task — files read, constraints, blockers>
  PLAN:  <one-line summary of what you are about to do and why>

Rules:
- Keep each line under ~160 characters. Do not nest markdown or code blocks inside these lines.
- Emit them together, STATE first then PLAN, immediately before the tool call they describe.
- Skip them for trivial read-back tool calls (e.g., re-reading a file you just wrote). Do not spam them.
- These markers DO NOT replace your normal text output — they supplement it. Continue writing normal progress updates.
```

**Resolution chain** (if the plan does not specify `subagent_type` for an agent):

1. **Discovery waves** → `"Explore"` (always, read-only)
2. **Quality review** → `"session-orchestrator:session-reviewer"` (always)
3. **Impl-Core / Impl-Polish / Quality (test-writing)** → check in order:
   a. Project agent matching the task domain (e.g., `"database-architect"` for DB tasks)
   b. Plugin agent (e.g., `"session-orchestrator:code-implementer"`)
   c. `"general-purpose"` (final fallback)

   > **Docs-role dispatch (A3):** `docs-writer` is the canonical first-class agent for Docs-role tasks (audience-split documentation generation per `skills/docs-orchestrator/SKILL.md`). It flows through step 3a naturally: when the session plan specifies `subagent_type: "docs-writer"` (project-level) or `subagent_type: "session-orchestrator:docs-writer"` (plugin-level), the resolution chain matches at step 3a without a separate branch. Cross-reference: `agents/docs-writer.md` (agent definition), `skills/docs-orchestrator/SKILL.md` (execution protocol and hook points). No new resolution branch is required — 3a handles it.

4. **Finalization** → direct execution (no subagent needed)

> **How to detect project agents:** The session plan's "Agent Registry" section lists all discovered agents. If an agent name does NOT contain a colon (`:`), it's a project-level agent. If it contains `session-orchestrator:`, it's a plugin agent.

**CRITICAL: `run_in_background: false`** — You MUST wait for ALL agents to complete before proceeding. NEVER use `run_in_background: true` during wave execution. Dispatch all agents in a single message for maximum parallelism, then wait.

#### Platform-Specific Dispatch

**Claude Code:** Use the `Agent` tool as shown above. Agent types follow the resolution chain above.

**Codex CLI:** Codex uses typed agent roles defined in `.codex-plugin/agents/`. Map wave roles to Codex agents:
- **Discovery** waves → `explorer` agent (read-only)
- **Impl-Core / Impl-Polish** waves → `wave-worker` agent (workspace-write), or project-specific agents if defined in the platform's agents directory (`.claude/agents/`, `.codex/agents/`, or `.cursor/agents/`)
- **Quality** review → `session-reviewer` agent (read-only)
- **Finalization** → direct execution (no subagent needed)

Dispatch via Codex's multi-agent system — describe the task and specify the agent role. The prompts remain identical across platforms.

**Cursor IDE:** No Agent() tool available. Execute wave tasks sequentially within the current Composer session:
1. For each task in the wave, implement it fully (you are both coordinator AND implementer)
2. After completing each task, report status inline
3. Run incremental quality checks after all tasks in the wave complete
4. Proceed to the next wave

The `agents-per-wave` config is ignored on Cursor — all work is sequential. Session-reviewer dispatch is deferred to session-end (Phase 1.8).

> **Timeout note:** Agent timeout is controlled by `maxTurns` from `circuit-breaker.md`, not by a time-based timeout. Claude Code's built-in turn limit provides the safety net. There is no need to set explicit time-based timeouts on agent dispatch.

### 2. Review Agent Outputs

**Step 2.0 — Restore coordinator CWD (#219):** BEFORE reading any agent output or running any quality check, restore the coordinator's working directory. Claude Code's `Agent` tool with `isolation: "worktree"` `chdir()`s into each worktree internally and does NOT restore it on agent return. Subsequent Edit/Write/Bash calls would silently route to whichever worktree's tree CWD last drifted into.

```js
import { restoreCoordinatorCwd } from '$PLUGIN_ROOT/scripts/lib/worktree.mjs';

const cwd = await restoreCoordinatorCwd();
if (cwd.restored) {
  console.warn(`wave-executor: restored coordinator CWD from ${cwd.from} → ${cwd.to}`);
  // Include this line in the wave progress update so the coordinator has an audit trail.
}
```

Run this step for every wave, regardless of isolation setting — it is a no-op when CWD never drifted.

After ALL agents in the wave complete:

1. **Read each agent's result** carefully
1a. **Validate agent output schema** (if `output-schema-validation.enabled: true` in Session Config — default `false`):

   For each completed agent record, call `validateAgentOutput({ agentName, raw })` from `scripts/lib/agent-output-schema.mjs` where `agentName` is the kebab-case agent name and `raw` is the agent's full return text.

   Handle the four result modes:

   - **`mode: 'validated', ok: true`** — silent. Set `schema_status: 'ok'` on the agent record in `subagents.jsonl`.
   - **`mode: 'validated', ok: false`** — schema violation. Annotate the agent record with `schema_violation: true` and `schema_errors: [...]`. Then:
     - Under `enforce: warn` (default): log the violation in the wave progress update and continue. The wave is NOT blocked.
     - Under `enforce: strict`: surface the violation as a wave-blocking finding. Halt further agent processing and report to the coordinator before proceeding to the conflict check.
     - Under `enforce: off`: record the violation in `subagents.jsonl` for diagnostics (`schema_violation: true`, `schema_errors: [...]` are set on the agent record) but do NOT emit a log line in the wave progress update and do NOT block the wave. This is identical to `warn` minus the in-wave noise — forensic data is preserved; operator output is silenced.
   - **`mode: 'parse-error'`** — two distinct diagnostic sub-cases collapsed into one mode for backward-compat; either:
     - **parse-error (no-block)**: agent output contains no fenced ```json block at all. Common backward-compat case for agents that predate the schema contract.
     - **parse-error (bad-json)**: a fenced ```json block exists but the block fails `JSON.parse`. Indicates an agent-side serialisation bug — more interesting than no-block from a diagnostic standpoint, and the operator may want to follow up.

     Both sub-cases share the same recovery: log a warning in the wave progress update, set `schema_status: 'parse-error'` on the agent record in `subagents.jsonl`, and do NOT block the wave (#474 LOW-8 distinguishes the two so future tooling can route diagnostics differently per sub-case).
   - **`mode: 'schema-error'`** — the fenced ```json block parses cleanly but the parsed object fails AJV validation against the agent's declared `output-schema:`. This is a stronger signal than `parse-error`: the agent emitted JSON, but the shape diverged from its declared contract. Treat the same way as `validated, ok: false` under the configured `enforce` level (`warn` / `strict` / `off`) so the violation is recorded with `schema_violation: true` and `schema_errors: [...]`. Note: the legacy `validateAgentOutput()` returns `'validated', ok: false` for this case today — `schema-error` is the spec-level name (per #474 LOW-8) for the same condition, kept distinct from `parse-error` so the diagnostic log can route differently.
   - **`mode: 'unvalidated'`** — the agent has no declared `output-schema:` frontmatter. Silent skip (backward-compat path; as of #449 all 11 plugin agents are enrolled, but third-party agents installed via marketplace plugins may not be).

   Reference: agent contract at `agents/code-implementer.md`; runtime module at `scripts/lib/agent-output-schema.mjs::validateAgentOutput`.

2. **Check for conflicts**: did two agents modify the same file? → manual merge needed
3. **Check for failures**: did any agent report errors or blockers?
3a. **Apply stagnation patterns** (per agent): review each agent's tool-call sequence against the three patterns in `circuit-breaker.md` § Stagnation Patterns — Pagination Spiral, Turn-Key Repetition, Error Echo. Mark each agent STAGNANT/SPIRAL/FAILED accordingly; recovery feeds into step 3 (Adapt Plan). Two different agents reading the same file is coordination, not stagnation.

**Stagnation event-write** (gated on `persistence: true`): when any stagnation pattern fires for an agent during this step, append one line to `.orchestrator/metrics/events.jsonl` using shell `>>` (atomic for lines under PIPE_BUF):

```json
{"event":"stagnation_detected","timestamp":"<ISO 8601 UTC>","session":"<session_id>","wave":N,"agent":"<subagent_type>","pattern":"pagination-spiral|turn-key-repetition|error-echo","error_class":"<taxonomy value — omit field entirely if pattern is not error-echo>","file":"<relative path from project root, or null if not applicable>","occurrences":N}
```

Assign `error_class` using the taxonomy defined in `circuit-breaker.md` § "3. Error Echo" → Error-Class Taxonomy. For non-error-echo patterns, omit the `error_class` field. Paths are relative to the project root. `occurrences` is the count of pattern repetitions detected (minimum 3 per the trigger threshold).

3b. **Worktree base-ref freshness check (#195)**: For each agent dispatched with `isolation: "worktree"` in this wave, verify that the coordinator has not advanced `main` past the worktree's base commit before the merge-back copies files. Call `checkWorktreeBaseRefFresh({ suffix, targetBranch: 'main', agentScope, cwd })` from `scripts/lib/worktree-freshness.mjs`:

- `decision: 'pass'` (baseSha === currentSha) → proceed with merge-back.
- `decision: 'warn'` (main advanced, no agent-scope overlap) → proceed, but log the drift in the wave progress update so the coordinator can audit. This is typically benign — coordinator commits to unrelated files.
- `decision: 'block'` (main advanced, drift files overlap the agent's scope) → **STOP** the merge-back for this agent. The agent's copy would silently overwrite coordinator-committed work (this is exactly the 2026-04-20 07:30 and 09:00 regression). Either: (a) run `git diff main..wt-branch -- <overlap-files>` and manually reconcile before committing, or (b) ask the user whether to rebase the agent's branch onto current main and retry the merge. Do NOT proceed automatically.
- `decision: 'no-meta'` (meta file missing or corrupted) → log a warning and fall back to manual diff review before commit. Missing meta usually means the worktree was created by an older plugin version; corrupted meta warrants an issue.

Skip the check entirely for agents dispatched with `isolation: "none"` — there is no worktree merge-back in that path.

Log every non-`pass` result as an event to `.orchestrator/metrics/events.jsonl` (gated on `persistence: true`):
```json
{"event":"freshness_check","timestamp":"<ISO 8601 UTC>","session":"<session_id>","wave":N,"agent":"<description>","suffix":"<worktree suffix>","decision":"pass|warn|block|no-meta","drift_commits":N,"overlap_files":M}
```

3c. **File-level grounding** (per wave, informational, gated by `grounding-check: true` — default): compute Planned (union of agent file scopes for this wave from the dispatch metadata) vs Actual (files actually edited by this wave's agents). Report scope creep (Actual ∖ Planned) and incomplete coverage (Planned ∖ Actual). Does NOT block the next wave. Reuses the semantics defined in `skills/session-end/plan-verification.md` § 1.1a — the session-end variant computes against `$SESSION_START_REF`, the per-wave variant computes against the wave's pre-dispatch HEAD snapshot. Not to be confused with pre-dispatch grounding injection (§ Pre-Dispatch Grounding Injection above): that feature is per-agent and runs before dispatch to prevent friction; this check is per-wave and runs after dispatch to detect scope creep. Skip the entire check when `grounding-check: false`.
4. **Run incremental verification** (per the quality-gates skill, based on the wave's role):

   **Shared-lib touch auto-promotion (#555 FL-3)** — before selecting the role-based gate variant below, check whether this wave touched files under `scripts/lib/`, `hooks/`, or `.husky/`. If so, auto-promote the inter-wave gate from Quality-Lite (Incremental) to Full Gate (typecheck + test + lint). Rationale: an Impl wave that touches shared code has a wider blast radius than the agent can predict — deep-1647 inter-wave 3→4 caught 2 such regressions only because the Lite step happened to run the full test suite. Auto-promotion makes that coverage deterministic without imposing per-session cost on waves that don't touch shared code (W1-D5 chose Option B over the always-full Option A on this exact tradeoff).

   ```js
   import { detectSharedLibTouch } from '$PLUGIN_ROOT/scripts/lib/quality-gate.mjs';

   const touchResult = detectSharedLibTouch({
     repoRoot: process.cwd(),
     sinceRef: SESSION_START_REF,
     promoteWhenTouched: ['scripts/lib/', 'hooks/', '.husky/'],
   });

   if (touchResult.touched && (waveRole === 'Impl-Core' || waveRole === 'Impl-Polish')) {
     console.log(
       `ℹ Quality-Lite auto-promoted to Full Gate — wave touched shared code: ` +
       `${touchResult.paths.join(', ')} (#555 FL-3)`,
     );
     // Run Full Gate (typecheck + test + lint) instead of the role-default Incremental.
   } else {
     // Existing role-based selection (Discovery: none, Impl-*: Incremental, Quality: Full, Finalization: git status).
   }
   ```

   `detectSharedLibTouch` never throws — on any git failure (invalid sinceRef, detached HEAD, missing repo) it returns `{ touched: false, paths: [] }`, so a probe failure silently falls back to the role-default Incremental rather than blocking the wave. When `waveRole === 'Quality'`, the gate is **already Full** — no further promotion possible, no double-promotion. When `waveRole === 'Discovery'` or `'Finalization'`, this check is skipped entirely (the role's verification semantics don't include a test gate to promote).

   **Baseline cache check (#258)** — before running Incremental quality checks for this wave, consult the session-start Baseline cache. If the cache is still valid and the diff since `$SESSION_START_REF` is narrow (<50 files), skip Incremental for this wave and note the skip in the wave progress update.

   ```js
   // import at the top of the wave-executor runtime
   import { shouldSkipIncremental } from '$PLUGIN_ROOT/scripts/lib/quality-gates-cache.mjs';

   const skip = shouldSkipIncremental({ repoRoot: process.cwd(), sessionStartRef: SESSION_START_REF });
   if (skip.skip) {
     console.log(`ℹ Incremental quality check skipped — ${skip.reason} (${skip.changedFileCount} files changed).`);
     // proceed to next wave without running Incremental
   } else {
     // run Incremental quality check as before (per role-specific rules below)
   }
   ```

   `shouldSkipIncremental` never throws — on any error (git failure, unreadable cache) it returns `skip: false` so Incremental runs. Full Gate at session-end is NEVER skipped regardless of the cache — see the close-safety invariant in `skills/quality-gates/SKILL.md § Baseline Cache (#258)`.

   - After **Discovery**: no verification needed (read-only)
   - After **Impl-Core**: Incremental quality checks per quality-gates (test changed files, typecheck)
   - After **Impl-Polish**: Incremental quality checks + integration verification
   - **Simplification pass** (at the start of the Quality wave, before test/review agents):
     1. Identify all files changed in this session: `git diff --name-only $SESSION_START_REF..HEAD`
     2. Filter to production files only (exclude `*.test.*`, `*.spec.*`, `__tests__/`). If no production files changed, skip the simplification pass entirely — proceed directly to test/review agents.
     3. Dispatch 1-2 simplification agents with:
        - Changed file list (production files only — exclude `*.test.*`, `*.spec.*`, `__tests__/`)
        - Reference: `slop-patterns.md` from the discovery skill directory — include the actual patterns in the agent prompt
        To include the patterns: read `skills/discovery/slop-patterns.md` and paste the full content into the agent prompt under a "## Slop Patterns Reference" heading. Do NOT ask the agent to read the file itself — include it inline so the agent has zero-dependency context.
        - Reference: project's CLAUDE.md (or AGENTS.md on Codex CLI) conventions
        - Instruction: "Review each changed file for AI-generated code patterns. Apply targeted simplifications: remove unnecessary try-catch around non-throwing operations, delete over-documentation (params that repeat the name, returns that say 'the result'), replace re-implemented stdlib functions with standard alternatives, simplify redundant boolean logic (if/else returning true/false, double negation, explicit boolean comparisons). Do NOT change functionality. Do NOT touch files you weren't given. Do NOT commit."
        - Tools: Read, Edit, Grep, Glob
        - Model: sonnet
     4. After simplification agents complete, proceed to Quality test/review agents
   - After **Quality**: Full Gate quality checks per quality-gates (typecheck + test + lint, must all pass)
     (Full Gate is NEVER skipped regardless of cache state — this is the close-safety invariant.)
   - After **Finalization**: final git status check

#### Auto-Fix Protocol (#521)

When `verification-auto-fix.enabled: true`, the inter-wave Quality-Gate uses
`runQualityGateWithRetry()` to dispatch up to `max-retries` (default 2)
fixer-agent attempts before aborting.

Per attempt:
1. Run quality-gate (lint, typecheck, test in order).
2. On failure, collect: failure output, corrective_context from
   `.orchestrator/current-session.json`, changed files since last green SHA.
3. Dispatch code-implementer fixer-subagent with the bundle.
4. Re-run quality-gate.
5. After max-retries → write `.orchestrator/metrics/verification-failures/<ts>.json`
   diagnostics bundle and abort the wave.

See `SKILL.md` § "Inter-Wave Quality-Gate (with Auto-Fix Loop — #521)" for
the full invocation pattern.

##### STATE.md Deviation — Auto-Fix Result

After `runQualityGateWithRetry()` returns:

- **If `result.ok === true`:** No deviation entry — quality gate passed, wave proceeds normally.
- **If `result.attempts > 1` and `result.ok === true`:** Append ONE entry to `## Deviations` in `<state-dir>/STATE.md`:
  ```
  - [<ISO 8601 UTC>] Wave N auto-fix succeeded after N attempts (max-retries config: M). Failed gate(s): <gate-names>. Final pass on attempt N.
  ```
- **If `result.ok === false`:** Append ONE entry to `## Deviations` in `<state-dir>/STATE.md`:
  ```
  - [<ISO 8601 UTC>] Wave N auto-fix exhausted retries after N attempts (max-retries config: M). Failed gate: <gate-name>. Diagnostics bundle: <bundlePath>. Coordinator to review bundle and decide: fix manually, disable auto-fix and retry, or abort wave.
  ```

Use `appendDeviationOnDisk(repoRoot, isoTimestamp, message)` from `scripts/lib/state-md.mjs`.
This is a **coordinator-only** write — fixer-subagents do not write STATE.md. The lock library
ensures atomicity if multiple coordinator-level deviations land in the same wave.

#### Auto-Commit Checkpoint (Optional, Opt-In)

> Gate conditions — ALL of the following must be true for this step to run:
> 1. `$CONFIG["auto-commit-per-wave"] === true`
> 2. `$CONFIG.persistence === true`
> 3. The Incremental quality check in step 4 returned **PASS** (skip or fail → do not commit)
> 4. Worktree base-ref freshness check (step 3b) returned **pass** or **warn** for all agents (not **block**)
> 5. No unresolved merge conflicts in the working tree (`git status --short` shows no `UU`/`AA`/`DD` lines)
>
> When any condition is false, skip this step silently. Log "auto-commit-per-wave skipped" in the wave progress update if the gate condition was `auto-commit-per-wave: true` but another condition failed — so the operator knows the flag is set but the checkpoint did not fire.

**Commit message format:**

```
chore(wave-N): auto-checkpoint — <Role> wave complete

Quality-Lite: PASS | Wave: N / <total-waves> | Session: <session_id>
Agents: <done>/<total> done, <partial> partial, <failed> failed
```

**Env-var bypass:** `SO_SKIP_AUTO_COMMIT=1` disables the commit for the current shell invocation regardless of config — useful for CI environments or when a human is reviewing changes mid-session.

**STATE.md deviation logging:** after a successful commit, append one entry to `## Deviations` using `appendDeviationOnDisk(repoRoot, isoTimestamp, message)` from `scripts/lib/state-md.mjs` (acquires the lock automatically):

**Wrapper choice:** the canonical on-disk wrapper is `appendDeviationOnDisk(repoRoot, isoTimestamp, message)` — it acquires the STATE.md lock automatically before reading + writing. Callers in `.mjs` modules MUST prefer the on-disk wrapper; callers that pre-read STATE.md contents may use `appendDeviation(stateContents, isoTimestamp, message)` directly but MUST then route the write through `writeStateMd()`. Never use `readFileSync(STATE) → transform → writeFileSync(STATE)` — the race window allows STATE.md corruption under parallel waves (PSA-005).

```
- [<ISO 8601 UTC>] Wave N auto-commit: <sha> (<Role>, Quality-Lite PASS, <N> files staged)
```

If the commit itself fails (e.g., nothing to commit, pre-commit hook rejects), do NOT append the deviation. Instead, log the failure in the wave progress update as a WARN and continue to the next step without blocking.

**Mission-status transition:** after a successful auto-commit, transition the mission status for all tasks in this wave from `in-dev` → `testing` using `setMissionStatus(stateContent, taskId, 'testing')` from `scripts/lib/state-md.mjs`. This matches the coordinator-level rule in `SKILL.md § Mission-Status Updates`: "in-dev → testing: Quality wave begins and this item's implementation wave completed without failure." The auto-commit checkpoint fires at the same logical moment — after implementation completes and Quality-Lite passes.

**Implementation deferred:** This subsection documents the contract. The procedural body (git add/commit sequence + error handling) will land in V3.6 as `scripts/lib/auto-commit.mjs` (see follow-up issue GitLab #214). Until then, this section is a no-op stub when `auto-commit-per-wave: true` is set; the coordinator MUST warn the user at session-start that auto-commits are not yet active (emit: "auto-commit-per-wave is set but the implementation (scripts/lib/auto-commit.mjs) is not yet available — commits will occur at session-end via /close as normal").

---

5a. **Persona-reviewer dispatch** (opt-in, gated by `wave-reviewers` config):
   - Read `wave-reviewers` from Session Config. If the key is absent or the array is empty → skip this step entirely (no-op).
   - Applicable waves: **Impl-Core** and **Impl-Polish** only. Skip for Discovery, Quality, and Finalization waves.
   - For each reviewer name in the array, dispatch in parallel with read-only scope. Example:
     ```
     // Dispatch all configured reviewers in parallel (Promise.all semantics)
     Agent({
       description: "Persona review — <reviewer-name> — Wave N",
       prompt: "<include: wave scope, changed files list, relevant plan section>",
       subagent_type: "session-orchestrator:<reviewer-name>",
       run_in_background: false
     })
     ```
   - Each reviewer writes its findings to `.orchestrator/audits/wave-reviewer-<wave>-<reviewer-name>.md`. The coordinator does NOT need to create this file — the reviewer agent writes it directly.
   - **Findings are ADVISORY**: reviewer output never blocks the subsequent wave. After all dispatched reviewers complete:
     - If any reviewer reports **WARN**: surface the findings to the user in the wave progress summary. Feed actionable items into the next wave's agent assignments (step 3 — Adapt Plan).
     - If any reviewer reports **FAIL**: surface the findings prominently in the wave progress summary with a `[REVIEWER FAIL]` prefix. Still proceed to step 5 (session-reviewer) — do not halt wave execution.
     - If all reviewers report **PASS** or produce no findings: log a one-line note and continue.
   - **Default behaviour unchanged**: when `wave-reviewers` is absent or `[]`, this step is a no-op and the wave loop proceeds exactly as before.
   - Supported reviewer names (plugin-provided): `architect-reviewer`, `qa-strategist`, `analyst`. Custom reviewer agents in `agents/` are also valid if their `name` frontmatter matches.

5. **Session-reviewer dispatch** (after Impl-Core, Impl-Polish, and Quality waves only):
   - When integrating reviewer findings, follow the receiving-review protocol — see `.claude/rules/receiving-review.md` for the 6-step pattern (READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT) and the forbidden-phrase list.
   - After **Impl-Core** and **Impl-Polish** waves, dispatch the session-reviewer agent to verify wave output:
     ```
     Agent({
       description: "Review wave N output",
       prompt: "<include: session plan, wave results, changed files list, acceptance criteria>",
       subagent_type: "session-orchestrator:session-reviewer",
       run_in_background: false
     })
     ```
   - The session-reviewer checks changed files against the plan and reports PASS/WARN/FAIL per category (implementation, tests, TypeScript, security, silent failures, test depth, type design, issues).
   - If the session-reviewer reports **WARN or FAIL** findings: add fix tasks to the next wave's agent assignments (feed into step 3 — Adapt Plan).
   - After the **Quality** wave: dispatch the session-reviewer with **full session scope** (all files changed since session start, not just the current wave). Use `git diff --name-only $SESSION_START_REF..HEAD` to provide the complete changed files list.
   - Include `SESSION_START_REF` (captured in Pre-Wave 1) in the session-reviewer prompt so it can compute the full changed files list independently.
   - **Relationship to session-end Phase 1.8:** Wave-level session-reviewer runs provide incremental feedback during execution. Session-end Phase 1.8 runs a final comprehensive review of ALL changes. Both are complementary — wave reviews catch issues early, session-end review is the final quality gate.
   - **Discovery** and **Finalization** waves: skip session-reviewer dispatch — Discovery is read-only and Finalization is a final git status check only.
   - This is complementary to the incremental verification in step 4 — the session-reviewer provides deeper analysis (security, silent failures, test depth, type design) that automated checks do not cover.
6. **Pencil design review** (after Impl-Core and Impl-Polish roles only, if `pencil` configured in Session Config):
   a. Check Pencil editor state: `get_editor_state({ include_schema: false })`. If no editor active, open the configured `.pen` file via `open_document({ filePathOrTemplate: "<pencil-path>" })`. If that also fails → skip with note "Pencil review skipped — .pen file unavailable."
   b. Get design structure: `batch_get({ filePath: "<pencil-path>", patterns: [{ type: "frame" }], readDepth: 2, searchDepth: 2 })` — find frames relevant to this wave's UI work.
   c. Screenshot relevant frames: `get_screenshot({ filePath: "<pencil-path>", nodeId: "<frame-id>" })` for each frame matching the wave's UI tasks.
   d. Read the actual UI files changed in this wave (from agent outputs).
   e. **Compare**: layout structure, component hierarchy, visual elements (headings, buttons, inputs, cards), responsive behavior.
   f. **Report** in wave progress:
      `- Design: [ALIGNED / MINOR DRIFT / MAJOR MISMATCH] — [specific findings]`
   g. **Act on results**:
      - ALIGNED → proceed to next wave
      - MINOR DRIFT → add fix tasks to next wave (no pause)
      - MAJOR MISMATCH → **PAUSE wave execution**:
        1. Report specific mismatches to user
        2. AskUserQuestion: "Continue as-is", "Revise plan for remaining waves", "Abort session"
           > If AskUserQuestion is unavailable (Codex CLI), present as numbered list.
        3. If "Revise" → re-run session-plan for remaining waves only
        4. If "Abort" → mark remaining waves as DEFERRED, proceed to session-end
   
   Always use the `filePath` parameter on Pencil MCP calls. Only review frames relevant to the current wave, not the entire file.

7. **Capture wave metrics**: If `persistence` is enabled in Session Config, record for this wave after all agents complete and quality checks run. If `persistence` is `false`, skip metrics capture entirely — do not accumulate in-memory metrics. Record:
   - `wave_number`, `role`, `started_at` (when agents were dispatched), `completed_at` (when all finished)
   - `agent_count`: number of agents dispatched
   - Per-agent results: `{description, status: done|partial|failed, files_changed_count}`
   - `files_changed`: total unique files changed this wave (from `git diff --stat --name-only`)
   - `quality_check`: incremental check result (pass/fail/skipped)
   Append this wave record to the session metrics `waves` array.

### 3. Adapt Plan (if needed)

After reviewing wave results, decide:

- **On track**: proceed to next wave as planned
- **Minor issues**: add fix tasks to next wave's agent assignments
- **Major blocker**: propose a revised plan for the remaining waves and present the choice to the user via `AskUserQuestion` (proceed / revise / abort). See `.claude/rules/ask-via-tool.md` — never surface this as an inline prose question.
- **Agent failed**: re-dispatch with corrected instructions in next wave
- **Scope change**: document why, adjust remaining waves, present scope deltas to the user via `AskUserQuestion` (accept / reject / modify).

**Deviation protocol**: ALWAYS document WHY you deviated from the plan. Log it in a brief note that session-end can reference.

**User interaction protocol**: Any decision surfaced to the user from this loop — plan revisions, scope changes, recovery-path choice, pause/continue prompts — goes through `AskUserQuestion`. Inline markdown-list choices are a bug; see `.claude/rules/ask-via-tool.md`.

#### Dynamic Scaling

After reviewing wave results, adjust the next wave's agent count based on performance signals:

| Signal | Action | Example |
|--------|--------|---------|
| All agents completed in under 3 minutes wall-clock, no issues | Reduce next wave by 1-2 agents | 6 agents all done in <3m → next wave uses 4 |
| Agent failures or broken code | Add fix agents to next wave (+1-2) | 2 agents failed → next wave gets 2 extra |
| Scope expansion discovered | Scale up next wave | New module found → add agents for it |
| Quality regressions found | Add targeted fix agents | 3 test failures → 3 fix agents next wave |

**Scaling constraints:**
- Never exceed `agents-per-wave` from Session Config
- Never go below 1 agent per wave
- Log all scaling decisions in the wave progress update
- Record actual vs. planned agent count in wave metrics

### 3a. Post-Wave: Update STATE.md

> Skip if `persistence: false`.

After each wave completes and before the progress update, update `<state-dir>/STATE.md`:

1. **Frontmatter**: set `current-wave` to the just-completed wave number; set `status` to `active` (or `paused` if waiting on user input)
2. **`## Current Wave`**: replace contents with next wave info — wave number, role, agents to dispatch and count
3. **`## Wave History`**: append an entry for the completed wave:
   ```
   ### Wave N — <Role>
   - Agent "<description>": <done|partial|failed> — <files changed> — <1-line note>
   - Agent "<description>": <done|partial|failed> — <files changed> — <1-line note>
   ```
4. **`## Deviations`**: if the plan was adapted in step 3, append a timestamped entry:
   ```
   - [<ISO timestamp>] Wave N: <what changed and why>
   ```

5. **Heartbeat refresh (#590-3)** — after the STATE.md write, refresh the session-lock heartbeat so long-running deep sessions do not let the 4h TTL lapse between waves. Best-effort: a failure must NOT block the wave.

   ```js
   // Per-wave heartbeat refresh (#590-3) — keeps session.lock fresh during long deep sessions.
   // sessionId = the session identifier established by session-start Phase 1.2 acquire()
   //   and stored in .orchestrator/session.lock (session_id field); matches the
   //   STATE.md frontmatter `session:` field written during Pre-Wave 1b initialization.
   import { updateHeartbeat } from '../../scripts/lib/session-lock.mjs';
   updateHeartbeat({ sessionId, repoRoot: process.cwd() });
   ```

   Skip silently if `persistence: false` in Session Config (no session.lock exists in that mode).

### 3a-bis. Agent-Status Telemetry (#565)

> Optional operator-side observability — NOT load-bearing. Best-effort, fire-and-forget telemetry that a tmux `--with-status-pane` (see `skills/tmux-layout/SKILL.md`) renders as a live side-channel per ADR-0007. A status push must NEVER block or fail a wave — mirror the §3a heartbeat-refresh framing exactly.

**Gate:** `persistence: true` in Session Config. When `persistence: false`, skip every push below — there is no runtime side-channel to feed.

The helper is `scripts/lib/agent-status.mjs`. Its exports (`setStatus`, `setProgress`, `readCurrentStatus`) are all no-throw and return `{ ok: true } | { ok: false, reason }`; the coordinator ignores the return value (best-effort). Push at **three anchors** in the wave loop:

1. **dispatch** — in `### 1. Dispatch Agents`, as each agent is dispatched, push its status. Use `setProgress` when the wave's per-agent ordinal is meaningful, else `setStatus`:

   ```js
   import { setStatus, setProgress } from '../../scripts/lib/agent-status.mjs';

   // For each agent dispatched in this wave (i = 0-based position, total = wave agent count):
   await setStatus(agentId, `dispatched — ${subagentType}`);              // free-text variant
   // — or —
   await setProgress(agentId, { step: i + 1, total, label: subagentType }); // progress variant
   ```

   `agentId` is a stable per-agent key (e.g. `wave${waveN}-${i}-${subagentType}`). There is **no separate "agent-start" hook distinct from dispatch** — wave agents are in-process `Agent()` calls with no PID/TTY (see `skills/tmux-layout/SKILL.md § When NOT to Use`), so dispatch IS the start signal. Do not invent one.

2. **agent-end** — in `### 2. Review Agent Outputs` step 1 (Read each agent's result), as each agent's terminal status is determined, push it:

   ```js
   // status ∈ {'done','partial','failed'} from the agent's STATUS: line
   await setStatus(agentId, status);
   ```

3. **wave-end rollup** — in `### 3a. Post-Wave: Update STATE.md`, beside the `updateHeartbeat` call (step 5), push one wave-level rollup using a wave-scoped key:

   ```js
   // e.g. agentId = `wave${waveN}` ; counts from the wave's per-agent results
   await setStatus(`wave${waveN}`, `wave ${waveN} complete — ${done} done, ${partial} partial, ${failed} failed`);
   ```

A push failure (timeout, fs-error, invalid-input) is logged to the wave progress update at most as a one-line WARN — never block, never retry, never surface to the user. If `agent-status.mjs` is absent (older plugin checkout), wrap the import defensively and no-op, exactly as `layouts.mjs` does for its telemetry import.

### 3b. Persona-Gate Hook (#458)

> Opt-in mid-wave hook that fans out a `/persona-panel`-style review after a configured wave completes. Distinct from `### 5a. Persona-reviewer dispatch` (which uses the `wave-reviewers` Session Config key and dispatches code-oriented `architect-reviewer` / `qa-strategist` / `analyst` agents). This hook uses the `persona-gate-wave` Session Config key and dispatches catalog personas (domain-experts, buyer-personas, auditors) from `.claude/personas/`. The two keys are independent and may both be configured on the same project.

**Gate conditions** — ALL must be true for the hook to fire:

1. `persona-gate-wave.enabled: true` in Session Config (default: `false`).
2. The just-completed wave matches `persona-gate-wave.after` — one of `'quality'` or `'impl-polish'`. The hook runs AFTER step 3a (STATE.md updated) and BEFORE step 4 (progress update), so the dispatch context already reflects the completed wave's results.
3. `persona-gate-wave.mode !== 'off'` (when `mode: 'off'` the hook is a silent no-op even when `enabled: true`).

When any gate condition is false, skip this step entirely — proceed to `### 4. Progress Update`.

**Dispatch sequence:**

```js
import { loadCatalog } from '$PLUGIN_ROOT/scripts/lib/persona-panel/catalog-loader.mjs';
import { buildPersonaPrompt, validatePersonaOutput } from '$PLUGIN_ROOT/scripts/lib/persona-panel/persona-runner.mjs';
import { consolidate } from '$PLUGIN_ROOT/scripts/lib/persona-panel/consolidator.mjs';
import { writeJsonAtomic } from '$PLUGIN_ROOT/scripts/lib/io.mjs';
import { appendDeviationOnDisk } from '$PLUGIN_ROOT/scripts/lib/state-md.mjs';

const cfg = $CONFIG['persona-gate-wave'];                        // already normalised by parseSessionConfig
const catalog = await loadCatalog();                              // throws if .claude/personas/ missing or invalid
const rosterNames = cfg.personas.length > 0
  ? cfg.personas
  : [...catalog.keys()];                                          // empty list → all catalog personas
const personas = rosterNames.map((n) => catalog.get(n)).filter(Boolean);
```

Dispatch each persona in parallel via the Agent tool, using `cfg['dispatch-model']` as the model and `Read, Grep, Glob` tools only (panel personas are read-only by contract). Each dispatch wraps the wave's scope summary + changed-files list in `buildPersonaPrompt(persona.persona, target, targetContent)`.

After all agents return, collect their outputs and validate each via `validatePersonaOutput(persona.persona, agentText)`. Compose the panel verdict via `consolidate(outputs, 'hard-gate-threshold', { threshold: cfg.threshold_parsed })`.
<!-- threshold_parsed is pre-computed by _normalizePersonaGateWave in persona-gate-wave.mjs; no re-parse needed here -->

**Behaviour by mode:**

| `mode` | Action on consolidator result |
|--------|--------------------------------|
| `off` | No dispatch (gate condition above). |
| `warn` | Log findings to the wave progress update under a `Persona-gate:` bullet. Continue to step 4 regardless of `final_verdict`. |
| `strict` | If `final_verdict === 'PROCEED'`: log to progress, continue. Otherwise pause and surface an `AskUserQuestion` with three options:<br>1. **proceed-as-is** — log Deviation, continue (Recommended only after operator inspects sidecar)<br>2. **revise-remaining-waves** — return `{ verdict: 'FIX_REQUIRED', revision_context: { dissenting_personas, recommendations } }` to the wave-executor caller<br>3. **abort-session** — return `{ verdict: 'BLOCKED' }` to the caller |

**Sidecar write:** before reporting any verdict, validate the panel result against `agents/schemas/persona-panel-sidecar.schema.json` (via `validateAgentOutput` or a direct AJV compile) and then write atomically via `writeJsonAtomic(path, value, { schemaPath })`:

```
.orchestrator/persona-panel/<iso-timestamp>-<runId>.json
```

The sidecar carries `personas_invoked`, per-persona `outputs`, and the full `consolidation` block — operators consult it from the AskUserQuestion prompt before deciding `strict`-mode follow-up.

**STATE.md deviation contract:** on `warn` (with at least one dissenting persona) or any `strict`-mode non-PROCEED verdict, append one timestamped entry to `## Deviations` via `appendDeviationOnDisk(repoRoot, iso, message)` from `scripts/lib/state-md.mjs` (acquires the STATE.md lock):

```
- [<ISO 8601 UTC>] Wave N persona-gate <warn|strict-proceed|strict-revise|strict-abort>: dissenting=[<persona-1>, <persona-2>], threshold=<cfg.threshold>, mode=<cfg.mode>. Sidecar: <relative-path>.
```

On a clean `PROCEED` no deviation is written — the sidecar alone is sufficient evidence.

**Wave metrics extension:** when persistence is enabled, extend the wave metrics record (step 7 of `### 2. Review Agent Outputs`) with a `persona_gate` block:

```json
"persona_gate": {
  "triggered": true,
  "threshold": "<cfg.threshold>",
  "personas_pass": <N>,
  "personas_fail": <M>,
  "mode_used": "<cfg.mode>",
  "final_verdict": "<PROCEED|PROCEED_WITH_FOLLOWUPS|BLOCKED|REQUIRES_COORDINATOR>",
  "sidecar_path": ".orchestrator/persona-panel/<...>.json"
}
```

When the hook is skipped (gate condition false), omit the `persona_gate` field entirely — never write `triggered: false` for skipped runs, so a downstream consumer can distinguish "hook did not fire" from "hook fired but found no dissent".

**Motivating example:** the `gotzendorfer-v2` W5 Buyer-Panel pattern (six buyer personas at `hard-gate-threshold` `6-of-6`, `mode: 'strict'`, `after: 'quality'`) — UI work is gate-checked against every persona before commit, abort on any dissent. See `docs/session-config-reference.md § Persona-Gate Wave (#458)` and `commands/persona-panel.md` for the standalone CLI equivalent.

### 3c. Strategic Compact-Nudge (#620)

> Advisory-only checkpoint. Never auto-compacts. `/compact` is a user slash-command; the coordinator/operator decides when to invoke it.

**Gate conditions** — ALL must be true for the nudge to emit:

1. `compact-nudge.enabled: true` in Session Config (default: `false`).
2. The just-completed wave's role is listed in `compact-nudge.after` (default: `['discovery', 'impl']`). Compare the wave's canonical role string (lower-case) against the list.
3. `compact-nudge.mode !== 'off'` (when `mode: 'off'` the nudge is a silent no-op even when `enabled: true`).

When any gate condition is false, skip this step entirely — proceed to `### 4. Progress Update`.

**Nudge format** — when the gate fires, append ONE advisory bullet to the wave progress update (step `### 4`):

```
- 💡 Compact checkpoint: Wave N (<Role>) complete — consider /compact before Wave N+1 (<NextRole>) to free context (advisory only; see decision table). Never auto-compacts.
```

**What survives `/compact` vs what is lost:**

| Survives | Lost |
|---|---|
| CLAUDE.md, STATE.md (on disk), wave-scope.json, JSONL metrics (.orchestrator/), git history, all files on disk | Intermediate reasoning/thinking traces, previously-read file contents cached in context, tool-call history for prior waves |

This frames the nudge: the persistent artefacts (plan, scope, STATE.md, git diff) are the distilled output of completed work; losing in-context file reads is the cost. Compact is worth it when the completed wave produced bulky research/audit output that is unlikely to be re-referenced verbatim.

**Decision table:**

| Wave boundary (completed → next) | Compact? | Why |
|---|---|---|
| Discovery → Impl-Core | Yes | Research/audit context is bulky; the plan + wave-scope.json is the distilled output. |
| Impl-Core → Impl-Polish (long Core) | Maybe | Compact only if Polish targets different files; keep if Polish builds on Core's changes. |
| Impl-Polish → Quality | No | Quality references the just-written code; losing it is costly. |
| Quality → Finalization | No | Finalization needs the full session diff. |
| Mid-implementation (within a wave) | No | Losing file paths + partial state is expensive. |
| After a FAILED/aborted wave | Yes | Clear the dead-end reasoning before the adapted retry. |
| Switching to an unrelated task block (deep session) | Yes | Debug/exploration traces pollute unrelated downstream work. |

**Behaviour by mode:**

| `mode` | Action |
|--------|--------|
| `off` | No nudge (gate condition above). |
| `warn` | Emit the advisory bullet in the wave progress update. Coordinator/operator acts at their discretion. |

The nudge is informational only — no AskUserQuestion, no state-md write, no sidecar. This step never blocks forward progress.

### 4. Progress Update

After each wave, provide a brief status:

```
## Wave [N] ([Role]) Complete ✓
- [Agent 1]: [done/partial/failed] — [1-line summary]
- [Agent 2]: [done/partial/failed] — [1-line summary]
- Duration: [Nm Ns] (wall-clock from dispatch to completion)
- Tests: [passing/failing] | TypeScript: [0 errors / N errors]
- Design: [aligned/drift/mismatch — or N/A if not Impl-Core/Impl-Polish or no pencil config]
- Scaling: [unchanged / reduced to N / increased to N] — [reason]
- Adaptations for Wave [N+1] ([NextRole]): [none / list changes]
```

## Scope Manifest

Before each wave dispatch:

1. **Write `<state-dir>/wave-scope.json`** with the wave's scope:
   > (Platform-specific: `.claude/wave-scope.json` on Claude Code, `.codex/wave-scope.json` on Codex CLI, `.cursor/wave-scope.json` on Cursor IDE)

   **Deriving `blockedCommands` (policy-file-first, #155):** Before writing `wave-scope.json`, extract the blocked patterns from the consolidated policy file:
   ```bash
   BLOCKED=$(jq -c '[.rules[] | select(.severity == "block") | .pattern]' .orchestrator/policy/blocked-commands.json)
   ```
   Use `$BLOCKED` as the `blockedCommands` value in `wave-scope.json`.

   **Fallback:** If `.orchestrator/policy/blocked-commands.json` is missing (pre-#155 repo), use the legacy hardcoded array and log a warning in the wave progress update:
   ```bash
   BLOCKED='["rm -rf", "git push --force", "DROP TABLE", "git reset --hard", "git checkout -- ."]'
   # Warning: policy file .orchestrator/policy/blocked-commands.json not found — using legacy hardcoded blocklist
   ```

   ```json
   {
     "wave": N,
     "role": "<role>",
     "enforcement": "<from Session Config, default: warn>",
     "allowedPaths": ["<from agent specs in session plan>"],
     "blockedCommands": "<derived dynamically from .orchestrator/policy/blocked-commands.json (severity: block rules); falls back to legacy 5-element array if policy file absent>",
     "gates": "<copy of enforcement-gates from Session Config, or omit if unset>"
   }
   ```
   The `gates` field (optional) mirrors `enforcement-gates` from Session Config (#77). When present, hooks check each gate individually via `gate_enabled()`. Missing gate entries default to enabled, preserving default behavior.
2. Validate by piping through `node "$PLUGIN_ROOT/scripts/validate-wave-scope.mjs"` (where `$PLUGIN_ROOT` is `$CLAUDE_PLUGIN_ROOT`, `$CODEX_PLUGIN_ROOT`, or `$CURSOR_RULES_DIR` per platform — see `skills/_shared/config-reading.md`). If validation fails (exit 1), fix the JSON based on stderr errors and retry.
3. `allowedPaths` is the UNION of all agent file scopes for this wave
   To compute `allowedPaths`: read each agent's specification from the session plan. Each agent lists its "Files:" scope (e.g., `skills/session-end/SKILL.md`, `scripts/*.sh`). Collect all file paths and glob patterns from all agents in this wave into a single flat array. Deduplicate entries. If an agent's scope uses globs (e.g., `scripts/*.sh`), include the glob pattern as-is — the enforcement hook resolves globs at check time.
4. Read `enforcement` from Session Config (default: `warn`). The `enforcement` field is REQUIRED in `wave-scope.json` — always write it explicitly. The hooks default to `warn` if the field is missing, which would silently degrade strict enforcement. If jq was confirmed missing in Pre-Execution Check step 4, set `enforcement` to `off` and include a comment in the progress update noting that enforcement is disabled.
5. For **Discovery** role waves, set `allowedPaths` to `[]` (empty array) — Discovery agents are read-only and must not modify files. Also add to each Discovery agent prompt: "You are READ-ONLY. Do NOT use Edit or Write tools."
   > **Defense in depth:** The empty `allowedPaths` enforcement hook is the PRIMARY barrier (blocks Write/Edit at the tool level). The prompt instruction is a SECONDARY safeguard. If jq is unavailable (enforcement set to `off`), the prompt instruction becomes the ONLY barrier — log a warning in this case.
6. For **Quality** role waves, use two-phase scope enforcement:
   - **Phase 1 (Simplification)**: Before dispatching simplification agents, set `allowedPaths` to the production files changed this session (`git diff --name-only $SESSION_START_REF..HEAD`, excluding test files). After simplification agents complete, **delete** `<state-dir>/wave-scope.json` before proceeding to Phase 2.
   - **Phase 2 (Test/Review)**: Before dispatching test and review agents, regenerate `<state-dir>/wave-scope.json` with `allowedPaths` restricted to test file patterns (`**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`, plus test config files). Quality test/review agents must not modify production source code.

   **Phase transition sequence:**
   1. Compute production file list: `git diff --name-only $SESSION_START_REF..HEAD | grep -v -E '\.(test|spec)\.' | grep -v '__tests__/'`
   2. If no production files → skip Phase 1 entirely, proceed to Phase 2 (write test-only wave-scope.json)
   3. Write Phase 1 wave-scope.json with production file allowedPaths
   4. Dispatch simplification agents, wait for completion
   5. Delete `<state-dir>/wave-scope.json`
   6. Write Phase 2 wave-scope.json with test file allowedPaths (`**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`)
   7. Dispatch test/review agents
7. After the final wave completes, delete `<state-dir>/wave-scope.json` (cleanup)
