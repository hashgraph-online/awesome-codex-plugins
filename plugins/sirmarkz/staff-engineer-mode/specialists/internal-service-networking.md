---
name: internal-service-networking
description: "Use when internal service traffic needs discovery, routing, locality, peer identity matching, or private access"
---

# Internal Service Networking

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
- A trust-domain, namespace, or peer-name change can alter which internal workloads authenticate or authorize each other.

## When Not To Use

- The request is public edge abuse or denial-of-service defense; use `edge-traffic-and-ddos-defense` instead.
- The request is a vague network issue without a known affected path, surface, or symptom; use the router first.
- The issue is per-call retry/timeout/backpressure policy without networking architecture; use `dependency-resilience` instead.
- The main topic is API contract design; use `api-design-and-compatibility` instead.
- The work is broad identity/secrets beyond network identity; use `identity-and-secrets` instead.
- The main issue is certificate, cryptographic key, trust root, or algorithm lifecycle without a service peer-matching or private traffic decision; use `cryptography-and-key-lifecycle` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Service topology, traffic flows, protocols, locations, fault domains, partitions, dependencies, and responsibility.
- Concrete problem: service identity, encrypted transport, authorization, traffic classification, traffic splitting, locality, failover, observability, policy, or debugging.
- Current service discovery, load balancing, DNS/routing, ingress/egress, expected source addresses, and network boundaries.
- Per service edge, the identity the caller or server presents; the peer identity, trust domain, namespace, or audience the verifier expects; the verification trust path when it changes; the matching rule; the authorization rule bound to that identity; and the mismatch response.
- For peer-identity transitions, current and target identities, verifier accept sets, mixed-version paths, issuance or workload-switch order, old-identity usage signals, compatibility-window deadline, removal gate, and rollback limit.
- Traffic entry points, internal/external classification, authorization decisions at each path, routing or load-balancing limits, connection/concurrency limits, queue limits, overflow behavior, and emergency adjustment path.
- Packet-size, encapsulation, fragmentation, and traffic-class behavior only for service paths where large payloads, overlays, tunnels, or failover can change packet handling.
- Traffic inspection, mirroring, telemetry, or policy features on the service data path, including affected endpoint classes and disable or bypass behavior when those features exist.
- Planned service-discovery, routing, gateway, or traffic-policy changes, including exact targets, adjacent-capacity risk, batch and pause controls, post-activation checks, and rollback.
- When physical links, network devices, provider work, or public route origin are in scope: exact asset and target, idle or in-use state, expected route origin, serving-node ingress and egress address attachment, supervision, batch boundary, monitoring, pause criteria, and rollback.
- Minimum healthy-capacity floors, topology-input completeness, endpoint readiness and rejoin gates, route-state freshness, controller leadership or reload behavior, convergence or withdrawal behavior, stale client or fallback configuration, and rollback for internal routing changes.
- Control-plane partition or fail-open behavior that can keep packets flowing while topology or route state becomes stale.
- Latency, cross-location egress, failure domains, retry behavior, and dependency resilience policies.
- Platform maturity: upgrade process, sidecar/proxy/data-plane operations, incident history, and local diagnostic path.
- Telemetry needs: route, upstream/downstream identity, locality, retries, connection errors, request context, and whether emergency telemetry or control tools survive degraded capacity on the affected path.

## Workflow

