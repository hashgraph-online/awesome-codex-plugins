---
name: validate
description: 'Freshly judge a finished change against its acceptance: PASS, FAIL, or NOT_PROVEN. Not for claim-vs-tree checks; that is reality-check. Triggers: "validate", "is this proven", "check this change".'
---
# Validate

Independently judge one exact subject against the acceptance in its existing
bead or caller source, return one semantic result, and stop. Validate is the
sole `verdict.v2` writer when persistence is requested. Before the verdict,
read `boundaries.md` in the rpi skill's `references` directory for the state
Validate leaves to the caller.

## Prompt

```text
Validate bead ag-1234 in this fresh context. Intent: the bead text and digest.
Subject: manifest.json from `python3 skills/validate/scripts/validate.py
manifest --root . --include cli/internal/gates`. Author context ctx-a1. Re-run `cd cli && go test
./internal/gates/...`. Return PASS, FAIL, or NOT_PROVEN with evidence; stop.
```

## Preconditions

- The subject is a nonempty implementation candidate: the manifest lists at
  least one entry. Plans, audits, and reviews are subjects only when the
  caller explicitly requested document review.
- The intent source is a caller-owned artifact or a runtime-owned
  content-addressed snapshot; its acceptance digest is derived automatically.
- Author and validator context IDs are explicit, and freshness is attested
  with `source: runtime | caller` and an attester identity. Missing,
  colliding, or unattested identities produce `NOT_PROVEN`: a declared trust
  fact, not cryptographic proof of isolation.

## Cross-family fresh validator (default on risky surfaces)

Classify risk by the change's effect on acceptance and enforcement, not its
extension or location alone. Changes to acceptance, tests/gates, stopping and
allowance rules, safety, disclosure, hooks, or executable control behavior need
a second fresh validator from a different model family. Documentation that
agents execute as policy can change enforcement and takes this stronger path.

The conservative cues remain `cli/internal/gates/**`, `scripts/check-*.sh`,
`tests/**`, `skills/*/scripts/**`, `skills/cc-hooks/policies/**`, `lib/**`,
`.github/workflows/**`, and `scripts/security-gate.sh`. A narrowly scoped wording
or reference correction with evidence of no behavioral or enforcement effect
may use one fresh author-distinct judge and applicable exact-input receipts.
Record that risk reason in existing intent/evidence prose; no risk artifact is
required. Unknown or disputed risk takes the stronger path. This rule applies
prospectively: it cannot remove a review leg already required for the current
change, or override caller-required diversity. Fresh judgment, exact subject,
all acceptance, and empty `not_checked` remain mandatory at every risk level.
Route adapter selection and invocation through
[agent-native model-dispatch](../agent-native/references/model-dispatch.md);
[references/mechanics.md](references/mechanics.md) owns evidence storage.
The fresh and cross-family legs receive independently supplied initial inputs:
exact subject, unchanged acceptance and authorized evidence, without peer
conclusions. Record actual model/context identities and runtime receipts.
With no authorized live adapter, disclose `diversity_unsatisfied`. If the leg
is required by risk or caller acceptance, a single-family PASS is `NOT_PROVEN`;
optional unavailable diversity is disclosed with the same-model result.
Same-family agreement is not convergence. A single-family FAIL stands.

When the two judges disagree, each reports its own verdict and neither resolves
the split. Required diversity converges only when both judges pass, so a split is
never PASS. Repair works the split down, and what survives it is the
orchestrator's decision, made in the open: both reads go in the report with
what was decided and why. Validate never treats agreement with itself, the
absence of a second verdict, or a preferred judge as a tie-break.

## Mutating-check quarantine

Classify every acceptance-listed command as read-only or subject-mutating
before running it: regen scripts, sync scripts, formatters, and anything with
`--force` are mutating until proven otherwise. Run a mutating check only
against a disposable copy or a committed subject, never the judged working
tree (the boundaries appendix records the regen that overwrote a subject).

## Scope disclosure

