---
name: operational-ownership-transfer
description: "Use when operational ownership of a running system moves between teams and needs a verified acceptance gate"
---

# Operational Ownership Transfer

## Iron Law

```
NO OWNERSHIP TRANSFER WITHOUT A VERIFIED ACCEPTANCE GATE THAT THE RECEIVING TEAM CAN RUN AND CHANGE THE SYSTEM
```

A handoff that moves a system to a team which cannot operate it leaves the next incident with slow MTTR, unexecutable runbooks, and unknown failover paths. A single remaining owner is a single point of human failure.

## Overview

Produces the operational-acceptance gate for moving a running system between teams: a bus-factor and tribal-knowledge inventory, and a verified gate that the receiving team can run and change the system unaided, the operate-phase counterpart to a launch-readiness review. It owns the transfer event and routes doc freshness, steady-state paging, and concurrent launch readiness out. It does not own staffing, headcount, or compensation.

**Core principle:** prove the receiving team can operate and change the system before the transfer is done, not after the next incident.

## When To Use

- Operational ownership of a running system is moving from one team to another.
- A single owner or undocumented dependency makes the system a bus-factor risk.
- The receiving team needs a verified gate that it can deploy, roll back, page, and recover for the system.
- Tribal knowledge must convert to verified, executable capability before the handoff closes.

## When Not To Use

- The concern is document freshness and source of truth; use `documentation-lifecycle`.
- The concern is steady-state paging, toil, and alert load for an existing owner; use `oncall-health`.
- The concern is a concurrent launch or traffic-shift readiness; use `production-readiness-review`.
- The concern is the architectural responsibility record for a component; use `architecture-decisions`.
- A system being retired rather than handed over goes to `migration-and-deprecation` then `service-decommission-and-sunset`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- The system being transferred, the giving team, and the receiving team.
- Current single owners, undocumented dependencies, and known landmines.
- Existing runbooks, deploy and rollback procedures, and failover steps.
- The receiving team's current paging, access, and operational familiarity.
- Any concurrent launch or change happening alongside the transfer.

## Workflow

1. **Inventory bus-factor and tribal knowledge.** Identify single owners, undocumented dependencies, manual steps, and known landmines that live only in someone's head.
2. **Verify runbook executability.** Have the receiving team run the runbooks and record where they fail or assume tribal knowledge.
3. **Dry-run deploy and rollback.** Confirm the receiving team can deploy, roll back, and perform a manual failover for the system.
4. **Transfer paging and escalation.** Move paging and escalation ownership into the receiving team's rotation and verify it fires.
5. **Hand over the dependency map.** Give the receiving team the upstream and downstream dependency map and the contacts for each.
6. **Gate on acceptance.** Hold a dated acceptance gate with a blocker register; the transfer is not done while blockers remain open.
7. **Route the rest.** Send doc freshness to `documentation-lifecycle`, steady-state paging to `oncall-health`, and any concurrent launch readiness to `production-readiness-review`.

## Synthesized Default

Convert tribal knowledge to a verified acceptance gate: receiver-run runbooks, a deploy and rollback dry-run, paging in the receiver's rotation, and a dated blocker register. The receiving team must pass the gate unaided; an open blocker stops the transfer.

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

- A short temporary transfer can use a smaller gate only when duration, rollback owner, and emergency escalation are explicit.
- Staffing, compensation, and org design remain out of scope unless framed as an operational single-point-of-failure control.
- Concurrent launch readiness stays with `production-readiness-review`; this specialist owns the transfer gate.

## Response Quality Bar

- Lead with the transfer blocker, acceptance gate, bus-factor risk, or runbook executability result requested.
- Cover tribal knowledge, runbook execution, deploy and rollback dry-runs, paging transfer, dependency map, blockers, and handoffs before optional ownership breadth.
- Make recommendations actionable with acceptance criteria, dry-run evidence, blocker owners, dates, and routing for adjacent work.
- Name the details to inspect, such as current owners, runbooks, deploy and rollback procedures, failover steps, paging routes, access, and dependency maps; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside verified operational transfer; route doc lifecycle, on-call health, production readiness, or architecture ownership when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Bus-factor and tribal-knowledge inventory: single owners, undocumented dependencies, landmines.
- Runbook executability result: which runbooks the receiver ran and where they failed.
- Deploy, rollback, and failover dry-run result.
- Paging and escalation transfer confirmation.
- Dependency map handover.
- Dated acceptance gate with a blocker register.
- Handoffs to `documentation-lifecycle`, `oncall-health`, `production-readiness-review`.

## Checks Before Moving On

- `bus_factor`: single owners and undocumented dependencies are identified.
- `runbook_executable`: the receiving team ran the runbooks and gaps are recorded.
- `deploy_rollback_dryrun`: the receiver demonstrated deploy, rollback, and failover.
- `paging_transferred`: paging and escalation fire in the receiver's rotation.
- `dependency_map`: upstream and downstream dependencies and contacts are handed over.
- `acceptance_gate`: a dated gate with an open-blocker register decides done.

## Red Flags - Stop And Rework

- The transfer closes on a doc handoff with no verified capability.
- One person still holds knowledge nobody else can execute.
- The receiving team has never deployed or rolled back the system.
- Paging still routes to the giving team after transfer.
- The acceptance gate has open blockers but is called done.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Hand over docs and call it transferred | Verify the receiver can run and change the system. |
| Leave knowledge with one person | Convert it to executable runbooks and a dry-run. |
| Forget to move paging | Transfer paging and escalation and confirm it fires. |
| Skip the dependency map | Hand over upstream and downstream dependencies and contacts. |
