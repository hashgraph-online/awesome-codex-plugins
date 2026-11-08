# utoipa Official Docs Summary

last_verified_at: 2026-11-05

## Contents

- Stable package snapshot
- Derives and path metadata
- Router composition and spec splitting
- Swagger UI serving
- Version caveats
- How this affects the skill
- Sources

## Stable package snapshot

Verified from docs.rs and the utoipa changelog on 2026-11-05.

| Package | Stable | Notes |
|---|---:|---|
| `utoipa` | 6.0.0 | MSRV 1.88; OpenAPI 3.2 support via `Version32`; derives `ToSchema`, `IntoParams`, `ToResponse`, `OpenApi` |
| `utoipa-axum` | 0.3.0 | `OpenApiRouter`, `routes!`, `split_for_parts` |
| `utoipa-swagger-ui` | 10.0.2 | `SwaggerUi` layer for axum; bundled UI version is independent |

The rendered utoipa documentation is internally inconsistent about the default OpenAPI version: the feature list mentions 3.1 while the `openapi` module describes 3.2. Declare the version explicitly.

## Derives and path metadata

- `#[derive(ToSchema)]` generates a reusable schema for a request or response type.
- `#[derive(IntoParams)]` generates path or query parameters from struct fields.
- `#[derive(OpenApi)]` builds the root document and its component registry.
- `#[utoipa::path(get, path = "/users/{id}", ...)]` attaches operation metadata to a handler and is what the router collector reads.

Source: [utoipa docs](https://docs.rs/utoipa/latest/utoipa/)

## Router composition and spec splitting

```rust
let (router, api) = OpenApiRouter::new()
    .routes(routes!(get_user, create_user))
    .split_for_parts();
```

- `OpenApiRouter::routes` registers the method router and extends the document with the handler's path metadata.
- `split_for_parts` returns the inner `axum::Router` and the `OpenApi` value.
- `routes!` only collects handlers annotated with `#[utoipa::path]`.
- `routes!` panics on duplicate registration of the same HTTP method for a path and on CONNECT handlers.

Source: [OpenApiRouter](https://docs.rs/utoipa-axum/latest/utoipa_axum/router/struct.OpenApiRouter.html), [routes!](https://docs.rs/utoipa-axum/latest/utoipa_axum/macro.routes.html)

## Swagger UI serving

```rust
let app = Router::new().merge(
    SwaggerUi::new("/swagger-ui")
        .url("/api-docs/openapi.json", ApiDoc::openapi()),
);
```

- `.url(spec_path, openapi)` attaches a spec endpoint.
- `.merge(...)` attaches the UI router to the axum router.
- The axum integration requires the crate's `axum` feature and axum 0.7 or later.

Source: [utoipa-swagger-ui](https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/)

## Version caveats

- utoipa 6 can emit OpenAPI 3.2; many client generators still expect 3.0 or 3.1. Pin the emitted version explicitly.
- The bundled Swagger UI version is a separate dependency from the OpenAPI version.
- A plain `axum::Router` merged next to an `OpenApiRouter` contributes routes but no metadata.
- Operation IDs must be unique and stable or generated clients churn.

## How this affects the skill

- The skill requires one spec source, one spec endpoint, and an explicit OpenAPI version.
- Documented handlers must be the same handlers the runtime serves; the collector does not discover plain routes.
- Swagger UI is treated as a separate exposure decision from the JSON document.

## Sources
> Checked 2026-11-05.
| Claim | Source | Checked |
|---|---|---|
| utoipa 6.0.0, derives, 3.2 support, MSRV 1.88 | <https://docs.rs/utoipa/latest/utoipa/> | 2026-11-05 |
| utoipa changelog for 6.0.0 | <https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md> | 2026-11-05 |
| `OpenApiRouter`, `split_for_parts`, `routes!` semantics and panics | <https://docs.rs/utoipa-axum/latest/utoipa_axum/> | 2026-11-05 |
| `SwaggerUi` axum integration | <https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/> | 2026-11-05 |
