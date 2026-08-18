---
name: incident-response-and-postmortems
description: "Use when running active incidents, writing postmortems, or setting status cadence and action items"
---

# Incident Response And Postmortems

## Iron Law

```
NO INCIDENT WITHOUT ROLES, IMPACT, AND STATUS CADENCE; NO POSTMORTEM WITHOUT TIMELINE, CONTRIBUTING FACTORS, AND VERIFIED ACTIONS
```

The two halves are co-designed: live response is unsafe without named responders, declared impact, and a predictable next-update time; a postmortem that only names a root cause or a person has not explained the system. For a solo developer the responder roles collapse onto one person, but the role labels still have to be explicit so nothing falls between them.

## Overview

Produces incident roles and severity, a live timeline, a status-update cadence, a checkpoint packet for shift changes, and a blameless postmortem whose action items have due dates, and observable verification signals. Refuses "human error" as a conclusion and refuses action items that read "be more careful".

**Core principle:** coordinate clear roles, mitigate impact, preserve a timeline, communicate predictably, and convert learning into verified engineering improvements.

## When To Use

- The user asks for outage handling, incident command, severity, status updates, response roles, timelines, postmortems, or action items.
- A customer-impacting degradation, data issue, security event, or operational emergency is active or recently resolved.
- You need a blameless postmortem or follow-up tracker.
- An incident exposed gaps in alerts, runbooks, responsibility, deployment safety, or architecture standards.

## When Not To Use

- The work is pre-launch readiness with no incident; use `production-readiness-review` instead.
- The request is brand, PR, legal strategy, or customer-support policy beyond operational status communication.
- The user asks only to define telemetry; use `observability-and-alerting` instead.
- The user asks only to reduce alert fatigue; use `oncall-health` instead.

## Info To Gather

- Impact: affected users, journeys, severity, start/end times, data loss/corruption, and business-critical periods.
- Current state: active, mitigated, resolved, monitoring, or postmortem-only.
- Responders, roles, fallback path, user decision point, and communication channels.
- Available docs, dependency status, and user-provided contacts that can inform mitigation without blocking on an outside party.
- Timeline events: detection, triage, mitigation, customer communication, resolution, and recurrence.
- Mitigations attempted, signals observed, dashboards/logs/traces used, and changes during the window.
- Impact scoping by affected users or tenants, fault domain, dependency, and recent change markers.
- Contributing factors, missed signals, runbook gaps, responsibility gaps, and action-item candidates.

## Workflow

1. **During active impact, assign roles.** Use incident commander, operations lead, communications lead, and scribe when coordination requires them; for solo work, explicitly take each role yourself.
2. **Classify ticket severity.** Use impact radius and urgency: highest severity for widespread critical user or data/security impact, high severity for major but bounded customer impact, medium severity for limited degradation or internal dependency risk, and low severity for a low-impact anomaly requiring follow-up.
3. **Put live-site impact first.** Treat customer-visible availability, health, and security as the top priority until impact is controlled.
4. **Bound impact scope early.** Use user, tenant, fault-domain, dependency, and recent-change signals to bound impact safely.
5. **Mitigate before explaining.** Prefer actions that reduce user impact safely; postpone deep root-cause analysis until impact is controlled.
6. **Keep a safe live timeline.** Record timestamped facts, hypotheses, decisions, redacted action summaries, status updates, evidence links, and responsibility changes. Define need-to-know access, retention and disposal, integrity, and prohibited fields; never copy credentials, personal data, raw sensitive configuration, or unrestricted command output into the general timeline.
7. **Communicate predictably.** Derive status cadence from impact, uncertainty, mitigation rate, audience needs, and responder load. A severe fast-moving incident may need updates within tens of minutes, while a stable bounded incident may use a longer interval. Record the chosen cadence and next update time rather than treating 30 minutes or one hour as universal thresholds. Say what is known, unknown, impact, mitigation, and when the next update will occur.
8. **Change strategy when stuck.** Predeclare evidence-based stall triggers such as no impact improvement after a bounded interval, worsening guardrails, exhausted safe hypotheses, or unclear mitigation authority. Within existing authority, switch to a safer mitigation, narrower diagnostic path, or rollback when a trigger fires. Ask the user before expanding scope, risk, or authority, but do not turn every strategy change into a waiting point.
9. **Checkpoint explicitly.** At every incident-commander or shift change, record state, current hypothesis, customer impact, in-flight actions, user decision point, comms cadence, and next decision point.
10. **Use the normal hotfix path where possible.** Reduce context switching by keeping artifact, branch, change, and rollout mechanics traceable even under urgency.
11. **Run security incidents as a protected track.** When confidentiality, integrity, identity, abuse, or data exposure may be involved, preserve logs and artifacts, restrict sensitive details to need-to-know responders, and keep operational facts separate from legal conclusions.
12. **Stabilize and verify.** Confirm recovery with user-visible metrics and internal health.
13. **Write a blameless postmortem.** Explain every contributing factor supported by evidence across the relevant technical, operational, detection, change, or organizational layers. A simple incident may have one supported trigger and one missed defense; a complex incident may have many.
14. **Replace unsupported root-cause certainty.** If the user supplies "root cause: X", distinguish the observed trigger from contributing conditions and missed defenses. Add only factors supported by records; mark plausible but unproven explanations as hypotheses or unknowns, not as required layers.
15. **Create verified actions.** Every action needs due date, observable completion signal, and classification: prevent, detect, mitigate, or learn.
16. **Feed standards.** Turn recurring classes into SLO, observability, safe-change, HA, dependency-resilience, or platform-improvement work.

