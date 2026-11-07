# 아키텍처 규칙 참조

> Axum hypercore 프로젝트의 전체 규칙 집합

참고: 아래 규칙 일부는 axum 기본값보다 엄격합니다. 이는 보편적인 프레임워크 요구가 아니라 hypercore 팀 규약입니다.

브라운필드 적용 규칙: 건드리지 않은 기존 코드는 스타일이나 hypercore 전용 문제라면 즉시 실패 대신 마이그레이션 작업으로 추적할 수 있습니다. 안전, 타입, 검증, 전송 경계 문제는 특히 건드린 코드에서 즉시 차단합니다.

---

## 금지

| 범주 | 금지 |
|----------|-----------|
| 컨트롤러 | 단순 handler 함수로 충분한데 컨트롤러식 거대 모듈이나 라우트당 trait 추상화를 도입하는 것 |
| 라우트 | 단일 조립 함수 없이 `Router::new()` 조각이 흩어지는 것 |
| 순서 | 구체 라우트보다 fallback을 먼저 등록하거나, matchit 명시도 확인 없이 등록 순서로 경로 우선순위를 기대하는 것 |
| 검증 | body를 도메인 타입으로 역직렬화한 뒤 검증 경계 없이 신뢰하는 것 |
| 데이터베이스 | handler에서 SQLx 쿼리 매크로, 풀, 마이그레이션 도우미를 직접 import하는 것 |
| 마이그레이션 | 명시적 정책 없이 요청 handler나 프로세스 시작에서 마이그레이션을 실행·생성하는 것 |
| 타입 | 요청에서 온 값에 `unwrap()`·`expect()`를 쓰거나, 타입 없는 `serde_json::Value`가 도메인 로직으로 넘어가는 것 |
| 오류 | `sqlx::Error`, 접속 문자열, 내부 식별자를 응답 본문으로 노출하는 것 |
| OpenAPI | 저장소가 스펙을 발행하는데 공개 라우트 변경에 맞는 utoipa 메타데이터를 갱신하지 않는 것 |
| 플랫폼 | 라우트 모듈에서 리스너를 바인딩하거나 비밀을 읽거나 tracing을 초기화하는 것 |
| 경로 | Rust 모듈·파일을 `camelCase`나 `kebab-case`로 짓는 것(`userProfile.rs`, `create-user.rs`) |
| Rust | axum 0.8 extractor에 `async_trait`을 붙이거나, 공개 handler 오류 타입으로 `Box<dyn Error>`를 쓰거나, 불변 조건 없이 `unsafe`를 쓰는 것 |
| Git | AI 표식, 이모지, 여러 줄 커밋 메시지 |

---

## 아키텍처 관심사 정합성

이 저장소의 서버 스택에는 같은 아키텍처 관심사가 적용됩니다. Axum에서는 아래처럼 소유하므로, 여러 스택이 있는 저장소도 스택별 즉흥 처리 대신 동등한 게이트를 받습니다.

| 관심사 | Axum 소유자 |
|---|---|
| 런타임 경계 / 부트스트랩 | tokio, 리스너, `axum::serve`, shutdown, tracing을 담은 `main.rs`(또는 `bin/*.rs`) |
| 조립 루트 | `fn app(state) -> Router` 또는 `build_router` 함수 하나 |
| 전송 표면 | `routes/*` handler 함수와 extractor |
| 유스케이스 | `services/*` 함수 또는 구조체 |
| 영속성·외부 클라이언트 | `repositories/*`, `clients/*`, `db/*` |
| 계약 | `openapi.rs`와 DTO의 `utoipa` derive |
| 오류 정책 | `IntoResponse`를 구현한 `AppError` 하나 |
| 테스트 | `tests/*` 통합 테스트, 모듈 옆 단위 테스트 |

스택 번역은 문법이 아니라 관심사를 유지합니다. Hono 미들웨어는 tower layer가 되고, Hono validator는 serde와 검증 extractor가 되며, Drizzle repository는 SQLx repository가 되고, `AppType`식 RPC 타입은 명시적 DTO와 OpenAPI 타입이 됩니다.

---

## 계층 아키텍처

```text
Bootstrap / Runtime Edge
  main.rs -> config, tracing, pool, state, serve, shutdown
       |
       v
Router Composition
  app.rs / lib.rs -> fn app(state: AppState) -> Router
       |
       v
Routes / Handlers / Extractors
  routes/<domain>.rs or routes/<domain>/mod.rs
       |
       v
Services / Use Cases
  services/<domain>.rs -> business decisions, transaction boundaries
       |
       v
Repositories / External Clients / Database Boundary
  repositories/<domain>.rs, clients/<provider>.rs
  db/pool.rs, migrations/
```

**데이터 흐름 규칙:**
- 전송 관심사는 handler, extractor, layer, 응답 모양에 남습니다.
- 도메인 로직은 service/유스케이스에 남습니다.
- 저장소·SDK 로직은 repository나 client에 남습니다.
- 풀 생성, SQLx 쿼리 매크로, 스키마 소유, 마이그레이션 실행은 데이터베이스 경계와 부트스트랩에 남습니다.
- handler는 `sqlx::query!`, `PgPool`, `sqlx::migrate!`, 테이블·모듈 내부를 직접 import하지 않습니다.
- 라우트 모듈은 기본적으로 컨트롤러 계층으로 자라지 않습니다.

