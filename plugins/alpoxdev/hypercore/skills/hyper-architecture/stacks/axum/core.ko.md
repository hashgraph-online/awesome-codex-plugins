`hyper-architecture`의 Axum 스택 가이드입니다. `rules/stack-detection.ko.md`가 대상을 Axum로 라우팅하면 이 파일을 읽고, 이 파일이 그 대상의 작업을 맡습니다.

- 범위: Axum(Rust) HTTP 서버 아키텍처를 만들거나 검토하거나 재구성하거나 감사할 때 사용합니다. 프로젝트와 모듈 구조, Router 조립, handler와 extractor, tower 및 tower-http 미들웨어, 요청 검증, SQLx 영속성과 마이그레이션, 오류 처리, OpenAPI/Swagger 계약, 테스트, tokio 서버 부트스트랩을 다룹니다. Actix Web, Rocket, Poem, warp 같은 Axum이 아닌 Rust 프레임워크, 클라이언트 전용 Rust 코드, 아키텍처 경계를 넘지 않는 문구만의 수정, Hypercore 규약 없이 공식 crate 기본값만 원하는 요청에는 사용하지 않습니다.
- 실행 조건: Axum 프로젝트가 있거나 새로 만들어 달라는 요청이 필요합니다. 버전과 API 주장에는 공식 axum, tower, tower-http, sqlx, utoipa, validator 문서와 로컬 Cargo.toml·Cargo.lock 확인이 필요합니다. 내장 스크립트는 없고, cargo check, cargo clippy, 프로젝트 테스트가 검증 수단입니다.

@architecture-rules.md
@../../rules/axum/project-structure.md
@../../rules/axum/routes.md
@../../rules/axum/handlers.md
@../../rules/axum/middleware.md
@../../rules/axum/validation.md
@../../rules/axum/database.md
@../../rules/axum/openapi.md
@../../rules/axum/errors.md
@../../rules/axum/testing.md
@../../rules/axum/platform.md
@../../rules/axum/conventions.md
@../../references/official/axum/axum-docs.md
@../../references/official/axum/tower-docs.md
@../../references/official/axum/sqlx-docs.md
@../../references/official/axum/utoipa-docs.md
@../../references/official/axum/ecosystem-docs.md

# Axum 아키텍처 강제

<output_language>

이 스킬 파일이 영어로 작성되어 있어도, 사용자에게 보이는 모든 산출물, 저장 문서, 보고서, 계획, 생성 문서, 요약, 인수인계 메모, 커밋 메시지 초안, 검증 노트의 기본 언어는 한국어입니다.

소스 코드 식별자, CLI 명령, 파일 경로, crate 이름, 타입 이름, JSON/YAML 필드 이름, API 이름, 인용한 원문은 필요한 원래 언어 그대로 둡니다.

사용자가 다른 언어를 명시적으로 요청했거나, 기존 대상 산출물의 일관성을 위해 다른 언어를 유지해야 하거나, 기계 판독 계약이 정확한 영어 토큰을 요구할 때만 다른 언어를 씁니다.

</output_language>

<purpose>

- 코드를 바꾸기 전에 Hypercore Axum 아키텍처 규칙을 강제합니다.
- Axum 전용 게이트를 적용하기 전에 대상이 실제 Axum 서버인지 확인합니다.
- 조립, handler와 extractor, tower 미들웨어, 검증, SQLx 영속성, 마이그레이션, 오류 처리, OpenAPI 계약, 테스트, 서버 부트스트랩의 일관성을 유지합니다.
- 이 저장소가 다른 서버 스택에 적용하는 것과 같은 아키텍처 관심사를 Rust의 소유권·타입 규칙으로 옮겨 적용합니다.
- axum보다 엄격한 요구는 보고할 때 Hypercore 규약으로 표시합니다.

</purpose>

<routing_rule>

Axum 서버의 구현, 검토, 교정, 아키텍처 강제에 이 스킬을 사용합니다.