1. **Name the problem.** Do not propose mesh until the repeated capability gap is explicit.
2. **Map traffic.** Identify internal routes, traffic entry points, dependencies, locations, failover paths, identity boundaries, traffic classifications, policy points, and overflow behavior.
3. **Compare no-mesh alternatives.** Consider library, gateway, platform, or simple load-balancer capabilities before adding a mesh-wide data plane. Choose active, passive, or application health signals and their thresholds from the failure mode; do not require every mechanism on every path. Choose load distribution from connection, locality, state, and fairness needs, and drain connections on backend removal or deploy. Retry, timeout, and circuit-breaker policy stays with `dependency-resilience` even when implemented in traffic tooling; this file owns identity, discovery, locality, health, and drain.
4. **Define internal routing policy.** Include locality, failover, traffic splitting, health, drain, and responsibility for retry or timeout policy. For discovery, load-balancer, gateway, or service-route changes, validate topology inputs, endpoint readiness and rejoin, healthy-capacity floors, route-state freshness, controller leadership and reload behavior, convergence or withdrawal, stale client or fallback configuration, emergency refresh, and rollback before broad exposure.
5. **Constrain fail-open changes.** If the data plane is operating through a control-plane partition or fail-open mode, freeze or narrowly gate topology-changing operations until route-state freshness and convergence are confirmed; otherwise a survivable control-plane fault can become packet loss or congestion.
6. **Validate packet handling when the service path needs it.** Test representative packet sizes, encapsulation overhead, fragmentation behavior, traffic classes, and observer or inspection features across primary and failover paths when overlays, tunnels, large payloads, or data-path features can affect them. Do not add packet-level gates to ordinary service paths without that risk.
7. **Gate planned network work.** For discovery, gateway, route, or traffic-policy mutations, verify the exact logical target and current serving state, use bounded batches, protect adjacent healthy capacity, monitor immediately, pause on observed-versus-intended mismatch, validate post-activation behavior, and keep rollback. When the requested internal-network change also touches physical links, devices, provider work, or public route origin, add a risk-triggered operations module: verify the exact asset and target, idle or in-use state, expected route origin, and serving-node ingress and egress address attachment; require supervised batches, immediate monitoring, pause criteria, and rollback. Do not force these physical/public checks onto ordinary service-routing work.
8. **Define identity and policy per edge.** Record the identity each side presents, the exact peer identity or identity set each verifier accepts, the trust-domain or namespace boundary, the verification trust path when it changes, the match rule, the authorization decision bound to the match, and fail-closed behavior for an unexpected peer. Prefer short-lived, rotation-capable workload identity, using attestation when the trust model and runtime support it. Apply least-privilege service policy or segmentation where lateral movement is a material risk.
9. **Stage peer-identity transitions verifier first.** Before a trust-domain, namespace, or peer-name rename, make each affected verifier accept the bounded old-and-new identity set and both verification trust paths when trust material also changes. Prove that mixed peers authenticate and authorize as intended. Switch issuers or workloads in reversible batches, observe presented identity and mismatch reasons per edge, and retain the old acceptance only until new-identity use is complete and rollback no longer needs it. Then remove the old identity and test that it fails closed. A compatibility alias must not broaden authorization beyond the original service edge.
10. **Model failure and upgrades.** Include proxy/control-plane failure, config error, upgrade rollout, planned-work error, and debug burden.
11. **Instrument paths.** Capture the route, presented and expected peer identity, verifier configuration version, match or mismatch reason, locality, errors, latency, connection saturation, queue pressure, and overflow decisions needed to diagnose the selected failure modes. Include request correlation and retry metadata when the application contract permits them. Test that incident telemetry and reroute controls remain usable when the affected path has reduced capacity.
12. **Plan adoption.** Roll out by service, partition, or environment; keep rollback and exception path.

## Synthesized Default

Do not add service mesh by default. Adopt a mesh or equivalent platform traffic layer only when repeated cross-service needs justify its operational cost: identity, encrypted transport, traffic policy, telemetry, authorization, routing, or locality.



## Exceptions

- Small systems may use simple internal load balancing and library conventions.
- High-security or multi-tenant platforms may justify centralized identity and traffic policy earlier.
- Cross-location systems may prefer explicit location boundaries and locality rules over opaque global routing.
- Emergency network changes need audit, rollback, and post-change reconciliation.

## Response Quality Bar

- Lead with the mesh/no-mesh decision, routing policy, identity model, or failure-mode blocker requested.
- For quick design or troubleshooting answers, include one compact per-edge baseline: `<caller> -> <callee>`, discovery or routing behavior, stale or unavailable behavior, service identity and authorization decision, the failure signal under investigation, and one runnable verification path. Add dashboards, alerts, default-deny exceptions, and protocol details only when the requested artifact needs them.
- Cover concrete repeated needs, traffic map, routing/locality/failover, identity and authorization, retry responsibility, telemetry, upgrades, rollback, and cost or latency tradeoffs that affect the decision before optional mesh breadth.
- Make recommendations actionable with policy locations, rollout stages, config checks, failure tests, rollback steps, and operational runbooks where relevant.
- Name the details to inspect, such as dependency maps, route config, retry/timeout settings, control-plane health, proxy versions, identity assertions, latency/egress data, and incident history; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside internal traffic and service mesh decisions. Route dependency resilience or zero-trust work only when it materially changes the mesh decision.
- Be concise: avoid generic mesh advocacy and prefer compact decision records and routing matrices.
- Scale the artifact to the request: one service edge needs its route, identity, authorization, failure behavior, telemetry, and verification; add adoption, packet, planned-change, cross-location, and full operations modules only when those risks apply.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Internal traffic and dependency map.
- Mesh/no-mesh decision record with alternatives.
- Routing, locality, failover, and traffic-splitting policy.
- Traffic-path capacity table with entry point, classification, routing or concurrency limit, overflow behavior, and emergency adjustment when capacity policy is in scope.
- Packet-size and traffic-class validation for primary and failover paths when overlays, tunnels, large payloads, or data-path features create that risk.
- Observer-path safety check for traffic inspection, mirroring, telemetry, or policy features when present, with affected endpoint classes and disable or bypass path.
- Internal routing-change safety checks covering topology inputs, endpoint readiness and rejoin, control-plane or fail-open state, healthy-capacity floors, route-state freshness, controller leadership or reload, stale client or fallback configuration, convergence or withdrawal, emergency refresh, and rollback.
- Planned service-routing change gate for exact logical target, pre/post checks, batch size, adjacent-capacity monitoring, pause criteria, and rollback when a route or policy changes.
- Physical and public network operations module, when those surfaces are in scope, covering expected route origin, serving-node address attachment, exact asset and target, idle or in-use state, supervision, batching, monitoring, pause criteria, and rollback.
- Workload identity, peer-matching, encrypted transport, and authorization model for each affected edge.
- Trust-domain, namespace, or peer-name transition plan when identity matching changes, with verifier-first compatibility, mixed-peer tests, bounded old/new acceptance, mismatch telemetry, rollout order, removal gate, negative test, and rollback.
- Operations, upgrade, diagnostics, and rollback plan.
- Emergency observability and control-path survivability under degraded routing or capacity.
- Network telemetry and debugging requirements.
- Cost and latency tradeoff notes for cross-boundary traffic.

