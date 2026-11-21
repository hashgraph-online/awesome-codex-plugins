# Rust Crate 생태계 공식 근거 Snapshot

설치된 crate 버전, 기본 기능, MSRV, 타깃 계층, MCP 명세 리비전이 변경을 가를 때 읽습니다. 이 snapshot은 이 패키지가 근거로 삼는 공식 주장과 확인 날짜를 기록합니다. 다른 버전을 쓰는 프로젝트는 그 버전 자체의 동작으로 다시 확인해야 합니다.

- last_verified_at: 2026-11-07
- `status`: 2026-11-07에 crates.io registry API, docs.rs, Cargo Book, Rust CLI book, wasm-bindgen·wasm-pack guide, MCP 명세를 검토 완료
- `baseline`: stable Rust `1.99.1`(stable channel manifest 기준 `2026-10-15`); clap 4.6.7, clap_complete 4.6.11, anyhow 1.0.104, thiserror 2.0.21, tracing 0.1.44, tracing-subscriber 0.3.23, assert_cmd 2.2.2, predicates 3.1.4, trycmd 1.2.1, snapbox 1.2.2, insta 1.49.0, anstream 1.0.0, anstyle 1.0.14, cargo-dist 0.34.0, cargo-binstall 1.26.2, wasm-bindgen과 wasm-bindgen-cli 0.2.130, wasm-bindgen-test 0.3.80, wasm-pack 0.15.1, console_error_panic_hook 0.1.7, serde-wasm-bindgen 0.6.5, tsify 0.5.8, rmcp 3.9.0, schemars 1.2.3, axum 0.8.9, cargo-deny 0.20.2, cargo-machete 0.9.2
- `refresh_when`: crate 메이저가 움직이거나, MSRV 정책이 바뀌거나, 타깃 계층이 바뀌거나, MCP 명세가 새 리비전을 내거나, rustwasm·wasm-bindgen 조직이 다시 바뀔 때
- `authority`: 근거일 뿐이며 user/project 지시, 설치 toolchain, `Cargo.lock`이 우선

## 목차

1. crate version
2. Rust toolchain과 target
3. clap
4. error, exit code, logging
5. CLI 출력과 배포
6. WASM
7. MCP
8. Cargo와 workspace
9. 이 snapshot에서 미검증
10. Sources

## crate version

2026-11-07에 crates.io API로 캡처했고, version은 최대 stable release와 그 publish date입니다.

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
| cargo-dist(binary `dist`) | 0.34.0 | 2026-11-02 |
| cargo-binstall | 1.26.2 | 2026-10-31 |
| wasm-bindgen | 0.2.130 | 2026-10-30 |
| wasm-bindgen-cli | 0.2.130 | 2026-10-30 |
| wasm-bindgen-test | 0.3.80 | 2026-10-30 |
| wasm-pack | 0.15.1 | 2026-10-30 |
| console_error_panic_hook | 0.1.7 | 2021-10-11(오래됨) |
| serde-wasm-bindgen | 0.6.5 | 2024-02-27 |
| tsify | 0.5.8 | 2026-08-23 |
| rmcp | 3.9.0 | 2026-11-05 |
| schemars | 1.2.3 | 2026-10-12 |
| axum | 0.8.9 | 2026-04-14 |
| cargo-deny | 0.20.2 | 2026-07-09 |
| cargo-machete | 0.9.2 | 2026-04-15 |

version만 확인하고 이 snapshot에서 권고하지 않는 것: `figment` 0.10.19(2024-05-17 publish)와 `config` 0.15.27(2026-09-30). Rust CLI book의 설정 장이 아직 초안이므로 둘 다 CLI 설정의 공식 기본값이 아닙니다.

## Rust toolchain과 target