Actix Web, Rocket, Poem, warp 등 다른 Rust 웹 프레임워크, 클라이언트 전용 또는 임베디드 Rust, 아키텍처 경계를 넘지 않는 문구만의 수정, 공식 crate 기본값만 원하는 요청에는 이 스킬을 강제하지 않습니다.

이 스킬은 자기 완결적입니다. Axum 규칙을 적용하려고 다른 스킬의 설치, 경로, 호출에 의존하지 않습니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Axum 서버를 아키텍처적으로 안전하고, 타입이 살아 있고, 관측 가능하고, 문서화되게 유지하며, 공식 crate 동작과 표시된 Hypercore 규약에 맞춥니다. |
| Trigger | 구조, Router 조립, handler, extractor, 미들웨어, 검증, SQLx, 마이그레이션, OpenAPI, 오류, 테스트, 부트스트랩을 건드리는 Axum 작업. |
| Scope | 건드린 Axum 소스, `Cargo.toml`, 마이그레이션, 주제 규칙 파일, 공식 참조, 작고 되돌릴 수 있는 아키텍처 수정을 검토하고 안내합니다. |
| Authority | 사용자와 프로젝트 지시가 이 스킬보다 우선합니다. API 사실에서는 공식 crate 문서가 Hypercore 규약보다 우선합니다. 안전, 타입, 검증, 데이터 경계 규칙은 위험한 변경을 차단합니다. |
| Evidence | 저장소 표지, `Cargo.toml`/`Cargo.lock`, 건드린 경로, 주제 규칙, 드리프트가 문제일 때 공식 참조, 컴파일러·테스트 출력을 사용합니다. |
| Tools | 로컬 검색, 읽기, 수정, `cargo check`, `cargo clippy`, `cargo test`, 로컬 HTTP 스모크 요청을 사용합니다. 마이그레이션, 자격 증명 접근, 프로덕션 부작용, 런타임 교체, 광범위한 재작성은 게이트합니다. |
| Loop | 최적화 루프는 없습니다. 교정 후 3단계 게이트와 건드린 검사에 대해 최대 두 번의 검증-수리 반복만 허용하고, 건드린 범위 안에 있고 게이트를 통과할 때만 변경을 유지합니다. |
| Output | 규칙 분류, 변경 파일, 검증 근거, 남은 위험, 공식 대 Hypercore 라벨을 포함한 한국어 아키텍처 발견 또는 구현 요약. |
| Verification | 관련 `cargo` 검사와 건드린 표면의 최종 체크리스트를 실행하고, 변경 표면에 도달 가능하면 실제 요청 하나를 수행합니다. |
| Stop condition | 프로젝트 모드가 확인되고, 해당 게이트가 통과하거나 차단 사유로 보고되고, 검증 근거가 기록되면 멈춥니다. |

</instruction_contract>

<activation_examples>

Positive examples:

- `이 Axum 서비스 구조를 라우트 추가 전에 검토해줘.`
- `Axum API의 라우팅, 상태, 미들웨어, 오류 처리를 하나의 아키텍처로 리팩터해줘.`
- `새 Axum 라우트를 추가하고 extractor 순서와 typed rejection을 유지해줘.`
- `handler가 풀을 직접 만지지 않게 SQLx를 이 Axum API에 연결해줘.`
- `영속 엔드포인트를 추가하기 전에 SQLx 마이그레이션과 OpenAPI 경계를 검토해줘.`
- `hyper-architecture 전체 수정`

Negative examples:

- `일반적인 Actix Web 미들웨어 가이드를 만들어줘.`
- `Rust 서버가 없는 React SPA를 검토해줘.`

Boundary examples:

- `Axum health 응답 문자열만 한 줄 바꿔줘.` 아키텍처 경계가 걸리지 않으면 직접 수정으로 충분합니다.
- `공식 Axum 기본값만 쓰고 Hypercore 추가 규약은 빼줘.` 이 스킬은 여전히 적용되지만, 공식 문서를 넘는 Hypercore 전용 엄격성은 선택 사항으로 낮춥니다.
- `이 저장소에는 Hono API와 Rust Axum 워커가 있어.` 이 스킬은 Axum 워커만 소유하고, 다른 서버는 자기 아키텍처 규칙을 유지합니다.

