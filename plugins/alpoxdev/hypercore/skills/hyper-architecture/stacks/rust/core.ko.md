`hyper-architecture`의 Rust 스택 가이드입니다. Axum 서버가 아니고 Tauri 백엔드도 아닌 Rust crate를 다룹니다. `rules/stack-detection.ko.md`가 대상을 Rust로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다. 1단계에서 정한 프로필이 어떤 게이트를 적용할지 결정합니다.

- 범위: 제품 표면이 명령줄 바이너리, WebAssembly 모듈, Model Context Protocol 서버, 라이브러리 crate인 Rust crate를 만들거나 검토하거나 재구성하거나 감사할 때 사용합니다. crate와 모듈 배치, 오류와 로깅 정책, CLI 인자 파싱과 출력 계약, WASM 타깃과 바인딩 선택, MCP 도구와 전송 배선, 테스트, 측정된 릴리스 작업을 다룹니다. Axum HTTP 서버, Tauri `src-tauri` crate, 라우터가 읽지 않은 `Cargo.toml`만이 신호인 crate, 아키텍처 경계를 넘지 않는 문구만의 수정, Hypercore 규약 없이 공식 crate 기본값만 원하는 요청에는 사용하지 않습니다.
- 실행 조건: 대상의 `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml` 또는 `.cargo/config.toml`, 그리고 소스 트리가 있을 때 그것들입니다. 버전과 API 주장에는 `references/official/rust/rust-crates-2026-11-07.md`의 날짜가 붙은 스냅숏이 필요합니다. `cargo check`, `cargo clippy`, `cargo test`, 프로젝트 자체 빌드 명령이 검증 수단이고 내장 스크립트는 없습니다.

@architecture-rules.md
@../../rules/rust/crate-layout.md
@../../rules/rust/errors-and-logging.md
@../../rules/rust/cli.md
@../../rules/rust/wasm.md
@../../rules/rust/mcp-server.md
@../../rules/rust/testing.md
@../../rules/rust/performance.md
@../../references/official/rust/rust-crates-2026-11-07.md

# Rust Crate 아키텍처

> crate의 프로필을 manifest에서 먼저 정하고, 모든 Rust 규칙을 모든 crate에 적용하는 대신 프로필마다 하나의 게이트 묶음을 강제합니다.

<output_language>

이 스킬 파일이 영어로 작성되어 있어도, 사용자에게 보이는 모든 산출물, 저장 문서, 보고서, 계획, 생성 문서, 요약, 인수인계 메모, 커밋 메시지 초안, 검증 노트의 기본 언어는 한국어입니다.

소스 코드 식별자, CLI 명령, 파일 경로, crate 이름, 타입 이름, JSON 필드 이름, MCP capability 이름, 인용한 원문은 필요한 원래 언어 그대로 둡니다. 사용자가 다른 언어를 명시적으로 요청했거나, 기존 대상 산출물의 일관성을 위해 다른 언어를 유지해야 하거나, 기계 판독 계약이 정확한 영어 토큰을 요구할 때만 다른 언어를 씁니다.

</output_language>

<purpose>

- 코드를 바꾸기 전에 Hypercore Rust crate 아키텍처를 강제합니다.
- 프로필 전용 게이트를 적용하기 전에 crate의 프로필을 증명합니다. CLI 규칙과 WASM 규칙은 출력과 panic 동작에서 서로 모순되기 때문입니다.
- crate 경계를 정직하게 유지합니다. 워크스페이스 공통 규약은 셋업 기준선이 소유하고, 이 가이드는 crate 구조와 런타임 동작을, Axum과 Tauri 가이드는 각자 표면을 소유합니다.
- 공식 crate 동작과 이 패키지의 기본값을 구분하고, 풀리지 않은 주제는 단정하지 않고 미검증으로 표시합니다.

</purpose>

<routing_rule>

Axum 서버가 아니고 Tauri 백엔드도 아닌 Rust crate의 셋업, 구현, 검토, 교정, 아키텍처 강제에 이 가이드를 사용합니다.

