# 아키텍처 규칙 참조

> Axum 서버도 Tauri 백엔드도 아닌 Rust crate의 전체 규칙 집합

참고: 아래 일부 규칙은 crate 자체의 기본값보다 엄격합니다. 보편적인 Rust 요구가 아니라 Hypercore 팀 규약입니다. 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

브라운필드 채택 규칙: 건드리지 않은 기존 코드는 스타일이나 Hypercore 전용 문제라면 즉시 실패가 아니라 마이그레이션 작업으로 추적할 수 있습니다. 안전, 타입, 실패 계약, 프로토콜 경계 문제는 특히 건드린 코드에서 즉시 차단합니다.

워크스페이스 공통 규약은 여기서 반복하지 않습니다. resolver, 툴체인 고정, `[workspace.lints]`, 릴리스 프로필 섹션, rustfmt, clippy, 공급망 검사는 `rules/setup/rust.md`가 소유하고, 이 파일은 crate 아키텍처가 의존하는 것을 소유합니다.

---

## Forbidden

| Category | Forbidden |
|---|---|
| Profile | manifest에서 프로필을 정하지 않은 crate에 CLI, WASM, MCP 규칙을 적용하는 것 |
| Boundary | crate 규칙 파일 안에 `rules/setup/rust.md` 내용을 다시 쓰거나, Axum이나 Tauri 표면을 이 가이드 소유로 주장하는 것 |
| Entry | `main.rs`의 비즈니스 로직, 인자를 파싱하고 실행하고 결과를 포맷하는 것을 한 함수에서 하는 바이너리 |
| Exit | 호출 경로 깊은 곳의 `std::process::exit`, 직접 쓴 종료 코드 101, 정상 실패 경로에서의 panic |
| Errors | 라이브러리 공개 API의 `anyhow::Error`, 테스트 밖에서 사용자나 파일 입력에 대한 `unwrap()`/`expect()` |
| Logging | 진단용 `println!`, `env-filter` 기능 없이 쓰는 `EnvFilter`, 라이브러리 안에서 설정하는 subscriber |
| Output | stdout으로 나가는 진단, 기록된 결정 없이 바뀌는 기계 계약 |
| WASM | `target/wasm32-unknown-unknown/release/*.wasm` 원본 측정, 통째로 켜는 `web-sys` 기능 목록, `Ts<Vec<T>>` |
| MCP | stdio 서버 stdout에 MCP가 아닌 것, `rmcp`가 있는데 손으로 만든 JSON-RPC 전송, 고정하지 않은 명세 리비전 |
| Features | 한 타깃만 필요한 가산 의존성의 기능을 전역으로 켜는 것, crate가 쓰지 않는 동작을 끌어오는 `default` 기능 |
| Paths | `camelCase`나 `kebab-case` Rust 모듈·파일(`userProfile.rs`, `create-user.rs`) |
| Rust | 불변 조건을 밝히지 않은 `unsafe`, 공개 함수에서 반환하는 `Box<dyn Error>`, 전역 `static mut` |
| Git | AI 표시, 이모지, 여러 줄 커밋 메시지 |

---

## 프로필 선택

프로필은 요청에서 추측하는 것이 아니라 manifest의 사실입니다. 프로필 규칙 파일을 읽기 전에 그것을 결정한 필드와 함께 보고합니다.

| Order | Profile | Deciding evidence | Owns |
|---|---|---|---|
| 1 | `mcp-server` | `[dependencies]`의 `rmcp` | 도구 정의, 전송, stdout 규율, 프로토콜 버전 |
| 2 | `wasm` | `"cdylib"`가 있는 `crate-type`과 `wasm-bindgen`, 또는 툴체인·cargo 설정의 `wasm32-*` 타깃 | 타깃, crate 타입, 바인딩, 크기 |
| 3 | `cli` | `clap`, `[[bin]]`, 또는 `src/main.rs` | 명령, 출력 계약, 종료 코드, 배포 |
| 4 | `library` | 위에 해당하지 않는 `[package]` | 공개 API, 오류 타입, 기능 |

`rmcp`와 `axum`이 함께 있는 crate는 `mcp-server`입니다. Axum 가이드는 MCP 엔드포인트 밖의 HTTP 라우트에만 합류합니다. `[[bin]]`과 `wasm32` 타깃이 함께 있는 crate는 네이티브 테스트 하네스를 가진 `wasm`이며, 한 종류의 산출물 두 개가 아닙니다.

---

## 계층 아키텍처

```text
Process edge
  main.rs / bin/*.rs        -> argument parse, subscriber init, exit code
       |
       v
Application surface
  lib.rs                    -> run(cli) -> Result<(), E>, one public entry
       |
       v
Commands / tools / exported functions
  commands/<verb>.rs, tools/<tool>.rs, api/<area>.rs
       |
       v
Domain logic
  domain/<area>.rs          -> pure functions, no I/O ownership
       |
       v
Adapters
  io/, http/, fs/, host/    -> files, network, wasm-bindgen boundary, host calls
```

**데이터 흐름 규칙:**

