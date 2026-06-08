---
name: internal-service-networking
description: "Use when designing internal service traffic needing discovery, routing, locality, identity, or private access"
---

# Internal Networking And Service Mesh

## Iron Law

```
NO INTERNAL SERVICE PATH WITHOUT IDENTITY, FAILURE MODE, OBSERVABILITY, AND AN OPERATIONS PLAN FOR EVERY HOP
```

Every hop on a service-to-service path needs a workload identity, a documented failure mode, telemetry that explains what happened, and a runnable debugging and upgrade path. "We added a mesh" or "we use DNS" is not an answer to any of those four. For a solo or two-service deployment the rule still applies at a smaller scale.

> This skill assumes a multi-service deployment. A single-process app does not have internal service hops; route to `dependency-resilience` for remote-call policy or `architecture-decisions` if the question is whether to split.

## Overview

Internal networking should solve concrete traffic, identity, policy, and observability problems; mesh is not a default.

**Core principle:** choose the simplest internal networking model that provides required routing, identity, reliability, observability, and operations guarantees.

## When To Use

- The user is designing, changing, or troubleshooting internal service networking, service mesh, internal load balancing, service discovery, east-west traffic policy, authenticated service-to-service transport, locality-aware routing, or cross-location network cost.
- Services need consistent traffic policy, identity, telemetry, routing, or authorization at the platform layer.
- Internal routing or failover behavior affects reliability, latency, blast radius, or cost.
- The user asks whether adopting a service mesh is justified.
- The affected path is known to be internal service-to-service or private network traffic.

## When Not To Use

- The request is public edge abuse or denial-of-service defense; use `edge-traffic-and-ddos-defense` instead.
- The request is a vague network issue without a known affected path, surface, or symptom; use the router first.
- The issue is per-call retry/timeout/backpressure policy without networking architecture; use `dependency-resilience` instead.
- The main topic is API contract design; use `api-design-and-compatibility` instead.
- The work is broad identity/secrets beyond network identity; use `identity-and-secrets` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Service topology, traffic flows, protocols, locations, fault domains, partitions, dependencies, and responsibility.
- Concrete problem: service identity, encrypted transport, authorization, traffic classification, traffic splitting, locality, failover, observability, policy, or debugging.
- Current service discovery, load balancing, DNS/routing, ingress/egress, expected source addresses, and network boundaries.
- Traffic entry points, internal/external classification, authorization decisions at each path, routing or load-balancing limits, connection/concurrency limits, queue limits, overflow behavior, and emergency adjustment path.
- Packet-size, encapsulation, fragmentation, and traffic-class behavior for paths where large payloads, tunnels, interconnects, or device failover can change packet handling.
- Traffic inspection, mirroring, telemetry, or policy features that sit on the data path, including disable or bypass behavior and endpoint classes they can affect.
- Planned work on links, interfaces, devices, routes, or traffic policies, including work orders, exact targets, adjacent-resource risk, idle/in-use verification, automation availability, manual fallback path, post-activation checks, and supervision.
- Minimum healthy capacity floors, topology input completeness, asset lifecycle state such as planned, installed, commissioned, isolated, or production-serving, workflow compatibility across mixed device generations, failed-isolation state, production-ready rejoin gate, route-state freshness or expiration budget, controller leadership or reload behavior, route convergence or withdrawal behavior, external or partner failover signaling, owned address range, expected route origin, expected ingress or egress address attachment, stale route or boot/fallback config artifacts, and cached client state for routing changes.
- Control-plane partition or fail-open behavior that can keep packets flowing while topology or route state becomes stale.
- Latency, cross-location egress, failure domains, retry behavior, and dependency resilience policies.
- Platform maturity: upgrade process, sidecar/proxy/data-plane operations, incident history, and local diagnostic path.
- Telemetry needs: route, upstream/downstream identity, locality, retries, connection errors, request context, and whether emergency telemetry or control tools survive degraded capacity on the affected path.

## Workflow