- `rmcp` 의존성이 있는 crate는 MCP 전송에 `axum`을 함께 써도 `mcp-server` 프로필로 이 가이드에 라우팅합니다. Axum 가이드는 MCP 엔드포인트 밖의 HTTP 라우트를 건드릴 때만 더합니다.
- JavaScript 호스트용 `.wasm`을 만드는 crate는 `wasm` 프로필로 이 가이드에 라우팅합니다. WASI 바이너리 모듈은 타깃만 다른 같은 프로필이며 별도 가이드가 아닙니다.
- 명령줄 인터페이스를 가진 바이너리 crate는 `cli` 프로필로 이 가이드에 라우팅합니다.
- `axum` 의존성이 없고 `[package]`가 있는 나머지는 `library` 프로필로 이 가이드에 라우팅합니다.

`axum` 서비스, `src-tauri` crate, 런타임 표면이 없는 빌드 스크립트나 proc-macro 전용 crate, 공식 crate 기본값만 원하는 요청에는 이 규칙을 적용하지 않습니다. 마지막 경우 `hypercore-default` 규칙은 선택적 발견으로 낮춥니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | 프로필, 소유 경계, 실패 동작, 출력 계약, 릴리스 설정을 검토 가능하고 성장해도 안정적인 Rust crate를 만듭니다. |
| Trigger | crate나 모듈 배치, `main.rs`와 `lib.rs`, 오류 타입, 로깅, CLI 파싱과 출력, WASM 타깃과 바인딩, MCP 도구와 전송, 테스트, 릴리스 프로필을 건드리는 Rust 작업. |
| Scope | 건드린 Rust 소스, `Cargo.toml`과 `Cargo.lock`, `rust-toolchain.toml`, `.cargo/config.toml`, 프로필 섹션, 테스트, 해당 규칙 파일, 작고 되돌릴 수 있는 수정. |
| Authority | 사용자와 프로젝트 지시가 이 가이드보다 우선합니다. API 사실에서는 공식 crate 문서가 우선합니다. 설치된 툴체인과 잠긴 의존성 버전이 프로젝트 동작을 결정합니다. Hypercore 기본값은 프로젝트가 채택할 때까지 권고입니다. |
| Evidence | manifest, lockfile, 툴체인 파일, 진입점, 건드린 소스와 테스트를 읽습니다. 버전이나 API 기본값 질문이 변경을 가를 때 날짜가 붙은 스냅숏을 씁니다. |
| Tools | 읽기, 검색, 수정, `cargo check`, `cargo clippy`, `cargo test`, `cargo build --release`, 프로젝트 자체 패키징 명령. 의존성 설치, 배포, WASM 후처리 설치, 배포(deploy)는 게이트합니다. |
| Loop | 요청당 검토 또는 교정 한 번, 그 뒤 활성 프로필의 3단계 게이트와 건드린 검사에 대해 최대 두 번의 검증-수리 반복. 변경은 건드린 범위 안에 있고 게이트를 통과할 때만 유지합니다. |
| Output | 프로필, `official`·`hypercore-default` 라벨, 변경 파일, 검증 근거, 남은 위험을 담은 한국어 발견 또는 구현 요약. |
| Verification | 활성 프로필의 `cargo check`, `cargo clippy`, 건드린 테스트와 함께 그 프로필의 산출물 검사(바이너리 실행, `*_bg.wasm` 크기, MCP 메시지 교환)를 수행합니다. |
| Stop condition | 읽은 manifest로 프로필이 증명되고, 해당 게이트가 통과하거나 차단 사유로 보고되고, 근거가 기록되면 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive:

- `이 Rust CLI 구조를 서브커맨드 늘리기 전에 정리해줘.` (`Cargo.toml`에 `clap`이 있고 `axum`이 없음)
- `Refactor this Rust crate into a thin main plus a testable lib, no behavior change.`
- `이 wasm-bindgen 크레이트 크기 줄이고 tsify 타입 붙여줘.`
- `rmcp로 만든 MCP 서버 crate 구조 정리해줘.`
- `hyper-architecture 전체 수정`

Negative:

