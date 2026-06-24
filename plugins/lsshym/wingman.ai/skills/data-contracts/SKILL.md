---
name: data-contracts
description: Use when aligning provider/consumer data contracts: APIs, webhooks, events, database rows, SDK responses, schemas, DTOs, generated clients, domain models, forms, config/env/CLI, UI props, or AI outputs. Trigger for real response wiring, mock replacement, field/schema/type mismatch, DTO mapping, enum/status drift, missing/optional fields, pagination, nested payloads, 接口对接, 字段对齐, 类型对不上. Do not use for styling, copy edits, imports, or no-boundary renames/refactors.
---

# Data Contracts

Align provider and consumer contracts without hiding semantic drift. A contract can be an API payload, database row, event, webhook, config object, SDK response, CLI input, schema, DTO, generated client type, domain model, form payload, AI structured output, or component interface.

Core principle: do not preserve a shape just because it already exists. First decide whether the consumer contract is local/temporary or stable/shared, then preserve the contract that owns the meaning. Semantic mismatch beats scope shortcuts: even local consumer contracts must not be renamed or deleted when they express a different business concept from the provider.

## When To Use

Use this when connecting one boundary to another:

- API response -> UI, service, or domain model.
- Database row -> domain entity.
- Event or webhook payload -> handler input.
- SDK result -> internal app model.
- Config/env/CLI input -> runtime options.
- Legacy type -> new type.
- Form state -> request DTO.
- AI structured output -> tool or schema input.
- Generated schema/client -> hand-written code.

Do not use this for pure formatting, styling, copy edits, or refactors with no boundary contract.

## Required Contract Checkpoint

Before changing code for a non-trivial contract boundary, identify:

- **Provider**: actual supplied shape from schema, sample, fixture, migration, source code, docs, or runtime payload.
- **Consumer**: receiving code shape, type, schema, DTO, handler, model, form, or interface.
- **Source of truth**: which side owns the business meaning, and why.
- **Gap**: naming-only, semantic mismatch, missing field, structural mismatch, enum/value mismatch, optionality mismatch, or source conflict.
- **Binding location**: parser/schema, adapter/mapper, repository boundary, domain model, request builder, event handler, component interface, or direct source use.
- **Verification**: focused test, typecheck, schema parse, sample payload, fixture, integration check, compile step, or render path.

Keep the checkpoint concise. Do not expose private chain-of-thought; report only concrete contract facts and decisions when useful.

## Core Protocol

Perform this analysis internally. Do not ask the user at each step. Ask only when semantic ownership, source of truth, or behavior-changing contract decisions cannot be resolved from code, memory, schemas, or docs.

1. **Identify the provider contract**: What shape is actually provided? Use real schemas, samples, types, migrations, docs, or source code.
2. **Identify the consumer contract**: What shape is expected by the receiving code?
3. **Decide ownership/source of truth by scope and stability**:
   - Local, temporary, single-page, or component-owned consumer types can usually change to match the provider only when the meaning is the same.
   - Shared domain models, public APIs, persisted shapes, exported SDK types, and widely-used app types are stable; preserve them and convert at a boundary.
   - Memory or domain truth wins.
   - Explicit schema/spec wins.
   - Existing project architecture wins.
   - Stable internal domain models usually win over external vendor payloads.
   - Backend/product API usually wins over display-only frontend components.
   - If changing a type would ripple through many call sites, treat it as stable unless the user asked for that migration.
   - If a local consumer name, function, prop, or enum expresses a business concept the provider does not expose, preserve that consumer concept and expose the missing/uncertain boundary instead of renaming it to the provider concept.
   - If still unclear and semantics matter, ask.
4. **Classify the gap**:
   - Naming only: same meaning, different style (`user_name` -> `userName`).
   - Semantic mismatch: names or values imply different meaning (`status` vs `workflowKind`). Do not resolve this by renaming, deleting, or narrowing the consumer contract to the provider concept.
   - Missing field: consumer requires data provider does not supply.
   - Structural mismatch: nesting, arrays, pagination, or ownership differ.
   - Source-of-truth conflict: both sides could plausibly own meaning.
5. **Choose the binding location**: decide where the provider shape becomes the consumer shape. Do not ask "how do I make this line compile?" Ask "where should this contract translation live?"
   - Schema/parser for external untrusted input.
   - Adapter/mapper/repository boundary when both sides are stable or external data must not leak inward.
   - Domain model when business meaning must be normalized.
   - Consumer interface when the consumer should accept the source contract directly.
   - Direct source usage for large, read-only, display-only shapes where mapping adds noise.
   - No new adapter when the only change is one local display field, the consumer is not shared, and the semantics are identical.
6. **Avoid ad-hoc call-site mapping**: Do not scatter casual field renames, proxy fields, or dummy values at random call sites. Local aliasing is fine only when semantics are identical and scope is small.
7. **Handle missing data explicitly**: Choose optionality, explicit fallback, validation error, contract change, or user confirmation. Do not invent placeholder fields just to satisfy types. If the provider lacks data for a distinct consumer concept, keep the consumer concept visible and return/throw/ask rather than replacing it with a different provider concept.
8. **Preserve behavior**: Change only what is required to align the boundary. Do not fold unrelated refactors into contract work.
9. **Verify**: Use the project's normal proof: tests, typecheck, schema parse, sample payload, fixture, integration check, or compile step.

## Example Use Rule

If implementation examples are needed, read `references/examples.md`, then one matching language example.

Examples demonstrate executable boundary handling style: imports, validation, errors, tests, main functions, and run commands.

Do not copy example domains, field names, enum values, architecture, or language into the project unless they match the existing code. Always follow the project's actual language, libraries, and patterns.

Do not write pseudocode into project files.

## Ask The User When

- Both sides use different terms that may represent different business concepts.
- The change would alter a public API, stable domain model, persisted schema, or existing behavior.
- No memory, docs, schema, or code ownership pattern identifies the source of truth.
- You cannot tell whether a consumer type is local/temporary or shared/stable.
- A provider lacks data for a distinct consumer concept.
- Adding an adapter layer would be an architectural decision and the project has no precedent.

## Common Mistakes

Read `references/anti-patterns.md` when fixing type errors, replacing mock data, mapping API fields, handling missing data, or resolving enum/status/price/permission fields.
