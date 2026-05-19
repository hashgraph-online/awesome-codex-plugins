---
name: convergence-monitoring
user-invocable: true
tags: [autoresearch, convergence, loop-control, wave-executor]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Monitor iterative improvement loops for convergence. Three signals — shrinking diff,
  pass-rate plateau, velocity — drive a Stop/Continue/Investigate decision at each
  inter-wave checkpoint. Distinct from /evolve (retrospective) and session-reviewer
  (wave output review): convergence-monitoring answers "are we making progress?" not
  "was the last wave correct?". Primary consumer: /autoresearch loops and wave-executor
  inter-wave checkpoints.
attribution: >
  Inspired by cavekit's documented convergence-monitoring concept (MIT, Julius Brussee).
  Implemented from spec since upstream skill not yet published as of 2026-04-30.
---

> **Platform Note:** State files use the platform's native directory: `.claude/` (Claude Code),
> `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). Shared metrics live in
> `.orchestrator/metrics/`. See `skills/_shared/platform-tools.md`.

# Convergence-Monitoring Skill

## Platform-native (CC 2.1.105+)

This skill's watcher is registered as a plugin monitor via `.claude-plugin/plugin.json`'s `experimental.monitors` reference to `monitors/monitors.json`. Each session that loads this plugin auto-starts the watcher in the background (see `scripts/lib/convergence-monitor.mjs`). Each NDJSON stdout line from the watcher becomes a `<task_notification>` event Claude sees mid-session.

For harness < 2.1.105 (no monitor support), the skill's manual probes documented below serve as the fallback path.

## When to Invoke

**Explicit invocation (`/convergence-monitoring`):** Standalone assessment — reads wave
history from `.orchestrator/metrics/events.jsonl`, computes all three signals, reports
verdict + recovery options.

**Embedded (loop context):** `/autoresearch` and `wave-executor` invoke this skill after
each Impl-Core or Impl-Polish wave when `convergence-monitoring: true` is set in Session
Config. The skill returns a structured verdict that the caller uses to gate the next wave.

**NOT a substitute for quality gates.** Quality-gates verify correctness (typecheck, test,
lint). Convergence-monitoring verifies *progress direction* — whether the work is moving
toward done or oscillating/stalling.

---

## Phase 0: Activation Gate

### 0.1 Explicit Invocation

If invoked via `/convergence-monitoring`, skip to Phase 1 unconditionally.

### 0.2 Embedded Invocation

When called from `wave-executor` or `/autoresearch`, check:

1. Read Session Config per `skills/_shared/config-reading.md`. Store as `$CONFIG`.
2. Check `$CONFIG."convergence-monitoring"`. If the field is absent or `false`, return
   verdict `SKIP` immediately — the caller MUST NOT block on a skipped monitoring call.
3. Require `$WAVE_NUMBER` (integer, current wave) and `$SESSION_START_REF` (git SHA) to
   be provided by the caller. If either is absent, emit warning and return `SKIP`.
4. Require at least **2 completed waves** of history. If `$WAVE_NUMBER < 2`, return
   `SKIP` — not enough data to assess trend.

---

## Phase 1: Signal Collection

Read wave history from `.orchestrator/metrics/events.jsonl`. Filter to records matching
`$SESSION_START_REF` and `event_type` in `{wave.start, wave.end, quality.incremental}`.

Compute the three signals in parallel. Each signal produces:

```
{ signal: "<name>", value: <float>, trend: "improving" | "plateau" | "regressing", confidence: 0.0-1.0 }
```

### Signal 1 — Shrinking Diff (SD)

Measures: is the diff still shrinking, or has it reached noise level?

**Computation:**
```
diff_sizes[] = [git diff --stat $wave_N_start_ref $wave_N_end_ref | tail -1 | grep -oE '[0-9]+ insertion' | awk '{print $1}']
  for each completed wave in this session
