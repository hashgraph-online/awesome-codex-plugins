# Performance

> Record a release-build baseline first, change one lever, and re-measure the same artifact — binary size, `*_bg.wasm` size, or wall time.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default. Rules are ordered by typical impact, which is this package's ordering, not a measured ranking. A performance claim without a before and after number from the same command is not a result.

## 1. Measure first

`hypercore-default` — Performance work runs on a release build. A debug build's timing, size, and allocation profile are not evidence.

| Goal | Command | Record |
|---|---|---|
| Binary size | `cargo build --release` then `stat -c%s`/`wc -c` on `target/release/<bin>` | bytes, target triple, profile name |
| Build time | `cargo build --release` with a clean `target` (or `cargo clean -p <crate>` for one crate) | wall seconds, machine, crate count |
| WASM size | build, run wasm-bindgen/wasm-pack, then `wc -c` on `*_bg.wasm` | bytes, target, `--target` mode |
| Startup time | the binary's own timing flag or a shell loop with `time`, warm cache, N=20 | median wall time |
| Hot path | `perf`/Instruments profile of a release build, or a timing harness in the crate | function names plus percentages |

`hypercore-default` — Baseline rules:

- One command, one machine, one profile per measurement. Mixing a laptop number with a CI number produces a fictional delta.
- Warm and cold runs are different numbers; say which one is recorded.
- A clean build measures compile time; an incremental build measures link time. State which.
- For a library, measure the consumer binary, because the library alone has no runtime.

`hypercore-default` — Benchmarking crates (`criterion`, `hyperfine`) were not verified for this snapshot and are not mandated here. If the project already uses one, keep it and record the version; if it does not, a shell loop with a warm cache is an acceptable baseline for a first measurement.

## 2. Release profile levers

`official` — Cargo's release defaults are `opt-level = 3`, `debug = false`, `lto = false`, `codegen-units = 16`, `panic = "unwind"`, `strip = "none"`, and `incremental = false` (https://doc.rust-lang.org/cargo/reference/profiles.html). Every strong setting below is therefore an explicit opt-in, never something the project already has.

| Lever | Values | Effect | Cost |
|---|---|---|---|
| `lto` | `true`/`"fat"`, `"thin"`, `false`, `"off"` | Cross-crate inlining and dead-code removal; smaller and faster | Build/link time |
| `codegen-units` | 1–256 (default 16, 256 for incremental) | Fewer units means more whole-program optimization | Parallelism lost, build slower |
| `opt-level` | `0`–`3`, `"s"`, `"z"` | `"z"` also turns off loop vectorization | Size versus speed |
| `panic` | `"unwind"`, `"abort"` | `"abort"` removes unwinding tables | No `catch_unwind`, no backtrace |
| `strip` | `"none"`, `"debuginfo"`, `"symbols"`, `true` | `true` equals `"symbols"` | Debuggability of the shipped artifact |
| `debug` | `false`, `0`–`2`, `"none"`/`"line-tables-only"`/`"full"` | Debug info presence | Size |