## Checks Before Moving On

- `problem_check`: mesh or routing layer adoption maps to concrete repeated needs.
- `failure_model`: data-plane, control-plane, config, and upgrade failure modes are addressed.
- `diagnostic_check`: debugging, upgrade, and incident-response paths are explicit and runnable or marked unknown.
- `routing_policy`: locality, failover, traffic split, and retry/timeout responsibility are defined.
- `health_model`: endpoint health uses the active, passive, or application signal and thresholds required by the selected failure model.
- `lb_and_drain`: load distribution matches state, locality, connection, and fairness needs; backend removal or deploy drains connections when in-flight work exists.
- `segmentation`: service traffic uses identity-bound least-privilege policy; attestation and network segmentation are included when the trust model or lateral-movement risk requires them.
- `entry_classification`: each in-scope internal, gateway, or failover entry path triggers the expected traffic classification and authorization decision.
- `peer_identity_contract`: each affected edge states presented identity, expected peer identity or set, trust-domain or namespace boundary, verification trust path when it changes, match rule, authorization binding, and mismatch behavior.
- `identity_transition`: identity renames update verifiers before issuers or workloads, test mixed peers, observe old/new use and mismatch reasons, bound dual acceptance, remove the old identity only after the gate, and prove the retired identity fails closed.
- `routing_change_safety`: service route or discovery changes validate topology input, endpoint readiness and rejoin, control-plane or fail-open state, controller reload behavior, healthy-capacity floors, route-state freshness, convergence, stale-client behavior, emergency refresh, and rollback.
- `planned_work_safety`: planned service-discovery, gateway, route, or traffic-policy changes verify exact logical targets, current serving state, pre/post checks, batching, adjacent capacity, pause criteria, and rollback.
- `physical_public_work_safety`: when physical links, devices, provider work, or public route origin are in scope, the plan verifies asset and target, idle or in-use state, expected origin, serving-node address attachment, supervision, batching, monitoring, pause criteria, and rollback.
- `traffic_entry_capacity`: when traffic limits are part of the decision, entry points have capacity, connection or concurrency, routing, and overflow behavior stated.
- `packet_size_path`: when overlays, tunnels, large payloads, or data-path features create packet risk, representative sizes, encapsulation, fragmentation, and traffic classes are tested across primary and failover paths.
- `observer_path_safety`: when traffic inspection, mirroring, telemetry, or policy features sit on the data path, they have affected endpoint classes, validation, and disable or bypass behavior.
- `emergency_tooling_survives`: observability and control tools needed for reroute, refresh, or rollback work during reduced capacity on the affected path.
- `overflow_behavior`: overload, spillover, or reject behavior is defined and observable.
- `telemetry_check`: route, identity, locality, retry, latency, and error metadata are observable.

## Red Flags - Stop And Rework

- Mesh is selected because it is fashionable.
- Proxy upgrades or data-plane incidents have no runnable diagnostic or rollback path.
- Routing retries conflict with application retry budgets.
- A routing change can remove too much healthy capacity or leave stale client artifacts with no rollback plan.
- A service route or traffic-policy change bypasses equivalent pre/post checks or delays monitoring after exposure.
- Physical or public network work changes the wrong asset, an in-use link, an unexpected route origin, or an unattached serving address without a supervised pause and rollback path.
- A path with overlays, tunnels, large payloads, or packet-changing data-plane features passes only small-packet reachability tests.
- Cross-location routing hides latency and egress cost.
- Identity is asserted but not tied to authorization or audit.
- A workload presents a new trust-domain or peer identity before every affected verifier accepts it.
- An old/new identity alias has no expiry, removal signal, or authorization boundary.
- Backends are removed or deployed with no connection draining, dropping in-flight requests.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Mesh first | Start with the capability gap and simpler options. |
| Hidden retries | Align network retries with application retry budgets. |
| No upgrade plan | Treat data-plane upgrades as production releases. |
| Renaming identity in one step | Expand verifier acceptance, switch presented identity in batches, then contract the old acceptance. |
| Treating physical or public network work as ordinary service routing | Add the risk-triggered operations module with asset, state, origin, address-attachment, supervision, batching, monitoring, pause, and rollback checks. |
