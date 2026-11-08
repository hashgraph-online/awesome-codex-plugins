# Request Validation

> Validate at the transport boundary, then hand typed domain values inward

---
## Stable Package Baseline

As verified on 2026-11-05, `validator` is 0.21.0. It is a derive-based validation crate, not an axum integration: axum has no built-in validator, so a validating extractor is the integration point. `serde` handles shape and type; `validator` handles rules/axum that types cannot express. The `validator` documentation still shows `version = "0.16"` in its install snippet, so trust the published crate version and `Cargo.lock`, not that snippet.

- Validate every externally controlled `Path`, `Query`, header, cookie, JSON, form, or multipart value that influences behavior.
- Deserialize into a request DTO, validate it, then convert into a domain type. Do not pass DTOs into repositories.
- Keep one validation-error envelope. Choose `422` for semantically invalid input and `400` for malformed syntax, or the reverse, but document the policy once and apply it everywhere.
- Distinguish serde rejection from rule rejection: `JsonRejection` covers missing content type, syntax, and deserialization; `ValidationErrors` covers rule violations.
- Validate `Path` and `Query` DTOs too. A `Uuid` in the path is already type-safe, but pagination bounds, sort whitelists, and filter lengths are not.
- Body size limits are part of validation: set `DefaultBodyLimit` explicitly when uploads or large payloads are accepted.
- Do not add or swap validation crates merely to match this skill.

## Core Rule

Validate request data before service logic consumes it, and keep the failure shape identical across handlers.

## Approved Options

| Shape | Prefer |
|---|---|
| Shape and type only | `serde` derives on the DTO |
| Field rules/axum (length, range, email, regex) | `validator` derive plus a validating extractor |
| Cross-field rules/axum | `validator` `custom` on the struct or an explicit service check with a typed error |
| Path/query bounds | Explicit checks in the handler or a small validated extractor |
| Upload constraints | `DefaultBodyLimit` plus a size check before parsing the full body |

## Example

```rust
use serde::Deserialize;
use validator::Validate;

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUser {
    #[validate(email)]
    pub email: String,
    #[validate(length(min = 1, max = 100))]
    pub name: String,
    #[validate(range(min = 18, max = 120))]
    pub age: u8,
}

pub async fn create_user(
    State(state): State<AppState>,
    ValidatedJson(payload): ValidatedJson<CreateUser>,
) -> Result<(StatusCode, Json<UserDto>), AppError> {
    let user = state.users.create(payload.into()).await?;
    Ok((StatusCode::CREATED, Json(user)))
}
```

`ValidatedJson` comes from `rules/axum/handlers.md`; its rejection type is `AppError`, so validation failures and domain failures share one body.

## Error Mapping

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("validation failed")]
    Validation(#[from] validator::ValidationErrors),
    #[error("invalid request")]
    BadRequest(&'static str),
    #[error("unauthorized")]
    Unauthorized,
    #[error("not found")]
    NotFound,
    #[error(transparent)]
    Database(#[from] sqlx::Error),
}
```

Map `Validation(...)` to `422` with field errors and `BadRequest(...)` to `400` without internals. Never echo the raw payload back.

## Review Checklist

- Non-trivial request DTOs carry `Validate` and are validated before service calls
- Path, query, header, and multipart input are validated, not only JSON bodies
- One error envelope covers serde rejections and rule violations
- Validation failures do not leak field values or internal paths
- Cross-field rules/axum live in one place, not duplicated per handler
- Body limits are explicit where large payloads are possible
- No new validation dependency was added without a stated need

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `validator` derive usage, built-in rules/axum, `ValidationErrors` shape, current version 0.21.0 | [validator](https://docs.rs/validator/latest/validator/), [ValidationErrors](https://docs.rs/validator/latest/validator/struct.ValidationErrors.html) |
| `JsonRejection` variants and `Result<Json<T>, JsonRejection>` handling | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| `DefaultBodyLimit` behavior | [axum DefaultBodyLimit](https://docs.rs/axum/latest/axum/extract/struct.DefaultBodyLimit.html) |
