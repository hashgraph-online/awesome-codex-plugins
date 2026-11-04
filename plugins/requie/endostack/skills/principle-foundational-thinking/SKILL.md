---
name: principle-foundational-thinking
description: Use before writing logic, picking core types, or deciding whether infrastructure or features come first. Settle data shapes and groundwork first, and isolate any state that concurrent actors could change.
disable-model-invocation: true
---

# Foundational thinking

Fix the data shapes and the order of groundwork before any logic exists, so the code that follows inherits them. Structural decisions should keep future options open, and code-level decisions should keep things simple.

## When it applies

Before writing logic, when choosing core types and data structures, when deciding whether scaffolding or features come first, and when concurrent actors might share state. It is never a reason for speculative abstraction; [principle-laziness-protocol](../principle-laziness-protocol/SKILL.md) still governs size.

## What to do

1. Choose the core types first. Enumerate how the data will be read and written, and pick structures that fit the most common paths. An audit log queried by actor and time range wants an append-only store indexed on those fields, chosen before any handler exists.
2. At the code level, deduplicate structure (types and data models should converge), not every repeated line. A few similar statements beat a premature abstraction. Prefer explicit code over clever code, and test behavior and edge cases over line coverage.
3. If two actors will touch the same state, ask what a simultaneous change by the other one would do. Isolate the state unless that answer is "nothing". See [principle-separate-before-serializing-shared-state](../principle-separate-before-serializing-shared-state/SKILL.md).
4. Scaffold first. Anything every later phase benefits from (CI, linting, test infrastructure, shared types, a secrets scanner in pre-commit) comes before features. Sequence the work to keep options open: infrastructure ahead of features, and tests ahead of fixes.
5. Keep commits small and about one thing.
6. Make each increment introduce a coherent abstraction or deepen an existing one.
7. Subtract before scaffolding. Delete dead code first, then lay foundations ([principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md)).

## The failure it prevents

Logic written against the wrong data shape, premature deduplication, races from casually shared state, and features built before the infrastructure that would verify them.

## Done when

Core types are named and justified by access patterns before logic exists, and the scaffold is in place before features.

Related: [principle-experience-first](../principle-experience-first/SKILL.md), [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md), [principle-separate-before-serializing-shared-state](../principle-separate-before-serializing-shared-state/SKILL.md), [principle-model-the-domain](../principle-model-the-domain/SKILL.md).
