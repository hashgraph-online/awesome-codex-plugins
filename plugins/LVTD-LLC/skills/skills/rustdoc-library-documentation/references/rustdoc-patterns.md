# Rustdoc Patterns

Patterns for Rust library documentation that compiles and helps consumers.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Crate narrative | Top-level explanation of what the crate is for and how to start. |
| Public invariant | Condition callers must rely on or preserve. |
| Doctest | Rustdoc example compiled and run by `cargo test`. |
| Hidden setup | Doctest lines hidden with `#` to keep examples readable. |
| Examples directory | Longer runnable scenarios outside inline rustdoc. |
| Feature docs | Documentation that explains feature flags and optional behavior. |

## Core Rules

1. Write docs from the caller's perspective.
2. Document public API behavior, errors, panics, invariants, and examples.
3. Keep inline examples short enough to scan.
4. Use doctests for core API examples whenever practical.
5. Use `examples/` for long or multi-step scenarios.
6. Run `cargo test --doc` and docs for important feature combinations.
7. Mention feature gates where APIs are conditional.

## Pattern: Crate-Level Docs

```rust
//! A short crate purpose statement.
//!
//! # Quick Start
//!
//! ```
//! use my_crate::Parser;
//!
//! let parsed = Parser::new().parse("input")?;
//! # Ok::<(), my_crate::Error>(())
//! ```
//!
//! # Cargo Features
//!
//! - `serde`: Enables serialization support for public data types.
```

Keep the first example close to the most common successful use case.

## Pattern: Public Function Docs

```rust
/// Parses a single input document.
///
/// # Errors
///
/// Returns an error when the input is syntactically invalid.
///
/// # Examples
///
/// ```
/// # use my_crate::parse;
/// let value = parse("name = value")?;
/// # Ok::<(), my_crate::Error>(())
/// ```
pub fn parse(input: &str) -> Result<Value, Error> {
    todo!()
}
```

Document errors and panics where callers need to make decisions.

## Review Checklist

- [ ] Crate-level docs explain purpose and first successful use.
- [ ] Public APIs have examples when examples clarify use.
- [ ] Error and panic behavior is documented.
- [ ] Feature-gated APIs explain required features.
- [ ] `cargo test --doc` passes.
- [ ] Longer examples live in `examples/` and are runnable.
