# Error Boundaries

Good Rust services use more than one error style. Pick the style from the
caller contract, not from habit.

## Typed Domain Errors

Use typed enums when callers should branch:

```rust
#[derive(Debug, thiserror::Error)]
pub enum LoginError {
    #[error("invalid credentials")]
    InvalidCredentials,
    #[error("account is locked")]
    AccountLocked,
}
```

Typed errors work well for validation, authorization decisions, duplicate
resources, idempotency conflicts, and expected workflow states.

## Opaque Application Errors

Use `anyhow::Error` or an opaque application error when callers should attach
context and bubble up:

```rust
let row = sqlx::query!(...)
    .fetch_optional(pool)
    .await
    .context("failed to fetch user credentials")?;
```

Add context at the boundary where the operation is meaningful. Avoid wrapping
the same error with vague context at every layer.

## HTTP Adapters

Keep HTTP mapping close to the web layer. Domain crates should not depend on
Actix, Axum, Warp, or Rocket.

Actix:

```rust
impl actix_web::ResponseError for AppError {
    fn status_code(&self) -> actix_web::http::StatusCode {
        match self {
            AppError::BadRequest(_) => StatusCode::BAD_REQUEST,
            AppError::Unauthorized => StatusCode::UNAUTHORIZED,
            AppError::Unexpected(_) => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}
```

Axum:

```rust
impl axum::response::IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let status = match self {
            AppError::BadRequest(_) => StatusCode::BAD_REQUEST,
            AppError::Unauthorized => StatusCode::UNAUTHORIZED,
            AppError::Unexpected(_) => StatusCode::INTERNAL_SERVER_ERROR,
        };
        status.into_response()
    }
}
```

## Logging Once

Prefer this flow:

1. Add context with `Context` or typed variants as errors move up.
2. Convert to a response at the framework boundary.
3. Emit one structured error event there, with request context.

Avoid logging inside every helper and then returning the same error. Duplicate
logs make incidents harder to read.
