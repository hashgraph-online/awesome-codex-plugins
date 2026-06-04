---
name: production-readiness-review
description: "Use when launch, migration, impact change, major traffic shift, or release needs go/no-go readiness details"
---

# Production Readiness Decision

## Iron Law

```
NO LAUNCH READINESS CLAIM WITHOUT REVIEWABLE EVIDENCE OR A DATED RISK RECORD
```

Per the shared governance and risk-acceptance lifecycle, missing evidence is a blocker, a recorded follow-up with check path and due date, or explicit dated risk acceptance with compensating control. Controls without artifacts cannot be claimed as effective.

## Overview

Produces a dimensioned launch posture with a readiness matrix, a blocker list, and an exception register with expiry dates. Stops launches that confuse intentions for checked facts. Risk acceptance and exception handling follow the shared risk-acceptance lifecycle and compensating-control format.

**Core principle:** before launch or major traffic shift, show with artifacts, not intentions, that responsibility, reliability, observability, safe change, security, capacity, recovery, and incident paths are good enough for the declared impact.

## When To Use

- The user asks whether a service, feature, migration, impact increase, major traffic shift, or system is ready for production.
- A launch touches multiple engineering surfaces and needs one readiness posture.
- The user asks for production readiness across responsibility, SLOs, rollout, security, capacity, recovery, and operations.
- You need blockers, exceptions, and follow-up routes before go/no-go.

## When Not To Use

- A small code change has no production responsibility, operational, security, or reliability impact.
- The user needs one narrow artifact, such as only an SLO table (use `slo-and-error-budgets` instead) or only a threat model (use `secure-sdlc-and-threat-modeling` instead).
- The request is model-serving promotion details, eval thresholds, skew, drift, monitoring, or rollback; use `ml-reliability-and-evaluation` instead.
- A live incident is underway; route to `incident-response-and-postmortems` first.
- The question is business confirmation, marketing launch, legal release decision, or procurement; out of scope.

## Info To Gather

- Launch scope, impact dimensions, customer/user impact, production dependencies, and user decision point.
- Architecture artifact: component diagram or textual component map, request/data flow, upstream and downstream dependencies, and fault-domain boundaries.
- Operability: launch and rollback owner when the path is not fully automated CI/CD with automatic rollback; responder handoff, fallback path, diagnostics, incident path, post-launch watch window, and user decision point.
- SLOs/error budgets, dashboards, alerts, runbooks, and incident communication path.
- Availability posture: location independence, partition survivability, static failover capacity, and recovery drill results.
- Rollout plan, rollback path, canary metrics, migration plan, and feature/config lifecycle.
- Security posture: threat model, data classification, access controls, secrets, supply-chain controls, and vulnerability status.
- Capacity, load-test results, overload behavior, failover target, and dependency quotas.
- Backup/restore, DR results, data migration validation, and destructive-change safeguards.
- Freshness of readiness details: last checked dashboards, alerts, runbooks, rollout checks, recovery checks, load tests, and open drift since the last readiness decision.
- Open risks, exceptions, compensating controls, expiry dates, and follow-up actions using the shared risk-acceptance lifecycle and compensating-control format.

## Workflow

1. **Classify launch scope.** State what is launching, who is affected, and which standard applies.
2. **Classify launch impact.** Classify launch impact along five dimensions, not as a single ordinal label: external commitment, customer-criticality, data sensitivity, state durability, and blast radius. Stricter checks attach to dimensions that apply, not to a number. This dimensioned approach follows the shared risk-response framing.
3. **Collect artifacts.** Gather readiness details from specialist domains instead of rewriting all domain work inside PRR; mark stale details and drift since the last relevant readiness decision.
4. **Check architecture shape.** Identify the component diagram or textual map, production dependencies, fault-domain map, and user-flow health model for the launch path; if these are missing for a customer-impacting launch, mark the architecture gap explicitly.
5. **Mark each domain.** Use Pass, Blocker, Exception, Follow-up, or Not Applicable. A gap is a Blocker when it can violate the launch's user, data, security, recovery, or rollback requirement before launch; it is a Follow-up only when launch risk remains bounded and the follow-up action, check path, and due date are explicit.
6. **Check runtime readiness.** Require SLOs, journey health model, telemetry, alerts, runbooks, fallback path, diagnostics, and incident path for customer-impacting launches.
7. **Check change readiness.** Require rollout, rollback, canary, compatibility, migration, and cleanup details.
8. **Check resilience and recovery.** Require location or partition independence, static failover capacity, overload behavior, failover targets, recovery drills, and restore test results when relevant.
9. **Check security and integrity.** Require threat model, access controls, secret handling, build integrity, and unresolved vulnerability posture.
10. **Check cross-pillar tradeoffs.** Identify reliability, security, cost, operational, and performance decisions that improve one quality while weakening another.
11. **Check ownership and watch.** For manual or semi-automated launch and rollback paths, name the launch owner and rollback owner; for fully automated CI/CD with automatic rollback, name the automation path instead. Always name responder handoff, post-launch watch window, and success or abort checks.
12. **Summarize advisory posture.** Produce blockers, exceptions, and follow-up routes. The skill identifies objective blockers and readiness gaps; the user decides whether to proceed.
13. **Pair release cuts with build traceability.** For a new release, run `release-build-reproducibility` before the first release command so pinned inputs, artifact identity, promotion, and rollback traceability are reviewed alongside readiness.

## Synthesized Default

Use PRR as a cross-domain readiness decision for launches and major changes. It should inspect available details, identify missing artifacts, expose cross-pillar tradeoffs, and route only the highest-risk gaps. It should not auto-load every specialist skill.



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

