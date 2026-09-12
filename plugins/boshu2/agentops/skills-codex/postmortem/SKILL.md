---
name: postmortem
description: 'Analyze outcomes or an interim cutoff. Use when: a postmortem is explicitly requested; consumes available judgment, never gates code acceptance or requires a lesson.'
---
# Postmortem

Answer an explicit retrospective causal question about a completed or stopped
goal, session or change using its actual intent, outcome and judgment evidence.
For an explicitly requested interim analysis, pin the cutoff and pending checks;
its conclusions describe that interval and do not establish a final outcome.

## Prompt

```text
Postmortem this stopped change using its accepted intent, native session,
check results and reviewer messages. Which correction cycles were avoidable,
and which checks were necessary? No verdict file was saved. Answer inline.
```

## Critical Constraints

- Postmortem is retrospective causal analysis, not the general learning umbrella
  or a code-acceptance gate: acceptance proof and causal inference are different judgments.
  A request for code and a postmortem does not make the postmortem an input to
  code judgment. Wait for a known outcome unless interim analysis was requested;
  keep the caller's overall request incomplete until its requested analysis exists.
- Existing verdicts and native judgments remain unchanged. It does not re-run acceptance validation
  or fabricate missing proof to enable a retrospective. An existing `verdict.v2`
  is optional evidence; its absence does not exclude a stopped or unvalidated subject.
- Because the caller owns subsequent action, do not rewrite proof, operate
  tracker state, change the remaining plan, reopen work or promote a rule.
- Empty or inconclusive analysis is valid; recommend no change when warranted.
  Manufacture neither certainty nor a lesson.

## Workflow

1. Pin the explicit question, accepted intent, subject identity, actual outcome
   and available judgment. Cite native work/session references, commits, checks
   and reviewer messages as applicable; cite an existing verdict by exact id.
   Keep missing evidence explicit before drawing conclusions.
2. Reconstruct only the relevant evidence-backed timeline. Keep delivered
   behavior, failed/stopped work and process output distinct; hidden author
   reasoning is not fact. Missing judgment is not a PASS or a FAIL.
3. Separate delivered facts from causal hypotheses. Test contributing conditions
   against cited evidence, at least one
   plausible alternative and a counterfactual. Distinguish necessary validation
   and compatibility work from avoidable rework; repeated review alone proves no waste.
4. For time/token claims, state source, interval, units, included/excluded actors
   and uncertainty. Separate elapsed time, overlapping work and accounting scopes;
   never equate totals with waste, savings or money without supporting evidence.
5. Optionally seek independent support or challenge for contested causal claims
   within caller authority. Return supported/rejected claims, unknowns and at
   most three supported changes with limits or small suggested experiments. Stop;
   suggestions do not authorize implementation.

## Correlation-to-cause discrimination

Treat causal statements as hypotheses until the mechanism is demonstrated.
Promoting a claim from correlation to cause requires all three:

- a stated mechanism — the specific path by which the condition produced the
  outcome, in terms a reader could check against the subject;
- discriminating evidence — an observation that the mechanism predicts and at
  least one plausible alternative does not;
- a counterfactual test — what should have differed if the claim were false,
  with the cited evidence showing it did differ.

Post-hoc fix attribution — "we changed X and the failure stopped, therefore X
was the cause" — satisfies none of these alone. The symptom may be intermittent,
or recovery and the change may share an unobserved cause. Keep such claims as
correlations with untested alternatives and a suggested discriminating experiment.
Every supported causal claim needs all three elements with citations; anything
less stays a correlation or unknown.

## Output Specification

- Default to concise inline Markdown: question, pinned inputs, relevant timeline,
  hypotheses/evidence/counterfactuals, unknowns and bounded suggestions. No mandatory report or worksheet.
- Only when requested, save `YYYY-MM-DD-postmortem-<topic>.md` in caller-selected
  protected external non-Git storage. Missing routing does not authorize a
  repository fallback; preserve existing requested evidence under owner policy.
- `bash skills/postmortem/scripts/validate.sh` checks package structure and
  contract markers. It does not inspect report truth, causal support or acceptance.
- The caller owns bookkeeping, planning and delivery. Optional
  [Memory](../memory/SKILL.md) owns any separately authorized curation, support
  and destination-disclosure review; retrospective evidence cannot promote itself.

## Quality Checklist

- [ ] The causal question and actual inputs are pinned; gaps are explicit.
- [ ] Supported and rejected claims cite discriminating evidence.
- [ ] Alternatives, counterfactuals, and unknowns remain visible.
- [ ] The report stops short of proof, planning, tracker, and delivery authority.

Behavior examples are in [postmortem.feature](references/postmortem.feature).