- `Actix Web이나 Axum 서버 구조를 정리해줘.` 그 표면은 해당 가이드가 소유합니다.
- `src-tauri 안의 Rust 코드를 정리해줘.` 그 crate는 Tauri가 소유합니다.

Boundary:

- `CLI 출력 문구 한 줄만 바꿔줘.` 변경과 경계 확인 한 번만 수행합니다.
- `Use official crate defaults only, not the extra Hypercore conventions.` 가이드는 여전히 적용되지만 `hypercore-default` 엄격성은 낮아집니다.

</activation_examples>

<trigger_conditions>

인자는 교정 범위를 바꾸며 규칙은 바꾸지 않습니다.

| Argument | Meaning |
|---|---|
| missing | 요청받았거나 건드린 범위를 검토·수정합니다. 건드리지 않은 드리프트는 백로그로 보고할 수 있습니다. |
| `전체 수정` | 감지한 crate 전체에 대한 교정 모드. 이번 실행에서 안전하게 바꿀 수 있는 모든 모듈, 타깃, 테스트, 프로필 섹션을 다룹니다. |
| `full fix` / `fix all` | `전체 수정`과 같습니다. |
| `공식 기본만` / `official defaults only` | `전체 수정`을 함께 요청하지 않았다면 `hypercore-default` 규약을 선택적 발견으로 낮춥니다. |

</trigger_conditions>

<skill_architecture>

- Core(`stacks/rust/core.md`): 프로필 선택, 계약, 게이트 순서, 워크플로, 검증, 정지 조건.
- Rules: `stacks/rust/architecture-rules.md`와 `reference_routing`에 매핑된 주제 파일.
- References: `references/official/rust/rust-crates-2026-11-07.md`가 날짜가 붙은 crate, 타깃, 명세 사실을 담습니다.
- Assets: `assets/evals/rust-cases.jsonl`이 트리거와 동작 사례를 담습니다.
- 별도 트랙: `rules/setup/rust.md`가 워크스페이스 공통 툴링(툴체인 고정, rustfmt, clippy, `[workspace.lints]`, resolver, 릴리스 프로필, 공급망 검사)을, `rules/rust/performance.md`가 측정된 성능 작업을 소유합니다. 이 가이드는 둘을 다시 서술하지 않고 참조합니다.

</skill_architecture>

<loop_policy>

- 요청당 검토 또는 교정 한 번입니다.
- 교정 후 활성 프로필의 게이트와 건드린 검사에 대해 최대 두 번의 검증-수리 반복이 실행됩니다. 변경은 건드린 범위 안에 있고 게이트를 통과할 때만 유지됩니다.
- 성능 주장은 `rules/rust/performance.md`의 측정-변경-측정 루프를 따르며, 리팩터를 정당화하려고 이 루프에 들어오지 않습니다.

</loop_policy>

<language_and_translation_default>

발견, 교정 요약, 검증 노트는 한국어로 씁니다. 식별자, 경로, crate 이름과 타입 이름, `official`·`hypercore-default` 라벨은 원래 형태로 두어 보고가 규칙 파일과 1:1로 대응하게 합니다. `stacks/rust/core.ko.md`는 이 파일을 절 단위로 미러링하며, 여기서 규칙을 바꾸면 같은 편집에서 저쪽도 바꿉니다.

</language_and_translation_default>

<reference_routing>

수정 전에 `stacks/rust/architecture-rules.md`를 읽고, 그다음 건드린 표면을 소유한 파일만 엽니다.

