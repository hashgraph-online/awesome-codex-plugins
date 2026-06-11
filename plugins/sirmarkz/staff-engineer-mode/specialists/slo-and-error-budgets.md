---
name: slo-and-error-budgets
description: "Use when user journeys need SLIs, SLOs, error budgets, burn-rate alerts, urgent-vs-follow-up alerts, or budget rules"
---

# SLO Error Budget Engineering

## Iron Law

```
NO SLO WITHOUT A USER JOURNEY, ERROR-BUDGET MATH, AND BUDGET RESPONSE RULES
```

If the journey, window, target, budget, and budget response are missing, do not call the SLO complete. The response says when to send an urgent alert, when to create a follow-up, when to slow releases, who can override, and what reliability work comes next.

## Overview

Produces an SLI/SLO table tied to named user journeys, an error-budget calculation, multi-window burn-rate alert rules, and budget-state release rules. Refuses 100-percent targets, host-health proxies, and urgent alerts that do not name a user.

**Core principle:** define the experience users are promised, measure it with SLIs, set an SLO that leaves an explicit error budget, and let that budget govern alert urgency and release risk.

## When To Use

- The user asks what reliability target, availability target, latency target, freshness target, correctness target, or durability target a service should meet.
- The user asks which alerts need urgent response, how burn-rate alerts should work, or how to connect alerts to SLOs.
- A launch, PRR, impact increase, or reliability decision needs SLI/SLO details.
- Existing alerts are noisy because they monitor causes instead of user-visible symptoms.

## When Not To Use

- The user only asks to build dashboards, traces, or logging without a user-visible objective; use `observability-and-alerting` instead.
- The user asks to reduce existing urgent-alert volume or on-call fatigue; use `oncall-health` instead unless new SLO policy is the main work.
- The user asks for cost optimization without reliability targets; use `cost-aware-reliability` instead.
- A live outage is underway; route to `incident-response-and-postmortems` first.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Critical user journeys, API operations, tenants, customer segments, and response paths.
- Candidate SLIs mapped from the four golden signals (latency, traffic, errors, saturation) for availability, latency, freshness, correctness, durability, and data loss.
- Current metrics, logs, traces, dashboards, alerts, and incident history.
- Missing-metric behavior, low-traffic detection strategy, and any synthetic or heartbeat signal needed to see user impact when organic traffic is sparse.
- Traffic shape: request volume, batch cadence, peak/seasonal behavior, and dependency fanout.
- External commitments or contractual SLAs, support commitments, business-critical periods, and known customer commitments.
- Release process: canary checks, freeze rules, rollback authority, and reliability-work intake.

## Workflow

1. **Name the user journey.** Write the journey in user terms: "checkout succeeds", "message is delivered", "dataset is fresh", not "instances are healthy".
2. **Choose the SLI.** Prefer direct measures of good events over proxy infrastructure health. If direct measurement is missing, mark telemetry work as a blocker or explicit proxy risk; missing samples are unknown or bad, never green by default.
3. **Define good and bad events.** Specify numerator, denominator, exclusion rules, sampling source, and data-retention limits.
4. **Model health states.** Define healthy, degraded, unavailable, and recovering for the journey so partial failures and degraded quality do not disappear inside raw uptime.
5. **Set the SLO target and window.** Pick a target users need and the system can plausibly meet. Keep internal thresholds tighter than external customer commitments when they exist. Include availability, latency, freshness, recovery, or correctness targets only when they match the journey. Avoid 100 percent unless failure is impossible by construction.
6. **Calculate the budget.** Convert target and window into allowed bad events or bad minutes. Include low-traffic math so one event does not create nonsensical burn.
7. **Design alerts from burn.** Separate urgent burn alerts from follow-up-only budget responses. Alert urgently only when a short-window and a longer-window burn both show near-term exhaustion risk for a user journey, such as fast burn over minutes plus sustained burn over roughly an hour. Create follow-up-only budget responses when multi-hour or multi-day burn threatens the window but does not require immediate action, or when diagnostic non-urgent signals explain likely causes without direct user-visible exhaustion. Recompute thresholds for low traffic; use synthetic or heartbeat signals when real traffic cannot detect failure quickly enough. Configure multi-window, multi-burn-rate alerts with concrete tiers: alert urgently when both a short window (~1h) and a confirmation window (~5m) show a high burn rate (for a 30-day window, roughly a 14.4x burn consuming ~2% of budget in 1h), and raise a slower follow-up alert for ~6h or multi-day burn that threatens the window without immediate action.
8. **Handle latency correctly.** State where latency is measured and how percentiles are aggregated. Do not average percentiles across services or windows; merge compatible distributions or measure at the user-journey boundary.
9. **Define budget responses.** State what happens when budget is healthy, threatened, exhausted, or repeatedly exhausted: urgent alert, follow-up, slow release, override, or prioritize reliability work.
10. **Route gaps.** Missing telemetry goes to observability; staged rollout rules go to progressive delivery; launch aggregation goes to PRR.

