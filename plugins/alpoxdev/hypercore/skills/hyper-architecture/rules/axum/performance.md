# Performance

> Measure the release build, spend the first effort on the deploy profile, pool sizing, and response bytes, and never quote a dev-build number.

Read this when the request names slowness, throughput, latency, memory, binary size, or "최적화" on an Axum service. The architecture track owns where code lives; this file owns the levers that change measured cost.

## Measure first

Record a number before touching any lever, on a release build only. The Cargo defaults are not a performance profile: `opt-level = 3`, `lto = false`, `codegen-units = 16`, `panic = 'unwind'`, `strip = "none"` [L-58].

```bash
cargo build --release
cargo build --release 2>&1 | tail -1        # after each profile change, same machine
```

Then, against the built server with the repository's own load tool or bench harness:

- Record p50/p95 latency and requests per second for one representative read and one write route.
- Record the compressed and uncompressed response bytes for the heaviest JSON response.
- Record the process RSS after the load run and the binary size with `ls -l target/release/<bin>`.
- Check the effective pool size and worker count from the running configuration, not from memory.

A lever whose effect cannot be measured here (no load generator, no staging database, no release toolchain) is reported as not measured. It is never claimed as a gain.

## Rules

Ordered by typical impact for a request-serving Axum binary.

1. **`official` — Set an explicit release profile.** Start with `lto = "thin"`, `codegen-units = 1`, `strip = true`, and `panic = "abort"` for services; `"thin"` "takes substantially less time to run while still achieving performance gains similar to 'fat'", and `true`/"fat" covers the whole dependency graph when final binary and peak speed matter more than link time [L-58]. These settings are always opt-in because the defaults are `lto = false` and `codegen-units = 16` [L-58].
2. **`official` — Size the SQLx pool for production and for the database's own ceiling.** The crate defaults are `max_connections: 10`, `min_connections: 0`, `acquire_timeout: 30s`, `idle_timeout: 10 min`, `max_lifetime: 30 min`, and `test_before_acquire: true`; `Pool::connect` says the default is "mainly suited for testing and light-duty applications" [L-59][L-60]. Cap `max_connections × replicas ≤ server max_connections − superuser reserve`, since the PostgreSQL default is 100 slots with 3 reserved, leaving 97 usable [L-60].
3. **`official` — Buy response bytes only with the codecs you serve.** `CompressionLayer` is feature-gated (`compression-br`, `compression-gzip`, `compression-zstd`, `compression-deflate`) and honours `Accept-Encoding`; enable the subset the clients actually negotiate [L-61]. Use `compress_when` with a predicate over `(StatusCode, Version, &HeaderMap, &Extensions)` so error responses and pre-compressed payloads are skipped [L-69].
4. **`official` — Bound the request and the body separately.** `TimeoutLayer::with_status_code(StatusCode::REQUEST_TIMEOUT, Duration::from_secs(30))` returns a deliberate status instead of dropping the connection [L-62]. A plain `TimeoutLayer` bounds the request, not the body: add `RequestBodyTimeoutLayer`/`RequestBodyDeadlineLayer` and `ResponseBodyTimeoutLayer` when a response can stream indefinitely, and "use both if you want both an idle timeout and an absolute deadline" [L-62].
5. **`official` — Leave tokio worker threads at the default unless a measurement says otherwise.** The default is the machine's available parallelism via `available_parallelism`, it overrides `TOKIO_WORKER_THREADS`, and the docs advise keeping it "on the smaller side"; `current_thread` ignores `worker_threads` entirely [L-57]. The remaining knobs (`max_blocking_threads`, `thread_keep_alive`, `thread_stack_size`, `event_interval`, `global_queue_interval`, `disable_lifo_slot`) are evidence-only changes [L-57].
6. **`hypercore-default` — Consider mimalloc only after the allocator is shown to be the cost.** `#[global_allocator] static GLOBAL: MiMalloc = MiMalloc;` is a drop-in swap, but the crate documents a real tradeoff: the `secure` feature adds guard pages, randomized allocation, and encrypted free lists with "a performance penalty … usually around 10%" [L-63]. No official axum or tokio page endorses a custom allocator, so treat this as a team option, not a rule of the stack [L-63].
7. **`hypercore-default` — Keep the request span cheap.** `tower-http`'s `TraceLayer` plus `tracing` is the supported path; add fields (method, path template, status, latency) rather than formatting bodies, and do not log inside polling hot paths. The middleware rule set owns the layer order; this file only says the tracing configuration is a measured lever when p99 is dominated by logging.

