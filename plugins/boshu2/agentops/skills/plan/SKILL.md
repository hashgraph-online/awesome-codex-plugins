---
name: plan
description: 'Shape a request into one end-to-end slice with observable behavior; review write scope and reversible decisions. Use when: planning, breaking down or scoping a change.'
practices:
- bdd-gherkin
- design-by-contract
- ddd-bounded-context
hexagonal_role: domain
consumes: []
produces: []
output_contract: 'in-place caller intent update or concise proposed amendment; never an AgentOps planning artifact'
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: execution
  dependencies: []
  capabilities: [shape_intent, define_acceptance, bound_write_scope, resume_discovery]
  effects: [update_intent_source]
  canonical_status: canonical
  disposition: keep
---

# Plan

Shape missing intent into one actionable slice, then stop. A clear change can
proceed directly; load a specialist only for the question it answers.
Prefer the caller's tracker, if any; otherwise use the conversation or
supplied text. Planning produces no AgentOps packet.

## A plan meets these rules

1. **One slice, not a roadmap.** Shape the narrowest change that produces an
   observable result end to end, through every layer it touches. No phases,
   no layer-by-layer breakdown, no backlog: later work stays one coarse line
   each until new evidence makes it the next slice.
2. **An example before any design.** Write at least one Given/When/Then with
   an observable result. Cover the boundary where a mistake is costly to
   undo, such as a repeated or external side effect, lost data or widened
   access, not only the happy path.
3. **Look up facts; ask only for choices.** Read code, docs and the tracker
   instead of asking. Ask the caller at most one question, only for a choice
   no source can answer, with your recommendation and its tradeoff.
4. **The repository's words.** Reuse the term its code, glossary or tracker
   defines; never coin a parallel name.
5. **Scope by consumer.** Name the owners to edit, every live caller and test
   of the changed behavior, and generated companions as a class. Scope is
   authority, not a predicted file count.
6. **A discriminating check:** what fails today and passes after the slice.

## Output

Write this block into the caller's existing intent (tracker item or
conversation). It is the whole plan.

```text
Outcome:  <who observes what, in the repository's terms>
Example:  Given <state>, when <event>, then <observable result>
Slice:    <the one end-to-end change that makes the example true>
Scope:    <owners>; consumers: <live callers and tests>; generated: <class> | none
Check:    <the test or observation that fails now and passes after the slice>
Question: <one caller choice, your recommendation, its tradeoff> | none
Later:    <deferred item and the evidence that would make it next> | none
```

Add an Example line only for another consequential boundary, and a non-goal
only where it prevents a plausible scope mistake.

## Workflow

1. Read the accepted intent, any existing plan or native handoff, and the
   relevant source owners and active constraints. Reuse the
   acceptance already supplied in the conversation or bead; clarify only what
   prevents action or judgment. To resume or replace another context, hand a
   slice on, plan code together with a requested retrospective, or keep an
   exact snapshot of conversation intent, follow
   [resume and handoff](references/resume-and-handoff.md).
2. Route only the uncertainty that could change the slice (table below).
3. Fill the block. A mechanical cross-cutting migration that cannot stay
   working slice by slice uses expand, migrate, contract and states where
   integration is required. Include recapture of affected bound evidence where
   necessary; in repositories with AgentOps provenance bindings,
   `ao provenance evidence-orphans` finds it. Across an epic,
   [Navigate](../navigate/SKILL.md) picks the next bead; Plan shapes that bead.
4. When evidence disproves an approach, keep the failed assumption, its
   evidence and the revised check in the existing intent. An approach change
   within accepted outcome and scope needs no new permission; acceptance or
   scope expansion needs the caller. Never relabel a failed acceptance
   condition as a caveat to obtain green.

Stop planning once the implementer can act and the validator can judge. More
research, decomposition or review must resolve a named remaining uncertainty;
reserve capacity for implementation, integration and repair.

## Route uncertainty

| Uncertainty | Next action |
|---|---|
| Fact a source can answer | Inspect the smallest authoritative source and cite it. [Research](../research/SKILL.md) owns deeper tracing; [Domain](../domain/SKILL.md) owns disputed vocabulary. Never ask the caller to recite it. |
| Caller choice | Recover existing authorization first. What remains is the one question, with its concrete tradeoff; an agent cannot supply the caller's answer. |
| Assumption only an observation can settle | State the competing predictions and the smallest observation that separates them, using an optional [probe or prototype](references/ground-truth-routing.md). A persuasive design or an agent vote cannot settle unobserved behavior. |
| Safely deferred | Put it under Later with the event or evidence that would make it relevant. Deferral cannot hide an unanswered acceptance condition. |

Resolve reversible implementation details within accepted scope. Mark
inference and missing evidence; never promote either into a source fact or a
settled caller choice. For consequential uncertainty that survives source
checks and observation, an optional [challenge](references/challenge.md)
returns advice or a next discriminator, never permission or acceptance.
[Memory recall](../memory/references/recall.md) helps only when prior
evidence could change the next action.

## Who decides

Use real undo cost, affected users and existing authority. A material
irreversible choice outside that authority goes to the caller; prior
authorization stays valid. Reviewer agreement is evidence, not permission to
replace the caller's intent: explain a consequential disagreement and its
support instead of silently changing acceptance. A proposed process artifact
needs a concrete consumer, the decision it gates, an observed defect and a
retirement condition; otherwise omit it.

## Examples and naming

An example can be plain text; BDD needs no `.feature` file or interview. In a
repository that calls queued work a **Job**:

> Given a Job has already completed, when the worker receives it again,
> then its completed result is returned and its side effect is not repeated.

Write "Job", not a parallel label such as "task item". Keep the accepted
example available to Implement and Validate; tests added after coding may
supplement it but cannot redefine what was promised. For product planning,
separate demonstrated behavior from aspiration; an ordinary feature needs no
product document.

## Scope

Use normalized repository-relative scope patterns. An uncovered live consumer
needs a concise exact-file amendment to the caller; continue independent
in-scope work meanwhile. Generated companions already in scope need no extra
permission. [Boundaries](../rpi/references/boundaries.md) keep work and status
in the caller's tracker and delivery under repository policy.
