# OpenAPI and Swagger

> Treat the generated document as a typed contract boundary

---
## Stable Package Baseline

As verified on 2026-11-05, `utoipa` is 6.0.0, `utoipa-axum` is 0.3.0, and `utoipa-swagger-ui` is 10.0.2; the utoipa crates require Rust 1.88. utoipa 6 adds OpenAPI 3.2 support via `Version32`. The rendered documentation is internally inconsistent about the default emitted version, because the feature list says 3.1 while the `openapi` module describes 3.2, so declare the target version explicitly in the `OpenApi` builder instead of assuming one.

- Prefer `utoipa` derives on DTOs plus `#[utoipa::path]` on handlers, and compose with `utoipa-axum` `OpenApiRouter` when the repository already uses it.
- `OpenApiRouter::routes(routes!(handler))` collects the handler's path metadata and registers the axum method router; `split_for_parts()` returns `(Router, OpenApi)`.
- Only handlers annotated with `#[utoipa::path]` and collected through `routes!` appear in the generated document. A plain `Router` merged alongside contributes routes but no spec.
- `routes!` panics on duplicate method registration for the same path and on CONNECT handlers. Compose each path once.
- Serve the spec from one canonical endpoint such as `/api-docs/openapi.json`, and attach Swagger UI with `.merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", ApiDoc::openapi()))`.
- Gate spec and UI exposure separately and per environment. A hidden UI does not make a public JSON spec private.
- Validate or lint the generated document before publishing or using it for codegen, and diff it when it is committed.
- Database rows are not automatically public schemas. Map rows to DTOs before publishing.

## Core Rule

When an Axum API publishes OpenAPI, route changes update the contract in the same change. The document must describe the same requests, responses, status codes, security, and examples that the runtime actually supports.

## Approved Generation Paths

| Repo shape | Preferred path |
|---|---|
| Derive-first, axum-native | `utoipa` derives plus `#[utoipa::path]`, composed manually or with `OpenApiRouter` |
| Router-collected | `utoipa-axum::OpenApiRouter` + `routes!` + `split_for_parts()` |
| Contract crate | A dedicated `openapi` or `contract` module/crate owning the `OpenApi` builder and shared schemas |
| UI only | `utoipa-swagger-ui` merged against the canonical spec endpoint |

Do not switch generators across a whole app unless the user explicitly asked for that migration.

## Folder Structure

```text
src/
├── app.rs
├── openapi.rs          # ApiDoc, shared components, security schemes
├── dto/
│   ├── mod.rs
│   └── user.rs         # ToSchema / IntoParams derives
└── routes/
    └── users/
        ├── mod.rs
        └── handlers.rs # #[utoipa::path] on each public handler
```

- Keep shared components, security schemes, examples, and error envelopes in `openapi.rs` when more than one feature reuses them.
- Keep operation metadata on the handler it documents.
- Compose the canonical document at the app boundary, not by copying fragments by hand.
- Use a stable spec path such as `/api-docs/openapi.json`.
- Serve Swagger UI from a separate path such as `/swagger-ui` or an admin route.

## Operation Metadata Checklist

Every documented operation should define:

- Stable `operation_id`
- Consistent `tag`
- Path params, query params, headers, and request body schemas
- Success responses with status-specific schemas
- Expected error responses such as 400, 401, 403, 404, 409, 422, and 500 when applicable
- Auth requirements through reusable `securitySchemes`
- Request and response examples that match the schema
- Deprecation or hidden metadata when an endpoint should not be public

## Contract Drift Rules

| Drift | Rule |
|------|------|
| Handler accepts input not represented in the document | BLOCKED. Add the parameter/body schema or stop documenting the route. |
| Document lists a status the handler never returns | WARNING. Fix the handler or the document before codegen. |
| Handler returns status-specific payloads but the document shows one generic response | WARNING. Add explicit response schemas. |
| Documented schema exposes raw database rows with internal or sensitive fields | BLOCKED. Add DTO mapping. |
| Shared auth layer exists but the document omits security requirements | BLOCKED for public or partner-facing documents. |
| Swagger UI is public by accident | BLOCKED. Add auth/admin/dev gating or record the public-docs decision. |
| Generated document fails validation or has broken `$ref` values | BLOCKED before publishing. |
| A documented body omits `415` while clients can send an undeclared content type | WARNING. Document the outcome or narrow accepted media types. |
| A body is optional in the document but the handler assumes every field | BLOCKED. Mark the body required or validate the absent case. |

