---
name: data-lineage-and-provenance
description: "Use when regulated or business data needs source-of-record, derivation graphs, and recompute impact analysis"
---

# Data Lineage And Provenance

## Iron Law

```
NO REGULATED OR REPORTED FIGURE WITHOUT A SOURCE-OF-RECORD AND A DERIVATION GRAPH THAT SUPPORTS RECOMPUTE
```

A reported number with no source-of-record and no derivation graph cannot be defended to an auditor, and when its upstream source is wrong, nobody can find and recompute every figure it touched.

## Overview

Produces the governance and audit lineage spine for business and regulated data across operational and analytical systems: origin capture, transformation and derivation chains, source-of-record designation, downstream consumer and report and model dependency graphs, and source-correctness blast-radius and recompute impact analysis. It answers "what is the authoritative source for this number, how was it computed, and what must be recomputed if the source was wrong." It routes pipeline recovery, personal-data lifecycle, and build provenance out.

**Core principle:** know the authoritative source and full derivation chain for regulated figures, so the team can bound recompute after a bad source.

## When To Use

- Regulated or reported business data needs a source-of-record and a defensible derivation chain.
- A bad upstream source requires finding and recomputing every derived figure, dashboard, dataset, or model it touched.
- An auditor or regulator asks how a number was produced and from which authoritative source.
- Purpose or consent origin tags must travel with data across service and storage boundaries.

## When Not To Use

- The concern is pipeline freshness, replay, or backlog recovery; use `data-pipeline-reliability`.
- The concern is personal-data inventory, consent, or erasure; use `privacy-and-data-lifecycle`.
- The concern is build-artifact provenance, artifact inventory, or signing; use `software-supply-chain-security`.
- The concern is boundary schema compatibility; use `data-contracts`.
- Storage and consistency semantics go to `distributed-data-and-consistency`; multi-surface control evidence goes to `engineering-control-evidence`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- The regulated or reported figures in scope and who consumes them.
- The systems each figure flows through, operational and analytical.
- Candidate source-of-record for each figure and any competing sources.
- Transformation and derivation steps between source and reported figure.
- Existing lineage capture, if any, and where it breaks at boundaries.

## Workflow

1. **Designate source-of-record.** For each figure, name the authoritative source and resolve competing sources.
2. **Capture origin and derivation.** Record where data originates and each transformation that produces the reported figure.
3. **Build the dependency graph.** Map downstream consumers, reports, datasets, and models that depend on each source. Record provenance with an entity/activity/agent model (what was derived, by which process, attributed to which owner) and stamp each derivation edge with the producing process version and timestamp so a published figure can be defended and recomputed.
4. **Cross boundaries.** Make lineage survive service and storage boundary crossings, not stop at the edge of one system.
5. **Carry purpose tags.** Where consent or purpose constrains use, attach tags that travel with the data.
6. **Define recompute impact.** For a wrong source, define how to compute the blast radius and recompute or restate every derived figure.
7. **Make it auditable.** Produce a lineage record an auditor or regulator can follow from reported figure back to authoritative source.

## Synthesized Default

Designate a source-of-record, capture the derivation chain, and build the downstream dependency graph so the team can bound recompute after a bad source. Lineage must survive boundary crossings; per-system lineage that stops at the edge leaves recompute scope unknown. Route pipeline recovery and personal-data lifecycle to their specialists.

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

- Local diagnostic metrics can use lighter lineage if they are not regulated, reported externally, or used for material decisions.
- Personal-data deletion and consent workflows remain with privacy lifecycle when the lineage graph is not the central artifact.
- Pipeline freshness and replay controls stay with pipeline reliability after lineage identifies the impacted graph.

## Response Quality Bar

- Lead with the missing source-of-record, derivation gap, dependency graph, or recompute-impact decision requested.
- Cover authoritative sources, transformations, downstream consumers, boundary crossings, purpose tags, recompute procedure, and auditable records before optional data-governance breadth.
- Make recommendations actionable with lineage tables, graph edges, recompute steps, and records an auditor can follow.
- Name the details to inspect, such as data flows, transformations, reports, datasets, models, source candidates, and existing lineage capture; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside governance and audit lineage; route pipeline recovery, privacy lifecycle, contract compatibility, and build provenance when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Source-of-record designation per regulated figure.
- Origin and derivation chain from source to reported figure.
- Provenance records using an entity/activity/agent model with version and timestamp on each derivation edge.
- Downstream dependency graph: consumers, reports, datasets, models.
- Boundary-crossing lineage decision.
- Purpose and consent origin tags where they apply.
- Recompute and restatement impact procedure for a wrong source.
- Auditable lineage record from figure back to source.

## Checks Before Moving On

- `source_of_record`: every regulated figure has one authoritative source, competing sources resolved.
- `derivation_chain`: the transformations from source to figure are captured.
- `provenance_model`: each derivation edge records the producing process, responsible owner, and the version and time it ran.
- `dependency_graph`: downstream consumers, reports, datasets, and models are mapped.
- `boundary_lineage`: lineage survives service and storage boundary crossings.
- `recompute_impact`: a wrong source has a defined blast-radius and recompute procedure.
- `auditable`: the lineage record can be followed from figure back to source.

## Red Flags - Stop And Rework

- A reported figure has no designated source-of-record.
- Lineage stops at the boundary of one system.
- A wrong upstream source has no way to find what it touched.
- Competing sources for the same figure are unresolved.
- The lineage record cannot be followed end to end.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treat pipeline lineage as governance lineage | Build a source-to-figure graph that survives boundaries. |
| Leave the authoritative source implicit | Designate and resolve source-of-record per figure. |
| Lineage as an undated diagram | Use an entity/activity/agent model with version and timestamp per edge. |
| Skip downstream mapping | Map every consumer, report, dataset, and model. |
| Discover recompute scope during the incident | Define blast-radius and recompute before you need it. |