---

## 프로젝트 구조와 확장성

crate나 모듈을 만들기 전, compact/service/workspace 프로필을 고르기 전, 소유 경계를 바꾸기 전, 수직 슬라이스를 옮기기 전, 워크스페이스를 설계하기 전에 [`rules/axum/project-structure.md`](../../rules/axum/project-structure.md)를 읽습니다.

핵심 불변 조건은 여기 남습니다:

- `Router`를 반환하는 조립 함수 하나와 상태를 적용하는 명백한 지점 하나를 유지합니다.
- 의존성은 부트스트랩에서 조립, 라우트, service, repository, 데이터베이스·외부 시스템으로 흐릅니다.
- 라우트는 전송 조정을 소유하고 SQL, 마이그레이션, provider SDK 세부, 프로세스 시작을 소유하지 않습니다.
- 하위 계층은 `axum` extractor나 응답 타입을 import하지 않습니다.
- 관찰 가능한 소유나 의존 압력에서만 구조를 키우고, 빈 계층을 미리 만들지 않습니다.
- 브라운필드 이동 중 공개 경로, layer 순서, 응답 모양, 마이그레이션 출처를 보존합니다.
- 생성 파일과 설정된 소스·쿼리·마이그레이션 루트를 도구가 소유한 위치에 둡니다.

---

## Handler 타입 규칙

### 선호하는 소형 모듈 패턴

```rust
pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/users", get(list_users).post(create_user))
}
```

### 선호하는 추출 handler 패턴

```rust
pub async fn list_users(State(state): State<AppState>) -> Result<Json<Vec<UserDto>>, AppError> {
    let users = state.users.list().await?;
    Ok(Json(users))
}
```

### 핵심 규칙

- handler는 평범한 `async fn` 값입니다. `Send + Sync + 'static`이어야 하고 `impl IntoResponse`를 반환합니다.
- extractor는 왼쪽에서 오른쪽으로 실행되고, body를 소비하는 extractor 하나가 마지막입니다.
- `State`와 `FromRef` 하위 상태는 body extractor 앞에 옵니다.
- panic하거나 handler마다 즉석 오류 응답을 만들지 말고 `Result<T, AppError>`를 반환합니다.
- 요청 파싱, 검증, service 조정을 읽기 쉽게 유지합니다. 50줄을 넘는 handler는 보통 빠진 service를 감추고 있습니다.

---

## 검증 규칙

- 전송 DTO에는 serde를 쓰고, 타입 모양을 넘는 규칙에는 `validator` derive나 동등한 명시적 검사를 씁니다.
- 도메인 로직이 payload를 소비하기 전에 검증합니다. 도메인 타입은 검증되지 않은 입력으로 만들어질 수 없어야 합니다.
- 검증 오류 봉투를 하나로 유지합니다. 의미상 잘못된 입력에 `422 Unprocessable Entity`, 문법상 잘못된 입력에 `400 Bad Request`를 쓰는 것 모두 방어 가능하지만, API마다 정책 하나를 골라 문서화합니다.
- JSON body뿐 아니라 `Path`, `Query`, 헤더, multipart 입력도 검증합니다.
- 이 스킬에 맞추려고 검증 crate를 추가하거나 교체하지 않습니다.

## 데이터베이스 / SQLx 규칙

- 영속성을 handler 구현 세부가 아닌 별도 아키텍처 경계로 취급합니다.
- 비자명한 영속 동작에는 `routes -> services -> repositories -> pool`을 선호합니다.
- 부트스트랩에서 만든 공유 풀 하나를 `AppState`에 두고, 요청마다 연결하지 않습니다.
- 쿼리 모드를 일관되게 유지합니다. `DATABASE_URL` 또는 커밋된 `.sqlx` 오프라인 데이터를 쓰는 컴파일 타임 검사 `sqlx::query!`, 또는 명시적 행 매핑을 쓰는 런타임 검사 `sqlx::query`입니다. 조용히 섞지 않습니다.
- 마이그레이션은 설정된 디렉터리에 두고 적용된 마이그레이션을 편집하지 않습니다.
- 다단계 쓰기에는 명시적 트랜잭션을 쓰고 트랜잭션 핸들을 repository로 넘깁니다.
- SQLx, 마이그레이션, 트랜잭션, DTO, 비준수 검사의 세부는 `rules/axum/database.md`를 봅니다.

## OpenAPI / Swagger 규칙