</activation_examples>

<trigger_conditions>

인자는 교정 범위를 바꾸며 핵심 규칙은 바꾸지 않습니다.

| Situation | Mode |
|---|---|
| 인자 없음 | 요청받았거나 건드린 Axum 범위를 검토·수정합니다. 건드리지 않은 기존 드리프트는 Hypercore 전용이거나 마이그레이션이 위험하면 백로그로 보고할 수 있습니다. |
| `전체 수정` | 전체 교정 모드. 감지한 Axum 서버 전체를 스캔하고 안전하고 국소적이며 되돌릴 수 있고 검증 가능한 모든 위반을 고칩니다. 건드린 파일에서 멈추지 않습니다. |
| `full fix` / `fix all` | `전체 수정`과 같습니다. |
| `공식 기본만` / `official defaults only` | 공식 crate 동작을 기본 표면으로 쓰고, 사용자가 `전체 수정`도 요청하지 않았다면 Hypercore 전용 규약을 선택적 발견으로 낮춥니다. |

`전체 수정` 모드에서:

- 모든 Rust 소스, `Cargo.toml`, 라우트 모듈, handler, extractor, 미들웨어, SQLx 쿼리와 마이그레이션, OpenAPI 정의, 테스트, 부트스트랩 진입점을 범위에 넣습니다.
- 감지한 Axum crate의 모듈과 파일 이름을 스캔합니다. Rust 소스 모듈은 `snake_case`여야 하며 kebab-case로 바꾸지 않습니다.
- 3.5단계의 저위험 자동 교정을 건드린 파일만이 아니라 crate 전체에 적용합니다.
- 같은 실행에서 안전하게 끝낼 수 없는 위험한 변경은 파일 경로와 실패한 규칙을 담은 정확한 차단 항목이나 백로그로 남깁니다. 조용히 무시하지 않습니다.

</trigger_conditions>

<skill_architecture>

- Core(`stacks/axum/core.md`): 트리거, 계약, 게이트 순서, 교정 정책, 검증, 정지 조건.
- Rules: `stacks/axum/architecture-rules.md`와 `reference_routing`에 매핑된 주제 파일.
- References: `references/official/axum/axum-docs.md`, `tower-docs.md`, `sqlx-docs.md`, `utoipa-docs.md`, `ecosystem-docs.md`가 날짜가 붙은 공식 사실을 담습니다.
- Assets: `assets/evals/axum-cases.jsonl`이 트리거와 동작 사례를 담습니다.
- 내장 스크립트 없음: `cargo check`, `cargo clippy`, `cargo test`, 실제 요청 하나가 검증 표면입니다.

</skill_architecture>

<loop_policy>

- 최적화 루프는 없습니다. 요청당 검토 또는 교정 한 번입니다.
- 교정 후 3단계 게이트와 건드린 검사에 대해 최대 두 번의 검증-수리 반복이 실행됩니다. 변경은 건드린 범위 안에 있고 게이트를 통과할 때만 유지됩니다.
- 루프는 첫 통과 체크리스트 또는 보고된 차단 지점에서 끝나며, 초록 결과를 얻으려고 건드린 범위를 넓히지 않습니다.

</loop_policy>

<language_and_translation_default>

발견, 교정 요약, 검증 노트는 한국어로 씁니다. 식별자, 경로, crate 이름, 타입 이름, `official`과 `hypercore-only` 라벨은 원래 형태로 두어 보고가 규칙 파일과 1:1로 대응하게 합니다. `stacks/axum/core.ko.md`는 이 파일을 절 단위로 미러링하며, 여기서 규칙을 바꾸면 같은 편집에서 저쪽도 바꿉니다.