1. **Name the problem.** Do not propose mesh until the repeated capability gap is explicit.
2. **Map traffic.** Identify internal routes, traffic entry points, dependencies, locations, failover paths, identity boundaries, traffic classifications, policy points, and overflow behavior.
3. **Compare no-mesh alternatives.** Consider library, gateway, platform, or simple load-balancer capabilities before adding a mesh-wide data plane. Specify the health-checking model (active and/or passive checks, healthy/unhealthy thresholds, outlier ejection) that gates every routing and failover decision; the load-balancing distribution (prefer consistent hashing where locality or connection-churn matters); and graceful connection draining on backend removal or deploy. Retry, timeout, and circuit-breaker policy stays with `dependency-resilience` even when implemented in mesh tooling; this file owns identity, discovery, locality, health, and drain.
4. **Define routing policy.** Include locality, failover, traffic splitting, retries, timeouts, and circuit behavior responsibility. For discovery, load-balancer, gateway, public route, or route changes, validate topology input completeness, asset lifecycle state before production-serving use, workflow compatibility across mixed device generations, failed-isolation detection, production-ready rejoin gates, healthy-capacity floors, route-state freshness or expiration budget, controller leadership change and reload behavior with invalid or stale config present, convergence or withdrawal behavior, external or partner failover signals when ingress can keep targeting degraded capacity, owned address range and expected route origin, expected ingress or egress address attachment on serving nodes, stale route, boot/fallback config, or client artifacts, emergency refresh/reload path, and rollback behavior before broad exposure.
5. **Constrain fail-open changes.** If the data plane is operating through a control-plane partition or fail-open mode, freeze or narrowly gate topology-changing operations until route-state freshness and convergence are confirmed; otherwise a survivable control-plane fault can become packet loss or congestion.
6. **Validate packet handling.** Test representative packet sizes, encapsulation overhead, fragmentation behavior, traffic classes, and observer or inspection features across primary, failover, and recently flapped paths so a reachability check cannot miss packet loss caused by the network feature itself.
7. **Gate planned network work.** For work that removes, activates, or mutates links, interfaces, devices, routes, or traffic policy, split execution into small batches, emit start/end notifications, verify exact target and idle/in-use status before action, require supervision for customer-traffic paths, monitor adjacent capacity during the window, and pause the work class when the observed target differs from the work order. If automation is unavailable, do not use a manual path unless it runs equivalent pre-activation checks, starts monitoring immediately, and records post-activation validation.
8. **Define identity and policy.** State how workload identity, traffic classification, authenticated encrypted transport, authorization, and audit work. Test every entry-path class, including external-to-internal and internal-only paths, against the policy decision it will trigger. Use short-lived, attested, rotating workload identity feeding the authorization decision, and treat network-layer segmentation (least-privilege east-west policy, lateral-movement containment) as part of the routing posture.
9. **Model failure and upgrades.** Include proxy/control-plane failure, config error, upgrade rollout, planned-work error, and debug burden.
10. **Instrument paths.** Capture request IDs, route metadata, identity, upstream locality, retries, errors, latency, connection saturation, queue pressure, and overflow decisions. Test that incident telemetry, reroute controls, and emergency tooling remain usable when the impaired path has reduced capacity.
11. **Plan adoption.** Roll out by service, partition, or environment; keep rollback and exception path.

## Synthesized Default

Do not add service mesh by default. Adopt a mesh or equivalent platform traffic layer only when repeated cross-service needs justify its operational cost: identity, encrypted transport, traffic policy, telemetry, authorization, routing, or locality.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Small systems may use simple internal load balancing and library conventions.
- High-security or multi-tenant platforms may justify centralized identity and traffic policy earlier.
- Cross-location systems may prefer explicit location boundaries and locality rules over opaque global routing.
- Emergency network changes need audit, rollback, and post-change reconciliation.

## Response Quality Bar

- Lead with the mesh/no-mesh decision, routing policy, identity model, or failure-mode blocker requested.
- For quick design or troubleshooting answers, still include one compact per-edge baseline: `<caller> -> <callee>` discovery/routing mechanism and stale/unavailable behavior; service-to-service authentication mechanism and scope, such as mutual-authentication transport workload identity, mesh identity, or a signed service token for that edge; per-request authorization decision criteria, such as caller identity plus method/resource/action; default-deny service policy with user-confirmed exception rule; RED metrics (request rate, error rate, latency) with dashboard and alert; and runnable debug command or procedure.
- Cover concrete repeated needs, traffic map, routing/locality/failover, identity/encrypted transport/authorization, retry responsibility, telemetry, upgrades, rollback, and cost/latency tradeoffs before optional mesh breadth.
- Make recommendations actionable with policy locations, rollout stages, config checks, failure tests, rollback steps, and operational runbooks where relevant.
- Name the details to inspect, such as dependency maps, route config, retry/timeout settings, control-plane health, proxy versions, identity assertions, latency/egress data, and incident history; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside internal traffic and service mesh decisions. Route dependency resilience or zero-trust work only when it materially changes the mesh decision.
- Be concise: avoid generic mesh advocacy and prefer compact decision records and routing matrices.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Internal traffic and dependency map.
- Mesh/no-mesh decision record with alternatives.
- Routing, locality, failover, and traffic-splitting policy.
- Traffic-path capacity table with entry point, traffic classification, routing limit, connection/concurrency limit, overflow behavior, and emergency adjustment path.
- Packet-size and traffic-class validation covering primary, failover, and recently changed paths.
- Observer-path safety check for traffic inspection, mirroring, telemetry, or policy features, with affected endpoint classes and disable or bypass path.
- Routing-change safety checks covering topology input completeness, asset lifecycle state, workflow compatibility across mixed device generations, failed-isolation detection, production-ready rejoin gate, control-plane or fail-open state, healthy-capacity floors, route-state freshness or expiration budget, controller leadership or reload behavior, owned address range and expected route origin, expected ingress or egress address attachment, stale route, boot/fallback config, or client artifacts, convergence or withdrawal behavior, external or partner failover signaling, emergency refresh/reload path, and rollback.
- Planned network work safety gate for exact target verification, automation or manual path, equivalent pre/post checks, batch size, supervision, start/end notification, adjacent-capacity monitoring, and pause criteria.
- Workload identity, encrypted transport, and authorization model.
- Operations, upgrade, diagnostics, and rollback plan.
- Emergency observability and control-path survivability under degraded routing or capacity.
- Network telemetry and debugging requirements.
- Cost and latency tradeoff notes for cross-boundary traffic.

