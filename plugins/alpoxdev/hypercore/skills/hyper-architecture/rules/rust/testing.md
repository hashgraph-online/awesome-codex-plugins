# Testing

> Drive the binary as a process, snapshot whole transcripts instead of strings, test the WASM boundary where it ships, and call MCP tools without a transport.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default.

## 1. Test at the layer that can fail

`hypercore-default` — Each profile tests a different surface first:

| Profile | Primary test | Tool |
|---|---|---|
| `cli` | Process behavior: exit code, stdout, stderr | `assert_cmd` + `predicates` |
| `cli` | Many small argument cases and usage text | `trycmd` |
| `cli` | Large structured output | `insta` snapshots |
| `wasm` | Exported functions inside a real JS or WASM runtime | `wasm-bindgen-test` via `wasm-pack test` |
| `mcp-server` | Tool functions as plain Rust functions | `cargo test` |
| `mcp-server` | One round trip over the chosen transport | an integration test driving the stdio stream |
| `library` | Public API behavior and error variants | `cargo test` unit and integration |

A unit test that calls an internal helper does not prove the CLI works; a process test that only checks the exit code does not prove the message. Test both where both are contractual.

## 2. `assert_cmd`

`official` — `assert_cmd` 2.2.2 belongs in `[dev-dependencies]` together with `predicates` (https://rust-cli.github.io/book/print.html). Two macro forms exist: `assert_cmd::pkg_name!()` reads `CARGO_PKG_NAME` at compile time, and `cargo_bin!("bin-name")` resolves `env!("CARGO_BIN_EXE_<bin>")`. The latter "only works inside integration tests/benches", because Cargo sets that variable only there (https://docs.rs/assert_cmd/latest/assert_cmd/, https://doc.rust-lang.org/cargo/reference/cargo-targets.html). `crate_name!` is deprecated since 2.1.0 in favor of `pkg_name!`, and `Command::cargo_bin` was un-deprecated in 2.1.3.

```toml
[dev-dependencies]
assert_cmd = "2.2"
predicates = "3.1"
```

```rust
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn rejects_unknown_target() {
    Command::cargo_bin("mytool")
        .unwrap()
        .args(["build", "--target", "nope"])
        .assert()
        .failure()
        .code(2)
        .stdout(predicate::str::is_empty())
        .stderr(predicate::str::contains("invalid value"));
}
```

`hypercore-default` — Assert on the contract, not the prose:

- Exit code, stdout emptiness, and one stable substring from stderr. A full-message equality assertion breaks on every help-wording change.
- For a `--json` run, parse the lines and assert on record types and fields, not on the serialized string.
- Never assert on a timestamp, a PID, a temporary path, or terminal width. If output contains one, redact it or drop the assertion.
- One test per failure class in the exit-code table, so a changed mapping fails loudly.

## 3. `trycmd` and `insta`

`official` — `trycmd` 1.2.1 runs whole herds of `.toml`/`.trycmd` cases, with `TRYCMD=dump` and `TRYCMD=overwrite` controlling the snapshot workflow; `snapbox` (1.2.2) is the one-off, customizable layer beneath it; `insta` 1.49.0 covers value and inline snapshots through `cargo-insta` (https://docs.rs/trycmd/latest/trycmd/, https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md).

`hypercore-default` — Pick by shape, not by preference:

| Need | Tool |
|---|---|
| Twenty invocations where each is a command line plus expected stdout/stderr | `trycmd` |
| One large structured value (a report, a parsed manifest, an error tree) | `insta` |
| A single test that needs a custom predicate | plain `assert_cmd` |

`hypercore-default` — Rules:

- Snapshot files are reviewed in the pull request like code. `TRYCMD=overwrite` and `cargo insta accept` are for the author's machine, not for CI.
- A snapshot diff that only changes a version string or a path is regenerated deliberately, not merged blindly.
- Do not hand-maintain expected output strings in test source when a snapshot file would do; that is how two copies of the same prose drift.
- `insta` inline snapshots are for short values that read better beside the assertion. A multi-screen inline snapshot belongs in a file.

## 4. `wasm-bindgen-test`

`official` — `wasm-bindgen-test` 0.3.80 provides `#[wasm_bindgen_test]`, and browsers are driven by `wasm-pack test --node --firefox --chrome --safari --headless` (https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/, https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html).

`hypercore-default` — Two test classes:

- Pure logic tested natively with `cargo test`. This is why the crate carries `rlib` beside `cdylib` and why logic is not behind `#[cfg(target_arch = "wasm32")]`.
- Boundary behavior tested under WASM: a function that touches `web-sys`, a `JsValue` conversion, a promise, or a DOM interaction.

`hypercore-default` — Rules:

- CI runs at least `wasm-pack test --node` for every WASM crate, because a native test cannot see an ABI mistake.
- A browser matrix (`--chrome --firefox --headless`) is added for a crate that touches DOM APIs; it costs CI time and catches the class of bug `--node` misses.
- An async exported function is tested with an `async` test body; a test that polls with a sleep is a flake.
- A `wasm-bindgen-test` case that silently skips when the runtime is absent is worse than no test; assert that the runtime is present.

## 5. MCP server tests

`hypercore-default` — Three layers, cheap to expensive:

1. Tool function over its argument struct, called directly. This covers validation, result mapping, and error variants, and it is a plain `#[test]`.
2. Service function below the tool, called with a test state. This covers business behavior.
3. One transport test: spawn the binary, write a newline-delimited `initialize` request plus one `tools/call`, read the response lines, assert the result. This catches stdout pollution, framing, and version negotiation in one case.

`hypercore-default` — Additional rules:

- A test that writes its own JSON-RPC frames must build them from the SDK's serde types when those types are public, so a protocol-shape change fails at compile time.
- Assert on parsed response values, never on raw frame text; newline handling and key order are not the contract.
- For the HTTP transport, one test posts to the mounted path with a real body and asserts a JSON or streamed response; the router test harness is the same one the Axum guide uses.
- Never leave a transport test that depends on a fixed port. Bind port 0 and read the assigned port, or use an in-process service.
- A stdio test that hangs is a bug in the server's EOF handling; give the child a timeout and kill it, then fail with the captured stderr.

## 6. What not to test

`hypercore-default` — Skip tests that restate the compiler or the framework:

- That a clap flag exists because it was declared; help-text snapshots already cover the user-visible surface.
- That serde round-trips a derive; test the mapping only where a custom serializer or a rename exists.
- That a WASM export is registered; call it.
- That a mock returns what the mock was told to.
- Wall-clock timing, allocation counts, or binary size inside `cargo test`. Those belong to `rules/rust/performance.md` and are measured, not asserted.

## 7. Running the suite

`hypercore-default` — Order, and what each step is for:

```bash
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
wasm-pack test --node            # WASM crates
cargo test --test cli_transcripts # trycmd herd
```

- `--all-targets` is what makes `check` and `clippy` cover tests and benches.
- An ignored test is reported with its `#[ignore]` reason; a silently skipped suite is a false green.
- A test that needs network, a database, or a browser is marked and documented, so a contributor without that dependency knows what did not run.

## Checklist

- [ ] Each profile's primary surface has a test: process behavior, WASM boundary, tool function, or public API.
- [ ] `assert_cmd` and `predicates` are dev-dependencies and the binary is addressed through `cargo_bin!`.
- [ ] CLI assertions check exit code and stable substrings, never full prose.
- [ ] One test covers each exit-code class.
- [ ] `trycmd` or `insta` holds the large expected output, and snapshots are reviewed in the change.
- [ ] Every WASM crate has at least one `wasm-pack test --node` case, plus a browser case when DOM APIs are touched.
- [ ] No WASM test silently skips when its runtime is missing.
- [ ] MCP tools are tested as plain functions, and one transport test drives the real stream.
- [ ] Transport tests bind no fixed port and cannot hang without a timeout.
- [ ] No test asserts a timestamp, a PID, a temporary path, or a serialization order.
- [ ] `cargo check`, `cargo clippy`, and `cargo test` ran with `--all-targets`, and any ignored test is reported.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| `assert_cmd` in dev-dependencies with `predicates` | https://rust-cli.github.io/book/print.html |
| `pkg_name!`, `cargo_bin!`, `CARGO_BIN_EXE_<name>` scope, `crate_name!` deprecation | https://docs.rs/assert_cmd/latest/assert_cmd/, https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| `trycmd` case herds and `TRYCMD=dump`/`TRYCMD=overwrite`; `snapbox` beneath it | https://docs.rs/trycmd/latest/trycmd/ |
| `insta` value and inline snapshots through `cargo-insta` | https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md |
| `wasm-bindgen-test` and `wasm-pack test` runtime flags | https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/, https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html |
| `cdylib` plus `rlib` keeps native tests possible | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| `rmcp` stdio framing and EOF behavior a transport test must exercise | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| The test layering, assertion rules, and skip policy | this package's convention, not an official Rust requirement |
