---
name: validate
description: 'Freshly judge whether a finished change and its claims meet original acceptance: PASS, FAIL or NOT_PROVEN. Use when: asked for a go/no-go, sign-off or independent verdict.'
practices:
- design-by-contract
- llm-eval-harness
- content-addressed-storage
hexagonal_role: driving-adapter
consumes:
- subject-manifest.v1
produces:
- subject-manifest.v1
- validation-result
- verdict.v2
context_rel:
- kind: customer-of
  with: plan
- kind: customer-of
  with: implement
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: judgment
  dependencies: []
  capabilities: [compute_subject_identity, judge_acceptance, return_validation_result, persist_verdict]
  effects: [write_verdict_artifact]
  canonical_status: canonical
  disposition: keep
output_contract: 'PASS | FAIL | NOT_PROVEN with criteria, evidence, checked/not_checked, identity, and freshness; optional schemas/verdict.v2.schema.json persistence'
---

# Validate

Freshly judge one finished candidate against its original acceptance, return
`PASS`, `FAIL`, or `NOT_PROVEN` with criterion-level evidence, and stop.
Neighbours: advice or a second look is [Review](../review/SKILL.md); whether a
stated claim holds is [Reality Check](../reality-check/SKILL.md). This file
carries every rule the judgment needs. Linked files, including
[RPI boundaries](../rpi/references/boundaries.md) and
[mechanics](references/mechanics.md), add depth only: if one cannot be read,
judge from this file and say which was unavailable.

## Rules that decide the verdict

- The author cannot issue a binding PASS, and advisory findings cannot stand in
  for this judgment. An author's summary, confidence or assurance is a claim to
  check, not evidence; explanation alone is not proof.
- Each criterion needs its own evidence on the exact candidate. A criterion
  nobody demonstrated goes in `not_checked` and never counts toward PASS.
- A changed test, tolerance, golden, suppression or acceptance text must still
  satisfy the original intent. Green obtained by weakening the oracle is FAIL
  for the criterion it was meant to prove, and that green is not evidence.
- Read receipts; do not re-run checks the author ran on this exact subject or
  that CI will run. Re-execute only a risk-critical claim that has no receipt.
- A necessary finding never becomes an optional caveat or non-goal.

Decide in this order:

1. The subject changed during judgment, changed-path coverage is incomplete,
   or author and validator identity or freshness is missing, colliding or
   unattested: NOT_PROVEN.
2. A criterion is proven failed, or a change is proven out of scope: FAIL, even
   when other criteria are unverified.
3. Any in-scope criterion lacks evidence: NOT_PROVEN.
4. Every criterion is verified with evidence, checked scope is nonempty and
   `not_checked` is empty: PASS.

## Establish intent first

An explicit request for Validate, an acceptance verdict or independent proof
that original acceptance is met selects this skill, even when phrased as
"review this". Generic checking or readiness questions, even with criteria
supplied, do not: ask once whether the caller wants advice or an acceptance
judgment, and wait. Issue no verdict or readiness approval meanwhile; missing
intent is not a `NOT_PROVEN` verdict. Shared routing:
[advice or acceptance](../review/references/advice-or-acceptance.md).

## When a fresh judgment is worth it

Spend validation where a mistake is costly. For an ordinary change the author's
checks and CI are the gate, and no fresh judgment is owed. Use Validate when:

- the caller asks for an acceptance verdict or independent proof;
- a mistake cannot be cheaply undone after it lands: a published release or
  instructions users will follow, a security boundary, destroying data or
  tracker state, deleting a check that protects the product; or
- no deterministic check covers the behavior that changed.

Judge once. Report NOT_PROVEN with its gaps and stop; do not request or wait
for another round. After the author repairs findings, the affected checks
confirm the repair; a second judgment happens only when the caller asks for
one. Keep the judgment's cost a fraction of the cost of the work: when it
approaches that cost, stop and return what is unchecked.

## Subject

The subject is a nonempty implementation candidate, held unchanged after
required checks and known repairs; plans, audits and reviews are subjects only
when the caller requested document review. Supplied failed-acceptance evidence
means FAIL on that subject; do not review a moving repair. Bind its identity at
the start and again at the end of judgment:

- With AgentOps installed: `ao provenance manifest --root "$REPO_ROOT" --include "$CHANGED_PATH"`,
  one `--include` per changed path.
- In any Git repository: the commit SHA (`git rev-parse HEAD`) and the changed
  paths (`git diff --name-only <base>...HEAD`); for uncommitted work, the
  `git status --porcelain` listing and a `shasum -a 256` of each changed file.
- A subject supplied only in the conversation, such as a pasted diff or a
  described change, is exactly what was supplied; anything it does not show is
  unverified.

A requested retrospective follows the code judgment and is not evidence for it.
When intent bundles both, judge the code criteria separately and keep the
overall request incomplete until the retrospective exists; issue no overall
PASS early. An explicitly requested review of the retrospective judges that
document on its own scope.