```

- `value` = ratio of latest wave diff to peak diff (0.0 = unchanged, 1.0 = as large as ever)
- `trend`:
  - `improving` — diff_sizes shrinking monotonically for last 2 waves (value < 0.6)
  - `plateau` — diff_sizes stable within ±15% for 2+ consecutive waves (value 0.0–0.15)
  - `regressing` — diff_sizes growing (value > 1.0 relative to prior wave)
- `confidence` = min(1.0, completed_waves / 3) — unreliable below 3 waves

**False positive flag:** A plateau on diff size with a *large* diff is not convergence —
it may be an oscillation. Cross-check with Signal 3 (velocity) before concluding.

### Signal 2 — Pass-Rate Plateau (PR)

Measures: has the test pass-rate stabilized at a level (high or low)?

**Computation:** Read `quality.incremental` events from `events.jsonl` for this session.
Extract `test.passed / test.total` per wave where the field is present.

- `value` = latest pass-rate (0.0–1.0)
- `trend`:
  - `improving` — pass-rate strictly increasing across last 2 waves
  - `plateau` — pass-rate within ±2% for 2+ consecutive waves
  - `regressing` — pass-rate decreasing
- `confidence` = min(1.0, quality_events_count / 2)

**False positive flag:** A plateau at 1.0 (100% pass) is the desired end-state.
A plateau at < 0.9 with no improving trend is a ceiling signal — see Phase 3.

### Signal 3 — Velocity (VEL)

Measures: commits and modified-line count per wave — declining velocity is normal
as work nears completion; zero velocity for 2+ waves is a stall.

**Computation:**
```
commits_per_wave[] = [git rev-list --count $wave_N_start_ref..$wave_N_end_ref]
lines_per_wave[]   = [git diff --shortstat $wave_N_start_ref $wave_N_end_ref | awk '{print $4+$6}']
  for each completed wave in this session
```

- `value` = lines changed in latest wave (raw integer, not ratio)
- `trend`:
  - `improving` — commits or lines increasing (unusual mid-loop; flag for review)
  - `plateau` — < 5 lines + 0 commits in latest wave
  - `regressing` — lines declining (normal trajectory near convergence)
- `confidence` = min(1.0, completed_waves / 2)

---

## Phase 2: Convergence Decision Table

Aggregate signal trends into a single verdict. Apply the table top-to-bottom; use the
first matching row.

| SD trend   | PR trend   | VEL trend  | Verdict       | Rationale                                                    |
|------------|------------|------------|---------------|--------------------------------------------------------------|
| plateau    | plateau    | plateau    | **STOP**      | All three signals stable — loop has converged.               |
| plateau    | plateau    | regressing | **STOP**      | Velocity decline + stable quality — natural wind-down.       |
| improving  | improving  | regressing | **CONTINUE**  | Still making progress. Velocity decline is expected.         |
| improving  | plateau    | regressing | **CONTINUE**  | Diff still shrinking; pass-rate already high.                |
| plateau    | improving  | regressing | **CONTINUE**  | Pass-rate catching up; diff mostly stable — finishing work.  |
| regressing | *any*      | improving  | **INVESTIGATE** | Diff growing and velocity up — scope expansion or churn.   |
| *any*      | regressing | *any*      | **INVESTIGATE** | Pass-rate declining — regressions introduced.               |
| plateau    | plateau    | improving  | **INVESTIGATE** | Stable diff + stable quality but velocity up — odd state.  |
| *any*      | *any*      | plateau    | **INVESTIGATE** | Velocity zero for 2+ waves — stall or early plateau.        |

**Confidence gate:** If any signal has confidence < 0.5, downgrade STOP → CONTINUE and
INVESTIGATE → CONTINUE (not enough data to act confidently on a Stop or Investigate).
Emit a note: `low-confidence: <signal-names>`.

### Verdict Output (structured)

```json
{
  "verdict": "STOP | CONTINUE | INVESTIGATE | SKIP",
  "signals": {
    "shrinking_diff": { "trend": "...", "value": 0.0, "confidence": 0.0 },
    "pass_rate":      { "trend": "...", "value": 0.0, "confidence": 0.0 },
    "velocity":       { "trend": "...", "value": 0,   "confidence": 0.0 }
  },
  "low_confidence": [],
  "notes": []
}
```

Emit verdict JSON to stdout. Append one JSONL record to
`.orchestrator/metrics/events.jsonl` with `event_type: convergence.checkpoint`.

---

## Phase 3: Non-Convergence Diagnosis

Execute this phase when `verdict == INVESTIGATE`. Skip if `verdict` is STOP or CONTINUE.

The core question: **ceiling or convergence?**

- **Convergence** — the work is done; signals stabilized at the desired state (pass-rate ~1.0,
  diff ~0). Stop is the right action but signals were ambiguous.
- **Ceiling** — progress has halted but the desired state has NOT been reached. Something
  is blocking further improvement.

### 3.1 Ceiling vs Convergence Dichotomy

| Observable                                    | Classification   |
|-----------------------------------------------|------------------|
| pass-rate plateau ≥ 0.95, diff plateau ≈ 0   | Convergence      |
| pass-rate plateau < 0.90 with no trend        | Ceiling          |
| diff growing (SD regressing) for 2+ waves     | Churn / Ceiling  |
| velocity plateau with large outstanding diff  | Stall / Ceiling  |
| velocity plateau with near-zero diff          | Convergence      |

### 3.2 Ceiling Root-Cause Probes

Run these read-only probes to characterize the ceiling. Each probe takes < 5 seconds.

1. **Recurring failures:** `git log --oneline $SESSION_START_REF..HEAD -- '*.test.*' | wc -l`
   — high churn in test files with no new commits to production files suggests a test-fix loop.

2. **Oscillating files:** identify files that appear in 3+ wave diffs in this session.
   These are the **fragile modules** (see architecture.md Module/Seam vocabulary) — their
   seam is leaking complexity into the loop.

3. **Stagnation events:** read `stagnation_events` from the latest session record in
   `sessions.jsonl`. A non-empty list confirms the loop is repeating edit-format-friction
   rather than making functional progress.

4. **Scope drift:** compare `$CONFIG."plan-prd-location"` PRD's in-scope items against
   `git diff --name-only $SESSION_START_REF..HEAD`. Files outside PRD scope indicate
   the loop has expanded beyond its brief.

Report the probe results in Phase 4.

---

## Phase 4: Recovery Suggestions

Present options based on the Phase 3 diagnosis. Do NOT auto-apply any recovery action —
present to the user and await confirmation.

| Diagnosis        | Recovery Option                                               | When to Use                                               |
|------------------|---------------------------------------------------------------|-----------------------------------------------------------|
| Convergence      | **Accept and stop** — declare loop done                      | pass-rate ≥ 0.95, all scope items addressed               |
| Ceiling / Stall  | **Rollback to last-known-good wave** — `git reset --soft`   | Loop is chasing a regression it introduced                |
| Ceiling / Churn  | **Scope reduction** — remove non-PRD files from agent brief  | Loop has drifted outside its brief                        |
| Stall (fragile)  | **Agent-count adjustment** — reduce agents per wave by 50%  | Too many agents editing the same fragile module           |
| Stall (format)   | **Stagnation break** — inject pre-edit grounding prompt      | `stagnation_events` present; loop repeating format errors |
| Ceiling (test)   | **Test-fix isolation** — spawn dedicated fix wave**          | Pass-rate < 0.90 but diff near zero                       |

**Rollback caveat:** Present the exact command (`git reset --soft <wave_N-1_end_ref>`)
and require explicit user confirmation. Never execute it automatically.

### 4.1 Recovery Report Format

```
## Convergence Report — Wave N

