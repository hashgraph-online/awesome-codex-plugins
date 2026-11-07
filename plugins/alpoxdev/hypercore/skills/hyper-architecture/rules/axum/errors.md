# Errors and Responses

> One error type, one response shape, no internal leakage

---
## Stable Baseline

As verified on 2026-11-05, axum handlers signal failure by returning a type that implements `IntoResponse`; `thiserror` 2.0 is the current derive crate for error enums. axum's default rejections produce plain-text bodies, so an API that wants a stable JSON envelope must translate rejections as well as domain errors. `fallback` handles unmatched paths and `method_not_allowed_fallback` handles a known path with an unsupported method; without the latter, axum returns 405 with an `Allow` header.

- Define one `AppError` enum and one `ErrorBody` DTO.
- Implement `IntoResponse` once, mapping each variant to a status, a stable machine `code`, and a safe message.
- Log the internal cause with `tracing::error!` before returning the sanitized body.
- Never include SQL text, connection strings, backtraces, file paths, or provider payloads in the response.
- Map `sqlx::Error::RowNotFound` and domain "not found" to 404 deliberately; do not let an infrastructure variant become 500 by accident.
- Translate extractor rejections. A custom extractor should return `AppError`, not axum's default rejection, when the API promises a JSON envelope. `Json<T>::from_request` fails with `JsonRejection`, so an `AppError` variant with `#[from] axum::extract::rejection::JsonRejection` is what makes `?` work inside the extractor.
- Keep not-found and method-not-allowed bodies consistent with the same envelope.
- Panics are not error handling: avoid `unwrap()` and `expect()` on request-derived values, and treat a panic as a bug that aborts the connection.

## Core Rule

Expected failures are typed values that convert into responses. Unexpected failures are logged and returned as a generic 500.

## Example

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("validation failed")]
    Validation(#[from] validator::ValidationErrors),
    #[error("invalid request")]
    InvalidRequest(#[from] axum::extract::rejection::JsonRejection),
    #[error("unauthorized")]
    Unauthorized,
    #[error("forbidden")]
    Forbidden,
    #[error("not found")]
    NotFound,
    #[error("conflict")]
    Conflict,
    #[error("database error")]
    Database(#[from] sqlx::Error),
}

#[derive(Serialize, utoipa::ToSchema)]
pub struct ErrorBody {
    pub code: &'static str,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fields: Option<serde_json::Value>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code, message, fields) = match self {
            AppError::Validation(errors) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "validation_failed",
                "request validation failed".to_owned(),
                serde_json::to_value(errors.field_errors()).ok(),
            ),
            AppError::InvalidRequest(_) => (
                StatusCode::BAD_REQUEST,
                "invalid_request",
                "request body is not valid JSON".to_owned(),
                None,
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                "unauthorized",
                "authentication required".to_owned(),
                None,
            ),
            AppError::Forbidden => (
                StatusCode::FORBIDDEN,
                "forbidden",
                "not allowed".to_owned(),
                None,
            ),
            AppError::NotFound => (
                StatusCode::NOT_FOUND,
                "not_found",
                "resource not found".to_owned(),
                None,
            ),
            AppError::Conflict => (
                StatusCode::CONFLICT,
                "conflict",
                "resource conflict".to_owned(),
                None,
            ),
            AppError::Database(err) => {
                tracing::error!(error = %err, "database error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "internal_error",
                    "internal server error".to_owned(),
                    None,
                )
            }
        };

        (status, Json(ErrorBody { code, message, fields })).into_response()
    }
}
```

## Not-Found and Method Handling

```rust
use axum::{http::StatusCode, response::IntoResponse, Json};

pub async fn not_found() -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorBody {
            code: "not_found",
            message: "route not found".to_owned(),
            fields: None,
        }),
    )
}
```

Register `fallback(not_found)` once at the composition root. Add `method_not_allowed_fallback` only when the API contract distinguishes 405 from 404, and document that choice.

## Review Checklist

- One `AppError` exists and every handler returns it or a type that converts into it
- `IntoResponse` is implemented once; handlers do not hand-build error bodies
- Internal causes are logged, not serialized
- Not-found and method-not-allowed responses use the same envelope
- Extractor rejections are translated where the API promises JSON errors
- `sqlx::Error` variants are mapped deliberately
- No `unwrap()` or `expect()` on request-derived values in touched code
- Tests cover the status and body of at least one failure per error class

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `IntoResponse` is the handler failure path, tuple responses, `StatusCode` | [axum response](https://docs.rs/axum/latest/axum/response/index.html), [IntoResponse](https://docs.rs/axum/latest/axum/response/trait.IntoResponse.html) |
| Default rejection bodies and `Result<T, T::Rejection>` handling | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| `fallback` and `method_not_allowed_fallback` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html) |
| `thiserror` 2.0 derive | [thiserror](https://docs.rs/thiserror/latest/thiserror/) |