`official` — `[profile.*]` sections are "only recognized in the *root* manifest, and ignored in member crates' manifests" (https://doc.rust-lang.org/cargo/reference/workspaces.html). A member that declares its own `[profile.release]` is changing nothing.

`official` — "Tests, benchmarks, build scripts, and proc macros ignore the `panic` setting" (https://doc.rust-lang.org/cargo/reference/profiles.html). So a test suite's behavior must never depend on `panic = "abort"`, and `panic = "abort"` tests need the nightly `panic-abort-tests` flag.

`hypercore-default` — Starting points, each measured before being kept:

```toml
# Shipped CLI or MCP server: smaller binary, no unwinding tables
[profile.release]
lto = "thin"          # "fat" only when the last few percent justify the link time
codegen-units = 1
strip = "debuginfo"   # keep symbols out of the shipped artifact, keep them in a debug split
panic = "abort"

# WASM module: size is the metric, not throughput
[profile.release]
lto = true
codegen-units = 1
opt-level = "z"       # measure "s" too; the docs warn "s" can win
panic = "abort"
strip = "symbols"
```

`hypercore-default` — Change one value per measurement. Two levers in one run produces a number nobody can attribute.

`hypercore-default` — A separate `[profile.dist]` inheriting `release` keeps aggressive settings out of local builds when `dist` drives releases. Its dist-specific configuration belongs to `rules/rust/cli.md`; the `[profile.release]` values above stay this file's, because each is changed with a measurement. `rules/setup/rust.md` sets only the baseline profile values and leaves release-shaping levers here.

## 3. WASM size levers

`official` — The raw `target/wasm32-unknown-unknown/release/foo.wasm` "is not optimized for size and you should not measure it". Measure the generated `foo_bg.wasm` after the wasm-bindgen CLI ran, because the CLI "will automatically strip all unneeded functionality" (https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html).

`official` — `lto = true` "gives LLVM many more opportunities to inline and prune functions … will make the `.wasm` smaller". `opt-level = "s"` can beat `"z"`, and the docs say "Always measure!". `wasm-opt -Os`/`-Oz` post-processing "can often get another 15-20% savings" (https://rustwasm.github.io/docs/book/reference/code-size.html).

`hypercore-default` — Order of attack for a module that is too large:

1. Drop unused `web-sys` features and unused dependencies. This usually beats every compiler flag, and it is the only lever that also shortens builds.
2. Turn off debug info (`strip = "symbols"`, and do not pass `--keep-debug` in the shipped build).
3. `opt-level = "z"` against `"s"`, measured both.
4. `lto = true` with `codegen-units = 1`.
5. `wasm-opt -Os`/`-Oz` as a post-process, when Binaryen is available.
6. `--split-debug-info`/`--split-linked-modules` only when the consumer supports the resulting split; both break most bundlers.

`hypercore-default` — Record the size of the artifact the user downloads, not of an intermediate file. A number from `target/` is not a shipped number.

## 4. Allocation and hot paths

`hypercore-default` — Allocation work follows a measurement. Without a profile, "reduce allocations" is a guess that often trades readability for nothing.

Measured first, then these levers, most local first:

| Symptom | Lever |
|---|---|
| A clone in a loop | Borrow (`&str`, `&[T]`) or move instead of cloning |
| Many small `String` allocations while building one value | Pre-size with `String::with_capacity` / `Vec::with_capacity` |
| Repeated formatting in a hot loop | Format once outside the loop, or write into a reused buffer |
| A `HashMap` lookup per item | Consider sorting plus binary search, or a different key |
| Contention in a server path | Per-task state instead of a shared lock; never hold a lock across `.await` |
| Allocator pressure shown by the profile | A global allocator is a lead, not a default; the candidate crate's own docs report a performance penalty for its hardened mode, and no official Rust page endorses a custom allocator |

`hypercore-default` — In a WASM module, allocations cross a boundary that JavaScript also pays for. Prefer passing `Uint8Array`/`js_sys` types for large payloads over arrays of numbers, and avoid building a `JsValue` per item when one structured value will do.

`hypercore-default` — In a CLI, process startup often dominates a small task. Measure total wall time before optimizing inner loops; a 2 ms loop improvement is invisible against a 40 ms cold start.

## 5. What not to do

`hypercore-default` — Reject these as "optimizations":

- Setting `lto = true` everywhere because it sounds faster; it costs build time and the delta may be inside noise.
- `unsafe` for speed without a stated invariant and a benchmark.
- Rewriting a hot function before a profile names it.
- Claiming a size win from the `target/` artifact instead of the post-bindgen file.
- Comparing a debug build to a release build, or a warm run to a cold one.
- Reporting a percentage from one run; repeat until the number is stable, or report the range.
- Changing `panic` to `"abort"` in a library others depend on; that choice belongs to the final binary.

## 6. Recording the result

`hypercore-default` — A performance change note carries:

```text
artifact: target/release/mytool (aarch64-apple-darwin, profile.release)
before: 4_812_904 bytes   (lto = false, codegen-units = 16, strip = none)
after:  2_140_112 bytes   (lto = "thin", codegen-units = 1, strip = "debuginfo")
command: cargo build --release && wc -c target/release/mytool
```

- Name the artifact, the profile, and the exact command.
- One changed lever per line, so the attribution is visible.
- Keep the losing measurements too; a rejected lever is a useful record.

## Checklist

- [ ] Baseline recorded from a release build, with the artifact path and profile named.
- [ ] The measurement command is stated and repeatable on the same machine.
- [ ] One lever changed per measurement, with the before and after numbers recorded.
- [ ] `[profile.*]` settings live in the root manifest only.
- [ ] WASM size was taken from `*_bg.wasm`, not from the rustc output under `target/`.
- [ ] Unused `web-sys` features and dependencies were checked before compiler flags.
- [ ] `opt-level = "s"` and `"z"` were compared where size is the metric.
- [ ] `panic = "abort"` was not assumed to affect tests, benches, build scripts, or proc macros.
- [ ] Allocation work started from a profile, not from a guess.
- [ ] No `unsafe` was added for speed without an invariant and a benchmark.
- [ ] The change note names the artifact, the profile, the command, and the delta.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| Release profile defaults, `lto`/`codegen-units`/`opt-level`/`strip`/`panic` values and effects, and the test/bench panic exception | https://doc.rust-lang.org/cargo/reference/profiles.html |
| `[profile.*]` is read only from the root manifest | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| Measure `*_bg.wasm` after wasm-bindgen stripped it | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `lto = true`, `opt-level = "s"` versus `"z"`, and the 15–20% `wasm-opt` figure | https://rustwasm.github.io/docs/book/reference/code-size.html |
| `--keep-debug`, `--split-debug-info`, `--split-linked-modules` behavior | https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html |
| `dist` profile separation when `dist` drives releases | https://axodotdev.github.io/cargo-dist/book/reference/concepts.html |
| The measure-change-measure procedure, the lever ordering, and the recording format | this package's convention, not an official Rust requirement |
