---
name: observability-and-alerting
description: "Use when telemetry, dashboards, alert rules, or runbooks need design outside SLO or release-check policy"
---

# Observability And Alerting

## Iron Law

```
TELEMETRY STARTS FROM USER SYMPTOMS; URGENT ALERTS NEED USER IMPACT, URGENCY, ACTIONABILITY, AND A RUNBOOK
```

Telemetry that does not map to a user-visible symptom is decoration. An alert that lacks impact, urgency, actionability, or a runbook should not be urgent by default. The two halves are co-designed: signals exist so that someone can act on them, and urgent alerts fire only on signals that show user-felt impact.

## Overview

Produces telemetry requirements tied to user journeys, a dashboard specification that answers impact and recent change, and an alert policy where every urgent alert has user impact, urgency, actionability, and a runbook. Refuses host-health urgent alerts, anonymous alerts, and dashboards built from whatever the platform happened to emit.

**Core principle:** instrument user-visible symptoms first, then add enough causal context to debug without guessing.

## When To Use

- The user is designing, building, or revising metrics, logs, traces, dashboards, alerting, runbooks, correlation IDs, telemetry fields, or production debugging paths.
- A service cannot explain incidents from existing signals.
- The user asks how to instrument a new service, dependency, queue, pipeline, or rollout.
- Alert rules are the main deliverable and the work is not asking to connect them to SLO or error-budget policy.

## When Not To Use

- The user needs reliability targets, SLO math, SLO-based urgent/follow-up policy, or budget policy; use `slo-and-error-budgets` instead.
- The user needs to reduce existing urgent-alert volume or toil; use `oncall-health` instead unless new telemetry is central.
- The user is in a live incident; route to `incident-response-and-postmortems` first.
- The work is only local development logging without production operations impact.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Critical user journeys, SLOs, customer-criticality, and incident history.
- Request paths, dependency map, queues, data stores, batch jobs, and external integrations.
- Existing metrics, logs, traces, dashboards, alerts, runbooks, and known blind spots.
- Customer support escalations, status or support-tool dependencies, alternate communication paths, and signals that primary incident tooling is degraded.
- Telemetry pipeline: sources, source event-size and shape bounds, processors, redaction/sampling, routing, validation lookup cache and capacity, exporters or sinks, sink-config validation and isolation, queue/backpressure behavior, write or storage quotas, volume budgets, and drop policy.
- Dashboard purpose, first-screen health question, metric definitions, metric consumers such as alerts or automated control loops, missing-signal behavior, backfill or permanent-gap semantics, visual status rules, and alert-to-runbook links.
- Fault-domain labels needed for impact analysis, such as location, deployment unit, partition, shard, tenant, and deployment stage.
- Deployment markers, version identifiers, feature/config flags, tenant/customer context, and correlation identifiers.
- Security detection hypotheses from threat models, with required telemetry or audit data, effective enablement or coverage state, normalization or freshness lag, severity, owner, and response path.
- Privacy constraints, sensitive fields, retention requirements, and sampling limits.
- Responder workflow: where urgent alerts go, what local response path handles them, and how runbooks are used.
- Maintenance and suppression rules: muted signals, replacement coverage, owner, expiry, and the signal that still catches resource exhaustion or user impact during the window.

## Workflow

