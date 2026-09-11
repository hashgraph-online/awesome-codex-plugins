---
name: plan
description: 'Define intended behavior, review write scope and assess reversible decisions. Use when: acceptance or approach is unclear before coding; stop once actionable.'
---
# Plan

Shape only missing intent. Prefer the caller's tracker, if any; otherwise use
the conversation or supplied text. Planning produces no AgentOps packet.
A clear change can proceed directly. Use established domain names throughout
intent, examples, code and validation; [Domain](../domain/SKILL.md) helps when
meanings or boundaries are genuinely unclear.

## Workflow

1. Read accepted intent and relevant source owners and active constraints.
   Resolve only consequential uncertainty; do not reopen settled decisions
   without new evidence. Identify the caller-visible outcome, scope and first
   useful check.
2. Describe the intended observable behavior before implementation. Reuse
   acceptance already supplied in the conversation or bead; clarify only what
   prevents action or judgment. Name the actor or caller, the event and the
   observable result. One example often suffices; use Given/When/Then for
   branching behavior and consequential boundaries. Include non-goals only
   where they prevent a plausible scope mistake in that existing source.
   Scope includes the hand-edited owners, affected tests/live consumers and
   generator-owned companions as a class; it is authority, not a predicted
   file count. A consequential assumption deserves an early discriminating
   check, not a general checklist or exhaustive survey.
3. Choose the smallest action that advances acceptance or falsifies the risky
   assumption. Include recapture of affected bound evidence where necessary;
   use `ao provenance evidence-orphans` when applicable, not a mandatory ledger.
4. When evidence disproves an approach, briefly retain the failed assumption,
   evidence and revised check in the existing intent or handoff. Approach
   changes within accepted outcome and scope need no new permission; acceptance
   or scope expansion requires caller authority. Never relabel a failed
   acceptance condition as a caveat to obtain green.
5. Give another context exact intent references and the evidence it needs to
   act. Keep approach notes separate from frozen acceptance. Do not transmit
   the entire research history when a focused source reference will suffice.

Stop planning once the implementer can act and the validator can judge. More
research, decomposition or review must resolve a named remaining uncertainty.
Specialists and [ground-truth routing](references/ground-truth-routing.md) are
optional. [Memory recall](../memory/references/recall.md) is useful only when
prior evidence could change the next action.

## Behavior and naming

An example can be plain text; BDD does not require a `.feature` file or an
interview. For example, in a repository that calls queued work a **Job**:

> Given a Job has already completed, when the worker receives it again,
> then its completed result is returned and its side effect is not repeated.

Use the actual domain term instead of inventing a parallel label such as
"task item." Identify what the caller can observe and the smallest check that
distinguishes the desired behavior from the current failure. Keep the accepted
example available to Implement and Validate. Tests added after coding may
supplement it; they cannot redefine what was promised.

For uncertain designs, probe the assumption that could change the approach.
For product planning, distinguish demonstrated behavior from aspiration and
refine the existing product owner only within the request. A product document
is not required for an ordinary feature.

## Decision cost and stopping

Use real undo cost, affected users and existing authority when choosing who
must decide. Resolve reversible implementation details within accepted scope.
A material irreversible choice outside that authority needs the caller; prior
authorization remains valid. Reviewer agreement is evidence, not permission
to replace the caller's intent. Explain a consequential disagreement and its
support rather than silently changing acceptance.

A proposed process artifact earns its cost only with a concrete consumer,
subject or release decision, observed defect and retirement condition. If the
next action adds only ceremony or repeats settled evidence, omit it. Stop when
the implementer can act and the validator can judge, reserving capacity for
implementation, integration and repair.

This guidance adapts the intent-first approach in
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills)
using AgentOps' existing intent and evidence contracts.

## Identity and scope

Use runtime-derived source identity and digest. If conversation intent needs
an exact snapshot, existing `ao provenance snapshot-intent --source -
--evidence-root <explicit-root>` uses caller-selected protected external
non-Git storage. Missing routing permits neither workspace fallback nor a
second planning artifact. Preserve legacy proof.

Use normalized repository-relative scope patterns. An uncovered live consumer
needs a concise exact-file amendment to the caller; continue independent
in-scope work meanwhile. Generated companions already in scope need no extra
permission. [Boundaries](../rpi/references/boundaries.md) keep work/status in
the caller's tracker and delivery under repository policy.
