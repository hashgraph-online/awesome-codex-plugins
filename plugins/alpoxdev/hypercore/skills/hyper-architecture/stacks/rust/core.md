Stack guide inside `hyper-architecture` for Rust crates that are not Axum servers and not Tauri backends. Read it when `rules/stack-detection.md` routes a target to Rust; from then on this file owns that target's work, and the profile decided in Step 1 selects which gates apply.

- Scope: Use this guide when building, auditing, restructuring, or reviewing a Rust crate whose product surface is a command-line binary, a WebAssembly module, a Model Context Protocol server, or a library crate. It covers crate and module layout, error and logging policy, CLI argument parsing and output contracts, WASM target and binding choices, MCP tool and transport wiring, tests, and measured release work. Do not use it for an Axum HTTP server, a Tauri `src-tauri` crate, a crate whose only signal is a `Cargo.toml` the router has not read, copy-only edits that cross no architecture boundary, or requests that want official crate defaults with no Hypercore conventions.
- Runtime needs: The target's `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` or `.cargo/config.toml`, and source tree when they exist. Version and API claims need the dated snapshot in `references/official/rust/rust-crates-2026-11-07.md`. `cargo check`, `cargo clippy`, `cargo test`, and the project's own build command are the verification surface; no bundled script exists.

@architecture-rules.md
@../../rules/rust/crate-layout.md
@../../rules/rust/errors-and-logging.md
@../../rules/rust/cli.md
@../../rules/rust/wasm.md
@../../rules/rust/mcp-server.md
@../../rules/rust/testing.md
@../../rules/rust/performance.md
@../../references/official/rust/rust-crates-2026-11-07.md

# Rust Crate Architecture

> Decide the crate's profile from the manifest first, then enforce one gate set per profile instead of applying every Rust rule to every crate.

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical file is written in English.

Preserve source code identifiers, CLI commands, file paths, crate names, type names, JSON field names, MCP capability names, and quoted source excerpts in their required or original language. Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens.

</output_language>

<purpose>

- Enforce Hypercore Rust crate architecture before code changes.
- Prove the crate's profile before any profile-specific gate is applied, because a CLI rule and a WASM rule contradict each other on output and panic behavior.
- Keep the crate boundary honest: workspace-wide conventions belong to the setup baseline, this guide owns crate structure and runtime behavior, and the Axum and Tauri guides own their own surfaces.
- Tell official crate behavior from this package's defaults, and mark unresolved topics as unverified instead of asserting them.

</purpose>

<routing_rule>

Use this guide for setup, implementation, review, remediation, or architecture enforcement on a Rust crate that is not an Axum server and not a Tauri backend.

- A crate with an `rmcp` dependency routes here with the `mcp-server` profile even when it also uses `axum` for the MCP transport. The Axum guide is added only when the request touches HTTP routes outside the MCP endpoint.
- A crate that produces a `.wasm` for a JavaScript host routes here with the `wasm` profile. A WASI binary module is the same profile with a different target, not a different guide.
- A crate that is a binary with a command-line interface routes here with the `cli` profile.
- Everything else with a `[package]` and no `axum` dependency routes here with the `library` profile.

