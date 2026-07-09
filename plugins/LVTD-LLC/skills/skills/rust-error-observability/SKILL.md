---
name: rust-error-observability
description: Use when adding, changing, debugging, or reviewing Rust service error handling and observability, especially when separating domain errors from HTTP responses, adding thiserror/anyhow, implementing ResponseError or IntoResponse, adding tracing spans, redacting secrets, or diagnosing async failures.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Error Observability
  category: Rust
  tags: rust,error-handling,observability,tracing,backend
---

# Rust Error Observability

Use this skill to make Rust service failures understandable to operators while
keeping user-facing responses safe. Treat error handling and telemetry as one
design surface.

## Core Workflow

1. Inventory error flows: handler return types, service/repository errors,
   worker errors, middleware, logs, and tracing setup.
2. Classify each error by purpose:
   - Domain or validation outcome.
   - Recoverable control flow.
   - Operator diagnostic.
   - User-facing HTTP response.
3. Keep domain errors typed. Use `thiserror` for expected branches that callers
   should match on.
4. Add context at infrastructure boundaries. Use `anyhow` or opaque application
   errors when callers should not match every dependency failure.
5. Map errors to HTTP responses in one place per framework: `ResponseError`,
   Axum `IntoResponse`, or a small adapter function.
6. Add structured spans before more log lines. Include stable diagnostic fields,
   not raw payloads or secrets.
7. Ensure errors are logged once. Prefer logging at the outer boundary where
   request context is available.
8. Test both the public response and the diagnostic path when behavior changed.

## Error Boundary Rules

- Domain modules return domain errors, not HTTP status codes.
- Repository modules attach query or operation context, but do not log every
  error.
- Handlers convert domain outcomes into response types and let unexpected
  failures become a consistent 500.
- Background workers log failed job IDs, attempt counts, and next action.
- Avoid `unwrap`, `expect`, or stringly `map_err` in service paths unless the
  invariant is local and the panic message is useful.

Read `references/error-boundaries.md` when choosing between `thiserror`,
`anyhow`, opaque errors, and framework response adapters.

## Tracing Rules

- Instrument request handlers, service methods, outbound clients, database
  operations, and worker jobs at boundaries.
- Use `#[tracing::instrument(skip(...))]` for request bodies, pools, clients,
  passwords, tokens, and large values.
- Attach fields like request ID, user ID, tenant ID, job ID, upstream name, and
  idempotency key when safe.
- Do not log secrets, cookies, password hashes, bearer tokens, or full PII.

Read `references/tracing.md` for spans, subscriber setup, and test logging.
Read `references/secrets-and-pii.md` before touching secret-bearing values.

## HTTP Response Pattern

Keep response errors stable and intentional:

```rust
pub enum SubscribeError {
    Validation(SubscribeValidationError),
    Unexpected(anyhow::Error),
}

impl actix_web::ResponseError for SubscribeError {
    fn status_code(&self) -> actix_web::http::StatusCode {
        match self {
            Self::Validation(_) => actix_web::http::StatusCode::BAD_REQUEST,
            Self::Unexpected(_) => actix_web::http::StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}
```

The response body should be safe for users. The trace event should carry the
diagnostic context operators need.

## Reference Files

- `references/error-boundaries.md`: choosing error types and response adapters.
- `references/tracing.md`: spans, fields, subscriber setup, and test output.
- `references/secrets-and-pii.md`: redaction rules for secrets and sensitive
  user data.
