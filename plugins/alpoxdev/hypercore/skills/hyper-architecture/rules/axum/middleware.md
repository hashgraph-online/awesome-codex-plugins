# Middleware and Layers

> Compose tower layers with an order you can explain

---
## Stable tower Baseline

As verified on 2026-11-05, axum has no bespoke middleware system; it uses tower services, and `tower` 0.5 plus `tower-http` 0.7 provide the common layers. Middleware can be attached to a `Router`, a `MethodRouter`, or a single handler.

- `Router::layer` wraps every route added **before** the call, so the last `.layer()` is the outermost layer and receives the request first.
- `ServiceBuilder` composes top to bottom: the first `.layer()` inside the builder receives the request first. This is the recommended form because it reads in execution order.
- `Router::route_layer` runs only when a route matches. `Router::layer` also runs for unmatched paths. Use `route_layer` for middleware that must not observe or reshape 404 responses.
- axum expects infallible services. A fallible layer such as `TimeoutLayer` needs `HandleErrorLayer` placed **above** it in the same builder to convert errors into responses.
- `middleware::from_fn` and `from_fn_with_state` write async middleware without implementing `Service`; use `from_fn_with_state` whenever the middleware needs `AppState`.
- `from_extractor` is for a type that is both an extractor and middleware; use `from_fn` otherwise.
- Use `tower-http` `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, `RequestIdLayer`, and `PropagateRequestIdLayer` instead of hand-rolling equivalents.
- Request-scoped values belong in request extensions or a typed extractor, never in a mutable global or a `static Mutex`.

## Recommended Order

```rust
use std::time::Duration;

use axum::{error_handling::HandleErrorLayer, Router};
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    cors::CorsLayer,
    request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer},
    timeout::TimeoutLayer,
    trace::TraceLayer,
};

pub fn layers(router: Router<AppState>) -> Router<AppState> {
    router.layer(
        ServiceBuilder::new()
            .layer(SetRequestIdLayer::x_request_id(MakeRequestUuid))
            .layer(TraceLayer::new_for_http())
            .layer(CorsLayer::permissive())
            .layer(HandleErrorLayer::new(|_: BoxError| async {
                StatusCode::REQUEST_TIMEOUT
            }))
            .layer(TimeoutLayer::new(Duration::from_secs(30)))
            .layer(CompressionLayer::new())
            .layer(PropagateRequestIdLayer::x_request_id()),
    )
}
```

The request meets `SetRequestIdLayer` first and the response leaves through `PropagateRequestIdLayer`. Read the list top to bottom as the ingress order.

## Typed Middleware Pattern

```rust
use axum::{
    extract::{Request, State},
    middleware::Next,
    response::Response,
};

pub async fn require_auth(
    State(state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, AppError> {
    let token = req
        .headers()
        .get(axum::http::header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(AppError::Unauthorized)?;

    let user = state.auth.verify(token).await?;
    req.extensions_mut().insert(user);

    Ok(next.run(req).await)
}
```

Mount it with `axum::middleware::from_fn_with_state(state.clone(), require_auth)` on the router that needs it.

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| Layer order is accidental | BLOCKED |
| A fallible layer lacks error handling | BLOCKED |
| Middleware mutates shared state through a global | BLOCKED |
| Auth or tenancy checks live in handlers only | WARNING |
| `route_layer` and `layer` are used interchangeably without a reason | BLOCKED |
| Timeouts, CORS, compression, or tracing are hand-rolled | WARNING |

## Review Checklist

- Layer order is written once and can be read top to bottom
- Fallible layers have a `HandleErrorLayer` above them
- Shared state reaches middleware through `from_fn_with_state` or a stateful layer
- Request-scoped values use extensions or a typed extractor
- Feature-only authorization is scoped, not global
- Middleware does not become a hidden business-logic layer
- CORS policy is explicit and does not combine `permissive()` with credentials
- Timeouts return a deliberate response instead of dropping the connection

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Layer ordering for `.layer()`, `ServiceBuilder`, `route_layer`, `from_fn` variants, `HandleErrorLayer`, state in middleware | [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html) |
| `Router::layer`, `Router::route_layer`, `MethodRouter::layer` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html) |
| `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, request-id layers | [tower-http](https://docs.rs/tower-http/latest/tower_http/) |
| `ServiceBuilder` composition semantics | [tower ServiceBuilder](https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html) |
