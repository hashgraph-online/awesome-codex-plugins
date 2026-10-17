---
name: persistent-connection-systems
description: "Use when long-lived client connections need lifecycle, backpressure, presence, and drain-on-deploy design"
---

# Persistent Connection Systems

## Iron Law

```
NO LONG-LIVED CONNECTION WITHOUT A DECLARED ACCESS POLICY, RECOVERY CONTRACT, BACKPRESSURE, AND DRAIN-ON-DEPLOY PATH
```

A non-public connection without revocation can retain unauthorized capability. Any persistent-connection feature without declared replay or resynchronization, a slow-consumer bound, and a drain path can lose or duplicate updates, exhaust server memory, and overwhelm the backend on deploy.

## Overview

Produces the connection-protocol spec and a capacity and drain plan for long-lived client connections: authenticated and authorized access for non-public data or actions, or an explicitly anonymous public scope with abuse bounds; heartbeat and idle timeout; reconnect with backoff and declared resume semantics; gap recovery; bounded fanout; capacity; and deploy draining. It owns the connection lifecycle and routes broker-mediated delivery and request/reply policy out.

**Core principle:** every long-lived connection must be authenticated and authorized unless it is deliberately anonymous and public with explicit scope and abuse bounds; it must also declare recovery, bound slow consumers, and drain cleanly on deploy.

## When To Use

- A feature holds long-lived client connections and needs handshake, heartbeat, idle-timeout, and reconnect-with-resume behavior.
- Reconnect storms after a deploy or network blip threaten the backend.
- Slow consumers risk exhausting server memory, or messages are dropped with no resume cursor.
- Presence, subscription, or fanout state needs a lifecycle, and deploys must drain connections without losing sessions.

## When Not To Use

- The concern is broker-mediated async delivery semantics; use `event-workflows`.
- The concern is request/reply timeout, retry, or circuit-breaker policy; use `dependency-resilience`.
- The concern is raw connection-count, memory, file-descriptor, or autoscaling headroom without reconnect, heartbeat, or drain semantics; use `performance-and-capacity`.
- The concern is east-west load-balancer or service-routing internals; use `internal-service-networking`.
- Staged rollout sequencing goes to `progressive-delivery`; client-side offline and sync gating goes to `mobile-release-engineering`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Connection type and protocol, expected concurrent connections, and message rate per connection.
- Reconnect behavior on deploy and on network blip, and whether a resume cursor exists.
- Access posture: authentication source and principal/tenant binding for non-public data or actions, or the deliberately anonymous/public scope and abuse/rate bounds; subscription/action authorization, token expiry/refresh, revocation propagation, and forced-disconnect behavior where authenticated.
- Delivery contract, ordering scope, cursor namespace and epoch, replay retention horizon, cursor/effect persistence, duplicate handling, gap detection, and snapshot or resynchronization path.
- Slow-consumer handling today and what happens to server memory when a client cannot keep up.
- Presence, subscription, and fanout state and where it lives.
- Deploy and rotation cadence and how connections are drained, if at all.

## Workflow

1. **Define the access and connection lifecycle.** For non-public data or actions, specify authenticated handshake, trusted principal and tenant binding, current authorization, expiry/refresh, revocation propagation, and forced disconnect. A public one-way stream may be deliberately anonymous only when its scope, absence of privileged actions, abuse/rate bounds, and monitoring are explicit. In either case define heartbeat, keepalive, idle timeout, and clean close; never treat an accepted connection as permanent authorization.
2. **Declare delivery and resume semantics.** State ordering scope and whether delivery is best-effort, at-most-once, or at-least-once; do not imply exactly-once application from a cursor alone. Define cursor namespace, scope, epoch, retention horizon, and expiry behavior. For resumable delivery, persist cursor progress atomically with application effects or make application duplicate-safe, detect sequence gaps, and provide snapshot or full-resynchronization when history is unavailable. Require reconnect backoff with jitter so a fleet does not reconnect in lockstep.
3. **Bound slow consumers.** Define per-connection and per-channel backpressure, buffer limits, and what happens when a client cannot keep up so one slow consumer cannot exhaust memory.
4. **Manage scoped presence and fanout.** Define how presence and subscription state is authorized where needed, established, refreshed, revalidated after permission changes, bounded for anonymous/public streams, and cleaned up on disconnect or revocation.
5. **Size protocol-tied connection capacity.** State concurrent-connection and stream limits, file-descriptor budget, and affinity or sticky-routing needs as part of the connection lifecycle, reconnect, and drain design.
6. **Drain on deploy.** Define how connections drain on deploy and rotation so sessions migrate or resume rather than drop, and bound the reconnect rate the backend can absorb.
7. **Recover gaps and expired cursors.** Define ordering checks, gap detection, history-horizon monitoring, duplicate handling, and a snapshot or reconciliation path so missed or replayed updates are observable and repairable rather than silent.

