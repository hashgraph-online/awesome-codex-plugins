# Target Language Guide

## Default Posture

Keep the skill target-neutral. Do not assume Rust, TypeScript, Python, Java, or any other language. Record a target language only when the user, destination repository, or explicit migration request supplies it.

## What To Capture

When target constraints exist, record:

- language and version policy, if discoverable from the destination repo
- package, crate, module, or service boundaries
- public API compatibility requirements
- protocol, config, and data/schema compatibility requirements
- serialization and schema constraints
- error model expectations
- concurrency or async model expectations
- persistence and migration constraints
- testing framework and fixture constraints
- platform support requirements

## What To Avoid

Do not choose:

- internal module layout based on source layout
- private type names copied from source
- algorithms copied from source
- dependency choices without destination repo evidence or user direction
- code generation templates

## Skeleton Guidance

Represent eventual implementation areas as neutral destinations:

- `area_id`: stable clean identifier
- `purpose`: behavior owned by the area
- `spec_ids`: clean behavior specs covered by the area
- `public_contracts`: compatibility surfaces to preserve
- `target_constraints`: destination constraints
- `test_obligations`: tests needed to verify behavior
- `open_decisions`: choices intentionally left for a later implementation phase

When no target language is supplied, use `target_language: "unspecified"` and keep all design notes language-neutral.

## Compatibility And Test Parity

Use existing artifact fields for compatibility. Record public API, protocol, config, and data/schema compatibility in `public_surface`, `compatibility_notes`, `public_contracts`, and `target_constraints`. Record equal-output expectations in behavior spec `outputs`, `observable_behaviors`, `invariants`, and `test_scenarios`.

When source tests exist, convert their behavioral intent into clean tests that validate the same observable outputs. Equal output covers public return values, serialized data, CLI or API responses, errors, state changes, ordering, and compatibility-relevant side effects. Do not copy source test names, fixture structure, private helpers, or source-shaped assertions.