## Example

```rust
use utoipa::{OpenApi, ToSchema};
use utoipa_axum::{router::OpenApiRouter, routes};
use utoipa_swagger_ui::SwaggerUi;

#[derive(ToSchema, serde::Serialize)]
pub struct UserDto {
    pub id: uuid::Uuid,
    pub email: String,
}

#[utoipa::path(
    get,
    path = "/users/{id}",
    tag = "users",
    params(("id" = uuid::Uuid, Path, description = "User id")),
    responses(
        (status = 200, body = UserDto),
        (status = 404, body = crate::error::ErrorBody),
    )
)]
pub async fn get_user(/* ... */) {}

#[derive(OpenApi)]
#[openapi(
    info(title = "API", version = "1.0.0"),
    components(schemas(UserDto, crate::error::ErrorBody))
)]
pub struct ApiDoc;

pub fn documented_router(state: AppState) -> axum::Router {
    let (router, api) = OpenApiRouter::new()
        .routes(routes!(get_user))
        .split_for_parts();

    router
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", api))
        .with_state(state)
}
```

## Version and Package Caveats

- Choose the emitted OpenAPI version explicitly. utoipa 6 can emit 3.2, while many codegen consumers still expect 3.0 or 3.1.
- `utoipa-swagger-ui` serves UI assets; it does not generate the document. Its bundled Swagger UI version is independent of the OpenAPI version.
- `routes!` requires `#[utoipa::path]`; a handler without it does not appear in the spec even when it is registered.
- Plain `Router` sub-apps nested under an `OpenApiRouter` may not contribute metadata. Keep documented and undocumented routers clearly separated.
- `operation_id` collisions break client generators; keep them stable and unique.
- Types used in schemas need their utoipa feature enabled, for example `uuid` for `Uuid` and `chrono` for date types. A missing feature shows up as `ToSchema` not implemented.
- Every type referenced in `responses(...)` or `components(schemas(...))` must itself derive `ToSchema`, including the shared error body.
- Do not publish internal error shapes. Use the shared `ErrorBody` type.
- Keep the spec generation deterministic; sort or fix ordering where the generator allows it, and diff committed output.

## Review Checklist

- One generation strategy is used consistently
- Spec endpoint and Swagger UI endpoint are separate and intentional
- Runtime DTOs and documented schemas share a source
- Every documented operation has an `operation_id`, tag, request schema, and error responses
- `routes!` is used only with `#[utoipa::path]` handlers
- Database rows are mapped to public DTOs before publication
- The emitted OpenAPI version is explicit
- Reusable schemas, errors, security schemes, and parameters live in components
- The generated document is validated or linted in CI or locally
- Swagger UI exposure matches the environment policy

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| utoipa 6.0.0 features, MSRV 1.88, OpenAPI 3.2 support, version-description inconsistency | [utoipa CHANGELOG](https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md), [utoipa docs](https://docs.rs/utoipa/latest/utoipa/) |
| `OpenApiRouter`, `routes!`, `split_for_parts`, duplicate and CONNECT panics | [utoipa-axum](https://docs.rs/utoipa-axum/latest/utoipa_axum/), [OpenApiRouter](https://docs.rs/utoipa-axum/latest/utoipa_axum/router/struct.OpenApiRouter.html) |
| `SwaggerUi::new(...).url(...)` and `.merge(...)` with axum | [utoipa-swagger-ui](https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/) |
| `ToSchema`, `IntoParams`, `OpenApi` derive roles | [utoipa docs](https://docs.rs/utoipa/latest/utoipa/) |