| Touched surface | File |
|---|---|
| `main.rs`와 `lib.rs` 분리, 모듈 배치, 워크스페이스 멤버, 기능 플래그, crate 경계 | `rules/rust/crate-layout.md` |
| `anyhow`와 `thiserror`, 종료 코드, `ExitCode`, tracing 설정, `EnvFilter`, stdout과 stderr | `rules/rust/errors-and-logging.md` |
| clap derive와 env 기능, 서브커맨드, 출력 계약, NDJSON과 `IsTerminal`, 완성 스크립트 생성, `dist` 릴리스 바이너리 | `rules/rust/cli.md` |
| WASM 타깃 선택, `crate-type`, wasm-bindgen과 wasm-pack, 크기 측정, `tsify`, `web-sys` 기능, panic hook | `rules/rust/wasm.md` |
| `rmcp` 버전과 명세 리비전, 도구 매크로, schemars 입력 스키마, stdio와 Streamable HTTP 전송, stdout 규율 | `rules/rust/mcp-server.md` |
| `assert_cmd`, `trycmd`와 `insta`, `wasm-bindgen-test`, MCP 도구와 stdio 테스트 | `rules/rust/testing.md` |
| 측정된 릴리스 작업: 빌드 시간, 바이너리와 `*_bg.wasm` 크기, 릴리스 프로필 레버, 할당 핫 패스 | `rules/rust/performance.md` |
| 툴체인 고정, rustfmt, clippy, `[workspace.lints]`, resolver, 릴리스 프로필 소유, 공급망 검사 | `rules/setup/rust.md` |
| 규칙 뒤의 버전, 기능 기본값, MSRV, 타깃 계층, 명세 사실 | `references/official/rust/rust-crates-2026-11-07.md` |

워크스페이스 공통 규약은 `rules/setup/rust.md`가 소유합니다. resolver, lint, 툴체인, 릴리스 프로필 규칙을 여기서 중복하지 않습니다. 이 가이드는 crate 아키텍처가 의존하는 것만 진술합니다.

</reference_routing>

<support_file_read_order>

1. 규칙 분류와 차단 게이트를 위해 `stacks/rust/architecture-rules.md`.
2. `reference_routing` 순서로 건드린 표면의 주제 파일.
3. 모듈, 타깃, 기능을 옮기거나 추가하기 전에 `rules/rust/crate-layout.md`.
4. 툴링이 범위에 있지만 소유 질문이 이미 정리됐으면 `rules/setup/rust.md`.
5. 버전, 기본 기능, MSRV, 타깃 계층, 명세 리비전이 변경을 가를 때 `references/official/rust/rust-crates-2026-11-07.md`.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | crate가 Rust임을 증명하고 manifest로 프로필을 고름 | 결정 필드가 붙은 프로필 |
| 2 | 건드린 표면의 규칙 파일을 읽음 | 최소 근거 집합 |
| 3 | 계획한 변경을 그 프로필의 게이트에 대조 | 파일 경로가 붙은 발견 |
| 3.5 | 건드린 범위 안에서 저위험 자동 교정 적용 | 수정 또는 백로그 항목 |
| 4 | 아래 순서로 구현하고 검증 | 변경 파일과 근거 |

1단계 — 프로필 선택. 무엇보다 먼저 manifest를 읽습니다. 프로필이 이후 어떤 게이트가 존재하는지를 결정합니다.

```bash
rg -n '^\[package\]|^\[lib\]|^\[\[bin\]\]|^\[workspace\]|^\[features\]|crate-type|^rmcp|^clap|^wasm-bindgen|^axum' Cargo.toml
rg -n 'rust-version|edition|resolver|lints' Cargo.toml
cat rust-toolchain.toml 2>/dev/null; cat .cargo/config.toml 2>/dev/null
```

그다음 `rules/stack-detection.ko.md`가 이미 진술한 감지 순서를 적용합니다. 첫 일치가 이깁니다.

| Order | Profile | Deciding evidence |
|---|---|---|
| 1 | `mcp-server` | `[dependencies]`의 `rmcp`. MCP 전송에 `axum`을 함께 쓰는 crate도 포함합니다. |
| 2 | `wasm` | `"cdylib"`를 포함하는 `[lib] crate-type`과 `wasm-bindgen` 의존성, 또는 `rust-toolchain.toml`이나 `.cargo/config.toml`의 `wasm32-*` 타깃 |
| 3 | `cli` | `clap` 의존성, `[[bin]]` 섹션, 또는 `src/main.rs` |
| 4 | `library` | 위에 해당하지 않는 `[package]` |

