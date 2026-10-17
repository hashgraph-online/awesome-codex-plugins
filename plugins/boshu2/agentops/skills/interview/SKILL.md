---
name: interview
description: 'Interview you one question at a time, each with a recommendation, to settle a big outcome before agents work alone. Use when: selected by name.'
practices: [bdd-gherkin, ddd-bounded-context, design-by-contract]
hexagonal_role: domain
consumes: [repo-context, native-work-state]
produces: [caller-outcome, goal-acceptance]
context_rel:
- kind: supplier-to
  with: craft-goal
skill_api_version: 1
user-invocable: true
disable-model-invocation: true
metadata:
  tier: execution
  dependencies: []
  capabilities: [interview_caller, settle_caller_choices, write_acceptance_examples, settle_domain_terms]
  effects: [update_intent_source]
  canonical_status: canonical
  disposition: keep_strategy
  stability: stable
output_contract: 'one question per turn with a labeled recommendation and tradeoff; decided, terms, open and deferred lists the caller can see; settled decisions appended to the existing intent source within authority; a handoff to Craft Goal, RPI or Plan'
---

# Interview

Shape a big outcome with the caller, one question per turn, before agents run
alone. You look up facts; the caller makes choices. **Why:** answering shapes
the caller's thinking, and control is highest before launch. Interview creates
nothing new (no goal, bead or file) and changes no status, claim or closure;
within authority it only appends settled notes to an existing intent source
(see [Show the state](#show-the-state)).

## Each turn

1. **Look it up** in the tracker, docs and code first. Ask only for choices:
   outcome, proof, non-goals, authority, budgets, priorities, risk tolerance.
2. **Pick the branch.** Start with the outcome, then the open branch that most
   changes acceptance, scope or authority. Defer any that change no decision.
3. **Ask one question** in this shape, so the caller can accept, amend or
   reject in one line. Wait for the answer.
4. **Record** only what the caller decides. A skip stays open; "your call"
   accepts the recommendation shown. A revision reopens dependent answers.

```text
Q<n>: <the decision>. <the question, with 2 to 4 options when they exist>
My recommendation: <answer>, because <source or reason>.
Tradeoff: <the one cost that matters>
```

## Answerer

The caller answers by default. On request ("let a council answer my
interview"), a council answers through [Council](../council/SKILL.md)'s
interview-panel mode; the caller accepts or amends its answers in one pass
before anything is recorded, and authority, budgets and acceptance changes
stay the caller's.

## BDD: acceptance as examples

Drive each criterion to a Given/When/Then with an observable result and its
proving evidence. Draft the example yourself as the recommendation; the caller
accepts or edits it. "Works reliably" is not acceptance; ask what would be seen.

```gherkin
Given a Job has already completed
When the worker receives that Job again
Then it returns the completed result without a second side effect
# Proof: a redelivery test asserts one side effect and the completed result
```

## DDD: one term per concept

When a word is vague, overloaded or has synonyms, ask which term the domain uses.
Record one term with a one-line definition and use only it in examples, notes,
code and tests. [Domain](../domain/SKILL.md) owns deeper modeling.

## Show the state

Open each turn with one line: what just settled and how many choices stay
open. Show these lists on request, after a revision and at stop:

- **Decided:** each choice; acceptance carries its Given/When/Then and proof.
- **Terms:** each settled term with its one-line definition.
- **Open:** unanswered choices, most consequential first.
- **Deferred:** choices that change no next decision, and what revives them.

Within authority, append settled decisions and terms to the intent source
(root epic, issue or conversation), and Open and Deferred at stop. If a goal
already runs on that epic, do not append a changed criterion or term; list it
under Open as an acceptance change so the caller can hold and re-craft first. In BD:

```bash
bd context --json    # confirm the destination before any write
bd show <epic-id>    # on resume: reuse settled notes, start from Open
bd update <epic-id> --append-notes "decided: <choice> | example: <Given/When/Then>"
```

## Stop and hand off

Stop when the caller stops, the next question would only restate a settled
answer, the work proves to be one slice, or Craft Goal admission is decided:

1. outcome and non-goals;
2. terminal acceptance, each criterion with its proving evidence;
3. authority: reads, writes, external effects, Git, and when agents must ask;
4. budgets: numeric limits per wave of work and for the whole goal, which
   nothing renews, and how many results that change no decision trigger HOLD
   (implementation stops for causal review);
5. the first falsifiable question.

Hand over the lists; the caller starts the next step: Craft Goal for several
related experiments, RPI or [Plan](../plan/SKILL.md) for one outcome with
items 1 to 3 and real bounds. Open items stay open; never fill one to finish.