- OpenAPI를 장식용 문서 페이지가 아니라 API 계약으로 취급합니다.
- 공개 DTO에 `utoipa` derive를, handler에 `#[utoipa::path]`를 쓰고, 저장소가 이미 쓰면 `utoipa-axum` `OpenApiRouter`로 조립합니다.
- 런타임 스키마와 문서 스키마를 일치시키고, 가능하면 DTO 소스를 하나로 씁니다.
- `/api-docs/openapi.json` 같은 정본 스펙 엔드포인트 하나를 발행합니다.
- Swagger UI는 `/swagger-ui` 같은 별도 라우트로 제공하고 환경 결정에 따라 보호합니다.
- 문서화한 모든 작업은 안정된 `operation_id`, 태그, 요청 스키마, 성공 응답, 예상 오류 응답, 유용한 예시를 가져야 합니다.
- 공유 스키마, 파라미터, 응답, 예시, 보안 스킴은 재사용 가능한 컴포넌트 아래에 둡니다.
- 발행하거나 코드 생성에 쓰기 전에 생성 스펙을 검증하거나 lint합니다.

---

## 미들웨어 규칙

- axum에는 자체 미들웨어 시스템이 없고 layer가 tower service입니다. 추가하기 전에 순서를 이해합니다.
- `.layer()` 호출은 앞서 추가한 모든 라우트를 감싸므로 마지막 호출이 가장 바깥 layer이고 요청이 먼저 만납니다.
- `ServiceBuilder`는 위에서 아래로 조립합니다. builder의 첫 `.layer()`가 요청을 먼저 봅니다.
- `route_layer`는 라우트가 매칭될 때만 실행되고, `layer`는 매칭되지 않은 경로에도 실행됩니다. 404를 관찰하면 안 되는 layer에는 `route_layer`를 씁니다.
- 공유 인증, 로깅, 요청 ID, CORS, 압축, 타임아웃은 layer에 둡니다.
- 실패 가능 layer는 그 위에 `HandleErrorLayer`가 필요합니다. axum은 실패 불가 service를 기대합니다.
- `from_fn` 미들웨어에서 상태를 쓰려면 `from_fn_with_state`를 씁니다.
- 요청 범위 데이터는 요청 extension이나 typed extractor에 두고, 가변 전역에 두지 않습니다.

---

## 오류 처리 규칙

- `AppError` enum 하나를 정의하고 도메인·인프라 오류를 그것으로 번역하며 `IntoResponse`를 한 번 구현합니다.
- 공개 본문을 안정적으로 유지합니다. 기계 코드, 사람용 메시지, 선택적 필드 오류입니다. SQL 텍스트, 접속 문자열, 백트레이스를 넣지 않습니다.
- `sqlx::Error::RowNotFound`를 의도적으로 매핑합니다. 없는 행은 보통 `500`이 아니라 `404`입니다.
- 명시적 `fallback`과, 계약상 필요하면 `method_not_allowed_fallback`을 추가합니다.
- `tracing::error!`로 내부 원인을 기록하고 정제된 응답을 반환합니다.
- 요청에서 온 값을 `unwrap()`하지 않습니다. handler 안의 panic은 연결을 끊고 원인을 감춥니다.

---

## 테스트 규칙

- `tower::ServiceExt::oneshot`으로 라우터를 직접 테스트합니다. 포트도, 경쟁도, sleep도 없이 layer와 extractor까지 포함합니다.
- 요청 builder, 쿠키, multipart 도우미가 유용하면 `axum-test` `TestServer`를 씁니다.
- repository 테스트에는 실제 데이터베이스를 쓰고, 가능하면 끝에 롤백하는 트랜잭션이나 테스트별 격리 스키마를 씁니다. 테스트를 프로덕션 데이터로 돌리지 않습니다.
- 변경한 상태 코드, 검증 실패, 오류 봉투를 다룹니다.
- OpenAPI 발행이 저장소 계약의 일부라면 문서화한 공개 라우트 계열마다 통합 테스트 하나를 유지합니다.

---

## 플랫폼 설정 규칙

- 리스너 바인딩, 설정 로딩, tracing 설정, 풀 생성, graceful shutdown은 `main.rs`나 `bin/*.rs`에 둡니다.
- `.with_state(state)`로 상태를 한 번 주입하고 조립 함수에서 `Router<()>`를 반환합니다.
- `axum::serve(listener, app).with_graceful_shutdown(...)`을 쓰고 HTTP 루프를 직접 만들지 않습니다.
- 설정을 명시적 타입으로 만들고 시작 시 검증합니다. handler에 `std::env::var`를 흩뿌리지 않습니다.
- health와 readiness 엔드포인트는 가볍게 유지하고 선택적 의존성과 분리합니다.
- 아키텍처 검토 안에서 비동기 런타임, TLS 백엔드, 배포 manifest를 바꾸지 않습니다.

---

## Sources

> Checked 2026-11-05. 이 파일은 이 패키지 자체 참조 밖의 외부 출처를 근거로 삼지 않았습니다. 공식 axum, tower, SQLx, utoipa 동작은 [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md), [`references/official/axum/tower-docs.md`](../../references/official/axum/tower-docs.md), [`references/official/axum/sqlx-docs.md`](../../references/official/axum/sqlx-docs.md), [`references/official/axum/utoipa-docs.md`](../../references/official/axum/utoipa-docs.md)에 위임했고 2026-11-05에 확인했습니다.
