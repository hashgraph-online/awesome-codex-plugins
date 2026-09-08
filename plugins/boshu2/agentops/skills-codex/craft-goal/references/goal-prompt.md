# Mayor-style goal prompt

Copy this prompt verbatim, replacing every angle-bracket field. Do not delete
the wave, hard-envelope, and terminal-report sections.

```text
Goal outcome:
<larger caller-visible result>

Terminal acceptance and evidence:
1. <criterion> — <authoritative proof>

Non-goals and authority:
- <excluded outcomes/mechanisms>
- Reads/writes/external/Git authority: <exact scope>

Bead graph:
- Root epic/mol: <existing id or bounded bootstrap rule>
- Initial experiments, if known: <bead → criterion/uncertainty>
- Record notes, scratch, evidence, verdict refs, and dependency/provenance links.

Experiment policy:
- One bead is one RPI experiment.
- Select only work tied to an unmet criterion or named blocking uncertainty.
- Consume each verdict unchanged; useful progress needs evidence tied to an
  unmet criterion or a blocking uncertainty, not digest/count movement alone.
- Distinguish pre-existing discovery from introduced regression using causal
  evidence; unknown cause and recurrence require HOLD, not a design diagnosis.
- Classify discoveries as necessary-now, linked-follow-up, or HOLD/rescope.
  Never downgrade a necessary finding to optional to obtain completion.
- Retain evidence/provenance; revise or withdraw beliefs when evidence changes.

Wave envelope:
- <numeric RPI/concurrency/time/token/live-attempt limits>

Hard goal envelope:
- <numeric total RPI/time/token/live-attempt/compaction/surface limits>
- No artifact, repair, helper, subject, compaction, or wave resets a total.
- Include helper and validation costs inside the allowance.
- Enforcing native controls and observable remaining allowance: <actual controls
  and measurements; explicitly identify any unmeasured aggregate>.
- Objective text alone does not enforce a budget or a native pause.

Breaker and andon:
- Ordinary informative red may produce a materially different next experiment.
- <threshold> non-ratcheting results, oscillation, regression, unknown defect
  cause, recurrence, or scope pressure: HOLD implementation for causal review.
- Consult exactly one bounded fresh helper per HOLD incident inside the existing
  allowance; repeated continuation of that incident does not reset the helper.
- UNSTUCK names a different admissible experiment and discriminating check;
  ESCALATE or no useful admissible experiment reports NEEDS_OPERATOR.
- Cancellation, explicit refusal/judgment, or spent hard time/cost/quota skips
  the helper and stops work; a retry threshold alone is not a spent budget.

Wave checkpoint:
- acceptance matrix; graph frontier; verdict/evidence summary;
- ratchets versus non-progress; measured remaining budgets; next thesis;
- observed native continuation/stop state, outstanding gaps, and helper use.
  Never claim a native pause or aggregate enforcement based only on this text.

Terminal reports:
- ACHIEVED: every terminal criterion is proven.
- NOT_ACHIEVED: envelope or permitted search is exhausted; report exact gaps.
- NEEDS_OPERATOR: judgment, rescope, or helper escalation; stop implementation.
```