## Synthesized Default

Use the standard SRE sequence as the default: user journey -> health model -> SLI -> SLO -> error budget -> multi-window burn-rate alert -> release and reliability rules. Treat reliability targets as design inputs and error budgets as a guardrail on change velocity rather than as a reason to stop delivery permanently.



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

- Internal tools may use advisory SLOs, follow-up alerts, and longer windows when urgent alerts would not protect users.
- External SLAs may force stricter internal SLOs; state both and keep the engineering SLO tighter than the contractual breach point.
- Low-volume services may need event-count thresholds or synthetic checks so one failed request does not create misleading burn.
- Diagnostic cause alerts can trigger urgent response only when they are urgent, actionable, and reliably precede user-visible impact.
- Planned maintenance, deliberate shedding, or abusive traffic may be excluded only with enumerable, time-bounded, and auditable rules.

## Response Quality Bar

- Lead with the SLO table, alert rules, budget-state decision, or telemetry blocker requested.
- Cover user journeys, SLIs, health states, target/window math, burn alerts, dashboards, release rules, and observability gaps before optional SRE breadth.
- Make recommendations actionable with metric definitions, thresholds, windows, alert routes, budget consequences, and follow-up checks where relevant.
- Name the details to inspect, such as request/event sources, numerator/denominator definitions, traffic volume, deployment markers, current burn, urgent-alert history, and dashboard links; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside SLO and error-budget engineering. Route rollout policy, observability instrumentation, or PRR only when they are the central unresolved risk.
- Be concise: avoid generic SRE exposition and prefer compact SLI/SLO and burn-policy tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Critical journey inventory with impact and response path.
- SLI/SLO table with target, window, source metric, numerator, denominator, and exclusions.
- Health-state definitions for healthy, degraded, unavailable, and recovering conditions where partial degradation matters.
- Error-budget calculation in bad events or bad minutes.
- Burn-rate alert rules that separate urgent burn alerts from follow-up-only budget responses, including windows, budget-consumption rate, low-traffic handling, and diagnostic non-urgent rules.
- Missing-data policy for each SLI, plus synthetic or heartbeat detection for low-traffic journeys where needed.
- Dashboard requirements that show SLO state, burn, traffic, fault-domain scope where relevant, and recent deployments.
- Budget-state release rules and reliability-work triggers.
- Assumptions, proxy risks, blockers, and follow-up routes.

## Checks Before Moving On

- `journey_coverage`: every externally committed or explicitly user-critical journey has a SLI and user-visible success definition.
- `health_state`: the SLO can distinguish successful, degraded, unavailable, and excluded events where users experience partial failure.
- `math_check`: every SLO has a target, window, denominator, allowed bad events or minutes, and low-traffic handling.
- `promise_margin`: internal alert or stop thresholds are stricter than external commitments where such commitments exist.
- `missing_data_policy`: missing SLI samples have an explicit health meaning and response.
- `low_traffic_detection`: low-volume journeys use event-count math, synthetic checks, heartbeat signals, or a documented proxy risk.
- `alert_mapping`: every urgent alert maps to SLO burn or has a documented urgent/actionable exception; slow burn and diagnostic non-urgent signals become follow-up-only budget responses.
- `budget_response`: exhausted-budget behavior is stated, including who can allow releases and what work is prioritized.
- `telemetry_check`: every SLI names its metric/log/event source or marks observability work as a blocker.

## Red Flags - Stop And Rework

- The SLI measures CPU, memory, instance health, queue depth, or host availability without connecting to user success.
- The SLO target is 100 percent because "this must never fail".
- Burn-rate thresholds are copied from another service without traffic-window math.
- The response recommends urgent alerts for every cause alert.
- The budget response says "improve reliability" without release, review, user-decision, or work-intake consequences.
- Latency SLOs average percentile values instead of measuring the journey or merging compatible distributions.
- Journey SLOs are synthesized from component SLOs without an explicit dependency model.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Starting with dashboards | Start with journeys, then metrics. |
| Ad-hoc SLI selection | Start from the four golden signals, then pick journey-direct measures. |
| Treating SLA and SLO as synonyms | SLA is external promise; SLO is engineering target; SLI is measurement. |
| Making all alerts urgent alerts | Alert urgently on budget burn; create follow-ups for slow or diagnostic signals. |
| Hiding missing telemetry | Mark telemetry as a blocker or proxy risk. |
