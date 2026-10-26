---
name: postmortem
description: 'Explain why a change, incident or session went as it did, separating proven causes from coincidence. Use when: asked for a postmortem, retro or root-cause write-up.'
practices:
- sre
- lean-startup
hexagonal_role: domain
consumes: []
produces:
- postmortem-analysis
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  capabilities: [postmortem]
  effects: [write_requested_postmortem_report]
  canonical_status: canonical
  disposition: keep_strategy
  tier: judgment
  dependencies: []
output_contract: 'concise inline causal analysis; a requested durable report is YYYY-MM-DD-postmortem-<topic>.md in caller-selected protected external non-Git storage'
---

# Postmortem

Answer an explicit retrospective causal question about a completed or stopped
goal, session, change or incident from its actual intent, outcome and judgment evidence.
For an explicitly requested interim analysis, pin the cutoff and pending checks;
its conclusions describe that interval and do not establish a final outcome.
Neighbours: how a plan not yet run could fail is [Premortem](../premortem/SKILL.md);
whether a finished change meets acceptance is [Validate](../validate/SKILL.md).

## First check: correlation or cause?

Treat every causal statement as a hypothesis, including the one the caller
arrives with. Promoting a claim from correlation to cause requires all three:

- a stated mechanism: the specific path by which the condition produced the
  outcome, in terms a reader could check against the subject;
- discriminating evidence: an observation that the mechanism predicts and at
  least one plausible alternative does not;
- a counterfactual test: what should have differed if the claim were false,
  with cited evidence showing it did differ.

Post-hoc fix attribution, "we changed X and the failure stopped, therefore X
was the cause", satisfies none of these alone: the symptom may be intermittent,
or the recovery and the change may share an unobserved cause. Keep such claims
as correlations, name the alternatives still standing, and suggest the
discriminating experiment; a recommendation built on an unproven cause is
framed as that experiment, not as a supported change. Rejecting a claim needs
discriminating evidence too, or a prediction of the claim that the evidence
contradicts. Anything less stays a correlation or an unknown.

## Prompt

```text
Postmortem last Thursday's release: the deploy needed four attempts and two
rollbacks before it stuck. Using the deploy log, the CI runs and the incident
channel notes, which failures were avoidable and what caused each one?
Answer inline.
```

## Critical Constraints

- Postmortem is retrospective causal analysis, not the general learning umbrella
  or a code-acceptance gate: code judgment never waits on it, and Plan's
  [code plus a retrospective](../plan/references/resume-and-handoff.md) rule
  keeps the two separate when both are requested.
  Wait for a known outcome unless interim analysis was requested.
- It does not re-run acceptance validation, change existing verdicts or
  fabricate missing proof. An existing `verdict.v2` is optional evidence; its
  absence does not exclude a stopped or unvalidated subject.
- Because the caller owns subsequent action, do not rewrite proof, operate
  tracker state, change the remaining plan, reopen work or promote a rule.
- Empty or inconclusive analysis is valid; recommend no change when warranted.
  Manufacture neither certainty nor a lesson.

## Workflow

1. Pin the question, accepted intent, subject identity, actual outcome and
   available judgment with exact ids (commits, checks, messages, an existing
   verdict); keep missing evidence explicit. For an incident, intent is the
   expected service behaviour or SLO, judgment is the alerts and checks, and
   step 2 looks for the deploy, config change, upstream event or missing signal
   before the departure.
2. Rebuild only the timeline the claims depend on, keeping delivered behavior,
   failed or stopped work and process output distinct. For a correction or stop,
   locate the first observable departure from the accepted behavior and the
   instruction, tool result or missing input immediately before it. Compare a
   successful case under similar conditions when available; otherwise name that
   missing comparison. A pause required by the caller is expected behavior.
   Hidden author reasoning is not fact; missing judgment is not a PASS or a FAIL.
3. Put each causal claim through the first check above. Distinguish necessary
   validation and compatibility work from avoidable rework; repeated review
   alone proves no waste.
   If the inputs include an earlier postmortem of the same subject, account for
   its recommendations before issuing new ones: applied, partly applied,
   not applied, or unknown, with evidence from the supplied work since then.
   Preserve whether a change was authorized, held or never approved; missing
   evidence of application is not failed adoption. Report recurrence of the
   targeted failure only when observed. For repeated unapplied advice, name
   known obstacles or an unresolved question instead of simply repeating it.
   Nonapplication alone proves neither cause, blame nor that the advice helps.
4. For time or token claims, state source, interval, units, included and
   excluded actors, and uncertainty. Separate elapsed time, overlapping work and
   accounting scopes; never equate totals with waste, savings or money without
   supporting evidence.
5. Return the output below and stop; suggestions do not authorize implementation.

## Output Specification

- Default to concise inline Markdown, no mandatory report or worksheet:

  ```text
  Question: <the causal question>
  Inputs: <intent, outcome and evidence, with exact ids>; missing: <gaps>
  Timeline: <only the events the claims depend on>
  Claims:
  - <claim>: supported | correlation | rejected | unknown
    mechanism / discriminating evidence / counterfactual: <each, cited, or "none">
    alternatives still standing: <rivals the evidence cannot rule out>
  Accounting (if claimed): <source, interval, units, actors, uncertainty>
  Unknowns: <what would settle them>
  Earlier advice (if supplied): <recommendation> - applied | partly applied | not applied | unknown, <evidence>
  Changes (at most three, or "no change"): <change> - <its limit, or the experiment that tests it>
  ```

- Aim each change at what the next run will meet, usually the instruction,
  tool result or missing input found in step 2, not at re-fixing code that is
  already repaired. The kind of avoidable miss picks the lever:
  - Mechanical slip (wrong path, skipped command, forbidden call): a lint rule,
    test, hook or config guard. Read the repository's check commands, hooks and
    CI first; an existing check that did not run or could not fail is the
    change, not a duplicate. When no seam in the code can hold such a check, name
    [Architecture](../architecture/SKILL.md) as the follow-up, with that defect
    as its named pain.
  - Judgment miss: one proposed standard, runbook step or instruction line;
    writing it is separately authorized [Memory](../memory/SKILL.md) work.
  - Fact found slowly: one pointer where the search began. Fact out of reach:
    a way to expose it next time, such as a captured log or an alert; changing
    access needs caller authority.
- Only when requested, save `YYYY-MM-DD-postmortem-<topic>.md` in caller-selected
  protected external non-Git storage. Missing routing does not authorize a
  repository fallback; preserve existing requested evidence under owner policy.
- Curation, support and destination-disclosure review of any lesson are
  separately authorized [Memory](../memory/SKILL.md) work; retrospective
  evidence cannot promote itself.
