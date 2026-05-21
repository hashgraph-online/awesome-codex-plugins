---
name: oncall-health
description: "Use when pages, suppression rules, toil, runbook gaps, or recurring manual ops are hurting responders"
---

# Oncall Health And Toil Reduction

## Iron Law

```
NO RECURRING PAGE OR MANUAL RUNBOOK STEP WITHOUT A FIX PATH AND ELIMINATION PLAN
```

If the same alert or manual operation keeps recurring, the system is asking for engineering work.

## Overview

Repeated pages and manual operations are engineering defects.

**Core principle:** keep pages urgent and actionable, convert repeated manual work into durable fixes, and protect responders from avoidable operational load.

## When To Use

- The user is designing or revising paging alerts, toil, runbook, suppression, escalation, or manual-operation decisions that affect responder load.
- The user asks to reduce pages, alert fatigue, toil, manual operations, repeated runbook work, or operational burden.
- On-call responders are paged by non-urgent, unactionable, duplicate, or noisy alerts.
- Manual mitigations are repeated often enough to automate or remove.
- Runbooks are missing, stale, unsafe, or too vague to execute under pressure.

## When Not To Use

- The user asks about staffing, compensation, rotation fairness, headcount, or HR process; out of scope unless reframed as technical toil reduction.
- The main deliverable is new telemetry or alert construction; use `observability-and-alerting` instead.
- The main work is defining SLOs or paging thresholds from scratch; use `slo-and-error-budgets` instead.
- The request is generic developer productivity with no operational pain; out of scope for routed specialists.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Paging history: alert name, count, time, severity, duration, action taken, user impact, and fix path.
- Toil inventory: manual, repetitive, automatable, tactical, page-driven work.
- Runbooks, fallback paths, responsibility, checkpoint notes, and incident/postmortem actions.
- Alert-to-runbook reachability, runbook freshness, impact check, mitigation path, and verification step for paging alerts.
- Alert policy: paging versus non-paging response, SLO mapping, diagnostic alerts, dedupe, grouping, and suppression.
- Automation candidates, recurring incident classes, platform gaps, and unsafe manual steps.
- Responder load: after-hours pages, sleep-impacting pages, unresolved alerts, and checkpoint friction.

## Workflow

1. **Classify pages.** Mark each paging alert as urgent/actionable/user-visible/novel, non-paging, diagnostic, duplicate, stale, or false positive.
2. **Find top load sources.** Rank by page count, duration, user impact, recurrence, and manual effort.
3. **Separate symptom from cause.** Keep user-impact pages, but remove duplicate cause alerts unless they drive distinct action.
4. **Fix runbooks.** Every paging alert needs a reachable, current runbook with impact check, mitigation, fallback, rollback, and verification.
5. **Eliminate toil.** Automate, self-heal, remove, or redesign repeated manual operations; do not just document them better.
6. **Create an engineering backlog.** Give every recurring class a priority, expected page reduction, and verification metric.
7. **Protect the signal.** Use SLO burn, grouping, dedupe, maintenance windows, and non-paging routing to prevent alert erosion.
8. **Set a page-rate budget.** State a numeric per-shift or per-week page target and how it will be measured. Compare against current rate.
9. **Check runbook freshness.** For every paging alert, record runbook last-verified date and require freshness cadence alongside coverage.
10. **Refresh regularly.** Feed incident/postmortem findings back into alert rules, platform work, and reliability standards.

## Synthesized Default

Pages should be urgent, actionable, user-visible, and novel. Everything else should become a non-paging follow-up, automation, grouping, suppression, or removal. Toil reduction should produce engineering work with measured page or manual-effort reduction, and live-site responsibility should feed back into product engineering priorities.



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

- Some pre-user-impact alerts may page if they are tested leading indicators with a safe, immediate mitigation.
- Low-tier internal systems may route most operational signals to non-paging follow-up if user impact is limited and the user accepts the response latency.
- Temporary noisy alerts are allowed during a risky migration only with expiry, and cleanup task.
- Staffing and compensation questions remain out of scope unless translated into technical page/toil reduction.

## Response Quality Bar

- Lead with the page classification, toil inventory, alert-change decision, or automation backlog requested.
- Cover urgency, actionability, user visibility, novelty, runbook quality, repeated manual work, responsibility, and measurement before optional on-call breadth.
- Make recommendations actionable with page/follow-up/remove decisions, runbook fixes, automation tasks, expiry dates, and measured reduction targets where relevant.
- Name the details to inspect, such as alert history, pages per responder, after-hours volume, runbook links, toil hours, manual steps, suppression rules, and incident outcomes; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside technical on-call health and toil. Mark staffing, compensation, and HR questions out of scope unless translated into engineering controls.
- Be concise: avoid generic on-call advice and prefer compact page inventories and remediation backlogs.

## Required Outputs

- Paging-alert inventory and classification.
- Top toil sources with frequency, effort, and removal path.
- Alert changes: page/follow-up/remove/group/dedupe/suppress decisions.
- Runbook gap list and required updates.
- Automation or redesign backlog with expected page/manual-effort reduction.
- Responsibility and fallback fixes.
- Measurement plan for page volume, after-hours pages, and toil hours.
- Numeric page budget per shift or week with the measurement window and source.
- Runbook coverage AND freshness check (last-verified date, freshness cadence) for each paging alert.
- Alert-to-runbook path showing each paging alert reaches a current runbook with impact check, mitigation, and verification.

## Checks Before Moving On

- `paging_classification`: each paging alert is classified by urgency, actionability, user visibility, and novelty.
- `toil_inventory`: repeated manual work has frequency, and elimination or automation plan.
- `runbook_check`: remaining paging alerts link to executable runbooks with mitigation and verification.
- `alert_runbook_path`: each paging alert links to a reachable, current runbook with impact check, mitigation path, and verification step.
- `noise_reduction`: proposed changes state expected page or toil reduction and how it will be measured.
- `scope_check`: staffing, compensation, and HR issues are reframed or marked out of scope.
- `page_budget`: a numeric per-shift or per-week page target is stated with measurement window.
- `runbook_freshness`: each paging alert has a last-verified date and a freshness cadence.

## Red Flags - Stop And Rework

- The solution is "make the runbook longer" for repeated manual work.
- A paging alert has no action other than "look at dashboard".
- Responders routinely silence, ignore, or rerun alerts.
- Every cause alert pages alongside the symptom alert.
- Alert reduction removes the only user-impact signal.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating pages as inevitable | Treat avoidable pages as engineering defects. |
| Automating bad operations | Remove or redesign unsafe manual work when possible. |
| Deleting noisy alerts blindly | Preserve user-impact coverage and verify replacement signal. |
| Measuring only count | Track after-hours load, duration, recurrence, and toil hours. |
