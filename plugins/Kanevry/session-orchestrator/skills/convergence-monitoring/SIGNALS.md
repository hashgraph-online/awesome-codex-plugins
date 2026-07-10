# Convergence-Monitoring — Signal Reference

Companion to `SKILL.md`. Defines each signal precisely: how to compute it, what threshold
means what, and what false positives look like. Consume this when implementing callers or
debugging unexpected verdicts.

---

## Signal 1: Shrinking Diff (SD)

**What it measures:** Is the volume of change still decreasing wave-over-wave?

A well-converging loop should produce progressively smaller diffs — large changes early
(scaffold, core logic), shrinking to fixes and polish, approaching zero at completion.

### Computation

```bash
# For wave N (run after wave completes):
WAVE_START_REF="<git SHA of wave N start>"
WAVE_END_REF="<git SHA of wave N end>"

# Lines added in this wave (insertions only — deletions tracked separately)
INSERTIONS=$(git diff --shortstat "$WAVE_START_REF" "$WAVE_END_REF" \
  | grep -oE '[0-9]+ insertion' | awk '{print $1}')
DELETIONS=$(git diff --shortstat "$WAVE_START_REF" "$WAVE_END_REF" \
  | grep -oE '[0-9]+ deletion' | awk '{print $1}')
WAVE_DIFF_SIZE=$((${INSERTIONS:-0} + ${DELETIONS:-0}))

# Ratio against peak diff (peak = max diff_size across all waves in session)
PEAK_DIFF_SIZE=$(jq -s 'map(.diff_size) | max' <<< "$WAVE_HISTORY_JSON")
SD_VALUE=$(echo "scale=3; $WAVE_DIFF_SIZE / $PEAK_DIFF_SIZE" | bc)
```

### Thresholds

| SD value  | Interpretation                                         |
|-----------|--------------------------------------------------------|
| > 1.0     | This wave is larger than any previous — churn alert    |
| 0.6–1.0   | Still substantial work; loop is active                 |
| 0.15–0.6  | Shrinking — healthy progression                        |
| 0.0–0.15  | Near-zero change — plateau (convergence or stall)      |

### Trend Mapping

| Condition                                              | Trend        |
|--------------------------------------------------------|--------------|
| SD_VALUE < 0.6 AND less than prior wave's value        | `improving`  |
| SD_VALUE within ±15% of prior wave for 2+ waves       | `plateau`    |
| SD_VALUE > prior wave's SD_VALUE                       | `regressing` |

### False Positives

- **Refactor-heavy waves** produce large diffs (file moves, renames) that look like
  regressions. Mitigation: if `git diff --name-only | grep -c '/dev/null'` is high
  (files deleted/renamed), discount the diff size by 40%.
- **Test-only waves** often produce large line counts with zero functional change.
  The quality-gates pass-rate signal compensates for this.
- **Plateau at large diff** does NOT mean convergence — it means oscillation. Always
  cross-check velocity before issuing a STOP verdict on a large-diff plateau.

### Confidence Formula

```
SD_confidence = min(1.0, completed_waves / 3)
```

Minimum 3 waves before the ratio is meaningful. Below 3 waves: `confidence < 1.0`,
verdict is downgraded per Phase 2 confidence gate.

---

## Signal 2: Pass-Rate Plateau (PR)

**What it measures:** Has the test pass-rate stabilized?

Pass-rate is the most direct quality signal. An improving trend confirms the loop is
fixing real defects. A plateau at ≥ 0.95 is the desired end-state. A plateau below
0.90 is a ceiling — the loop cannot fix what it's breaking.

### Computation

Read from `.orchestrator/metrics/events.jsonl`, filtering `event_type: quality.incremental`
for the current session:

```bash
# Extract pass-rate per wave:
PASS_RATES=$(jq -s --arg session "$SESSION_START_REF" '
  [.[] | select(.session_start_ref == $session and .event_type == "quality.incremental")
       | (.test.passed // 0) / ((.test.total // 1) | if . == 0 then 1 else . end)]
' events.jsonl)

# Latest value:
PR_VALUE=$(echo "$PASS_RATES" | jq 'last')
# Prior value:
PR_PRIOR=$(echo "$PASS_RATES" | jq '.[length - 2] // 0')
```

If `quality.incremental` events are absent (test runner not configured), set
`PR_confidence = 0.0` and trend = `plateau` (neutral; do not block on missing data).

### Thresholds

| PR value  | Interpretation                                             |
|-----------|------------------------------------------------------------|
| ≥ 0.95    | Target zone — loop should stop unless diff still large     |
| 0.90–0.95 | Acceptable; continue if improving                          |
| < 0.90    | Below target — investigate if no improving trend           |
| Δ > +0.05 | Large improvement — continue regardless of other signals   |
| Δ < -0.03 | Regression — issue INVESTIGATE regardless of other signals |

### Trend Mapping

