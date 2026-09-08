---
name: rpi
description: 'Coordinate one RPI traversal: one bounded Plan and Implement experiment, then fresh Validate and a bounded repair phase to convergence. Triggers: "run rpi", "run one traversal", "execute this plan", orchestration or worker delegation that implements changes.'
---
# RPI

Run one experiment from the caller's existing intent source and stop:

```text
anti-ceremony guard -> Plan -> Implement -> fresh Validate -> bounded repair -> report
```

RPI invokes the guard exactly once before Plan, preserves the original intent,
and dispatches Plan and Implement at most once; Validate repeats only inside
the repair phase, under the convergence law and the caller's `repair_rounds`.
Read [references/boundaries.md](references/boundaries.md), the ownership and
delegation boundary shared by the core skills, before dispatch.
[`scripts/run_once.py`](scripts/run_once.py) is the grandfathered pure reference:
it consumes supplied rounds and decoded receipt facts without Git, `ao`, a
tracker, I/O, helper dispatch, or a budget account. It checks the repair bound,
recurrence, discovery classification evidence, and named gap closure; fresh
judgment still establishes acceptance relevance and the truth of those facts.

## Prompt

```text
Run rpi on bead ag-1234 ("ao gate check lists the probe-coverage row").
Intent: the bead. Scope: cli/internal/gates/** plus docs/CI-CD.md. First check:
cd cli && go test ./internal/gates/... Fresh validator in a distinct context,
plus a cross-family leg (the scope is a risky surface). repair_rounds=2.
```

## It's working if

- The transcript shows one `anti-ceremony` call, then at most one `plan` and
  one `implement` dispatch.
- The validator's context ID differs from the author's, and the report opens
  with `status:` and changed paths, not a digest.
- Each round appends one `repair round N: k open findings` line to `checked`
  alongside the acceptance gap closed and its proof. Counts may grow through
  evidenced pre-existing discoveries; they never establish progress or cause.
  The run ends on `converged`, a law violation, or `repair_rounds`, with no next
  action after the evidence.

## Admission and phase lock

RPI activates for any plan-execute-verify request that changes the subject
(orchestration, worker delegation, "execute this plan"), named or not.
Research-, audit-, and review-only delegation produces evidence for a caller
and earns no verdict.

Once the caller accepts a plan (a duel or design synthesis included),
Plan is closed for that intent: every later lane returns implementation
evidence (diffs, commits, test results, receipts). Another planning, audit, or review
lane over the same intent needs new explicit caller authorization; a review
comment alone is not that.

## Contract

1. Invoke anti-ceremony's artifact-free quick guard once with the caller
   outcome, proposed process work, remaining proof, and stop condition. On
   `STOP`, dispatch no core phase, report `NOT_PLANNED` with the guard's
   one-sentence reason, and stop. On `CONTINUE`, proceed and add nothing else.
