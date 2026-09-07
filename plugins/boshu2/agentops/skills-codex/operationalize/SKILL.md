---
name: operationalize
description: 'Distill repeated, evidence-backed expertise Triggers: "operationalize this", "turn this expertise into a reusable capability".'
---
# Operationalize

Turn repeated, cited expertise into a proposal for a reusable artifact.

1. Require cited evidence for the expertise: real occurrences or an explicit
   authoritative source, subject to the three-instance floor below when the
   proposal abstracts a rule.
2. State the triggering situation, desired behavior, inputs, outputs, negative
   examples, and evidence.
3. Apply the process-artifact creation gate before choosing a shape. A proposed
   certificate, ledger, dashboard, matrix, meta-report, readiness review,
   speculative check, skill, or workflow must name its concrete consumer, the
   subject or release decision it gates, the observed defect class justifying
   it, and its deletion condition. Code or process introduced solely to consume
   the artifact does not qualify. If any answer is missing, propose no artifact
   and redirect to the caller-requested subject. Minimal integrity or recovery
   state is allowed only when necessary to prevent a named evidence-loss or
   corruption mode.
4. Choose the smallest fitting shape: reference, skill, deterministic check, or
   caller-owned workflow.
5. Search existing capabilities and prefer extension over duplication.
6. Provide an activation example, holdout/negative example, owner, and rollback
   or deletion condition.
7. Return the proposal inline to the caller or an authoring specialist. When
   the caller asks for a durable artifact, write it under
   `.agents/scratch/operationalize/` first and return the path; the proposal
   is advisory either way.

## Three-instance floor

A rule needs three real occurrences before it may be abstracted. Count only
occurrences that actually happened and can be cited — sessions, diffs,
verdicts, or artifacts that resolve in this repository — not hypothetical
cases or restatements of one event. With one or two occurrences, propose a
quote-anchored reference note instead and stop short of a rule. An explicit
authoritative source may substitute for occurrences only when the proposal
transcribes that source rather than generalizing beyond it. The named failure
mode is premature abstraction: a rule minted from a single vivid incident
that encodes the incident's accidents as policy.

## Reapply proof

Every proposed rule carries a reapply proof: a demonstration that the rule,
as written, reproduces the correct decision on at least one of its source
occurrences without extra context. If applying the drafted rule to its own
source moment requires unwritten judgment, the rule is not yet operational —
tighten the wording until the reapply succeeds, or downgrade the proposal to
a reference. When the proposal creates process, the reapply proof must also
show that the creation gate returns the correct create-or-drop decision. No
reapply proof, no rule.

## Quote-bank anchors

Tie each rule to its source moments with a quote bank: for every counted
occurrence, a short verbatim quote or command/output excerpt plus a locally
resolving citation (repo path, `.agents/ao` digest, or session artifact). An
occurrence that cannot be quoted and cited does not count toward the
three-instance floor. Anchors let a later reader test whether the rule still
matches what actually happened, instead of trusting the abstraction.

## Boundary

Operationalize does not create tracker work, promote policy, start a factory,
validate its own output, or control another invocation. The proposal is
advisory: adopting it into a skill, deterministic check, reference, or
workflow is a separate, caller-selected step — `skill-builder`,
`workflow-builder`, or a fresh RPI — never performed here. The proposal
cannot promote itself, and process-only output earns no capability credit.