## Synthesized Default

Use role-based incident command during response and blameless, contributing-factor postmortems after recovery. Prefer mitigation and clear communication over premature diagnosis. Treat security incidents as record-sensitive operational events, keep engineering accountable for live-site outcomes, and treat action items as engineering commitments with verification, not aspirations.



## Exceptions

- Security, privacy, legal, or safety incidents may have confidentiality constraints; keep operating from verified facts and user-provided requirements.
- Very small internal incidents can use a lightweight postmortem if impact, timeline, and action tracking remain explicit.
- If an incident is ongoing, delay final postmortem conclusions and keep outputs focused on response.
- Customer-facing wording may need user confirmation, but operational status cadence and facts remain in scope.

## Response Quality Bar

- Lead with the incident command plan, current mitigation posture, timeline, postmortem finding, or action register requested.
- Cover impact, severity, roles, timeline, communications cadence, mitigation, contributing factors, missed defenses, and verified actions before optional incident mechanics.
- For postmortems, include a **Contributing Factors** section containing all evidence-supported triggers, conditions, and missed defenses. Mark unknowns and rejected hypotheses; do not invent a minimum number of factors or layers.
- Make recommendations actionable with user decision point, timestamps, next-update times, verification conditions, due dates, and follow-up checks where relevant.
- Name the details to inspect, such as alerts, dashboards, logs, deploy markers, chat timeline, customer-impact data, mitigation commands, and action verification; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside incident response and postmortems. Use security/privacy constraints or specialist reliability checks only when they are central to the next action.
- Be concise: avoid generic blameless-postmortem theory and prefer compact timelines, status updates, and action tables.
- Scale the artifact to incident state: during active impact, return roles, impact, mitigation, cadence, safe timeline, and next decision; add the full postmortem and action register after stabilization or when the user explicitly asks for them.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Incident role assignment and severity classification.
- Live or reconstructed timeline.
- Impact summary with detection, mitigation, and resolution times.
- Impact-scope table by user group or tenant, fault domain, dependency, and recent change marker where available.
- Communications cadence and status-update skeleton.
- Evidence-based strategy-change trigger, action allowed within current authority, and the condition that requires user confirmation because it expands scope or risk.
- Checkpoint packet for long incidents or responder changes.
- Postmortem with evidence-supported contributing factors, missed defenses, unknowns, and rejected hypotheses.
- Action-item register with due date, observable verification signal, and category.
- Follow-up engineering checks for the relevant skill surfaces.

## Checks Before Moving On

- `impact_check`: user impact, severity, start/end or current state, and affected journeys are stated.
- `impact_scoping`: affected users or tenants, fault domains, dependencies, and recent changes are scoped or marked unknown.
- `role_check`: response roles and user decision point are assigned or explicitly not needed.
- `timeline_check`: detection, triage, mitigation, communication, resolution, and key decisions are captured.
- `record_safety`: the timeline minimizes and redacts sensitive content, links to restricted evidence, and has access, retention and disposal, integrity, and prohibited-field rules.
- `checkpoint_check`: long incidents or role changes include state, in-flight actions, comms cadence, and next decision point.
- `blameless_check`: postmortem focuses on system factors and avoids person-blame or single-root-cause simplification.
- `action_check`: every action has due date, verification condition, and category.

## Red Flags - Stop And Rework

- The postmortem concludes "human error" without explaining system conditions.
- Timeline is reconstructed from memory with no timestamps or source records.
- Action items say "be more careful", "monitor better", or "improve tests" without verification.
- Status updates have no next-update time.
- Responders keep investigating without changing mitigation strategy when mitigation is stalled or authority is unclear.
- Mitigation is delayed because responders are debating root cause during active impact.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Root-cause hunting during impact | Mitigate first, analyze after stabilization. |
| One action per symptom | Group by contributing factor and defense gap. |
| Blameless means consequence-free | Focus accountability on system improvements and verified actions. |
| Postmortem as ritual | Feed findings into standards, platform, and reliability backlog. |