## Do not

- Quote a `cargo run` or `cargo build` debug number as a performance result. Debug builds are unoptimized and their timings say nothing about the release binary [L-58].
- Change `lto`, `codegen-units`, `panic`, or `strip` and call it a win without a before/after build time and runtime number. Every one of these is a build-time/runtime tradeoff [L-58].
- Set `worker_threads` by hand because "more threads is faster". The default already equals available parallelism, and the docs recommend keeping it small [L-57].
- Ship the SQLx defaults to production and then blame the database. `max_connections: 10` with `test_before_acquire: true` is a test configuration [L-59][L-60].
- Set every app replica to a pool size that only works for one replica. The sum across all applications must stay under the server limit [L-60].
- Add compression to responses that are already compressed, tiny, or binary, or let `CompressionLayer` rewrite error bodies by omission of `compress_when` [L-61][L-69].
- Add `mimalloc` with the `secure` feature while holding a latency budget, or present it as official axum guidance [L-63].
- Reach for an async-runtime swap, a different TLS backend, or a driver swap as a "performance fix" inside a review. Those are architecture decisions owned by `rules/axum/platform.md` and the architecture track.

## Checklist

- [ ] Before and after numbers exist for every claimed gain, from a release build.
- [ ] `[profile.release]` states `lto`, `codegen-units`, `panic`, and `strip` explicitly, and the choices are justified against the Cargo defaults.
- [ ] Pool size is explicit, and `max_connections × replicas` fits the database ceiling minus the superuser reserve.
- [ ] `acquire_timeout`, `idle_timeout`, `max_lifetime`, and `test_before_acquire` match the production intent.
- [ ] Compression codecs are enabled by feature and `compress_when` skips errors and non-compressible content.
- [ ] A request timeout returns a status, and streaming responses have body-level timeouts.
- [ ] Worker-thread count is left at the default or changed with a recorded measurement.
- [ ] Any custom allocator is justified by a profile and does not enable `secure` under a latency budget.
- [ ] The change keeps every gate from `stacks/axum/architecture-rules.md` and the checks from `rules/setup/rust.md` passing.

## Sources

> Checked 2026-11-07. Profile and runtime semantics come from the Cargo Book, the tokio and SQLx API docs, and the tower-http crate docs; version numbers come from the crates.io registry.

| Claim | Source |
|---|---|
| Release-profile defaults and `lto`/`codegen-units` semantics | [Profiles – The Cargo Book](https://doc.rust-lang.org/cargo/reference/profiles.html) |
| tokio `worker_threads` default, environment override, and tuning knobs | [tokio::runtime::Builder](https://docs.rs/tokio/latest/tokio/runtime/struct.Builder.html) |
| SQLx pool defaults (`max_connections`, timeouts, `test_before_acquire`) | [sqlx pool options source](https://raw.githubusercontent.com/launchbadge/sqlx/main/sqlx-core/src/pool/options.rs), [sqlx::Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html) |
| PostgreSQL connection ceiling and the multi-application pool budget | [sqlx::Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html) |
| `CompressionLayer` codec features and `Accept-Encoding` behavior | [tower_http::compression](https://docs.rs/tower-http/latest/tower_http/compression/index.html) |
| `compress_when` predicate signature | [tower-http compression predicate source](https://raw.githubusercontent.com/tower-rs/tower-http/main/tower-http/src/compression/predicate.rs) |
| Request and body timeout layers, `with_status_code` | [tower_http::timeout](https://docs.rs/tower-http/latest/tower_http/timeout/index.html) |
| mimalloc global allocator and the `secure` feature penalty | [mimalloc crate](https://docs.rs/mimalloc/latest/mimalloc/) |
| Current crate versions (axum 0.8.9, tokio 1.54.1, tower-http 0.7.1, mimalloc 0.1.52) | [crates.io API](https://crates.io/api/v1/crates/axum) |