프로필은 라우터가 스택을 보고하는 것과 같은 방식으로 근거와 함께 보고합니다. 한 산출물 묶음에서 동시에 참일 수 없는 두 프로필이 manifest에 보이면 두 필드를 보고하고 어느 쪽을 대상으로 하는지 묻습니다.

3단계 — 핵심 게이트. 공통 블록과 선택한 프로필의 블록만 적용합니다. 차단 게이트는 건드리지 않은 코드가 같은 패턴을 보여도 실패입니다.

공통 게이트:

- crate의 아키텍처가 `Cargo.toml`만으로 보입니다. 타깃, 기능, 의존성이 crate가 무엇인지 말하고, 어떤 모듈도 두 프로필의 규약을 섞지 않습니다.
- 워크스페이스 설정은 상속하고 중복하지 않습니다. `edition`, `rust-version`, 의존성 버전, lint는 `[workspace.package]`, `[workspace.dependencies]`, `[workspace.lints]`에서 오고, 프로필 섹션은 워크스페이스 루트에만 둡니다.
- Rust 모듈과 파일 이름은 `snake_case`이고, 의존성은 crate가 실제로 가진 동작에만, 코드가 쓰는 기능만 켜서 추가합니다.

`cli` 게이트:

- `main.rs`는 얇은 진입점이고 로직은 테스트 가능한 함수 뒤 `lib.rs`에 있습니다.
- clap이 파싱 오류를 소유합니다. 도움말과 버전은 stdout으로 종료 코드 0, 파싱 오류는 stderr로 종료 코드 2이고, crate가 그 경로를 직접 포맷하거나 종료하지 않습니다.
- 사람용 출력과 기계용 출력은 명시적 플래그나 TTY 검사로 분리되고, 진단은 stderr로 갑니다.
- 실패 종류마다 panic이 아닌 서로 다른 종료 코드가 있고, 101을 직접 쓰지 않습니다.

`wasm` 게이트:

- 타깃을 의도적으로 고릅니다. JavaScript 호스트면 `wasm32-unknown-unknown`, WASI 호스트면 `wasm32-wasip1`이나 `wasm32-wasip2`이며 실수로 섞지 않습니다.
- `crate-type`에 `cdylib`이 있고, 순수 로직은 네이티브 `cargo test`에서 도달 가능합니다.
- 크기는 wasm-bindgen 이후의 `*_bg.wasm` 산출물에서 측정하고 rustc 원본 출력에서는 측정하지 않습니다.
- JavaScript 경계 crate는 crate 전체가 WASM 전용이 아닌 한 `[target.'cfg(target_arch = "wasm32")'.dependencies]` 아래에 둡니다.

`mcp-server` 게이트:

- 서버는 `rmcp`로 만들고 대상 명세 리비전을 진술합니다. `2026-07-28`이고 `2025-11-25` 이전 버전과 호환됩니다.
- 전송은 기능으로 선언하고, 고른 전송이 배포와 맞습니다. stdio는 `transport-io`, HTTP는 `transport-streamable-http-server`입니다.
- stdio에서는 MCP 메시지 외에는 stdout에 도달하지 않고, 모든 로그 싱크가 구조적으로 stderr에 씁니다.
- 도구 입력 스키마는 필드에 문서가 붙은 타입 있는 `Parameters<T>`에서 오며, 타입 이름과 구조체 문서는 쓰이지 않습니다.
- 도구 handler는 네이티브 테스트가 호출할 수 있는 평범한 함수로 위임합니다.

`library` 게이트:

- 공개 API가 의도적입니다. 공개 항목은 `lib.rs`에서 도달 가능하고, 내부 모듈은 비공개이며, 공유 내부는 `pub(crate)`가 기본입니다.
- 오류 타입은 `thiserror` enum이고 `anyhow`는 공개 API에 나타나지 않습니다.
- 기능 플래그는 의존성이나 빌드 비용을 바꾸고, 가산적이며, 문서화됩니다. `default`는 작게 유지합니다.
- 라이브러리는 프로세스를 소유하지 않으므로 프로세스 인자를 읽거나, stdout에 쓰거나, 전역 subscriber를 설정하지 않습니다.

3.5단계 — 자동 교정. 국소적이고 되돌릴 수 있으며 저위험이면 직접 고칩니다.

