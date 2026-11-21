# Testing

> Test the router without a port, and test persistence against a real database

---
## Stable Baseline

As verified on 2026-11-05, `tower` 0.5 provides `ServiceExt::oneshot(self, req)` behind its `util` feature, and `axum-test` 21.1.0 provides `TestServer::new(app)` with a request builder. `oneshot` consumes the service and is therefore a one-request test helper; build a fresh router per request when the router is not `Clone`-cheap in the test's state.

- Test the router directly with `oneshot` for status codes, headers, bodies, layers, and extractor behavior. No port, no race, no sleep.
- Use `axum-test` `TestServer` when the test needs cookies, multipart, or a fluent request builder.
- Use a real database for repository tests, ideally with a transaction rolled back at the end or an isolated schema per test. Never point tests at production data.
- Use `#[sqlx::test]` when the repository already uses SQLx's test macro; otherwise migrate a disposable database in a fixture.
- Cover the error envelope, validation failures, and the changed success path, not only the happy path.
- Keep one integration test per documented public route family when OpenAPI publishing is part of the contract.
- Avoid asserting on the whole serialized body when a field-level assertion is enough; over-specified tests break on unrelated changes.
- Do not test framework wiring (that a route exists because it was registered). Test behavior the API promises.

## Core Rule

Tests exercise the same composition function production uses, with a test state, and assert observable HTTP behavior.

## Router Test Pattern

```rust
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use http_body_util::BodyExt;
use tower::ServiceExt;

#[tokio::test]
async fn returns_404_envelope() {
    let app = crate::app(crate::state::test_state()).await;

    let response = app
        .oneshot(
            Request::builder()
                .uri("/missing")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);

    let body = response.into_body().collect().await.unwrap().to_bytes();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(json["code"], "not_found");
}
```

## axum-test Pattern

```rust
use axum_test::TestServer;

#[tokio::test]
async fn creates_a_user() {
    let server = TestServer::new(crate::app(crate::state::test_state()).await).unwrap();

    let response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({ "email": "a@example.com", "name": "A" }))
        .await;

    response.assert_status_created();
    let body: serde_json::Value = response.json();
    assert_eq!(body["email"], "a@example.com");
}
```

Method names on `TestResponse` depend on the installed version; check the current API rather than assuming `assert_status_created` exists.

## Database Test Pattern

```rust
#[sqlx::test]
async fn repository_finds_user(pool: sqlx::PgPool) -> sqlx::Result<()> {
    sqlx::query("INSERT INTO users (id, email) VALUES ($1, $2)")
        .bind(uuid::Uuid::new_v4())
        .bind("a@example.com")
        .execute(&pool)
        .await?;

    let repo = crate::repositories::users::UsersRepository::new(pool);
    let found = repo.find_by_email("a@example.com").await?;

    assert!(found.is_some());
    Ok(())
}
```

`#[sqlx::test]` provisions and migrates a test database per test according to the crate's test configuration; confirm the setup in the repository before relying on it.

## Review Checklist

- Changed behavior has a test through the router, not only through a service function
- Tests use the same composition function production uses
- Layers and extractors are exercised, not bypassed
- Error and validation paths have at least one test each
- Database tests are isolated and never point at production
- Tests do not depend on wall-clock sleeps or fixed ports
- Assertions target stable contract fields, not incidental serialization order
- `cargo test` passes for the touched crate, and any ignored test is reported

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `ServiceExt::oneshot`, `util` feature, consume-once semantics | [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html) |
| `TestServer`, direct dispatch or random port, request/response flow | [axum-test](https://docs.rs/axum-test/latest/axum_test/) |
| Body collection for assertions | [http-body-util](https://docs.rs/http-body-util/latest/http_body_util/trait.BodyExt.html) |
| `#[sqlx::test]` macro | [sqlx::test](https://docs.rs/sqlx/latest/sqlx/attr.test.html) |
