# Experimentation Strategy Roadmap Examples

Examples for prioritizing experimentation platform investments.

## Scenario Examples

### Team Wants To Platformize Interleaving

**Situation**: One ranking team ran a successful interleaving prototype and wants
platform-wide support.

**Better approach**:
- Identify additional ranking use cases.
- Score design benefit, engineering complexity, and product need.
- Build minimal shared libraries and logging only if repeated value is clear.
- Use `ml-experiment-evaluation` for evaluation specifics.

### Quality Problems Undermine Trust

**Situation**: Teams are running many tests, but misconfiguration and missing
metrics make results hard to trust.

**Better approach**:
- Prioritize `experiment-verification-monitoring`.
- Track invalid test rate and issue detection time.
- Delay more advanced throughput strategies until quality improves.

### Experiment Queue Slows Product Learning

**Situation**: Teams wait weeks for available testing space.

**Better approach**:
- Use `experimentation-throughput-strategy` to identify whether the constraint
  is traffic, QA, analysis, or coordination.
- Consider sensitivity improvements before adopting complicated overlap rules.

### Advanced Method Is Too Hard To Adopt

**Situation**: Data science proposes contextual bandits, but product teams do
not understand setup or monitoring.

**Better approach**:
- Start with one high-value use case.
- Build templates and dashboards before broad rollout.
- Use `adaptive-experimentation-strategy` for readiness checks.

## Anti-Examples

### "Build It Because Top Companies Use It"

**Problem**: Copies advanced methods without matching product need or
infrastructure.

**Fix**: Require local use cases, prototype evidence, and adoption plan.

### "Speed Is The Only Metric"

**Problem**: More tests can reduce trust if results are invalid or confusing.

**Fix**: Pair throughput work with verification and insight-quality metrics.

## Quick Selection Table

| Roadmap Pressure | Better First Skill |
|------------------|--------------------|
| Slow experiment pipeline | `experimentation-throughput-strategy` |
| Noisy or expensive tests | `experiment-sensitivity-optimization` |
| ML model evaluation bottleneck | `ml-experiment-evaluation` |
| Misconfigured experiments | `experiment-verification-monitoring` |
| Questionable results | `trustworthy-experiment-insights` |
| Adaptive methods | `adaptive-experimentation-strategy` |
| Delayed impact | `long-term-impact-evaluation` |
