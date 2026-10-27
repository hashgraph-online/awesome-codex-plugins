# Goal prompt

Copy this prompt verbatim, replacing every angle-bracket field. Do not delete
the wave, hard-envelope, breaker and terminal-report sections.

```text
Goal outcome:
<larger caller-visible result>

Terminal acceptance and evidence:
1. Given <state>, when <event>, then <observable result> — <authoritative proof>

Domain terms:
- <term>: <one-line definition>; use only this word in beads, code and tests

Non-goals and authority:
- <excluded outcomes/mechanisms>
- Reads/writes/external/Git authority: <exact scope>

Bead graph:
- Tracker: <tracker with status, dependencies and notes>
- Root epic: <existing id or bounded bootstrap rule>
- Initial experiments, if known: <bead → criterion/uncertainty>
- Record notes, scratch, evidence, verdict refs, and dependency/provenance links.

Experiment policy:
- Apply the `navigate` skill each wave: observe, pick, ratchet, checkpoint.
  These policy lines bind with or without it.
- One build bead is one bounded experiment: native execution, or one RPI run
  when the caller selects it. A decision bead resolves through the method
  Navigate names for it, not through a build.
- An ordinary bead's checks and CI are its result. It gets one author-distinct
  fresh validation only when the caller asks, a mistake cannot be cheaply undone
  after it lands, or no deterministic check covers the change; a repair does
  not start another.
- Select only work tied to an unmet criterion or named blocking uncertainty.
- Consume each verdict unchanged; useful progress needs evidence tied to an
  unmet criterion or a blocking uncertainty, not digest/count movement alone.
- Distinguish pre-existing discovery from introduced regression using causal
  evidence; unknown cause and recurrence require HOLD, not a design diagnosis.
- Classify discoveries as necessary-now, linked-follow-up, or HOLD/rescope.
  Never downgrade a necessary finding to optional to obtain completion.
- Retain evidence/provenance; revise or withdraw beliefs when evidence changes.

Wave envelope:
- <numeric experiment/concurrency/time/token/live-attempt limits>

Hard goal envelope:
- <numeric total experiment/time/token/live-attempt/compaction/surface limits>
- No artifact, repair, helper, retry, subject, compaction, or wave resets a total.
- Include helper and validation costs inside the allowance.
- Enforcing native controls and observable remaining allowance: <actual controls
  and measurements; explicitly identify any unmeasured aggregate>.
- Objective text alone does not enforce a budget or a native pause.

Breaker and helper:
- Ordinary informative red may produce a materially different next experiment.
- HOLD implementation for causal review on: a repeated blocker, <threshold>
  non-ratcheting results, oscillation between prior approaches, introduced
  regression, unknown defect cause, recurrence, scope pressure, a requested
  acceptance change, or an operator-reserved decision.
- A requested acceptance change or operator-reserved decision reports
  NEEDS_OPERATOR at once, with no helper: only the caller can settle it.
- Any other HOLD incident gets at most one bounded fresh helper inside the
  allowance, given acceptance, observations, failed approaches, exact evidence
  and remaining allowance. Rewording the blocker or continuing the incident is
  not a new incident.
- UNSTUCK names a materially different admissible experiment, its
  discriminating check, and why it fits unchanged acceptance, authority and
  bounds; the goal, not the helper, resumes, and a spent experiment bound stays
  spent. ESCALATE, an unhelpful answer or no admissible experiment reports
  NEEDS_OPERATOR; no more implementation or helper dispatch follows.
- Cancellation stops at once. An explicit refusal, or a spent hard time/cost/
  quota ceiling, skips the helper and reports the refusal or NOT_ACHIEVED with
  the exact gaps. A retry threshold alone is not a spent budget, and a
  threshold for recording blocked is bookkeeping, not permission for more work.

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