</language_and_translation_default>

<reference_routing>

수정 전에 `stacks/axum/architecture-rules.md`를 읽습니다. 그다음 건드린 표면을 소유한 파일 하나를 엽니다:

| Touched surface | File |
|---|---|
| 프로젝트 프로필, crate/모듈 소유, 의존 방향, 워크스페이스, 구조 마이그레이션 | `rules/axum/project-structure.md` |
| Router 조립, nest와 merge, 경로 문법, fallback, 버전 접두사 | `rules/axum/routes.md` |
| handler 시그니처, extractor 순서, `State`, `Path`/`Query`/`Json`, typed rejection | `rules/axum/handlers.md` |
| tower layer, `from_fn`, `route_layer`, layer 순서, tower-http 스택, `HandleErrorLayer` | `rules/axum/middleware.md` |
| serde와 `validator` 경계, 검증 extractor, 오류 매핑 | `rules/axum/validation.md` |
| SQLx 풀, 쿼리, 오프라인 모드, 마이그레이션, 트랜잭션, repository 경계 | `rules/axum/database.md` |
| utoipa와 utoipa-axum 정의, 스펙 엔드포인트, Swagger UI 게이팅, 계약 드리프트 | `rules/axum/openapi.md` |
| `AppError`, `IntoResponse`, 오류 봉투, 404/405 동작 | `rules/axum/errors.md` |
| `tower::ServiceExt::oneshot`, `axum-test`, 통합·DB 테스트 | `rules/axum/testing.md` |
| `main.rs` 부트스트랩, 설정, `axum::serve`, graceful shutdown, tracing | `rules/axum/platform.md` |
| Rust 이름 규칙, 모듈, import, clippy와 스타일 | `rules/axum/conventions.md` |
| 지연, 처리량, 릴리스 프로필, SQLx 풀 크기, 압축, 타임아웃 layer, 메모리, 바이너리 크기 | `rules/axum/performance.md` |
| lint, format, clippy, rustfmt, toolchain 고정, workspace lint, CI 검사 순서 | `rules/setup/rust.md` |
| 규칙 뒤의 공식 axum 동작 또는 공식 기본값 요청 | `references/official/axum/axum-docs.md` |
| `rules/axum/middleware.md` 주장 뒤의 tower와 tower-http 동작 | `references/official/axum/tower-docs.md` |
| `rules/axum/database.md` 주장 뒤의 SQLx 동작 | `references/official/axum/sqlx-docs.md` |
| `rules/axum/openapi.md` 주장 뒤의 utoipa 동작 | `references/official/axum/utoipa-docs.md` |
| 검증, 테스트, 오류, 플랫폼 주장 뒤의 `validator`, `axum-test`, `thiserror`, `tracing` 동작 | `references/official/axum/ecosystem-docs.md` |

사용자가 공식 기본값을 요청하면 공식 참조에서 시작하고, Hypercore 전용 규칙을 선택적 오버레이로 취급하며, 어느 발견이 어느 쪽인지 라벨로 표시합니다.

</reference_routing>

<support_file_read_order>

1. 규칙 분류와 게이트 요약을 위해 `stacks/axum/architecture-rules.md`.
2. `reference_routing` 순서로 건드린 표면의 주제 파일.
3. 파일 이름이나 스타일을 수정하기 전에 `rules/axum/conventions.md`.
4. 공식 동작이나 공식 기본값 요청이면 `references/official/axum/axum-docs.md`.
5. 주장을 뒷받침하는 참조: layer는 `tower-docs.md`, 데이터베이스 동작은 `sqlx-docs.md`, API 계약은 `utoipa-docs.md`, 검증·테스트·오류·로깅 crate는 `ecosystem-docs.md`.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | 대상이 Axum 서버임을 증명 | 범위 결정 |
| 2 | 건드린 표면의 규칙 파일을 읽음 | 최소 근거 집합 |
| 3 | 계획한 변경을 핵심 게이트에 대조 | 파일 경로가 붙은 발견 |
| 3.5 | 건드린 범위 안에서 저위험 자동 교정 적용 | 수정 또는 백로그 항목 |
| 4 | 아래 파일 순서로 구현하고 검증 | 변경 파일과 근거 |

