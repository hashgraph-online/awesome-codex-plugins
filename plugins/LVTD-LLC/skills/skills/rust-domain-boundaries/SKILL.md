---
name: rust-domain-boundaries
description: Use when modeling, validating, refactoring, or reviewing Rust service domain boundaries, especially when replacing primitive String fields with newtypes, parse-don't-validate constructors, private invariants, TryFrom/FromStr parsers, request DTO boundaries, or property tests.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Domain Boundaries
  category: Rust
  tags: rust,domain-modeling,newtypes,validation,property-testing
---

# Rust Domain Boundaries

Use this skill to keep invalid states out of Rust service internals. Parse raw
input once at the boundary, store validated values in narrow domain types, and
make unchecked construction difficult.

## Core Workflow

1. Find raw input boundaries: HTTP payloads, path/query parameters, config
   files, environment variables, database rows, queues, and CLI flags.
2. Separate transport DTOs from domain types. Let `serde` deserialize incoming
   shapes, then convert DTO fields into validated domain values.
3. Replace primitive strings with small types for ruled values: email addresses,
   usernames, passwords, subscriber names, slugs, tenant IDs, idempotency keys,
   and money-like or duration-like values.
4. Give domain types private fields and smart constructors. Avoid unchecked
   `pub` fields or `impl From<String>` for fallible conversions.
5. Return typed validation errors that map to useful HTTP responses without
   leaking internal details.
6. Keep database and external API mapping explicit. Convert to raw strings at
   the final persistence or serialization edge.
7. Test invariants directly. Cover valid examples, malformed inputs, boundary
   lengths, normalization rules, and round trips.

## Type Design Rules

- Prefer `TryFrom<String>`, `TryFrom<&str>`, or `FromStr` for fallible parsing.
- Keep stored values owned unless profiling proves borrowing is necessary.
- Implement `AsRef<str>` or a named accessor for read-only exposure.
- Implement `Display` only when the formatted value is safe to show in logs,
  errors, and UI.
- Avoid deriving `Debug` for secret-bearing values unless the debug output is
  redacted.
- Make normalization visible in tests: trim, lowercase, Unicode handling, and
  canonicalization.

## Request Boundary Pattern

Deserialize into a request shape, then construct a command:

```rust
#[derive(serde::Deserialize)]
pub struct SubscribeRequest {
    email: String,
    name: String,
}

pub struct SubscribeCommand {
    pub email: EmailAddress,
    pub name: SubscriberName,
}

impl TryFrom<SubscribeRequest> for SubscribeCommand {
    type Error = SubscribeValidationError;

    fn try_from(value: SubscribeRequest) -> Result<Self, Self::Error> {
        Ok(Self {
            email: EmailAddress::parse(value.email)?,
            name: SubscriberName::parse(value.name)?,
        })
    }
}
```

Handlers should reject invalid input before business logic or database code. If
validation needs database state, keep pure parsing separate from uniqueness or
authorization checks.

## Tests

Read `references/property-testing.md` when invariants have many edge cases or
when an AI agent is likely to miss invalid inputs with example-only tests.

Minimum tests for a new domain type:

- Accept a realistic valid value.
- Reject empty input and whitespace-only input.
- Reject too-long input when storage or product rules impose limits.
- Reject format violations.
- Preserve or normalize exactly as documented by tests.
- Round-trip through `serde` or SQL mapping when that type crosses those
  boundaries.

## Reference Files

- `references/newtype-patterns.md`: constructor, trait, serde, and persistence
  patterns for Rust newtypes.
- `references/property-testing.md`: property-testing strategy for parsers and
  domain constructors.
