# WASM

> Pick the target before the tooling, produce the module from `cdylib`, measure the post-`wasm-bindgen` artifact, and keep the JavaScript boundary typed.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default.

## 1. Two architectures, one profile

`official` — `wasm32-unknown-unknown`, `wasm32-wasip1`, and `wasm32-wasip2` are all Tier 2 with full `std` (https://doc.rust-lang.org/rustc/platform-support.html). They are not interchangeable:

| Target | Host | Output | JavaScript glue |
|---|---|---|---|
| `wasm32-unknown-unknown` + wasm-bindgen | Browser or JavaScript runtime | Core module plus generated JS | Yes |
| `wasm32-wasip1` | WASI runtime | Core module | No |
| `wasm32-wasip2` | Component-model runtime (Wasmtime 17 and above) | A component, not a core module | No |

`official` — wasm-bindgen "is designed to target the `wasm32-unknown-unknown` target … The standard library is largely inert as modules like `std::fs` and `std::net` will simply return errors" (https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html). Its guide documents no WASI target, so a WASI module uses plain rustc output and no bindings.

`official` — `wasm32-wasip1` supports `std`, but "spawning a thread will always return an error", "spawning a process will always return an error", and file APIs go through WASI; gate with `#[cfg(all(target_os = "wasi", target_env = "p1"))]`, and `target_env = "p1"` only exists from Rust 1.80 (https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html). `wasm32-wasip2` "outputs a component as opposed to a core wasm module" and "is not tested in CI at this time" (https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html).

`hypercore-default` — Record the choice in one place, the manifest or a `README` line, with the host it serves. A target installed in the toolchain is not a decision.

## 2. Crate type and target scoping

`official` — `crate-type` accepts `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, and `proc-macro`, and applies only to library and example targets (https://doc.rust-lang.org/cargo/reference/cargo-targets.html). The official wasm-bindgen example manifest uses `[lib] crate-type = ["cdylib"]`, `web-sys` with an explicit feature list, and `[lints] workspace = true` (https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml).

`hypercore-default` — The layout:

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[target.'cfg(target_arch = "wasm32")'.dependencies]
wasm-bindgen = "0.2"
wasm-bindgen-futures = "0.4"
console_error_panic_hook = "0.1"
js-sys = "0.3"

[target.'cfg(target_arch = "wasm32")'.dependencies.web-sys]
version = "0.3"
features = ["Window", "Document", "Element", "HtmlElement"]
```

`official` — Target-scoped dependency sections are what the guide recommends "for better compile times" (https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html).

`official` — Logic that should be testable natively must not sit behind `#[cfg(target_arch = "wasm32")]`; only the binding layer does. That is the reason for `rlib` beside `cdylib`.

## 3. rustwasm moved

`official` — The Rust project published "Sunsetting the rustwasm GitHub org" on 2025-07-21: the working group was archived after about five years of inactivity, `wasm-bindgen` moved "to a new wasm-bindgen organization with new additional maintainers", and the organization itself was archived in September 2025 (https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/). The archived `rustwasm/team` README now states it is no longer where Rust and WebAssembly activity happens.

`hypercore-default` — Consequences a rule set must encode:

- Canonical homes are `github.com/wasm-bindgen/wasm-bindgen` and `github.com/wasm-bindgen/wasm-pack`. Never cite a `rustwasm/*` URL; those redirect.
- The wasm-bindgen guide and wasm-pack book live under `wasm-bindgen.github.io`. The older `rustwasm.github.io/wasm-pack/installer/` URLs are deprecated.
- `wasm-pack` is still maintained: 0.15.1 was published 2026-10-30 and the README credits maintenance by `@drager`.
- `console_error_panic_hook` did not move: its repository is archived, the last push was 2022-12-04, and the crate is stuck at 0.1.7 from 2021-10-11. It still works and is still the documented hook, but it must not be described as actively maintained.
- `serde-wasm-bindgen` also sits outside that organization, but its own docs call it "the officially preferred approach", with "much smaller code size overhead than JSON".

## 4. Versions and toolchain

`official` — `wasm-bindgen` is 0.2.130. The MSRV policy states "Libraries … MSRV of v1.81. CLI tools and their corresponding support libraries have a MSRV of v1.86", with a two-year library MSRV policy and MSRV changes allowed in patch releases (https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md). The published metadata agrees: `rust_version = "1.81"`.

`official` — The CLI is a separate crate, `wasm-bindgen-cli`, version-matched to the library. A version mismatch between the `wasm-bindgen` crate and the CLI is a hard error at binding time, so pin both in the toolchain step or install the CLI with `cargo install wasm-bindgen-cli --version <same>`.

`hypercore-default` — Put the target in `rust-toolchain.toml` so every contributor builds the same artifact:

```toml
[toolchain]
channel = "1.99"
components = ["rustfmt", "clippy"]
targets = ["wasm32-unknown-unknown"]
profile = "minimal"
```

`wasm-pack` 0.15.1 drives the CLI and writes the `package.json`; use it rather than a hand-rolled build script unless the project needs splitting, stripping, or a custom `--target` combination the tool does not expose.

## 5. Deployment target

`official` — `wasm-bindgen --target` accepts `bundler` (the default), `web`, `nodejs`, `deno`, `no-modules`, `experimental-nodejs-module`, and `module` (https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html). The default output assumes the module is natively an ES module, which no JavaScript implementation supports today, so a bundler is required; "the only known bundler known to be fully compatible with `wasm-bindgen` is webpack. Rolldown is also compatible with `rolldown-plugin-wasm`". `--target module` uses source-phase imports and is "currently only supported in ESBuild and Node.js 24".

`hypercore-default` — Choose by consumer, and state the choice:

| Consumer | Target | Note |
|---|---|---|
| Webpack or Rolldown bundler | `bundler` | The default and the documented-compatible path |
| A page with no bundler | `web` | Emits an `init()` that returns a promise |
| CommonJS Node tooling | `nodejs` | `require()`-style output |
| Deno | `deno` | Only where the runtime reads the generated imports |

Vite-specific configuration was not verified for this snapshot, so a Vite + WASM setup needs its own check against that plugin's docs rather than an assertion here.

## 6. Size: measure the right file

`official` — The raw `target/wasm32-unknown-unknown/release/foo.wasm` "is not optimized for size and you should not measure it". Measure the generated `foo_bg.wasm` after the wasm-bindgen CLI ran, because the CLI "will automatically strip all unneeded functionality" (https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html).

`official` — The knobs, from the Rust and WebAssembly book: `lto = true` "gives LLVM many more opportunities to inline and prune functions … will make the `.wasm` smaller"; `opt-level = "s"` or `"z"`, with the explicit warning that "`opt-level = "s"` can sometimes result in smaller binaries than `opt-level = "z"`. Always measure!"; and `wasm-opt -Os`/`-Oz` post-processing, which "can often get another 15-20% savings" (https://rustwasm.github.io/docs/book/reference/code-size.html).

`hypercore-default` — A size profile for a shipped module, with every value an explicit opt-in because Cargo's release defaults are `lto = false`, `codegen-units = 16`, `opt-level = 3`, `panic = "unwind"`, `strip = "none"`:

```toml
[profile.release]
lto = true
codegen-units = 1
opt-level = "z"
panic = "abort"
strip = "symbols"
```

`hypercore-default` — Measurement procedure: build, run wasm-bindgen, take `stat -c%s` (or `wc -c`) of `*_bg.wasm`, then change one lever and repeat. Record both numbers in the change note. `wasm-opt` comes from Binaryen; its install channel and version were not verified for this snapshot, so a project that enables it records how it is installed.

## 7. Panic and abort behavior

`official` — wasm-pack: "By default, Rust panics in WebAssembly compile with `panic=abort`, which aborts the WebAssembly instance on panic". `--panic-unwind` switches to nightly with `-Z build-std=std,panic_unwind` and `-Cpanic=unwind`, passes `--enable-exception-handling` to `wasm-opt`, and even then "the actual 'panic = recoverable JavaScript exception' behaviour requires runtime glue from your bindings layer" (https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html).

`official` — wasm-bindgen's abort machinery is conditional: hard-abort detection and `set_on_abort` "are enabled automatically when building with `panic=unwind`", while with `panic=abort` you must pass `--force-enable-abort-handler` (https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html). `schedule_reinit()` works in both modes.

`hypercore-default` — Accept `panic = "abort"` as the module's normal failure mode and make the failure readable:

```rust
#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}
```

An uncaught panic then surfaces as a `console.error` line with a message instead of `RuntimeError: Unreachable executed`. The hook crate is archived and stale, which is a maintenance fact to state, not a reason to drop the only documented hook. A project that needs recoverable panics states its nightly requirement and its glue layer; it is not a default.

`official` — The exact default panic strategy of `wasm32-unknown-unknown` itself was not read for this snapshot. The `wasm-pack` and WASI statements above are what is asserted.

## 8. `web-sys` features

`official` — `web-sys` gates "each Web interface behind a cargo feature" to keep build times low, and the API docs list the required feature per type and method — for example `Window::resize_to` needs the `Window` feature (https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html).

`hypercore-default` — Enable exactly the interfaces the code touches. A blanket feature list or `features = ["all"]` multiplies build time and hides which APIs the module actually uses. When a method does not exist on a type, the missing feature is the first thing to check, not a reason to reach for `js_sys` casts.

## 9. Typed boundary

`official` — `tsify` 0.5.8 has `json` as its default feature, and `js` "enables serialization through `serde-wasm-bindgen` … This will be the default in future versions" (https://docs.rs/tsify/latest/tsify/). The `into_wasm_abi` and `from_wasm_abi` attributes are deprecated in favor of `Ts<T>` because "that boundary cannot report failure": `FromWasmAbi::from_abi` returns `Self`, so a serde failure forces `throw_str`, which "will not run destructors" and leaks the partially deserialized value and every already-converted argument. `Ts<T>` moves (de)serialization inside the function where it is an ordinary `Result`. `Ts<Vec<T>>` is unsupported; use `Vec<Ts<T>>`.

```rust
#[derive(serde::Serialize, serde::Deserialize, tsify::Tsify)]
pub struct Options {
    /// Rendered width in CSS pixels.
    pub width: u32,
}

#[wasm_bindgen]
pub fn render(options: Ts<Options>) -> Result<JsValue, JsValue> {
    // Convert `Ts<Options>` into `Options` here; the conversion returns a
    // `Result`, so a malformed argument is an error rather than an abort.
    // ...
}
```

The derive generates the TypeScript declaration; `Ts<T>` carries the value. Do not add `into_wasm_abi`/`from_wasm_abi` attributes to a new type, because they put (de)serialization back on the infallible ABI path. Check the installed `tsify` version's docs for the exact conversion method name rather than copying one from memory.

`official` — `serde_wasm_bindgen::to_value` and `from_value` map `HashMap` to `Map`, a struct to an object, `Vec` and tuples to arrays, and `serde_bytes` to `Uint8Array`; `Serializer::json_compatible()` enables `serialize_missing_as_null`, `serialize_maps_as_objects`, and `serialize_bytes_as_arrays` "when JSON shapes are required"; `serde_wasm_bindgen::preserve` passes JavaScript objects such as `Date` and `RegExp` through untouched (https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/).

`hypercore-default` — Use `serde-wasm-bindgen` for the boundary rather than `serde_json` plus a string, and choose `json_compatible()` only when a JSON shape is a contract with the caller, because it costs size and loses JS-native types.

`official` — Useful CLI flags: `--keep-debug`, `--split-debug-info` with `--debug-info-url`, `--no-typescript`, `--omit-imports`, `--split-linked-modules` (recommended for lazy loading and stricter CSP but breaks most bundlers), `--js-string-builtins` (off by default because webpack fails on it), and `--ts-typed-array-buffers` (off by default, needs TypeScript 5.7 or later consumers) (https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html).

## Checklist

- [ ] The WASM target and its host are recorded, and `wasm32-unknown-unknown` is not used for a WASI host.
- [ ] `[lib] crate-type` contains `cdylib`, and `rlib` is added when native tests must reach the logic.
- [ ] `wasm-bindgen` and its JS-boundary siblings sit in `[target.'cfg(target_arch = "wasm32")'.dependencies]`.
- [ ] The `wasm-bindgen` crate and `wasm-bindgen-cli` versions match.
- [ ] `rust-toolchain.toml` lists the target, so all contributors build the same module.
- [ ] The `--target` deployment mode matches the consumer, and the bundler compatibility is stated.
- [ ] Size was measured on `*_bg.wasm`, not on the raw rustc output.
- [ ] Every size change records a before and after number from the same command.
- [ ] `web-sys` features match exactly the interfaces used.
- [ ] Boundary structs use `Ts<T>` with `tsify`, and no deprecated `into_wasm_abi` attribute remains on a new type.
- [ ] A panic hook is installed at module init, and the hook crate's maintenance state is stated.
- [ ] No documentation cites a `rustwasm/*` URL.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| Target tiers and `wasm32-wasip1`/`wasm32-wasip2` behavior | https://doc.rust-lang.org/rustc/platform-support.html, https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html, https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html |
| `wasm32-unknown-unknown` design, inert `std`, target-scoped dependencies | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html |
| `crate-type` values and scope | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| The example `cdylib` manifest | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml |
| rustwasm organization sunset and the new homes | https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/, https://raw.githubusercontent.com/rustwasm/team/master/README.md |
| `wasm-bindgen` 0.2.130, MSRV policy, separate CLI crate | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md, https://crates.io/api/v1/crates/wasm-bindgen |
| `wasm-pack` 0.15.1 maintenance and default panic behavior | https://raw.githubusercontent.com/wasm-bindgen/wasm-pack/master/README.md, https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html |
| Deployment `--target` values and bundler compatibility | https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html |
| Measure `*_bg.wasm`; size levers and the 15–20% `wasm-opt` figure | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html, https://rustwasm.github.io/docs/book/reference/code-size.html |
| Abort handling and `set_on_abort` conditions | https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html |
| `console_error_panic_hook` 0.1.7 and archived repository | https://docs.rs/console_error_panic_hook/latest/console_error_panic_hook/ |
| `web-sys` per-interface feature gating | https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html |
| `tsify` `Ts<T>`, deprecated ABI attributes, and `Ts<Vec<T>>` | https://docs.rs/tsify/latest/tsify/ |
| `serde-wasm-bindgen` mappings, `json_compatible()`, `preserve` | https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/ |
| wasm-bindgen CLI flags | https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html |
| The size profile, measurement procedure, and panic-hook rule | this package's convention, not an official Rust requirement |
