---
name: progressive-delivery
description: "Use when config, schema, data, or non-API client changes need staged rollout, canary metrics, or rollback plans"
---

# Progressive Delivery And Safe Change

## Iron Law

```
NO PRODUCTION CHANGE WITHOUT A BLAST RADIUS, STOP CRITERIA, AND RECOVERY PATH
```

If the rollout cannot be stopped or reversed when rollout signals degrade, it is not safe delivery.

Operational canary metrics, SLO symptoms, and stop thresholds are part of progressive delivery. Do not read another specialist for those details unless the user explicitly asks for a separate causal experiment, readout, reliability-objective, or alerting artifact.

## Overview

Produces a staged rollout plan with named blast radius per stage, predeclared canary metrics with baseline and observation windows, stop and rollback criteria, and cleanup responsibility for every temporary flag or compatibility path. Refuses rollouts whose rollback only reverts code while config, schema, data, or clients stay forward.

**Core principle:** treat code, configuration, flags, schemas, data, infrastructure, and model artifacts as production changes with the same blast-radius discipline.

## When To Use

- The user asks how to roll out, rollback, canary, phase, stage, check, migrate, or release a change.
- A change involves configuration, feature flags, schema/data migration, dependency update, model change, infrastructure change, or client-visible behavior.
- The user asks how to reduce production risk from deployments or release trains.
- PRR or launch readiness needs rollout, rollback, and canary details.

## When Not To Use

- A live incident needs immediate command and mitigation; route to `incident-response-and-postmortems` first.
- The question is only code review or merge checks; use `agent-pr-review` for a concrete diff or `testing-and-quality-gates` for blocking checks.
- The question is build systems, release branches, packaging, or reproducible artifacts; use `release-build-reproducibility` instead.
- The main risk is database lock/backfill execution; use `database-operations` instead for that detail and use this skill for rollout sequencing.
- The question is causal experiment design/readout, sample-ratio mismatch, exposure logging, or metric validity beyond rollout health; ordinary canary metrics, stop criteria, and rollout guardrails stay here.
- The request is product launch messaging or marketing; out of scope.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Change type, responsible change path, affected users, blast radius, declared impact, and reversibility.
- Artifact identity and promotion path from build to environments.
- Production-like preflight stage coverage and whether exposure control is separate from deployment.
- Rollout unit: instance, ring, cohort, partition, deployment unit, location, tenant, percentage, device group, or internal-only group.
- Canary metrics: SLO symptoms, errors, latency, saturation, correctness, business invariants, and guardrail signals.
- Rollback or forward-fix path for code, config, flags, schema, data, and clients.
- Generated state, cached routing, queued work, active sessions or workflows, client-held tokens, last-known-good snapshots, and cleanup steps that may outlive code rollback.
- Promotion behavior during rollback or incident response: paused stages, disabled automatic rollout queues, selected rollback artifact, and re-enable conditions.
- Feature-flag lifecycle, config validation, migration steps, cleanup responsibility, and expiry.
- Observability markers, dashboards, alerts, incident path, and communication expectations.

## Workflow