1. **Start with symptoms.** Define what users notice: failed requests, slow actions, stale data, dropped work, lost messages, or incorrect results.
2. **Add golden signals.** Capture latency, traffic, errors, and saturation for services; utilization, saturation, and errors for resources.
3. **Instrument dependencies.** Include call count, latency, errors, timeouts, retries, queue depth, queue age, and drain rate.
4. **Connect events.** Propagate trace context across every service boundary so the trace identifier is global to a request and span identifiers are local to each unit of work; attach deployment/change markers.
5. **Structure logs and events.** Require a baseline field set on every entry: UTC timestamp, severity, service identifier, trace identifier, request identifier, and message, plus stable fields for operation, tenant/customer context where safe, dependency, result, error class, and latency.
6. **Bound telemetry volume.** Give high-volume logs, traces, and generated events explicit volume budgets, cardinality limits, and quota-exhaustion behavior. Treat telemetry rollout changes like production changes when extra noise can hide, drop, or bill critical signals.
7. **Map threat detections when required.** For security detection work, connect each abuse case to a detection hypothesis, data component or audit event, signal expression, effective enablement check, freshness or normalization lag, owner, severity, and response route. Verify the backend coverage state after onboarding or configuration changes so a visible enabled setting cannot mask a disabled detector.
8. **Design telemetry pipelines.** Define where telemetry is received, transformed, sampled, redacted, queued, routed, and exported; state what happens under collector, validation-lookup, sink, quota, or backpressure failure. Validate source event size and shape, sink rules, and export rules before activation; bound validation reads with cache behavior, capacity budgets, and stale or missing configuration handling; isolate oversized or invalid source events and invalid sink state so one feed or destination cannot backlog unrelated telemetry streams.
9. **Define the health model.** State healthy, degraded, unavailable, and recovering conditions at component, dependency, journey, and workload levels; distinguish transient degradation from sustained unavailability.
10. **Design dashboards for questions.** Build the first view so impact is visible quickly, then drill down by scope, fault domain, recent changes, dependencies, saturation, and recovery progress. Every displayed metric needs unit, source, label semantics, threshold/window, downstream consumers, missing-data behavior, and whether gaps can be backfilled; color cannot be the only status signal.
11. **Make absent signals explicit.** Emit zero when zero is meaningful, and treat missing samples as a separate health state so silence cannot look healthy.
12. **Instrument operational channels.** Track whether status, support, escalation, and responder tools are healthy enough to detect and communicate impact; keep an alternate path when the primary path depends on the affected system.
13. **Guard suppression windows.** During maintenance, test, migration, or noisy rollout windows, state which alerts are muted, when muting expires, who owns it, and which replacement signal still catches resource exhaustion, stuck work, or user impact.
14. **Alert on symptoms.** Use SLO burn or direct user-impact alerts. Keep diagnostic and causal alerts as follow-ups unless urgent and actionable. Each alert rule should name the expression or symptom, window, labels, severity, owner, annotations, runbook, and expected noise behavior.
15. **Identify affected customers with privacy controls.** For customer-impacting services, define privacy-safe signals that support impact scoping and notification.
16. **Attach runbooks.** Every urgent alert needs triage steps, impact check, mitigation options, fallback path, and rollback/fallback links.

## Synthesized Default

Use SLO/user-journey symptoms, layered health models, golden signals, fault-domain labels, structured events, distributed context, deployment markers, and dependency signals as the default telemetry set. Use urgent alerts only when action is required now; use dashboards and follow-ups for investigation and slow-burn work.



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

- Early-stage services may begin with a minimal symptom dashboard and expand after real failure modes are known.
- Low-volume systems may need synthetic checks or heartbeat/freshness signals to detect user impact.
- Security and privacy constraints may require redaction, hashing, sampling, or separate audit trails.
- Some critical causal signals can trigger urgent alerts if they are tested leading indicators with a runbook.

## Response Quality Bar

- Lead with the dashboard spec, alert classification, telemetry gap, or runbook requirement requested.
- Cover user journeys, health states, golden signals, dependency context, deployment markers, privacy-safe events, urgent-alert policy, and runbooks before optional observability breadth.
- Make recommendations actionable with metric/log/trace names, thresholds, routes, runbook links, failure response, and rollout checks where relevant.
- Name the details to inspect, such as SLOs, metric sources, log fields, trace context, alert history, runbook content, deploy markers, and sensitive-data handling; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside observability and alerting. Route SLO definition, on-call policy, or incident response only when those are the central unresolved risk.
- Be concise: avoid generic telemetry lists and prefer compact journey-to-signal and alert-policy tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Telemetry requirements mapped to user journeys and dependencies.
- Dashboard specification for impact, scope, dependencies, saturation, and recent changes.
- Metric definition table covering unit, source, labels, threshold/window, owner path, missing-signal behavior, and backfill or permanent-gap semantics.
- Telemetry consumer table for alerts, autoscaling, automation, reports, and other control loops, including fail-safe behavior when data is missing or underreported.
- Fault-domain and affected-customer scoping signals where relevant.
- Alert policy with urgent/follow-up/diagnostic classification.
- Structured log/event field standard and sensitive-data handling.
- Telemetry volume and quota budget covering expected rate, burst behavior, cardinality limit, drop risk, and noise rollback.
- Maintenance suppression plan listing muted alerts, owner, expiry, replacement signal, and residual blind spot.
- Security detection mapping for threat-model-driven abuse cases when detection is in scope, including effective enablement or coverage check and data freshness or normalization lag.
- Telemetry pipeline map with source validation and isolation, processor, redaction/sampling, validation lookup cache and capacity, queue/backpressure, sink validation and isolation, sink, and drop behavior.
- Status, support, escalation, and responder-tool health signals plus alternate communication path.
- Trace or context propagation requirements.
- Alert-rule specification and runbook requirements for every urgent alert.
- Gaps and follow-up routes to SLO, on-call, incident, or platform work.