| Claim | Evidence | Caveat |
|---|---|---|
| stable Rust는 `1.99.1`이고 `2026-10-15` 날짜 | stable channel manifest | manifest가 기준이며 프로젝트는 자체 channel을 고정합니다 |
| Edition 2024는 1.85.0에 출시되고 `cargo new`가 2024 edition을 씀 | Edition Guide, Cargo manifest 문서 | 오래된 edition crate가 자동으로 틀린 것은 아닙니다 |
| `resolver = "3"`은 edition 2024 기본이고 Rust 1.84+를 요구하며 `resolver.incompatible-rust-versions`를 `allow`에서 `fallback`으로 바꿈 | Cargo resolver 문서 | 가상 manifest는 `package.edition`이 없어 명시해야 합니다 |
| `wasm32-unknown-unknown`, `wasm32-wasip1`(과 `-threads`), `wasm32-wasip2`는 `std`를 갖춘 Tier 2 | rustc platform support | Tier 2는 빌드 보장이지 테스트 통과 보장이 아닙니다 |
| `wasm32-wasip1`은 `std`를 지원하지만 스레드와 프로세스는 항상 오류, 파일 API는 WASI 경유. `target_env = "p1"`은 Rust 1.80부터 | rustc `wasm32-wasip1` 페이지 | WASI p1은 코어 모듈입니다 |
| `wasm32-wasip2`는 컴포넌트를 출력하고 Wasmtime 17+ 런타임이 필요하며 "현재 CI에서 테스트되지 않음" | rustc `wasm32-wasip2` 페이지 | CI 보장을 약속하지 않습니다 |
| 두 WASI 타깃은 기본으로 `-Cpanic=abort`로 컴파일 | rustc WASI 페이지 | `wasm32-unknown-unknown`의 기본값은 읽지 않았습니다 |

## clap

| Claim | Evidence |
|---|---|
| 메이저는 4이고 기능 20개, 기본값 6개(`color`, `error-context`, `help`, `std`, `suggestions`, `usage`) | clap 기능 목록 |
| `derive`와 `env`는 기본이 아니며 켜야 함 | clap 기능 목록 |
| derive 표면은 `Parser`, `Args`, `Subcommand`, `ValueEnum` | clap derive 참조 |
| `ValueEnum`은 unit 변형만 있는 enum에서 동작하며 나머지는 skip해야 함 | clap derive 참조 |
| `rename_all`은 `kebab-case`, `rename_all_env`는 `SCREAMING_SNAKE_CASE`가 기본 | clap derive 참조 |
| 표현식 없는 `#[command(version)]`은 crate version을 씀 | clap derive 참조 |
| 문서 주석이 `about`/`long_about`이 되므로 `#[command(version, about, long_about = None)]`이 짧은 형식을 유지 | clap derive 참조 |
| `Error::exit`는 stderr+2 또는 stdout+0으로 출력하고, `exit_code()`가 그 분할을 따르며 `use_stderr()`가 방향을 알림 | clap `Error` 문서 |
| `clap_complete`는 `generate`, `generate_to`, `Shell`, `aot` 모듈, `CompleteEnv`를 제공하고 `generator`·`shells`는 `aot` 대신 폐기 | clap_complete 문서 |

## error, exit code, logging

| Claim | Evidence |
|---|---|
| `anyhow::Result<T>`는 애플리케이션 코드용이고 `derive(Error)` 매크로를 묶지 않으며, backtrace는 Rust 1.65+에서 캡처되고 `RUST_BACKTRACE`/`RUST_LIB_BACKTRACE`로 켬 | anyhow 문서 |
| `thiserror`는 `std::error::Error`를 derive하고 "의도적으로 공개 API에 나타나지 않음" | thiserror 문서 |
| `anyhow::Error`를 감싼 변형의 `#[error(transparent)]`는 `Display`와 `source`를 위임 | thiserror 문서 |
| exit code 0–255는 이식 가능하고 panic은 101로 종료하며 `exitcode`가 BSD sysexits 어휘를 제공 | Rust CLI book, exit code |
| `tracing-subscriber` 기본값은 `ansi`, `fmt`, `smallvec`, `std`, `tracing-log`이고 `env-filter`는 기본이 아님 | tracing-subscriber 문서 |
| `EnvFilter::DEFAULT_ENV`는 `RUST_LOG`이고 `from_default_env()`는 변수가 비었거나 없을 때 ERROR 지시문을 더함 | tracing-subscriber 문서 |
| 기본 레벨 `info`, 일관된 로그 접두사, `--verbose` 또는 `RUST_LOG`로 상세도 조절 | Rust CLI book, human communication |
| `std::io::IsTerminal`이 터미널과 파이프를 구분하고, 기계 출력은 `type` 필드를 가진 줄 단위 JSON | Rust CLI book, machine communication |
| `anstream`의 `AutoStream`은 ANSI를 받아 터미널에 맞추고, `anstyle`은 공개 API용 스타일 타입 | anstream 문서 |

## CLI 출력과 배포

