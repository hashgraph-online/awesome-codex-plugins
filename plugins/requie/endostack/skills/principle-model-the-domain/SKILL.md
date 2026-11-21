---
name: principle-model-the-domain
description: Use when writing stateful logic, branch-heavy code, or the same shape assumption repeated across files. Capture domain rules with a state machine, typed model, or lookup table so invalid states cannot be built.
disable-model-invocation: true
---

# Model the domain

Encode the domain as a data structure in which invalid states cannot exist and branches become unnecessary, instead of scattering its rules through conditionals. Choosing the structure at the moment you write the code costs little. Introduced afterwards, it looks like a refactor, and refactors tend to be postponed indefinitely.

## When it applies

Writing stateful logic, code with heavy branching, and the same assumption about a data shape repeated across files. Apply it whenever you name the data shape for a code task.

Skip it when the current shape is clear, local, and unlikely to grow. Prefer plain code there. Be wary of an abstraction that adds indirection unless it also eliminates something: a branch, a repeated rule, a reachable invalid state, or a lifecycle hazard.

## What to do

Reach for the structure that fits:

1. A state machine in place of scattered booleans, phase flags, or lifecycle checks. An agent session with `is_authenticated`, `is_elevated`, and `is_locked` booleans permits "locked and elevated". A state machine with `Anonymous`, `Authenticated`, `Elevated`, and `Locked` states and explicit transitions does not.
2. A typed model in place of loose parameters or repeated assumptions about shape.
3. A lookup table, map, registry, or tagged union in place of branching scattered over files. A tool registry that maps each tool name to its handler and required permission puts the authorization rule in one table a reviewer can read.
4. A reducer or a command and event model in place of ad hoc mutation.
5. Modules built around a single area of domain knowledge, rather than around steps in a pipeline. Execution order (load, validate, transform, save) does not define ownership.
6. A small module boundary that collects repeated behavior, ownership, or invariants.
7. Queues, caches, indexes, graphs, trees, or normalized collections where the access patterns call for them.
8. If nothing standard fits, write down what the code must never permit and how the data is read, then find a structure that encodes exactly that.

## Signs you skipped it

A new feature adds one more branch to an existing if/else chain. A second boolean has to be kept consistent with a first. Phase-named modules each repeat the same domain rule.

## The failure it prevents

Rules duplicated across files that drift apart, and invalid states that are reachable because nothing prevents constructing them.

## Done when

Domain rules live in one structure and invalid states cannot be constructed.

Related: [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [principle-type-system-discipline](../principle-type-system-discipline/SKILL.md), [principle-minimize-reader-load](../principle-minimize-reader-load/SKILL.md), [statechart](../statechart/SKILL.md).