## Checks Before Moving On

- `problem_check`: mesh or routing layer adoption maps to concrete repeated needs.
- `failure_model`: data-plane, control-plane, config, and upgrade failure modes are addressed.
- `diagnostic_check`: debugging, upgrade, and incident-response paths are explicit and runnable or marked unknown.
- `routing_policy`: locality, failover, traffic split, and retry/timeout responsibility are defined.
- `health_model`: endpoint health uses defined active/passive checks with thresholds and outlier ejection before routing or failover.
- `lb_and_drain`: load-balancing distribution and graceful connection draining on backend removal/deploy are specified.
- `segmentation`: east-west traffic uses least-privilege segmentation with attested workload identity.
- `entry_classification`: internal, external, partner, and failover entry paths trigger the expected traffic classification and authorization decision.
- `routing_change_safety`: route or discovery changes validate topology input completeness, asset lifecycle state, workflow compatibility across mixed device generations, failed-isolation detection, production-ready rejoin gate, control-plane or fail-open state, and controller leadership or reload behavior with invalid or stale config present, preserve healthy-capacity floors, define route-state freshness or expiration budget, verify public route origin for owned address ranges when applicable, verify expected ingress or egress address attachment on serving nodes, have convergence and stale-client behavior defined, and can be rolled back or refreshed without hidden state.
- `planned_work_safety`: planned changes to links, interfaces, devices, routes, or traffic policy verify exact targets, idle/in-use status, automation or manual path, equivalent pre/post checks, supervision, batching, and pause criteria before execution.
- `traffic_entry_capacity`: traffic entry points have capacity, connection/concurrency, and routing limits stated.
- `packet_size_path`: representative packet sizes, encapsulation overhead, fragmentation behavior, and traffic classes are tested across primary and failover paths.
- `observer_path_safety`: traffic inspection, mirroring, telemetry, or policy features on the data path have affected endpoint classes, validation, and disable or bypass behavior.
- `emergency_tooling_survives`: observability and control tools needed for reroute, refresh, or rollback work during reduced capacity on the affected path.
- `overflow_behavior`: overload, spillover, or reject behavior is defined and observable.
- `telemetry_check`: route, identity, locality, retry, latency, and error metadata are observable.

## Red Flags - Stop And Rework

- Mesh is selected because it is fashionable.
- Proxy upgrades or data-plane incidents have no runnable diagnostic or rollback path.
- Routing retries conflict with application retry budgets.
- A routing change can remove too much healthy capacity or leave stale client artifacts with no rollback plan.
- Gateway nodes can serve traffic without the expected ingress or egress address identity attached.
- Manual link, route, or traffic-policy activation bypasses automation checks or delays monitoring after exposure.
- Owned address ranges have no expected-origin monitor or response path for external route leaks.
- Reachability tests pass with small packets while large-packet, encapsulated, or failover-path traffic is untested.
- Cross-location routing hides latency and egress cost.
- Identity is asserted but not tied to authorization or audit.
- Backends are removed or deployed with no connection draining, dropping in-flight requests.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Mesh first | Start with the capability gap and simpler options. |
| Hidden retries | Align network retries with application retry budgets. |
| No upgrade plan | Treat data-plane upgrades as production releases. |
| Blind global routing | Make locality, failover, and cost explicit. |
