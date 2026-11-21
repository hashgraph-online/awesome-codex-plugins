---
name: principle-separate-before-serializing-shared-state
description: Apply when parallel agents, workers, or processes might write the same key, file, state object, or branch. Start by giving each writer its own target, and add locking only where the design truly requires one shared target.
disable-model-invocation: true
---

# Separate before serializing shared state

If concurrent actors could write to one piece of state, eliminate the sharing before anything else. Add structural serialization only when having a single shared target is a real invariant. A written agreement such as "agents should not both edit this file" provides no concurrency control.

## When it applies

Concurrent actors (processes, workers, agents, parallel subagents) that could write to a common key, file, branch, or state object. Sharing that is read-only is exempt.

## What to do

1. List the shared mutable state: files, branches, keys, and APIs more than one actor writes.
2. By default, give each actor its own write target (its own file, key, branch, state directory, or worktree), and combine results only at the boundary where they are read or reported. Decide whether the actors truly require a single canonical object or are each publishing facts that do not depend on one another. Two workers each updating their own field inside one shared JSON file is still shared mutation. Two separate files are not.
3. Only if one shared target is a true invariant, serialize with structure: a lock file, sequential phases, a single-writer actor that owns the target, or an atomic compare-and-swap.
4. If you feel you need a lock, take that as a sign to examine the design before you add one.

For parallel coding subagents, give each its own worktree or checkout. If the agent has no worktree isolation, give each delegate a disjoint set of files and say so in the brief, or run them one after another.

Shared writable state is also an injection path: a subagent that read a hostile web page and writes to a notes file the coordinator reads passes the attacker's text upward. Separate targets let you choose which outputs to trust.

## The failure it prevents

Intermittent races that are hard to reproduce, and agents overwriting each other's work.

## Done when

Each writer owns its target, or sharing is serialized by structure.

Related: [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [principle-make-operations-idempotent](../principle-make-operations-idempotent/SKILL.md), [principle-treat-input-as-untrusted](../principle-treat-input-as-untrusted/SKILL.md).
