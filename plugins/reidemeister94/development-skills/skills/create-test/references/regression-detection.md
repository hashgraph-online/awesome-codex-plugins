# Regression Detection (Netflix model)

Static thresholds ("fail if > 500ms") fail in practice: they need per-test calibration that never happens, and background variance forces thresholds up until real regressions slip through. Use dynamic detection instead.

**Anomaly detection (per PR).** A metric is anomalous if it exceeds `mean + n*stddev` over the previous `m` runs. Netflix tuning: **n=4, m=40**. High-variance tests automatically get wider thresholds; no manual calibration; the regressive build shifts the baseline so innocent follow-up builds don't re-alert.

**Changepoint detection (post-merge, warning only).** e-divisive (energy statistic) over the last **100** points. Catches gradual regressions that individually fall under the anomaly threshold but collectively shift the baseline. Ignores one-time spikes; never fails the build.

**Noise reduction.** Run each test ~3x per PR and use the **minimum**, not average or median — external noise (GC pauses, network jitter, CPU contention) only pushes metrics UP, so the minimum is the cleanest estimate.

Result: ~90% fewer alerts while validating more test variations, with high-confidence failures. Source: Netflix TechBlog, "Fixing Performance Regressions Before They Happen" (2021).

Applies to any time-series test output: payload size (data growth), query count (N+1), memory (leaks), suite runtime.