Do not apply these rules to an `axum` service, to a `src-tauri` crate, to a build script or proc-macro-only crate with no runtime surface, or to a request that wants official crate defaults only, in which case the `hypercore-default` rules relax to optional findings.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce a Rust crate whose profile, ownership boundaries, failure behavior, output contract, and release settings are reviewable and stable as it grows. |
| Trigger | Rust work involving crate or module layout, `main.rs` and `lib.rs`, error types, logging, CLI parsing and output, WASM targets and bindings, MCP tools and transports, tests, or release profiles. |
| Scope | Touched Rust sources, `Cargo.toml` and `Cargo.lock`, `rust-toolchain.toml`, `.cargo/config.toml`, profile sections, tests, the matching rule files, and small reversible fixes. |
| Authority | User and project instructions outrank this guide. Official crate documentation controls API facts. The installed toolchain and locked dependency versions control project behavior. Hypercore defaults are recommendations until the project adopts them. |
| Evidence | Read the manifest, the lockfile, the toolchain file, the entry points, and the touched source and tests. Use the dated snapshot when a version or an API defaults question decides the change. |
| Tools | Read, search, edit, `cargo check`, `cargo clippy`, `cargo test`, `cargo build --release`, and the project's own packaging command. Gate dependency installs, publishing, WASM post-processing installs, and any deploy. |
| Loop | One review or remediation pass, then at most two verify-repair rounds against the Step 3 gates for the active profile. A change stays only when it is inside the touched scope and passes those gates. |
| Output | Korean findings or implementation summary with the profile, `official` and `hypercore-default` labels, changed files, verification evidence, and remaining risk. |
| Verification | `cargo check`, `cargo clippy`, and the touched tests for the active profile, plus the profile's own artifact check (binary run, `*_bg.wasm` size, MCP message exchange). |
| Stop condition | Stop when the profile is proven from a read manifest, the applicable gates pass or are reported as blockers, and the evidence is recorded. |

</instruction_contract>

<activation_examples>

Positive:

- `이 Rust CLI 구조를 서브커맨드 늘리기 전에 정리해줘.` (`Cargo.toml` has `clap`, no `axum`)
- `Refactor this Rust crate into a thin main plus a testable lib, no behavior change.`
- `이 wasm-bindgen 크레이트 크기 줄이고 tsify 타입 붙여줘.`
- `rmcp로 만든 MCP 서버 crate 구조 정리해줘.`
- `hyper-architecture 전체 수정`

Negative:

- `Actix Web이나 Axum 서버 구조를 정리해줘.` That surface belongs to its own guide.
- `src-tauri 안의 Rust 코드를 정리해줘.` Tauri owns that crate.

Boundary:

- `CLI 출력 문구 한 줄만 바꿔줘.` Apply the change and one boundary check only.
- `Use official crate defaults only, not the extra Hypercore conventions.` The guide still applies, but `hypercore-default` strictness relaxes.

</activation_examples>

<trigger_conditions>

Arguments change the remediation scope, not the rules.

| Argument | Meaning |
|---|---|
| missing | Review and fix the requested or touched scope. Untouched drift may be reported as backlog. |
| `전체 수정` | Full remediation across the whole detected crate: every module, target, test, and profile section that is safe to change in this run. |
| `full fix` / `fix all` | Same as `전체 수정`. |
| `공식 기본만` / `official defaults only` | Downgrade `hypercore-default` conventions to optional findings unless `전체 수정` was also requested. |

</trigger_conditions>

<skill_architecture>

- Core (`stacks/rust/core.md`): profile selection, contract, gate order, workflow, verification, stop condition.
- Rules: `stacks/rust/architecture-rules.md` plus the topic files mapped in `reference_routing`.
- References: `references/official/rust/rust-crates-2026-11-07.md` holds the dated crate, target, and specification facts.
- Assets: `assets/evals/rust-cases.jsonl` holds trigger and behavior cases.
- Separate tracks: `rules/setup/rust.md` owns workspace-wide tooling (toolchain pinning, rustfmt, clippy, `[workspace.lints]`, resolver, release profiles, supply-chain checks) and `rules/rust/performance.md` owns measured performance work. This guide references both instead of restating them.

</skill_architecture>

<loop_policy>

- One review or remediation pass per request.
- After remediation, at most two verify-repair rounds against the active profile's gates and the touched checks. A change stays only when it is inside the touched scope and passes.
- A performance claim follows the measure-change-measure loop in `rules/rust/performance.md` and never enters this loop to justify a refactor.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, crate and type names, and the labels `official` and `hypercore-default` in their source form so a report maps one-to-one onto the rule files. `stacks/rust/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/rust/architecture-rules.md` before editing, then open only the files that own the touched surface.

