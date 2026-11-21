# Crate Layout

> Split the binary from the library, give every module one owner, and let features and workspace members carry the differences that would otherwise leak into the crate.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default. Workspace-level tooling (resolver, toolchain, lints, release profiles) is owned by `rules/setup/rust.md`; this file owns what a crate's own structure depends on.

## 1. Thin binary, testable library

`official` — The official Rust CLI book makes the split for one reason: "the logic is testable without spawning a process." Reading the book's structure chapter shows the same shape this file standardizes. A `main.rs` that holds every step cannot be unit-tested and cannot be reused as a library.

`hypercore-default` — The shape:

```text
src/
├── main.rs            # parse, subscriber init, one exit-code mapping
├── lib.rs             # pub fn run(cli: Cli) -> anyhow::Result<()>
├── cli.rs             # clap derive types only
├── commands/
│   ├── mod.rs         # dispatch table: subcommand -> command fn
│   ├── check.rs       # one file per verb, already-parsed input
│   └── compile.rs     # not build.rs: that name belongs to Cargo
├── domain/
│   └── report.rs      # pure logic, no process globals
└── io/
    └── writer.rs      # filesystem, stdout, network
```

- `main.rs` does exactly four things: parse with clap, initialize the subscriber, call `run`, map the result to `ExitCode`.
- `lib.rs` exposes `run`. It does not install a subscriber, read `std::env::args`, or call `process::exit`.
- `cli.rs` holds `Parser`, `Subcommand`, and `Args` types with no logic. This keeps the parse surface greppable and one enum authoritative.
- `commands/<verb>.rs` owns one verb and takes typed arguments. It may call domain and io modules; it does not re-parse strings.
- `domain/` is pure: no environment variables, no clock reads without an injected source, no filesystem.

`hypercore-default` — A file named `build.rs` in `src/` clashes conceptually with Cargo's build script at the crate root; the tree above names the verb module `compile.rs` for that reason.

