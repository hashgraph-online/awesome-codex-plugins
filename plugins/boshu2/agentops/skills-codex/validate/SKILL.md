---
name: validate
description: 'Freshly judge a finished change against original acceptance before merge. Use when: independent proof is needed; author tests cannot issue PASS. Triggers: "check this change".'
---
# Validate

Freshly judge the exact candidate against accepted intent, return
`PASS`, `FAIL`, or `NOT_PROVEN`, and stop. The author cannot provide binding PASS. Read RPI
[boundaries](../rpi/references/boundaries.md) before judgment; load helper flags
and storage details from [mechanics](references/mechanics.md) when needed.

## Preconditions and freshness

Final review starts after required checks and known repairs, with the candidate
held unchanged. Supplied failed-acceptance evidence means FAIL on that subject;
do not review a moving repair. The subject is a nonempty implementation candidate; plans, audits
and reviews are subjects only when the caller requested document review.

Use exact caller/runtime-owned intent bytes and derived acceptance identity.
Author and validator context IDs must be explicit and distinct; freshness is
attested by runtime or caller with the attester's identity. Missing, colliding
or unattested identity means NOT_PROVEN, not proof of isolation by role name.

Default to one fresh reviewer in the author's model family: Codex/OpenAI for
Codex/OpenAI, Claude/Anthropic for Claude/Anthropic. Use the runtime's configured
capable model unless pinned. A new role in the author's context is not fresh.
Supply task-specific intent, scope, exact subject and relevant evidence, without
full author history, desired verdict or peer conclusions. Retrieve more source
when a criterion requires it; concise input must not omit necessary evidence.

Cross-model review is opt-in. `--cross-model [model]` is a skill prompt selection,
not an AO flag; it adds a fresh other-family reviewer. Required legs remain
required: unavailable diversity yields `diversity_unsatisfied` and NOT_PROVEN
for the combined request, even if another leg passed. Preserve delivered FAILs
and dissent; neither voting nor model preference makes a split PASS. Optional
unavailable diversity stays disclosed without erasing findings. Exact invocation,
authorization, runtime identity and independent-input rules live in
[model-dispatch](../agent-native/references/model-dispatch.md). No fixed
ten-minute cap applies; respect real caller/native bounds without renewing them.
A timeout is missing judgment, not FAIL. Shared-family or cross-family agreement
alone is not truth or proof of freedom from training bias.

## Judgment

Use the helper for each changed path (repeat `--include` for complete scope):

```sh
ao provenance manifest --root "$REPO_ROOT" --include "$CHANGED_PATH"
```

1. Derive `subject-manifest.v1` using the existing helper at start and end.
   A mismatch means mutation and NOT_PROVEN. Verify exact intent continuity,
   cited evidence digests and complete changed-path coverage; missing integrity
   is NOT_PROVEN. Proven out-of-scope change is FAIL.
2. Revisit the original accepted behavior examples, including those in the
   conversation or bead. Check the observable result and its established
   domain meaning on the exact candidate. A new test or renamed concept cannot
   replace an unfulfilled scenario; missing scenario evidence is NOT_PROVEN.
   Inspect the actual diff against every acceptance criterion. Risk determines
   depth: acceptance, permissions, tests/gates, stopping, disclosure, hooks and
   executable controls warrant deeper inspection, including prose policy.
   Unknown risk merits examination, not automatic extra reviewers.
3. Re-execute discriminating proofs for risk-critical, uncertain or thinly
   evidenced claims. Valid digest-bound receipts may establish routine facts;
   do not replay every author command or full suite merely because this is a
   fresh context. The repository's required integration checks still run on
   the final subject. A changed subject needs new judgment and affected checks.
4. Classify commands before executing them. Regeneration, synchronization,
   formatting and `--force` are subject-mutating until proven otherwise; run
   them only on a disposable copy or a committed subject, never an uncommitted
   judged tree. Do not overwrite the candidate while validating it.
5. Reject green obtained through weaker assertions, tolerances, goldens,
   suppressions or acceptance edits. Each criterion needs supporting evidence;
   explanation alone is not proof. A necessary finding cannot become an
   optional caveat or non-goal. Publication/provenance claims in docs also need
   verifiable evidence.
6. Return one result with criterion-level evidence, findings, checked scope,
   `not_checked`, author/judge identities and contexts, and the freshness
   attestation. PASS requires all criteria verified, nonempty checked scope and
   top-level evidence, and empty `not_checked`. An unverified criterion means
   NOT_PROVEN; proven failed acceptance or scope violation means FAIL.

## Findings and report

`not_checked` means in-scope acceptance that was not verified. Other limits
remain in criterion reasoning, declared non-goals or residual-risk prose; never
hide or delete them to obtain PASS. Keep prior findings visible. For each new
finding, name a short stable nonempty `class` describing the defect, reused on
recurrence, and distinguish pre-existing, introduced or unknown cause using
before/after or equivalent causal evidence. Counts and timestamps alone do not
establish cause. Known findings return to direct repair; causal stalls use the
RPI single-helper rule, not repairs delegated to this validator.

Keep the report proportional: cite the exact subject, complete bound manifest
and existing receipts instead of copying path or digest inventories. Group
generated companions by source owner and verified equivalence; still verify
every changed path and cited binding. Include excerpts only to assess a finding.
Retain every criterion, necessary finding, identity, freshness fact and unchecked
surface. Complete coverage does not require a second copy of the evidence.

Return the candidate verdict promptly when the judgment is complete. When
delivery is outside the accepted review scope, the caller checks its native facts without
another semantic review of unchanged content. Delivery inside acceptance stays
unverified until its evidence exists: do not issue complete PASS early or remove
the criterion. Use the existing result for any pending delivery update, without
repeating the investigation or creating another report.

Validate is the sole semantic author of `verdict.v2`.
Only when the caller requests machine-readable evidence or a declared consumer
requires it, persist through `ao provenance store-verdict`. Validate supplies judgment;
Go verifies structure and storage, not truth. Otherwise return the result
through the existing caller channel without hidden machine artifacts.
Validate owns no repair, retry, delivery or tracker transition.
