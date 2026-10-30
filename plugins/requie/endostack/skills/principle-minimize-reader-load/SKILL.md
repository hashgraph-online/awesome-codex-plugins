---
name: principle-minimize-reader-load
description: Use when shaping or reviewing code that is hard to follow, deciding whether new indirection or state is worth it, or writing output for people. Reduce the indirections and hidden mutable state a reader has to track.
disable-model-invocation: true
---

# Minimize reader load

Measure maintainability by how hard a reader must work to understand the code. Two separate axes set that effort: the number of hops between a question and its answer, and the amount of hidden or changeable state the reader has to keep in mind.

## When it applies

Reviewing or shaping hard-to-follow code, deciding whether new indirection or new state is justified, and writing anything people will read, including verdicts and reports. It is a lens you always hold, not a procedure with preconditions.

## What to do

1. Treat line counts, cyclomatic complexity, and architectural tidiness as proxies. Reader effort is the target.
2. Guard both axes. They vary independently. A flat file full of globals can be as hard to read as a deep stack of adapters.
3. Delete layers whose cost exceeds their benefit: wrappers with one caller, interfaces with one implementation, and indirection added for a future that never came. Inline them.
4. Require each layer to change the abstraction. A layer that forwards the same methods with the same arguments is pass-through, so collapse it.
5. Prefer interfaces that hide meaningful decisions. A broad interface that conceals little forces readers to learn its surface and its internals as well.
6. Narrow the scope of state. From most to least preferred: pure functions that return values instead of mutating, then local variables, then object fields, then module-level state, and globals last. Compute values instead of keeping copies synchronized.
7. State each invariant one time, where data enters, and let consumers rely on it.
8. Any new indirection or state must remove at least as much reader load somewhere else as it introduces.
9. Apply the half-minute test: a newcomer should be able to say where a value comes from and what can change it in about thirty seconds.

Reader load is a security property. A permission check that a reviewer has to trace through four decorators and a mutable global request context is a check that reviewers stop verifying. An authorization decision a reader can find and confirm in one function is one they will actually audit.

## The failure it prevents

Deep wrapper stacks, hidden global state, and invariants restated in every consumer.

## Done when

The half-minute test passes.

[principle-guard-the-context-window](../principle-guard-the-context-window/SKILL.md) is the agent analog of this principle.

Related: [principle-guard-the-context-window](../principle-guard-the-context-window/SKILL.md), [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md), [principle-boundary-discipline](../principle-boundary-discipline/SKILL.md).
