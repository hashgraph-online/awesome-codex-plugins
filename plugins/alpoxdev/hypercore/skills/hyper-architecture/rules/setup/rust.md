# Rust Setup Baseline

> Pin one stable toolchain, format with stable-only rustfmt keys, put lint policy in `[workspace.lints]`, and fail CI on warnings.

Rules are `official` when an opened page listed under `## Sources` states them and `hypercore-default` when this package chose the default. Templates live in `assets/templates/setup/rust/`. Applies to `axum`, `rust`, `tauri` (`src-tauri`), and any crate whose build runs on the Rust toolchain.

## 1. Detect first

`hypercore-default` — Read before writing:

| Look for | Meaning |
|---|---|
| `rust-toolchain.toml`, `rust-toolchain` | Toolchain already pinned |
| `rustfmt.toml`, `.rustfmt.toml` | Formatter config in force |
| `clippy.toml`, `.clippy.toml` | Clippy settings in force |
| `[lints]` in a member `Cargo.toml`, `[workspace.lints]` in the root | Lint policy exists |
| `[workspace.package].rust-version`, `rust-version` | MSRV declaration |
| `.cargo/config.toml` | Build settings, possibly `[build] warnings` |
| `edition`, `resolver` in `Cargo.toml` | Language edition in force |

A workspace that already has `[workspace.lints]` keeps its stricter levels; the template only fills gaps.

## 2. Toolchain