| Touched surface | File |
|---|---|
| `main.rs` and `lib.rs` split, module layout, workspace members, feature flags, crate boundary | `rules/rust/crate-layout.md` |
| `anyhow` versus `thiserror`, exit codes, `ExitCode`, tracing setup, `EnvFilter`, stdout versus stderr | `rules/rust/errors-and-logging.md` |
| clap derive and env features, subcommands, output contracts, NDJSON and `IsTerminal`, completion generation, release binaries with `dist` | `rules/rust/cli.md` |
| WASM target choice, `crate-type`, wasm-bindgen and wasm-pack, size measurement, `tsify`, `web-sys` features, panic hook | `rules/rust/wasm.md` |
| `rmcp` version and specification revision, tool macros, schemars input schemas, stdio and Streamable HTTP transports, stdout discipline | `rules/rust/mcp-server.md` |
| `assert_cmd`, `trycmd` and `insta`, `wasm-bindgen-test`, MCP tool and stdio tests | `rules/rust/testing.md` |
| Measured release work: build time, binary and `*_bg.wasm` size, release profile levers, allocation hot paths | `rules/rust/performance.md` |
| Toolchain pinning, rustfmt, clippy, `[workspace.lints]`, resolver, release profile ownership, supply-chain checks | `rules/setup/rust.md` |
| Version, feature-default, MSRV, target-tier, and specification facts behind a rule | `references/official/rust/rust-crates-2026-11-07.md` |

Workspace-wide conventions belong to `rules/setup/rust.md`. Do not duplicate its resolver, lint, toolchain, or release-profile rules here; this guide only states what a crate's architecture depends on.

</reference_routing>

<support_file_read_order>

1. `stacks/rust/architecture-rules.md` for rule classes and blocking gates.
2. The topic file for the touched surface, in `reference_routing` order.
3. `rules/rust/crate-layout.md` before moving or adding a module, target, or feature.
4. `rules/setup/rust.md` when tooling is in scope but the ownership question is already settled.
5. `references/official/rust/rust-crates-2026-11-07.md` when a version, default feature, MSRV, target tier, or specification revision decides the change.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | Prove the crate is Rust and pick its profile from the manifest | Profile with the deciding field |
| 2 | Load the rule files for the touched surface | Minimal evidence set |
| 3 | Judge planned changes against that profile's gates | Findings with file paths |
| 3.5 | Apply low-risk auto-remediations inside the touched scope | Edits or backlog items |
| 4 | Implement in the order below, then verify | Changed files and evidence |

Step 1 — profile selection. Read the manifest before anything else; the profile decides which later gates exist at all.

```bash
rg -n '^\[package\]|^\[lib\]|^\[\[bin\]\]|^\[workspace\]|^\[features\]|crate-type|^rmcp|^clap|^wasm-bindgen|^axum' Cargo.toml
rg -n 'rust-version|edition|resolver|lints' Cargo.toml
cat rust-toolchain.toml 2>/dev/null; cat .cargo/config.toml 2>/dev/null
```

Then apply this order, which is the detection order `rules/stack-detection.md` already states. The first match wins.

| Order | Profile | Deciding evidence |
|---|---|---|
| 1 | `mcp-server` | `rmcp` in `[dependencies]`, including a crate that also depends on `axum` for the MCP transport |
| 2 | `wasm` | `[lib] crate-type` containing `"cdylib"` together with a `wasm-bindgen` dependency, or a `wasm32-*` target in `rust-toolchain.toml` or `.cargo/config.toml` |
| 3 | `cli` | a `clap` dependency, a `[[bin]]` section, or `src/main.rs` |
| 4 | `library` | a `[package]` with none of the above |

Report the profile with its evidence, the same way the router reports a stack. If the manifest shows two profiles that cannot both be true of one artifact set, report both fields and ask which one the request targets.

Step 3 — critical gates. Apply the cross-cutting block plus only the chosen profile's block. A blocking gate fails even when untouched code shows the same pattern.

Cross-cutting gates:

- The crate's architecture is visible from `Cargo.toml` alone: targets, features, and dependencies state what the crate is, and no module mixes two profiles' conventions.
- Workspace settings are inherited, not duplicated: `edition`, `rust-version`, dependency versions, and lints come from `[workspace.package]`, `[workspace.dependencies]`, and `[workspace.lints]`; profile sections live in the workspace root only.
- Rust module and file names are `snake_case`, and a dependency is added only for a behavior the crate has, with the features the code uses.

`cli` gates:

- `main.rs` is a thin entrypoint and the logic lives in `lib.rs` behind a testable function.
- clap owns parse errors: help and version exit 0 on stdout, a parse error exits 2 on stderr, and the crate does not format or hand-exit those paths itself.
- Human output and machine output are separated by an explicit flag or TTY check, and diagnostics go to stderr.
- Failure classes have distinct non-panic exit codes, and 101 is not written by hand.

`wasm` gates:

- The target is chosen deliberately: `wasm32-unknown-unknown` for a JavaScript host, `wasm32-wasip1` or `wasm32-wasip2` for a WASI host, never mixed by accident.
- `crate-type` includes `cdylib`, and pure logic stays reachable from a native `cargo test`.
- Size is measured on the post-`wasm-bindgen` `*_bg.wasm` artifact, never on the raw rustc output.
- JavaScript-boundary crates sit behind `[target.'cfg(target_arch = "wasm32")'.dependencies]` unless the whole crate is WASM-only.

`mcp-server` gates:

- The server is built on `rmcp`, and the target specification revision is stated: `2026-07-28`, compatible with `2025-11-25` and earlier.
- Transports are declared as features, and the chosen transport matches the deployment: `transport-io` for stdio, `transport-streamable-http-server` for HTTP.
- On stdio, nothing but MCP messages reaches stdout; every log sink writes to stderr structurally.
- Tool input schemas come from a typed `Parameters<T>` whose fields carry the documentation, because the type name and struct documentation are not used.
- Tool handlers delegate to plain functions that a native test can call.

`library` gates:

- The public API is deliberate: public items are reachable from `lib.rs`, internal modules stay private, and `pub(crate)` is the default for shared internals.
- The error type is a `thiserror` enum; `anyhow` does not appear in the public API.
- Feature flags change dependencies or build cost, are additive, and are documented; `default` stays small.
- Nothing in the crate reads process arguments, writes to stdout, or configures a global subscriber, because a library does not own the process.

Step 3.5 — auto-remediation. Apply directly when local, reversible, and low-risk:

- Move logic out of `main.rs` into `lib.rs` and leave `main` as a thin entrypoint returning `ExitCode`.
- Replace a `process::exit` deep in a call path with a returned error and one exit code mapping at the top.
- Move a `println!` diagnostic on a CLI or MCP path to stderr through the logging stack, and add a missing clap feature (`derive`, or `env` when an env fallback exists) instead of hand-parsing.
- Move a `wasm-bindgen` or `web-sys` dependency into the `wasm32` target section, add the `web-sys` feature the used interface requires, and add `rlib` beside `cdylib` so native tests reach the same logic.
- Replace a hand-built MCP `Tool` value with a `#[tool]` function taking `Parameters<T>`.
- Rename a touched `camelCase` or `kebab-case` module to `snake_case` and update `mod` declarations and imports in the same change.

Do not auto-apply broad or breaking changes: swapping an async runtime, replacing `anyhow` with `thiserror` across a public API, changing a crate type or WASM target, changing a published CLI flag or output shape, changing an MCP tool name or input schema, or rewriting the release profile.

Step 4 — implementation order:

1. Confirm the profile and read the manifest, toolchain file, and entry points.
2. Fix crate and module ownership, including the `main.rs`/`lib.rs` split and feature set.
3. Fix the error and logging policy, then the output contract.
4. Apply the profile's own boundary: CLI parsing and subcommands, WASM target and bindings, MCP tools and transports, or the library public API.
5. Add or repair tests, then measure and change performance last, one lever at a time.
6. Run verification.

</workflow>

<required>

