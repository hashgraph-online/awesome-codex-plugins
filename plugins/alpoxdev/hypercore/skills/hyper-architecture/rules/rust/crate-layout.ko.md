# Crate 배치

> 바이너리와 라이브러리를 분리하고, 모듈마다 소유자 하나를 두며, crate로 새어 들어올 차이는 기능과 워크스페이스 멤버가 지게 합니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 워크스페이스 수준 툴링(resolver, 툴체인, lint, 릴리스 프로필)은 `rules/setup/rust.md`가 소유하고, 이 파일은 crate 자체 구조가 의존하는 것을 소유합니다.

## 1. 얇은 바이너리, 테스트 가능한 라이브러리

`official` — 공식 Rust CLI 책이 이 분리를 하는 이유는 하나입니다. "로직을 프로세스를 띄우지 않고 테스트할 수 있게" 하려는 것입니다. 책의 구조 장을 읽으면 이 파일이 표준화하는 모양과 같습니다. 모든 단계를 담은 `main.rs`는 단위 테스트할 수 없고 라이브러리로 재사용할 수도 없습니다.

`hypercore-default` — 모양은 이렇습니다.

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

- `main.rs`는 정확히 네 가지만 합니다. clap으로 파싱하고, subscriber를 초기화하고, `run`을 호출하고, 결과를 `ExitCode`로 매핑합니다.
- `lib.rs`는 `run`을 노출합니다. subscriber를 설치하거나 `std::env::args`를 읽거나 `process::exit`를 호출하지 않습니다.
- `cli.rs`는 `Parser`, `Subcommand`, `Args` 타입만 담고 로직이 없습니다. 파싱 표면을 grep하기 쉽게 하고 enum 하나를 권위로 남깁니다.
- `commands/<verb>.rs`는 동사 하나를 소유하고 타입 있는 인자를 받습니다. 도메인과 io 모듈을 호출할 수 있지만 문자열을 다시 파싱하지 않습니다.
- `domain/`은 순수합니다. 환경 변수, 주입되지 않은 시계 읽기, 파일 시스템이 없습니다.

`hypercore-default` — `src/`의 `build.rs`라는 파일명은 crate 루트의 Cargo 빌드 스크립트와 개념적으로 충돌합니다. 동사 모듈을 동작 이름(`compile.rs`, `render.rs`)으로 지어 읽는 사람이 둘을 혼동하지 않게 합니다.

