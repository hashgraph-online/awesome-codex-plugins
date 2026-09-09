# Optional fixed-dispatch reference adapter

The grandfathered `scripts/run_once.py` is a pure developer reference for callers
that explicitly select fixed dispatch and a finite list of supplied review rounds.
It invokes an explicit anti-ceremony function, Plan and Implement at most once;
its repair evaluator consumes supplied evidence and cannot execute agents, infer
causes, fix subjects or enforce aggregate budgets. Installed native RPI follows
its operating charter, not this adapter. The old phase lock and default two-round
limit apply only to this selected adapter, never as a restriction on native
implementation's direct repairs or evidence-driven approach revision.

Its existing deterministic tests guard exact evidence and finite consumption;
they do not prove native agent behavior or practical benefit. It stops when
converged, stopped by the law, or out of `repair_rounds` and never extends the
caller's bound. The adapter preserves these narrower admission semantics:

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


An unknown cause or recurrence returns evidence to the native caller; the
adapter dispatches no helper. The native charter decides whether a genuine
causal stall merits its single bounded consultation. This does not revive a
spent caller bound or change a completed verdict.