- `main.rs`의 로직을 `lib.rs`로 옮기고 `main`은 `ExitCode`를 반환하는 얇은 진입점으로 남깁니다.
- 호출 경로 깊은 곳의 `process::exit`를 반환되는 오류와 맨 위의 단일 종료 코드 매핑으로 바꿉니다.
- CLI나 MCP 경로의 `println!` 진단을 로깅 스택을 거쳐 stderr로 옮기고, 손으로 파싱하는 대신 빠진 clap 기능(`derive`, 환경 폴백이 있으면 `env`)을 추가합니다.
- `wasm-bindgen`이나 `web-sys` 의존성을 `wasm32` 타깃 섹션으로 옮기고, 쓰는 인터페이스가 요구하는 `web-sys` 기능을 추가하며, 네이티브 테스트가 같은 로직에 도달하도록 `cdylib` 옆에 `rlib`를 추가합니다.
- 손으로 만든 MCP `Tool` 값을 `Parameters<T>`를 받는 `#[tool]` 함수로 바꿉니다.
- 건드린 `camelCase`나 `kebab-case` 모듈을 `snake_case`로 바꾸고 같은 변경에서 `mod` 선언과 import를 갱신합니다.

광범위하거나 깨질 수 있는 변경은 자동 적용하지 않습니다. 비동기 런타임 교체, 공개 API 전체에서 `anyhow`를 `thiserror`로 교체, crate 타입이나 WASM 타깃 변경, 공개된 CLI 플래그나 출력 모양 변경, MCP 도구 이름이나 입력 스키마 변경, 릴리스 프로필 재작성입니다.

4단계 — 구현 순서.

1. 프로필을 확인하고 manifest, 툴체인 파일, 진입점을 읽습니다.
2. `main.rs`/`lib.rs` 분리와 기능 집합을 포함해 crate와 모듈 소유를 고칩니다.
3. 오류와 로깅 정책, 그다음 출력 계약을 고칩니다.
4. 프로필 자체 경계를 적용합니다. CLI 파싱과 서브커맨드, WASM 타깃과 바인딩, MCP 도구와 전송, 또는 라이브러리 공개 API입니다.
5. 테스트를 추가하거나 고친 뒤, 성능은 마지막에 레버 하나씩 측정하며 바꿉니다.
6. 검증을 실행합니다.

</workflow>

<required>

- 프로필 전용 규칙을 적용하기 전에 읽은 manifest와 그것을 결정한 필드로 프로필을 증명합니다.
- crate 경계를 지킵니다. 워크스페이스 공통 규약은 `rules/setup/rust.md`로 미루고, Axum과 Tauri 표면은 각자 가이드에 남깁니다.
- crate마다 실패 정책 하나를 둡니다. 라이브러리 경계에는 `thiserror` enum, 애플리케이션 경계에는 `anyhow`, panic이 아닌 서로 다른 종료 코드, 직접 쓴 101 없음입니다.
- `cli`에서는 얇은 `main.rs`와 테스트 가능한 `lib.rs`, clap이 소유하는 파싱 오류, 분리된 출력 경로.
- `wasm`에서는 명시적 타깃과 crate 타입, wasm-bindgen 이후 산출물에서 측정한 크기.
- `mcp-server`에서는 명세 리비전을 진술한 `rmcp`, 기능으로 선언한 전송, 프로토콜 메시지만 쓰는 stdout.
- `library`에서는 안정된 공개 API와 프로세스 소유 없음.
- 각 발견을 `official` 또는 `hypercore-default`로 표시하고, 미검증 주제는 미검증으로 밝힌 보고.
- `cargo check`, `cargo clippy`, 건드린 테스트, 프로필 산출물 검사의 근거.

</required>

<forbidden>

