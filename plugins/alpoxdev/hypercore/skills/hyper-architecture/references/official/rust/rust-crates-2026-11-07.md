# Rust Crate Ecosystem Official Evidence Snapshot

Read when an installed crate version, a default feature, an MSRV, a target tier, or an MCP specification revision decides the change. This snapshot records the official claims this package relies on and the date each was verified. A project on another version must be reviewed against that version's own behavior.

- last_verified_at: 2026-11-07
- `status`: reviewed from the crates.io registry API, docs.rs, the Cargo Book, the Rust CLI book, the wasm-bindgen and wasm-pack guides, and the MCP specification on 2026-11-07
- `baseline`: stable Rust `1.99.1` (dated `2026-10-15` in the stable channel manifest); clap 4.6.7, clap_complete 4.6.11, anyhow 1.0.104, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23, assert_cmd 2.2.2, predicates 3.1.4, trycmd 1.2.1, snapbox 1.2.2, insta 1.49.0, anstream 1.0.0, anstyle 1.0.14, cargo-dist 0.34.0, cargo-binstall 1.26.2, wasm-bindgen and wasm-bindgen-cli 0.2.130, wasm-bindgen-test 0.3.80, wasm-pack 0.15.1, console_error_panic_hook 0.1.7, serde-wasm-bindgen 0.6.5, tsify 0.5.8, rmcp 3.9.0, schemars 1.2.3, axum 0.8.9, cargo-deny 0.20.2, cargo-machete 0.9.2
- `refresh_when`: a crate major moves, MSRV policy changes, a target tier changes, the MCP specification publishes a new revision, or the rustwasm or wasm-bindgen organization changes again
- `authority`: evidence only; user and project instructions, the installed toolchain, and `Cargo.lock` remain authoritative

## Contents

1. Crate versions
2. Rust toolchain and targets
3. clap
4. Errors, exit codes, and logging
5. CLI output and distribution
6. WASM
7. MCP
8. Cargo and workspace
9. Unverified for this snapshot
10. Sources

## Crate versions

Captured through the crates.io API on 2026-11-07; version is the maximum stable release, with its publish date.

| Crate | Version | Published |
|---|---|---|
| clap | 4.6.7 | 2026-09-14 |
| clap_complete | 4.6.11 | 2026-09-15 |
| anyhow | 1.0.104 | 2026-07-18 |
| thiserror | 2.0.21 | 2026-09-23 |
| tracing | 0.1.44 | 2025-12-18 |
| tracing-subscriber | 0.3.23 | 2026-03-13 |
| assert_cmd | 2.2.2 | 2026-05-11 |
| predicates | 3.1.4 | 2026-02-11 |
| trycmd | 1.2.1 | 2026-07-21 |
| snapbox | 1.2.2 | 2026-05-26 |
| insta | 1.49.0 | 2026-10-03 |
| anstream | 1.0.0 | 2026-02-11 |
| anstyle | 1.0.14 | 2026-03-13 |
| cargo-dist (binary `dist`) | 0.34.0 | 2026-11-02 |
| cargo-binstall | 1.26.2 | 2026-10-31 |
| wasm-bindgen | 0.2.130 | 2026-10-30 |
| wasm-bindgen-cli | 0.2.130 | 2026-10-30 |
| wasm-bindgen-test | 0.3.80 | 2026-10-30 |
| wasm-pack | 0.15.1 | 2026-10-30 |
| console_error_panic_hook | 0.1.7 | 2021-10-11 (stale) |
| serde-wasm-bindgen | 0.6.5 | 2024-02-27 |
| tsify | 0.5.8 | 2026-08-23 |
| rmcp | 3.9.0 | 2026-11-05 |
| schemars | 1.2.3 | 2026-10-12 |
| axum | 0.8.9 | 2026-04-14 |
| cargo-deny | 0.20.2 | 2026-07-09 |
| cargo-machete | 0.9.2 | 2026-04-15 |