- Internal prototypes may use advisory PRR if they cannot affect customers, production data, or shared infrastructure.
- Externally committed, regulated, stateful, or sensitive-data systems require stricter checks and dated risk acceptance using the shared risk-acceptance lifecycle.
- Emergency launches can proceed with documented risk when delaying is worse, but follow-up checks and post-launch checks are mandatory.
- A domain can be Not Applicable only with the disqualifying property, supporting details, and reason, not by omission.

## Response Quality Bar

- Lead with the launch posture, blocker list, exception register, or readiness decision boundary requested.
- Show the structured PRR artifact to the user before any release receipt, tag, promotion, or override receipt. Use `skills/_shared/assets/templates/prr-checklist.md` when available, or render the same headings and tables.
- Cover architecture, responsibility, runtime readiness, safe change, recovery, security, and capacity details before optional PRR breadth.
- Include an architecture row for customer-impacting launches: component diagram or textual map, dependencies, and fault-domain map.
- Make recommendations actionable with missing details, checks, due dates, stop criteria, user risk acceptance, and exception expiry where relevant using the shared risk-acceptance lifecycle.
- Name the details to inspect, such as dashboards, SLOs, rollout plans, runbooks, load tests, restore checks, threat models, and vulnerability status; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside launch readiness. Route only the highest-risk specialist follow-ups and cap them at two unless the user asks for a full readiness pack.
- Be concise: avoid generic checklist prose and prefer compact readiness matrices, blocker tables, and exception registers.

## PRR Output Scaling

Show a user-visible structured PRR artifact, scaled to launch impact.

- **Local source checkpoint:** local tag/build/checkpoint; no push, publish, deploy, users, runtime, production data, or external commitment.
- **External artifact:** pushed tag, hosted release, package, or artifact used outside the local repo.
- **Production/customer-impacting:** deploy, traffic shift, migration, stateful change, customer-facing change, or sensitive-data change.

If scope is ambiguous, ask once:

> I am treating this as local-only because it is not being pushed, published, deployed, or exposed to users. If wrong, tell me whether this is public or production/customer-impacting.

Local output: compact table with scope, impact dimensions, checks, blockers/exceptions (`None` if absent), and advisory posture.

External output: compact readiness matrix with commitment, compatibility, rollback, checks, blockers/exceptions, and advisory posture.

Production/customer-impacting output: full `prr-checklist.md` shape.

## Required Outputs

- Output shape: use PRR Output Scaling. Use the full template for production/customer-impacting changes; include compact structured fields for local source checkpoints and external artifacts.
- PRR readiness matrix by domain and status.
- Freshness and drift notes for readiness details that can go stale, such as dashboards, runbooks, rollout checks, recovery checks, and load tests.
- Architecture entry with component diagram or textual map, production dependencies, and fault-domain map.
- Launch ownership or automation path, plus post-launch verification plan with responder handoff, watch window, and success or abort checks.
- Availability row covering fault-domain independence, static capacity under loss, recovery mechanism, and drill results.
- Launch blocker list with required details, file/path or artifact reference, and due date.
- Exception register with user risk acceptance, expiry, compensating control, and refresh trigger using the shared risk-acceptance lifecycle and compensating-control format.
- Advisory launch posture and risk summary.
- Specialist follow-up routes, capped and prioritized.
- Impact dimensions and advisory boundaries: which dimensions apply, what the skill can mark as blocker, exception, follow-up, or not applicable, versus who decides launch.

## Checks Before Moving On

- `impact_check`: classification names which impact dimensions apply (external commitment, customer-criticality, data sensitivity, state durability, blast radius) and which do not, with rationale.
- `architecture_check`: architecture details include component diagram or textual component map, production dependencies, and fault-domain map for the affected launch path.
- `ownership_check`: manual or semi-automated paths name launch and rollback owners; fully automated CI/CD with automatic rollback names the automation path; responder handoff, post-launch watch window, and success or abort checks are explicit.
- `operability_check`: every production component has fallback path, diagnostics, impact context, and user decision point.
- `runtime_check`: customer-impacting paths have SLOs, health states, telemetry, alerts, runbooks, and incident path.
- `change_check`: rollout, rollback, canary metrics, compatibility, and cleanup are documented.
- `freshness_check`: readiness details that can drift have a last-checked signal, current source, or explicit follow-up using the shared continuous-monitoring and performance-evaluation discipline.
- `availability_check`: customer-impacting systems have location/partition independence, static failed-domain capacity, recovery path, and validation results or an explicit exception.
- `recovery_check`: stateful or high-impact systems have restore/DR results or an explicit exception.
- `exception_check`: every accepted risk has explicit user acceptance, expiry, compensating control, and refresh trigger using the shared risk-acceptance lifecycle and compensating-control format.

## Red Flags - Stop And Rework

- The checklist is green but has no links, commands, artifact references, or explicit user decision point.
- PRR gives go/no-go authority to the agent instead of presenting details for the user decision.
- PRR is performed privately and only the receipt, verdict, or launch posture is shown to the user.
- Exceptions never expire.
- The launch can roll forward but cannot roll back or stop safely.
- "Not applicable" is used to avoid security, recovery, or incident checks without rationale.
- A missing blocker is downgraded to follow-up without stating why the launch risk remains bounded.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating PRR as a mega-skill | Aggregate readiness details and route gaps to specialists. |
| Counting intentions as facts | Require artifacts, commands, dashboards, runbooks, or dated risk-acceptance records using the shared risk-acceptance lifecycle. |
| Making all risks equal | Separate blockers from accepted exceptions and follow-ups. |
| Forgetting responsibility | Name launch/rollback owners when humans run the path; name the automation path when CI/CD and rollback are automatic; every blocker and exception needs supporting details, expiry, and user decision point. |
