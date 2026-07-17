---
name: implement
description: Execute one bounded RED to GREEN experiment
---
# Implement

Execute exactly one bounded experiment described by the resolved bead or caller
intent. Implement owns subject edits and factual evidence. It does not create a
second planning record or a model-authored candidate packet.

## Workflow

1. Read the intent, acceptance, and scope from their existing source. A runtime
   may snapshot and hash that source automatically for drift detection.
2. Run the declared first acceptance check before changing behavior. RED-first
   applies only when acceptance is behavioral: preserve evidence that the check
   fails for the expected missing behavior. Relocations, doc merges, and pure
   refactors need no failing-check ritual — record an honest green pre-change
   baseline instead.
3. Make the smallest in-scope change that satisfies the active behavior.
4. Run the targeted acceptance checks and capture factual results.
5. Refactor only while those checks stay green. Refactoring does not change the
   acceptance test.
6. Have the runtime derive actual changed paths and `subject-manifest.v1` from
   the before/after subject. Do not make the model transcribe those facts.
7. Return the manifest digest, author context ID, and exact check receipts in the
   response or runtime channel. Stop.

Specialists such as standards, domain, test, refactor, and security may provide
advice. They are never hard dependencies and cannot add lifecycle authority.

## Evidence proportionality

During edits, run the smallest deterministic checks that can falsify the active
change. Reuse exact-input receipts when their subject and tool identity still
match. Run an expensive full-suite check at the integration boundary, or
earlier only when the intent explicitly makes it the first acceptance check.
Repeatedly replaying the full suite after every focused edit adds latency, not
proof.

## Scope conflict rule

On discovering a live consumer of the change outside the declared write scope
— a test asserting the old path, a generated twin, a gate reading the moved
file — stop and report the exact file and line to the caller. Do not silently
expand scope to absorb it. One repair revision of the intent is the maximum
before escalating to the caller; the 2026-07-15 heal-skill fold took three
intent revisions (lineage under `.agents/ao/intents/sha256/26a4f2be...eb48`)
because hand-enumerated scope kept missing live consumers.

Before declaring GREEN, self-audit the diff for mocks, placeholders, TODO
stubs, and hardcoded fixture values standing in for real behavior. A check
that passes against a placeholder is not evidence for the acceptance
criterion; either finish the behavior or report it as not built.

## Boundary

- Do not commit, push, claim, close, release, land, reserve, retry, or invoke a
  semantic validator.
- Do not silently expand acceptance. A different acceptance contract is a new
  intent for a caller to start separately.
- A failed check is evidence for the caller, not permission to create a packet
  or validation loop.
