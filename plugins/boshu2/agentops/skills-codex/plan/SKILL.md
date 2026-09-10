---
name: plan
description: 'Shape or refine the existing bead or caller intent in place. Triggers: "plan", "discover and plan", "shape this goal", "review write scope", "check scope boundaries", "scope this change".'
---
# Plan

Shape only missing intent. Prefer the caller's tracker, if any; otherwise use
the conversation or supplied text. Planning produces no AgentOps packet.
A clear change can proceed directly.

## Workflow

1. Read accepted intent and relevant source owners and active constraints.
   Resolve only consequential uncertainty; do not reopen settled decisions
   without new evidence. Identify the caller-visible outcome, scope and first
   useful check.
2. Clarify missing acceptance examples and non-goals in that existing source.
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
