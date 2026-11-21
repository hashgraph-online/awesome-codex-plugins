---
name: principle-redesign-from-first-principles
description: Use when a new requirement has to fit into an existing design. Rework the design as though the requirement had been there from the beginning, and carry it into every type, doc, and example, instead of attaching it at the side.
disable-model-invocation: true
---

# Redesign from first principles

Rework the design so that a new requirement looks like it was there from day one. Bolting it onto the side of the existing structure is the failure this principle prevents.

## When it applies

Fitting a new requirement into a design that already exists. Compare [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md), which challenges a factual belief behind a string of failed fixes.

## What to do

1. Read every affected file and understand the current design before changing it.
2. Ask what you would build from scratch if this requirement had been there on day one.
3. Carry the change into everything that refers to the old design: types, documentation, examples, and the rationale sections explaining why the design looks the way it does.
4. Plan the complete redesign, then deliver it in verifiable increments ([principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md)).

An example. A single-tenant agent platform gains a requirement for multi-tenancy. Bolting it on means adding a `tenant_id` parameter to the functions that happened to break, and every query that was missed becomes a cross-tenant data leak. Redesigning means asking how the system would look if tenants had existed from the start: a tenant is part of every request context, storage is scoped by tenant at the data access layer, and no query can be written without one. The second design makes the leak impossible to write. The first only makes it less common.

## The failure it prevents

Features bolted on in ways that distort the design, and docs and examples that still describe the old world.

## Done when

The design reads as if the requirement was always there.

Related: [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [principle-attack-the-premise](../principle-attack-the-premise/SKILL.md), [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md).