1단계 — 프로젝트 검증: `rules/axum/project-structure.ko.md`의 탐색 명령(Axum 표지, 영속성 표지, `전체 수정` 모드의 crate 전체 목록화)과 `rules/stack-detection.md`의 라우팅 확인을 실행합니다. Axum 표지가 없으면 Axum 규칙을 강제하지 말고 일반 구현·검토 경로로 돌려보냅니다.

3단계 — 핵심 게이트. 브라운필드 규칙: 건드리지 않은 기존 스타일 드리프트는 백로그가 될 수 있지만, 안전, 타입, 검증, 영속성, OpenAPI, 런타임 경계 문제는 건드린 작업에서 즉시 차단합니다. `전체 수정` 모드에서는 감지한 Axum crate 전체가 건드린 범위입니다. 교정 세부는 연결된 지원 파일의 체크리스트를 사용하고, 이 코어는 그것을 다시 서술하지 않습니다.

- `Router`를 반환하는 조립 루트가 하나이고 `main.rs`는 부트스트랩만 합니다. 상태는 `with_state`로 한 번 주입합니다.
- handler가 SQL, 풀 생성, 마이그레이션 로직을 들고 있지 않고 영속성은 repository 뒤에 있습니다.
- body를 소비하는 extractor가 마지막이고, 공유 상태는 body 앞에서 추출하며, 사용자 입력을 `unwrap()`하지 않습니다.
- layer는 명시적 순서로 조립되고, 실패 가능 layer에는 `HandleErrorLayer` 또는 동등한 처리가 있으며, 매칭되지 않은 경로에서 실행되면 안 되는 layer에는 `route_layer`를 씁니다.
- 요청 DTO는 serde와, 타입 모양을 넘는 규칙에는 `validator` 경계를 쓰고, 검증 실패는 하나의 안정된 오류 봉투로 매핑합니다.
- SQLx 쿼리, 트랜잭션, 마이그레이션은 데이터베이스/service 경계 뒤에 있고, 마이그레이션은 커밋되며 요청 handler가 적용하지 않습니다.
- 공개 문서 라우트는 런타임 스키마, 응답 타입, utoipa 스펙이 일치하고, Swagger UI 노출은 환경 정책과 맞습니다.
- 하나의 `AppError`가 `IntoResponse`를 구현하고, 내부 오류 텍스트, SQL, 비밀은 응답 본문에 도달하지 않습니다.
- 부트스트랩 코드가 `axum::serve`, 시그널 처리, tracing 초기화, 설정 검증을 소유하고, 라우트 모듈은 포트를 바인딩하지 않습니다.
- Rust 모듈과 파일은 `snake_case`이고, `cargo clippy`에 건드린 코드에서 새 경고가 없습니다.

3.5단계 — 자동 교정. 문제가 국소적이고 되돌릴 수 있으며 저위험이면 직접 고칩니다:

- body를 소비하는 extractor가 마지막이 되도록 인자 순서를 바꿉니다.
- handler의 직접 `sqlx` 쿼리를 해당 도메인의 기존 repository나 service로 옮깁니다.
- handler 안의 요청별 `pool.clone()` 또는 `PgPool::connect`를 공유 `AppState` 풀로 바꿉니다.
- 건드린 쿼리에 빠진 repository 래퍼나, 건드린 조정 로직에 빠진 service 호출을 추가합니다.
- 무관한 handler에 전체 `AppState`를 넘기는 대신 `FromRef` 하위 상태를 추가합니다.
- 직접 만든 `sqlx::Error` 응답을 기존 `AppError` 변환으로 바꿉니다.
- 저장소가 이미 스펙을 발행하면 건드린 공개 라우트에 빠진 `utoipa` 애노테이션을 추가합니다.
- 라우트 모듈의 `axum::serve`나 리스너 바인딩을 바이너리 진입점으로 옮깁니다.
- 건드린 `camelCase`나 `kebab-case` Rust 모듈을 `snake_case`로 바꾸고 같은 변경에서 `mod` 선언과 import를 갱신합니다.