1. **Classify the change.** Separate code, config, flag, schema, data, infrastructure, dependency, model, and client components; each can fail differently.
2. **Bound the blast radius.** Pick the smallest rollout unit that still gives signal. State who or what can be affected at each stage, and avoid stages that can damage multiple independent locations, partitions, or deployment units at once.
3. **Promote one artifact.** Build once and promote the same artifact or immutable change set through stages.
4. **Define compatibility.** Ensure old and new versions can coexist across clients, services, data, and messages during rollout.
5. **Stage stateful changes.** Keep reader/writer compatibility across at least one-version skew; use expand/contract, dual-read/dual-write, delayed cleanup, and explicit schema/data ordering when state is involved.
6. **Choose canary checks.** Select metrics before release from the deploy workflow and metric-definition files when they exist. Include user-visible symptoms, correctness, and internal health. Scope each metric to the canary slice itself; fleet-aggregate metrics dilute the signal into the size of the unchanged deployment, so canary regression vanishes long before it crosses a fleet-wide threshold. Each check needs a baseline window, minimum observation window, bake time, and enough exposed traffic or an alternate signal such as synthetic probes, extended bake time, or manual verification. For the small first rollout, stop if any scoped canary metric breaches its predeclared threshold, the deploy workflow health gate fails, telemetry quality is suspect, the minimum signal is not reached in the observation window, rollback cannot start immediately, or the affected artifact and rollout unit cannot be identified.
7. **Check each exposure step.** Exercise the changed path in a production-like preflight stage, including interaction with concurrent canaries/config changes and restart or recovery under representative load when the change affects efficiency, capacity, or startup behavior. Then start with a tiny production slice when the service supports it and move through rings, cohorts, partitions, stamps, deployment units, or locations after health signals say the previous step is safe. Preserve the declared surge and failover headroom at every step. For ordinary stateless serving deployments with no better capacity model, replacing no more than one-third of serving capacity at once is a useful starting guardrail; stateful, batch, client, tiny-fleet, or non-serving changes need their own safety threshold.
8. **Set stop rules.** Define thresholds, who can halt, and how rollback works. Stop signals should fire before the tighter internal SLO alert thresholds are crossed.
9. **Classify rollback and promotion control.** Pre-classify rollback safety per change: it is safe when the change is stateless, flag-gated, additive, or a new deploy has minimal state divergence; it is dangerous when a schema migration has run, a data format changed and new data is being written, external clients depend on the new contract, a stateful workflow is in flight, or a cache holds data in the new format. Choose forward-fix when rollback would cause more damage than the current impact, the fix is small with a short deploy path, or impact is confined to an isolatable subset. When rolling back a subset, pause promotion into and out of affected rollout units until the fix or risk decision is clear. Disable automatic rollout queues while responders are mitigating an active production issue, and require an explicit re-enable decision after the queued work is inspected. Select the rollback artifact from the point where the harmful change entered; the previous release may not be enough. Include cleanup or repair for generated config, cached routes, queued work, active sessions or workflows, client-held tokens, and last-known-good snapshots before considering rollback complete. Verify both new traffic and in-flight sessions, because rollback may fix new work while old sessions remain stuck.
10. **Handle forward-fix-only surfaces.** If rollback is structurally impossible, require a server-side kill switch or disable path, staged adoption metric, hotfix lane, and explicit user confirmation before first exposure.
11. **Handle non-code changes as first class.** Validate config, stage flags, throttle migrations, and delay destructive cleanup.
12. **Keep emergency flow familiar.** Hotfixes may move faster, but should use the same artifact identity, health checks, and traceable branch/change workflow where practical.
13. **Close the loop.** Record rollout results, remove temporary flags/paths, and update standards if the rollout found a new class of risk.

## Synthesized Default

Use build-once promotion, progressive exposure, predeclared health and canary metrics, automated or explicit stop criteria, reversible changes, and cleanup responsibility. Prefer small production slices, bake time, and independent fault-domain waves over parallel broad exposure. Prefer compatibility and expand/contract patterns over big-bang cutovers. Treat deploy, exposure, and customer-visible release as separate control points.



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

- Emergency fixes may use a narrower or faster rollout when waiting is riskier than release, but stop criteria and rollback checks still apply.
- Some destructive data changes cannot be rolled back; they require backup/restore test results, delayed cleanup, and forward-fix criteria.
- Low-risk internal changes may use lighter checks if blast radius and user risk acceptance using the shared risk-acceptance lifecycle are explicit.
- Client releases with slow adoption may require forward-fix and kill-switch strategy rather than true rollback.
- Temporary experiment flags should expire within about 90 days by default; long-lived operational kill switches need a renewal cadence and removal or renewal decision.

## Response Quality Bar

