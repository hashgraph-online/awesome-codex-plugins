---
name: sdlc-maintain
description: Monitor deployed code against project-root bands.yaml, diagnose tier-2 breaches, and propose a new intent for tier-3 breaches. Do NOT use to apply production fixes, merge or deploy code, replace incident ownership, or make unapproved risk decisions.
---

# SDLC Maintain

Run Stage 6 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Close the delivery loop through deterministic monitoring. Escalate a tier-3 breach
into a proposed new intent; never apply a production fix yourself.

Use the project's bands as the control policy. Do not substitute subjective
thresholds for the declared configuration.

## Entry gate

Proceed only when the relevant code is deployed and `bands.yaml` exists at the
project root.

If deployment has not occurred, wait for the human-approved deployment path.

If `bands.yaml` is missing, report the missing control configuration and stop.

## Required configuration

The project uses this contract template for `bands.yaml`:

```yaml
metric: [metric_name]
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose, tools: "[tool list]" }
  3sigma: { action: propose, routes: [pull_request, runbook:X] }
```

Read the actual file rather than assuming a metric, baseline, rule, tool, or
route from this example.

## Procedure

1. Read `bands.yaml` in full.
2. Identify the monitored metric, baseline, rules, tiers, actions, and configured
   diagnosis tools.
3. Query the appropriate monitoring source for current and relevant historical
   data.
4. Evaluate the observed data against the declared bands.
5. Apply Western Electric rules when `bands.yaml` specifies them.
6. Record the data queried, evaluation time, and resulting tier.
7. On a tier-1 breach, log the breach and evidence.
8. On a tier-2 breach, diagnose using only the tools listed in `bands.yaml`.
9. Record diagnostic evidence, hypotheses, and unresolved uncertainty.
10. On a tier-3 breach, write a new proposed fix intent and stop.
11. On a tier-3 breach whose evidence points at a specific merged change, also
    write a proposed reviewer eval case, as described below.

Do not silently change the baseline, tier definitions, or alerting configuration.

If monitoring access is unavailable, report the specific unavailable source and
do not claim that a band is healthy.

## Tier actions

For a tier-1 breach, log it according to the configured action. Do not turn a
routine log event into an unapproved production change.

For a tier-2 breach, diagnose with the configured tool list. Keep diagnosis
separate from remediation and record what the evidence does and does not prove.

For a tier-3 breach, create `.sdlc/<slug>-fix/intent.md` as a new proposal. Base
the content on observed monitoring evidence, not on a guessed root cause.

Route this new intent to `sdlc-plan` so the normal human interview and approval
gate starts the loop again.

## Tier-3 proposed intent

Use the normal Stage 1 intent structure for the new fix proposal.

State the breach and evidence in **Problem**. Describe the desired restored or
improved behaviour in **Proposed outcome**.

List affected users and systems, operational constraints, and all unresolved root
cause questions explicitly.

The proposal is not authorization to change production.

## Proposed reviewer eval case

A breach that traces to a merged change is a defect the review passes did not
catch. Record it where it can be used to test the reviewer, or the same class
escapes again.

Write `.sdlc/evals/reviewer/proposed/<slug>.md` with: the change and its commit
SHA, the file and line holding the defect, the bug class in one phrase, the
observed production evidence, and the fix once it exists. The case passes when the
reviewer, run against that change, reports that file and that bug class at
`Important`.

Do not write a case when the evidence does not identify a specific change. A guess
in the eval set makes every later reviewer score meaningless.

Do not promote the case yourself. A person moves it to `confirmed/` after agreeing
the defect is real; only `confirmed/` cases gate anything. Writing a proposal is
not confirming a root cause.

## Scheduled responsibilities

Run vulnerability scanning periodically according to the project's configured
schedule and tools.

Handle incident-response signals from Slack or Teams through Claude Tag when that
integration is configured.

Treat scheduled scans and incident signals as evidence sources; follow the same
band evaluation and tier action rules.

Do not invent schedules, integrations, alert routes, or runbooks that the project
has not configured.

## Prohibitions

Never apply a production fix yourself.

Never merge or deploy a remediation.

Never bypass human triage by converting a tier-3 proposal directly into code.

Never state a root cause as fact without evidence.

## Exit gate and handoff

On a tier-3 breach, write the proposed `.sdlc/<slug>-fix/intent.md` and stop.

Human triage decides whether the intent enters the delivery loop.

Hand off the new intent to `sdlc-plan`; do not proceed to design or build it.

For tier-1 and tier-2 events, retain the log or diagnosis evidence and continue
monitoring according to the configured schedule.
