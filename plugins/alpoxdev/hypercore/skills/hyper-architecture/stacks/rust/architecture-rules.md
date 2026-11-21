# Architecture Rules Reference

> Complete rule set for Rust crates that are not Axum servers or Tauri backends

Note: some rules below are stricter than the crates' own defaults. They are Hypercore conventions, not universal Rust requirements. Rules are labelled `official` when the dated snapshot's opened pages state them and `hypercore-default` when this package chose the default.

Brownfield adoption rule: untouched legacy code may be tracked as migration work instead of an immediate failure when the issue is stylistic or Hypercore-specific. Safety, typing, failure-contract, and protocol-boundary issues still block immediately, especially in touched code.

Workspace-wide conventions are not repeated here. Resolver, toolchain pinning, `[workspace.lints]`, release profile sections, rustfmt, clippy, and supply-chain checks belong to `rules/setup/rust.md`; this file owns what a crate's architecture depends on.

---

## Forbidden

| Category | Forbidden |
|---|---|
| Profile | Applying CLI, WASM, or MCP rules to a crate whose profile was never decided from its manifest |
| Boundary | Restating `rules/setup/rust.md` content inside a crate rule file, or claiming the Axum or Tauri surface for this guide |
| Entry | Business logic in `main.rs`; a binary that parses arguments, executes, and formats results in one function |
| Exit | `std::process::exit` deep in a call path, a hand-written exit code 101, or a panic used as a normal failure path |
| Errors | `anyhow::Error` in a library's public API; `unwrap()`/`expect()` on user or file input outside tests |
| Logging | `println!` for diagnostics; `EnvFilter` used without the `env-filter` feature; a subscriber configured inside a library |
| Output | Diagnostics on stdout; a machine contract that changes shape without a recorded decision |
| WASM | Measuring the raw `target/wasm32-unknown-unknown/release/*.wasm`; a blanket `web-sys` feature list; `Ts<Vec<T>>` |
| MCP | Anything but MCP messages on a stdio server's stdout; a hand-rolled JSON-RPC transport where `rmcp` exists; an unpinned specification revision |
| Features | An additive dependency's feature enabled globally when only one target needs it; `default` features that pull in behavior the crate does not use |
| Paths | Rust modules or files named `camelCase` or `kebab-case` (`userProfile.rs`, `create-user.rs`) |
| Rust | `unsafe` without a stated invariant; a `Box<dyn Error>` returned from a public function; a global `static mut` |
| Git | AI markers, emojis, multi-line commit messages |

---

## Profile Selection

The profile is a manifest fact, not a guess from the request. Report the profile with the field that decided it before reading a profile rule file.

| Order | Profile | Deciding evidence | Owns |
|---|---|---|---|
| 1 | `mcp-server` | `rmcp` in `[dependencies]` | Tool definitions, transports, stdout discipline, protocol version |
| 2 | `wasm` | `crate-type` with `"cdylib"` plus `wasm-bindgen`, or a `wasm32-*` target in the toolchain or cargo config | Target, crate type, bindings, size |
| 3 | `cli` | `clap`, `[[bin]]`, or `src/main.rs` | Commands, output contract, exit codes, distribution |
| 4 | `library` | a `[package]` with none of the above | Public API, error type, features |

A crate with `rmcp` and `axum` is `mcp-server`; the Axum guide joins only for HTTP routes outside the MCP endpoint. A crate with `[[bin]]` and a `wasm32` target is `wasm` with a native test harness, not two artifacts of one kind.

---

## Layer Architecture

```text
Process edge
  main.rs / bin/*.rs        -> argument parse, subscriber init, exit code
       |
       v
Application surface
  lib.rs                    -> run(cli) -> Result<(), E>, one public entry
       |
       v
Commands / tools / exported functions
  commands/<verb>.rs, tools/<tool>.rs, api/<area>.rs
       |
       v
Domain logic
  domain/<area>.rs          -> pure functions, no I/O ownership
       |
       v
Adapters
  io/, http/, fs/, host/    -> files, network, wasm-bindgen boundary, host calls
```

**Data flow rules:**

- The process edge owns argument parsing, subscriber initialization, and the single exit-code mapping. Nothing below it calls `process::exit`.
- A command or tool module receives already-parsed, typed input and returns a typed result; it does not re-parse strings or read environment variables.
- Domain logic stays free of process globals, so it is testable with `cargo test` on the host.
- Adapters own the outside world: file access, HTTP, the `wasm-bindgen` boundary, and the MCP transport. Domain and command code call adapters, never the reverse.
- A library crate ends at the application surface; it never initializes a subscriber, reads argv, or writes to stdout.

---

## Crate Layout Invariants

Read `rules/rust/crate-layout.md` before adding a module, target, feature, or workspace member.

- `main.rs` is thin and `lib.rs` holds `run`. The split exists so the logic is testable without spawning a process.
- One module, one owner. A module that both formats output and performs I/O is a boundary that has not been decided.
- Features are additive and documented. A feature that only one target needs lives in that target's dependency section instead.
- A workspace member inherits `edition`, `rust-version`, dependency versions, and lints. It does not repeat or override them locally without a stated reason.
- Grow the module tree from observable ownership pressure. Do not pre-create empty `services/`, `domain/`, or `adapters/` folders.

---

## Error and Logging Invariants

Read `rules/rust/errors-and-logging.md` for the full policy.