2. Resolve the existing bead or caller intent. Invoke Plan once only if the
   source needs shaping; Plan updates that source or proposes an amendment and
   creates no AgentOps packet. Without usable intent, report `NOT_PLANNED`.
   Before Implement or a fresh Validate, always bind the intent: a durable
   caller-owned source by reference and digest, or, only when no durable
   source exists, the exact resolved bytes snapshotted by the runtime under
   their digest.
   For selected CDLC work, the caller carries and records work/startup identities before substantive work for every child or resume, following [session associations](../cass/references/SESSION_FORMATS.md#work-to-session-associations) independently of final handoff; unknowns and failures remain explicit, and RPI never mutates the tracker.
3. When the write scope touches a risky surface (the short list
   [`validate`](../validate/SKILL.md) names), have one fresh judge read the
   frozen plan before Implement. A blocking finding sends the plan back to the
   caller as `NOT_PLANNED`, naming that finding. The caller may waive the read,
   and the report says so. Every terminal report says whether that read was not
   required, clean, blocking, waived, or never finished, so a waived or dead
   read is never taken for a clean one.
4. Invoke Implement once: one bounded experiment; the runtime derives subject
   identity and check receipts. After Implement, and again after each repair
   round, run `bash scripts/evidence-orphans.sh <changed paths>` and put its
   output in the check receipts, so the validator and the caller both see what
   evidence this change orphaned. With no subject built, report `NOT_BUILT`.
5. Invoke Validate once in a context distinct from the author's, passing the
   intent reference and digest, exact subject manifest, receipts, validator
   identity, and freshness attestation.
6. Enter the bounded repair phase: on `FAIL` or `NOT_PROVEN` with findings,
   repair the named findings and re-validate freshly while the law admits
   another round; stop when converged, stopped by the law, or out of
   `repair_rounds`. Persist `verdict.v2` only when the caller requests
   machine-readable evidence or a declared consumer requires it.

`NOT_PLANNED` and `NOT_BUILT` are report statuses, never semantic verdicts.
A caller or explicitly selected bounded outer goal may authorize a materially
different experiment within unchanged goal acceptance, scope, and allowance;
that starts a new invocation, never resets a spent bound, and never rewrites a
prior verdict. Changing accepted outcome or scope requires caller authority.

## The convergence law

A repair round is admitted only while all hold:

1. `rounds_used < repair_rounds` (caller-declared, default 2).
2. New digest-bound evidence proves closure of a named acceptance finding or,
   for `NOT_PROVEN`, resolves a named proof gap. A changed digest or a smaller
   finding count alone is not useful progress. Generated-only changes qualify
   only when the evidence proves that they repair required behavior or parity.
   An unchanged subject previously judged FAIL cannot be repaired by a new label
   or verdict flip; changed bytes still require acceptance proof.
3. No finding id closed in an earlier round reopens. No closed finding class
   recurs, and no introduced regression or new finding of unknown cause is
   admitted. Before/after reproduction or equivalent causal evidence under the
   same acceptance must distinguish a pre-existing discovery from a regression;
   neither counts, timestamps, nor a new id establish that distinction.

Keep the union of every required judge's findings, keyed by stable
`findings[].id`; do not hide a necessary finding as optional. Newly exposed
pre-existing defects may increase the open count while another acceptance gap
is demonstrably closed. Their evidence must prove prior existence;
unknown cause stops repair for causal examination even if another gap closed.
Validators reuse a short stable `class` for each kind of defect. A reopened id
or returning class warrants causal HOLD in a selected outer goal. Recurrence
alone does not prove that the design is wrong and never auto-reopens Plan.

Reuse existing check receipts, findings summaries, and evidence references for
this reasoning. In the pure reference, decoded receipt bindings use `ref`,
`subject_digest`, and `resolves` for ids actually closed. `preexisting` ids must
bind reproduction to the prior subject digest; `introduced` ids bind causal
comparison to the current digest and stop repair. These are supplied receipt
facts, not new persisted verdict fields or a lifecycle schema. The reference
cannot prove a receipt's truth or infer cause from wording.

Converged: the fresh validator returns PASS and every required cross-family
validator does too, over the exact subject and all acceptance with empty
`not_checked`. On any violation RPI stops and reports the current status.
`checked` carries one line per round (`repair round N: k open findings`); open
findings ride in the result and the report. A reworded finding with the same id
is the same finding. Acceptance and its digest stay fixed. The orchestrating
context fixes; judge legs only read. RPI convenes no further judge of its own,
does not escalate, and does not auto-replan.

## Cross-family validation

[`validate`](../validate/SKILL.md) owns risk classification by effect on
acceptance and enforcement. Fresh author-distinct judgment always remains;
changes to acceptance, stopping, guards, safety, or enforcement require the
stronger cross-family leg even when expressed in documentation. Narrow low-risk
wording edits may use one fresh judge with exact applicable receipts. Unknown
risk takes the stronger path. This prospective rule never waives a leg already
required for the current change or by caller acceptance. No authorized live
adapter for a required leg means `diversity_unsatisfied` / `NOT_PROVEN`.

Two judges disagreeing is the orchestrator's decision, and it is made in the
open. Both reads go in the report, each with its own verdict, alongside what
was decided and why. A risky surface still converges only when both judges
pass, so a split is never a PASS and no finding leaves the open set because one
judge was preferred.

## Judgment dispatch

| Condition | Leg |
|---|---|
| the write scope reaches a risky surface at Plan exit, a broad or unbounded scope included | [`premortem`](../premortem/SKILL.md) before Implement; a blocking finding is `NOT_PLANNED` |
| the two judges split | the orchestrator decides in the open and records both reads; [`council`](../council/SKILL.md) is available when the caller selects it |
| an irreversible landing decision | `one-way-door`, caller-selected, outside the traversal |

## Waves

RPI executes one traversal. A multi-wave intent runs one wave per `crank`
invocation: the caller selects the wave and the `repair_rounds` bound, crank
forwards both, invokes RPI per lane, returns wave evidence, and stops.
The caller selects each wave; RPI never extends the caller's bound.

## Spiral breaker

The hard [`anti-ceremony`](../anti-ceremony/SKILL.md) dependency owns the quick
guard; RPI reuses that judgment instead of turning each component, gate
failure, or specialist comment into a new planning artifact, and one terminal
goal may span several source owners as one bounded experiment.

The spiral breaker fires on a convergence-law violation; repeated activity
without acceptance-relevant evidence cannot renew repair. FAIL and NOT_PROVEN
are outcomes, not progress by themselves. Informative red may falsify a live
hypothesis and justify a different experiment in an explicitly selected bounded
outer goal under unchanged acceptance. It does not extend this RPI's bound.

The selected outer goal owns causal HOLD and exactly one bounded fresh helper
per incident, charged inside its remaining allowance. Cancellation, an explicit
refusal/judgment lane, or a genuinely spent hard time/cost/quota ceiling skips
that helper. An unhelpful helper stops implementation; automatic continuation
cannot create another helper incident. RPI itself neither dispatches that helper
nor reports native pause/aggregate enforcement from objective text.
Report `NOT_BUILT` when no subject exists; otherwise report the subject's current
status and unresolved acceptance, keeping the full integration check and
required fresh validation for the frozen subject.

## Report

1. **Interactive response:** return the result to the caller in natural
   language. This is the default assistant response.
2. **Machine artifact:** return or persist the exact `rpi-report.v1` object
   only when the caller requests machine-readable evidence or a declared
   adapter consumes it; `schemas/rpi-report.v1.schema.json` (repo checkout)
   owns its nine-key shape and `status` set.

Say in the report what this change orphaned: the evidence the plan budgeted to
recapture, and the evidence the orphan receipt actually named after Implement
and after each repair round.

Lead with the status and one sentence naming the caller-visible outcome, then
the subject: paths changed, commits, test results, acceptance satisfied or
remaining. A rising artifact count over an unchanged subject is a stop
signal, not progress. Add only the strongest proof, material unchecked scope,
and a clickable verdict reference when one exists; for `NOT_PLANNED`,
`NOT_BUILT`, or a guard `STOP`, say why no subject exists in one sentence.
One short paragraph or at most four bullets, ending with the evidence.
When no machine artifact was requested, do not create a hidden one.