- A profile proven from a read manifest, with the field that decided it, before any profile-specific rule is applied.
- The crate boundary respected: workspace-wide conventions deferred to `rules/setup/rust.md`, and the Axum and Tauri surfaces left to their own guides.
- One failure policy per crate: a `thiserror` enum at library boundaries, `anyhow` at the application boundary, distinct non-panic exit codes, and no hand-written 101.
- On `cli`, a thin `main.rs` and a testable `lib.rs`, with clap owning parse errors and output routes separated.
- On `wasm`, an explicit target and crate type, and size measured on the post-`wasm-bindgen` artifact.
- On `mcp-server`, `rmcp` with a stated specification revision, feature-declared transports, and stdout reserved for protocol messages.
- On `library`, a stable public API and no process ownership.
- A report labeling each finding `official` or `hypercore-default`, with unverified topics named as unverified.
- Verification evidence from `cargo check`, `cargo clippy`, the touched tests, and the profile's artifact check.

</required>

<forbidden>

- Applying CLI output or exit-code rules to a WASM module or an MCP server, or applying WASM size rules to a native binary, because the crate's profile was never decided.
- Treating a Rust crate with an `axum` dependency as this guide's target, or a `src-tauri` crate as anything but Tauri's, or duplicating `rules/setup/rust.md` content (resolver, lints, toolchain, release profile) inside a crate rule file.
- Claiming a WASM size from the raw `target/wasm32-unknown-unknown/release/*.wasm` file, or writing anything but MCP messages to stdout in a stdio MCP server.
- Promoting a version, MSRV, or specification revision that the dated snapshot does not state.
- Renaming a published CLI flag, an MCP tool name, or a public library item without a recorded decision, or reporting a gate as passed without the command output that shows it.

</forbidden>

<validation>

- [ ] The crate's profile and its deciding manifest field are recorded.
- [ ] The touched surface's rule file was read, and `공식 기본만` applied when requested.
- [ ] Workspace inheritance is used where the crate is a member, and no profile section sits in a member manifest.
- [ ] `main.rs` and `lib.rs` split correctly for `cli` targets, or the crate states why it has no library half.
- [ ] One error policy is in place: `thiserror` at library boundaries, `anyhow` at the application boundary, non-panic exit codes.
- [ ] stdout carries only the contract: human output or NDJSON behind a flag for `cli`, protocol messages only for a stdio `mcp-server`.
- [ ] `EnvFilter` is enabled with the non-default `env-filter` feature wherever it is used.
- [ ] For `wasm`, the target, crate type, and `web-sys` feature set match the code, and size was taken from `*_bg.wasm`.
- [ ] For `mcp-server`, the specification revision is stated, transports are features, and tool schemas come from typed fields.
- [ ] For `library`, the public API is intentional and no process-global behavior is owned by the crate.
- [ ] `cargo check`, `cargo clippy`, and the touched tests ran, with the profile's artifact check recorded.
- [ ] Findings are labeled `official` or `hypercore-default`, and any unverified topic is named as such.

</validation>

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/rust/rust-crates-2026-11-07.md`, which cites the crate documentation, the Cargo Book, and the MCP specification read on 2026-11-07.

| Claim | Source |
|---|---|
| clap 4.6.7 derive surface, feature defaults, and exit-code contract | https://docs.rs/clap/latest/clap/_derive/index.html, https://docs.rs/crate/clap/latest/features, https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `anyhow` for applications, `thiserror` for library error enums | https://docs.rs/anyhow/latest/anyhow/, https://docs.rs/thiserror/latest/thiserror/ |
| `tracing-subscriber` `env-filter` is not a default feature | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| 0–255 portable exit codes and the panic code 101 | https://rust-cli.github.io/book/in-depth/exit-code.html |
| `wasm32-unknown-unknown` target behavior and `cdylib` layout | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| Size is measured on the post-`wasm-bindgen` `*_bg.wasm` | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `rmcp` 3.9.0 and the `2026-07-28` specification revision | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md |
| stdio transport may not write non-MCP data to stdout | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| Profile order, ownership boundaries, and the `hypercore-default` labels | this package's convention, not an official Rust requirement |
