# Experiment Verification Monitoring Examples

Examples for catching experiment-quality issues before they damage trust.

## Scenario Examples

### Treatment Configured For Wrong Audience

**Situation**: A test intended for new users is accidentally eligible for all
users.

**Better approach**:
- Prelaunch QA verifies eligibility rules.
- Canary checks exposure volume and segment mix.
- Alert fires if returning-user exposure exceeds threshold.

### Exposure Logging Missing

**Situation**: Assignment works, but exposure events never fire for the treatment.

**Better approach**:
- Prelaunch metric validation checks exposure events.
- Canary compares assignment and exposure counts.
- Experiment pauses until logging is fixed.

### A/A Test Finds Imbalance

**Situation**: Identical treatments produce a suspicious metric difference.

**Better approach**:
- Investigate assignment balance and metric pipeline.
- Check whether eligibility or exposure rules differ.
- Do not dismiss the issue because "nothing changed."

### Overlapping Tests Interfere

**Situation**: Two active experiments modify recommendations on the same page.

**Better approach**:
- Scheduling metadata flags shared surface and metric.
- Owners review whether tests can coexist.
- Active monitoring segments by combined exposure when overlap is allowed.

## Anti-Examples

### "QA Passed On One Browser"

**Problem**: A single manual check does not verify assignment, exposure, metrics,
or affected segments.

**Fix**: Use a standard prelaunch verification checklist and automate repeated
checks.

### "We'll Notice At Readout"

**Problem**: Final readout is too late to recover wasted traffic and user harm.

**Fix**: Add canaries, dashboards, and alerts for active tests.

## Quick Selection Table

| Failure Risk | Better Check |
|--------------|--------------|
| Wrong audience | Eligibility and exposure validation |
| Broken treatment | QA tool and canary |
| Missing metrics | Metric freshness and exposure dashboard |
| Platform drift | Periodic A/A tests |
| Cross-test conflict | Leakage/interference monitoring |
