---
name: documentation-lifecycle
description: "Use when runbooks, design docs, ADRs, or onboarding docs need owners, source of truth, or freshness rules"
---

# Engineering Documentation Lifecycle

## Iron Law

```
NO CRITICAL ENGINEERING DOC WITHOUT AUDIENCE, SOURCE OF TRUTH, FRESHNESS RULE, AND CHANGE TRIGGER
```

If a doc can mislead an operator or steer a change, it needs an audience, source of truth, freshness rule, and change trigger before it is usable.

## Overview

Engineering documentation is useful only when it is findable, maintained, current, authoritative, and tied to the system it describes.

**Core principle:** make docs part of the delivery system, with audience, freshness signal, source of truth, and change trigger.

## When To Use

- The user is designing, restructuring, or lifecycle-managing engineering docs, runbooks, design docs, decision records, onboarding guides, operational references, or documentation standards.
- The user asks to inventory stale docs or decide ownership, source of truth, freshness rules, verification cadence, or archive criteria.
- Documentation is stale, duplicated, missing hard to find, or disconnected from code and operations.
- A launch, migration, incident, or deprecation needs docs that remain accurate after the change lands.
- You need a doc lifecycle, not just copy editing.

## When Not To Use

- The main artifact is an architecture decision; use `architecture-decisions`.
- The main artifact is an incident timeline or postmortem; use `incident-response-and-postmortems`.
- The request is marketing, sales, or public positioning copy.
- The request is routine editorial or mechanical documentation maintenance with no source-of-truth dispute, operational guidance gap, stale-doc risk, or lifecycle decision.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Doc type, audience, source of truth, repo or system link, and user decision point.
- Current doc set, duplicates, stale pages, search paths, and missing operational references.
- Operational docs, runbooks, dashboard metric definitions, source of truth, freshness triggers, and alert/dashboard link health.
- Change triggers: code responsibility, service behavior, alerts, runbooks, interfaces, migrations, and deprecations.
- Verification cadence, freshness signal, archival rule, and exception path.
- Signs that users can find and apply the doc during real work.

## Workflow

1. **Classify docs by job.** Place every doc asset into exactly one quadrant: tutorial (learning-oriented), how-to (task-oriented), reference (information-oriented), or explanation (understanding-oriented). Tag runbooks and decision records separately as operational and architectural artifacts. Split or rewrite any doc that mixes quadrants until each piece sits in one.
2. **Name the audience.** State who uses the doc and what decision or task it supports.
3. **Assign responsibility.** Give every critical doc a user/agent responsibility path and an update trigger tied to the system lifecycle. Anonymous docs become stale silently.
4. **Pick the source of truth.** Remove or mark duplicates so readers know where authority lives.
5. **Add freshness signals.** Include last-verified state, lifecycle stage, change trigger, and archive rule; operational docs refresh after incidents, threshold changes, dependency changes, or readiness findings.
6. **Connect docs to delivery.** Link docs to code, alerts, dashboards, runbooks, release checks, or decision records where they are used.
7. **Test usability.** Verify a fresh agent or the user from a clean clone can find and follow the doc under realistic conditions.
8. **Retire stale docs.** Archive misleading content rather than keeping it searchable with no current source of truth.

## Synthesized Default

Use a lightweight documentation lifecycle: classify by user job, assign define source of truth, tie updates to system changes, add freshness signals, and archive stale material. Critical runbooks and launch docs should be checked as part of delivery, not after outages show they were wrong.



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

- Short-lived design notes may expire after the decision is recorded elsewhere.
- Exploratory notes can remain rough if clearly marked as non-authoritative.
- Emergency docs may start minimal but need cleanup immediately after the event.

## Response Quality Bar

- Lead with the doc lifecycle, inventory, rewrite plan, or freshness check requested.
- Cover audience, source of truth, doc type, update trigger, discoverability, and archival rule before optional style advice.
- Make recommendations actionable with verification cadence, stale-doc handling, and delivery checks where relevant.
- Name the details to inspect, such as current docs, usage paths, responsibility paths, stale pages, runbook tests, and change triggers; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside engineering documentation. Route architecture decisions, incident writeups, or marketing copy only when they are central.
- Be concise: prefer doc inventories and lifecycle rules over broad writing theory.

## Required Outputs

- Documentation inventory **table with explicit columns**: `Doc | Diátaxis quadrant (tutorial / how-to / reference / explanation) | Responsibility path | Source of truth | Last verified | Verification cadence | Staleness signal`. Runbooks and decision records tagged separately as operational/architectural.
- Source-of-truth map that **states the no-duplication rule explicitly** (e.g., "one canonical location per system; duplicates are marked non-authoritative or deleted").
- Freshness rule naming **both verification cadence AND staleness signal** (e.g., "verify every 90 days; mark `stale` if last-verified > cadence or if linked alert/code changed without doc update").
- Docs-as-code workflow: **traceable doc changes AND automated checks** (link-checker, markdown lint, CI build) running on every doc PR.
- Required docs for launch, operations, migration, or maintenance.
- Operational-doc freshness matrix for runbooks and dashboard metric definitions.
- Update triggers tied to code, operations, and release events.
- Stale-doc cleanup plan.
- Usability and findability checks.

## Checks Before Moving On

- `audience_job`: each critical doc names its reader and supported task.
- `doc_source`: responsibility path and source of truth are explicit.
- `quadrant_classification`: every doc in the inventory **table carries a visible quadrant label** (tutorial / how-to / reference / explanation); runbooks and decision records tagged separately as operational/architectural. Mixed-quadrant docs are split.
- `no_duplication_rule`: source-of-truth section states an explicit rule against duplication, not just "remove duplicates."
- `staleness_signal`: freshness policy names both a cadence and the signal that flips a doc to stale.
- `docs_as_code`: doc changes flow through linked changes AND automated checks (lint, link-check, or CI).
- `freshness_rule`: change trigger, lifecycle state, and archive rule exist.
- `delivery_link`: docs required for operation or launch are tied to delivery checks.
- `operational_doc_freshness`: runbooks and dashboard metric definitions have source of truth, freshness trigger, and last-verified signal.
- `usability_check`: someone can find and use the doc without tribal knowledge.

## Red Flags - Stop And Rework

- Two docs contradict each other and neither is marked authoritative.
- A runbook has no source of truth or last-verified signal.
- A launch depends on undocumented manual knowledge.
- Stale docs remain searchable after the system changes.
- Documentation standards focus on formatting while operational gaps remain.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Writing before audience | Start with reader job and decision. |
| Keeping every page forever | Archive misleading docs aggressively. |
| Treating docs as separate from delivery | Add update triggers to code and release workflows. |
| Style as control | Govern responsibility, truth, freshness, and usability. |
