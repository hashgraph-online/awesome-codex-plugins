# Advanced Debugging Governance

Load this reference only for the evidence triggers named in `SKILL.md`. It
owns escalation execution cards and expanded governance checks. It does not
own deep causal proof: `root-cause-claim-contract.md` remains the sole owner of
the Pre-Claim Gate, causal topology proof, falsifier proof, and layer ceiling.

## Contents

- Layer-stop and intervention cards
- Residual-symptom and compound-root procedure
- Architecture escalation after repeated fixes
- Expanded H/T/D governance gate

## Layer-stop procedure

Start at L1 and exhaust the current layer's “why” questions before moving up:
L1 symptom, L2 logic, L3 system, L4 architecture, L5 cross-system contract,
L6 platform constraint, L7 spec gap. Use this card when the stop point changes
the repair boundary, contract owner, product/spec decision, or user correction
path—not for ordinary factual answers.

```text
Layer Stop Card:
- Current Stop Layer: L1 | L2 | L3 | L4 | L5 | L6 | L7 | T-class boundary
- Checked Path:
- Evidence For Stop:
- Excluded Layers:
- Falsifier:
- User Intervention Point:
- Next Action:
```

The falsifier here records what observation would reopen the stop decision.
When a root-cause claim is in scope, use the proof contract rather than
expanding or reinterpreting the falsifier in this reference.

If a user provides a fact that contradicts the stop layer, preserve it as
evidence, reopen the earliest invalid edge, and produce:

```text
Intervention Card:
- User-provided fact:
- Invalidated assumption or edge:
- Earliest layer reopened:
- Evidence to reacquire:
- Repair paused: yes
```

## Residual symptoms and compound roots

After a repair, any remaining symptom starts a fresh diagnosis before another
edit. Compare the old and new causal paths:

| Observation | Working classification | Next action |
| --- | --- | --- |
| Same conditions and same path | incomplete repair | resume upward from the source |
| Different conditions, paths converge | repair stopped too low | reopen their shared upstream |
| Different conditions, paths diverge | possible independent compound | diagnose each path separately |
| Same symptom, reduced only | downstream mitigation | trace back from the remaining source |

Treat these as working classifications, not proof. When paths diverge or a
compound/cluster is plausible, read `root-cause-claim-contract.md` and apply
its topology and member-proof contract. Do not duplicate that table here.

Extended topology procedure:

1. Draw one bounded path per observed manifestation using evidence anchors.
2. Mark the first confirmed convergence or divergence point; unknown edges
   remain unknown rather than being collapsed.
3. Ask whether apparently separate members share an upstream owner; if so,
   reopen that owner instead of multiplying repairs.
4. Hand the path set to the canonical topology proof owner before claiming
   `single-root`, `independent-compound`, or a cluster.
5. Carry every proven root into repair scope; an omitted independent root is a
   residual-risk finding, not a successful closeout.

## Rare intervention and architecture escalation

After three failed fixes, do not attempt a fourth. Escalate when fixes expose
new shared state/coupling, require broad refactoring, or create symptoms in new
places:

```text
Architecture Escalation:
- Failed repair hypotheses and evidence:
- Repeated owner/coupling pattern:
- Current canonical owner uncertainty:
- Architecture question for the user:
- Safe read-only next step:
```

If the correct change is outside the repository, breaks a published contract
without migration, depends on undefined behavior, or lacks permission/data,
switch from repair to a bounded mitigation and disclose the boundary.

## Expanded governance gate

Before claiming debugging complete, classify countable signals.

### H-class: continue upward if any apply

- H1: a conditional/exception branch was added.
- H2: multiple sites changed but selected regression covers only one.
- H3/H9: repair sits in a consumer/caller/presentation layer, not the owner.
- H4: the same bug pattern still exists elsewhere.
- H5: the original reproduction retains any anomaly.
- H6: history shows the symptom was “fixed” before and that diff was not
  inspected.
- H7: candidate fix adds keyword, phrase, regex, negation-word list, or sample-text exception.
- H13: candidate fix names only the observed sample wording/input instead of proving the bug class.
- H8: a guard, fallback, adapter, compatibility, prompt, or legacy path grew.
- H10: downstream logic re-parses raw text or re-infers action/state while typed intent, normalized state, contract, or another source-of-truth exists.
- H11: artifact/cache/readback symptoms were patched without producer proof.
- H12: duplicate owners remain without a retirement trigger.
- H14: topology-specific member proof is incomplete: a `conjunctive-cluster`
  lacks per-member necessity or set sufficiency, or an `independent-compound`
  lacks same-incident activity, per-root path proof, independence, or
  shared-upstream exclusion.
- H15: topology was declared compound/cluster without running the anti-disguise check.
- H16: an upstream generator or recurrence path remains open while the causal
  status is reported as `root`.
- H17: the quick lane was used without local origin/termination, negative
  upstream/history/same-pattern evidence, and a bug-class variant
  counterfactual.

### T-class: stop drilling and disclose mitigation

- T1: required change is outside repository authority.
- T2: it breaks a published API with no migration path.
- T3: correct behavior is undefined by the specification.
- T4: required permission or information is unavailable.

Record the boundary, root evidence, exposed vulnerability, mitigation, and
whether a more resilient contract is possible.

### D-class: depth evidence for closeout

Require: the canonical owner was repaired; the original reproduction is clean;
same-pattern occurrences are handled; no unnecessary path/fallback grew; and
Minimality Check says `sufficient repair` or retains a bounded patch with a
deletion trigger.

- D6: causal topology is explicitly classified by
  `root-cause-claim-contract.md`; conjunctive members pass necessity/set
  sufficiency, while independent roots pass same-incident, per-root path,
  independence, and shared-upstream proof.
- D7: anti-disguise check has been run for any compound/cluster classification.
- D8: the recurrence generator is accounted for and causal status matches the
  remaining evidence; open recurrence is not labeled `root`.
- D9: when the full challenge is skipped, the `Quick Exit Proof` is complete.

Then rerun `Goal | DeeperCause | Evidence | Risk/Unknown | Decision`, confirm
the source rather than the sample was fixed, state retirement delta, and assign
confidence A/B/C. H/T/D output is advisory method-pack evidence, never a
`GateDecision`, `PolicySnapshot`, or completion authority.
