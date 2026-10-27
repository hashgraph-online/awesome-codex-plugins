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
  triggers: ["write scope", "scope boundaries"]
---

# Plan

Shape missing intent into one actionable slice, then stop. A clear change can
proceed directly; load a specialist only for the question it answers.
Prefer the caller's tracker, if any; otherwise use the conversation or
supplied text. Supplied advice, such as an [Idea Genie](../idea-genie/SKILL.md)
portfolio or challenge, is evidence to weigh, never a decision.

## A plan meets these rules

1. **One slice, not a roadmap.** Shape the narrowest change that produces an
   observable result end to end, through every layer it touches. No phases,
   no layer-by-layer breakdown, no backlog: later work stays one coarse line
   each until new evidence makes it the next slice. When several slices could
   go first, prefer the smallest observable path that tests the approach's
   riskiest dependency. Outcomes that are each useful and checkable alone are
   separate plans, not slices: unless the request, the tracker or Navigate
   already settles which comes first, ask (rule 3) and keep the rest under
   Later. Named providers, devices or data
   sources are coverage of one outcome; separate them only when no shared path
   can meet a named requirement, and keep parts together when specifying one
   alone would mean guessing behavior it shares with another. Name any
   stand-in and what it cannot establish; a demonstration with that stand-in
   is not proof of the real integration.
2. **An example before any design.** Write at least one Given/When/Then with
   an observable result. Cover the boundary where a mistake is costly to
   undo, such as a repeated or external side effect, lost data or widened
   access, not only the happy path.
3. **Look up facts; ask only for choices.** Read code, docs and the tracker
   instead of asking. Ask the caller at most one question, only for a choice
   no source can answer, with your recommendation and its tradeoff. When
   several choices compete for it (which outcome comes first, a rule 7
   conflict, a recorded decision under [Who decides](#who-decides)), ask the
   one that most changes the slice and list each other under Later with what
   it would change. If several block acceptance,
   [Interview](../interview/SKILL.md) settles them one per turn.
4. **The repository's words.** Reuse the term its code, glossary or tracker
   defines; never coin a parallel name.
5. **Scope by consumer.** Name the owners to edit, every live caller and test
   of the changed behavior, and generated companions as a class, as
   repository-relative patterns. Scope is authority, not a predicted file
   count: a live consumer outside it goes to the caller as an exact-file
   amendment, while independent in-scope work continues.
6. **A discriminating check:** what fails today and passes after the slice.
7. **Unrequested mechanisms earn their place.** A guard, retry, fallback,
   option or abstraction nobody asked for joins the slice only when a contract
   requires it, when without it a traced failure would go unseen by anyone
   able to fix it in time, or when adding it later is costly: persisted data
   or formats, interfaces others depend on, payments, security. Use its
   smallest form and judge each add-on the same way; when unsure, leave it out
   and name it under Later with the evidence that would require it. If
   a failure of the slice would reach no one who can act, making it visible is
   part of the slice. No safeguard narrows requested behavior; a real conflict
   is the Question.

## Output

Write this block into the caller's existing intent when the request or
existing authorization covers editing it (the conversation always does);
otherwise return it as a proposed amendment. It is the whole plan.

```text
Outcome:  <who observes what, in the repository's terms>
Example:  Given <state>, when <event>, then <observable result>
Slice:    <the one end-to-end change that makes the example true>
Scope:    <owners>; consumers: <live callers and tests>; generated: <class> | none
Check:    <the test or observation that fails now and passes after the slice>
Question: <one caller choice, your recommendation, its tradeoff> | none
Later:    <deferred item and the evidence that would make it next> | none
```

Add an Example line only for another consequential boundary, an Open line for
a fact only a named person holds (with the drafted questions), and a non-goal
only where it prevents a plausible scope mistake.

## Workflow

1. Read the accepted intent, any existing plan or native handoff, and the
   relevant source owners and active constraints. Reuse the
   acceptance already supplied in the conversation or bead; clarify only what
   prevents action or judgment. To resume, hand a slice on, pair code with a
   retrospective or snapshot intent, follow
   [resume and handoff](references/resume-and-handoff.md).
2. Route only the uncertainty that could change the slice (table below).
   If an interface choice drives that uncertainty, use the conditional
   [caller-first design comparison](references/ground-truth-routing.md#compare-interfaces-from-the-callers-side)
   before committing to a boundary.
3. Fill the block. If a behavior-preserving restructuring would make the
   slice much smaller, name it on the Slice line as a precondition through
   [Refactor](../refactor/SKILL.md), with its own before-and-after check
   separate from the Check line, and keep it out of the slice's diff. A
   mechanical cross-cutting migration that cannot stay working slice by slice
   uses expand, migrate, contract and says where integration is required. If
   recorded evidence (scorecards, fixtures) is bound to files the slice
   changes, plan its recapture; with the `ao` CLI, which the plugin does not
   ship, `ao provenance evidence-orphans --root <repo-root> --changed <path>`
   lists those bindings. Across an epic, [Navigate](../navigate/SKILL.md)
   picks the next bead; Plan shapes that bead.
4. When evidence disproves an approach, keep the failed assumption, its
   evidence and the revised check in the existing intent, under the same
   authority as the Output write below. An approach change
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
| Fact only a named other person holds | Name the person and draft the few questions the gap needs, most consequential first, one idea each, with enough context to answer; return them with the plan, and the caller decides whether and how to send them. The item stays open until answered; never guess it or recast it as a caller choice. |
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
irreversible choice outside that authority goes to the caller, as does a slice
that would cut against a recorded decision such as an ADR, a published
contract or a declared non-goal: name that decision and the evidence for
reopening it as the Question, and keep the slice within it until the caller
answers. Prior authorization stays valid. Reviewer agreement is evidence, not
permission to replace the caller's intent: explain a consequential
disagreement and its support instead of silently changing acceptance. A
proposed process artifact needs a concrete consumer, the decision it gates, an
observed defect and a retirement condition; otherwise omit it.

## Example

An example can be plain text; BDD needs no `.feature` file or interview. In a
repository that calls queued work a **Job** (write "Job", not "task item"):

> Given a Job has already completed, when the worker receives it again,
> then its completed result is returned and its side effect is not repeated.

Tests added after coding may supplement the accepted example but cannot
redefine what was promised.
