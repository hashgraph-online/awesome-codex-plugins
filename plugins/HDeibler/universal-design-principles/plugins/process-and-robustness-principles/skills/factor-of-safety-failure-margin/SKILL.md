---
name: factor-of-safety-failure-margin
description: 'Use this skill when planning capacity, redundancy, graceful degradation, or recovery for systems that must keep working under stress — performance budgets, dependency failure handling, retry logic, error budgets, infrastructure capacity. Trigger when scoping infrastructure, designing error-handling architecture, planning for failure modes, or reviewing reliability incidents. Sub-aspect of `factor-of-safety`; read that first.'
---

# Failure margin: capacity, dependency, and graceful degradation

The complement to content-stress safety: designing the system itself to absorb failures and load spikes without falling over. The discipline is anticipating which way the system might fail and building in margin or fallback.

## Capacity margin

A system designed to handle exactly its current peak load will fail when load grows. Sustainable systems run at meaningful headroom.

### Sizing rule of thumb

- **Steady-state load**: design capacity at 2–3x typical load.
- **Anticipated peak**: design at 3–5x typical (covers daily/weekly spikes).
- **Burst capacity**: have ability to scale to 5–10x for marketing, viral events.

Cloud auto-scaling helps but isn't infinite — set explicit upper bounds and rate limits to prevent cost runaways during attacks.

### Headroom warning thresholds

Set monitoring at sub-capacity thresholds:

```
70% utilization → notify; investigate growth
85% utilization → page on-call; immediate investigation
95% utilization → critical; emergency response
```

Acting at 70% is far cheaper than acting at 100% (when the system has already started failing).

## Dependency margin

Most systems depend on external services: databases, third-party APIs, internal microservices. Each dependency is a potential failure point.

### Strategies

#### Timeouts everywhere

Every external call should have a timeout. Without timeouts, a slow dependency can exhaust your connection pool or thread pool, cascading failure.

```js
const result = await Promise.race([
  api.fetchUser(userId),
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error('timeout')), 2000)
  )
]);
```

#### Retries with backoff

For transient failures, retry — but with exponential backoff to avoid hammering a struggling dependency.

```js
async function fetchWithRetry(fn, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries || !isRetryable(error)) throw error;
      const delay = Math.min(1000 * 2 ** attempt, 10000) + Math.random() * 1000;
      await sleep(delay);
    }
  }
}
```

#### Circuit breakers

When a dependency is failing repeatedly, stop trying for a while. Fail fast rather than waiting for timeouts.

#### Caching as a fallback

If the dependency is read-heavy, cache responses. When the dependency is down, serve stale data with a marker.

## Graceful degradation

A system that fails gracefully provides reduced functionality during failures rather than no functionality.

Patterns:

### Degraded UI states

```jsx
function UserProfile({ userId }) {
  const { data, error } = useUser(userId);
  if (error?.transient) {
    return (
      <UserProfileSkeleton>
        <Banner type="warning">
          Some information couldn't load. Reload to try again.
        </Banner>
      </UserProfileSkeleton>
    );
  }
  return <UserProfileFull data={data} />;
}
```

The page renders something useful even when the data fetch fails.

### Feature degradation

When the recommendation engine is down, show a generic feed instead of a personalized one. When the search index is down, show recent items instead of search results. The user gets *something*; the broken feature doesn't break the whole product.

### Read vs. write degradation

A common pattern: when the database is overloaded, accept reads but defer writes (queue them for later processing). Users can browse; new content arrives slightly delayed.

## Error budgets (Google SRE)

Service-level objectives (SLOs) define an explicit margin for failure. A 99.9% uptime SLO permits ~43 minutes of downtime per month — the "error budget."

The discipline:

- **When the budget has remaining capacity**: the team can take risks (deploy faster, run experiments, push boundaries).
- **When the budget is consumed**: the team slows down (no risky deploys, focus on reliability).

This formalizes the trade-off between feature velocity and reliability. Without explicit budgets, teams often default to either pushing too hard (frequent incidents) or being too cautious (slow innovation).

## Worked example: an API call wrapped in three layers of margin

```js
async function getUserProfile(userId) {
  // Layer 1: request with timeout and retry
  const fetchFromAPI = () => withRetry(
    () => apiClient.get(`/users/${userId}`, { timeout: 2000 }),
    { maxRetries: 2, backoff: 'exponential' }
  );

  try {
    const data = await fetchFromAPI();
    cache.set(`user:${userId}`, data, { ttl: 60 });  // refresh cache
    return data;
  } catch (apiError) {
    // Layer 2: fall back to cache
    const cached = await cache.get(`user:${userId}`);
    if (cached) {
      logger.warn('API failed; serving cached data', { userId });
      return { ...cached, _stale: true };
    }
    // Layer 3: serve placeholder
    logger.error('API and cache failed; serving placeholder', { userId });
    return { id: userId, name: 'Unknown', _placeholder: true };
  }
}
```

Three layers of margin: retry with backoff, cache fallback, placeholder. The user always gets *something*; the system never crashes hard.

## Anti-patterns

- **No timeouts.** A slow dependency exhausts resources; the whole system slows or hangs.
- **Aggressive retries.** Retrying immediately and infinitely. The struggling dependency gets DDoS'd by your retries.
- **No circuit breaker.** Continuing to call a dead dependency forever; resources tied up.
- **All-or-nothing rendering.** If any data fetch fails, render nothing. Users see broken pages.
- **Capacity at exactly current load.** No margin for growth; the next traffic spike crashes the service.
- **Removing redundancy as "waste."** Until the redundancy was needed, it looked unused.

## Heuristics

1. **The dependency map.** List every external call. For each, ask: what's the failure mode? What's the user experience when it fails?
2. **The capacity headroom audit.** What's current peak utilization? Less than 50% headroom is fragile.
3. **The "what crashes the page?" check.** Disable each dependency in turn. What still renders? What breaks?
4. **The error-budget review.** If you're using SLOs, regularly review error-budget consumption. Adjust velocity vs. reliability accordingly.

## Related sub-skills

- **`factor-of-safety`** (parent).
- **`factor-of-safety-content-stress`** — UI margin for content edge cases.
- **`weakest-link`** — finding the dependency that's most likely to fail.
- **`forgiveness`** — user-side equivalent of system graceful degradation.
- **`feedback-loop`** — letting users know when degraded mode is active.

## Resources

- **Google SRE Book** (sre.google) — comprehensive guide to error budgets, SLOs, and reliability practice.
- **Petroski, H.** *To Engineer Is Human* — engineering perspective on safety factors.
- **Reason, J.** *Human Error* — system-level failure analysis.
