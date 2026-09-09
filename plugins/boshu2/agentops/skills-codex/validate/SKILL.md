---
name: validate
description: 'Freshly judge a finished change against its acceptance: PASS, FAIL, or NOT_PROVEN. Not for claim-vs-tree checks; that is reality-check. Triggers: "validate", "is this proven", "check this change", "cross-model review".'
---
# Validate

Independently judge one exact subject against the acceptance in its existing
bead or caller source, return one semantic result, and stop. Validate is the
sole semantic author of `verdict.v2` when persistence is requested.
`ao provenance store-verdict` supplies structural verification and atomic storage. Before the verdict,
read `boundaries.md` in the rpi skill's `references` directory for the state
Validate leaves to the caller.

## Prompt

```text
Validate bead ag-1234 in this fresh context. Intent: the bead text and digest.
Subject: manifest.json from:
ao provenance manifest --root . --include cli/internal/gates
Author context ctx-a1. Re-run `cd cli && go test ./internal/gates/...`.
Return PASS, FAIL, or NOT_PROVEN with evidence; stop.
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

## Fresh validator and model selection

Default to one fresh, author-distinct validator from the author's model family:
Codex/OpenAI work uses a fresh Codex/OpenAI reviewer; Claude/Anthropic work uses
a fresh Claude/Anthropic reviewer. Use the runtime's configured capable model
unless the caller pins one. Fresh context is required even when model weights
are identical; a new role instruction in the author's session is not fresh.
Risk determines the depth of evidence inspection, not an automatic second family.

Acceptance, tests/gates, stopping, allowances, safety, disclosure, hooks and
executable controls warrant deeper checks, including policy written as prose.
Conservative risk cues include `cli/internal/gates/**`, `scripts/check-*.sh`,
`tests/**`, `skills/*/scripts/**`, `skills/cc-hooks/policies/**`, `lib/**`,
`.github/workflows/**` and `scripts/security-gate.sh`. Unknown risk receives
deeper inspection; it does not silently change the selected model families.

The caller can request `--cross-model` or say "cross-model review" to add one
fresh validator from a different family. `--cross-model <model>` pins that
additional reviewer, for example `--cross-model claude-fable-5-1` from Codex
or `--cross-model gpt-6-astra` from Claude. These are skill prompt options,
not `ao` CLI flags. RPI forwards them unchanged. Without a pin, use an available,
authorized capable model from the other family; never silently substitute for
a pinned model or count two models in one family as cross-family diversity.
An explicit caller requirement remains required until the caller changes it;
changing the default cannot erase a finding or relabel a missing verdict as PASS.

Route selection and invocation through
[agent-native model-dispatch](../agent-native/references/model-dispatch.md);
[references/mechanics.md](references/mechanics.md) owns evidence storage.
There is no fixed ten-minute review timeout. Use the caller's selected review
timeout or remaining native deadline, respecting any earlier host or goal limit.
A timeout is missing judgment, not FAIL; never restart to renew an allowance.

Each selected judge receives the exact subject, unchanged acceptance and
authorized evidence independently, without the author's desired verdict or peer
conclusions. Record actual model/context identities and runtime receipts.
Missing freshness, an unbound subject, incomplete acceptance evidence, or
nonempty `not_checked` prevents PASS regardless of model family.
With no authorized adapter for requested diversity, disclose
`diversity_unsatisfied`: the required combined result is `NOT_PROVEN` even if
the same-family judge passed. A delivered FAIL stands. Advisory diversity that
the caller explicitly made optional may accompany the same-family result with
that limitation; it cannot discard an acceptance-relevant finding.

When selected judges disagree, preserve both verdicts and their evidence.
Required diversity converges only when both pass; neither majority vote nor a
preferred judge settles a split. Repair addresses known findings directly under RPI and real caller/native
bounds. Report unresolved dissent and the caller's decision openly.
Same-family fresh judgment reduces anchoring, but does not prove independence
from shared training biases; cross-family agreement is corroboration, not truth.

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
   by itself prove a design failure. Known defects return to direct repair;
   unknown cause, recurrence or no progress uses the charter's single bounded
   helper rule, without delegating repairs to this validator. Name the class or omit it; a `class` that is
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
