---
name: principle-type-system-discipline
description: Use when designing types, reviewing signatures, or writing statically typed code. Have the compiler refuse impossible states, confused primitives, and unhandled variants, and parse outside data where it enters.
disable-model-invocation: true
---

# Type system discipline

Let the type checker refuse impossible states, swapped primitives, and variants nobody handles. Design types so error cases and special cases cannot arise, rather than adding handlers for them.

## When it applies

Designing types, reviewing a function signature, and writing in any statically typed language. In an untyped language, apply the same intent with parse functions and runtime schemas.

## What to do

1. Brand semantic primitives. Values that share a primitive but mean different things get distinct types: a branded intersection in TypeScript, a newtype in Rust or Haskell, a distinct type in Go. `UserId` and `TenantId` are both strings, and a function that takes both in the wrong order is a cross-tenant access bug the compiler could have caught. Validate once at construction and trust the type afterward.
2. Consider data from outside the program untyped until a parser has accepted it. That covers IPC messages, JSON documents, RPC payloads, command-line arguments, config files, environment variables, database rows, and tool-call arguments produced by a model. Each boundary has a parse function that produces the typed model.
3. Derive types from authoritative schemas (protocol buffers, OpenAPI, GraphQL schemas, database migrations, design-token files).
4. Make illegal states unrepresentable. Use a discriminated union in place of an object with optional fields that are only valid in certain combinations.
5. Handle variants exhaustively, so adding a variant is a compile error at every unhandled site. Add a new `Permission` variant and the compiler lists every policy check that has not decided what to do with it.
6. Let types carry security properties: if only the sanitizer can construct `SanitizedHtml`, a template that accepts only that type cannot render raw input.
7. For TypeScript syntax specifics, follow the [typescript-best-practices](../typescript-best-practices/SKILL.md) skill.

## The failure it prevents

ID mix-ups, unvalidated external data deep in the system, drift between hand-rolled types and the real schema, and new variants that nothing handles.

## Done when

The compiler rejects the illegal states in question.

Related: [principle-boundary-discipline](../principle-boundary-discipline/SKILL.md), [principle-encode-lessons-in-structure](../principle-encode-lessons-in-structure/SKILL.md), [principle-model-the-domain](../principle-model-the-domain/SKILL.md), [typescript-best-practices](../typescript-best-practices/SKILL.md).