- 프로세스 경계가 인자 파싱, subscriber 초기화, 단일 종료 코드 매핑을 소유합니다. 그 아래 어디에서도 `process::exit`를 호출하지 않습니다.
- 명령이나 도구 모듈은 이미 파싱된 타입 있는 입력을 받아 타입 있는 결과를 반환합니다. 문자열을 다시 파싱하거나 환경 변수를 읽지 않습니다.
- 도메인 로직은 프로세스 전역에서 자유로워 호스트의 `cargo test`로 테스트할 수 있습니다.
- 어댑터가 바깥 세계를 소유합니다. 파일 접근, HTTP, `wasm-bindgen` 경계, MCP 전송입니다. 도메인과 명령 코드가 어댑터를 호출하고 그 반대가 아닙니다.
- 라이브러리 crate는 애플리케이션 표면에서 끝납니다. subscriber를 초기화하거나 argv를 읽거나 stdout에 쓰지 않습니다.

---

## Crate 배치 불변 조건

모듈, 타깃, 기능, 워크스페이스 멤버를 추가하기 전에 `rules/rust/crate-layout.md`를 읽습니다.

- `main.rs`는 얇고 `lib.rs`가 `run`을 담습니다. 이 분리는 프로세스를 띄우지 않고 로직을 테스트할 수 있게 하려고 존재합니다.
- 모듈 하나에 소유자 하나. 출력을 포맷하고 I/O까지 하는 모듈은 아직 정해지지 않은 경계입니다.
- 기능은 가산적이고 문서화됩니다. 한 타깃만 필요한 기능은 그 타깃의 의존성 섹션에 둡니다.
- 워크스페이스 멤버는 `edition`, `rust-version`, 의존성 버전, lint를 상속합니다. 근거 없이 지역에서 반복하거나 덮어쓰지 않습니다.
- 모듈 트리는 관찰 가능한 소유 압력에서 자랍니다. 빈 `services/`, `domain/`, `adapters/` 폴더를 미리 만들지 않습니다.

---

## 오류와 로깅 불변 조건

전체 정책은 `rules/rust/errors-and-logging.md`를 읽습니다.

- `thiserror`가 라이브러리 오류 enum을 derive합니다. `anyhow`는 `.context(...)`와 함께 쓰는 애플리케이션 경계의 오류 타입입니다. 라이브러리 공개 함수는 `anyhow::Error`를 반환하지 않습니다.
- 섞는 방식은 명시적입니다. 명령이 라이브러리 오류를 위로 실어야 하면 변형이 `#[error(transparent)]`로 `anyhow::Error`를 감쌉니다.
- 종료 코드는 계약입니다. 성공은 0, 실패 종류마다 서로 다른 0이 아닌 코드, clap 파싱 오류는 2, 예방하지 못한 panic에만 101을 남깁니다.
- `tracing`이 로깅 표면입니다. `EnvFilter`에는 `features = ["env-filter"]`가 필요합니다. 기본이 아니며, `RUST_LOG`가 없으면 폭포수가 아니라 error 레벨입니다.
- stdout은 산출물을, stderr는 진단·진행·로그를 담습니다. 파이프 소비자는 진행 줄을 받지 않습니다.
- subscriber는 프로세스 경계에서 한 번 초기화하며, 테스트도 호출하는 라이브러리 함수에서는 절대 하지 않습니다.

---

## CLI 불변 조건

전체 정책은 `rules/rust/cli.md`를 읽습니다.

- clap derive 타입은 한 모듈(`cli.rs`)에 있고, 하나의 `Subcommand` enum이 모든 동사를 명명하며, 동사마다 명령 모듈이 하나입니다.
- derive 기능을 명시적으로 선언합니다. `derive`는 항상, `env`는 환경 폴백이 있을 때만입니다.
- 기계 출력은 계약입니다. `--json` 플래그가 `type` 판별자를 가진 JSON 문서를 줄마다 하나씩 내보내고, stdout이 터미널이 아니거나 플래그가 주어졌을 때 켜집니다.
- 셸 완성 경로는 손으로 쓰지 않고 `clap_complete`에서 생성합니다.
- 릴리스 바이너리는 `dist`(패키지 `cargo-dist`)의 태그 기반 워크플로에서 나오고, `[profile.dist]`는 `[profile.release]`와 분리된 채로 둡니다.

---

## WASM 불변 조건

전체 정책은 `rules/rust/wasm.md`를 읽습니다.

- `wasm32-unknown-unknown`은 JavaScript 호스트를, `wasm32-wasip1`과 `wasm32-wasip2`는 JavaScript 글루가 없는 WASI 호스트를 섬깁니다. 선택은 마지막으로 설치한 타깃이 암시하는 것이 아니라 기록됩니다.
- `crate-type = ["cdylib"]`이 모듈을 만들고, `rlib`를 더하면 같은 로직을 네이티브 테스트에서 도달할 수 있습니다.
- JavaScript 경계 crate는 `[target.'cfg(target_arch = "wasm32")'.dependencies]` 아래에 둡니다.
- 크기는 wasm-bindgen 실행 이후 `*_bg.wasm`에서 측정하고, 크기 변경마다 before/after 수치를 기록합니다.
- `web-sys` 기능은 인터페이스 단위이며, 기능 목록이 코드의 호출과 일치합니다.
- panic은 모듈 초기화 시 panic hook으로 표면화하고, hook crate의 유지보수 상태는 가정하지 않고 진술합니다.

