---
name: postmortem
description: 'Test a retrospective causal question against outcome evidence. Use when: a postmortem is explicitly requested; finishing a task does not require a report or lesson.'
---
# Postmortem

> **Purpose:** Answer an explicit retrospective causal question using the
> already-validated outcome and evidence.

## Prompt

```text
Postmortem: verdict .agents/ao/verdicts/2026-08-30-cli-regen.json shows
NOT_PROVEN then PASS after we added a mutating-check guard to
skills/validate/scripts/validate.sh. Did that guard actually cause the
fix, or did the flaky CI runner just stop flaking that day?
```

## It's working if

Observable in the trace, without reading the prose:

- The report pins the exact `verdict.v2` id and the causal question before
  the timeline section.
- A claim promoted to cause cites its mechanism, evidence, and
  counterfactual together under the report's `hypotheses` list.
- A claim resting only on symptom cessation is listed under `unknowns`,
  not promoted to cause.
- The report lands at
  `.agents/scratch/postmortem/YYYY-MM-DD-postmortem-<topic>.md` and
  `bash skills/postmortem/scripts/validate.sh` exits 0.

## Critical Constraints

- Because proof and causal inference are different judgments, Postmortem is retrospective causal analysis, not the general learning umbrella and not a completion gate.
- It consumes immutable Validate verdict evidence and does not re-run acceptance validation because Validate already owns that proof.
- Treat causal statements as hypotheses because causal confidence must survive
  alternatives. Separate observed sequence, contributing conditions,
  counterfactuals, and unknowns.
- A correlation is not promoted to cause without evidence that discriminates
  plausible alternatives.
- Because the caller owns delivery decisions, do not rewrite proof, operate
  tracker state, change the remaining plan, or promote a rule. Return evidence
  to the caller.
- Empty or inconclusive analysis is valid; manufacture neither certainty nor a
  lesson to make the retrospective feel useful.

## Workflow

1. Pin the verdict, subject evidence, and explicit causal
   question.
2. Reconstruct the evidence-backed timeline without importing hidden author
   reasoning as fact.
3. List candidate contributing conditions and at least one plausible
   alternative explanation.
4. Test each claim against cited evidence and a counterfactual: what should
   differ if the claim were false?
5. Optionally use independent judges to challenge contested causal claims.
6. Emit a report containing supported claims, rejected claims, unknowns,
   evidence references, and suggested experiments. Stop.

## Correlation-to-cause discrimination

A fix is proven when the mechanism is demonstrated, not when symptoms stop.
Promoting a claim from correlation to cause requires all three:

- a stated mechanism — the specific path by which the condition produced the
  outcome, in terms a reader could check against the subject;
- discriminating evidence — an observation that the mechanism predicts and at
  least one plausible alternative does not;
- a counterfactual test — what should have differed if the claim were false,
  with the cited evidence showing it did differ.

Symptom disappearance after a change satisfies none of these on its own: the
change and the recovery may share an unobserved cause, or the symptom may be
intermittent. The named failure mode is post-hoc fix attribution — "we
changed X and the failure stopped, therefore X was the cause." Claims backed
only by symptom cessation stay in the report as correlations with the
untested alternatives listed, and the suggested experiment is the
discrimination that would settle them. Stop condition: every supported causal
claim in the report carries all three elements with citations; anything less
is filed under correlations or unknowns, never silently promoted.

## Output Specification

- **Artifact directory:** `.agents/scratch/postmortem/`.
- **Filename convention:** `YYYY-MM-DD-postmortem-<topic>.md`.
- **Serialization/schema format:** Markdown with causal question, pinned inputs,
  timeline, hypotheses, evidence, counterfactuals, unknowns, and experiments.
- **Validator command:** `bash skills/postmortem/scripts/validate.sh`.
- **Downstream handoff:** Learn or the caller may consume the analysis; they own
  any bookkeeping, promotion, planning, or delivery decision.

## Quality Checklist

- [ ] The causal question and immutable inputs are pinned.
- [ ] Supported and rejected claims cite discriminating evidence.
- [ ] Alternatives, counterfactuals, and unknowns remain visible.
- [ ] The report stops short of proof, planning, tracker, and delivery authority.

Executable behavior is in [postmortem.feature](references/postmortem.feature).