## Synthesized Default

Give each non-public long-lived connection authenticated, revocable authorization; allow anonymous access only for a deliberately public scope with abuse bounds. Give every connection a declared delivery contract, duplicate/gap handling, resynchronization where needed, slow-consumer bounds, and a drain-on-deploy path. Use jittered reconnect and bounded buffers. Dropping live sessions without a bounded recovery contract is a defect.

## Exceptions

- Small internal streams can accept reconnect without resume only when message loss is harmless and documented.
- A cursorless best-effort notification stream is acceptable only when stale or missing updates are harmless and a later snapshot restores truth.
- One-way notification streams still need backpressure, heartbeat, and drain behavior.
- A deliberately anonymous public notification stream may omit identity binding when it exposes no non-public data or privileged action and has explicit abuse, rate, and fanout bounds.
- Client-specific offline sync belongs with client release gates when the connection lifecycle is no longer the dominant risk.

## Response Quality Bar

- Lead with the connection lifecycle, reconnect, backpressure, capacity, or drain decision requested.
- Cover the authenticated-or-deliberately-anonymous posture, authorization or public-scope boundary, abuse bounds, heartbeat, delivery and resume semantics, gap recovery, slow-consumer bounds, capacity, and drain before optional breadth.
- Make recommendations actionable with protocol choices, buffer limits, reconnect-rate bounds, deploy-drain steps, and verification cases.
- Name the details to inspect, such as connection counts, message rates, resume cursor behavior, buffer growth, deploy logs, and presence state; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside long-lived connection lifecycle and drain; route broker workflows, request/reply dependency policy, and raw capacity when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Connection-protocol spec: authenticated and authorized access for non-public data/actions, or a deliberately anonymous public scope with abuse/rate bounds; heartbeat, applicable expiry/revocation behavior, idle timeout, and close.
- Delivery and resume decision: ordering scope, delivery guarantee, backoff with jitter, cursor namespace/epoch/horizon/expiry, cursor-and-effect atomicity or deduplication, and expired-cursor resynchronization.
- Backpressure and slow-consumer policy: buffer limits and overflow behavior.
- Presence, subscription, and fanout state lifecycle.
- Protocol-tied connection-capacity plan: concurrent limits, file-descriptor budget, affinity, and the lifecycle decision each limit protects.
- Drain-on-deploy plan and absorbable reconnect-rate bound.
- Ordering, duplicate, gap-detection, snapshot, and reconciliation decision for streamed updates.

## Checks Before Moving On

- `access_lifecycle`: each connection is authenticated and authorized for non-public data/actions or deliberately anonymous with a bounded public scope; applicable expiry, revocation, permission change, and forced-disconnect behavior is defined.
- `reconnect_resume`: reconnect uses backoff with jitter and the declared delivery contract defines cursor scope, epoch, horizon, replay/duplicate behavior, atomic progress or deduplication, and expired-cursor resynchronization.
- `backpressure`: per-connection buffers are bounded and slow consumers cannot exhaust memory.
- `presence_cleanup`: presence and subscription state is cleaned up on disconnect.
- `connection_capacity`: concurrent-connection and file-descriptor budgets are tied to lifecycle, reconnect, and drain behavior.
- `drain_on_deploy`: deploys drain or migrate connections within an absorbable reconnect rate.
- `gap_detection`: missed or duplicate messages and expired history are observable and have a snapshot or reconciliation path.

## Red Flags - Stop And Rework

- Reconnect has no backoff, so a blip becomes a thundering herd.
- A slow consumer can grow an unbounded server-side buffer.
- Deploys drop every live connection at once.
- Streamed updates can be silently dropped with no resume cursor, gap signal, or resynchronization path.
- A cursor is claimed to prevent replay or skips without a retention horizon, epoch, atomic progress or deduplication, gap detection, and resynchronization path.
- A connected client retains subscriptions or action capability after token expiry, revocation, tenant change, or permission removal.
- Anonymous access exposes non-public data or privileged actions, or has no abuse/rate/fanout bounds.
- Presence state leaks after a client disconnects.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Reconnect immediately on drop | Back off with jitter and resume from a cursor or resynchronize according to the delivery contract. |
| Treating a cursor as exactly-once | Declare the delivery contract; make effects duplicate-safe and repair gaps or expired history. |
| Authorizing only the handshake | Reauthorize subscriptions and actions, and disconnect or reduce capability on expiry or revocation. |
| Requiring identity for every public stream while omitting it for sensitive streams | Declare authenticated access for non-public data/actions and narrowly bounded anonymous access only for deliberately public streams. |
| Buffer everything for slow clients | Bound buffers and shed or disconnect on overflow. |
| Treat deploys as connection-safe | Drain connections and bound the reconnect rate. |
| Assume delivery is gap-free | Detect and surface missed messages. |
