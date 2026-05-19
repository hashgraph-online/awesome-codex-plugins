---
name: autopilot
description: >
  Use this skill when running an autonomous session-orchestration loop. Chains session-start → session-plan →
  wave-executor → session-end for N iterations with kill-switches (SPIRAL, FAILED
  wave, carryover > 50%, max-hours, sub-threshold confidence). Reads Mode-Selector
  output (Phase B) to decide auto-execute vs. fallback. Writes one autopilot.jsonl
  record per loop run. Phase C scaffold (issue #277); implementation lives in
  scripts/lib/autopilot.mjs (Phase C-1 follow-up).
user-invocable: true
tags: [phase-c, autopilot, autonomous, loop]
model: sonnet
---

# Autopilot Skill

## Status

**Phase C-1.b complete (2026-04-25, issues #295 + #300).** Runtime at
`scripts/lib/autopilot.mjs` enforces all 8 kill-switches:

- **Pre-iteration (5, #295):** `max-sessions-reached`, `max-hours-exceeded`,
  `resource-overload`, `low-confidence-fallback` (with iter-1-fallback /
  iter-2+-exit asymmetry), `user-abort`.
- **Post-session (3, #300):** `spiral`, `failed-wave`, `carryover-too-high`.
  Read schema-canonical fields off the `sessionRunner` return shape:
  `agent_summary.{spiral, failed}` (numeric counts) and `effectiveness.{carryover,
  planned_issues}`. Absent fields → no kill (forward-compatible: a `sessionRunner`
  that does not yet emit those fields silently no-ops the post-session gates).

Atomic `autopilot.jsonl` writer (tmp+rename, schema_version 1) and silent-clamp
`parseFlags` shipped in C-1. `autopilot_run_id` is passed into `sessionRunner`
via `args.autopilotRunId`; production callers MUST persist it into the per-iteration
`sessions.jsonl` record (additive optional field, schema_version 1 compatible).
See `skills/wave-executor/SKILL.md § Return Shape Contract` and
`skills/session-end/SKILL.md § Phase 3.7`.

## Purpose

Autopilot collapses the per-session attention cost when Mode-Selector is confident enough
to make routine decisions autonomously. A productive day commonly ships 3–7 sessions; each
manual session-start costs the user 10–60 seconds of context-switch attention. When the
session is genuinely routine (mechanical refactor, post-merge housekeeping, repeated
follow-ups from a planned epic), that attention cost is pure overhead.

`/autopilot` reads the Mode-Selector recommendation, executes the recommended session if
confidence clears the threshold, then loops — checking kill-switches between iterations.
The user invokes the loop once and walks away; autopilot stops itself when work runs out
or quality degrades.

This is **opt-in by design**: autopilot never starts itself. The user must run
`/autopilot` explicitly. Configuration thresholds (`--max-sessions`, `--max-hours`,
`--confidence-threshold`) are CLI flags, not Session Config defaults — the user signals
intent for THIS run, not a standing policy.

## Command Surface

```
/autopilot [--max-sessions=N] [--max-hours=H] [--confidence-threshold=0.X] [--dry-run]
```

| Flag | Default | Bounds | Meaning |
|------|---------|--------|---------|
| `--max-sessions` | `5` | 1..50 | Iteration cap (graceful exit when reached) |
| `--max-hours` | `4.0` | 0.5..24.0 | Wall-clock budget for entire loop |
| `--confidence-threshold` | `0.85` | 0.0..1.0 | Minimum `selectMode` confidence for auto-execute |
| `--dry-run` | `false` | — | Print planned iterations without executing |

Out-of-range values silently clamp to bounds. `--dry-run` exits after printing — never
invokes session lifecycle.

## Loop Semantics

```
state := { iterations_completed: 0, started_at: now(), kill_switch: null, sessions: [] }

WHILE state.iterations_completed < max-sessions:
  IF (now() - state.started_at) > max-hours:
    kill_switch := 'max-hours-exceeded'; break
  IF resource_verdict() == 'critical' AND peer_count() > autopilot-peer-abort:
    kill_switch := 'resource-overload'; break

  recommendation := mode-selector.selectMode(<live signals from session-start Phase 7.5>)

  IF recommendation.confidence < confidence-threshold:
    IF state.iterations_completed == 0:
      fallback_to_manual()  # iteration 1: hand off cleanly to manual /session flow
    ELSE:
      kill_switch := 'low-confidence-fallback'  # iteration 2+: exit, let user decide
    break

  cap := resource_adaptive_cap()
  session_result := run_session(mode=recommendation.mode, agents_per_wave_cap=cap)
  state.sessions.append(session_result.session_id)

  IF session_result.spiral_detected: kill_switch := 'spiral'; break
  IF session_result.failed_waves > 0: kill_switch := 'failed-wave'; break
  IF session_result.carryover_ratio > 0.50: kill_switch := 'carryover-too-high'; break

  state.iterations_completed += 1

write_autopilot_jsonl(state, kill_switch)
print_summary(state, kill_switch)
```

**Atomicity rule:** iteration boundaries are atomic. A session must complete (`/close`
including the post-session writes) before the next iteration starts. Autopilot does NOT
abort sessions mid-flight; kill-switches are checked AFTER each session completes.

## Kill-Switches

| Kill-switch | Trigger | Recovery hint |
|-------------|---------|---------------|
| `spiral` | wave-executor spiral detection fires | Triage the spiraling wave manually; autopilot will not retry. |
| `failed-wave` | Any wave reports `agent_summary.failed > 0` | Investigate failure mode (test contract drift, env issue). Re-run after fix. |
| `carryover-too-high` | `carryover_ratio > 0.50` | Last session under-delivered. Reduce scope or split issues before resuming. |
| `max-hours-exceeded` | Wall-clock exceeds `--max-hours` | Re-run with higher `--max-hours` or address slow waves. |
| `max-sessions-reached` | `iterations_completed == --max-sessions` | Graceful — not an error. |
| `resource-overload` | `verdict==critical AND peers > autopilot-peer-abort` | Wait for peer sessions to complete or close them. |
| `low-confidence-fallback` | `confidence < threshold` (iteration 2+) | Re-run with lower `--confidence-threshold` or run next session manually. |
| `user-abort` | Ctrl+C / Esc | Re-run when ready. |

## Resource-Adaptive Concurrency

Autopilot does NOT hard-block on peer Claude processes. It adapts `agents-per-wave` cap
per iteration based on the most-restrictive resource signal.

| Tier | RAM free | Swap | Peers | macOS memory_pressure | cap |
|------|----------|------|-------|------------------------|-----|
| green | ≥ 6 GB | < 1 GB | ≤ 2 | ≥ 30% free | Session Config default |
| warn | 4–6 GB | 1–2 GB | 3–4 | 15–30% free | 4 |
| degraded | 2–4 GB | 2–3 GB | 5–6 | 5–15% free | 2 |
| critical | < 2 GB | > 3 GB | > 6 | < 5% free | 0 (coord-direct) |

**Most-restrictive-signal-wins:** `[ram=8GB, swap=0, peers=7]` → critical (peer rule wins).

Defaults are conservative initial estimates. Phase C-3 follow-up calibrates the swap and
memory_pressure thresholds against real autopilot-run effectiveness data.

## Production Wiring

Phase C-1 ships `runLoop` as a pure controller. Phase C-1.c ships `buildLiveSignals` as
the canonical signals-assembly helper. This section documents the **in-process driver
protocol** (Option B from #301): how Claude — running as the coordinator in a chat
session — drives `runLoop` between manual `/session` invocations. The headless wrapper
(Option A, `scripts/autopilot.mjs` CLI spawning `claude -p`) is reserved for Phase C-5.

### Dependency-Injection Contract

`runLoop` requires four injected dependencies:

| Field | Signature | Source |
|---|---|---|
| `modeSelector` | `() => Promise<{mode, confidence, rationale?}>` | wraps `selectMode(await buildLiveSignals())` |
| `sessionRunner` | `({mode, autopilotRunId}) => Promise<{session_id, agent_summary?, effectiveness?}>` | wraps a `/session <mode>` invocation; reads `sessions.jsonl` tail to construct return value |
| `resourceEvaluator` | `() => {verdict}` | wraps `evaluate(await probe(), thresholds)` from `resource-probe.mjs` |
| `peerCounter` | `() => number` | reads `claude_processes_count` from a fresh `probe()` snapshot |

`abortSignal` is optional (Ctrl+C / Esc → `user-abort` kill-switch).

### In-Process Driver Skeleton

```js
import { runLoop, parseFlags } from '$PLUGIN_ROOT/scripts/lib/autopilot.mjs';
import { buildLiveSignals } from '$PLUGIN_ROOT/scripts/lib/build-live-signals.mjs';
import { selectMode } from '$PLUGIN_ROOT/scripts/lib/mode-selector.mjs';
import { probe, evaluate } from '$PLUGIN_ROOT/scripts/lib/resource-probe.mjs';

const flags = parseFlags(process.argv.slice(2));

const modeSelector = async () => {
  // Each iteration rebuilds signals from current disk state. STATE.md will be
  // freshly idle-reset by the previous /close, sessions.jsonl will have the
  // new tail entry, etc. This is the contract: live signals every iteration.
  const signals = await buildLiveSignals({ backlogLimit: 50 });
  return selectMode(signals);
};

const resourceEvaluator = () => {
  const snapshot = probeSync();   // or cached snapshot if probe is async
  return evaluate(snapshot, thresholds);
};

const peerCounter = () => {
  // Synchronous-friendly count from a recent probe snapshot.
  return latestSnapshot.claude_processes_count ?? 0;
};

const sessionRunner = async ({ mode, autopilotRunId }) => {
  // The coordinator (Claude) invokes /session <mode> manually here. After the
  // session completes (/close runs, sessions.jsonl appended), this function
  // reads the tail entry and projects it into the runLoop return-shape.
  const tail = readSessionsJsonlTail(1);   // last line, normalized
  return {
    session_id: tail.session_id,
    agent_summary: tail.agent_summary,    // {complete, partial, failed, spiral}
    effectiveness: tail.effectiveness,    // {planned_issues, carryover, completion_rate, ...}
  };
};

const result = await runLoop({
  ...flags,
  modeSelector,
  sessionRunner,
  resourceEvaluator,
  peerCounter,
});
```

### Why In-Process First

The in-process driver has Claude (the coordinator) call `/session <mode>` between
`runLoop` iterations, with `runLoop` orchestrating the kill-switches. Trade-offs:

- **Pro:** zero new infra. Reuses canonical kill-switch logic. Validates `buildLiveSignals`
  against real Phase 7.5 swap before headless complexity. Each iteration carries
  inter-session memory through STATE.md / sessions.jsonl / learnings.
- **Con:** not truly autonomous — Claude must stay in the chat. Doesn't deliver
  walk-away UX. That's Phase C-5's job.

### `autopilot_run_id` Propagation

When `runLoop` invokes `sessionRunner({mode, autopilotRunId})`, the per-iteration
`sessions.jsonl` record MUST carry `autopilot_run_id: <id>`. session-end Phase 3.7
writes this field. Manual sessions write `null` or omit it — readers treat both
identically per the v1 schema additive convention. See
`skills/session-end/session-metrics-write.md`.

### Acceptance Signals

A live `/autopilot` invocation against this wiring produces a non-zero `confidence`
recommendation when at least one signal source is populated (state-md rec fields,
sessions.jsonl tail, learnings, or backlog). Confidence at 0.0 with all four sources
populated is a Mode-Selector heuristic bug (file as `[Mode-Selector v1.x quirk]` issue),
not an autopilot bug.

## Telemetry

One record per `/autopilot` invocation, written to `.orchestrator/metrics/autopilot.jsonl`
via atomic tmp + rename. See `docs/prd/2026-04-25-autopilot-loop.md` § Output for the
full schema.

Each iteration's `sessions.jsonl` entry gets an additional optional field
`autopilot_run_id` (string or null) so retros can join across the two files without
schema changes.

Manual sessions write `autopilot_run_id: null` (or omit the field — both treated
identically by readers per the v1 schema additive convention).

## Integration with Other Skills

- **`mode-selector.mjs::selectMode`** — sole source of mode + confidence per iteration.
  Autopilot does not implement its own mode logic; v1.x quirks affect autopilot exactly
  as they affect manual session-start.
- **`resource-probe.mjs::probe + evaluate`** — extended in Phase C-2 with swap and
  memory_pressure signals. Existing consumers (manual session-start, wave-executor)
  benefit from the new signals automatically.
- **`session-start` / `session-plan` / `wave-executor` / `session-end`** — invoked
  unmodified. Autopilot is a controller around the existing session lifecycle, not a
  replacement.
- **`session-registry.mjs`** — peer-count signal source. Autopilot reads but does not
  write to the registry beyond the standard hook.
- **`mode-selector-accuracy`** — autopilot iterations write accuracy learnings exactly
  like manual sessions (Phase B-4 contract). The `chosen` field reflects autopilot's
  auto-execute decision, which equals `recommendation.mode` when confidence ≥ threshold.

## Critical Rules

- **Never auto-merge or auto-push beyond `/close` defaults.** `/close` already pushes to
  origin; autopilot does not add PR creation, merge, or force-push behavior.
- **Iteration boundaries are atomic.** Never abort a running session to start a new one.
- **Kill-switches checked AFTER each session.** Even if a kill-switch will fire after
  iteration N, iteration N completes cleanly first.
- **Iteration 1 sub-threshold falls back to manual; iteration 2+ exits with kill-switch.**
  This asymmetry is intentional — see PRD Q8.
- **`autopilot.jsonl` is the SOLE writer's responsibility of `autopilot.mjs`.** Other
  skills must not append to or rewrite this file.
- **Mode-Selector contract is read-only here.** Autopilot does not modify `selectMode`
  output, does not re-rank alternatives, does not patch confidence values.

## Anti-Patterns

- Do not invoke `/autopilot` from inside a running session. The skill is a top-level
  command; nested invocation is undefined behavior.
- Do not modify `autopilot.jsonl` schema additively without bumping `schema_version`.
  Readers MUST treat unknown fields as a forward-compat signal, not as corruption.
- Do not bypass `selectMode` to force-run a specific mode. If you want to run a specific
  mode, use `/session [mode]` manually — that is autopilot's fallback path.
- Do not lower `--confidence-threshold` below 0.5 in production. The Mode-Selector
  fallback table treats `< 0.5` as suggestion-only; autopilot at that threshold becomes
  a random-walk over modes.
- Do not implement kill-switch logic in this skill. Kill-switch enforcement is in
  `scripts/lib/autopilot.mjs`. The skill documents the contract; the runtime enforces it.

## Configuration

The `autopilot` block in Session Config (`CLAUDE.md` / `AGENTS.md`) accepts the following fields. All fields are optional; omitting a field applies the documented default.

```yaml
autopilot:
  bg-isolation: worktree   # worktree | none (default: worktree) — see #431
```

### bg-isolation

**Type:** `worktree` | `none` — **Default:** `worktree`

Controls whether `autopilot --multi-story` creates a per-story git worktree before spawning sub-sessions.

`worktree` (default): Each story pipeline receives its own isolated git worktree via `EnterWorktree`. Parallel writes are safe because every agent edits a private working copy. Cost: disk space proportional to the number of concurrent stories plus the latency of worktree creation at story-start.

`none` (opt-in): No worktrees are created. Sub-sessions spawn directly in the main working tree. Useful for monorepos where worktree creation is impractical due to large `node_modules`, sparse-checkout setups, or build caches that must be shared. **Requires file-scope discipline:** when `max-stories > 1`, every story must edit a disjoint set of files. If two stories touch the same file simultaneously, edits will collide silently. To enforce acknowledgement of this discipline, `autopilot-multi` requires `--deconflict-paths=<glob>` whenever `bg-isolation: none` AND `max-stories > 1`; omitting the flag is a hard error (exit 1). See `.claude/rules/parallel-sessions.md` PSA-001/002/003.

**Operator-awareness note:** CC 2.1.133 silently flipped `worktree.baseRef` default from `head` to `origin/<default>`, breaking users who relied on unpushed commits being included in their worktree base. The same class of upstream change can affect `bg-isolation` semantics in a future CC release. Treat CC changelog entries related to worktree or `--bg` session behaviour as requiring a re-read of this section before upgrading.

## References

- PRD: `docs/prd/2026-04-25-autopilot-loop.md`
- Implementation (Phase C-1 + C-1.b): `scripts/lib/autopilot.mjs` — exports `runLoop`, `parseFlags`, `writeAutopilotJsonl`, `KILL_SWITCHES`, `FLAG_BOUNDS`, `SCHEMA_VERSION`, `DEFAULT_PEER_ABORT_THRESHOLD`, `DEFAULT_JSONL_PATH`, `DEFAULT_CARRYOVER_THRESHOLD`
- Tests (Phase C-1 + C-1.b): `tests/lib/autopilot.test.mjs`
- Command file: `commands/autopilot.md`
- Mode-Selector contract: `skills/mode-selector/SKILL.md`
- Resource probe: `scripts/lib/resource-probe.mjs`
- Session registry: `scripts/lib/session-registry.mjs`
- Wave-executor return shape: `skills/wave-executor/SKILL.md § Return Shape Contract`
- Sessions.jsonl writer: `skills/session-end/session-metrics-write.md`
- Epic: [#271 v3.2 Autopilot — Autonomous Session Orchestration](https://github.com/Kanevry/session-orchestrator/issues/271)
- Issues: [#277 Phase C scaffold](https://github.com/Kanevry/session-orchestrator/issues/277), [#295 Phase C-1 runtime](https://github.com/Kanevry/session-orchestrator/issues/295), [#300 Phase C-1.b follow-up](https://github.com/Kanevry/session-orchestrator/issues/300)
- Phase A PRD: `docs/prd/2026-04-24-state-md-recommendations-contract.md`
- Phase B PRD: `docs/prd/2026-04-25-mode-selector.md`

## Open Questions (Phase C-1 to resolve)

- `--confidence-threshold=auto` — let autopilot self-tune from accumulated
  `mode-selector-accuracy` learnings? Requires ≥ 20 accuracy learnings before useful.
- STATE.md `autopilot-active: true` field — should other Claude sessions detect via the
  session-registry and refuse to start during an autopilot run? Dogfooding will inform.
- `failed-wave` granularity — distinguish "agent failed but was retried successfully"
  from "wave ended with un-recovered failures"? Requires wave-executor schema audit.
