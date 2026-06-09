---
name: platform-golden-paths
description: "Use when developer platforms, golden paths, service templates, scorecards, or paved-road defaults need design"
---

# Platform Engineering And Golden Paths

## Iron Law

```
NO GOLDEN PATH WITHOUT RESPONSIBILITY, SECURITY, OBSERVABILITY, DEPLOYMENT, AND OPERATIONS DEFAULTS
```

If a template creates a service but not an operable service, it is not a golden path.

> This skill can be used for a solo repo or a cross-project platform. Golden paths remove repeated setup; for a solo developer the same patterns live as repo templates and scripts, not as a platform product. Use `architecture-decisions` when the work is one service design rather than a reusable path.

## Overview

A good platform makes the safe path the easy path. Exception register fields follow the shared risk-register and compensating-control formats. Treat the platform as a product with users, a value proposition, and an owner, and optimize the paved road for reduced cognitive load.

**Core principle:** encode standards as reusable workflows, templates, scorecards, and self-service capabilities that projects use in routine work.

## When To Use

- The user asks about internal developer platforms, golden paths, paved roads, service catalogs, templates, scorecards, or standardized service creation.
- Multiple projects need repeatable service setup, deployment, responsibility, telemetry, security, or compliance records.
- The same operational or security gaps recur across services.
- A platform should reduce toil or make standards easier to satisfy.

## When Not To Use

- The work is one-off architecture for one service; use `architecture-decisions` instead.
- The request is only infrastructure policy mechanics; use `infrastructure-and-policy-as-code` instead.
- The request is compliance program management rather than engineering controls; use `engineering-control-evidence` instead only when in scope.
- The work is vendor selection or procurement; out of scope.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Target users, service types, common workflows, pain points, and current failure modes.
- Required defaults: responsibility, SLOs, telemetry, deployment, rollback, runbooks, security, secrets, cost tags, and recovery.
- Generated operational defaults: starter SLO, dashboard, alert/runbook, rollout, recovery, dependency inventory, and secure settings.
- Existing templates, catalogs, scorecards, delivery workflows, infrastructure modules, and exception process.
- Service catalog metadata source of truth, including owner, lifecycle, system relationships, API/dependency links, and operational links.
- Migration needs for existing services and adoption blockers.
- Platform responsibility, operating model, upgrade cadence, and feedback channels.

## Workflow

1. **Start from repeated pain.** Choose platform capabilities that remove recurring setup, safety, security, or operations work.
2. **Define the golden path.** Specify the service lifecycle from create, build, test, deploy, observe, operate, secure, recover, and retire.
3. **Bake in defaults.** Include responsibility, SLO hooks, telemetry, safe deploys, secret handling, access boundaries, runbooks, recovery, dependency inventory, and secure settings. Each generated default should be a usable artifact, not a placeholder. Instantiate secure baselines via `infrastructure-and-policy-as-code` (landing-zone-style pre-provisioned guardrails) so the paved path ships hardened account, network, and identity defaults.
4. **Make start-right templates.** Bootstrap repositories, delivery, infrastructure, observability, security, and policy defaults together so projects do not assemble safety by hand.
5. **Register ownership as code.** Keep catalog records in a versioned source of truth with owner, lifecycle, system, API/dependency relationships, documentation, runbook, dashboard, and on-call links; avoid manually curated catalogs that drift from reality.
6. **Expose self-service with guardrails.** Make the path usable without bespoke platform intervention for normal cases while policy, security, cost, and operations controls stay automatic.
7. **Design scorecards.** Measure capability maturity across investment, adoption, controls, provisioning and management, interfaces, and feedback; use source records for meaningful capabilities, not vanity checkboxes.
8. **Handle exceptions.** Require user-confirmed reason, expiry, compensating control, and migration plan using the shared risk-register and compensating-control formats.
9. **Plan adoption.** Prioritize new services, high-risk services, and repeated incident classes; avoid big-bang migrations.
10. **Close feedback loops.** Use incidents, developer friction, and scorecard gaps to improve the platform.

## Synthesized Default

Build golden paths around capabilities rather than tools: service creation, build, test, release, telemetry, security, responsibility, recovery, controls, and records. Provide self-service with guardrails, start-right templates, and escape hatches, but make exceptions visible and temporary.



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

- Specialized services can deviate when golden-path assumptions do not fit, but the exception must preserve equivalent checks and operations standards.
- Early platform phases may cover a narrow service type first; state non-goals.
- Strict scorecards should start advisory until platform capabilities make compliance achievable.
- Existing services may need incremental migration instead of template replacement.

## Response Quality Bar

- Lead with the platform capability map, golden-path design, scorecard, migration plan, or exception workflow requested.
- Cover lifecycle defaults, service responsibility, build/test/release, telemetry, security, recovery, record hooks, self-service, exceptions, adoption, and feedback before optional platform breadth.
- Make recommendations actionable with templates, required defaults, scorecard checks, migration batches, operating model, and exception expiry where relevant.
- Name the details to inspect, such as current service inventory, onboarding steps, platform friction, incident gaps, template outputs, scorecard results, adoption metrics, and user-visible failure records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside platform engineering and golden paths. Route infrastructure policy, release engineering, or observability only when those specialist gaps block the platform decision.
- Be concise: avoid generic platform-product language and prefer compact capability maps, lifecycle defaults, and adoption tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Platform capability map.
- Golden-path lifecycle and template requirements.
- Required service defaults and records hooks.
- Readiness-defaults matrix showing which operational defaults are created, usable, and checked by the golden path.
- Service catalog and responsibility model.
- Source-controlled catalog metadata standard with owner, lifecycle, system/API/dependency relationships, and operational links.
- Capability scorecard with meaningful checks, adoption feedback, and exception workflow.
- Migration/adoption plan.
- Feedback and operations model.

## Checks Before Moving On

- `template_defaults`: golden path includes responsibility, SLO/telemetry, deploy/rollback, runbook, security, and secrets defaults.
- `readiness_defaults`: generated defaults for SLO, dashboard, alert/runbook, rollout, recovery, dependency inventory, and secure settings are usable, not placeholders.
- `self_service`: normal workflow can be completed without bespoke platform work.
- `catalog_truth`: catalog ownership, lifecycle, dependency, API, and operational records come from a maintained source of truth.
- `exception_model`: exceptions have user-confirmed reason, expiry, compensating control, and migration path using the shared risk-register and compensating-control formats.
- `adoption_plan`: target services, migration order, and operating model are stated.
- `feedback_loop`: incidents, friction, and scorecard gaps feed platform backlog.

## Red Flags - Stop And Rework

- Template creates code but no runbook, alerts, or rollout path.
- Platform mandates standards projects cannot satisfy with available tools.
- Scorecards reward fields existing instead of capabilities working.
- Catalog entries are manually curated and no one can tell whether owner, lifecycle, dependency, or runbook data is current.
- Exceptions are permanent.
- Golden path is a vendor product wrapper rather than an engineering workflow.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Building a portal first | Start with repeatable workflows and defaults. |
| Platform as a pile of tools | Run it as a product: users, value proposition, owner, and a cognitive-load measure. |
| No escape hatch | Allow exceptions with user-confirmed reason, expiry, and equivalent controls. |
| Platform as ticket queue | Prefer self-service for normal paths. |
| Measuring adoption only | Measure operational and security outcomes too. |
