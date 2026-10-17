---
name: scaling-load-assumptions
description: 'Verify and design for load scaling — data volume, transaction volume, request rate, and user count. Use when sizing infrastructure, choosing data structures, designing pagination and lazy-loading patterns, evaluating dependencies'' rate limits, or load-testing before launch. Most scaling failures are load failures: a system that handled X requests/second can''t handle 10X. The skill is anticipating the load the system will see and designing or testing for it deliberately.'
---

# Scaling — load assumptions

The first kind of scaling fallacy: assumptions about how the system will perform under load — data volume, request rate, user count, transaction volume. A system that handles current load gracefully may fail catastrophically at 10x or 100x load. Often the failure isn't a steady degradation but a sharp cliff: things work fine until the moment they don't.

The work of treating load assumptions is partly architectural (designing systems that scale) and partly verification (testing at production-like scale before launch).

## Common load-scaling failures

**Linear search on a growing dataset.** A simple "search through all records" works for small datasets and times out for large ones. Eventually requires indexing or dedicated search infrastructure.

**N+1 query patterns.** A code pattern that issues one database query per item in a list. Fine for 10 items; catastrophic for 10,000.

**Unbounded results.** "Return all matching records" fine for small queries; explodes when "all matching" is millions of rows.

**Synchronous external API calls in a critical path.** Each call adds latency; under load, latency compounds and the system slows.

**Naive caching.** Caching every request individually fills memory; cache eviction becomes the new bottleneck.

**No backpressure.** A system that accepts requests faster than it can process them accumulates a backlog that grows without bound.

**Single points of failure under load.** A single database that handles all writes; a single cache server that holds all sessions. Works under low load; catastrophically fails when load exceeds the single instance's capacity.

**Inadequate rate limiting on dependencies.** A third-party API has a 1000 req/sec limit; the system makes 10,000 req/sec and gets throttled or blocked.

## Patterns for load resilience

**Pagination.** Don't return all results at once. Return a page of results with a cursor or offset for the next page. Forces the user (or client) to consume in chunks.

**Lazy loading / virtualization.** Load only what's currently visible. As the user scrolls, load more.

**Indexing.** Database indexes make queries fast even at large data volumes. Search infrastructure (Elasticsearch, Algolia) for full-text queries.

**Caching.** Store frequently-requested data in fast memory; serve from cache rather than recomputing or refetching.

**Asynchronous processing.** Move expensive work to background queues. Respond quickly; process slowly.

**Sharding / partitioning.** Split data across multiple databases or storage units. Each shard handles a fraction of the load.

**Read replicas.** Multiple read-only copies of the database; reads distributed across replicas; writes go to a single master.

**Rate limiting.** Cap the request rate per user or per source. Prevents single users from consuming disproportionate resources.

**Circuit breakers.** Detect when a dependency is failing or slow; stop calling it temporarily; resume when it recovers.

**Graceful degradation.** When some services are slow, return partial results or cached results rather than failing entirely.

**Auto-scaling.** Add capacity dynamically as load increases; remove when load decreases.

**Load testing.** Simulate production-scale load in a non-production environment. Identify bottlenecks before they hit users.

## Worked examples

### A list view that breaks at scale

A team builds a feature showing all activity in a user's account. With 100 events per account, the page loads in 200ms. With 100,000 events, the page takes 30 seconds and crashes the browser.

The fix: pagination (load 50 events per page) + virtualization (only render visible rows in the DOM) + filtering (let users narrow to specific event types). The system now scales to millions of events without breaking.

### An N+1 query pattern

An ORM auto-generates queries that fetch one user's data per row. For a list of 1000 users, it makes 1001 database queries (1 for the list, then 1 per user for related data). Page load takes 8 seconds.

The fix: eager loading (fetch related data in a single query) + caching (store frequently-accessed user data). Page load drops to 200ms. Same result; very different performance.

### A cache that becomes the bottleneck

A team adds Redis caching to speed up database queries. Initially great. As traffic grows, the Redis instance starts to hit CPU and memory limits; queries are now slow because Redis is the bottleneck.

The fix: Redis cluster (multiple instances handling different keys), local in-process caching for the hottest data, and cache eviction policies. The cache is no longer a single bottleneck.

### A third-party API rate limit

A product depends on a payment-processing API with a 100 req/sec limit. During a holiday sale, peak traffic produces 1000 req/sec. The API throttles; transactions fail; users see errors.

The fix: queue payment requests locally; process them at the rate the API allows; show users an "in progress" state for delayed transactions. + Negotiate a higher rate limit with the provider. + Add a backup payment provider for failover.

### A search query that times out

A simple full-text search across user-generated content works fine at 100K records. As the corpus grows to 100M records, queries take 30 seconds.

The fix: dedicated search infrastructure (Elasticsearch) with proper indexing. Queries become sub-second even at billion-record scale.

## Load testing patterns

**Synthetic load testing.** Tools like JMeter, Gatling, or k6 simulate users making requests. Run at multiples of expected production load.

**Production traffic mirroring.** Mirror real production traffic to a test environment. Tests with real-world request distributions.

**Chaos engineering.** Deliberately fail components to verify the system handles failure gracefully. Netflix's Chaos Monkey is the canonical example.

**Canary deployments.** Roll out new code to a small fraction of users first; verify it doesn't degrade under their load before rolling out broadly.

**Stress testing to find the breaking point.** Increase load until the system fails. Document the breaking point; design to be safely below it.

## Designing for load from the start

When designing a new system or feature, ask:

**What's the expected load in 6 months and 2 years?** Project upward; design with margin.

**Which operations are likely to scale poorly?** Linear scans, all-results queries, N+1 patterns.

**What's our story for handling 10x current load?** Adding capacity, sharding, caching, async processing.

**What dependencies have load limits?** Identify and design around them.

**How will we know when we're approaching limits?** Monitoring and alerts on the right metrics.

## Anti-patterns

**Premature optimization.** Adding complexity (caching, sharding) before measurements show it's needed. Better to start simple and add complexity when bottlenecks emerge — but design with the architectural choices that allow adding complexity later.

**No load testing.** Shipping to production without verifying that the system handles realistic load. Hoping it'll be fine.

**Underestimating peak traffic.** Designing for average load and being shocked when peak is 10x average. Most systems have peak/average ratios of 3–10x; design accordingly.

**Single instances of critical components.** A single database, a single cache server, a single application instance. Single points of failure under load.

**Ignoring third-party limits.** Building features that depend on third-party APIs without checking their rate limits or planning for throttling.

**Auto-scaling without budgets.** Auto-scaling is great until your bill becomes catastrophic. Set caps and alerts.

## Heuristic checklist

When designing for load, ask: **What's the projected load in the foreseeable future?** Design with margin. **Which operations scale linearly vs. non-linearly with input size?** Identify and improve the non-linear ones. **Have we load-tested at production-target scale?** If not, the load assumption is unverified. **What single points of failure exist?** Eliminate or accept the risk explicitly. **Do we have monitoring to detect approaching limits?** Surprises are costly.

## Related sub-skills

- `scaling-fallacy` — parent principle on the dangers of scale assumptions.
- `scaling-interaction-assumptions` — sibling skill on user-base scaling.
- `weakest-link` — load reveals weak links that were tolerable at small scale.
- `factor-of-safety` — design with margin for the load you might see, not just the load you have.
- `errors` — error handling becomes critical when load creates failure conditions.

## See also

- `references/load-test-patterns.md` — practical patterns for load testing and capacity planning.
