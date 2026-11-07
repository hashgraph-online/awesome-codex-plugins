# Axum Official Docs Summary

last_verified_at: 2026-11-05

## Contents

- Stable package snapshot
- Confirmed points from official docs
- Changes that bite in 0.8
- How this affects the skill
- Sources

## Stable package snapshot

Verified from docs.rs and the axum changelog on 2026-11-05. These are evidence snapshots, not automatic upgrade targets.

| Package | Stable | Compatibility observed |
|---|---:|---|
| `axum` | 0.8.9 | MSRV 1.80; `tokio` optional feature; `json`, `query`, `form`, `matched-path`, `original-uri`, `tower-log`, `tracing`, `multipart`, `ws`, `macros` features |
| `axum-core` | 0.5.x | `#[async_trait]` replaced by return-position `impl Trait` in traits |
| `axum-macros` | 0.5.x | `#[debug_handler]`, `#[derive(FromRequest)]`, `#[derive(FromRef)]` |
| `axum-extra` | 0.10.x | `Host`, `TypedHeader`, `CookieJar`, and other opt-in extractors |

Installed `Cargo.toml` and `Cargo.lock` win for implementation. Re-check docs.rs before changing dependencies after the verification date.

## Confirmed points from official docs

1. `Router<S>` is a router missing a state of type `S`; only `Router<()>` can be passed to `serve`. `with_state` supplies the state once. `nest` and `merge` require the same state type.
Source: [Router](https://docs.rs/axum/latest/axum/struct.Router.html), [State](https://docs.rs/axum/latest/axum/extract/struct.State.html)

2. Extractors run left to right. All but the last implement `FromRequestParts`; the last may implement `FromRequest` and consume the body. Exactly one body-consuming extractor is allowed, and axum enforces its position at compile time.
Source: [extract](https://docs.rs/axum/latest/axum/extract/index.html)

3. `State` is a global per-router value. Request-derived data belongs in `Extension`, a custom extractor, or request extensions. `FromRef` provides substates.
Source: [State](https://docs.rs/axum/latest/axum/extract/struct.State.html)

4. `Router::layer` wraps all previously added routes, so the last call is the outermost layer. `ServiceBuilder` runs its first layer first. `route_layer` runs only when the route matches.
Source: [middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

5. axum expects infallible services; a fallible layer needs `HandleErrorLayer` above it.
Source: [middleware error handling](https://docs.rs/axum/latest/axum/middleware/index.html)

6. `axum::serve(listener, app)` accepts a `TcpListener` and a make-service, and exposes `with_graceful_shutdown`.
Source: [serve](https://docs.rs/axum/latest/axum/fn.serve.html), [Serve](https://docs.rs/axum/latest/axum/serve/struct.Serve.html)

7. `fallback` handles unmatched paths, and `method_not_allowed_fallback` handles a known path with an unsupported method. Without the latter, axum returns 405 with an `Allow` header.
Source: [Router](https://docs.rs/axum/latest/axum/struct.Router.html)

8. `Json`, `Query`, `Path`, and `Form` rejections are typed and can be handled per handler with `Result<T, T::Rejection>`.
Source: [extract](https://docs.rs/axum/latest/axum/extract/index.html)

## Changes that bite in 0.8

- Path syntax changed from `/:id` and `/*rest` to `/{id}` and `/{*rest}`; the old syntax panics at startup.
- Handlers and services added to `Router` and `MethodRouter` must be `Sync`.
- `Option<Path<T>>` no longer swallows every error condition; `Option<Query<T>>` lost its `OptionalFromRequestParts` implementation.
- `Host` moved to `axum-extra`.
- `Serve::tcp_nodelay` was removed; `serve` is generic over listeners and `serve::ListenerExt` configures stream properties.
- 0.8.9 raised MSRV to 1.80.

Source: [axum CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md), [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md)

## How this affects the skill

- The skill checks the installed axum line before applying path or middleware rules; 0.7 syntax is a migration finding, not a style choice.
- Composition and state rules/axum follow `Router<S>` semantics rather than a generic "app object" model.
- Middleware rules/axum encode the documented ordering, because layer order is the most common source of subtle behavior changes.

## Sources
> Checked 2026-11-05.
| Claim | Source | Checked |
|---|---|---|
| Router state, `with_state`, `nest`, `merge`, `fallback`, `route_layer` | <https://docs.rs/axum/latest/axum/struct.Router.html> | 2026-11-05 |
| Extractor order and rejection handling | <https://docs.rs/axum/latest/axum/extract/index.html> | 2026-11-05 |
| State and `FromRef` | <https://docs.rs/axum/latest/axum/extract/struct.State.html> | 2026-11-05 |
| Layer ordering and `HandleErrorLayer` | <https://docs.rs/axum/latest/axum/middleware/index.html> | 2026-11-05 |
| `serve` and graceful shutdown | <https://docs.rs/axum/latest/axum/fn.serve.html> | 2026-11-05 |
| 0.8 breaking changes and MSRV | <https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md> | 2026-11-05 |