| Claim | Evidence |
|---|---|
| 도구는 `dist`이고 이전 이름은 `cargo-dist` | cargo-dist README |
| crates.io 패키지는 여전히 `cargo-dist`(0.34.0)이고 "`dist ...`로 호출할 수 있어야 함" | dist book, install |
| `dist init`이 설정을 쓰고 빌드 프로필을 추가하며 `.github/workflows/release.yml`을 생성하고, 릴리스는 태그(`v0.1.0`)로 시작하며 `dist build`는 로컬 플랫폼을, `dist plan`은 CI 미리보기를 냄 | dist book, Rust quickstart |
| 생성되는 `[profile.dist]`는 `release`를 상속하고 `lto = "thin"` | dist book, concepts |
| Rust CLI book의 설정 장은 아직 "TODO / Evaluate crates that exist / Cli-args + multiple configs + env variables" | Rust CLI book |

## WASM

| Claim | Evidence |
|---|---|
| rustwasm 워킹 그룹은 약 5년 무활동 끝에 2024년 보관되었고 `wasm-bindgen`은 새 조직으로 이전했으며 조직은 2025년 9월 보관됨 | Rust 프로젝트 블로그, 2025-07-21 |
| 보관된 `rustwasm/team` README는 더 이상 Rust·WebAssembly 활동이 일어나는 곳이 아니라고 진술 | rustwasm/team README |
| 공식 거처는 `wasm-bindgen/wasm-bindgen`과 `wasm-bindgen/wasm-pack`이고 이전의 `rustwasm.github.io/wasm-pack/installer/` URL은 폐기 | wasm-bindgen README, wasm-pack book |
| `wasm-pack` 0.15.1은 2026-10-30 publish이고 README는 `@drager`의 유지보수를 언급 | wasm-pack README, crates.io |
| `console_error_panic_hook`은 보관되었고 마지막 푸시 2022-12-04이며 0.1.7(2021-10-11)에 머묾 | docs.rs crate 페이지와 저장소 보관 표시 |
| `serde-wasm-bindgen`은 그 조직 밖이지만 그 문서가 "공식적으로 선호되는 접근"이라 하고 "JSON보다 훨씬 작은 코드 크기 오버헤드"를 줌 | serde-wasm-bindgen 문서 |
| `wasm-bindgen`은 0.2.130이고 라이브러리 MSRV 1.81, CLI·지원 라이브러리 MSRV 1.86이며 라이브러리 MSRV 2년 정책과 패치 릴리스 MSRV 변경을 허용 | wasm-bindgen README, crates.io 메타데이터(`rust_version = "1.81"`) |
| `wasm-bindgen`은 `wasm32-unknown-unknown`을 대상으로 하고 그곳에서 `std::fs`·`std::net`이 오류를 반환하며 타깃 범위 의존성을 컴파일 시간에 권장 | wasm-bindgen guide, Rust targets |
| `--target`은 `bundler`(기본), `web`, `nodejs`, `deno`, `no-modules`, `experimental-nodejs-module`, `module`을 받고, webpack이 완전 호환되며 Rolldown은 `rolldown-plugin-wasm`으로 호환되고 `module`은 ESBuild나 Node.js 24를 요구 | wasm-bindgen guide, deployment |
| `target/wasm32-unknown-unknown/release/*.wasm` 원본은 "크기 최적화가 되어 있지 않아 측정하면 안 되고", CLI가 strip한 뒤 `*_bg.wasm`을 측정 | wasm-bindgen guide, optimize size |
| `lto = true`가 모듈을 줄이고, `opt-level = "s"`가 `"z"`를 이길 수 있어 측정해야 하며, `wasm-opt -Os`/`-Oz`가 15–20%를 더 줄임 | Rust and WebAssembly book, code size |
| wasm-pack은 기본으로 `panic=abort`로 빌드하고, `--panic-unwind`는 nightly와 build-std, 런타임 글루를 요구 | wasm-pack book, build |
| 하드 abort 감지와 `set_on_abort`는 `panic=unwind`에서 자동으로 켜지고, `panic=abort`에서는 `--force-enable-abort-handler`가 필요 | wasm-bindgen guide, handling aborts |
| `web-sys`는 인터페이스마다 기능을 게이트하고 API 문서가 타입·메서드별 필요 기능을 알려줌 | wasm-bindgen guide, using web-sys |
| `tsify` 0.5.8은 `json`이 기본이고 `js`가 `serde-wasm-bindgen` 직렬화를 켜며 향후 기본이 될 예정이고, `into_wasm_abi`/`from_wasm_abi`는 `Ts<T>` 대신 폐기되었으며 `Ts<Vec<T>>`는 지원되지 않음 | tsify 문서 |
| `serde-wasm-bindgen`은 `HashMap`을 `Map`으로, 구조체를 객체로, `Vec`과 튜플을 배열로, `serde_bytes`를 `Uint8Array`로 매핑하고 `json_compatible()`과 `preserve`가 그 매핑을 바꿈 | serde-wasm-bindgen 문서 |
| `wasm-bindgen-test` 0.3.80이 `#[wasm_bindgen_test]`를 제공하고 브라우저는 `wasm-pack test --node --firefox --chrome --safari --headless`로 구동 | wasm-bindgen-test 문서, wasm-pack book |
| 유용한 CLI 플래그는 `--keep-debug`, `--split-debug-info`, `--no-typescript`, `--omit-imports`, `--split-linked-modules`, `--js-string-builtins`, `--ts-typed-array-buffers` | wasm-bindgen guide, CLI |
| `[lib] crate-type`은 `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, `proc-macro`를 받고 라이브러리·예제 타깃에 적용 | Cargo targets |

## MCP

| Claim | Evidence |
|---|---|
| `rmcp` 3.9.0(2026-11-05)은 "tokio 비동기 런타임을 쓰는 공식 Rust Model Context Protocol SDK 구현"이고 `rmcp-macros`가 동반 | rust-sdk README, crates.io |
| SDK는 안정 `2026-07-28` 명세를 구현하고 "`2025-11-25` 릴리스와 그 이전 버전과 완전히 호환" | rust-sdk README |
| `2026-07-28`이 현재 프로토콜 버전이고, 리비전은 Draft·Current·Final이며 폐기 유예는 최소 12개월, 신속 예외는 최소 90일 | MCP versioning 문서 |
| 기본 기능은 `base64`, `macros`, `server`, `schemars`, `transport-async-rw`, `uuid`이고 전송은 `transport-io`, `transport-child-process`, `transport-streamable-http-server`, `transport-streamable-http-client-reqwest`, `transport-worker` | rmcp 기능 목록 |
| TLS 선택은 `reqwest`(rustls, 권장), `reqwest-native-tls`, `reqwest-tls-no-provider` | rmcp 문서 |
| `#[tool]`은 함수 이름에서 `name`, 문서 주석에서 `description`, `Parameters<T>` 인자에서 `input_schema`, 그리고 `annotations`를 도출하고, `#[tool_router]`, `#[tool_router(server_handler)]`, `#[tool_handler]`가 라우터·handler 배선을 덮음 | rmcp-macros 문서, rust-sdk README |
| `inputSchema`와 `outputSchema`는 `T`의 필드에서 나오고 타입 이름과 타입 문서는 무시되며 스키마는 JSON Schema draft 2020-12이고 `schemars`가 재노출 | rust-sdk README |
| SEP-2106(`2026-07-28`)에서 `outputSchema`는 어떤 JSON Schema 타입도, `structuredContent`는 어떤 JSON 값도 될 수 있음 | rust-sdk README |
| `StreamableHttpService`는 `nest_service`로 마운트하는 Tower 서비스이고, 서비스 팩토리가 요청마다 실행되어 공유 상태가 `Clone` 핸들이어야 하며, `2026-07-28`은 세션 헤더도 독립 스트림도 재개도 없는 상태 없음이고 `with_json_response(true)`는 JSON 본문 하나를 반환 | rust-sdk README |
| stdio: 서버는 stdout에 MCP가 아닌 데이터를 "절대(MUST NOT)" 쓰지 않고, stderr 로깅은 "해도 되며(MAY)", 프레임은 개행으로 구분되고 내장 개행이 없으며, stdin EOF에서 "즉시 종료하는 것이 좋음(SHOULD)" | MCP stdio transport |
| 로깅 capability는 폐기(SEP-2577)되었지만 여전히 동작 | rust-sdk README |
| `list_all_*` 도우미가 커서를 넘고, 지원하지 않는 프로토콜 버전은 `UnsupportedProtocolVersionError`로 거부 | rust-sdk README, MCP versioning 문서 |