Version-confirmed but not recommended for this snapshot: `figment` 0.10.19 (published 2024-05-17) and `config` 0.15.27 (2026-09-30). Neither is an official default for CLI configuration, because the Rust CLI book's configuration chapter is still a stub.

## Rust toolchain and targets

| Claim | Evidence | Caveat |
|---|---|---|
| Stable Rust is `1.99.1`, dated `2026-10-15` | stable channel manifest | The manifest is the reference; a project pins its own channel |
| Edition 2024 shipped in 1.85.0, and `cargo new` writes the 2024 edition | Edition Guide, Cargo manifest docs | A crate on an older edition is not automatically wrong |
| `resolver = "3"` is the edition 2024 default, requires Rust 1.84+, and changes `resolver.incompatible-rust-versions` from `allow` to `fallback` | Cargo resolver docs | Virtual manifests must set it explicitly, because they have no `package.edition` |
| `wasm32-unknown-unknown`, `wasm32-wasip1` (and `-threads`), and `wasm32-wasip2` are Tier 2 with full `std` | rustc platform support | Tier 2 means guaranteed to build, not guaranteed to pass tests |
| `wasm32-wasip1` supports `std`, but threads and processes always error, and file APIs go through WASI; gate with `target_env = "p1"`, available from Rust 1.80 | rustc `wasm32-wasip1` page | WASI p1 is a core module |
| `wasm32-wasip2` outputs a component, needs a Wasmtime 17+ runtime, and "is not tested in CI at this time" | rustc `wasm32-wasip2` page | Do not promise CI coverage for it |
| Both WASI targets compile with `-Cpanic=abort` by default | rustc WASI pages | The `wasm32-unknown-unknown` default was not read |

## clap

| Claim | Evidence |
|---|---|
| Major is 4; the crate has 20 features and 6 defaults (`color`, `error-context`, `help`, `std`, `suggestions`, `usage`) | clap feature list |
| `derive` and `env` are not defaults and must be enabled | clap feature list |
| Derive surface is `Parser`, `Args`, `Subcommand`, `ValueEnum` | clap derive reference |
| `ValueEnum` works only on enums whose variants are unit variants, unless the rest are skipped | clap derive reference |
| `rename_all` defaults to `kebab-case`; `rename_all_env` defaults to `SCREAMING_SNAKE_CASE` | clap derive reference |
| `#[command(version)]` with no expression uses the crate version | clap derive reference |
| Doc comments become `about`/`long_about`, so `#[command(version, about, long_about = None)]` keeps the short form | clap derive reference |
| `Error::exit` prints to stderr with status 2 or to stdout with status 0; `exit_code()` follows that split; `use_stderr()` reports it | clap `Error` docs |
| `clap_complete` offers `generate`, `generate_to`, `Shell`, an `aot` module, and `CompleteEnv`; `generator` and `shells` are deprecated in favor of `aot` | clap_complete docs |

## Errors, exit codes, and logging

| Claim | Evidence |
|---|---|
| `anyhow::Result<T>` is for application code and bundles no `derive(Error)` macro; backtraces are captured on Rust ≥ 1.65 and enabled via `RUST_BACKTRACE`/`RUST_LIB_BACKTRACE` | anyhow docs |
| `thiserror` derives `std::error::Error` and "deliberately does not appear in your public API" | thiserror docs |
| `#[error(transparent)]` on a variant wrapping `anyhow::Error` delegates `Display` and `source` | thiserror docs |
| Exit codes 0–255 are portable; a panic exits 101; `exitcode` provides the BSD sysexits vocabulary | Rust CLI book, exit codes |
| `tracing-subscriber` defaults are `ansi`, `fmt`, `smallvec`, `std`, `tracing-log`; `env-filter` is not a default | tracing-subscriber docs |
| `EnvFilter::DEFAULT_ENV` is `RUST_LOG`; `from_default_env()` adds an ERROR directive when the variable is empty or unset | tracing-subscriber docs |
| `info` as the default level, consistent log prefixes, and `--verbose` or `RUST_LOG` for verbosity | Rust CLI book, human communication |
| `std::io::IsTerminal` distinguishes a terminal from a pipe; machine output is line-delimited JSON with a `type` field | Rust CLI book, machine communication |
| `anstream`'s `AutoStream` accepts ANSI and adapts to the terminal; `anstyle` is the styling type for public APIs | anstream docs |

