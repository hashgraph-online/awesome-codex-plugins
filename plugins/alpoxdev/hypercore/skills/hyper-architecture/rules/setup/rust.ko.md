# Rust Setup Baseline

> stable toolchain 하나를 고정하고, stable key만 쓰는 rustfmt로 format하며, lint 정책을 `[workspace.lints]`에 두고, CI를 warning에서 실패시킵니다.

규칙은 `## Sources`에 열거한 페이지가 그대로 진술할 때 `official`, 이 패키지가 기본값을 골랐을 때 `hypercore-default`입니다. Template은 `assets/templates/setup/rust/`에 있습니다. `axum`, `rust`, `tauri`(`src-tauri`), 그리고 build가 Rust toolchain에서 도는 모든 crate에 적용합니다.

## 1. Detect first

`hypercore-default` — 쓰기 전에 읽습니다.

| 찾을 것 | 의미 |
|---|---|
| `rust-toolchain.toml`, `rust-toolchain` | toolchain 이미 고정됨 |
| `rustfmt.toml`, `.rustfmt.toml` | 적용 중인 formatter config |
| `clippy.toml`, `.clippy.toml` | 적용 중인 Clippy 설정 |
| member `Cargo.toml`의 `[lints]`, root의 `[workspace.lints]` | lint 정책 존재 |
| `[workspace.package].rust-version`, `rust-version` | MSRV 선언 |
| `.cargo/config.toml` | build 설정, `[build] warnings` 가능 |
| `Cargo.toml`의 `edition`, `resolver` | 적용 중인 언어 edition |

`[workspace.lints]`가 이미 있는 workspace는 더 엄격한 level을 유지하고 template은 빈 곳만 채웁니다.

## 2. Toolchain

