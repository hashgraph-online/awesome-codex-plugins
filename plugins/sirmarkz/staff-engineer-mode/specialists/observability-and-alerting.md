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
- Critical user journeys, SLOs, service tier, and incident history.
- Request paths, dependency map, queues, data stores, batch jobs, and external integrations.
- Existing metrics, logs, traces, dashboards, alerts, runbooks, and known blind spots.
- Telemetry pipeline: sources, processors, redaction/sampling, routing, exporters or sinks, queue/backpressure behavior, and drop policy.
- Dashboard purpose, first-screen health question, metric definitions, missing-signal behavior, visual status rules, and alert-to-runbook links.
- Fault-domain labels needed for impact analysis, such as location, deployment unit, partition, shard, tenant, and deployment stage.
- Deployment markers, version identifiers, feature/config flags, tenant/customer context, and correlation identifiers.
- Privacy constraints, sensitive fields, retention requirements, and sampling limits.
- Responder workflow: where urgent alerts go, what local response path handles them, and how runbooks are used.

## Workflow

1. **Start with symptoms.** Define what users notice: failed requests, slow actions, stale data, dropped work, lost messages, or incorrect results.
2. **Add golden signals.** Capture latency, traffic, errors, and saturation for services; utilization, saturation, and errors for resources.
3. **Instrument dependencies.** Include call count, latency, errors, timeouts, retries, queue depth, queue age, and drain rate.
4. **Connect events.** Propagate trace context across every service boundary so the trace identifier is global to a request and span identifiers are local to each unit of work; attach deployment/change markers.
5. **Structure logs and events.** Require a baseline field set on every entry — UTC timestamp, severity, service identifier, trace identifier, request identifier, and message — plus stable fields for operation, tenant/customer context where safe, dependency, result, error class, and latency.
6. **Design telemetry pipelines.** Define where telemetry is received, transformed, sampled, redacted, queued, routed, and exported; state what happens under collector, sink, quota, or backpressure failure.
7. **Define the health model.** State healthy, degraded, unavailable, and recovering conditions at component, dependency, journey, and workload levels; distinguish transient degradation from sustained unavailability.
8. **Design dashboards for questions.** Build the first view so impact is visible quickly, then drill down by scope, fault domain, recent changes, dependencies, saturation, and recovery progress. Every displayed metric needs unit, source, label semantics, threshold/window, and missing-data behavior; color cannot be the only status signal.
9. **Make absent signals explicit.** Emit zero when zero is meaningful, and treat missing samples as a separate health state instead of letting silence look healthy.
10. **Alert on symptoms.** Use SLO burn or direct user-impact alerts. Keep diagnostic and causal alerts as follow-ups unless urgent and actionable. Each alert rule should name the expression or symptom, window, labels, severity, owner, annotations, runbook, and expected noise behavior.
11. **Identify affected customers safely.** For customer-impacting services, define privacy-safe signals that support impact scoping and notification.
12. **Attach runbooks.** Every urgent alert needs triage steps, impact check, mitigation options, fallback path, and rollback/fallback links.

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

- Telemetry requirements mapped to user journeys and dependencies.
- Dashboard specification for impact, scope, dependencies, saturation, and recent changes.
- Metric definition table covering unit, source, labels, threshold/window, owner path, and missing-signal behavior.
- Fault-domain and affected-customer scoping signals where relevant.
- Alert policy with urgent/follow-up/diagnostic classification.
- Structured log/event field standard and sensitive-data handling.
- Telemetry pipeline map with source, processor, redaction/sampling, queue/backpressure, sink, and drop behavior.
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
- `telemetry_pipeline`: collection, processing, redaction/sampling, routing, sink, backpressure, and drop behavior are defined.
- `alert_rule_definition`: urgent alerts define expression or symptom, window, labels, severity, owner, annotations, runbook, and expected noise behavior.
- `runbook_link`: every urgent alert has a runbook with impact check, mitigation, fallback, and verification.
- `privacy_check`: sensitive data handling is defined for logs, traces, labels, and events.
- `debug_path`: dashboards answer impact, scope, cause candidates, recent changes, and recovery state.

## Red Flags - Stop And Rework

- Dashboards start from whatever the platform emits instead of user journeys.
- Every dependency error triggers an urgent alert even when retries hide user impact.
- Logs contain sensitive data or unbounded high-cardinality fields without controls.
- Alerts have no runbook or response path.
- Alert rules omit owner, window, labels, annotations, or expected noise behavior.
- Telemetry pipelines drop, sample, or backpressure data without an explicit impact on health signals.
- Metrics show averages only and hide tail latency or saturation.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Collecting everything | Collect signals that answer operational questions. |
| Urgent alerts on causes | Alert on symptoms; use causes for debugging. |
| Ignoring changes | Add deployment, config, and feature markers. |
| Logging prose | Use stable structured fields. |