## CLI output and distribution

| Claim | Evidence |
|---|---|
| The tool is `dist`, formerly `cargo-dist` | cargo-dist README |
| The crates.io package is still `cargo-dist` (0.34.0), and it "should be invocable as `dist ...`" | dist book, install |
| `dist init` writes the config, adds a build profile, and generates `.github/workflows/release.yml`; releases are tag-driven (`v0.1.0`); `dist build` builds the local platform; `dist plan` previews CI | dist book, Rust quickstart |
| The generated `[profile.dist]` inherits `release` with `lto = "thin"` | dist book, concepts |
| The Rust CLI book's configuration chapter is still "TODO / Evaluate crates that exist / Cli-args + multiple configs + env variables" | Rust CLI book |

## WASM

| Claim | Evidence |
|---|---|
| The rustwasm working group was archived in 2024 after about five years of inactivity; `wasm-bindgen` moved to a new organization; the organization was archived in September 2025 | Rust project blog, 2025-07-21 |
| The archived `rustwasm/team` README states it is no longer where Rust and WebAssembly activity happens | rustwasm/team README |
| Canonical homes are `wasm-bindgen/wasm-bindgen` and `wasm-bindgen/wasm-pack`; older `rustwasm.github.io/wasm-pack/installer/` URLs are deprecated | wasm-bindgen README, wasm-pack book |
| `wasm-pack` 0.15.1 was published 2026-10-30 and the README credits maintenance by `@drager` | wasm-pack README, crates.io |
| `console_error_panic_hook` is archived, last pushed 2022-12-04, and stuck at 0.1.7 (2021-10-11) | docs.rs crate page and repository archive flag |
| `serde-wasm-bindgen` is outside that organization but its docs call it "the officially preferred approach", with "much smaller code size overhead than JSON" | serde-wasm-bindgen docs |
| `wasm-bindgen` is 0.2.130; library MSRV is 1.81, CLI and support-library MSRV is 1.86, with a two-year library MSRV policy and MSRV changes allowed in patch releases | wasm-bindgen README, crates.io metadata (`rust_version = "1.81"`) |
| `wasm-bindgen` targets `wasm32-unknown-unknown`; `std::fs` and `std::net` return errors there; target-scoped dependencies are recommended for compile time | wasm-bindgen guide, Rust targets |
| `--target` accepts `bundler` (default), `web`, `nodejs`, `deno`, `no-modules`, `experimental-nodejs-module`, `module`; webpack is fully compatible, Rolldown with `rolldown-plugin-wasm` also works; `module` needs ESBuild or Node.js 24 | wasm-bindgen guide, deployment |
| The raw `target/wasm32-unknown-unknown/release/*.wasm` "is not optimized for size and you should not measure it"; measure `*_bg.wasm` after the CLI stripped it | wasm-bindgen guide, optimize size |
| `lto = true` shrinks the module; `opt-level = "s"` can beat `"z"` and must be measured; `wasm-opt -Os`/`-Oz` can add another 15–20% | Rust and WebAssembly book, code size |
| wasm-pack builds with `panic=abort` by default; `--panic-unwind` requires nightly plus build-std and runtime glue | wasm-pack book, build |
| Hard-abort detection and `set_on_abort` are enabled automatically under `panic=unwind`; with `panic=abort` the `--force-enable-abort-handler` flag is required | wasm-bindgen guide, handling aborts |
| `web-sys` gates each interface behind a feature; the API docs name the required feature per type and method | wasm-bindgen guide, using web-sys |
| `tsify` 0.5.8 defaults to `json`; `js` enables `serde-wasm-bindgen` serialization and will become the default; `into_wasm_abi`/`from_wasm_abi` are deprecated in favor of `Ts<T>`; `Ts<Vec<T>>` is unsupported | tsify docs |
| `serde-wasm-bindgen` maps `HashMap` to `Map`, structs to objects, `Vec` and tuples to arrays, and `serde_bytes` to `Uint8Array`; `json_compatible()` and `preserve` change those mappings | serde-wasm-bindgen docs |
| `wasm-bindgen-test` 0.3.80 provides `#[wasm_bindgen_test]`; browsers run through `wasm-pack test --node --firefox --chrome --safari --headless` | wasm-bindgen-test docs, wasm-pack book |
| Useful CLI flags include `--keep-debug`, `--split-debug-info`, `--no-typescript`, `--omit-imports`, `--split-linked-modules`, `--js-string-builtins`, `--ts-typed-array-buffers` | wasm-bindgen guide, CLI |
| `[lib] crate-type` accepts `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, `proc-macro`, and applies to library and example targets | Cargo targets |

## MCP

| Claim | Evidence |
|---|---|
| `rmcp` 3.9.0 (2026-11-05) is "An official Rust Model Context Protocol SDK implementation with tokio async runtime", alongside `rmcp-macros` | rust-sdk README, crates.io |
| The SDK implements the stable `2026-07-28` specification and stays "fully compatible with the `2025-11-25` release and earlier versions" | rust-sdk README |
| `2026-07-28` is the current protocol version; revisions are Draft, Current, or Final, with a deprecation window of at least 12 months, or at least 90 days under the expedited exception | MCP versioning docs |
| Default features are `base64`, `macros`, `server`, `schemars`, `transport-async-rw`, `uuid`; transports are `transport-io`, `transport-child-process`, `transport-streamable-http-server`, `transport-streamable-http-client-reqwest`, `transport-worker` | rmcp feature list |
| TLS selectors are `reqwest` (rustls, recommended), `reqwest-native-tls`, `reqwest-tls-no-provider` | rmcp docs |
| `#[tool]` derives `name` from the function, `description` from the doc comment, `input_schema` from a `Parameters<T>` argument, and `annotations`; `#[tool_router]`, `#[tool_router(server_handler)]`, and `#[tool_handler]` cover router and handler wiring | rmcp-macros docs, rust-sdk README |
| `inputSchema` and `outputSchema` derive from the fields of `T`; the type name and type documentation are ignored; schemas are JSON Schema draft 2020-12; `schemars` is re-exported | rust-sdk README |
| Under SEP-2106 (`2026-07-28`), `outputSchema` may be any JSON Schema type, and `structuredContent` may be any JSON value | rust-sdk README |
| `StreamableHttpService` is a Tower service mounted with `nest_service`; the service factory runs per request, so shared state must be a `Clone` handle; `2026-07-28` is stateless with no session header, standalone stream, or resumption; `with_json_response(true)` returns one JSON body | rust-sdk README |
| stdio: the server "MUST NOT" write non-MCP data to stdout, "MAY" log to stderr, frames are newline-delimited and contain no embedded newlines, and the server "SHOULD" exit on stdin EOF | MCP stdio transport |
| The logging capability is deprecated (SEP-2577) but still functional | rust-sdk README |
| `list_all_*` helpers walk cursors; unsupported protocol versions are rejected with `UnsupportedProtocolVersionError` | rust-sdk README, MCP versioning docs |

