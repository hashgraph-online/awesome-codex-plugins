# Handlers and Extractors

> Keep handlers typed, thin, and ordered correctly

---
## Stable axum 0.8 Baseline

As verified on 2026-11-05, a handler is an `async fn` whose arguments implement `FromRequestParts` (all but the last) or `FromRequest` (the last, body-consuming one). Extractors run left to right. Exactly one extractor may consume the body, and axum enforces that it is the final argument at compile time. Since axum-core 0.5, `FromRequestParts` uses return-position `impl Trait` in traits, so `#[async_trait]` is no longer required and is a `hypercore-only` style violation when left in new code.

- Put `State`, `Path`, `Query`, `HeaderMap`, and authentication extractors before `Json`, `Form`, `Bytes`, or `String`.
- Return `Result<T, AppError>` where `T: IntoResponse`; do not build error responses inline in every branch.
- Use `Result<Json<T>, JsonRejection>` only when a single handler needs to distinguish malformed JSON from a semantic failure.
- `Path<(A, B)>` must match the number of path parameters exactly in 0.8; a mismatch is a rejection, not a silent partial parse.
- Prefer a typed DTO over `serde_json::Value`; `Value` may exist at the transport edge but must not cross into services.
- Use `#[axum::debug_handler]` from `axum-macros` when a handler fails to satisfy `Handler`; it produces a targeted error instead of a trait wall.
- Do not put business branching in extractors. A custom extractor validates identity or shape; a service decides policy.

## Core Rule

- Inline handlers are acceptable for small routes
- Extracted handlers stay plain functions grouped by feature; do not wrap them in controller structs
- Handlers own transport orchestration only: extraction, validation call, service call, response shaping
- Handler modules do not contain SQL, pool construction, or migration calls

## Preferred Pattern

```rust
use axum::{extract::{Path, State}, Json};

use crate::{dto::user::CreateUser, error::AppError, state::AppState};

pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUser>,
) -> Result<(StatusCode, Json<UserDto>), AppError> {
    let user = state.users.create(payload).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

pub async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<UserDto>, AppError> {
    Ok(Json(state.users.get(id).await?))
}
```

## Custom Extractor Pattern

Use a custom extractor when the same validation or authentication boundary repeats across handlers.

```rust
use axum::{
    extract::{FromRequest, Request},
    Json,
};
use serde::de::DeserializeOwned;
use validator::Validate;

use crate::error::AppError;

pub struct ValidatedJson<T>(pub T);

impl<T, S> FromRequest<S> for ValidatedJson<T>
where
    T: DeserializeOwned + Validate,
    S: Send + Sync,
{
    type Rejection = AppError;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        let Json(value) = Json::<T>::from_request(req, state).await?;
        value.validate()?;
        Ok(Self(value))
    }
}
```

The extractor returns the same `AppError` used by handlers, so validation failures and domain failures share one envelope. Because `Json::<T>::from_request` rejects with `JsonRejection`, `AppError` needs a `#[from] axum::extract::rejection::JsonRejection` variant for the `?` above to compile.

## Response Rules

- Return `Json<T>` for JSON, `StatusCode` for empty bodies, and tuples such as `(StatusCode, Json<T>)` when the status carries meaning.
- Implement `IntoResponse` once for `AppError`; do not duplicate status mapping per handler.
- Use `NoContent` for 204 responses.
- Keep response DTOs separate from database rows; see `rules/axum/database.md`.

## Review Checklist

- Extractors appear in a valid order and the body extractor is last
- Shared state is extracted through `State`, not through globals
- Request-derived values are never `unwrap()`ed
- Handlers return `Result` with the shared error type
- DTOs are typed and validated before service calls
- Handlers do not import `sqlx` or provider SDKs
- Custom extractors reuse the shared error envelope
- `#[async_trait]` is absent from new extractor implementations
- Handler modules stay readable; a handler that needs a long comment to explain its branching belongs in a service

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Extractor order, the single body-consuming extractor, `Result<T, T::Rejection>`, custom extractors | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| `State` placement before body extractors and `FromRef` substates | [axum State](https://docs.rs/axum/latest/axum/extract/struct.State.html) |
| Return-position `impl Trait` replaces `#[async_trait]` in the 0.8 line | [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md) |
| `Path` tuple length checking in 0.8 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `#[debug_handler]` behavior | [axum-macros](https://docs.rs/axum-macros/latest/axum_macros/attr.debug_handler.html) |