`official` — 패키지는 manifest 하나에서 두 타깃을 가질 수 있습니다. `[lib]`와 `src/main.rs`에서 오는 암묵적 바이너리입니다. `CARGO_BIN_EXE_<name>`은 통합 테스트에서 설정되므로 경로를 추측하지 않고 블랙박스 CLI 테스트를 할 수 있습니다(https://doc.rust-lang.org/cargo/reference/cargo-targets.html).

## 2. 모듈 소유

`hypercore-default` — 모듈 하나에 책임 하나를 두고 파일 맨 위 한 줄로 진술합니다.

| Module | Owns | Must not own |
|---|---|---|
| `cli.rs` | 인자 모양과 기본값 | 실행, I/O |
| `commands/<verb>.rs` | 동사 하나의 조정 | 파싱, 다른 곳이 소유한 출력 포맷 도우미 |
| `domain/<area>.rs` | 결정과 데이터 변환 | 파일 시스템, 네트워크, 프로세스 전역 |
| `io/<device>.rs` | 외부 경계 하나 | 비즈니스 결정 |
| `output/` | 한 결과 타입의 사람용·기계용 렌더러 | 데이터 수집 |

`hypercore-default` — 대략 400줄을 넘거나, 부분을 설명하려고 절 주석이 필요한 모듈은 보통 소유자가 둘입니다. 줄 수로 자르지 말고 주석이 명명한 이음매에서 자릅니다.

`official` — Rust 모듈과 파일 이름은 `snake_case`입니다. 항목에는 컴파일러의 `non_snake_case` lint가, 모듈 파일에는 모듈 파일 관례가 이를 강제합니다. 디렉터리도 같은 규칙을 따릅니다.

## 3. 워크스페이스 멤버 분리

`official` — 가상 manifest는 resolver를 추론할 `package.edition`이 없으므로 `resolver`를 명시해야 합니다(https://doc.rust-lang.org/cargo/reference/workspaces.html). resolver 버전, `rust-version`, lint 표는 워크스페이스 루트에서 한 번 설정하고 멤버가 상속합니다.

`hypercore-default` — crate를 워크스페이스 멤버로 떼어내는 이유는 아래뿐이며, 모두 선호가 아니라 빌드나 소유 사실입니다.

| Reason | Split |
|---|---|
| 두 번째 산출물의 릴리스 주기가 다름(CLI와 공개 라이브러리) | 라이브러리를 별도 멤버로, 바이너리가 그것에 의존 |
| 한 산출물만 쓰는 의존성이 빌드 시간을 지배함 | 그 의존성을 소유한 멤버, 나머지는 의존하지 않음 |
| 경계를 컴파일러로 강제해야 함(도메인이 HTTP crate를 보면 안 됨) | 계층별 멤버, 의존 방향은 manifest에 |
| 타깃 플랫폼이 다름(네이티브 도구 옆의 `wasm32` 산출물) | 타깃별 멤버, 또는 타깃 범위 의존성 섹션이 있는 한 멤버 |

"깔끔해서" 분리하지 않습니다. 새 멤버는 manifest 하나, 배포 단위 하나, 일관되게 유지할 버전 줄 하나를 더합니다.

`hypercore-default` — 멤버 manifest는 그 멤버에 특정한 것만 담습니다. `name`, `description`, `[lib]`/`[[bin]]`, 자체 의존성, `[lints] workspace = true`입니다. `edition`, `rust-version`, `version`, `license`, 공유 의존성 버전은 `[workspace.package]`와 `[workspace.dependencies]`에서 옵니다.

`official` — 워크스페이스 의존성은 `optional`로 선언할 수 없고, 워크스페이스 표에 선언한 `features`는 멤버 `[dependencies]`의 기능과 가산적으로 합쳐집니다(https://doc.rust-lang.org/cargo/reference/workspaces.html). 따라서 멤버는 상속한 의존성을 optional로 만들 수 없습니다. 의존성이 optional이어야 하면 멤버에 남깁니다.

## 4. 기능 정책

`official` — 기능 플래그는 설계상 가산적입니다. 기능을 켜도 다른 crate가 의존하는 동작이 사라지지 않습니다. Cargo는 그래프 전체에서 crate마다 기능 집합 하나를 해석합니다.

`hypercore-default` — 규칙 묶음:

- 그 기능 없이는 crate의 주 용도가 불가능한 경우가 아니면 `default = []`입니다.
- 의존성이나 동작 하나에 기능 하나를 두고, 릴리스나 고객이 아니라 켜는 것을 이름으로 씁니다(`serde`, `http`, `telemetry`).
- 한 타깃만 필요한 기능은 기능이 아닙니다. 그 의존성은 `[target.'cfg(...)'.dependencies]`에 둡니다.
- API 모양을 바꾸는 기능은 crate 문서와 체인지로그에 기록합니다. semver에 관련된 표면이기 때문입니다.
- `cfg` 게이트는 `#[cfg(feature = "...")]`를 쓰고, crate가 문서를 발행하면 `#[cfg_attr(docsrs, doc(cfg(...)))]`를 함께 씁니다.

`official` — 패키지 수준 `default-features = false` 덮어쓰기는 Rust 1.99 이상의 edition 2024 패키지에서만 안정적으로 적용되고, 그 전에는 워크스페이스 의존성도 기본 기능을 끄지 않으면 무시되거나 거부될 수 있습니다(https://doc.rust-lang.org/cargo/reference/workspaces.html). 따라서 crate가 기본 기능을 끌어오면 안 될 때는 멤버별이 아니라 워크스페이스 의존성에서 끕니다.

## 5. crate 타입과 타깃 배치

`official` — 허용 값은 `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, `proc-macro`이고, `crate-type`은 라이브러리와 예제 타깃에만 적용됩니다(https://doc.rust-lang.org/cargo/reference/cargo-targets.html).

`hypercore-default` — 네이티브 테스트도 되어야 하는 WASM 산출물의 모양입니다.

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[target.'cfg(target_arch = "wasm32")'.dependencies]
wasm-bindgen = "0.2"
```

`rlib` 절반이 `cargo test`로 같은 코드를 호스트용으로 빌드하게 합니다. 타깃 범위 의존성은 `wasm-bindgen`을 네이티브 빌드 밖에 두어 호스트 컴파일 시간을 줄입니다.

## 6. crate에 있으면 안 되는 것

`hypercore-default` — 아래를 두지 않습니다. 각각이 crate를 프로세스나 호스트에 조용히 결합시키기 때문입니다.

- 라이브러리 코드가 호출하는 `main` 전용 `process::exit` 도우미.
- 매개변수가 될 수 있는 설정을 담은 `lazy_static`/`OnceLock` 전역.
- 출하 바이너리에 컴파일되는 테스트 전용 모듈.
- 손으로 고치는 생성 파일.
- 통합 테스트가 쓰는 `#[cfg(test)] pub` 탈출구. 실제 생성자를 노출합니다.
- 절대 경로나 기계 특정 플래그 기본값.

## Checklist

- [ ] `main.rs`가 파싱하고, subscriber를 초기화하고, `run`을 호출하고, 종료 코드 하나를 매핑한다.
- [ ] `lib.rs`가 진입 함수를 노출하고 프로세스 전역을 소유하지 않는다.
- [ ] `cli.rs`가 clap 타입만 담고, `Subcommand` enum 하나가 모든 동사를 명명한다.
- [ ] 명령 모듈마다 동사 하나를 소유하고 타입 있는 입력을 받는다.
- [ ] 도메인 모듈에 파일 시스템, 네트워크, 환경 접근이 없다.
- [ ] `build.rs` 동사 모듈은 Cargo 빌드 스크립트와 혼동되지 않게 이름을 바꿨다.
- [ ] 모듈과 디렉터리 이름이 `snake_case`다.
- [ ] 워크스페이스 멤버가 `edition`, `rust-version`, 버전, lint를 반복하지 않고 상속한다.
- [ ] `[profile.*]` 섹션이 워크스페이스 루트 manifest에만 있다.
- [ ] 기능이 가산적이고, 문서화되며, 켜는 것을 이름으로 쓴다.
- [ ] WASM crate가 `cdylib`과 `rlib`를 함께 선언하고 `wasm-bindgen`을 `wasm32` 타깃으로 한정했다.
- [ ] 테스트 전용이나 생성 코드가 출하 산출물에서 도달 불가능하다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 crate와 Cargo 페이지에서 왔고, 구조 규칙은 이 패키지의 규약입니다.

| Claim | Source |
|---|---|
| 라이브러리/바이너리 분리가 프로세스를 띄우지 않고 로직을 테스트하게 함 | https://rust-cli.github.io/book/print.html |
| Cargo 타깃, `crate-type` 값, 통합 테스트용 `CARGO_BIN_EXE_<name>` | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| 가상 manifest의 명시적 `resolver`, 워크스페이스 상속, optional·가산 기능 규칙 | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| resolver 3 동작과 MSRV fallback | https://doc.rust-lang.org/cargo/reference/resolver.html |
| Edition 2024와 그에 필요한 Rust 버전 | https://doc.rust-lang.org/edition-guide/rust-2024/index.html |
| `[workspace.lints]` 범위: 현재 패키지만, 의존성 제외 | https://doc.rust-lang.org/cargo/reference/manifest.html |
| `rust-toolchain.toml` 필드와 레거시 override 우선순위 | https://rust-lang.github.io/rustup/overrides.html |
| `wasm-bindgen` 타깃 지침과 `cdylib` 예제 manifest | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml |
| 모듈 이름과 위 디렉터리 배치 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
