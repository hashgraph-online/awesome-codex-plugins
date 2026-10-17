# Experimentation Throughput Strategy Examples

Examples for choosing and operating higher-throughput experiment strategies.

## Scenario Examples

### Capacity Queue On A Shared Checkout Surface

**Situation**: Three teams want to test checkout changes in the same two-week
window: payment copy, shipping defaults, and coupon placement.

**Risk**:
- Same surface.
- Same conversion metric.
- Plausible interaction between trust, price perception, and friction.

**Better approach**:
- Isolate the highest-stakes checkout test.
- Defer or split the others by audience or time.
- Add a capacity view so checkout experiments are visible before launch week.

### Independent Back-End Performance Test

**Situation**: One team tests a back-end latency improvement while another tests
copy on a marketing page.

**Risk**:
- Different surfaces and mechanisms.
- Different primary metrics.
- Low interaction risk.

**Better approach**:
- Allow overlap if exposure and metrics are cleanly logged.
- Monitor shared guardrails such as site reliability and conversion.

### Hidden Coordination Bottleneck

**Situation**: Leadership assumes tests are delayed because traffic is scarce.
Pipeline review shows most tests wait for prelaunch QA and metric review.

**Better approach**:
- Do not adopt overlapping tests yet.
- Create an experiment QA checklist and reusable metric review template.
- Re-evaluate traffic capacity after process delays shrink.

### Overlapping Test Conflict Flag

**Situation**: Experiments A and B both affect search ranking and engagement.
The scheduling tool flags shared surface and metric risk.

**Better approach**:
- Require owners to review whether the treatments can interact.
- If the risk is real, isolate or convert one test into an offline/interleaving
  evaluation.
- If the risk is acceptable, document why and monitor segment-level outcomes.

## Anti-Examples

### "Run Everything At Once"

**Problem**: Maximizes apparent throughput while making results hard to trust.

**Fix**: Use overlap rules, conflict dimensions, and owner review.

### "Every Test Must Wait"

**Problem**: Protects interpretability but wastes capacity on independent
experiments.

**Fix**: Use isolated testing for risky cases and overlapping testing for
low-interference cases.

## Quick Selection Table

| Situation | Better Strategy |
|-----------|-----------------|
| Same surface, same metric, high stakes | Isolated test |
| Different surfaces and independent metrics | Overlapping test |
| Unknown conflict risk | Hybrid with owner review |
| Queue caused by QA or analysis delay | Process/tooling improvement first |
| Traffic scarce but precision needed | Improve metric sensitivity |