`official` — rustc and cargo 1.99.1 were the stable channel on 2026-10-15 (https://static.rust-lang.org/dist/channel-rust-stable.toml). Pin the exact patch so a local machine and CI compile with the same compiler.

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/rust/rust-toolchain.toml` | `rust-toolchain.toml` | Channel, components, profile |

`hypercore-default` — Pin `1.99.1` with `components = ["rustfmt", "clippy"]` and `profile = "minimal"`. Do not pin `nightly` unless the crate actually needs an unstable feature; `rustfmt` unstable keys and `panic-abort-tests` are the two common reasons, and each must be recorded in `AGENTS.md`.

`official` — `edition = "2024"` with `resolver = "3"` in the workspace root is the current combination; the resolver version follows the edition when omitted, and edition 2024 selects resolver 3 (https://doc.rust-lang.org/cargo/reference/workspaces.html).

## 3. rustfmt

`official` — Each rustfmt option is either stable or unstable; unstable options need a nightly toolchain plus `unstable_features = true` (https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md). `imports_granularity` (#4991) and `group_imports` (#5083) are both unstable, so a stable-toolchain `rustfmt.toml` must not set them.

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/rust/rustfmt.toml` | `rustfmt.toml` | Stable-only formatting options |

`official` — Stable keys used by the template: `edition`, `style_edition`, `max_width`, `hard_tabs`, `tab_spaces`, `newline_style`, `reorder_imports`, `use_field_init_shorthand`, `use_small_heuristics` (https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md).

`official` — Set `edition` explicitly even though `cargo fmt` reads it from `Cargo.toml`: a direct `rustfmt` invocation defaults to 2015 (https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md).

`official` — The CI form is `cargo fmt --all --check`; `--check` exits 0 when nothing would change and 1 when it would (https://raw.githubusercontent.com/rust-lang/rustfmt/master/README.md).

`hypercore-default` — `max_width = 100` matches rustfmt's own default and keeps the diff small on an existing crate. Do not lower it during a migration; a width change reformats every file.

`hypercore-default` — Import grouping and granularity stay manual because the options are nightly-only. Do not add `unstable_features = true` to make them work on a stable pin — that combination is ignored or errors depending on the channel, and it silently changes formatting between machines.

## 4. Clippy and workspace lints

`official` — `[lints.clippy]` is shorthand for `{ level, priority }` entries; `priority` is a signed integer where lower (especially negative) numbers have lower priority, so a group declared at `priority = -1` loses to an individual lint at the default `0` (https://doc.rust-lang.org/cargo/reference/manifest.html).

`official` — Workspace policy goes in `[workspace.lints.rust]` and `[workspace.lints.clippy]` in the root manifest; each member opts in with `[lints] workspace = true`, and MSRV is respected in that inheritance since 1.74 (https://doc.rust-lang.org/cargo/reference/workspaces.html).

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/rust/workspace-lints.toml` | merge into the root `Cargo.toml` | `[workspace.lints]` block |
| `assets/templates/setup/rust/clippy.toml` | `clippy.toml` | MSRV for lint suggestions |

`official` — Groups and their defaults: `clippy::correctness` is deny-by-default and aborts compilation, `clippy::suspicious`, `clippy::complexity`, `clippy::perf`, and `clippy::style` are warn-by-default, `clippy::pedantic` and `clippy::restriction` are allow-by-default and the docs advise against enabling `restriction` as a whole (https://doc.rust-lang.org/clippy/lints.html).

`hypercore-default` — Enable `all`, `correctness`, `suspicious`, `complexity`, `perf`, and `style` at group level with `priority = -1`, and cherry-pick from `pedantic`/`nursery` one lint at a time. Never blanket-enable `restriction`.

`hypercore-default` — Baseline individual lints: `dbg_macro = "deny"`, `unwrap_used = "warn"`, `todo = "warn"`, `mem_forget = "warn"`. A crate that already denies a stricter set keeps it.

`official` — `clippy.toml` accepts `msrv` and MSRV changes which suggestions Clippy emits; it must match `rust-version` in `Cargo.toml` (https://doc.rust-lang.org/clippy/configuration.html).

`hypercore-default` — The template's `clippy.toml` says `msrv = "1.99"`; set it to the workspace's `rust-version`, patch omitted, in the same change that bumps MSRV. A mismatch produces suggestions the declared MSRV cannot compile.

## 5. Fix, do not silence

`hypercore-default` — Fix the lint. Silence only when the code is correct and the lint cannot know it, and then narrow the suppression:

| Situation | Wrong | Right |
|---|---|---|
| Lint fires on generated or macro-expanded code | `#![allow(...)]` at crate root | `#[allow(clippy::x)]` on the item, with a comment naming the reason |
| Test-only pattern | Allow in `src/` | `#[cfg_attr(test, allow(clippy::x))]` |
| A whole module is conceptually exempt | Allow at the module | Module-level `#![allow]` inside that file only |
| The lint found a real bug | `#[allow]` | Change the code |

`hypercore-default` — Never widen a workspace group level to clear a single crate's finding; put a per-item allow in that crate. Deleting the lint entry from `[workspace.lints]` to make CI pass is a scope change, not a fix.

## 6. CI commands

`official` — Since Cargo 1.97 the recommended way to fail on warnings is `CARGO_BUILD_WARNINGS=deny` or `[build] warnings = "deny"` in `.cargo/config.toml`, because `cargo clippy -- -D warnings` invalidates the build cache and is "therefore not recommended" (https://doc.rust-lang.org/clippy/usage.html).

`hypercore-default` — The two CI commands, in this order:

```bash
cargo fmt --all --check
cargo clippy --all-targets --all-features
```

`hypercore-default` — Run clippy with the environment, not with trailing flags added ad hoc:

```bash
CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets --all-features
```

`hypercore-default` — `--all-targets` covers tests, benches, and examples; `--all-features` catches feature-gated code that a default build never compiles. A crate whose feature combinations do not all compile declares that in its docs rather than dropping `--all-features` without a reason.

`hypercore-default` — The same two commands run in the pre-commit hook for `*.rs` files (`assets/templates/setup/repo/lefthook.yml`); the hook runs `cargo fmt --all` and `cargo clippy --all-targets --all-features`.

`hypercore-default` — `cargo clippy --fix` implies `--all-targets`; it is a local convenience and never a CI step, because it rewrites source.

## 7. Profiles

`official` — `[profile.*]` sections are recognized only in the root manifest and ignored in member manifests (https://doc.rust-lang.org/cargo/reference/workspaces.html).

`hypercore-default` — Setup sets only the baseline profile values the performance track assumes exist. Release-shaping levers (`lto`, `codegen-units`, `opt-level`, `panic`, `strip`) belong to `rules/<stack>/performance.md` and are changed there with a measurement, never here.

`hypercore-default` — When a release profile is added, put it in the root `Cargo.toml` and add `[profile.dev]` / `[profile.test]` only when a measured need exists; a member manifest with `[profile.release]` changes nothing and misleads readers.

## Checklist

- [ ] Existing `rust-toolchain.toml`, `rustfmt.toml`, `clippy.toml`, `[lints]`, and `rust-version` were read first.
- [ ] `rust-toolchain.toml` pins one stable patch with `rustfmt` and `clippy` components.
- [ ] `rustfmt.toml` contains stable keys only; no `imports_granularity` or `group_imports`.
- [ ] `rustfmt.toml` sets `edition` (and `style_edition` for edition-2024 crates).
- [ ] `[workspace.lints]` exists in the root manifest and every member opts in with `[lints] workspace = true`.
- [ ] Clippy groups are declared with `priority = -1`; `restriction` is not blanket-enabled.
- [ ] `clippy.toml` `msrv` equals the workspace `rust-version`.
- [ ] CI runs `cargo fmt --all --check` then clippy with `CARGO_BUILD_WARNINGS=deny`.
- [ ] Every suppression is item-scoped and carries a reason comment.
- [ ] No release-profile lever was changed in the setup track.

## Sources

> Checked 2026-11-07. Facts come from the pages cited below and recorded in `references/official/tooling/tooling-2026-11-07.md`.

| Claim | Source |
|---|---|
| rustc and cargo 1.99.1 on the stable channel (manifest dated 2026-10-15) | https://static.rust-lang.org/dist/channel-rust-stable.toml |
| Stable versus unstable rustfmt options and `unstable_features` | https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md |
| `imports_granularity` (#4991) and `group_imports` (#5083) are unstable | https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md |
| `cargo fmt --check` exit codes | https://raw.githubusercontent.com/rust-lang/rustfmt/master/README.md |
| `[lints]` shorthand and `priority` ordering | https://doc.rust-lang.org/cargo/reference/manifest.html |
| `[workspace.lints]`, `[lints] workspace = true`, MSRV respected since 1.74, resolver and edition | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| Clippy group defaults and the advice against enabling `restriction` | https://doc.rust-lang.org/clippy/lints.html |
| `msrv` in `clippy.toml` and its effect on suggestions | https://doc.rust-lang.org/clippy/configuration.html |
| `CARGO_BUILD_WARNINGS=deny` over `-- -D warnings`; `--fix` implies `--all-targets` | https://doc.rust-lang.org/clippy/usage.html |
| `[profile.*]` recognized only in the root manifest | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| Toolchain pin, workspace lint levels, suppression policy, and the CI command pair | this package's convention built on the pages above |
