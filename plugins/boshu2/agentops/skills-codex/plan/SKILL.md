---
name: plan
description: 'Shape or refine the existing bead or caller Triggers: "plan", "discover and plan", "shape this goal".'
---
# Plan

Turn the caller's intent into one bounded, testable behavior in the place that
already owns the work. Prefer the caller's tracker, if any. When no durable
tracker or issue reference is available, use the caller's conversation or
supplied text; the runtime snapshots those resolved intent bytes so later
contexts can read and hash the same source. Do not make the model restate those
facts in a packet.

## Workflow

1. Resolve the intent source and choose one active behavior. When that source
   is not already durable, have the runtime pass its exact bytes to the
   validate skill's `scripts/validate.py snapshot-intent --source -`, resolved
   relative to wherever that skill package is installed (a repo checkout:
   `skills/validate/scripts/validate.py`; an installed skill package:
   `.agents/skills/validate/scripts/validate.py`), and use the returned
   `intent_ref` for later phases.
2. Route the work by type (see **Ground-truth routing**) and name its ground
   truth first. Then inspect only enough real context to make paths, interfaces,
   and evidence concrete: hydrate only the context sources this decision needs
   and carry their citations forward. Existing research and specialist skills
   are advisory inputs, never a merged context store.
3. Ensure the source contains acceptance examples, important non-goals, and the
   allowed write scope. Use lightweight prose or Given/When/Then only where it
   removes ambiguity; do not require both normal and edge ceremony for every
   change.
4. Name the first useful acceptance check.
5. If authorized and the source is writable, update that bead or issue in
   place. Otherwise return a concise proposed amendment to the caller.

Planning produces no AgentOps packet. A durable caller-owned source stays in
place; the runtime carries its reference and the digest of its exact resolved
bytes to detect later acceptance drift. Only when no durable source exists does
the runtime store those bytes under their digest as a content-addressed
snapshot. That fallback is derived automatically and is not another
model-authored planning artifact.

Bound the work around the caller-visible outcome, not individual files, gates,
or reviewer comments. Decomposition is useful only when it reduces reasoning
cost; it must not multiply invocations or proof artifacts.

## Scope admission

In a repository with generated projections, write scope names generator-owned
outputs as a class — the hand-edited sources plus all outputs of the owning
regen commands — never as a hand-enumerated path list. Hand enumeration is
falsified the first time a regen command rewrites a companion the author did
not list: the 2026-07-15 heal-skill fold burned two implement lanes and three
intent revisions (`.agents/ao/intents/sha256/d1db59d4...2b81` superseded by
`f5fd7c3c...af75` superseded by `26a4f2be...eb48`) before scope was restated
as a class.

Before freezing acceptance, run a complexity admission: enumerate the
generated companions, parity twins (for example a `skills-codex/` mirror), and
test files that assert on the paths being changed. Anything this pass finds
that the scope does not admit will surface later as an out-of-scope diff or a
broken gate.

## Ground-truth routing

Every plan needs a ground truth outside the planner's own reasoning. Before
freezing acceptance, classify the work and name its ground truth, its control
experiment, and its deviation ledger from the row below.

| Work type | Ground truth | Control experiment | Deviation ledger |
|---|---|---|---|
| Integrate an external substrate, runtime, tracker, or service | the vendor's own docs plus stock behavior | run their vanilla quickstart on pinned versions with zero local code, before designing | each deviation from the documented flow, each justified; and every component you write that has a native counterpart in the substrate |
| Extend this project | the repo's existing patterns and behavior spec | the simplest version that satisfies acceptance, and why it is insufficient | each novelty introduced — new abstraction, dependency, or pattern |
| Greenfield | reference experience and domain prior art | a walking skeleton | each deviation from the boring default, ~one novelty per change |

The Extend row is already the repo's default discipline: behavior-first
acceptance, RED -> GREEN, the smallest real change. The Integrate row is the one
that is cheap to skip and expensive to have skipped — run the stock control
experiment *before* you design, or you will re-plumb what the substrate already
documents and inherit bugs you built yourself.

Trigger: the Integrate-row mechanics — the stock-quickstart control run and the
deviation ledger from the documented flow — apply only to integration-class work
(adopting or wiring in an external substrate, runtime, tracker, or service).
Routine feature work on this project uses the Extend row and does not incur them.

A plan is done only when it passes the fresh-context test: a cold context,
given the intent source alone, could execute it without the author's
conversation. If execution needs facts that live only in the planning
conversation, move them into the source before freezing.