## Cargo and workspace

| Claim | Evidence |
|---|---|
| In a virtual workspace, `resolver` must be set explicitly because there is no `package.edition` to infer from | Cargo workspaces |
| Inheritable package keys include `edition`, `rust-version`, `version`, `license`, `repository`, `authors`, `keywords`, `categories` | Cargo workspaces |
| Workspace dependencies cannot be `optional`, and workspace `features` are additive with a member's own features | Cargo workspaces |
| A package-level `default-features = false` override wins only in edition 2024 packages on Rust 1.99+; earlier it may be ignored or rejected | Cargo workspaces |
| `[workspace.lints]` is respected as of 1.74 and applies to the current package only, not dependencies (which get `--cap-lints`) | Cargo workspaces, manifest |
| `[profile.*]` is recognized only in the root manifest and ignored in member manifests | Cargo workspaces, profiles |
| Release defaults are `opt-level = 3`, `debug = false`, `lto = false`, `codegen-units = 16`, `panic = "unwind"`, `strip = "none"`, `incremental = false` | Cargo profiles |
| `strip` accepts `"none"`, `"debuginfo"`, `"symbols"`, or `true`; `opt-level` accepts `"s"` and `"z"`, where `"z"` turns off loop vectorization; `lto` accepts `true`/`"fat"`, `"thin"`, `false`, `"off"` | Cargo profiles |
| Tests, benchmarks, build scripts, and proc macros ignore the `panic` setting; `panic = "abort"` tests need nightly `panic-abort-tests` | Cargo profiles |
| `rust-version` declares the supported toolchain, and resolver 3 `fallback` prefers packages at or below it, so a stale MSRV caps dependency versions | Cargo manifest, resolver |
| `rust-toolchain.toml` accepts `channel`, `components`, `targets`, `profile`; `channel` and `path` are mutually exclusive; a legacy `rust-toolchain` file wins if both exist | rustup book |
| `cargo-deny` covers `licenses`, `bans`, `advisories`, `sources`; `cargo-machete` exits 0 with no unused dependencies, 1 with at least one, 2 on error | cargo-deny README, cargo-machete README |
| `[lints] workspace = true` plus `[workspace.lints.rust]`/`[workspace.lints.clippy]` is the inheritance mechanism, with shorthand or `{ level, priority }` entries | Cargo manifest |