명시적 근거 없이 광범위하거나 깨질 수 있는 마이그레이션을 자동 적용하지 않습니다: 앱 전체 layer 재작성, ORM이나 드라이버 교체, 스키마 테이블·컬럼·인덱스 이름 변경, 프로덕션 마이그레이션 적용·삭제, 테스트 없는 트랜잭션 경계 재작성, 클라이언트를 깨는 RPC·응답 모양 변경, 런타임이나 비동기 런타임 교체, crate 전체에 새 아키텍처 계층 추가.

4단계 — 구현 순서:

1. 현재 구조와 규칙 위반을 검증합니다. `전체 수정` 모드에서는 수정 전에 감지한 Axum crate 전체를 목록화합니다.
2. 이후 import와 테스트가 안정된 경로에 의존하므로 안전할 때 모듈·파일 이름을 먼저 고칩니다.
3. Router 조립, 상태 연결, 라우팅 순서를 고칩니다.
4. handler와 extractor 타입, 그다음 검증 경계를 고칩니다.
5. 건드린 영속성 동작의 데이터베이스, repository, 트랜잭션, 마이그레이션 경계를 고칩니다.
6. 미들웨어 조립과 오류 변환을 고칩니다.
7. 건드린 공개 라우트의 OpenAPI 메타데이터와 응답 계약을 고칩니다.
8. 경계에서 부트스트랩, 설정, 관측성을 고칩니다.
9. 검증을 실행합니다.

</workflow>

<required>

- Axum 규칙을 적용하기 전에 Axum 서버임을 증명하고, 요청이 Axum 범위를 벗어나면 이유를 밝힙니다.
- `main.rs`와 분리된 `Router` 조립 함수 하나, 한 번만 적용된 상태, 명시된 라우팅 순서.
- 저장소의 기존 계층 유지: handler가 SQLx 풀, 스키마, 마이그레이션 실행기로 직접 가지 않습니다.
- 올바른 extractor 순서, typed state, 비자명한 입력에 대한 요청 검증.
- 각 발견을 `official` 또는 `hypercore-only`로 표시한 보고.
- `cargo check`, `cargo clippy`, `cargo test`, 변경 표면에 도달 가능한 경우 실제 요청 하나의 검증 근거.

</required>

<forbidden>

- 요청이 비슷하게 들린다는 이유로 Actix Web, Rocket, Poem, warp 등 다른 프레임워크에 Axum 규칙을 강제하는 것.
- 명시적 권한 없이 프로덕션 마이그레이션을 이름 변경·적용하거나 스키마 테이블·컬럼·인덱스 이름을 바꾸는 것.
- 아키텍처 검토 안에서 비동기 런타임, 데이터베이스 드라이버, ORM, TLS 백엔드를 교체하는 것.
- 기록된 결정 없이 응답 모양을 바꿔 기존 클라이언트를 깨는 것.
- Hypercore 규약을 공식 axum 동작으로 제시하는 것.
- 건드리지 않은 기존 코드가 같은 패턴을 보인다는 이유로 차단 게이트를 침묵시키는 것.
- 실행하지 않은 검사를 실행했다고 하거나, 출력 없이 게이트를 통과로 보고하는 것.

</forbidden>

<validation>