- `thiserror` derives the library error enum. `anyhow` is the application boundary's error type with `.context(...)`. A library's public function does not return `anyhow::Error`.
- Mixing is explicit: a variant wraps `anyhow::Error` with `#[error(transparent)]` when a command needs to carry a library error upward.
- Exit codes are a contract: 0 for success, distinct non-zero codes per failure class, 2 for a clap parse error, and 101 reserved for a panic that was not prevented.
- `tracing` is the logging surface. `EnvFilter` needs `features = ["env-filter"]`, because it is not a default, and `RUST_LOG` unset means the error level rather than a firehose.
- stdout carries the deliverable and stderr carries diagnostics, progress, and logs. A pipe consumer never receives a progress line.
- The subscriber is initialized once, at the process edge, and never in a library function that a test also calls.

---

## CLI Invariants

Read `rules/rust/cli.md` for the full policy.

- clap derive types live in one module (`cli.rs`), one `Subcommand` enum names every verb, and each verb has one command module.
- Derive features are declared explicitly: `derive` always, `env` only when an environment fallback exists.
- Machine output is a contract: a `--json` flag emitting one JSON document per line with a `type` discriminator, enabled when stdout is not a terminal or when the flag is passed.
- A shell-completion path is generated from `clap_complete`, not hand-written.
- Release binaries come from `dist` (package `cargo-dist`) with a tag-driven workflow, and `[profile.dist]` stays separate from `[profile.release]`.

---

## WASM Invariants

Read `rules/rust/wasm.md` for the full policy.

- `wasm32-unknown-unknown` serves a JavaScript host; `wasm32-wasip1` and `wasm32-wasip2` serve a WASI host with no JavaScript glue. The choice is recorded, not implied by whatever target was last installed.
- `crate-type = ["cdylib"]` produces the module; adding `rlib` keeps the same logic reachable from a native test.
- JavaScript-boundary crates sit under `[target.'cfg(target_arch = "wasm32")'.dependencies]`.
- Size is measured on `*_bg.wasm` after wasm-bindgen ran, and every size change records a before and after number.
- `web-sys` features are per interface; the feature list matches the calls in the code.
- Panics are surfaced through the panic hook at module init, and the hook crate's maintenance state is stated rather than assumed.

---

## MCP Server Invariants

Read `rules/rust/mcp-server.md` for the full policy.

- The server uses `rmcp` and states its target revision: `2026-07-28`, compatible with `2025-11-25` and earlier.
- Transports are features: `transport-io` for stdio, `transport-streamable-http-server` for HTTP mounted on a router.
- Each tool is one `#[tool]` function taking `Parameters<T>`; the schema comes from the fields, so field documentation is the schema documentation.
- Tool handlers validate and delegate to a plain function; the macro layer is a transport adapter, not a business layer.
- On stdio, stdout is reserved for protocol frames, and the subscriber writer is set to stderr structurally.
- The legacy HTTP+SSE transport is not promised, and the deprecated logging capability is not the plan for a new server.

---

## Testing Invariants

Read `rules/rust/testing.md` for the full policy.

- `assert_cmd` with `predicates` covers process behavior; the binary is addressed through `cargo_bin!` rather than a hand-built path.
- `trycmd` covers many small CLI transcripts; `insta` covers larger value snapshots. Expected output is not hand-maintained in test source.
- `wasm-bindgen-test` covers the JavaScript boundary, run through `wasm-pack test` for the target that ships.
- MCP tools are tested as plain functions, and one test drives the stdio message exchange.
- A test never asserts incidental serialization order or a wall-clock delay.

---

## Performance Invariants

Read `rules/rust/performance.md` for the measured track.

- Baseline first: build time and artifact size from one named command, on a release build.
- One lever per measurement: `lto`, `codegen-units`, `opt-level`, `strip`, `panic`, or `wasm-opt`, then re-measure the same artifact.
- Cargo's release defaults are `lto = false`, `codegen-units = 16`, `opt-level = 3`, `panic = "unwind"`, `strip = "none"`, so every strong setting is an explicit opt-in.
- `opt-level = "s"` can beat `"z"`; measure both before choosing.
- A claimed gain needs a before and after number from the same command on the same machine.
- Allocation work follows a measurement; a custom allocator is a lead, not a default.

---

## Sources

> Checked 2026-11-07. The crate, toolchain, target, and specification statements restate `references/official/rust/rust-crates-2026-11-07.md`, which cites the pages opened on 2026-11-07.

| Claim | Source |
|---|---|
| clap derive, feature defaults, and exit-code behavior | https://docs.rs/clap/latest/clap/_derive/index.html, https://docs.rs/crate/clap/latest/features, https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `anyhow` at application boundaries, `thiserror` for library errors, `#[error(transparent)]` | https://docs.rs/anyhow/latest/anyhow/, https://docs.rs/thiserror/latest/thiserror/ |
| `env-filter` is not a `tracing-subscriber` default feature | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| Exit codes 0–255, panic code 101, sysexits guidance | https://rust-cli.github.io/book/in-depth/exit-code.html |
| Machine output as line-delimited JSON with a `type` field | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `wasm32-unknown-unknown` and the post-`wasm-bindgen` size measurement | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `rmcp` 3.9.0, the `2026-07-28` revision, tool macros, and transports | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://docs.rs/crate/rmcp/latest/features |
| stdio may not write non-MCP data to stdout | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| Cargo release profile defaults | https://doc.rust-lang.org/cargo/reference/profiles.html |
| The layering, module ownership, and label conventions | this package's convention, not an official Rust requirement |
