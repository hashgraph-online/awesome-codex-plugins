---
name: infrastructure-and-policy-as-code
description: "Use when infrastructure needs declarative desired state, policy checks, drift detection, or environment promotion"
---

# Infrastructure Desired State And Policy As Code

## Iron Law

```
NO INFRASTRUCTURE CHANGE WITHOUT VERSIONED DESIRED STATE, POLICY CHECKS, DRIFT RESPONSE, AND RECOVERY PLAN
```

If production infrastructure can change outside versioned desired state, policy checks, drift response, and a recovery plan, the platform is not controlled.

## Overview

Infrastructure is safer when desired state, policy checks, drift handling, and rollback are explicit.

**Core principle:** make infrastructure changes declarative, enforceable, traceable, and continuously reconciled.

## When To Use

- The user is designing or changing infrastructure as code, declarative delivery, policy as code, deployment admission, drift detection, environment promotion, or infrastructure rollback.
- A platform needs enforceable standards for deployment, networking, identity, secrets, tagging, or runtime configuration.
- Manual infrastructure changes are causing drift, outages, or traceability gaps.
- The user needs to map platform policies into automated checks.

## When Not To Use

- The request is application business logic policy.
- The work is broad platform product design; use `platform-golden-paths` instead.
- The main topic is artifact provenance or signing; use `software-supply-chain-security` instead.
- The request is one-off architecture without reusable infrastructure policy.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Infrastructure resources, environments, responsible change path, desired-state repositories, and change workflow.
- Infrastructure boundaries for independent fault domains, shared control-plane dependencies, drift detection, and emergency reconciliation path.
- Policy requirements: security, reliability, identity, network, secrets, tagging, cost, and operational standards.
- Deployment/admission points, promotion model, user confirmations, and emergency-change path.
- Drift sources, detection methods, reconciliation authority, and incident history.
- Rollback/roll-forward mechanisms, state storage, locks, and blast-radius controls.
- Secret material, secret references, diff redaction, and state-store protection requirements.

## Workflow

1. **Define desired state.** Identify which infrastructure and runtime config must be represented declaratively.
2. **Keep secrets out of desired-state diffs.** Store secret references, encrypted envelopes, or external secret bindings instead of plaintext; redact plans/diffs and fail the change if secret values appear in change artifacts.
3. **Make changes traceable in version control.** Require responsible change path, plans/diffs, checks, and user confirmations appropriate to risk.
4. **Encode and test policies.** Convert standards into automated rules with clear failure messages, fixture tests, historical dry runs where feasible, and an exception path.
5. **Separate platform and workload boundaries.** Make shared services, application environments, fault-domain boundaries, shared control-plane dependencies, and responsibility explicit so policy inheritance and exceptions are understandable.
6. **Enforce at the right point.** Use pre-merge, pre-deploy, admission, or continuous drift checks depending on risk and feasibility.
7. **Detect drift.** Compare actual state to desired state and decide whether to alert, reconcile, or open a ticket.
8. **Plan rollback.** State when rollback is possible, when roll-forward is safer, and how state is protected.
9. **Handle emergencies.** Permit manual break-glass only with separate emergency identity, traceability, maximum duration, automatic re-locking, reconciliation, and post-change check.
10. **Protect the source of truth.** Treat desired-state repositories, state stores, lock stores, and reconcilers as production control-plane dependencies with access control, backup, and recovery plans.
11. **Feed records.** Surface policy and drift records to scorecards and PRR where useful.

## Synthesized Default

Use declarative desired state, traceable changes, automated policy checks, clear platform/workload boundaries, drift detection, controlled reconciliation, and explicit emergency paths. Policies should be technology-agnostic standards expressed as enforceable rules.



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

- Some low-risk experiments can use temporary manual resources if isolated and expiry is enforced.
- Emergency changes may bypass normal change flow only with traceability and reconciliation.
- Not every policy should block immediately; advisory mode helps tune signal before enforcement.
- Roll-forward may be safer than rollback for stateful infrastructure; document the decision.

## Response Quality Bar

- Lead with the infrastructure workflow, policy decision, drift finding, or emergency-change procedure requested.
- Cover desired-state scope, traceability, plan/diff details, policy checks, enforcement mode, drift response, rollback or roll-forward, and emergency reconciliation before optional GitOps breadth.
- Make recommendations actionable with source-of-truth paths, policy rules, exception workflow, detection cadence, reconciliation steps, and checks where relevant.
- Name the details to inspect, such as repo paths, plans/diffs, user confirmations, policy outputs, drift reports, reconciliation logs, break-glass records, and deployment status; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside infrastructure workflow and policy-as-code. Route platform product work or supply-chain controls only when they are central to the decision.
- Be concise: avoid generic GitOps background and prefer compact workflow and control matrices.

## Required Outputs

- Infrastructure change workflow.
- Desired-state scope and responsibility.
- Fault-domain infrastructure boundary map, including shared state or control-plane dependencies that can defeat intended independence.
- Policy-as-code control matrix.
- Enforcement point and exception model.
- Drift detection and reconciliation plan.
- Rollback/roll-forward and emergency-change procedure.
- Secret-reference and diff-redaction guardrails.
- Desired-state and state-store protection plan.
- Links for change, policy, drift, and deployment records.

## Checks Before Moving On

- `desired_state`: managed infrastructure scope and source of truth are explicit.
- `change_record`: changes are linked to a plan/diff, responsible change path, and confirmation path.
- `secret_check`: desired state and change artifacts do not expose plaintext secrets.
- `policy_check`: policies map to engineering standards and enforcement/advisory mode.
- `drift_check`: drift detection and reconciliation response are defined.
- `infra_fault_boundary`: intended independent fault domains have separate configurable boundaries or an explicit shared-dependency exception.
- `emergency_check`: manual break-glass changes require separate identity, expiry, change history, reconciliation, and re-locking.

## Red Flags - Stop And Rework

- Production resources are changed manually and never reconciled.
- Policies block without clear error messages or exception path.
- Desired state is split across undocumented sources.
- Secret values appear in desired state, plan output, logs, or change diffs.
- Rollback assumes state can simply be reverted.
- Emergency changes leave permanent drift.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Policy as prose | Encode enforceable or traceable checks. |
| Blocking too early | Tune in advisory mode, then enforce high-signal rules. |
| Ignoring drift | Define detection, reconciliation, and the change path. |
| No emergency path | Add traceable break-glass and post-change cleanup. |