- Lead with the rollout plan, halt criteria, rollback path, or exposure decision requested.
- Cover blast radius, artifact identity, canary metrics, compatibility, feature/config lifecycle, migration safety, and cleanup before optional delivery topics.
- Make recommendations actionable with stage thresholds, windows, stop criteria, rollback or forward-fix actions, and cleanup expiry where relevant.
- Name the details to inspect, such as artifact IDs, deploy markers, canary baselines, SLO/error signals, migration checks, rollback checks, and flag inventory; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Do not load adjacent metric, experiment, or SLO guidance just because canary metrics or SLO symptoms are mentioned; use those only when the user asks for a separate causal readout, reliability-objective, or alerting artifact.
- Stay inside progressive exposure and safe change. Route build reproducibility, API compatibility, or data migration depth only when they materially block rollout safety.
- Be concise: avoid generic CD background and prefer compact rollout, metric, and rollback tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Rollout plan with stages, blast radius, responsible change path, and schedule.
- Preflight and first-slice checks for the changed path, with the rollout unit and stop signal for each step.
- Canary metric set with thresholds, baseline window, observation window, minimum signal, and expected behavior.
- Stop, rollback, mitigation, and forward-fix criteria, including first-slice minimum signal, thresholds, owner, abort action, and rollback-target selection when a latent harmful change is possible.
- Abort cleanup plan for generated state, cached routes, queued work, active sessions or workflows, client-held tokens, last-known-good snapshots, and promotion blockers.
- Promotion pause and re-enable criteria for rollback, partial rollback, and incident-mode automatic rollout queues.
- Compatibility plan for old/new code, clients, data, messages, config, and stateful reader/writer skew.
- Feature flag/config lifecycle plan with expiry and removal condition.
- Migration and cleanup plan for temporary paths or data structures.
- Verification commands or check links for each check.

## Checks Before Moving On

- `blast_radius`: every rollout stage names affected users/systems and maximum impact.
- `artifact_identity`: the release identifies the artifact/change set and promotion path.
- `canary_criteria`: canary metrics, thresholds, windows, and stop rules are defined before rollout.
- `fault_domain_sequence`: customer-impacting exposure moves through bounded instance, cohort, partition, deployment-unit, or location waves rather than parallel broad deployment.
- `preflight_parity`: the changed path is exercised in a production-like preflight stage or the gap is explicit.
- `small_slice_first`: production exposure starts with a small slice unless the risk decision explains why not.
- `auto_stop_signal`: stop or rollback signals are tied to user-visible health and stricter internal thresholds.
- `rollback_path`: rollback or forward-fix path and rollback-target artifact are pre-classified per change type, tested, rehearsed, or explicitly exempted with user confirmation.
- `abort_cleanup`: rollback or halt repairs generated state, queues, caches, active sessions or workflows, client-held artifacts, and last-known-good snapshots that can reintroduce the bad change.
- `promotion_control`: rollback or partial rollback prevents the rejected artifact from being reintroduced before re-enable criteria are met.
- `incident_mode_gate`: automatic rollout queues are paused during active mitigation and inspected before promotion resumes.
- `cleanup_responsibility`: temporary flags, configs, compatibility paths, and migration leftovers have cleanup action and expiry.

## Red Flags - Stop And Rework

- Rollback means "revert the PR" while config, data, schema, or clients are not reversible.
- Rollback leaves promotion running, so the bad artifact can be redeployed into the affected slice.
- Rollback reverts deployable artifacts while polluted generated state, queues, caches, or client-held artifacts keep causing impact.
- Rollback target defaults to the immediately previous release without checking when the harmful change entered.
- Canary metrics are picked after the rollout begins.
- One rollout stage can affect multiple independent fault domains before prior stages bake.
- Feature flags have no removal plan.
- Configuration changes bypass validation or staged rollout.
- Destructive cleanup happens in the same step as first exposure.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating deploy and release as the same thing | Deploy safely first; expose behavior progressively. |
| Only measuring service health | Include user symptoms and correctness invariants. |
| Ignoring config | Validate, stage, and roll back config as carefully as code. |
| Forgetting cleanup | Track temporary flags and compatibility paths to removal. |
