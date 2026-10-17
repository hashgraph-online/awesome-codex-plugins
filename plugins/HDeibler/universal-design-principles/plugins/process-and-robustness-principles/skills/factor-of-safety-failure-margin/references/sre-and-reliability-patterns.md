# SRE and reliability patterns reference

A reference complementing `factor-of-safety-failure-margin` with the modern site-reliability-engineering vocabulary and patterns.

## Site Reliability Engineering (SRE)

Site Reliability Engineering, formalized at Google and codified in *Site Reliability Engineering* (O'Reilly, 2016), is the modern discipline of running production software at scale. Many of its practices are explicit factor-of-safety thinking applied to software:

### Service-level objectives (SLOs)

A formal target for system reliability:

- **SLO**: 99.9% of requests succeed within 500ms over a rolling 30-day window.
- **SLI** (indicator): the actual measurement of success/latency.
- **SLA**: a contractual commitment, typically looser than the SLO, attached to consequences.

The SLO is the safety target. Operating well above the SLO means there's margin for risk-taking; operating at or below the SLO means stop and stabilize.

### Error budgets

The complement of an SLO:

- 99.9% SLO → 0.1% error budget.
- Translates to ~43 minutes of permitted downtime per month, or ~26 seconds per day.

The team can spend the error budget on risk: faster releases, infrastructure changes, experiments. When the budget is consumed, releases pause; teams focus on reliability work until the budget recovers.

This is explicit safety-factor management: the budget is the margin; operating within it is sustainable; exceeding it triggers protective response.

## Reliability patterns

### Timeouts

Every external call needs a timeout. Without one, a slow dependency can exhaust resources.

```js
// Good: explicit timeout
const result = await fetch(url, { signal: AbortSignal.timeout(2000) });

// Bad: no timeout (default may be unbounded)
const result = await fetch(url);
```

### Retries with exponential backoff and jitter

For transient failures, retry — but not aggressively. Exponential backoff prevents stampedes; jitter prevents synchronized retries.

```js
async function withRetry(fn, opts = {}) {
  const { maxRetries = 3, initialDelay = 100, maxDelay = 10000 } = opts;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      const exp = initialDelay * 2 ** attempt;
      const jitter = Math.random() * exp * 0.5;
      await sleep(Math.min(exp + jitter, maxDelay));
    }
  }
}
```

### Circuit breakers

When a dependency is failing, stop calling it for a while. Two common states:

- **Closed**: normal operation; requests pass through.
- **Open**: dependency is failing; requests fail fast without trying the dependency.
- **Half-open**: periodically try one request to see if the dependency has recovered.

```js
class CircuitBreaker {
  constructor(threshold = 5, timeout = 30_000) {
    this.failures = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.openedAt = null;
  }

  async call(fn) {
    if (this.openedAt && Date.now() - this.openedAt < this.timeout) {
      throw new Error('circuit open');
    }
    try {
      const result = await fn();
      this.failures = 0;
      this.openedAt = null;
      return result;
    } catch (err) {
      this.failures++;
      if (this.failures >= this.threshold) {
        this.openedAt = Date.now();
      }
      throw err;
    }
  }
}
```

### Bulkheading

Isolating resources so failure in one area doesn't cascade. For example, separate connection pools per dependency so a slow dependency doesn't exhaust the pool used by a fast one.

### Graceful degradation

When something fails, provide reduced functionality rather than no functionality:

- Search service down → show recents.
- Recommendation engine down → show generic feed.
- Profile data fetch fails → show placeholder card.

The user gets *something*; the broken feature doesn't break the whole product.

### Canary releases

Deploy a new version to a small percentage of traffic; monitor; expand gradually. Each percentage increase is a safety factor — issues are caught before full rollout.

### Feature flags

Ship code disabled; enable it at runtime per-cohort or per-percentage. Allows fast rollback without code redeploy.

## Capacity planning

### Headroom guidelines

| Utilization | Status | Action |
|---|---|---|
| < 50% | Healthy | Normal operation |
| 50–70% | Watch | Capacity-planning meeting; investigate growth |
| 70–85% | Warning | Add capacity within days |
| 85%+ | Critical | Page on-call; immediate capacity addition or load shedding |

Acting at 70% is far cheaper than acting at 100% (when the system has already started failing).

### Load shedding

When the system can't handle the offered load, shed some load explicitly rather than letting everything degrade:

- Reject some requests at the load balancer.
- Disable heavy features (recommendations, exports).
- Show a "we're busy, try in a minute" message.

Better than slow degradation that affects all users equally.

## Common failures of failure-margin design

- **No timeouts.** A slow dependency exhausts thread pools or connection pools; the whole service slows or hangs.
- **Aggressive retries.** Retrying immediately and infinitely. The struggling dependency gets DDoS'd by your retries.
- **No circuit breaker.** Continuing to call a dead dependency forever; resources tied up.
- **All-or-nothing rendering.** If any data fetch fails, render nothing. Users see broken pages.
- **Capacity at exactly current load.** No margin for growth; the next traffic spike crashes.
- **Removing redundancy as "waste."** Until needed, it looked unused. Then a single failure cascades.
- **Optimizing without monitoring.** Cutting margin without instrumentation to detect when it was needed.

## Resources

- **Beyer, B. et al. (eds.)** *Site Reliability Engineering* (O'Reilly, 2016). Canonical SRE book.
- **Beyer, B. et al. (eds.)** *The Site Reliability Workbook* (O'Reilly, 2018). Practical SRE patterns.
- **Nygard, M.** *Release It!* (2007, 2nd ed. 2018). Reliability patterns for production software.
- **Allspaw, J.** *The Art of Capacity Planning* (2008).
- **Adam Shostack and Andy Ozment writings** on threat modeling and security margin.