`not_checked` has exactly one meaning: **in-scope acceptance surface this
validation did not verify**. PASS asserts the whole declared acceptance
surface was verified, so a PASS carries no `not_checked` entries; every other
scope limit has a home that survives inside a PASS: a bounded proof in
`criteria[].reason`, a declared non-goal in the intent source, residual risk
in the report (table in the mechanics reference). Emptying `not_checked` to
obtain PASS is a contract violation: unverified acceptance makes the honest
result `NOT_PROVEN`, and an entry that was never acceptance moves to its home
and stays visible. A finding necessary to acceptance cannot be relabeled as
optional, residual risk, or a non-goal to obtain PASS.

## Workflow

1. Derive `subject-manifest.v1` with the helper's `manifest` command (flags
   in the mechanics reference) at the start and again at the end; any
   mismatch is subject mutation and returns `NOT_PROVEN`.
2. Confirm the intent-source digest is unchanged since implementation, every
   cited evidence digest matches the artifact it names, and complete
   changed-path coverage can be derived; otherwise `NOT_PROVEN`.
3. Adjudicate the actual diff: runtime-derived changed paths against the
   intent's scope classes. A proven out-of-scope path is `FAIL`; incomplete
   scope evidence is `NOT_PROVEN`.
4. Inspect the exact subject and evidence. Reported exit codes are claims:
   re-execute the proofs that bear on acceptance. A changed test, gate,
   fixture, golden, tolerance, suppression, or acceptance source must be
   required by the original intent, with green coming from implemented
   behavior; green obtained by weakening acceptance is `FAIL`. Judge every
   acceptance criterion against its own evidence reference; a criterion with
   no evidence of its own is unverified, not passed.
5. Choose exactly one semantic result: `PASS`, `FAIL`, or `NOT_PROVEN`. Return
   it with criterion-level results, findings, evidence references, `checked`,
   `not_checked`, both identities, both context IDs, and the freshness
   attestation. Name a `class` for each finding: one short stable name for the
   kind of defect, one per finding, reused word for word when the same kind
   recurs, so the orchestrator can see a closed kind come back. Explain in the
   existing summary and evidence whether a newly exposed defect pre-existed the
   change, was introduced by it, or has unknown cause. Use before/after proof or
   equivalent causal evidence under unchanged acceptance; counts and timestamps
   do not establish cause. Recurrence calls for causal examination and does not
   by itself prove a design failure. Name the class or omit it; a `class` that is
   present and blank is a finding against this validator,
   and so is a class that does not describe its finding. PASS
   requires distinct identities, explicit freshness, nonempty checked scope,
   nonempty top-level evidence, evidence for every criterion, and an empty
   `not_checked`. A documentation sentence claiming something is published,
   pinned, or proven is an acceptance criterion like any other: it needs a
   check this validator can run, or it is `not_checked`. The
   `docs.claims-tracked` gate covers the tracked-file half of that and nothing
   more.
6. Only when the caller requests machine-readable evidence or a declared
   downstream consumer requires it, persist canonical `verdict.v2` with the
   helper's `store-verdict` (mechanics reference), then return the artifact
   path and digest with the result. Stop.

Fresh validation is independent judgment over the exact subject, not a replay
of every author command: rerun the risk-critical, uncertain, or thinly
evidenced checks; a digest-bound deterministic receipt may prove routine
facts; replay an expensive full suite only when acceptance requires it. The
repository's full literal CI command set, as quoted in `AGENTS.md`, runs
once, on the final integrated subject.

## It's working if

Observable in the trace, without reading the prose, and the rubric a fresh
independent judge scores this skill against:

- A criterion whose evidence is a justification rather than a proof is named,
  and the result is `NOT_PROVEN` rather than `PASS`.
- Green obtained by widening a tolerance, skipping a case, or re-baselining a
  budget is reported as `FAIL`, never as completion.
- Every scope limit is placed in one of the Scope-disclosure homes; none was
  deleted to reach `PASS`.
- The subject manifest is derived twice, at the start and at the end, and the
  two are compared.

## Boundary

Validate emits no next action, repair, retry, replan, or delivery state (full
list in the boundaries reference); ledger availability cannot change a
verdict's validity.