`official` — 2026-10-15 기준 stable channel은 rustc와 cargo 1.99.1입니다(https://static.rust-lang.org/dist/channel-rust-stable.toml). local machine과 CI가 같은 compiler로 build하도록 patch까지 고정합니다.

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/rust/rust-toolchain.toml` | `rust-toolchain.toml` | channel, component, profile |

`hypercore-default` — `1.99.1`을 `components = ["rustfmt", "clippy"]`, `profile = "minimal"`로 고정합니다. crate가 unstable feature를 실제로 필요로 하지 않는 한 `nightly`를 고정하지 않습니다. 흔한 이유는 rustfmt unstable key와 `panic-abort-tests` 둘이고, 각각 `AGENTS.md`에 기록해야 합니다.

`official` — workspace root에 `edition = "2024"`와 `resolver = "3"`을 두는 것이 현재 조합입니다. resolver version은 생략하면 edition을 따르고 edition 2024는 resolver 3을 고릅니다(https://doc.rust-lang.org/cargo/reference/workspaces.html).

## 3. rustfmt

`official` — rustfmt option은 stable이거나 unstable입니다. unstable option은 nightly toolchain과 `unstable_features = true`를 함께 요구합니다(https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md). `imports_granularity`(#4991)와 `group_imports`(#5083)는 둘 다 unstable이므로 stable toolchain의 `rustfmt.toml`에 넣으면 안 됩니다.

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/rust/rustfmt.toml` | `rustfmt.toml` | stable key만 쓴 formatting option |

`official` — template이 쓰는 stable key는 `edition`, `style_edition`, `max_width`, `hard_tabs`, `tab_spaces`, `newline_style`, `reorder_imports`, `use_field_init_shorthand`, `use_small_heuristics`입니다(https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md).

`official` — `cargo fmt`가 `Cargo.toml`에서 edition을 읽더라도 `edition`을 직접 적습니다. `rustfmt`를 직접 실행하면 기본값이 2015입니다(https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md).

`official` — CI 형태는 `cargo fmt --all --check`입니다. `--check`는 바꿀 것이 없으면 0, 있으면 1로 끝납니다(https://raw.githubusercontent.com/rust-lang/rustfmt/master/README.md).

`hypercore-default` — `max_width = 100`은 rustfmt 기본값과 같아 기존 crate의 diff를 작게 유지합니다. 이전 중에 줄이지 않습니다. width를 바꾸면 모든 file이 다시 format됩니다.

`hypercore-default` — import grouping과 granularity는 option이 nightly 전용이라 수동으로 둡니다. stable 고정에서 이들을 쓰려고 `unstable_features = true`를 더하지 않습니다. channel에 따라 무시되거나 error가 나고, machine마다 formatting이 조용히 달라집니다.

## 4. Clippy and workspace lints

`official` — `[lints.clippy]`는 `{ level, priority }` 항목의 축약입니다. `priority`는 부호 있는 정수이고 낮은(특히 음수) 값이 우선순위가 낮으므로, `priority = -1`로 선언한 group은 기본 `0`인 개별 lint에 집니다(https://doc.rust-lang.org/cargo/reference/manifest.html).

`official` — workspace 정책은 root manifest의 `[workspace.lints.rust]`와 `[workspace.lints.clippy]`에 두고, 각 member는 `[lints] workspace = true`로 참여합니다. 이 상속에서 MSRV는 1.74부터 존중됩니다(https://doc.rust-lang.org/cargo/reference/workspaces.html).

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/rust/workspace-lints.toml` | root `Cargo.toml`에 병합 | `[workspace.lints]` block |
| `assets/templates/setup/rust/clippy.toml` | `clippy.toml` | lint 제안용 MSRV |

`official` — group 기본값은 다음과 같습니다. `clippy::correctness`는 deny 기본이고 compilation을 중단합니다. `clippy::suspicious`, `clippy::complexity`, `clippy::perf`, `clippy::style`은 warn 기본입니다. `clippy::pedantic`과 `clippy::restriction`은 allow 기본이고 문서는 `restriction`을 통째로 켜지 말라고 권합니다(https://doc.rust-lang.org/clippy/lints.html).

`hypercore-default` — `all`, `correctness`, `suspicious`, `complexity`, `perf`, `style`은 `priority = -1`로 group 단위 활성화하고 `pedantic`/`nursery`는 lint 하나씩 골라 씁니다. `restriction`은 절대 통째로 켜지 않습니다.

`hypercore-default` — 기본 개별 lint는 `dbg_macro = "deny"`, `unwrap_used = "warn"`, `todo = "warn"`, `mem_forget = "warn"`입니다. 이미 더 엄격한 집합을 deny하는 crate는 그대로 유지합니다.

`official` — `clippy.toml`은 `msrv`를 받고 MSRV는 Clippy가 내는 제안을 바꿉니다. `Cargo.toml`의 `rust-version`과 같아야 합니다(https://doc.rust-lang.org/clippy/configuration.html).

`hypercore-default` — template의 `clippy.toml`은 `msrv = "1.99"`입니다. MSRV를 올리는 같은 변경에서 workspace `rust-version`에 맞추고 patch는 뺍니다. 어긋나면 선언한 MSRV로 compile할 수 없는 제안이 나옵니다.

## 5. Fix, do not silence

`hypercore-default` — lint를 고칩니다. 코드가 맞고 lint가 알 수 없을 때만 끄며, 그때도 범위를 좁힙니다.

| 상황 | 잘못된 방식 | 올바른 방식 |
|---|---|---|
| 생성 code나 macro 확장에서 lint 발생 | crate root `#![allow(...)]` | 해당 item에 `#[allow(clippy::x)]`와 이유를 적은 주석 |
| test 전용 pattern | `src/`에서 allow | `#[cfg_attr(test, allow(clippy::x))]` |
| module 전체가 개념상 예외 | module에서 allow | 그 file 안에서만 module 단위 `#![allow]` |
| lint가 실제 bug를 찾음 | `#[allow]` | code를 고침 |

`hypercore-default` — crate 하나의 finding을 없애려고 workspace group level을 넓히지 않습니다. 그 crate에 item 단위 allow를 넣습니다. CI를 통과시키려고 `[workspace.lints]` 항목을 지우는 것은 fix가 아니라 범위 변경입니다.

## 6. CI commands

`official` — Cargo 1.97부터 warning에서 실패시키는 권장 방식은 `CARGO_BUILD_WARNINGS=deny` 또는 `.cargo/config.toml`의 `[build] warnings = "deny"`입니다. `cargo clippy -- -D warnings`는 build cache를 무효화하므로 "therefore not recommended"입니다(https://doc.rust-lang.org/clippy/usage.html).

`hypercore-default` — CI 명령 두 개를 이 순서로 실행합니다.

```bash
cargo fmt --all --check
cargo clippy --all-targets --all-features
```

`hypercore-default` — clippy는 임의로 뒤에 flag를 붙이지 말고 환경 변수로 실행합니다.

```bash
CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets --all-features
```

`hypercore-default` — `--all-targets`는 test, bench, example을 포함하고 `--all-features`는 기본 build가 compile하지 않는 feature 전용 code를 잡습니다. 모든 feature 조합이 compile되지 않는 crate는 이유 없이 `--all-features`를 빼지 말고 그 사실을 문서에 적습니다.

`hypercore-default` — 같은 두 명령을 `*.rs` file의 pre-commit hook(`assets/templates/setup/repo/lefthook.yml`)에서 실행합니다. hook은 `cargo fmt --all`과 `cargo clippy --all-targets --all-features`를 돌립니다.

`hypercore-default` — `cargo clippy --fix`는 `--all-targets`를 포함합니다. source를 다시 쓰므로 local 편의 기능이고 CI 단계가 아닙니다.

## 7. Profiles

`official` — `[profile.*]` section은 root manifest에서만 인식되고 member manifest에서는 무시됩니다(https://doc.rust-lang.org/cargo/reference/workspaces.html).

`hypercore-default` — setup은 performance track이 존재한다고 가정하는 기준선 profile 값만 둡니다. release를 빚는 lever(`lto`, `codegen-units`, `opt-level`, `panic`, `strip`)는 `rules/<stack>/performance.md` 소관이고, 측정과 함께 그곳에서만 바꿉니다.

`hypercore-default` — release profile을 추가할 때는 root `Cargo.toml`에 넣고, `[profile.dev]`/`[profile.test]`는 측정된 필요가 있을 때만 더합니다. member manifest의 `[profile.release]`는 아무것도 바꾸지 않으면서 읽는 사람을 오도합니다.

## Checklist

- [ ] 기존 `rust-toolchain.toml`, `rustfmt.toml`, `clippy.toml`, `[lints]`, `rust-version`을 먼저 읽었습니다.
- [ ] `rust-toolchain.toml`이 `rustfmt`와 `clippy` component를 포함한 stable patch 하나를 고정합니다.
- [ ] `rustfmt.toml`에 stable key만 있고 `imports_granularity`와 `group_imports`가 없습니다.
- [ ] `rustfmt.toml`이 `edition`(edition 2024 crate는 `style_edition`도)을 설정합니다.
- [ ] root manifest에 `[workspace.lints]`가 있고 모든 member가 `[lints] workspace = true`로 참여합니다.
- [ ] Clippy group을 `priority = -1`로 선언했고 `restriction`을 통째로 켜지 않았습니다.
- [ ] `clippy.toml`의 `msrv`가 workspace `rust-version`과 같습니다.
- [ ] CI가 `cargo fmt --all --check` 다음에 `CARGO_BUILD_WARNINGS=deny`로 clippy를 실행합니다.
- [ ] 모든 억제가 item 범위이고 이유 주석을 갖습니다.
- [ ] setup track에서 release profile lever를 바꾸지 않았습니다.

## Sources

> 확인 2026-11-07. 아래 인용 페이지와 `references/official/tooling/tooling-2026-11-07.md`에 기록된 페이지에서 사실을 가져왔습니다.

| Claim | Source |
|---|---|
| stable channel의 rustc와 cargo 1.99.1(manifest 2026-10-15) | https://static.rust-lang.org/dist/channel-rust-stable.toml |
| rustfmt option의 stable/unstable 구분과 `unstable_features` | https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md |
| `imports_granularity`(#4991)와 `group_imports`(#5083)는 unstable | https://raw.githubusercontent.com/rust-lang/rustfmt/master/Configurations.md |
| `cargo fmt --check` 종료 code | https://raw.githubusercontent.com/rust-lang/rustfmt/master/README.md |
| `[lints]` 축약과 `priority` 순서 | https://doc.rust-lang.org/cargo/reference/manifest.html |
| `[workspace.lints]`, `[lints] workspace = true`, 1.74부터 MSRV 존중, resolver와 edition | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| Clippy group 기본값과 `restriction` 활성화 반대 권고 | https://doc.rust-lang.org/clippy/lints.html |
| `clippy.toml`의 `msrv`와 제안에 미치는 영향 | https://doc.rust-lang.org/clippy/configuration.html |
| `-- -D warnings` 대신 `CARGO_BUILD_WARNINGS=deny`, `--fix`는 `--all-targets` 포함 | https://doc.rust-lang.org/clippy/usage.html |
| `[profile.*]`는 root manifest에서만 인식 | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| toolchain 고정, workspace lint level, 억제 정책, CI 명령 쌍 | 위 페이지를 바탕으로 한 이 패키지의 convention |
