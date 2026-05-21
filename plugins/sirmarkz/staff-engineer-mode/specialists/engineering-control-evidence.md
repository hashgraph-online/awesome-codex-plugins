---
name: engineering-control-evidence
description: "Use when designing or collecting cross-surface engineering records, scorecards, exceptions, or control maps"
---

# Engineering Control Records

## Iron Law

```
NO CROSS-SURFACE CONTROL MAP WITHOUT REPEATABLE RECORD SOURCE, CADENCE, EXCEPTION PATH, AND REFRESH TRIGGER PER CONTROL
```

If a control cannot be inspected against a maintained, repeatable engineering artifact on a defined cadence, it is not part of this skill. Single-surface records belong in the matching specialist skill.

> This skill assumes a multi-surface engineering records request. The artifacts it produces (cross-surface control maps, engineering scorecards, exception registers) exist to coordinate records across different engineering surfaces. A solo developer can still use it when one project needs a combined record pack; single-domain records stay with the matching specialist skill.
> Even in a cross-project context, this skill aggregates locally available engineering records for the user. It does not wait for legal, manager, or external sign-off.

## Overview

Engineering controls are useful only when they are close to the work and produce records from engineering systems.

**Core principle:** aggregate records from artifacts projects already create: diffs, tests, build attestations, deployment records, runbooks, incidents, access-change records, scans, and exceptions.

## When To Use

- The request explicitly spans two or more engineering surfaces and asks to design or collect one record pack, scorecard, control-to-artifact map, or exception register.
- You need one normalized record inventory across SDLC, reliability, supply chain, access, vulnerability, observability, data, or operations because separate engineering surfaces otherwise duplicate tracking.
- The user asks how to show engineering standards are followed across delivery and operations using artifacts from normal engineering work.
- Cross-surface engineering exceptions need expiry, compensating controls, residual risk, and revisit triggers in one register.
- A multi-surface engineering record pack is required and no single specialist covers the full surface set.

## When Not To Use

- The request is single-launch, single-traffic-shift, or tier-change readiness; use `production-readiness-review`.
- A single specialist covers the needed records directly: deployed vulnerability details belong to `vulnerability-management`; build-path provenance belongs to `software-supply-chain-security`; identity, secrets, and access details belong to `identity-and-secrets`; reliability target details belong to `slo-and-error-budgets`; alert and telemetry details belong to `observability-and-alerting`; backup and restore test results belong to `backup-and-recovery`; tenant boundary checks belong to `tenant-isolation`; data lifecycle details belong to `privacy-and-data-lifecycle`; data pipeline details belong to `data-pipeline-reliability`; threat-model details belong to `secure-sdlc-and-threat-modeling`; AI-assisted change verification belongs to `ai-coding-governance`.
- The user asks for records but actually wants a single-domain answer; use the matching specialist above.
- The request is broad compliance, legal, procurement, vendor risk, auditor-liaison program management, or business program management outside engineering lifecycle and operations.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Engineering standards, systems in scope, delivery decisions, and who needs the records.
- Existing artifacts: PRs, CI logs, tests, scans, build records, deployments, runbooks, incidents, access reviews, and dashboards.
- Refresh cadence, exception rules, and who can accept the risk.
- Current scorecards, manual collection burden, gaps, incidents, and recurring findings.
- Required engineering expectations or internal guidelines and how they map to engineering behavior.
- Broad practice or checklist inputs that need translation into concrete engineering behavior and one owning specialist per item.

## Workflow

1. **Check cross-surface scope.** Confirm the work spans at least two specialist engineering surfaces and that no single specialist covers the full record set. If the request is single-launch readiness, use `production-readiness-review`. If the request is single-domain records, use the matching specialist and stop.
2. **Map expectations to behavior.** Express each expectation as something engineers do, prevent, detect, confirm, test, or verify.
3. **Translate source material.** For broad practice inputs, rewrite each technical item into capability language, assign one owning specialist, and skip org-only or non-technical items.
4. **Locate records near engineering work.** Prefer generated records from changes, CI, deploys, access systems, scanners, runbooks, and incidents.
5. **Assign responsibility and cadence.** Every record source needs an owner, refresh cadence, and failure response.
6. **Define exceptions.** Require expiry, compensating control, refresh trigger, and risk-acceptance authority appropriate to severity.
7. **Build scorecards carefully.** Score capabilities and record state, not vanity metrics. Normalize overlapping security, reliability, supply-chain, operations, and internal engineering expectations into one record map.
8. **Create standards backlog.** Record gaps from failed record pulls, expired exceptions, incidents, and recurring findings with severity, expected fix path, and target date.
9. **Feed findings back.** Use incidents, failed reviews, and recurring exceptions to update standards and platform defaults.

## Synthesized Default

Keep records close to engineering workflows and automate collection where possible. Use one expectation-to-record map across overlapping engineering standards, benchmarks, and internal checklists so projects do not maintain duplicate tracking or conflicting interpretations.



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

- Single-surface records should be produced by the specialist skill, with this skill only aggregating if needed.
- Manual records can be temporary when automation is not yet available, but they need expiry and a replacement path.
- Legal/auditor-facing interpretation is out of scope; this skill produces engineering records, not legal conclusions.
- Threat-detection mapping is included only when detection coverage is explicitly in scope.

## Response Quality Bar

- Lead with the expectation-to-record map, scorecard, exception register, or record pack outline requested.
- Cover engineering behavior, repeatable record sources, cadence, pass/fail states, exceptions, and workflow fit before optional program breadth.
- Make recommendations actionable with artifact sources, collection cadence, failure response, automation backlog, and exception expiry where relevant.
- Name the details to inspect, such as CI results, deploy records, configuration snapshots, change records, incident records, control outputs, and source artifact links; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside engineering records. Do not make legal, procurement, staffing, or external-assurance statements.
- Be concise: avoid generic compliance language and prefer compact engineering record tables.

## Required Outputs

- Engineering expectation-to-behavior-to-record map.
- Translation map from broad practice items to one owning specialist, with non-technical items marked skipped.
- Record inventory with source, cadence, and retention.
- Scorecard with pass/fail/exception states.
- Exception register with expiry, compensating controls, refresh trigger, residual risk, and acceptance authority.
- Record pack outline linked to source artifacts.
- Standards update backlog with gap source, engineering expectation, severity, expected fix path, and target date.

## Checks Before Moving On

- `scope_check`: request explicitly spans two or more engineering surfaces, no single specialist covers the full record set, and non-engineering program management is excluded.
- `record_source`: every expectation maps to a repeatable engineering artifact source.
- `source_translation`: broad practice inputs are rewritten as concrete engineering behavior and assigned to one owning specialist, with org-only items skipped.
- `cadence_check`: every record source has refresh cadence and failure response.
- `exception_check`: exceptions have expiry, compensating control, and refresh trigger.
- `workflow_fit`: records are captured from normal engineering workflows where possible.

## Red Flags - Stop And Rework

- Expectations are copied from standards without mapping to engineering behavior.
- A key record is a screenshot someone must manually collect every quarter.
- Exceptions never expire.
- Scorecards reward document presence rather than control effectiveness.
- The skill is being used as lawyer, procurement owner, staffing owner, or compliance-program manager.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Central record chores | Put records in the workflow that creates them. |
| Duplicate maps per standard | Normalize overlapping expectations into one record map. |
| Open-ended exceptions | Add expiry, compensating control, and refresh trigger. |
| Using this for everything | Prefer domain skills for single-surface records. |
