---
name: plan
description: Shape or refine the existing bead or caller
---
# Plan

Turn the caller's intent into one bounded, testable behavior in the place that
already owns the work. Prefer the caller's tracker, if any. When no tracker is
available, use the caller's conversation or supplied issue text; the runtime
snapshots the resolved intent bytes automatically so later contexts can read
and hash the same source. Do not make the model restate those facts in a packet.

## Workflow

1. Resolve the intent source and choose one active behavior. When that source
   is not already durable, have the runtime pass its exact bytes to
   `python3 skills/validate/scripts/validate.py snapshot-intent --source -` and
   use the returned `intent_ref` for later phases.
2. Inspect only enough real context to make paths, interfaces, and evidence
   concrete. Existing research and specialist skills are advisory inputs.
3. Ensure the source contains acceptance examples, important non-goals, and the
   allowed write scope. Use lightweight prose or Given/When/Then only where it
   removes ambiguity; do not require both normal and edge ceremony for every
   change.
4. Name the first useful acceptance check.
5. If authorized and the source is writable, update that bead or issue in
   place. Otherwise return a concise proposed amendment to the caller.

Planning produces no AgentOps packet. The runtime stores and hashes the resolved
source bytes to detect later acceptance drift. That content-addressed snapshot
is derived automatically and is not another model-authored planning artifact.

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

A plan is done only when it passes the fresh-context test: a cold context,
given the intent source alone, could execute it without the author's
conversation. If execution needs facts that live only in the planning
conversation, move them into the source before freezing.