## Unverified for this snapshot

- **CLI configuration crate.** No official recommendation exists; the CLI book's configuration chapter is a stub. Only versions were checked, so no maintenance claim is made for `figment` or `config`.
- **`exitcode` crate.** The book recommends it, but its version, publish date, and maintenance state were not checked. Rules therefore name the sysexits vocabulary without pinning the crate.
- **`wasm32-unknown-unknown` default panic strategy.** Confirmed for `wasm-pack` builds and the WASI targets only; the rustc page for `wasm32-unknown-unknown` itself was not read.
- **Vite plus WASM.** Vite's own guidance and `vite-plugin-wasm` were not read, so no Vite-specific WASM rule is stated.
- **`wasm-bindgen` 0.2.131+ or a 1.0 roadmap.** Only 0.2.130 and the unreleased changelog were read; no timeline is claimed.
- **`dist` on crates.io.** The book says package names are still `cargo-dist` and may be renamed later; whether a `dist` package exists for this tool was not confirmed.
- **MCP Tasks (SEP-2663).** `rmcp` exposes a `task_manager` module, but the extension's status in the `2026-07-28` specification was not read.
- **`cargo-deny`/`cargo-machete` configuration schema.** Only check names and exit codes were read; the `deny.toml` schema was not opened.
- **`rmcp` 3.9.0 exact import paths** for the parameter wrapper and structured result constructor. They change between minor releases; verify against the installed version.
- **Benchmark harness.** `criterion` and `hyperfine` versions were not checked, so no version is pinned in the performance rules.

## Sources

> Checked 2026-11-07. Every claim above was taken from the pages below on that date; the research lane's source ids are kept in parentheses.