| Condition                                                  | Trend        |
|------------------------------------------------------------|--------------|
| PR_VALUE > PR_PRIOR by > 0.02                              | `improving`  |
| PR_VALUE within ±0.02 of PR_PRIOR for 2+ consecutive waves | `plateau`   |
| PR_VALUE < PR_PRIOR by > 0.03                              | `regressing` |

### False Positives

- **New tests added mid-loop** temporarily lower pass-rate as they're written before
  the implementation is complete. Look for `test.total` growing while `test.passed` is
  stable — this is healthy, not a regression.
- **Flaky tests** produce oscillating pass-rate without real quality change. If pass-rate
  alternates between two values (e.g., 0.97 / 0.94 / 0.97), classify as plateau at the
  higher value and emit a `flaky-tests-suspected` note.
- **Missing test runner** produces no events; default to neutral (plateau at 1.0 with
  confidence 0.0) — never block the loop on missing instrumentation.

### Confidence Formula

```
PR_confidence = min(1.0, quality_events_count / 2)
```

Minimum 2 `quality.incremental` events in this session before the trend is meaningful.

---

## Signal 3: Velocity (VEL)

**What it measures:** Is the agent still producing commits and changes?

Declining velocity is *expected and healthy* as a loop nears completion — early waves
scaffold and wire, later waves polish and fix. Zero velocity for 2+ waves means the loop
has stopped making progress, whether or not quality gates pass.

### Computation

```bash
# Commits in this wave:
VEL_COMMITS=$(git rev-list --count "$WAVE_START_REF".."$WAVE_END_REF")

# Lines changed in this wave:
VEL_LINES=$(git diff --shortstat "$WAVE_START_REF" "$WAVE_END_REF" \
  | awk '{gsub(/[^0-9 ]/,"",$0); print $1+$3}')

# Prior wave lines (for trend):
VEL_LINES_PRIOR=<read from events.jsonl for wave N-1>
```

### Thresholds

| Condition                        | Interpretation                                 |
|----------------------------------|------------------------------------------------|
| VEL_COMMITS = 0, VEL_LINES < 5  | Stall — loop made no progress this wave         |
| VEL_LINES < 20, declining       | Normal wind-down — approaching completion       |
| VEL_LINES stable (not declining) | Oscillation risk — check for churn              |
| VEL_LINES increasing             | Scope expansion or churn — flag for review      |

### Trend Mapping

| Condition                                          | Trend        |
|----------------------------------------------------|--------------|
| VEL_LINES > prior wave by > 20% for 2+ waves      | `improving`  |
| VEL_COMMITS = 0 AND VEL_LINES < 5                 | `plateau`    |
| VEL_LINES declining monotonically                  | `regressing` |

### False Positives

- **Finalization waves** (git commit, SSOT updates, CHANGELOG) produce velocity after
  an implementation plateau. This looks like `improving` but is actually loop close-out.
  If `git log --oneline | head -5` shows only chore/docs commits, classify as `plateau`.
- **Empty waves** (all agents dispatched but none committed) show zero velocity. This is
  a hard stall, not a convergence — always cross-check with PR signal.
- **Large refactor waves** appear as high velocity with SD also high — the loop is
  rewriting, not progressing. The SD + VEL combination triggers INVESTIGATE in the
  decision table.

### Confidence Formula

```
VEL_confidence = min(1.0, completed_waves / 2)
```

---

## Composite Confidence

When producing the final verdict, the composite confidence is:

```
composite_confidence = (SD_confidence + PR_confidence + VEL_confidence) / 3
```

If `composite_confidence < 0.5`:
- STOP → downgraded to CONTINUE
- INVESTIGATE → downgraded to CONTINUE

The caller must surface `low_confidence: [<signal>, ...]` in the report so the user
can decide whether to trust the CONTINUE verdict or force a decision.

---

## Event Schema (convergence.checkpoint)

Written to `.orchestrator/metrics/events.jsonl` after each Phase 2 evaluation:

```json
{
  "schema_version": 1,
  "ts": "<ISO 8601 UTC>",
  "session_start_ref": "<git SHA>",
  "wave_number": 3,
  "event_type": "convergence.checkpoint",
  "verdict": "CONTINUE",
  "signals": {
    "shrinking_diff": { "trend": "improving", "value": 0.42, "confidence": 0.67 },
    "pass_rate":      { "trend": "plateau",   "value": 0.97, "confidence": 1.0  },
    "velocity":       { "trend": "regressing","value": 48,   "confidence": 1.0  }
  },
  "composite_confidence": 0.89,
  "low_confidence": [],
  "notes": []
}
```

All fields required. `notes` is a string array (empty when no anomalies detected).

---

## See Also

`skills/convergence-monitoring/SKILL.md` · `skills/wave-executor/wave-loop.md` ·
`.orchestrator/metrics/events.jsonl` schema