## Checks Before Moving On

- `symptom_first`: urgent alerts map to SLO burn or direct user-visible impact.
- `health_model`: component and dependency signals aggregate into critical-journey and workload health states.
- `causal_context`: telemetry includes dependency, correlation, version/change, and saturation context.
- `fault_domain_context`: telemetry can separate impact by location, deployment unit, partition, shard, tenant, or deployment stage where those domains exist.
- `dashboard_scan`: the first dashboard view shows user impact quickly and supports drill-down by scope, fault domain, dependency, change, and recovery state.
- `metric_definition`: user-facing metrics define unit, source, labels, threshold/window, and missing-signal behavior.
- `missing_signal_behavior`: missing samples and zero values are distinguishable where that difference changes health.
- `gap_semantics`: telemetry gaps state whether they can be backfilled, remain permanent, or require alternate evidence for audits, alerts, autoscaling, and incident review.
- `telemetry_consumers`: alerts, automation, reports, and control loops that consume each critical metric have missing or underreported data behavior.
- `telemetry_pipeline`: collection, source validation and isolation, processing, redaction/sampling, routing, validation lookup cache and capacity, sink validation and isolation, backpressure, and drop behavior are defined.
- `telemetry_volume_budget`: high-volume telemetry has rate, burst, cardinality, quota, and noise-rollback controls before rollout.
- `suppression_guard`: maintenance or noisy-change alert suppression names owner, expiry, replacement coverage, and residual blind spot.
- `operational_channel_health`: status, support, escalation, and responder tools have health signals and an alternate path when they depend on the affected system.
- `security_detection_map`: threat-driven detections connect abuse case, data source, signal, effective enablement or coverage check, freshness or normalization lag, owner, severity, and response route.
- `alert_rule_definition`: urgent alerts define expression or symptom, window, labels, severity, owner, annotations, runbook, and expected noise behavior.
- `runbook_link`: every urgent alert has a runbook with impact check, mitigation, fallback, and verification.
- `privacy_check`: sensitive data handling is defined for logs, traces, labels, and events.
- `debug_path`: dashboards answer impact, scope, cause candidates, recent changes, and recovery state.

## Red Flags - Stop And Rework

- Dashboards start from whatever the platform emits instead of user journeys.
- Every dependency error triggers an urgent alert even when retries hide user impact.
- Logs contain sensitive data or unbounded high-cardinality fields without controls.
- A telemetry change can emit enough logs, spans, or events to exhaust quota, drop unrelated signals, or create billing impact without a rollback or exclusion path.
- Alerts have no runbook or response path.
- Alert rules omit owner, window, labels, annotations, or expected noise behavior.
- Monitoring records abnormal behavior but no alert, escalation, or support signal reaches the owning team.
- Telemetry pipelines drop, sample, or backpressure data without an explicit impact on health signals.
- Metrics show averages only and hide tail latency or saturation.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Collecting everything | Collect signals that answer operational questions. |
| Urgent alerts on causes | Alert on symptoms; use causes for debugging. |
| Ignoring changes | Add deployment, config, and feature markers. |
| Logging prose | Use stable structured fields. |