## Cargo와 workspace

| Claim | Evidence |
|---|---|
| 가상 workspace에서는 `package.edition`이 없어 `resolver`를 명시해야 함 | Cargo workspaces |
| 상속 가능한 package key는 `edition`, `rust-version`, `version`, `license`, `repository`, `authors`, `keywords`, `categories` | Cargo workspaces |
| workspace 의존성은 `optional`일 수 없고, workspace `features`는 멤버 자체 기능과 가산적으로 합쳐짐 | Cargo workspaces |
| 패키지 수준 `default-features = false` 덮어쓰기는 Rust 1.99+의 edition 2024 패키지에서만 이기고 그 전에는 무시되거나 거부될 수 있음 | Cargo workspaces |
| `[workspace.lints]`는 1.74부터 존중되고 현재 패키지에만 적용되며 의존성은 `--cap-lints`를 받음 | Cargo workspaces, manifest |
| `[profile.*]`는 루트 manifest에서만 인식되고 멤버 manifest에서는 무시 | Cargo workspaces, profiles |
| 릴리스 기본값은 `opt-level = 3`, `debug = false`, `lto = false`, `codegen-units = 16`, `panic = "unwind"`, `strip = "none"`, `incremental = false` | Cargo profiles |
| `strip`은 `"none"`, `"debuginfo"`, `"symbols"`, `true`를 받고, `opt-level`은 `"s"`·`"z"`를 받으며 `"z"`는 루프 벡터화를 끄고, `lto`는 `true`/`"fat"`, `"thin"`, `false`, `"off"`를 받음 | Cargo profiles |
| 테스트, 벤치, 빌드 스크립트, proc macro는 `panic` 설정을 무시하고 `panic = "abort"` 테스트는 nightly `panic-abort-tests`가 필요 | Cargo profiles |
| `rust-version`은 지원 툴체인을 선언하고 resolver 3 `fallback`이 그 이하 버전 패키지를 선호하므로 낡은 MSRV가 의존성 버전을 제한 | Cargo manifest, resolver |
| `rust-toolchain.toml`은 `channel`, `components`, `targets`, `profile`을 받고 `channel`과 `path`는 상호 배타이며, 레거시 `rust-toolchain` 파일이 둘 다 있으면 이김 | rustup book |
| `cargo-deny`는 `licenses`, `bans`, `advisories`, `sources`를 덮고, `cargo-machete`는 미사용 의존성이 없으면 0, 하나 이상이면 1, 오류면 2로 종료 | cargo-deny README, cargo-machete README |
| `[lints] workspace = true`와 `[workspace.lints.rust]`/`[workspace.lints.clippy]`가 상속 기구이고 항목은 축약형이나 `{ level, priority }`를 받음 | Cargo manifest |