`official` — A package can hold both targets from one manifest: `[lib]` and the implicit binary from `src/main.rs`. `CARGO_BIN_EXE_<name>` is set for integration tests, which is what makes the black-box CLI test possible without a path guess (https://doc.rust-lang.org/cargo/reference/cargo-targets.html).

## 2. Module ownership

`hypercore-default` — One module, one responsibility, stated in one line at the top of the file:

| Module | Owns | Must not own |
|---|---|---|
| `cli.rs` | Argument shapes and defaults | Execution, I/O |
| `commands/<verb>.rs` | One verb's orchestration | Parsing, output formatting helpers owned elsewhere |
| `domain/<area>.rs` | Decisions and data transforms | Filesystem, network, process globals |
| `io/<device>.rs` | One external boundary | Business decisions |
| `output/` | Human and machine renderers for one result type | Data collection |

`hypercore-default` — A module over roughly 400 lines, or one that needs a section comment to explain its parts, is usually two owners. Split along the seam the comment names rather than by line count.

`official` — Rust module and file names are `snake_case`; this is enforced by the compiler's `non_snake_case` lint for items and by the module file convention. Directories follow the same rule.

## 3. Workspace member split

`official` — A virtual manifest has no `package.edition` to infer a resolver from, so `resolver` must be set explicitly (https://doc.rust-lang.org/cargo/reference/workspaces.html). Resolver version, `rust-version`, and lint tables are configured once at the workspace root; members inherit them.

`hypercore-default` — Split a crate out of a workspace member only for one of these reasons, each of which is a build or ownership fact rather than a preference:

| Reason | Split |
|---|---|
| A second artifact has its own release cadence (a CLI plus a published library) | Separate member for the library, binary depends on it |
| A dependency is needed by one artifact only and dominates build time | Member that owns it, others do not depend on it |
| A boundary must be enforced by the compiler (domain must not see the HTTP crate) | Member per layer, dependency direction in manifests |
| A target platform differs (`wasm32` artifact beside a native tool) | Member per target, or one member with a target-scoped dependency section |

Do not split "for cleanliness". A new member adds a manifest, a publish unit, and a version line to keep consistent.

`hypercore-default` — A member manifest carries only what is specific to that member: `name`, `description`, `[lib]`/`[[bin]]`, its own dependencies, and `[lints] workspace = true`. `edition`, `rust-version`, `version`, `license`, and shared dependency versions come from `[workspace.package]` and `[workspace.dependencies]`.

`official` — Workspace dependencies cannot be declared `optional`, and `features` declared in the workspace table are additive with the ones in the member's `[dependencies]` (https://doc.rust-lang.org/cargo/reference/workspaces.html). So a member cannot make an inherited dependency optional; if a dependency must be optional, it stays in the member.

## 4. Feature policy

`official` — Feature flags are additive by design: enabling a feature never removes behavior another crate relies on. Cargo resolves one feature set per crate for the whole graph.

`hypercore-default` — Rule set:

- `default = []` unless the crate's primary use is impossible without the feature.
- One feature per dependency or behavior, named after what it enables (`serde`, `http`, `telemetry`), not after a release or a customer.
- A feature that only one target needs is not a feature; put the dependency in `[target.'cfg(...)'.dependencies]` instead.
- A feature that changes an API shape is documented in the crate docs and in the changelog, because it is a semver-relevant surface.
- `cfg` gates use `#[cfg(feature = "...")]` and a `#[cfg_attr(docsrs, doc(cfg(...)))]` when the crate publishes docs.

`official` — A package-level `default-features = false` override only takes effect reliably in edition 2024 packages on Rust 1.99+, and may be ignored or rejected before that unless the workspace dependency also disables default features (https://doc.rust-lang.org/cargo/reference/workspaces.html). So disable default features at the workspace dependency, not per member, when the crate must not pull them.

## 5. Crate-type and target layout

`official` — Allowed values are `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, and `proc-macro`, and `crate-type` applies only to library and example targets (https://doc.rust-lang.org/cargo/reference/cargo-targets.html).

`hypercore-default` — For a WASM artifact that must also be testable natively:

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[target.'cfg(target_arch = "wasm32")'.dependencies]
wasm-bindgen = "0.2"
```

The `rlib` half is what lets `cargo test` build the same code for the host. The target-scoped dependency keeps `wasm-bindgen` out of the native build, which shortens host compile times.

## 6. What must not be in the crate

`hypercore-default` — Keep these out, because each one silently couples the crate to a process or a host:

- A `main`-only `process::exit` helper called from library code.
- A `lazy_static`/`OnceLock` global holding configuration that could be a parameter.
- A test-only module compiled into the released binary.
- A generated file edited by hand.
- A `#[cfg(test)] pub` escape hatch used by integration tests; export a real constructor instead.
- An absolute path or a machine-specific flag default.

## Checklist

- [ ] `main.rs` parses, initializes the subscriber, calls `run`, and maps one exit code.
- [ ] `lib.rs` exposes the entry function and owns no process globals.
- [ ] `cli.rs` holds clap types only, and one `Subcommand` enum names every verb.
- [ ] Each command module owns one verb and receives typed input.
- [ ] Domain modules contain no filesystem, network, or environment access.
- [ ] A `build.rs` verb module is renamed so it cannot be confused with Cargo's build script.
- [ ] Module and directory names are `snake_case`.
- [ ] A workspace member inherits `edition`, `rust-version`, versions, and lints instead of repeating them.
- [ ] `[profile.*]` sections appear only in the workspace root manifest.
- [ ] Features are additive, documented, and named after what they enable.
- [ ] A WASM crate declares both `cdylib` and `rlib`, with `wasm-bindgen` scoped to the `wasm32` target.
- [ ] No test-only or generated code is reachable from the released artifact.

## Sources

> Checked 2026-11-07. Facts come from the crate and Cargo pages recorded in `references/official/rust/rust-crates-2026-11-07.md`; structural rules are this package's convention.

| Claim | Source |
|---|---|
| The library/binary split keeps logic testable without spawning a process | https://rust-cli.github.io/book/print.html |
| Cargo targets, `crate-type` values, `CARGO_BIN_EXE_<name>` for integration tests | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| Virtual manifests must set `resolver` explicitly; workspace inheritance; optional and additive feature rules | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| Resolver 3 behavior and MSRV fallback | https://doc.rust-lang.org/cargo/reference/resolver.html |
| Edition 2024 and the Rust version it requires | https://doc.rust-lang.org/edition-guide/rust-2024/index.html |
| `[workspace.lints]` scope: the current package only, not dependencies | https://doc.rust-lang.org/cargo/reference/manifest.html |
| `rust-toolchain.toml` fields and the legacy override precedence | https://rust-lang.github.io/rustup/overrides.html |
| `wasm-bindgen` target guidance and the `cdylib` example manifest | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml |
| Module naming and the directory layout above | this package's convention, not an official Rust requirement |