---

## MCP 서버 불변 조건

전체 정책은 `rules/rust/mcp-server.md`를 읽습니다.

- 서버는 `rmcp`를 쓰고 대상 리비전을 진술합니다. `2026-07-28`이고 `2025-11-25` 이전과 호환됩니다.
- 전송은 기능입니다. stdio는 `transport-io`, HTTP는 라우터에 마운트하는 `transport-streamable-http-server`입니다.
- 각 도구는 `Parameters<T>`를 받는 `#[tool]` 함수 하나입니다. 스키마가 필드에서 오므로 필드 문서가 스키마 문서입니다.
- 도구 handler는 검증하고 평범한 함수로 위임합니다. 매크로 계층은 비즈니스 계층이 아니라 전송 어댑터입니다.
- stdio에서 stdout은 프로토콜 프레임 전용이고, subscriber writer는 구조적으로 stderr입니다.
- 레거시 HTTP+SSE 전송을 약속하지 않고, 폐기된 logging capability를 새 서버의 계획으로 삼지 않습니다.

---

## 테스트 불변 조건

전체 정책은 `rules/rust/testing.md`를 읽습니다.

- `assert_cmd`와 `predicates`가 프로세스 동작을 덮습니다. 바이너리는 손으로 만든 경로가 아니라 `cargo_bin!`으로 지목합니다.
- `trycmd`는 작은 CLI 전사 여러 개를, `insta`는 더 큰 값 스냅숏을 덮습니다. 기대 출력을 테스트 소스에 손으로 유지하지 않습니다.
- `wasm-bindgen-test`가 JavaScript 경계를 덮고, 출하하는 타깃으로 `wasm-pack test`를 돌립니다.
- MCP 도구는 평범한 함수로 테스트하고, stdio 메시지 교환을 구동하는 테스트 하나를 둡니다.
- 테스트는 부수적인 직렬화 순서나 벽시계 지연을 단언하지 않습니다.

---

## 성능 불변 조건

측정 트랙은 `rules/rust/performance.md`를 읽습니다.

- 먼저 기준선을 잡습니다. 릴리스 빌드에서 이름 붙인 명령 하나로 빌드 시간과 산출물 크기를 잽니다.
- 측정마다 레버 하나만 바꿉니다. `lto`, `codegen-units`, `opt-level`, `strip`, `panic`, `wasm-opt` 중 하나를 바꾼 뒤 같은 산출물을 다시 잽니다.
- Cargo 릴리스 기본값은 `lto = false`, `codegen-units = 16`, `opt-level = 3`, `panic = "unwind"`, `strip = "none"`이므로 강한 설정은 모두 명시적 선택입니다.
- `opt-level = "s"`가 `"z"`를 이길 수 있으므로 둘 다 측정한 뒤 고릅니다.
- 주장하는 이득에는 같은 명령, 같은 기계에서 잰 before/after 수치가 필요합니다.
- 할당 작업은 측정을 따릅니다. 커스텀 할당자는 기본값이 아니라 후보입니다.

---

## Sources

> Checked 2026-11-07. crate, 툴체인, 타깃, 명세 진술은 `references/official/rust/rust-crates-2026-11-07.md`를 다시 진술하며, 그 파일이 2026-11-07에 연 페이지를 인용합니다.

| Claim | Source |
|---|---|
| clap derive, 기능 기본값, 종료 코드 동작 | https://docs.rs/clap/latest/clap/_derive/index.html, https://docs.rs/crate/clap/latest/features, https://docs.rs/clap/latest/clap/error/struct.Error.html |
| 애플리케이션 경계의 `anyhow`, 라이브러리 오류의 `thiserror`, `#[error(transparent)]` | https://docs.rs/anyhow/latest/anyhow/, https://docs.rs/thiserror/latest/thiserror/ |
| `env-filter`는 `tracing-subscriber` 기본 기능이 아님 | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| 0–255 종료 코드, panic 코드 101, sysexits 지침 | https://rust-cli.github.io/book/in-depth/exit-code.html |
| `type` 필드를 가진 줄 단위 JSON 기계 출력 | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `wasm32-unknown-unknown`과 wasm-bindgen 이후 크기 측정 | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `rmcp` 3.9.0, `2026-07-28` 리비전, 도구 매크로, 전송 | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://docs.rs/crate/rmcp/latest/features |
| stdio는 stdout에 MCP가 아닌 데이터를 쓸 수 없음 | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| Cargo 릴리스 프로필 기본값 | https://doc.rust-lang.org/cargo/reference/profiles.html |
| 계층, 모듈 소유, 라벨 규약 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
