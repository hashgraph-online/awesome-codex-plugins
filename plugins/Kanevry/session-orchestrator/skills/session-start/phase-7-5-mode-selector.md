# Phase 7.5: Mode-Selector Pre-Pass (Epic #271 Phase B-2)

> Skip this phase if `persistence` config is `false`, or if the entire Phase 6.6 block was skipped.
> This is the **first wired invocation point** of `selectMode` (previously documented as "None wired" in `skills/mode-selector/SKILL.md` — Phase C `/autopilot` is the second, reserved for #277).

Run immediately before Phase 8 so the Mode-Selector recommendation can influence the AUQ option ordering.

## Distinction from Phase 1.5 Recommendations Banner

Phase 1.5 renders a `📋` banner that reads the **previous** session's archived Recommendation fields from STATE.md (`recommended-mode`, `rationale`, `completion-rate`, etc., written by session-end Phase 3.7a). It is a backward-looking handoff signal.

Phase 7.5 runs `selectMode(signals)` — a **forward-looking** computation over live signals gathered this session (current carryover ratios, recent sessions trend, learnings, bootstrap tier). It emits a `📊` banner.

Both banners may render in the same session-start run. That is intentional: the `📋` banner tells you what the last session recommended; the `📊` banner tells you what the selector computes from all available data right now. They should usually agree. When they diverge, the `📊` signal is more current and should be treated as authoritative.

## Step 1: Build Signals

Invoke `buildLiveSignals` from `scripts/lib/build-live-signals.mjs` to assemble the `signals` object. The helper composes all six source modules (state-md, sessions.jsonl, bootstrap.lock, scanBacklog, learnings, vaultStaleness reserved) with graceful-null on every failure. Pure async, never throws.

```js
import { buildLiveSignals } from '$PLUGIN_ROOT/scripts/lib/build-live-signals.mjs';

// Pass the surfaced top-N learnings (already computed in Phase 6.6) to avoid
// re-reading learnings.jsonl. Other paths default to canonical locations
// (.claude/STATE.md, .orchestrator/metrics/sessions.jsonl, .orchestrator/bootstrap.lock).
const signals = await buildLiveSignals({
  learnings: surfacedTopLearnings,   // array, may be empty
  backlogLimit: 50,
});
```

`buildLiveSignals` is the single SSOT for the Signals shape consumed by `selectMode` and by the autopilot driver protocol (see `skills/autopilot/SKILL.md § Production Wiring`). Phase 7.5 here and the autopilot in-process driver MUST go through this helper — do not inline the recipe in either call site.

**Key source bindings (Phase → field):**

| `signals` field | Populated from | Phase |
|---|---|---|
| `recommendedMode` | `parseRecommendations(frontmatter).mode` | Phase 1.5 |
| `carryoverRatio` | `parseRecommendations(frontmatter).carryoverRatio` | Phase 1.5 |
| `completionRate` | `parseRecommendations(frontmatter).completionRate` | Phase 1.5 |
| `previousRationale` | `parseRecommendations(frontmatter).rationale` | Phase 1.5 |
| `topPriorities` | `parseRecommendations(frontmatter).priorities` | Phase 1.5 |
| `recentSessions` | tail-10 of `.orchestrator/metrics/sessions.jsonl` | Phase 6.6 |
| `bootstrapLock` | `.orchestrator/bootstrap.lock` via `parseBootstrapLock` | Phase 4 |
| `learnings` | surfaced top-N learnings (confidence > 0.3) | Phase 6.6 |
| `backlog` | `scanBacklog({limit: 50})` from `backlog-scan.mjs` (live VCS scan) | Phase 7.5 Step 1 |

## Step 2: Invoke selectMode

Wrap the call in a try/catch. `selectMode` is a pure function with a defensive null-guard and should never throw, but if it does the session must not be blocked.

```js
let recommendation = null;

try {
  recommendation = selectMode(signals);
} catch (err) {
  // Log to sweep.log as mode-selector-error — no banner, continue to Phase 8.
  try {
    const { appendFileSync, mkdirSync } = await import('node:fs');
    mkdirSync('.orchestrator/metrics', { recursive: true });
    appendFileSync(
      '.orchestrator/metrics/sweep.log',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        event: 'mode-selector-error',
        detail: String(err?.message ?? err),
      }) + '\n',
    );
  } catch {}
  // Fall through: recommendation stays null → no banner, Phase 8 uses default AUQ ordering.
}
```

## Step 3: Render the 📊 Banner (conditional)

```js
const pct = (x) => Math.round(x * 100) + '%';

if (!recommendation || recommendation.confidence === 0.0) {
  // No banner. Fall through to Phase 8 with default (unmodified) AUQ ordering.

} else if (recommendation.confidence < 0.5) {
  // Low-confidence suggestion — informational banner only.
  // Do NOT pre-select this mode as the AUQ "Recommended" option.
  console.log(
    `📊 Mode-Selector suggests: ${recommendation.mode}` +
    ` (confidence: ${pct(recommendation.confidence)}) — ${recommendation.rationale}`
  );
  // Phase 8 AUQ ordering: unchanged from default. The banner is purely informational.

} else {
  // confidence >= 0.5 — pre-select as AUQ option 1 with "(Recommended by Mode-Selector)" label.
  console.log(
    `📊 Mode-Selector recommends: ${recommendation.mode}` +
    ` (confidence: ${pct(recommendation.confidence)}) — ${recommendation.rationale}`
  );
  // Phase 8 AUQ ordering: modified — see Step 4.
}
```

## Step 4: AUQ Option Ordering Protocol (Phase 8 integration)

Phase 8 reads `presentation-format.md` for the AUQ structure. The Mode-Selector output modifies option ordering **only when `recommendation.confidence >= 0.5`**. Do not modify `presentation-format.md` — the ordering adjustment is a runtime protocol applied at the call site in Phase 8.

**When `recommendation.confidence >= 0.5`:**

1. AUQ option 1 label: `"<recommendation.mode> (Recommended by Mode-Selector)"`.  
   AUQ option 1 description: `recommendation.rationale` + any relevant focus issues from Phase 3/6.
2. `recommendation.alternatives` (when non-empty, may have up to 3 entries) become options 2..N.  
   Each alternative label: `"<alt.mode> (confidence: <pct(alt.confidence)>%)"`.  
   Each alternative description: a brief label derived from the mode name (e.g. "housekeeping → cleanup cycle", "feature → standard incremental delivery").
3. Total AUQ options ≤ 4 (AUQ tool cap). If `alternatives.length >= 3`, show the first 2 and add a final option: `"Other (specify)"` with description `"Enter a custom mode or focus not listed above."`.
4. Any previously-computed focus recommendations from the Session Overview (Phase 8's ## Recommended Focus section) are folded into the descriptions of whichever option matches that mode. They are NOT added as separate AUQ options.

**When `recommendation.confidence < 0.5` (including `0.0`):**

AUQ option ordering is **unchanged** from the existing `presentation-format.md` default. The `📊` banner (if rendered) is informational only and does not influence option ordering.

**Codex CLI / Cursor IDE fallback (no AUQ tool):**

When operating on Codex CLI or Cursor IDE, apply the same ordering logic but render as a numbered Markdown list (per `presentation-format.md` Codex fallback section). When `confidence >= 0.5`, prefix option 1 with `(Recommended by Mode-Selector)`.

## Step 4.5: Context-Pressure Annotation (#332)

When `selectMode()` returns `context_pressure: { score, level }` with `level !== 'low'`, surface it in the AUQ option `description` for the recommended option (NOT in the question itself — the question must stay short):

| Level | Annotation to append to recommended option description |
|---|---|
| `low` | (no annotation) |
| `medium` | `"(context-pressure: medium — scope is moderately large or carryover present)"` |
| `high` | `"(context-pressure: high — recommend reducing scope or preferring deep mode)"` |

**Append** the annotation to the existing description — do NOT replace it. Example for a `feature` recommendation with medium pressure:

```
description: recommendation.rationale + " (context-pressure: medium — scope is moderately large or carryover present)"
```

**Additional rule when `level === 'high'` and recommended mode is `feature` or `housekeeping`:**

Include the `deep` alternative's score advantage in its description to help the user make an informed choice. The AUQ ordering protocol (Step 4) already places `alternatives` in options 2..N by confidence; context-pressure flows in as a delta in `computeDelta()` before scoring (wired in W2). The description nudge is the only addition required here:

```
// deep alternative description when context pressure is high and recommended mode is feature/housekeeping:
"(confidence: <pct(alt.confidence)>) — deep mode absorbs higher scope; preferred under high context-pressure"
```

This annotation is applied at the same site as Step 4's option-description assembly — add it conditionally after building the base descriptions.

Cross-reference: `skills/mode-selector/SKILL.md` § Context-Pressure Signal (#332) for the full heuristic and `computeContextPressure` contract.

## Step 5: Graceful No-Op Rules

All of the following result in **no banner and default AUQ ordering** — they are silent no-ops that do not block session startup:

| Condition | Why | Behaviour |
|---|---|---|
| `persistence: false` | Phase 6.6 skipped, no learnings/sessions data | Phase 7.5 skipped entirely |
| STATE.md absent | `rec === null`, all Phase-A `signals.*` are null | `selectMode` returns `confidence: 0.0` → no banner |
| Pre-v1.1 STATE.md (no Phase A fields) | `parseRecommendations` returns `null` → `rec === null` | Same as above |
| `selectMode` throws (should never happen) | Pure function contract violation | `mode-selector-error` logged to sweep.log, no banner |
| `recommendation.confidence === 0.0` | Default fallback branch in selector | No banner, default ordering |
| `recommendation === null` (catch path) | Error during invocation | No banner, default ordering |
| `.orchestrator/bootstrap.lock` absent | `bootstrapLockObj === null` | Signals still valid; lock contributes 0 delta |
| `sessions.jsonl` absent or < 1 entry | `recentSessions: []` | Signals still valid; trend contributes 0 delta |
| `glab`/`gh` CLI missing or non-zero exit | `scanBacklog` returns null | `signals.backlog: null`; backlog signal contributes 0 delta. Phase B-3 (#293). |
| no git origin | `detectVcs()` returns null → `scanBacklog` short-circuits | Same as above |

Note: `selectMode` is designed to NEVER throw (pure function, defensive null-guard). The try/catch in Step 2 is belt-and-suspenders. If it does throw, the `mode-selector-error` breadcrumb in sweep.log is the observable signal for debugging without blocking the session.

## Step 6: Record Mode-Selector Accuracy Learning (post-AUQ, Phase B-4)

Runs **after Phase 8 collects the user's mode choice** (or skip on Codex/Cursor numbered-list response). This step writes a `mode-selector-accuracy` learning to `.orchestrator/metrics/learnings.jsonl` so future Mode-Selector heuristic tuning has feedback data. Phase B-4 (#294).

**Trigger conditions (ALL must be true):**

1. Phase 7.5 produced a non-null `recommendation` (banner rendered — Step 3 was either the `< 0.5` or `>= 0.5` branch).
2. The user actively confirmed or overrode via AUQ (or numbered-list reply on Codex/Cursor). Timeouts and aborts do NOT trigger a write.
3. `recommendation.mode` and the user's chosen mode are both valid `isValidMode` values from `recommendations-v0.mjs`.

**Skip silently when:**

- Phase 7.5 was skipped (`persistence: false` or Phase 6.6 skipped).
- `recommendation === null` or `recommendation.confidence === 0.0` (no banner rendered).
- The chosen mode does not parse cleanly (e.g., custom "Other" free-text response).

**Write contract (delegated to `recordAccuracy` in `mode-selector-accuracy.mjs`):**

```js
import { recordAccuracy } from '$PLUGIN_ROOT/scripts/lib/mode-selector-accuracy.mjs';

// After Phase 8 AUQ resolves with the user's choice:
const result = await recordAccuracy({
  recommended: recommendation.mode,   // from Phase 7.5 Step 2
  chosen:      userChosenMode,        // from Phase 8 AUQ answer, normalized to canonical mode
  sessionId:   `${branch}-${ymd}-${hhmm}`, // matches the wave-executor session_id format
});

if (!result.ok) {
  // Log to sweep.log as mode-selector-accuracy-skip; never block session-start.
  appendFileSync(
    '.orchestrator/metrics/sweep.log',
    JSON.stringify({
      timestamp: new Date().toISOString(),
      event: 'mode-selector-accuracy-skip',
      detail: result.reason, // 'no-recommendation' | 'unknown-mode' | 'missing-session-id' | 'append-failed: ...'
    }) + '\n',
  );
}
```

**Lifecycle handling (NOT this step's job):**

The helper writes a fresh entry at `confidence: 0.5`. The +0.15 confirm / -0.20 contradict semantics are applied later by `evolve` and `session-end` when the same `(type, subject)` pair recurs across sessions. Subject pattern: `<recommended>-selected-vs-<chosen>` — agreement and override outcomes land at distinct subjects so they accumulate independently.

**Graceful no-op rules** (none of these block session-start):

| Condition | Behaviour |
|---|---|
| recommendation is null | helper returns `{ok: false, reason: 'no-recommendation'}` |
| chosen mode unparsable | helper returns `{ok: false, reason: 'unknown-mode'}` |
| `appendLearning` validation fails | helper returns `{ok: false, reason: 'append-failed: ...'}` |
| learnings.jsonl write I/O error | same as above; sweep.log captures detail |

## References

- Implementation: `scripts/lib/mode-selector.mjs::selectMode`
- Skill contract: `skills/mode-selector/SKILL.md`
- Phase A parser: `scripts/lib/state-md.mjs::parseRecommendations`
- Phase A writer: `skills/session-end/SKILL.md` Phase 3.7a
- Bootstrap lock reader: `scripts/lib/bootstrap-lock-freshness.mjs::parseBootstrapLock`
- Session normalizer: `scripts/lib/session-schema.mjs::normalizeSession`
- Backlog signal: `scripts/lib/backlog-scan.mjs::scanBacklog` (Phase B-3, #293)
- Accuracy helper: `scripts/lib/mode-selector-accuracy.mjs::recordAccuracy` (Phase B-4, #294)
- PRD: "Mode Selector" (#276; archived in the private Meta-Vault)
- Issues: [#292 Phase B-2 integration](https://github.com/Kanevry/session-orchestrator/issues/292), [#293 Phase B-3 backlog signal](https://github.com/Kanevry/session-orchestrator/issues/293), [#294 Phase B-4 accuracy feedback](https://github.com/Kanevry/session-orchestrator/issues/294)