## 이 snapshot에서 미검증

- **CLI 설정 crate.** 공식 권고가 없고 CLI book 설정 장이 초안입니다. 버전만 확인했으므로 `figment`나 `config`의 유지보수 주장은 하지 않습니다.
- **`exitcode` crate.** 책이 권고하지만 버전, publish date, 유지보수 상태를 확인하지 않았습니다. 따라서 규칙은 sysexits 어휘를 명명하고 crate는 고정하지 않습니다.
- **`wasm32-unknown-unknown` 기본 panic 전략.** `wasm-pack` 빌드와 WASI 타깃에 대해서만 확인했고 rustc의 `wasm32-unknown-unknown` 페이지는 읽지 않았습니다.
- **Vite와 WASM.** Vite 자체 지침과 `vite-plugin-wasm`을 읽지 않았으므로 Vite 전용 WASM 규칙을 진술하지 않습니다.
- **`wasm-bindgen` 0.2.131+ 또는 1.0 로드맵.** 0.2.130과 미출시 changelog만 읽었고 일정을 주장하지 않습니다.
- **crates.io의 `dist`.** 책은 패키지 이름이 여전히 `cargo-dist`이며 나중에 바뀔 수 있다고 합니다. 이 도구용 `dist` 패키지가 존재하는지 확인하지 않았습니다.
- **MCP Tasks(SEP-2663).** `rmcp`가 `task_manager` 모듈을 노출하지만 `2026-07-28` 명세에서의 지위를 읽지 않았습니다.
- **`cargo-deny`/`cargo-machete` 설정 스키마.** 검사 이름과 종료 코드만 읽었고 `deny.toml` 스키마는 열지 않았습니다.
- **`rmcp` 3.9.0의 정확한 import 경로.** 매개변수 래퍼와 구조적 결과 생성자 경로는 마이너 릴리스 사이에 움직이므로 설치된 버전으로 확인해야 합니다.
- **벤치마크 하네스.** `criterion`과 `hyperfine` 버전을 확인하지 않았으므로 성능 규칙에서 버전을 고정하지 않습니다.