- crate 프로필을 정하지 않은 채 CLI 출력이나 종료 코드 규칙을 WASM 모듈이나 MCP 서버에, WASM 크기 규칙을 네이티브 바이너리에 적용하는 것.
- `axum` 의존성이 있는 Rust crate를 이 가이드의 대상으로, `src-tauri` crate를 Tauri 아닌 것으로 취급하거나, `rules/setup/rust.md` 내용(resolver, lint, 툴체인, 릴리스 프로필)을 crate 규칙 파일 안에 중복하는 것.
- `target/wasm32-unknown-unknown/release/*.wasm` 원본에서 WASM 크기를 주장하거나, stdio MCP 서버의 stdout에 MCP 메시지가 아닌 것을 쓰는 것.
- 날짜가 붙은 스냅숏이 진술하지 않은 버전, MSRV, 명세 리비전을 승격하는 것.
- 기록된 결정 없이 공개 CLI 플래그, MCP 도구 이름, 공개 라이브러리 항목을 이름 변경하거나, 명령 출력 없이 게이트를 통과로 보고하는 것.

</forbidden>

<validation>

- [ ] crate의 프로필과 결정한 manifest 필드를 기록했다.
- [ ] 건드린 표면의 규칙 파일을 읽었고, 요청 시 `공식 기본만`을 적용했다.
- [ ] crate가 멤버일 때 워크스페이스 상속을 쓰고, 멤버 manifest에 프로필 섹션이 없다.
- [ ] `cli` 대상에서 `main.rs`와 `lib.rs`가 올바르게 분리됐거나, 라이브러리 절반이 없는 이유를 밝혔다.
- [ ] 오류 정책 하나가 자리잡았다. 라이브러리 경계의 `thiserror`, 애플리케이션 경계의 `anyhow`, panic이 아닌 종료 코드.
- [ ] stdout이 계약만 담는다. `cli`는 사람용 출력이나 플래그 뒤의 NDJSON, stdio `mcp-server`는 프로토콜 메시지뿐이다.
- [ ] `EnvFilter`를 쓰는 모든 곳에서 기본이 아닌 `env-filter` 기능을 켰다.
- [ ] `wasm`은 타깃, crate 타입, `web-sys` 기능 집합이 코드와 맞고, 크기를 `*_bg.wasm`에서 측정했다.
- [ ] `mcp-server`는 명세 리비전을 진술하고, 전송이 기능이며, 도구 스키마가 타입 있는 필드에서 온다.
- [ ] `library`는 공개 API가 의도적이고 crate가 프로세스 전역 동작을 소유하지 않는다.
- [ ] `cargo check`, `cargo clippy`, 건드린 테스트를 실행하고 프로필 산출물 검사를 기록했다.
- [ ] 발견을 `official` 또는 `hypercore-default`로 표시하고 미검증 주제를 미검증으로 밝혔다.

</validation>

## Sources

> Checked 2026-11-07. 이 진술은 패키지의 날짜가 붙은 스냅숏 `references/official/rust/rust-crates-2026-11-07.md`를 다시 진술하며, 그 파일이 2026-11-07에 읽은 crate 문서, Cargo Book, MCP 명세를 인용합니다.

| Claim | Source |
|---|---|
| clap 4.6.7 derive 표면, 기능 기본값, 종료 코드 계약 | https://docs.rs/clap/latest/clap/_derive/index.html, https://docs.rs/crate/clap/latest/features, https://docs.rs/clap/latest/clap/error/struct.Error.html |
| 애플리케이션에는 `anyhow`, 라이브러리 오류 enum에는 `thiserror` | https://docs.rs/anyhow/latest/anyhow/, https://docs.rs/thiserror/latest/thiserror/ |
| `tracing-subscriber`의 `env-filter`는 기본 기능이 아님 | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| 이식 가능한 0–255 종료 코드와 panic 코드 101 | https://rust-cli.github.io/book/in-depth/exit-code.html |
| `wasm32-unknown-unknown` 타깃 동작과 `cdylib` 배치 | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html, https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| 크기는 wasm-bindgen 이후 `*_bg.wasm`에서 측정 | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `rmcp` 3.9.0과 `2026-07-28` 명세 리비전 | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md |
| stdio 전송은 stdout에 MCP가 아닌 데이터를 쓸 수 없음 | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| 프로필 순서, 소유 경계, `hypercore-default` 라벨 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
