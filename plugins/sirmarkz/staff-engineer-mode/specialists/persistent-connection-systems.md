---
name: persistent-connection-systems
description: "Use when long-lived client connections need lifecycle, backpressure, presence, and drain-on-deploy design"
---

# Persistent Connection Systems

## Iron Law

```
NO LONG-LIVED CONNECTION WITHOUT RECONNECT-WITH-RESUME, PER-CONNECTION BACKPRESSURE, AND A DRAIN-ON-DEPLOY PATH
```

A persistent-connection feature with no resume cursor, no slow-consumer bound, and no connection-drain path will reconnect-storm after a blip, exhaust server memory on slow clients, and sever every live session on deploy.

## Overview

Produces the connection-protocol spec and a capacity and drain plan for long-lived client connections: handshake, heartbeat and idle timeout, reconnect with backoff and resume-from-cursor, presence and subscription and fanout state, per-connection and per-channel backpressure for slow consumers, protocol-tied connection capacity, and connection draining on deploy. It owns the connection lifecycle and routes broker-mediated delivery and request/reply policy out.

**Core principle:** every long-lived connection must resume without gaps, push back on slow consumers, and drain cleanly on deploy.

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
- Slow-consumer handling today and what happens to server memory when a client cannot keep up.
- Presence, subscription, and fanout state and where it lives.
- Deploy and rotation cadence and how connections are drained, if at all.

## Workflow

1. **Define the connection lifecycle.** Specify handshake, heartbeat and keepalive, idle timeout, and clean close.
2. **Make reconnect safe.** Require backoff with jitter on reconnect and a resume-from-cursor so a reconnect does not replay or skip messages, and so a fleet of clients does not reconnect in lockstep.
3. **Bound slow consumers.** Define per-connection and per-channel backpressure, buffer limits, and what happens when a client cannot keep up so one slow consumer cannot exhaust memory.
4. **Manage presence and fanout.** Define how presence and subscription state is established, refreshed, and cleaned up so it does not leak on disconnect.
5. **Size protocol-tied connection capacity.** State concurrent-connection and stream limits, file-descriptor budget, and affinity or sticky-routing needs as part of the connection lifecycle, reconnect, and drain design.
6. **Drain on deploy.** Define how connections drain on deploy and rotation so sessions migrate or resume rather than drop, and bound the reconnect rate the backend can absorb.
7. **Detect gaps.** Define ordering and gap detection for streamed updates so a missed message is observable, not silent.

## Synthesized Default

Give each long-lived connection a resume cursor, a slow-consumer bound, and a drain-on-deploy path. Use backoff-with-jitter reconnect and bounded per-connection buffers to avoid unbounded queues and lockstep reconnect. A deploy that drops live sessions is a defect.

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

- Small internal streams can accept reconnect without resume only when message loss is harmless and documented.
- One-way notification streams still need backpressure, heartbeat, and drain behavior.
- Client-specific offline sync belongs with client release gates when the connection lifecycle is no longer the dominant risk.

## Response Quality Bar

- Lead with the connection lifecycle, reconnect, backpressure, capacity, or drain decision requested.
- Cover handshake, heartbeat, reconnect-with-resume, slow-consumer bounds, presence cleanup, capacity, drain, and gap detection before optional client or broker breadth.
- Make recommendations actionable with protocol choices, buffer limits, reconnect-rate bounds, deploy-drain steps, and verification cases.
- Name the details to inspect, such as connection counts, message rates, resume cursor behavior, buffer growth, deploy logs, and presence state; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside long-lived connection lifecycle and drain; route broker workflows, request/reply dependency policy, and raw capacity when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Connection-protocol spec: handshake, heartbeat, idle timeout, close.
- Reconnect and resume decision: backoff with jitter and resume-from-cursor.
- Backpressure and slow-consumer policy: buffer limits and overflow behavior.
- Presence, subscription, and fanout state lifecycle.
- Protocol-tied connection-capacity plan: concurrent limits, file-descriptor budget, affinity, and the lifecycle decision each limit protects.
- Drain-on-deploy plan and absorbable reconnect-rate bound.
- Ordering and gap-detection decision for streamed updates.

## Checks Before Moving On

- `reconnect_resume`: reconnect uses backoff with jitter and resumes from a cursor without replay or skip.
- `backpressure`: per-connection buffers are bounded and slow consumers cannot exhaust memory.
- `presence_cleanup`: presence and subscription state is cleaned up on disconnect.
- `connection_capacity`: concurrent-connection and file-descriptor budgets are tied to lifecycle, reconnect, and drain behavior.
- `drain_on_deploy`: deploys drain or migrate connections within an absorbable reconnect rate.
- `gap_detection`: missed messages in a stream are observable.

## Red Flags - Stop And Rework

- Reconnect has no backoff, so a blip becomes a thundering herd.
- A slow consumer can grow an unbounded server-side buffer.
- Deploys drop every live connection at once.
- Streamed updates can be silently dropped with no resume cursor.
- Presence state leaks after a client disconnects.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Reconnect immediately on drop | Back off with jitter and resume from a cursor. |
| Buffer everything for slow clients | Bound buffers and shed or disconnect on overflow. |
| Treat deploys as connection-safe | Drain connections and bound the reconnect rate. |
| Assume delivery is gap-free | Detect and surface missed messages. |