## Identity and freshness

Author and validator identities must be explicit and distinct, and freshness
must be attested by the runtime or the caller, naming the attester. An
attestation is a declared trust fact, not cryptographic isolation. In ordinary
use these count:

- **Author:** the identity the caller gives for whoever produced the candidate:
  a person, a session or agent ID, or the commit author.
- **Validator:** this context's runtime ID when the runtime exposes one, such
  as a subagent or session ID; otherwise the handle the dispatcher holds for
  it, such as the agent ID returned at launch, or "this conversation" when the
  caller opened it for the judgment.
- **Freshness:** a statement from the runtime, the dispatcher or the caller,
  naming who makes it, that this context did not produce the candidate and was
  given intent, subject and evidence rather than the author's working history.
  When the caller opened this conversation for the judgment and supplied the
  candidate, the caller is the attester.

A role name, a persona switch inside the author's conversation, or the
validator vouching for itself does not count. Never invent an identity. An
identity gap makes the result NOT_PROVEN; keep every finding in the report.

## Reviewers

Default to one fresh reviewer in the author's model family: Codex/OpenAI for
Codex/OpenAI, Claude/Anthropic for Claude/Anthropic, on the runtime's
configured capable model unless pinned. Supply task-specific intent, scope,
exact subject and relevant evidence, without full author history, desired
verdict or peer conclusions. Concise input must not omit necessary evidence;
retrieve more source when a criterion requires it.

Cross-model review is opt-in: `--cross-model [model]` is a skill prompt
selection, not an AO flag, adding a fresh other-family reviewer through
[model-dispatch](../agent-native/references/model-dispatch.md). A required leg
that cannot run yields `diversity_unsatisfied` and NOT_PROVEN for the combined
request, even if another leg passed; optional diversity that is unavailable is
disclosed without erasing findings. Delivered FAILs and dissent stand; neither
voting nor model preference makes a split PASS, and agreement is not proof of
truth. No fixed ten-minute cap applies; respect real caller/native bounds
without renewing them. A timeout is missing judgment, not FAIL.

## Judgment

1. Bind the subject. Verify continuity with the exact caller-owned intent,
   cited evidence and complete changed-path coverage; missing integrity is
   NOT_PROVEN.
2. Revisit the original accepted behavior examples, including those in the
   conversation or bead, and check each observable result and its domain
   meaning on the exact candidate. A new test or renamed concept cannot replace
   an unfulfilled scenario. Inspect the actual diff against every criterion;
   publication or provenance claims in docs need verifiable evidence too. Risk
   sets depth: acceptance, permissions, tests and gates, stopping, disclosure,
   hooks and executable controls warrant deeper reading, including prose
   policy. Unknown risk merits examination, not extra reviewers.
3. Classify commands before running any. Regeneration, synchronization,
   formatting and `--force` mutate the subject until proven otherwise; run them
   only on a disposable copy or a committed subject, never the judged tree.
4. Bind the subject again; a mismatch is NOT_PROVEN.
5. Return one result in the shape below, promptly, and stop.

## Report

```text
Verdict: PASS | FAIL | NOT_PROVEN
Subject: <manifest digest, or commit SHA and changed paths>; unchanged start to end: yes | no
Criteria:
  1. <criterion> - verified | failed | not verified - <evidence: file:line, receipt, observed output>
Findings: <class> - <what and where> - <consequence>   (or "none")
Notes (optional, do not change the verdict): <...>
Checked: <what was inspected, and how>
Not checked: <in-scope acceptance not verified>   (empty only for PASS)
Identity: author <id>; validator <id>; freshness attested by <runtime | caller>: <attester>
```

A finding fails an acceptance criterion or would mislead a user, break install
or the CLI, or remove protection for the product; anything else is an optional
note the author may ignore. Give each new finding a short stable `class`,
reused on recurrence, and say whether it is pre-existing, introduced or unknown
from before/after evidence; counts and timestamps alone do not establish cause.
Keep prior findings visible. `not_checked` holds in-scope acceptance that was
not verified; other limits stay in criterion reasoning, declared non-goals or
residual-risk prose, never hidden to obtain PASS. Delivery inside acceptance
stays unverified until its evidence exists; never remove that criterion to
reach PASS. [Mechanics](references/mechanics.md) covers report proportion and
where each scope limit lives.

Validate is the sole semantic author of `verdict.v2`.
Only when the caller requests machine-readable evidence or a declared consumer
requires it, persist through `ao provenance store-verdict`
([mechanics](references/mechanics.md)); Go verifies structure and storage, not
truth. Otherwise return the result through the caller's existing channel,
without hidden machine artifacts. Validate owns no repair, retry, delivery or tracker transition:
known findings go back to the author for direct repair, and a causal stall uses
the RPI single-helper rule.
