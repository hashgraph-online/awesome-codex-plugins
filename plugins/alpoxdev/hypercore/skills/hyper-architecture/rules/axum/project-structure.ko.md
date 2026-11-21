# 프로젝트 구조와 소유권

> crate나 모듈 설계, 조립 소유권, 기능 성장, 워크스페이스, 구조 리팩터에 이 규칙을 읽습니다. 공식 axum 사실은 [`../../references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md)에 요약되어 있고, 아래 배치는 표시가 없으면 Hypercore 규약입니다.

## 탐색 명령

프로필을 고르거나, 구조 변경을 적용하거나, 건드리지 않은 crate를 보고하기 전에 실행합니다. 대상 라우팅 판정 자체는 `rules/stack-detection.md`가 소유하고, 이 블록은 구조 판단에 필요한 사실만 모읍니다.

```bash
# is this an Axum server at all
rg -n '^axum\s*=|axum\s*=\s*\{|axum-extra' Cargo.toml */Cargo.toml
rg -n "use axum::|axum::Router|axum::serve|#\[derive\(.*FromRef" src crates
rg -n "tokio::main|Router::new\(\)|\.with_state\(" src crates
```

```bash
# persistence indicators, when a database is in scope
rg -n 'sqlx|sea-orm|diesel|tokio-postgres' Cargo.toml */Cargo.toml
rg -n "PgPool|MySqlPool|SqlitePool|query!|query_as!|\.begin\(\)|sqlx::migrate" src crates
ls migrations sqlx.toml .sqlx 2>/dev/null
```

```bash
# full-crate inventory for 전체 수정 mode
rg --files -g '*.rs' src crates 2>/dev/null
rg -n "Router::new\(\)|\.route\(|\.nest\(|\.merge\(|\.layer\(|\.route_layer\(|from_fn|with_state|FromRef|Json<|Query<|Path<|validate\(|sqlx::|AppError|IntoResponse|utoipa" src crates
```

첫 블록이 아무것도 찾지 못하면 그 crate는 Axum 서버가 아니므로 Axum 규칙을 적용하지 않습니다.

## 1. 저장소 근거로 프로필 고르기

crate 배치, 바이너리, `Cargo.toml` 기능과 의존성, 모듈 트리, 조립 함수, 상태 타입, 풀 생성, 마이그레이션 디렉터리, OpenAPI 정의, 테스트, 현재 `use` 그래프를 확인합니다. 건드린 경계가 안전하지 않거나 요청한 변경을 막지 않으면 일관된 브라운필드 배치를 유지합니다.

모든 의존성에 명확한 소유자 하나를 주는 가장 작은 프로필을 씁니다:

| 프로필 | 사용 시점 | 지금 추가 |
|---|---|---|
| Compact | 라우트가 적고 재사용 가능한 도메인·영속 로직이 거의 없는 작은 서비스 | `main.rs`, `app.rs`, 평면 라우트 모듈, `state.rs`, `error.rs` |
| Service | 도메인이 여럿이고 기여자, 검증, 영속 워크플로, 생성 API 문서, 백그라운드 작업이 있음 | 도메인 라우트 모듈, service/repository 경계, `db/`, `openapi.rs`, 공유 미들웨어 |
| Workspace | 배포물이 여럿이거나 다른 crate가 소비하는 라이브러리 | API crate 안의 Service 구조와, 정당할 때 도메인·계약 crate |

모든 디렉터리를 미리 만들지 않습니다. 폴더나 crate는 뚜렷한 소유자, 의존 규칙, 빌드 계약이 있을 때만 승격합니다. 빈 계층과 한 함수짜리 통과 trait 추상화는 확장성이 아닙니다.

## 2. 소유권과 의존 방향

```text
bootstrap -> router composition -> route/handler -> service/use case -> repository/client -> database/external system
```

| 관심사 | 기본 소유자 | 소유하면 안 되는 것 |
|---|---|---|
| 런타임 시작, 리스너, 시그널, tracing 초기화 | `main.rs`, `bin/*.rs` | 도메인 규칙이나 영속 정책 |
| 루트 layer, fallback, 버전 접두사, 라우트 마운트 | `app.rs` 또는 `lib.rs` 조립 함수 | 기능 비즈니스 로직 |
| 경로·메서드, 추출, 인증 게이트, 응답 모양 | `routes/<domain>` | SQL, 풀 생성, 마이그레이션 실행 |
| 비즈니스 결정, 다단계 트랜잭션 | `services/<domain>` | `axum` extractor, `Json`, `Response`, 헤더 |
| 쿼리와 외부 SDK 적응 | `repositories/<domain>`, `clients/<provider>` | HTTP 응답 모양이나 라우트 등록 |
| 풀 생명주기, 마이그레이션, SQL 스키마 | `db/`, `migrations/` | 요청 라우팅 |
| 공유 DTO, utoipa 스키마, 스펙 조립 | `openapi.rs`, `dto/` | 라우트별로 중복된 스키마 사본 |

의존성은 아래로 향합니다. 하위 계층은 `axum` 전송 타입을 import하지 않습니다. 기능 라우트 모듈은 다른 기능의 라우트 모듈을 import하지 않고, 기능 간 워크플로는 service나 의도적으로 공유한 계약 타입에서 만납니다.

## 3. Compact 배치

```text
src/
├── main.rs             # tokio main, config, tracing, pool, serve, shutdown
├── app.rs              # fn app(state: AppState) -> Router
├── state.rs            # #[derive(Clone)] AppState
├── error.rs            # AppError + IntoResponse
└── routes/
    ├── mod.rs
    ├── health.rs
    └── users.rs
```

Compact 라우트는 작은 순수 도우미를 직접 호출할 수 있습니다. 비즈니스 결정, 재사용, 영속성, 트랜잭션, 외부 SDK 동작이 경계를 정당화할 때만 service나 repository를 추가합니다.

## 4. Service 배치

```text
src/
├── main.rs
├── app.rs              # 유일한 조립 함수
├── config.rs           # 타입이 있고 검증된 설정
├── state.rs            # AppState: config, pool, clients
├── error.rs
├── telemetry.rs        # tracing subscriber 설정
├── middleware/
│   ├── mod.rs
│   ├── auth.rs
│   └── request_id.rs
├── routes/
│   ├── mod.rs          # 마운트 테이블만
│   ├── health.rs
│   └── users/
│       ├── mod.rs      # routes() -> Router<AppState>
│       ├── handlers.rs
│       ├── dto.rs
│       └── tests.rs
├── services/
│   └── users.rs
├── repositories/
│   └── users.rs
├── clients/
│   └── mail.rs
├── db/
│   └── pool.rs
└── openapi.rs

migrations/
└── 20260101000000_create_users.sql
```

트리는 예시이며, 설정된 바이너리 이름, 모듈 루트, 쿼리 메타데이터(`.sqlx/`), 마이그레이션 디렉터리가 우선합니다.

## 5. 기능 성장 임계값

| 압력 | 구조적 대응 |
|---|---|
| 아주 작은 운영 엔드포인트 하나 | 라우트 모듈 하나 유지 |
| 검증이나 handler가 여럿 생김 | `routes/<domain>/`로 승격하고 DTO와 handler를 함께 둠 |
| 비즈니스 동작이 재사용되거나 독립 테스트 가능 | 기존 저장소 패턴에 따라 `services/<domain>` 추가 |
| 영속성·provider 호출이 생김 | repository/client 경계 추가. handler는 풀, 쿼리 매크로, provider SDK를 import하지 않음 |
| 두 도메인이 전송 비의존 타입을 재사용 | 그 타입을 `dto/`나 `domain/` 같은 목적 이름 모듈로 승격. 일반 `utils/` 쓰레기장을 만들지 않음 |
| 여러 도메인이 layer나 오류 매핑을 재사용 | 재사용되는 원시 요소만 `middleware/`나 `error.rs`로 승격 |
| 두 번째 crate가 계약을 소비 | 워크스페이스 crate 검토. 내부 repository 모듈을 crate 경계 너머로 노출하지 않음 |

파일 개수만으로 나누지 않습니다. 응집된 기능은 함께 둘 수 있고, 전송·비즈니스·영속 소유가 섞인 큰 파일은 한 번만 쓰여도 분리해야 합니다.

## 6. 조립과 타입 표면

명백한 조립 경로 하나를 유지합니다:

```rust
pub fn app(state: AppState) -> Router {
    Router::new()
        .merge(routes::health::routes())
        .nest("/api/v1", api_routes())
        .layer(tower_http::trace::TraceLayer::new_for_http())
        .fallback(handlers::not_found)
        .with_state(state)
}
```

- `/api`와 버전 접두사는 모든 기능 모듈 안이 아니라 조립 경계에 둡니다.
- 루트 layer는 fallback 앞에서 한 번 등록합니다.
- 테스트가 포트를 바인딩하지 않고 `app(test_state)`를 호출할 수 있을 만큼 `main.rs`를 얇게 유지합니다.
- 조립 함수는 `with_state` 후 `Router<()>`를 반환하고, 기능 모듈은 `Router<AppState>`를 반환합니다.
- 라우터에서 OpenAPI 정의를 생성하면 드리프트를 막기 위해 같은 라우트 정의에서 조립합니다.

## 7. 워크스페이스 배치

```text
crates/
├── api/                # Router를 노출하는 binary 또는 lib; 런타임과 구현 소유
├── domain/             # 순수 타입과 규칙; axum, sqlx 없음
└── persistence/        # 독립 빌드될 때 SQLx repository와 마이그레이션
```

crate 간 `axum`, `tokio`, `sqlx` 메이저 버전을 맞추고, 저장소가 이미 쓰면 워크스페이스 의존성 상속을 씁니다. 소비되는 라이브러리 crate는 비밀, 풀 내부, 서버 전용 구현 모듈을 노출하지 않습니다.

## 8. 브라운필드 마이그레이션

1. 실제 바이너리, 조립 함수, 상태 연결, 모듈 트리, 마이그레이션, 생성 메타데이터를 매핑합니다.
2. 파일을 옮기기 전에 소유 위반과 순환을 찾습니다.
3. 공개 경로, layer 순서, 오류 동작, 응답 모양, 마이그레이션 출처를 보존합니다.
4. 수직 슬라이스 하나씩 옮기고 `mod` 선언과 import를 원자적으로 갱신합니다.
5. 슬라이스마다 라우트·repository 테스트를 실행하고, 동작과 게이트를 통과할 때만 유지합니다.
6. 광범위한 이동이 요청을 넘으면 건드리지 않은 Hypercore 전용 드리프트를 백로그로 기록합니다. 건드린 코드의 안전, 검증, 타입, 영속성, 런타임 경계 위반은 여전히 차단합니다.

이것은 제한된 마이그레이션 루프입니다. 피드백은 집중 테스트와 import 경계 검사, 가드는 변경되지 않은 공개 동작과 계약, 최대 반복은 계획한 슬라이스 수이며, 가드를 실패한 슬라이스는 다음으로 넘어가기 전에 버리거나 되돌립니다.

## 9. 구조 검증

- 조립 함수 하나와 상태를 적용하는 지점 하나를 확인합니다.
- 모든 라우트에 모호하지 않은 소유자가 있고 fallback이 마지막인지 확인합니다.
- handler에서 `sqlx::`, `PgPool`, `MySqlPool`, `SqlitePool`, `migrate!`를 검색합니다.
- service와 repository에서 `axum::` extractor나 응답 타입을 검색합니다.
- 모듈 선언, `Cargo.toml` 기능 플래그, 마이그레이션 경로를 설정과 대조합니다.
- 옮긴 모듈에 `cargo check`와 집중 라우트·repository 테스트를 실행합니다.
- OpenAPI가 있으면 생성 문서에 대표 경로와 오류 모양이 여전히 있는지 확인합니다.
- 테스트하지 않은 바이너리, 데이터베이스, 마이그레이션, 생성 산출물을 명시합니다. 파일 배치만으로 성공을 추론하지 않습니다.

## Sources

> Checked 2026-11-05. 이 파일은 이 패키지 자체 참조 밖의 외부 출처를 근거로 삼지 않았습니다. 공식 axum 동작은 [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md)에 위임했고 2026-11-05에 확인했습니다.
