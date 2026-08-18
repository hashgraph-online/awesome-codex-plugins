---
name: rust-trait-api-design
description: Design and review Rust trait APIs, generic bounds, dispatch models, and conversion contracts for clear public interfaces. Use when designing, refactoring, or reviewing traits, generics, trait objects, associated types, impl Trait, From/TryFrom, AsRef, Borrow, or crate APIs.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Trait API Design
  category: Rust
  tags: rust,traits,generics,api-design,trait-objects
---

# Rust Trait API Design

Use this skill to make Rust APIs generic where useful, concrete where simpler,
and object-safe when dynamic dispatch is part of the design. Optimize for the
smallest capability contract that callers and implementors can understand.

## Core Workflow

1. Identify whether the API consumes, borrows, returns, stores, or dispatches
   behavior.
2. Start with concrete types for local code. Generalize only when at least two
   callers or implementations need the flexibility.
3. Use generic bounds for compile-time polymorphism and inlining. Use `dyn
   Trait` for heterogeneous values, plugin-like extension points, or runtime
   dispatch.
4. Place bounds at the point that needs them. Prefer `where` clauses when
   bounds are long or involve associated types.
5. Decide whether a trait is intended for downstream implementation. Seal it,
   keep fields private, or use constructors when invariants must not be
   implemented externally.
6. Use standard conversion traits where they match exactly. Do not invent a
   custom conversion trait before checking `From`, `TryFrom`, `AsRef`, `AsMut`,
   `Borrow`, `ToOwned`, and `Cow`.
7. Add compile tests, unit tests, or examples that prove the public API is
   callable the way the skill expects future users to call it.

## API Design Rules

- Accept `impl Trait` or a named generic for parameters when callers should
  pass many concrete types.
- Return `impl Trait` when hiding one concrete return type. Return `Box<dyn
  Trait>` when the concrete type varies at runtime.
- Prefer associated types when each implementation has one natural related
  type. Prefer generic trait parameters when one implementation supports many
  target types.
- Implement `From` for infallible conversions and `TryFrom` for fallible
  conversions. Implementing these gives callers `Into` and `TryInto`.
- Use `AsRef` for cheap reference-to-reference conversion. Use `Borrow` only
  when borrowed and owned forms have equivalent `Eq`, `Hash`, and `Ord`
  behavior.
- Avoid `Copy` bounds unless the algorithm semantically requires bitwise copy.

## Trait Object Review

Read `references/trait-api-patterns.md` when choosing between generics and
`dyn Trait`, or when public traits fail object-safety checks.

Before making a public trait object-safe, check:

- Methods do not use generic type parameters.
- Methods do not return `Self` unless constrained with `where Self: Sized`.
- Associated types are specified on the trait object where needed.
- The object is behind a pointer such as `&dyn Trait`, `Box<dyn Trait>`, or
  `Arc<dyn Trait + Send + Sync>`.

## Common Smells

- A public function takes `&Vec<T>` because it only needs iteration.
- The API accepts `String` and immediately borrows it as `&str`.
- The API implements `Into` directly instead of `From`.
- A trait has many blanket bounds that only one method needs.
- A trait object was used because lifetimes were confusing, not because runtime
  dispatch is required.
- `async-trait` is used in a public trait without checking whether native
  `async fn` in traits, `trait-variant`, or boxed futures fit the dispatch and
  `Send` needs better.
