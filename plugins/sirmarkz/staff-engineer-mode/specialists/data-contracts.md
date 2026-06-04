---
name: data-contracts
description: "Use when designing shared schemas, events, datasets, files, streams, or domain interfaces across components"
---

# Data Contracts And Domain Interfaces

## Iron Law

```
NO SHARED DATA INTERFACE WITHOUT A WRITTEN CONTRACT, COMPATIBILITY RULES, AND CURRENT OR PLANNED CONSUMERS
```

A "shared interface" is anything another component reads: a peer service, a downstream job, a different repo, even a future-you script. The contract states field meanings, types, and validity. Compatibility rules state what counts as additive vs breaking. For a new system, name the first expected consumers and the assumptions they depend on; for an existing system, name real consumers or the unknown-consumer risk.

> This skill assumes the data crosses a component or repo boundary. If the data model is fully private to one component with no external readers, use `architecture-decisions` instead.

## Overview

Data contracts let projects change independently without guessing what consumers depend on.

**Core principle:** make producer and consumer expectations explicit, versioned, maintained, compatibility-tested, and observable.

## When To Use

- The user asks about data contracts, schemas, domain interfaces, producer/consumer compatibility, schema evolution rules, or contract testing across projects.
- A new shared dataset, event shape, file, stream, or domain interface is being designed before consumers exist in production.
- A field, event, dataset, file, stream, or service output is consumed outside the responsible component.
- Producers and consumers deploy independently or interpret the same data differently.
- Data meaning, compatibility, responsibility, or evolution rules are unclear.

## When Not To Use

- One exposed service API contract is the whole problem; use `api-design-and-compatibility` instead.
- Workflow ordering, retries, or dead-letter handling is central; use `event-workflows` instead.
- Pipeline freshness, reprocessing, or lineage is central; use `data-pipeline-reliability` instead.
- The data model is fully private to one component and has no current or planned external consumers.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Producers, planned or existing consumers, domain meaning, critical fields, and consumer release cadence.
- Contract format, schema location, versioning policy, compatibility modes, and deprecation rules.
- Required, optional, nullable, defaulted, derived, sensitive, and deprecated fields.
- Consumer tests, sample payloads, expected or production usage, validation failures, and unknown consumers.
- Change workflow, compatibility checks, migration windows, and rollback or dual-publish needs.

## Workflow

1. **Find the boundary.** Identify every planned or existing consumer that relies on the data shape, semantics, timing, or quality.
2. **Define the contract.** Record field meanings, types, requiredness, defaults, units, sensitivity, responsibility, and validity rules.
3. **Choose evolution rules.** State what changes are compatible, conditionally compatible, or breaking.
4. **Version deliberately.** Use versions when semantics break; prefer additive changes when consumers can tolerate them.
5. **Test both sides.** Add producer validation and consumer-focused compatibility checks before merge or release.
6. **Measure adoption.** Before launch, state expected consumers and acceptance checks; after launch, track consumer usage, validation failures, deprecated fields, and migration progress.
7. **Plan deprecation.** Keep overlap, telemetry, consumer notice, and removal checks for breaking or semantic changes.
8. **Use adjacent checks.** Use API, event workflow, or pipeline reliability skills when execution details dominate.

## Synthesized Default

Use maintained, versioned, machine-checkable contracts for shared data boundaries. Prefer additive evolution, tolerant readers, producer validation, consumer compatibility tests, usage telemetry when available, and explicit deprecation checks. Treat semantic changes as breaking even when the field shape stays the same.



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

- Single-component data can use lighter contracts if no independent current or planned consumers exist.
- Emergency corrections may break compatibility when wrong data is more dangerous, but need consumer impact analysis and repair plan.
- Exploratory data products can start advisory, then harden before production consumers depend on them.

## Response Quality Bar

- Lead with the contract decision, compatibility decision, schema evolution plan, or consumer migration requested.
- Cover planned or existing consumers, semantics, compatibility class, validation, consumer tests, telemetry where available, and deprecation checks before optional registry detail.
- Make recommendations actionable with compatibility matrix, change checks, migration batches, and removal criteria where relevant.
- Name the details to inspect, such as planned consumer assumptions, consumer inventory, schema history, sample payloads, validation output, usage telemetry, and migration status; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside shared data interfaces. Use API, workflow, or pipeline skills only when that surface is the unresolved risk.
- Be concise: prefer compact contract and compatibility matrices over generic process prose.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Data contract decision with producers, planned or existing consumers, and domain meaning.
- Compatibility matrix for fields, semantics, timing, quality, and versioning.
- Validation and consumer-test plan.
- Evolution, deprecation, and migration plan with planned-consumer assumptions, telemetry where available, and removal checks.
- Sensitive-data handling notes for shared fields.
- Follow-up checks for API, workflow, or pipeline execution where needed.

## Checks Before Moving On

- `consumer_inventory`: planned consumers, known consumers, and unknown-consumer risk are explicit.
- `contract_defined`: field meaning, shape, requiredness, validity, and sensitivity are stated.
- `compatibility_class`: every change is classified as compatible, conditional, or breaking.
- `consumer_check`: compatibility is tested against real or representative consumer expectations.
- `migration_check`: deprecated or breaking changes have adoption telemetry and removal criteria.

## Red Flags - Stop And Rework

- A field keeps the same name but changes meaning.
- Producers claim "no consumers use this" without usage data.
- Consumers parse undocumented fields or rely on incidental ordering.
- Validation checks shape but not required semantics.
- Deprecated fields have no removal check.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating schema as semantics | Document meaning, units, defaults, and validity. |
| Producer-only tests | Add consumer compatibility checks. |
| Guessing consumers | Name planned consumers before launch; use telemetry and responsibility discovery after launch. |
| Breaking by cleanup | Plan overlap and removal checks. |
