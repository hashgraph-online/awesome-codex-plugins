---
name: mode-selector
description: >
  Use this skill when performing deterministic mode selection for session-start. Reads Phase A STATE.md
  recommendations + (future) learnings, sessions, backlog, bootstrap signals
  and returns {mode, rationale, confidence, alternatives}. Pure-function
  contract — no side effects, no STATE.md writes. Phase B scaffold (issue #276);
  full heuristic is follow-up sub-issues.
model: haiku
user-invocable: false
tags: [phase-b, autopilot, mode-selection, scaffold]
---

# Mode-Selector Skill

## Status

Heuristic v1 active (issue #291, shipped 2026-04-25). Wired into session-start Phase 7.5
(issue #292, shipped 2026-04-25). Backlog signal source live (issue #293, shipped 2026-04-25):
`signals.backlog` is populated by `scripts/lib/backlog-scan.mjs::scanBacklog`. Accuracy feedback
loop live (issue #294, shipped 2026-04-25): `scripts/lib/mode-selector-accuracy.mjs::recordAccuracy`
writes a `mode-selector-accuracy` learning after the user confirms/overrides the Phase 7.5 banner.
Phase B contract is **closed**. Phase C (#277) `/autopilot` Loop Command is the next epic and
owns its own PRD.

## Purpose

Mode-Selector centralizes the session-mode decision across all consumers: session-start Phase 1.5
banner, `/autopilot` (Phase C), and any future caller that needs a structured recommendation rather
than ad-hoc heuristics inline at the call site. Before this skill existed, mode-picking logic was
either implicit (user-typed free text) or embedded directly in session-start with no reuse path.

Phase A (`state-md.mjs::parseRecommendations`, issue #272) established the `recommended-mode`
frontmatter field written by session-end Phase 3.7a. Phase B is the skill that reads that field
(plus future signals) and returns a structured recommendation. The key output is a four-field
tuple: `{mode, rationale, confidence, alternatives}`. `mode` is the recommended session type.
`rationale` is a ≤120-char human-readable explanation. `confidence` is a float (0.0–1.0)
indicating how strongly the selector commits to the recommendation. `alternatives` is an ordered
list of `{mode, confidence}` objects representing the next-best choices, enabling callers to offer
override options without re-running the selector.

The selector is a pure function: given the same `signals` object it always returns the same output.
No file I/O, no network calls, no global state. This makes it trivially testable and safe to call
from any skill without side-effect risk.

## Contract

### Input: `signals` object

- `recommendedMode` (string|null) — Phase A frontmatter field; the `recommended-mode` key from `parseRecommendations()`
- `topPriorities` (number[]|null) — issue numbers from the `top-priorities` frontmatter field
- `carryoverRatio` (number|null) — float 0.0–1.0 from Phase A; fraction of issues carried over from previous session
- `completionRate` (number|null) — float 0.0–1.0 from Phase A; ratio of planned issues completed
- `previousRationale` (string|null) — the `rationale` string written by session-end Phase 3.7a
- `learnings` (object[]|null) — RESERVED; not consumed in scaffold; Phase B-1 heuristic input
- `recentSessions` (object[]|null) — RESERVED; not consumed in scaffold; recent-sessions trend input
- `backlog` (object|null) — `{criticalCount, highCount, staleCount, byLabel, total, vcs, limit}` from `scripts/lib/backlog-scan.mjs::scanBacklog` (Phase B-3, #293). `null` when CLI missing or no git origin — contributes 0 delta.
- `bootstrapLock` (object|null) — RESERVED; not consumed in scaffold; tier-aware sizing hints

### Output: `Recommendation` object

| Field | Type | Range / Values | Purpose |
|---|---|---|---|
| `mode` | string enum | `housekeeping` \| `feature` \| `deep` \| `discovery` \| `evolve` \| `plan-retro` | Recommended session type |
| `rationale` | string | ≤120 chars | Human-readable explanation for the recommendation |
| `confidence` | float | 0.0–1.0 | Selector commitment; see Fallback Behavior for threshold semantics |
| `alternatives` | `{mode, confidence}[]` | 0–3 entries; may be empty, never null | Next-best modes with partial confidence scores |

## Invocation Points

### Current

- **`skills/session-start/SKILL.md` Phase 7.5** — first wired invocation (issue #292). Renders
  `📊 Mode-Selector suggests:` when `confidence < 0.5` (informational, no pre-selection) or
  `📊 Mode-Selector recommends:` when `confidence >= 0.5` (pre-selects AUQ option 1). Eight
  graceful no-op conditions documented inline. Note: Phase 1.5 `📋` banner is NOT a Mode-Selector
  invocation — it reads Phase A STATE.md frontmatter directly via `parseRecommendations`; the
  Mode-Selector lives at Phase 7.5.
- **`tests/lib/mode-selector.test.mjs`** — 75 tests (7 describe blocks) exercising SPIRAL,
  CARRYOVER, high-confidence path, conflicting-signals, stale-signals, alternatives generation,
  and defensive parsing. `mode-selector.mjs` coverage 100%/100%/100%/100%. Issue #291.

### Future

- **`/autopilot` (Phase C, #277)** — auto-execute when `confidence >= 0.85` AND
  SPIRAL/FAILED/carryover-50% kill-switches pass. No user prompt in that path.

### Companion modules (Phase B closure)

- **`scripts/lib/backlog-scan.mjs::scanBacklog`** — feeds `signals.backlog`. Phase B-3 (#293).
  Module-level cache, glab/gh auto-detection, returns `null` on graceful-degradation paths.
- **`scripts/lib/mode-selector-accuracy.mjs::recordAccuracy`** — post-AUQ feedback writer. Phase B-4 (#294).
  Subject pattern `<recommended>-selected-vs-<chosen>`; agreement and override land at distinct subjects so
  the existing learning lifecycle can confirm/contradict them independently.

## Scaffold Heuristic (v0)

The v0 scaffold implements a minimal three-branch passthrough. It is intentionally thin so
the contract is exercisable by tests before the full Phase B-1 rule-set lands.

```
selectMode(signals):
  if signals is null/undefined:
    → {mode: 'feature', rationale: 'scaffold: null signals → default', confidence: 0.0, alternatives: []}
  if signals.recommendedMode is valid mode:
    → {mode: <recommendedMode>, rationale: 'scaffold: passthrough of Phase A recommended-mode', confidence: 0.5, alternatives: []}
  otherwise:
    → {mode: 'feature', rationale: 'scaffold: missing/invalid recommendedMode → default', confidence: 0.0, alternatives: []}
```

Note: the full Phase B heuristic — rule-set consuming learnings.jsonl, recent sessions trend,
VCS backlog priority-weighting, and bootstrap.lock tier — is the Phase B-1 follow-up sub-issue.

## Fallback Behavior

- `confidence = 0.0` means the selector is declining to choose; caller should fall back to its own
  logic (v0 heuristic) or prompt the user without pre-selecting any option.
- `0.0 < confidence < 0.5` means low-confidence; caller should present as a suggestion, never
  auto-execute; AUQ should show the recommended mode without marking it as "Recommended".
- `confidence ≥ 0.5` means accept as default; present as the pre-selected AUQ option; user can
  still override.
- `confidence ≥ 0.85` (future Phase C threshold) means suitable for autonomous execution in
  `/autopilot` mode without user prompt, subject to kill-switch guards.

## Integration with Other Skills

- **`state-md.mjs::parseRecommendations`** → read Phase A frontmatter fields; consumed via
  `signals.recommendedMode`, `signals.carryoverRatio`, `signals.completionRate`, etc.
- **`recommendations-v0.mjs::isValidMode`** → mode enum validation; import and use — do not
  redefine the six-value enum inline.
- **`learnings.mjs::readLearnings`** → reserved for Phase B-1 heuristic input via
  `signals.learnings`
- **`session-schema.mjs::normalizeSession`** → reserved for recent-sessions trend input via
  `signals.recentSessions`
- **`bootstrap-lock-freshness.mjs::parseBootstrapLock`** → reserved for tier-aware sizing hints
  via `signals.bootstrapLock`
- **`gitlab-ops.md`** → reserved for VCS backlog scan (Phase B-3) via `signals.backlog`

## Critical Rules

- **Pure function only.** No I/O, no side effects, no throws, no dynamic imports. `selectMode`
  must be synchronous and referentially transparent.
- **Never write STATE.md.** session-start or Phase C writes any derived state; the selector is
  read-only. session-end Phase 3.7a is the sole writer of `recommended-mode`.
- **Every return path returns all 4 keys.** The `{mode, rationale, confidence, alternatives}`
  shape is enforced by tests; missing keys are a contract violation.
- **`alternatives` is always an array.** Never `null`, never `undefined`, may be empty (`[]`).
- **Use `isValidMode` from `recommendations-v0.mjs`.** Do not redefine the mode enum; drift
  between selector and validator is a schema bug.

## Anti-Patterns

- Do not call `selectMode` from inside session-end. session-end Phase 3.7a is the SOLE producer
  of the `recommended-mode` frontmatter field; the selector is a consumer only.
- Do not add logging inside `selectMode` — the function must stay pure. Logging (breadcrumbs,
  sweep.log events) happens at the call site, not inside the selector.
- Do not expand the scaffold to consume `learnings` inside this session. That is Phase B-1
  follow-up work; the RESERVED fields in `signals` are intentionally ignored here.
- Do not treat `confidence` as binary. Threshold semantics (`0.5` accept-as-default, `0.85`
  auto-execute) live at the call site, not in the selector. The selector emits a float; the
  caller decides what to do with it.

## References

- Implementation: `scripts/lib/mode-selector.mjs`
- Tests: `tests/lib/mode-selector.test.mjs` (selector core, 75 tests), `tests/lib/backlog-scan.test.mjs` (signal source), `tests/lib/mode-selector-accuracy.test.mjs` (feedback loop)
- Backlog signal source: `scripts/lib/backlog-scan.mjs` (Phase B-3, #293)
- Accuracy feedback writer: `scripts/lib/mode-selector-accuracy.mjs` (Phase B-4, #294)
- PRD: "Mode Selector" (#276; archived in the private Meta-Vault)
- Epic: [#271 v3.2 Autopilot](https://github.com/Kanevry/session-orchestrator/issues/271)
- Issue: [#276 Phase B Mode-Selector](https://github.com/Kanevry/session-orchestrator/issues/276)
- Phase A Contract PRD: "STATE.md Recommendations Contract" (#271; archived in the private Meta-Vault)
- Phase A parser: `scripts/lib/state-md.mjs::parseRecommendations` (issue #272)
- Phase A writer: `skills/session-end/SKILL.md` Phase 3.7a (issue #273)
- Mode enum: `scripts/lib/recommendations-v0.mjs::isValidMode`

## Context-Pressure Signal (#332)

Context-pressure is a single 0.0–1.0 score combining scope size, cross-cutting keyword presence,
and recent-session carryover-ratio. It modulates `selectMode()` decisions without overriding them:

| Level  | Score       | Effect on mode delta                                  |
|--------|-------------|-------------------------------------------------------|
| low    | < 0.3       | feature +0.05 (rewards clean scope)                   |
| medium | 0.3 – 0.7   | no adjustment                                         |
| high   | ≥ 0.7       | feature −0.15, housekeeping −0.10 (favors deep)       |

### Components

- **Scope**: `(priorityCount - 3) / 10`, clamped to [0, 0.5] — 0 issues = 0, 3 = 0, 8 = 0.5, 13+ = 0.5
- **Cross-cutting keywords**: +0.25 fixed bonus if task description matches `/across all|every (skill|agent|repo)|repo-?wide|cross-cutting|rename across|massive refactor/i`
- **Carryover**: mean of `effectiveness.carryover / effectiveness.planned_issues` over the last 5 sessions, then `ratio - 0.3` clamped to [0, 0.25]

### Examples

- 2 issues, no cross-cutting keywords, low carryover → score ≈ 0.0 (low) → feature +0.05
- 8 issues, "rename across all skills", carryover 0.4 → score ≈ 0.5 + 0.25 + 0.1 = 0.85 (high) → feature −0.15, housekeeping −0.10
- 5 issues, no keywords, carryover 0.2 → score ≈ 0.2 (low) → feature +0.05

### Output

`selectMode()` now returns `context_pressure: { score, components: { scope, keywords, carryover }, level }` on all
return paths. The rationale string is annotated with `; pressure:<level>(<score>)` when level is `medium` or `high`.

### API

`computeContextPressure(signals)` is exported as a standalone pure function for testing and
future callers (e.g. session-start Phase 7.5 AUQ rendering — deferred to W3-C5).

### Constraints

Context-pressure is NOT an Express Path gate (Express Path is structural: housekeeping + ≤3 issues).
It is a complementary heuristic that surfaces in the session-start AUQ alongside the recommended mode.
Missing signal fields contribute 0 to the score — no NaN propagation.

## Open Questions (for Phase B-1 follow-up)

- Learnings freshness window — default 30d? Configurable per-type or a single global TTL?
- Backlog priority weighting — rule-based (`priority:critical = +0.2` confidence bonus) vs.
  learned from historical completion rates?
- Alternative-generation algorithm — top-N non-selected modes scored by partial signal match, or
  fixed set derived from v0 heuristic branches?
- Confidence computation — additive bonuses per signal (each signal adds a fixed delta) or
  multiplicative penalties (each contradicting signal scales down a base score)?
- Per-session-type thresholds — should `housekeeping` require higher confidence for auto-execution
  than `deep` given the asymmetry in effort and risk?
