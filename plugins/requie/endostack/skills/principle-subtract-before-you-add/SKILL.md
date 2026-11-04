---
name: principle-subtract-before-you-add
description: Use when planning the order of an addition, refactor, or rewrite. Clear out dead code and redundancy before building, so the system ends up simpler and no less capable, with a surface the same size or smaller.
disable-model-invocation: true
---

# Subtract before you add

As a system changes, take complexity out before you put new code in. Make simplifying a habit, so every change leaves a design that is simpler, does at least as much, and exposes no more surface than before.

## When it applies

Sequencing any addition, refactor, or rewrite. Subtraction is the default.

## What to do

1. Schedule removal work before construction work, and land it in its own commit.
2. Cut to the minimum before polishing.
3. Design for observed usage, not hypothetical edge cases.
4. Write only the validators, parsers, and guards that the spec and the real trust boundaries call for. Validation at a genuine boundary is required ([principle-boundary-discipline](../principle-boundary-discipline/SKILL.md)); a third copy of it deeper in is not.
5. Apply the same rule to prompts and agent instructions: delete redundant instructions and oversized templates.
6. When a doc, file, or link target adds nothing new, delete it. Do not leave a stub.

Subtraction shrinks attack surface. Before adding a new admin endpoint, remove the two unused debug endpoints beside it. Dead routes, unused dependencies, and orphaned feature flags are code that still runs, or still ships, with nobody watching it.

## The failure it prevents

Building on dead weight, speculative defensive code, and stub files that mislead readers.

## Done when

Dead code and redundancy are gone before new code lands.

Related: [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md), [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md).
