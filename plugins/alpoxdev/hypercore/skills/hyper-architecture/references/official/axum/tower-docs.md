# tower and tower-http Official Docs Summary

last_verified_at: 2026-11-05

## Contents

- Stable package snapshot
- Confirmed points from official docs
- Layer ordering rules/axum
- How this affects the skill
- Sources

## Stable package snapshot

Verified from docs.rs and crates.io metadata on 2026-11-05.

| Package | Stable | Notes |
|---|---:|---|
| `tower` | 0.5.3 | `Service`, `Layer`, `ServiceBuilder`, `ServiceExt` behind the `util` feature |
| `tower-http` | 0.7.1 | Trace, CORS, compression, timeout, request-id, limit, and static-file layers |
| `tower-layer` | 0.3.x | `Layer` trait used by all tower middleware |
| `tower-service` | 0.3.x | `Service` trait |

Installed `Cargo.lock` wins. Layer feature names differ per middleware, so check the installed crate's feature list before adding one.

## Confirmed points from official docs

1. axum has no bespoke middleware system; it integrates tower. All tower and tower-http middleware work with axum.
Source: [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

2. `ServiceBuilder` composes layers so that the first `.layer()` added receives the request first. `Router::layer` applies to previously added routes, so the last `.layer()` call is outermost.
Source: [axum middleware ordering](https://docs.rs/axum/latest/axum/middleware/index.html), [ServiceBuilder](https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html)

3. `ServiceExt::oneshot` consumes a service and calls it once when ready. It is the standard way to test a router without a socket.
Source: [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html)

4. A layer whose service can return an error must be paired with `HandleErrorLayer`, because axum expects infallible services. `TimeoutLayer` and rate-limit layers are the common cases.
Source: [axum middleware error handling](https://docs.rs/axum/latest/axum/middleware/index.html), [HandleErrorLayer](https://docs.rs/axum/latest/axum/error_handling/struct.HandleErrorLayer.html)

5. `tower-http` provides `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, `SetRequestIdLayer`, and `PropagateRequestIdLayer` as ready-made layers.
Source: [tower-http](https://docs.rs/tower-http/latest/tower_http/)

6. `ServiceBuilder::map_request`, `map_response`, `then`, and `and_then` cover small ad-hoc transformations without writing a `Service` impl.
Source: [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

## Layer ordering rules/axum

| Composition | Request order |
|---|---|
| `router.layer(A).layer(B).layer(C)` | C, B, A, handler |
| `ServiceBuilder::new().layer(A).layer(B).layer(C)` | A, B, C, handler |
| `route_layer` | Runs only when a route matches |
| `layer` | Runs for matched and unmatched paths, including the fallback |

Response order is the reverse of request order in every case.

## How this affects the skill

- The skill requires the layer stack to be readable top to bottom, which favors `ServiceBuilder`.
- `route_layer` versus `layer` is a gate because it changes whether authentication or tracing observes 404s.
- `HandleErrorLayer` placement is checked whenever a fallible layer is present.

## Sources
> Checked 2026-11-05.
| Claim | Source | Checked |
|---|---|---|
| axum uses tower and tower-http middleware | <https://docs.rs/axum/latest/axum/middleware/index.html> | 2026-11-05 |
| `ServiceBuilder` ordering | <https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html> | 2026-11-05 |
| `ServiceExt::oneshot` | <https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html> | 2026-11-05 |
| `HandleErrorLayer` and fallible layers | <https://docs.rs/axum/latest/axum/error_handling/struct.HandleErrorLayer.html> | 2026-11-05 |
| tower-http layer inventory | <https://docs.rs/tower-http/latest/tower_http/> | 2026-11-05 |
