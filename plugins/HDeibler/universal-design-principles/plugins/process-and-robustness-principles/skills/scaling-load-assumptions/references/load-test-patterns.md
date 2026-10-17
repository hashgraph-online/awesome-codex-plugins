# Load testing — patterns and tools

A practical guide to testing systems for load before launch.

## Test types

**Smoke test.** Run at low load to verify the system responds at all. Catches deployment issues, basic functionality regressions.

**Load test.** Run at expected production load. Verify that response times, error rates, and throughput meet targets.

**Stress test.** Run beyond expected load. Find the breaking point. Document what happens when limits are exceeded.

**Soak test.** Run at sustained load for an extended period (hours or days). Catch memory leaks, gradually-degrading behavior, queue overflows.

**Spike test.** Sudden large increase in load. Simulates real-world events (a viral moment, a launch, a sale).

**Volume test.** Test with large amounts of data (rather than just request volume). Verify queries, indexes, and storage handle growth.

## Tools

**JMeter.** Open-source, mature, comprehensive. Runs in JVM. Good for HTTP, SOAP, JDBC, and other protocols.

**Gatling.** Open-source, Scala-based DSL. Generates fewer test machines for the same load due to async architecture.

**k6.** Modern, JavaScript-based scripting. Good developer experience, excellent for cloud-native systems.

**Locust.** Python-based, distributed-friendly, simple scripting.

**Apache Bench (ab).** Very simple HTTP load tool; good for quick checks.

**Cloud-native tools.** AWS Load Testing, Azure Load Testing, etc. Integrate with cloud-native infrastructure for spinning up large numbers of test machines.

For modern web systems, k6 or Gatling are common starting choices. JMeter is mature and full-featured but more cumbersome.

## Test environment considerations

**Production-like environment.** Test in an environment that matches production (same instance types, same database, same dependencies). Tests in a smaller environment don't predict production behavior.

**Realistic data.** Test with production-like data volumes and shapes. A 1000-row test database doesn't predict behavior at 10M rows.

**Realistic request patterns.** Use real distribution of request types, not just the easy paths. Production traffic often has long tails of unusual requests.

**Isolation.** Test in an environment that won't affect real users. Don't load-test production directly except in carefully-controlled circumstances.

## Metrics to track

**Response time.** P50 (median), P95, P99 (99th percentile), P99.9. The tail latencies matter — a system with great median and terrible P99 has a bad user experience for some users.

**Throughput.** Requests per second the system can handle.

**Error rate.** Percentage of requests that fail.

**Resource utilization.** CPU, memory, disk I/O, network on each component.

**Saturation.** How close components are to their limits. A 90% saturated database is one bad spike away from failing.

**Queue depth.** For async systems, how many items are in queues. Growing queues = unmet demand.

## Test execution patterns

**Ramp-up.** Start at low load and increase gradually. Catches gradual degradation.

**Sustained load.** Hold at target load for a sustained period (10 minutes, an hour, a day). Catches steady-state issues.

**Step increase.** Hold at one level, jump to a higher level. Tests how the system reacts to sudden change.

**Realistic schedule.** Simulate real-world traffic patterns (peak/off-peak cycles, weekly patterns). Catches issues specific to the actual usage shape.

## Capacity planning

After load testing:

**Know your breaking point.** What load takes the system down?

**Set capacity targets below breaking point.** Provision for 50–75% of breaking-point load to leave headroom.

**Plan for growth.** Capacity should grow ahead of demand, not behind.

**Monitor for approach to limits.** Alerts when utilization approaches dangerous levels.

**Auto-scale where possible.** Add capacity dynamically based on demand.

## Common load-test pitfalls

**Testing only the happy path.** Load test only the easy requests. Misses the expensive operations that dominate real load.

**Underestimating concurrency.** Real users do many things simultaneously; tests with sequential single-user patterns don't capture this.

**Insufficient ramp-up.** Cold caches, JIT compilation, connection pools all affect early measurements. Warm up before measuring.

**Test in too-small environment.** Tests in dev that don't predict production. Use production-like infrastructure.

**Ignoring resource limits.** Tests that don't measure CPU, memory, etc. — only response time. Resources can be the limiting factor.

**One-off tests.** Load testing once before launch and never again. Performance changes as code evolves; test continuously.

**No baseline.** Tests without a baseline can't tell whether things are improving or degrading. Always have a previous test to compare against.

## Production observability

Beyond pre-launch testing:

**Real-user monitoring (RUM).** Measure actual user experiences from the browser/device. Catches issues that synthetic tests miss.

**Application performance monitoring (APM).** Tools like Datadog, New Relic, Honeycomb. Trace requests through the system to identify bottlenecks.

**Distributed tracing.** Follow requests across multiple services. Identify which service is the bottleneck for slow requests.

**Logging and analytics.** Structured logs that can be queried for performance analysis.

**Synthetic monitoring.** Continuously execute key user journeys; alert on degradation.

## Cross-reference

For interaction-based scaling, see `scaling-interaction-assumptions`. For the parent principle, see `scaling-fallacy`.
