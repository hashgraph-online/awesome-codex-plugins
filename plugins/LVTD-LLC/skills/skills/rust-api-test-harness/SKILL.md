---
name: rust-api-test-harness
description: Use when adding, changing, testing, or debugging Rust HTTP APIs and services, especially when Codex needs black-box integration tests, random-port app startup, real database test isolation, external HTTP mocks, or CI-ready cargo verification for Actix, Axum, Warp, Rocket, or similar Rust web frameworks.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust API Test Harness
  category: Rust
  tags: rust,api-testing,integration-tests,backend
---

# Rust API Test Harness

Use this skill to make Rust API work test-first, reproducible, and CI-ready.
Prefer black-box tests that exercise the service through HTTP and verify
observable behavior rather than reaching through framework internals.

## Core Workflow

1. Inspect the project first: `Cargo.toml`, workspace layout, existing `src/main.rs`,
   `src/lib.rs`, router/startup modules, `tests/`, migrations, Docker Compose,
   and CI workflows.
2. Find the application boundary. Extract startup code into a reusable function
   if needed so tests can bind a random local port and pass explicit state.
3. Write or update an integration test before changing behavior. Put API tests
   under `tests/` unless the project already has a clear convention.
4. Create a `spawn_app` helper that starts the service once per test case,
   captures the base URL, and owns any disposable test resources.
5. Exercise the public HTTP contract with `reqwest`, not framework-specific
   request objects, unless the project intentionally uses in-process tests.
6. Isolate state. Use real dependencies when behavior depends on their semantics:
   Postgres for SQL behavior, a mock HTTP server for external APIs, and unique
   resource names per test.
7. Keep test helpers as production-quality code. Give failures useful messages,
   hide boilerplate behind small helper methods, and avoid sleeps when readiness
   can be observed.
8. Run the local verification script or equivalent cargo commands before
   finishing.

## Startup Shape

Prefer a startup function that accepts infrastructure instead of creating it
inside the handler module. Actix can listen on a synchronous
`std::net::TcpListener`:

```rust
pub fn run(
    listener: std::net::TcpListener,
    app_state: AppState,
) -> Result<actix_web::dev::Server, std::io::Error> {
    let state = actix_web::web::Data::new(app_state);
    let server = actix_web::HttpServer::new(move || {
        actix_web::App::new()
            .app_data(state.clone())
            .route("/health_check", actix_web::web::get().to(health_check))
    })
    .listen(listener)?
    .run();

    Ok(server)
}
```

For Axum, prefer the same boundary but use Tokio's async listener type:

```rust
pub fn router(app_state: AppState) -> axum::Router {
    axum::Router::new()
        .route("/health_check", axum::routing::get(health_check))
        .with_state(app_state)
}

pub async fn spawn_axum_app() -> TestApp {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("failed to bind random port");
    let port = listener.local_addr().unwrap().port();
    let server = axum::serve(listener, router(test_state().await));
    let server_handle = tokio::spawn(async move { server.await });

    TestApp {
        address: format!("http://127.0.0.1:{port}"),
        http_client: reqwest::Client::new(),
        server_handle,
    }
}
```

## Test Harness Pattern

Use a helper object instead of repeating setup in every test.

```rust
pub struct TestApp {
    pub address: String,
    pub http_client: reqwest::Client,
    pub server_handle: tokio::task::JoinHandle<std::io::Result<()>>,
}

pub async fn spawn_app() -> TestApp {
    let listener = std::net::TcpListener::bind("127.0.0.1:0")
        .expect("failed to bind random port");
    let port = listener.local_addr().unwrap().port();

    let server = my_app::startup::run(listener, test_state().await)
        .expect("failed to start test server");
    let server_handle = tokio::spawn(server);

    TestApp {
        address: format!("http://127.0.0.1:{port}"),
        http_client: reqwest::Client::new(),
        server_handle,
    }
}
```

Add small helper methods when a multi-step user journey appears in more than
one test. Keep the method names behavior-oriented, for example
`post_subscription`, `login`, `create_newsletter`, or `confirm_subscription`.

Do not discard the `JoinHandle` returned by `tokio::spawn`. Keep it in the test
fixture so tests can detect an unexpectedly finished server task and abort it
during teardown instead of hiding server-side panics behind later
connection-refused errors.

## Assertions

- Assert status codes and response headers first.
- Assert persisted side effects through public APIs when possible; query the
  database directly only when the public API has no observation point yet.
- Assert negative cases as first-class behavior: missing fields, malformed
  payloads, duplicate submissions, unauthorized users, upstream failures, and
  timeouts.
- Avoid snapshotting noisy response bodies unless the API contract actually
  includes those exact bytes.

## State And Dependency Isolation

Read `references/database-test-isolation.md` when tests touch a database.
Read `references/external-http-mocks.md` when tests call third-party HTTP APIs.

Default preferences:

- Use real Postgres for Postgres-backed behavior instead of SQLite or in-memory
  substitutes.
- Use one logical database, schema, or unique namespace per test when tests can
  write shared state.
- Run migrations in setup before the app starts.
- Use `wiremock` or an equivalent local mock server for external HTTP APIs.
- Configure timeouts aggressively in tests so failures do not hang.

## Verification

Run the bundled preflight script from the Rust project root when the standard
cargo workflow applies:

```bash
path/to/rust-api-test-harness/scripts/check-rust-service.sh
```

By default, the script runs:

```bash
cargo fmt --all --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
```

Set `RUST_API_TEST_HARNESS_SKIP_CLIPPY=1` to skip only the clippy step. The
script still runs formatting and tests. Use this escape hatch when the project
configures linting separately in CI or when `--all-targets --all-features` is
known to be inappropriate for the local preflight.

If the project does not use all features in CI, mirror the repository's existing
CI commands instead and explain the deviation.

## Reference Files

- `references/database-test-isolation.md`: patterns for Postgres-backed tests,
  migrations, per-test databases, and cleanup tradeoffs.
- `references/external-http-mocks.md`: patterns for testing outbound HTTP
  clients and API workflows with local mocks.
