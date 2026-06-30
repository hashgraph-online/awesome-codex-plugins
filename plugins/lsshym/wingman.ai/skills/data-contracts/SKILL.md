---
name: data-contracts
description: Use when source data and receiving code may disagree on fields, shape, optionality, enum values, or business meaning. Trigger for real data wiring, mock replacement, field/schema/type mismatch, snake_case/camelCase, 接口对接, 字段对齐, 类型对不上. Do not use for styling, copy, imports, or no-boundary renames.
---

# Data Contracts

Use this skill when real source data must be connected to receiving code and the field names, structure, optionality, enum values, or business meaning may differ.

Core principle: align the smallest boundary that owns the meaning. Same meaning plus local receiver usually means direct source usage. Same meaning plus stable receiver usually means one boundary translation. Different meaning or missing source data must stay visible.

## When To Use

Use this when connecting one boundary to another:

- API or generated client response -> UI, service, request builder, or domain model.
- Database row -> domain entity.
- Event or webhook payload -> handler input.
- SDK/vendor response -> internal app model.
- Config/env/CLI input -> runtime options.
- Form state -> request DTO or view contract.
- AI structured output -> parser, schema, tool input, or downstream data model.
- Legacy type -> new type.

Do not use this for pure formatting, styling, copy edits, or refactors with no boundary contract.

Contract alignment is not permission to redesign the receiver. Do not change UI layout, visible copy, interactions, handler behavior, config behavior, domain behavior, or unrelated code unless the contract decision requires it.

## Required Contract Checkpoint

Before changing code for a non-trivial boundary, identify:

- **Source**: actual supplied shape from schema, sample, fixture, migration, source code, docs, or runtime payload.
- **Receiver**: receiving code shape, type, schema, DTO, handler, model, form, config object, or interface.
- **Owner/source of truth**: which side owns the business meaning, and why.
- **Gap**: naming-only, semantic mismatch, missing field, structural mismatch, enum/value mismatch, optionality mismatch, or source conflict.
- **Binding location**: direct source use, local alias, parser/schema, adapter/mapper, repository boundary, domain model, request builder, event handler, component interface, or config parser.
- **Verification**: focused test, typecheck, schema parse, sample payload, fixture, integration check, compile step, or render path.

Keep the checkpoint concise. Do not expose private chain-of-thought; report only concrete contract facts and decisions when useful.

## Decision Protocol

Perform this analysis internally. Do not ask the user at each step. Ask only when semantic ownership, source of truth, or behavior-changing contract decisions cannot be resolved from code, memory, schemas, or docs.

1. **Identify the source shape from real evidence**: Use schemas, samples, fixtures, migrations, source code, docs, generated types, or runtime payloads. Do not infer fields from the receiver.
2. **Identify the receiver contract**: What code, type, schema, handler, model, form, config object, component, or downstream data model receives the source?
3. **Decide ownership and stability**:
   - Memory or current domain truth wins.
   - Explicit schema/spec/docs win over guesses.
   - Existing project architecture wins when it clearly owns the boundary.
   - Local, temporary, single-page, display-only, or component-owned receivers are usually flexible.
   - Shared domain models, public APIs, persisted shapes, exported SDK types, config objects used by startup, and widely used app types are stable.
   - If changing a receiver would ripple through many call sites, treat it as stable unless the user asked for that migration.
4. **If meanings are identical**:
   - Local/temporary/display/single-use receiver: change the receiver to use source fields directly, or use local aliasing. Do not add an adapter just to preserve naming style such as camelCase over `snake_case`.
   - Stable/shared/public/domain/persisted receiver: convert once at the boundary that already owns external input or cross-contract translation.
5. **If meanings differ**: keep concepts separate. Do not rename, cast, narrow, or map by guess just to make types compile. A source `status` is not a receiver `workflowKind` unless evidence proves the same business meaning.
6. **If source data is missing**: do not add fields to the source type, fake defaults, placeholder values, or guessed fallbacks. Use a real alternate source, explicit absence, validation failure, deliberate contract change, or user confirmation.
7. **Choose one binding location**: direct source use, local alias, parser/schema, adapter/mapper, repository boundary, domain model, request builder, event handler, component interface, or config parser. Avoid scattered call-site mapping.
8. **Keep the change scoped to the data boundary**: no UI redesign, handler rewrite, config behavior change, domain behavior change, or unrelated refactor unless the contract decision requires it.
9. **Verify**: Use the project's smallest useful proof: focused test, typecheck, schema parse, sample payload, fixture, integration check, compile step, or render path.

## Example Use Rule

If implementation examples are needed, read `references/examples.md`, then one matching language example.

Examples demonstrate executable boundary handling style: imports, validation, errors, tests, main functions, and run commands.

Do not copy example domains, field names, enum values, architecture, or language into the project unless they match the existing code. Always follow the project's actual language, libraries, and patterns.

Do not write pseudocode into project files.

## Ask The User When

- Both sides use different terms that may represent different business concepts.
- The change would alter a public API, stable domain model, persisted schema, or existing behavior.
- No memory, docs, schema, fixture, code ownership pattern, or architecture identifies the source of truth.
- You cannot tell whether the receiver is local/temporary or shared/stable.
- The source lacks data for a distinct receiver concept.
- Adding an adapter layer would be an architectural decision and the project has no precedent.

## Common Mistakes

Read `references/anti-patterns.md` when fixing type errors, replacing mock data, mapping source fields, handling missing data, guessing aliases, or resolving enum/status/price/permission fields.
