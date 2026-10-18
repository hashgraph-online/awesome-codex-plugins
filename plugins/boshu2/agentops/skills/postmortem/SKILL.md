---
name: postmortem
description: 'Explain why a change, incident or session went as it did, separating proven causes from coincidence. Use when: a postmortem or retro is selected by name.'
practices:
- sre
- lean-startup
hexagonal_role: domain
consumes: []
produces:
- postmortem-report.md
context_rel: []
skill_api_version: 1
user-invocable: true
disable-model-invocation: true
metadata:
  capabilities: [postmortem]
  effects: [write_postmortem_report]
  canonical_status: canonical
  disposition: keep_strategy
  tier: judgment
  dependencies: []
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
output_contract: 'concise inline causal analysis; a requested durable report is YYYY-MM-DD-postmortem-<topic>.md in caller-selected protected external non-Git storage'
---

# Postmortem

Answer an explicit retrospective causal question about a completed or stopped
goal, session or change using its actual intent, outcome and judgment evidence.
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
was the cause", satisfies none of these alone. The symptom may be intermittent,
or the recovery and the change may share an unobserved cause. Keep such claims
as correlations, name the alternatives still standing, and suggest the
discriminating experiment. A recommendation built on an unproven cause is
framed as that experiment, not as a supported change. Every supported causal
claim needs all three elements with citations; anything less stays a
correlation or an unknown.

## Prompt

```text
Postmortem last Thursday's release: the deploy needed four attempts and two
rollbacks before it stuck. Using the deploy log, the CI runs and the incident
channel notes, which failures were avoidable and what caused each one?
Answer inline.
```

## Critical Constraints

- Postmortem is retrospective causal analysis, not the general learning umbrella
  or a code-acceptance gate: acceptance proof and causal inference are different
  judgments, so a request for code and a postmortem does not make the
  postmortem an input to code judgment. Wait for a known outcome unless
  interim analysis was requested, and keep the overall request incomplete until
  the requested analysis exists.
- Existing verdicts and native judgments remain unchanged. It does not re-run acceptance validation
  or fabricate missing proof to enable a retrospective. An existing `verdict.v2`
  is optional evidence; its absence does not exclude a stopped or unvalidated subject.
- Because the caller owns subsequent action, do not rewrite proof, operate
  tracker state, change the remaining plan, reopen work or promote a rule.
- Empty or inconclusive analysis is valid; recommend no change when warranted.
  Manufacture neither certainty nor a lesson.

## Workflow

1. Pin the question, accepted intent, subject identity, actual outcome and
   available judgment with exact ids (commits, checks, messages, an existing
   verdict); keep missing evidence explicit.
2. Rebuild only the timeline the claims depend on, keeping delivered behavior,
   failed or stopped work and process output distinct. Hidden author reasoning
   is not fact; missing judgment is not a PASS or a FAIL.
3. Put each causal claim through the first check above. Distinguish necessary
   validation and compatibility work from avoidable rework; repeated review
   alone proves no waste.
4. For time or token claims, state source, interval, units, included and
   excluded actors, and uncertainty. Separate elapsed time, overlapping work and
   accounting scopes; never equate totals with waste, savings or money without
   supporting evidence.
5. Optionally seek independent support or challenge for contested causal claims
   within caller authority. Return the output below and stop; suggestions do not
   authorize implementation.

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
  Unknowns: <what would settle them>
  Changes (at most three, or "no change"): <change> - <its limit, or the experiment that tests it>
  ```

- Only when requested, save `YYYY-MM-DD-postmortem-<topic>.md` in caller-selected
  protected external non-Git storage. Missing routing does not authorize a
  repository fallback; preserve existing requested evidence under owner policy.
- The caller owns bookkeeping, planning and delivery. Optional
  [Memory](../memory/SKILL.md) owns any separately authorized curation, support
  and destination-disclosure review; retrospective evidence cannot promote itself.

## Quality Checklist

- [ ] The causal question and actual inputs are pinned; gaps are explicit.
- [ ] Supported and rejected claims cite discriminating evidence.
- [ ] Alternatives, counterfactuals, and unknowns remain visible.
- [ ] At most three changes, each bounded or framed as an experiment.
- [ ] The report stops short of proof, planning, tracker, and delivery authority.

Behavior examples are in [postmortem.feature](references/postmortem.feature).
