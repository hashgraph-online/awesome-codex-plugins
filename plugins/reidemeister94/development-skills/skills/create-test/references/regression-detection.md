# Regression Detection Patterns

## The Problem with Static Thresholds

Static thresholds ("fail if response time > 500ms") are the default approach to regression detection in CI. They fail in practice:

- Require manual calibration per test — most never get calibrated
- Background variance triggers false positives → developers ignore alerts
- Constant threshold increases to avoid noise → real regressions slip through
- Netflix found only 30% of test variations had thresholds when using this approach

## Anomaly Detection (Immediate — Per PR)

A metric is anomalous if it exceeds `mean + n * stddev` computed from the previous `m` test runs.

**Netflix's tuning:** n=4, m=40 (configurable per team).

**Why it works:**
- Dynamic thresholds: high-variance tests automatically get wider thresholds
- No manual calibration required — works for any test, any metric
- Subsequent innocent builds don't trigger alerts (the regressive build shifts the baseline)

### Implementation Pattern (Python / pytest)

```python
import json
import statistics
from pathlib import Path

HISTORY_FILE = Path("tests/.perf_history.json")
N_STDDEV = 4
WINDOW = 40

def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {}

def record_and_check(test_name: str, value: float) -> tuple[bool, str]:
    """Record metric, return (is_anomaly, message)."""
    history = load_history()
    values = history.get(test_name, [])

    if len(values) >= WINDOW:
        mean = statistics.mean(values[-WINDOW:])
        std = statistics.stdev(values[-WINDOW:])
        threshold = mean + N_STDDEV * std

        if value > threshold:
            return True, (
                f"ANOMALY: {test_name} = {value:.2f} "
                f"(threshold: {threshold:.2f} = {mean:.2f} + {N_STDDEV}*{std:.2f})"
            )

    values.append(value)
    history[test_name] = values[-WINDOW * 2:]  # keep 2x window
    HISTORY_FILE.write_text(json.dumps(history, indent=2))
    return False, f"OK: {test_name} = {value:.2f}"
```

## Changepoint Detection (Retroactive — Post-Merge)

Identifies boundaries between two distinct data distribution patterns in a time series. Unlike anomaly detection, it catches gradual regressions that individually fall below the anomaly threshold but collectively shift the baseline.

**Algorithm:** e-divisive (energy statistic) on the last 100 data points.

**Key properties:**
- Does NOT fail tests — produces warnings for investigation
- Ignores one-time spikes (requires sustained distribution shift)
- Catches regressions already merged but not yet shipped

### When to Use Each

| Technique | Speed | Catches | False Positive Rate |
|-----------|-------|---------|-------------------|
| Anomaly detection | Immediate (per PR) | Sudden spikes, obvious regressions | Low (n=4σ) |
| Changepoint detection | Delayed (batch analysis) | Gradual degradation, cumulative regressions | Very low |
| Static thresholds | Immediate | Only regressions that cross fixed limits | High |

## Noise Reduction: Multiple Runs

Every test should run 3 times per PR. Use the **minimum** value across runs as the representative metric.

**Why minimum, not average or median:**
- External noise (GC pauses, network jitter, CPU contention) pushes metrics UP, not down
- Average: too many false positives (one outlier shifts the mean)
- Median: still affected when 2 of 3 runs hit noise
- Minimum: most effective at eliminating external noise

## Netflix Results

After switching from static thresholds to anomaly + changepoint detection:
- **90% reduction in alerts** while validating MORE test variations
- Much higher probability of genuine regression when alerts fire
- PR performance tests went from "almost constantly red" to mostly green with high-confidence failures

Source: Netflix TechBlog, "Fixing Performance Regressions Before They Happen" (2021)

## Applying This to Non-Performance Tests

The same pattern works for any measurable test output:
- **Response payload size** — detect unintended data growth
- **Query count** — detect N+1 regressions
- **Memory allocation** — detect memory leaks
- **Test execution time** — detect performance regressions in the test suite itself

Track these as time series per test, apply anomaly detection.