## Sources

> Checked 2026-11-07. 위 모든 주장은 그날 아래 페이지에서 가져왔고, 연구 lane의 source id를 괄호에 남깁니다.

| Claim group | Source |
|---|---|
| crate version과 publish date | https://crates.io/api/v1/crates/clap (L-01), https://crates.io/api/v1/crates/wasm-bindgen (L-25), 그리고 나열한 crate마다 같은 registry endpoint |
| Rust stable channel 기준선 | https://static.rust-lang.org/dist/channel-rust-stable.toml (L-62) |
| clap derive, 기능, exit code | https://docs.rs/clap/latest/clap/_derive/index.html (L-02), https://docs.rs/crate/clap/latest/features (L-03), https://docs.rs/clap/latest/clap/error/struct.Error.html (L-04), https://docs.rs/clap_complete/latest/clap_complete/ (L-05) |
| `anyhow`, `thiserror`, exit code | https://docs.rs/anyhow/latest/anyhow/ (L-06), https://docs.rs/thiserror/latest/thiserror/ (L-07), https://rust-cli.github.io/book/in-depth/exit-code.html (L-08) |
| CLI human·machine 출력, logging 지침 | https://rust-cli.github.io/book/in-depth/machine-communication.html (L-09), https://rust-cli.github.io/book/in-depth/human-communication.html (L-10), https://rust-cli.github.io/book/print.html (L-11) |
| `tracing-subscriber`와 `EnvFilter` | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ (L-61) |
| `anstream`과 `anstyle` | https://docs.rs/anstream/latest/anstream/ (L-15) |
| test crate | https://docs.rs/assert_cmd/latest/assert_cmd/ (L-12), https://docs.rs/trycmd/latest/trycmd/ (L-13), https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md (L-14) |
| `dist`와 그 book | https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md (L-16), https://axodotdev.github.io/cargo-dist/book/install.html (L-17), https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html (L-19), https://axodotdev.github.io/cargo-dist/book/reference/concepts.html (L-20) |
| rustwasm 선셋과 새 거처 | https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/ (L-22), https://raw.githubusercontent.com/rustwasm/team/master/README.md (L-23) |
| wasm-bindgen version, MSRV, target, deployment, size, aborts, CLI | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md (L-24), https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html (L-30), https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html (L-26), https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html (L-29), https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html (L-28), https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html (L-27) |
| wasm-pack build·test 동작 | https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html (L-37), https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html (L-38), https://raw.githubusercontent.com/wasm-bindgen/wasm-pack/master/README.md (L-39) |
| `web-sys` 기능, `wasm-bindgen-test`, panic hook, serde bridge, tsify | https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html (L-31), https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/ (L-33), https://docs.rs/console_error_panic_hook/latest/console_error_panic_hook/ (L-34), https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/ (L-35), https://docs.rs/tsify/latest/tsify/ (L-36) |
| Rust and WebAssembly 크기 지침 | https://rustwasm.github.io/docs/book/reference/code-size.html (L-40) |
| Rust target 계층과 WASI target | https://doc.rust-lang.org/rustc/platform-support.html (L-42), https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html (L-43), https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html (L-44) |
| MCP SDK, 매크로, 기능, 전송 | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md (L-45), https://docs.rs/rmcp/latest/rmcp/ (L-46), https://docs.rs/crate/rmcp/latest/features (L-47), https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html (L-48) |
| MCP stdio transport와 versioning | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md (L-49), https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md (L-51) |
| Cargo workspaces, resolver, profiles, manifest, targets | https://doc.rust-lang.org/cargo/reference/workspaces.html (L-52), https://doc.rust-lang.org/cargo/reference/resolver.html (L-53), https://doc.rust-lang.org/cargo/reference/profiles.html (L-54), https://doc.rust-lang.org/cargo/reference/manifest.html (L-55), https://doc.rust-lang.org/cargo/reference/cargo-targets.html (L-56) |
| Edition 2024와 toolchain override | https://doc.rust-lang.org/edition-guide/rust-2024/index.html (L-57), https://rust-lang.github.io/rustup/overrides.html (L-58) |
| 공급망 검사 | https://raw.githubusercontent.com/EmbarkStudios/cargo-deny/main/README.md (L-59), https://raw.githubusercontent.com/bnjbvr/cargo-machete/main/README.md (L-60) |