| Claim group | Source |
|---|---|
| Crate versions and publish dates | https://crates.io/api/v1/crates/clap (L-01), https://crates.io/api/v1/crates/wasm-bindgen (L-25), and the same registry endpoint for each crate listed |
| Rust stable channel baseline | https://static.rust-lang.org/dist/channel-rust-stable.toml (L-62) |
| clap derive, features, and exit codes | https://docs.rs/clap/latest/clap/_derive/index.html (L-02), https://docs.rs/crate/clap/latest/features (L-03), https://docs.rs/clap/latest/clap/error/struct.Error.html (L-04), https://docs.rs/clap_complete/latest/clap_complete/ (L-05) |
| `anyhow`, `thiserror`, exit codes | https://docs.rs/anyhow/latest/anyhow/ (L-06), https://docs.rs/thiserror/latest/thiserror/ (L-07), https://rust-cli.github.io/book/in-depth/exit-code.html (L-08) |
| CLI human and machine output, logging guidance | https://rust-cli.github.io/book/in-depth/machine-communication.html (L-09), https://rust-cli.github.io/book/in-depth/human-communication.html (L-10), https://rust-cli.github.io/book/print.html (L-11) |
| `tracing-subscriber` and `EnvFilter` | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ (L-61) |
| `anstream` and `anstyle` | https://docs.rs/anstream/latest/anstream/ (L-15) |
| Test crates | https://docs.rs/assert_cmd/latest/assert_cmd/ (L-12), https://docs.rs/trycmd/latest/trycmd/ (L-13), https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md (L-14) |
| `dist` and its book | https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md (L-16), https://axodotdev.github.io/cargo-dist/book/install.html (L-17), https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html (L-19), https://axodotdev.github.io/cargo-dist/book/reference/concepts.html (L-20) |
| rustwasm sunset and new homes | https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/ (L-22), https://raw.githubusercontent.com/rustwasm/team/master/README.md (L-23) |
| wasm-bindgen versions, MSRV, targets, deployment, size, aborts, CLI | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md (L-24), https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html (L-30), https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html (L-26), https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html (L-29), https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html (L-28), https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html (L-27) |
| wasm-pack build and test behavior | https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html (L-37), https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html (L-38), https://raw.githubusercontent.com/wasm-bindgen/wasm-pack/master/README.md (L-39) |
| `web-sys` features, `wasm-bindgen-test`, panic hook, serde bridge, tsify | https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html (L-31), https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/ (L-33), https://docs.rs/console_error_panic_hook/latest/console_error_panic_hook/ (L-34), https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/ (L-35), https://docs.rs/tsify/latest/tsify/ (L-36) |
| Rust and WebAssembly size guidance | https://rustwasm.github.io/docs/book/reference/code-size.html (L-40) |
| Rust target tiers and WASI targets | https://doc.rust-lang.org/rustc/platform-support.html (L-42), https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html (L-43), https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html (L-44) |
| MCP SDK, macros, features, transports | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md (L-45), https://docs.rs/rmcp/latest/rmcp/ (L-46), https://docs.rs/crate/rmcp/latest/features (L-47), https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html (L-48) |
| MCP stdio transport and versioning | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md (L-49), https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md (L-51) |
| Cargo workspaces, resolver, profiles, manifest, targets | https://doc.rust-lang.org/cargo/reference/workspaces.html (L-52), https://doc.rust-lang.org/cargo/reference/resolver.html (L-53), https://doc.rust-lang.org/cargo/reference/profiles.html (L-54), https://doc.rust-lang.org/cargo/reference/manifest.html (L-55), https://doc.rust-lang.org/cargo/reference/cargo-targets.html (L-56) |
| Edition 2024 and toolchain override | https://doc.rust-lang.org/edition-guide/rust-2024/index.html (L-57), https://rust-lang.github.io/rustup/overrides.html (L-58) |
| Supply-chain checks | https://raw.githubusercontent.com/EmbarkStudios/cargo-deny/main/README.md (L-59), https://raw.githubusercontent.com/bnjbvr/cargo-machete/main/README.md (L-60) |
