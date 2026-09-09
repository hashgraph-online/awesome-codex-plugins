---
name: plan
description: 'Shape or refine the existing bead or caller intent in place. Triggers: "plan", "discover and plan", "shape this goal", "review write scope", "check scope boundaries", "scope this change".'
---
# Plan

Shape only what is missing from the authorized intent. Prefer the caller's tracker, if any;
otherwise use the caller's conversation or supplied text. A clear trivial change
needs no planning worksheet or separate Plan dispatch. Planning produces no AgentOps packet.

## Workflow

1. Read the actual intent, relevant source owners and active constraints. Find
   the caller-visible outcome, allowed write scope and first useful check.
   Inspect only enough context to resolve a consequential uncertainty.
2. Where needed, clarify acceptance examples, important non-goals and scope in
   the existing source. Include generated companions as a class: hand-edited
   sources plus every output of the owning regeneration commands. Include tests
   and live consumers that must change with them. Scope is authority, not a
   prediction of an exact file count.
3. Choose the smallest acceptance-advancing action or discriminating check.
   Identify evidence the change could invalidate and include recapture where
   required. Use `ao provenance evidence-orphans` for affected bound evidence;
   avoid a mandatory ledger or taxonomy for changes that do not need one.
4. Revise the approach when evidence disproves an assumption under unchanged
   accepted outcome and scope. Record the disproved assumption, evidence and
   revised check briefly in the existing source or handoff. No new permission
   is needed for this approach revision. Changing acceptance or expanding scope
   needs caller authority; never quietly weaken the original check.
5. When another context needs the intent, pass enough exact source and references
   to act without the author's private reasoning. The runtime binds accepted
   intent for final validation; useful approach notes are separate from frozen
   acceptance so revising a hypothesis does not fabricate acceptance drift.

A plan is sufficient when the implementer can act and the validator can judge.
Then stop planning and implement. Specialists and
[ground-truth routing](references/ground-truth-routing.md) are optional tools for
consequential integration or design uncertainty, not universal worksheets.
[Memory recall](../memory/references/recall.md) is useful only when applicable
prior experience may change this work's next action.

## Identity and scope

Use the runtime's source reference and digest for exact accepted intent. For
conversation-only intent, existing `ao provenance snapshot-intent --source -
--evidence-root <explicit-root>` stores resolved bytes in a caller-selected
protected external non-Git evidence directory. Missing routing does not authorize
a workspace fallback or a second plan artifact. Preserve legacy proof.

Scope patterns are normalized repository-relative paths, cover the behavior,
and include generator-owned companions without granting unrelated directories.
A live consumer outside accepted scope needs a concise exact-file amendment to
the caller; continue independent authorized work while that decision is pending.
[Boundaries](../rpi/references/boundaries.md) keep work/status in the caller's
tracker and Git/delivery under repository policy.

## Prompt

```text
Use Plan to resolve the uncertain parser interface for this accepted change.
Keep acceptance and scope; use a real consumer check to test the assumption.
Revise the approach if it fails, then implement. No new planning artifact.
```

## It's working if

A clear small change skips planning paperwork. A falsified assumption changes
the approach and the next check; it does not trigger another approval round
unless outcome or scope changes. Generated outputs remain in scope and the
existing intent gives a fresh implementer enough information to act.