Verdict: INVESTIGATE
Diagnosis: Ceiling (pass-rate stuck at 0.82, 3 oscillating files)

Oscillating modules: src/lib/parser.ts, src/lib/tokenizer.ts, tests/parser.test.ts
Stagnation events: 2 (edit-format-friction in src/lib/parser.ts)

Recovery options:
  [A] Scope reduction — remove src/lib/tokenizer.ts from agent brief (outside PRD scope)
  [B] Agent-count adjustment — reduce from 6 to 3 agents next wave (shared fragile module)
  [C] Rollback — git reset --soft <wave_3_end_ref> (destructive, requires confirmation)
  [D] Continue anyway — override monitoring and proceed to next wave

Select option or type 'continue' to override.
```

---

## Anti-Patterns

- **Treating STOP as a quality gate.** Convergence-monitoring answers "are we done making
  progress?" not "is the code correct?" Full Gate quality checks are required separately
  even when verdict is STOP.
- **Acting on low-confidence verdicts without the confidence note.** Below 3 waves of
  history the signals are unreliable. The confidence gate in Phase 2 exists for this reason.
- **Conflating convergence with correctness.** A loop can converge to a broken state
  (pass-rate plateau at 0.6). Always cross-check the pass-rate value, not just the trend.
- **Auto-applying rollback.** Phase 4 recovery options are presented to the user, never
  auto-applied. Rollback is destructive and may discard valid work across parallel sessions
  (PSA-003).
- **Confusing convergence-monitoring with /evolve.** evolve is retrospective (what patterns
  should we learn from finished sessions?). convergence-monitoring is prospective (should the
  current loop continue?).

---

## See Also

- `skills/wave-executor/wave-loop.md` — intended consumer (inter-wave hook integration pending in a follow-up issue)
- `skills/evolve/SKILL.md` — retrospective learning; complements but does not replace
- `skills/quality-gates/SKILL.md` — correctness gate; runs independently of convergence verdict
- `docs/adr/006-autonomous-overnight-research.md` — ADR governing /autoresearch loops
- `.claude/rules/autonomous-agent-safety.md` (AAG-004) — branch-scoped experimentation contract
- `convergence-monitoring/SIGNALS.md` — signal computation reference + threshold rationale