- [ ] 읽은 manifest나 소스 파일로 Axum 프로젝트 감지를 확인했다.
- [ ] 건드린 표면의 규칙 파일을 읽었고, 요청 시 공식 기본값 모드를 적용했다.
- [ ] 건드린 Rust 모듈과 파일이 `snake_case`이고, `전체 수정` 모드에서는 crate 전체를 스캔했다.
- [ ] 단일 `Router` 조립 함수가 있고 `main.rs`는 부트스트랩만 한다.
- [ ] 상태가 `with_state`로 한 번 주입되고, 정당한 곳에서 하위 상태가 `FromRef`를 쓴다.
- [ ] extractor 순서가 유효하고 body를 소비하는 extractor가 마지막이다.
- [ ] 비자명한 요청 DTO가 service 로직 전에 검증된다.
- [ ] 건드린 handler가 SQLx 쿼리 매크로를 import하거나 풀을 직접 만들지 않는다.
- [ ] SQLx 쿼리 모드(컴파일 타임 검사 또는 오프라인)와 마이그레이션 출처가 저장소 설정과 일치한다.
- [ ] 영향을 받는 다단계 쓰기에 트랜잭션이 명시되어 있다.
- [ ] 건드린 문서 라우트의 OpenAPI 정의와 Swagger UI 노출이 갱신되고 환경에 맞다.
- [ ] 하나의 `AppError`/`IntoResponse` 정책이 있고 내부 정보를 노출하지 않는다.
- [ ] API DTO, OpenAPI 스키마, 응답 타입이 원시 데이터베이스 행이나 내부 필드를 노출하지 않는다.
- [ ] 부트스트랩 코드가 serve, shutdown, tracing, 설정 검증을 소유한다.
- [ ] `cargo check`, `cargo clippy`, 건드린 테스트를 실행했고, 도달 가능한 경우 실제 요청 하나를 수행했다.
- [ ] 최종 발견이 공식 axum 규칙과 Hypercore 규약을 구분한다.

</validation>

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Axum 0.8 경로 문법, extractor 순서, `State`, `Router` 상태 제네릭, layer 순서, `route_layer`, 미들웨어 동작 | [axum docs](https://docs.rs/axum/latest/axum/), [Router](https://docs.rs/axum/latest/axum/struct.Router.html), [extract](https://docs.rs/axum/latest/axum/extract/index.html), [middleware](https://docs.rs/axum/latest/axum/middleware/index.html), [State](https://docs.rs/axum/latest/axum/extract/struct.State.html) |
| Axum 0.8.0 호환 깨는 변경과 0.8.9 MSRV 1.80 | [axum CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| 0.8 계열에서 `FromRequestParts`에 `#[async_trait]`이 더 이상 필요 없음 | [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md) |
| `validator`, `axum-test`, `tower::ServiceExt` 기능 | [validator](https://docs.rs/validator/latest/validator/), [axum-test](https://docs.rs/axum-test/latest/axum_test/), [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html) |
| SQLx 0.9 기능 이름, 쿼리 매크로, 오프라인 모드, 마이그레이션, 트랜잭션 | [sqlx README](https://github.com/launchbadge/sqlx/blob/main/README.md), [sqlx CHANGELOG](https://github.com/launchbadge/sqlx/blob/main/CHANGELOG.md), [SQLx docs](https://docs.rs/sqlx/latest/sqlx/) |
| utoipa 6, utoipa-axum 0.3, utoipa-swagger-ui 10 동작과 MSRV | [utoipa CHANGELOG](https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md), [utoipa-axum](https://docs.rs/utoipa-axum/latest/utoipa_axum/) |
| 트리거 우선 `description`, 이중 언어 패키지 모양, 1단계 참조 규칙 | `instructions/skill/SKILL_AUTHORING.md` |
| 이름과 설명이 바뀔 때 로드되는 머리를 안정적으로 유지 | `instructions/cache/CACHE.md` |

### Evidence grade

Axum, tower, SQLx, utoipa에 대한 진술은 각 프로젝트의 자체 문서와 체인지로그에서 날짜가 붙은 스냅숏으로 가져온 `VENDOR` 사실입니다. 계층과 이름 규칙은 이 저장소의 규약이며, 공식 crate 지침을 넘는 부분은 `hypercore-only`로 표시합니다.
