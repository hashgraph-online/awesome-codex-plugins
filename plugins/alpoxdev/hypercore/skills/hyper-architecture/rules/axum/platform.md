# Platform Setup

> Keep runtime, configuration, and observability at the edge

---
## Stable Runtime Baseline

As verified on 2026-11-05, axum is 0.8.9 with MSRV 1.80, and `axum::serve` accepts a `TcpListener` plus anything that converts into a make-service, including a `Router`. Since axum 0.8, `serve` is generic over the listener and IO types, and `Serve::tcp_nodelay` was removed in favor of `serve::ListenerExt` for arbitrary stream properties.

- Keep `#[tokio::main]`, configuration loading, tracing setup, pool creation, state assembly, listener binding, and graceful shutdown in `main.rs` or a `bin/*.rs`.
- Expose a composition function that returns `Router`; the binary calls it. Tests call the same function.
- Build configuration once into a typed struct, validate it, and put it in `AppState`. Do not call `std::env::var` in handlers.
- Initialize tracing once, before serving, and respect `RUST_LOG` or the repository's filter configuration. `EnvFilter` requires `tracing-subscriber`'s `env-filter` feature because it is not a default, and `EnvFilter::from_default_env()` reads `RUST_LOG` and adds an `ERROR`-level directive when the variable is empty or unset.
- Bind explicitly rather than relying on a default address, and log the chosen address with structured fields.
- Use `with_graceful_shutdown` with a signal future so in-flight requests finish on SIGINT/SIGTERM.
- Keep health and readiness endpoints independent of optional dependencies; readiness may check the pool, liveness must not.
- Keep CORS, compression, timeouts, and request IDs in the layer stack, configured from typed values rather than hard-coded per environment.
- Do not change the async runtime, TLS backend, listener model, or deployment manifest inside an architecture review.

## Example

`EnvFilter` is not a default feature of `tracing-subscriber` (defaults are `ansi`, `fmt`, `smallvec`, `std`, `tracing-log`), so the dependency must enable it or the snippet below does not compile.

```toml
[dependencies]
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
```

```rust
use std::net::SocketAddr;

use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer())
        .init();

    let config = crate::config::Config::from_env()?;
    let pool = crate::db::pool::connect(&config.database_url).await?;
    let state = crate::state::AppState::new(config.clone(), pool);

    let app = crate::app(state);
    let addr: SocketAddr = config.bind_address()?;
    let listener = TcpListener::bind(addr).await?;

    tracing::info!(%addr, "server listening");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c().await.expect("ctrl-c handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    tracing::info!("shutdown signal received");
}
```

## Configuration Rules

- One typed `Config` struct with explicit fields and validation. Fail startup on a missing or malformed required value.
- Prefer a single parsing point (`Config::from_env` or the repository's existing config crate) over scattered reads.
- Never log secrets. Redact the database URL and any token fields in `Debug` implementations.
- Keep environment-specific values (bind address, log filter, CORS origins, pool size) in configuration, not in code branches.
- Separate startup configuration from request-time feature flags.

## Observability Rules

- Use `tracing` with spans around request handling, and `tower-http::trace::TraceLayer` for HTTP-level spans.
- Include method, path template, status, and latency in the request span; never include raw bodies or credentials.
- Log errors once, at the boundary where they are handled, with the internal cause.
- Expose metrics only through the repository's existing exporter; do not add a new telemetry stack inside an architecture review.

## Review Checklist

- `main.rs` owns serve, shutdown, tracing, config, and pool creation
- The composition function is callable from tests without binding a port
- Configuration is typed, validated, and free of scattered `env::var` calls
- Secrets are redacted from logs and error bodies
- Graceful shutdown is wired to SIGINT and SIGTERM on Unix
- Health and readiness endpoints are cheap and dependency-appropriate
- CORS and timeout values come from configuration
- No route module binds a listener or initializes global state

## Sources

> Checked 2026-11-07. Runtime and serve behavior were re-verified against the axum and tokio docs; the `env-filter` feature requirement comes from the tracing-subscriber feature list and `EnvFilter` source.

| Claim | Source |
|---|---|
| `axum::serve` with a listener and make-service, `with_graceful_shutdown` | [axum serve](https://docs.rs/axum/latest/axum/fn.serve.html), [Serve](https://docs.rs/axum/latest/axum/serve/struct.Serve.html) |
| `serve` generic over listeners, `tcp_nodelay` removal, MSRV 1.80 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md), [axum 0.8.9 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| Tokio runtime and signal handling | [tokio](https://docs.rs/tokio/latest/tokio/), [tokio::signal](https://docs.rs/tokio/latest/tokio/signal/index.html) |
| `tracing` subscriber setup | [tracing-subscriber](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/) |
| `EnvFilter` requires the `env-filter` feature, and `from_default_env()` reads `RUST_LOG` | [tracing-subscriber features](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/), [EnvFilter source](https://raw.githubusercontent.com/tokio-rs/tracing/master/tracing-subscriber/src/filter/env/mod.rs) |
| `TraceLayer` | [tower-http trace](https://docs.rs/tower-http/latest/tower_http/trace/index.html) |
