# Validation, Testing, and Runtime Ecosystem Summary

last_verified_at: 2026-11-05

## Contents

- Stable package snapshot
- validator
- axum-test
- thiserror and tracing
- How this affects the skill
- Sources

## Stable package snapshot

Verified from docs.rs and crates.io metadata on 2026-11-05.

| Package | Stable | Notes |
|---|---:|---|
| `validator` | 0.21.0 | Derive-based validation; no axum integration |
| `axum-test` | 21.1.0 | `TestServer`, request builder, direct dispatch or random port |
| `thiserror` | 2.0.21 | Error enum derive |
| `tracing` | 0.1.44 | Structured spans and events |
| `tracing-subscriber` | 0.3.23 | Subscriber and `EnvFilter` setup |
| `tokio` | 1.54.1 | Runtime, `TcpListener`, signal handling |
| `http-body-util` | 0.1.x | `BodyExt::collect` for test assertions |

## validator

- Derive `Validate` on a struct and annotate fields with `#[validate(...)]`.
- Built-in rules/axum include `email`, `url`, `length`, `range`, `must_match`, `contains`, `does_not_contain`, `custom`, `regex`, `non_control_character`, and `required`; `credit_card` needs the `card` feature.
- `validate()` returns `Result<(), ValidationErrors>`.
- `ValidationErrors` is `HashMap<Cow<'static, str>, ValidationErrorsKind>`; `field_errors()` returns the field-level map used in error bodies.
- The rendered docs still show `version = "0.16"` in the install snippet; that snippet is stale relative to the published 0.21.0.

Source: [validator](https://docs.rs/validator/latest/validator/), [ValidationErrors](https://docs.rs/validator/latest/validator/struct.ValidationErrors.html)

## axum-test

- `TestServer::new(app)` takes an axum `Router` in the basic case; the server can dispatch directly to the handler or bind a random port.
- Requests are built from the server, for example `server.post("/users").json(&value).await`.
- Responses expose status and body helpers, and the exact assertion method set depends on the installed version.
- Cookies, headers, and multipart helpers exist in the crate's modules.

Source: [axum-test](https://docs.rs/axum-test/latest/axum_test/)

## thiserror and tracing

- `#[derive(thiserror::Error)]` plus `#[error("...")]` and `#[from]` produces the error enum used by `AppError`.
- `tracing::error!`, `warn!`, `info!`, and `#[instrument]` are the logging surface; handlers and services use them instead of `println!`.
- `tracing_subscriber::registry().with(EnvFilter::from_default_env())` is the common initialization path for a binary.

Source: [thiserror](https://docs.rs/thiserror/latest/thiserror/), [tracing](https://docs.rs/tracing/latest/tracing/), [tracing-subscriber](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/)

## How this affects the skill

- Validation is implemented as a validated extractor because no official axum integration exists.
- Router tests use `tower::ServiceExt::oneshot` by default and `axum-test` when the builder or cookie support pays for itself.
- Error and logging rules/axum assume `thiserror` plus `tracing`, which are the ecosystem defaults, not framework requirements.

## Sources
> Checked 2026-11-05.
| Claim | Source | Checked |
|---|---|---|
| validator rules/axum and error types | <https://docs.rs/validator/latest/validator/> | 2026-11-05 |
| axum-test `TestServer` flow | <https://docs.rs/axum-test/latest/axum_test/> | 2026-11-05 |
| thiserror derive | <https://docs.rs/thiserror/latest/thiserror/> | 2026-11-05 |
| tracing and subscriber setup | <https://docs.rs/tracing/latest/tracing/> | 2026-11-05 |
| tokio runtime and signals | <https://docs.rs/tokio/latest/tokio/> | 2026-11-05 |
