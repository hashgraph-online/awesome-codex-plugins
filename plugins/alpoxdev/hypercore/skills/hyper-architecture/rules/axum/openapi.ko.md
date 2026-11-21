# OpenAPI와 Swagger

> 생성 문서를 타입이 있는 계약 경계로 취급합니다

---
## 안정 패키지 기준선

2026-11-05에 확인한 대로 `utoipa`는 6.0.0, `utoipa-axum`은 0.3.0, `utoipa-swagger-ui`는 10.0.2이고 utoipa crate는 Rust 1.88을 요구합니다. utoipa 6은 `Version32`를 통해 OpenAPI 3.2 지원을 추가합니다. 렌더링된 문서는 기본 출력 버전에 대해 내부적으로 일관되지 않습니다. 기능 목록은 3.1이라고 하고 `openapi` 모듈은 3.2를 설명하기 때문입니다. 따라서 버전을 가정하지 말고 `OpenApi` builder에서 대상 버전을 명시합니다.

- DTO의 `utoipa` derive와 handler의 `#[utoipa::path]`를 선호하고, 저장소가 이미 쓰면 `utoipa-axum` `OpenApiRouter`로 조립합니다.
- `OpenApiRouter::routes(routes!(handler))`는 handler의 경로 메타데이터를 모으고 axum 메서드 라우터를 등록합니다. `split_for_parts()`는 `(Router, OpenApi)`를 반환합니다.
- `#[utoipa::path]`가 붙고 `routes!`로 수집된 handler만 생성 문서에 나옵니다. 옆에서 병합한 평범한 `Router`는 라우트를 기여하지만 스펙은 기여하지 않습니다.
- `routes!`는 같은 경로에 메서드를 중복 등록하거나 CONNECT handler를 만나면 패닉을 냅니다. 경로마다 한 번만 조립합니다.
- 스펙은 `/api-docs/openapi.json` 같은 하나의 표준 엔드포인트에서 제공하고, Swagger UI를 `.merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", ApiDoc::openapi()))`로 붙입니다.
- 스펙 노출과 UI 노출은 환경별로 따로 게이트합니다. UI를 숨겼다고 공개 JSON 스펙이 비공개가 되지 않습니다.
- 배포하거나 코드 생성에 쓰기 전에 생성 문서를 검증하거나 린트하고, 커밋할 때는 diff를 확인합니다.
- 데이터베이스 행이 자동으로 공개 스키마가 되지 않습니다. 게시 전에 행을 DTO로 매핑합니다.

## 핵심 규칙

Axum API가 OpenAPI를 게시하면 라우트 변경은 같은 변경에서 계약을 갱신합니다. 문서는 런타임이 실제로 지원하는 요청, 응답, 상태 코드, 보안, 예시를 그대로 설명해야 합니다.

## 승인된 생성 경로

| 저장소 형태 | 선호 경로 |
|---|---|
| derive 우선, axum 네이티브 | `utoipa` derive와 `#[utoipa::path]`, 수동 또는 `OpenApiRouter`로 조립 |
| 라우터 수집 | `utoipa-axum::OpenApiRouter` + `routes!` + `split_for_parts()` |
| 계약 crate | `OpenApi` builder와 공유 스키마를 소유하는 전용 `openapi` 또는 `contract` 모듈·crate |
| UI만 | 표준 스펙 엔드포인트에 병합하는 `utoipa-swagger-ui` |

사용자가 그 마이그레이션을 명시적으로 요청하지 않는 한 앱 전체의 generator를 바꾸지 않습니다.

## 폴더 구조

```text
src/
├── app.rs
├── openapi.rs          # ApiDoc, 공유 컴포넌트, 보안 스킴
├── dto/
│   ├── mod.rs
│   └── user.rs         # ToSchema / IntoParams derive
└── routes/
    └── users/
        ├── mod.rs
        └── handlers.rs # 공개 handler마다 #[utoipa::path]
```

- 공유 컴포넌트, 보안 스킴, 예시, 오류 봉투를 기능 둘 이상이 재사용하면 `openapi.rs`에 둡니다.
- operation 메타데이터는 그것이 문서화하는 handler에 둡니다.
- 표준 문서는 조각을 손으로 복사하지 않고 앱 경계에서 조립합니다.
- `/api-docs/openapi.json` 같은 안정적인 스펙 경로를 씁니다.
- Swagger UI는 `/swagger-ui`나 관리자 라우트 같은 별도 경로에서 제공합니다.

## Operation 메타데이터 체크리스트

문서화하는 모든 operation은 다음을 정의해야 합니다.

- 안정적인 `operation_id`
- 일관된 `tag`
- 경로 매개변수, 쿼리 매개변수, 헤더, 요청 본문 스키마
- 상태별 스키마를 갖춘 성공 응답
- 해당할 때 400, 401, 403, 404, 409, 422, 500 같은 예상 오류 응답
- 재사용 가능한 `securitySchemes`를 통한 인증 요구 사항
- 스키마와 일치하는 요청·응답 예시
- 엔드포인트가 공개되면 안 될 때의 폐기 또는 숨김 메타데이터

## 계약 드리프트 규칙

| 드리프트 | 규칙 |
|------|------|
| handler가 문서에 없는 입력을 받음 | 차단. 매개변수·본문 스키마를 추가하거나 라우트 문서화를 중단합니다. |
| 문서가 handler가 절대 반환하지 않는 상태를 나열함 | 경고. 코드 생성 전에 handler나 문서를 고칩니다. |
| handler가 상태별 페이로드를 반환하지만 문서는 일반 응답 하나만 보여 줌 | 경고. 명시적 응답 스키마를 추가합니다. |
| 문서화된 스키마가 내부·민감 필드가 있는 원시 데이터베이스 행을 노출함 | 차단. DTO 매핑을 추가합니다. |
| 공유 인증 layer가 있지만 문서에 보안 요구 사항이 빠짐 | 공개 또는 파트너용 문서에서는 차단. |
| Swagger UI가 실수로 공개됨 | 차단. 인증·관리자·개발 게이트를 추가하거나 공개 문서 결정을 기록합니다. |
| 생성 문서가 검증에 실패하거나 깨진 `$ref` 값을 가짐 | 배포 전 차단. |
| 문서화된 본문이 `415`를 빠뜨렸는데 클라이언트가 선언되지 않은 콘텐츠 타입을 보낼 수 있음 | 경고. 결과를 문서화하거나 허용 미디어 타입을 좁힙니다. |
| 문서에서 본문이 선택적인데 handler가 모든 필드를 가정함 | 차단. 본문을 필수로 표시하거나 없는 경우를 검증합니다. |

## 예시

```rust
use utoipa::{OpenApi, ToSchema};
use utoipa_axum::{router::OpenApiRouter, routes};
use utoipa_swagger_ui::SwaggerUi;

#[derive(ToSchema, serde::Serialize)]
pub struct UserDto {
    pub id: uuid::Uuid,
    pub email: String,
}

#[utoipa::path(
    get,
    path = "/users/{id}",
    tag = "users",
    params(("id" = uuid::Uuid, Path, description = "User id")),
    responses(
        (status = 200, body = UserDto),
        (status = 404, body = crate::error::ErrorBody),
    )
)]
pub async fn get_user(/* ... */) {}

#[derive(OpenApi)]
#[openapi(
    info(title = "API", version = "1.0.0"),
    components(schemas(UserDto, crate::error::ErrorBody))
)]
pub struct ApiDoc;

pub fn documented_router(state: AppState) -> axum::Router {
    let (router, api) = OpenApiRouter::new()
        .routes(routes!(get_user))
        .split_for_parts();

    router
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", api))
        .with_state(state)
}
```

## 버전과 패키지 주의 사항

- 출력할 OpenAPI 버전을 명시적으로 고릅니다. utoipa 6은 3.2를 출력할 수 있지만 많은 코드 생성 소비자는 아직 3.0이나 3.1을 기대합니다.
- `utoipa-swagger-ui`는 UI 자산을 제공하고 문서를 생성하지 않습니다. 번들된 Swagger UI 버전은 OpenAPI 버전과 무관합니다.
- `routes!`는 `#[utoipa::path]`를 요구합니다. 그것이 없는 handler는 등록되어도 스펙에 나오지 않습니다.
- `OpenApiRouter` 아래에 중첩한 평범한 `Router` 하위 앱은 메타데이터를 기여하지 않을 수 있습니다. 문서화한 라우터와 문서화하지 않은 라우터를 분명히 분리합니다.
- `operation_id` 충돌은 클라이언트 generator를 깨뜨립니다. 안정적이고 고유하게 유지합니다.
- 스키마에 쓰는 타입은 해당 utoipa 기능이 켜져 있어야 합니다. `Uuid`에는 `uuid`, 날짜 타입에는 `chrono`입니다. 기능이 빠지면 `ToSchema`가 구현되지 않았다는 오류가 납니다.
- `responses(...)`나 `components(schemas(...))`에서 참조하는 타입은 공유 오류 body를 포함해 모두 `ToSchema`를 derive해야 합니다.
- 내부 오류 모양을 게시하지 않습니다. 공유 `ErrorBody` 타입을 씁니다.
- 스펙 생성을 결정적으로 유지합니다. generator가 허용하는 곳에서 정렬이나 순서를 고정하고 커밋된 출력의 diff를 확인합니다.

## 검토 체크리스트

- 생성 전략 하나를 일관되게 씁니다.
- 스펙 엔드포인트와 Swagger UI 엔드포인트가 분리되어 있고 의도적입니다.
- 런타임 DTO와 문서화된 스키마가 같은 출처를 공유합니다.
- 문서화한 모든 operation에 `operation_id`, tag, 요청 스키마, 오류 응답이 있습니다.
- `routes!`는 `#[utoipa::path]` handler와만 씁니다.
- 데이터베이스 행이 게시 전에 공개 DTO로 매핑됩니다.
- 출력 OpenAPI 버전이 명시되어 있습니다.
- 재사용 스키마, 오류, 보안 스킴, 매개변수가 components에 있습니다.
- 생성 문서를 CI나 로컬에서 검증하거나 린트합니다.
- Swagger UI 노출이 환경 정책과 일치합니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| utoipa 6.0.0 기능, MSRV 1.88, OpenAPI 3.2 지원, 버전 설명 불일치 | [utoipa CHANGELOG](https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md), [utoipa docs](https://docs.rs/utoipa/latest/utoipa/) |
| `OpenApiRouter`, `routes!`, `split_for_parts`, 중복과 CONNECT 패닉 | [utoipa-axum](https://docs.rs/utoipa-axum/latest/utoipa_axum/), [OpenApiRouter](https://docs.rs/utoipa-axum/latest/utoipa_axum/router/struct.OpenApiRouter.html) |
| `SwaggerUi::new(...).url(...)`와 axum에서의 `.merge(...)` | [utoipa-swagger-ui](https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/) |
| `ToSchema`, `IntoParams`, `OpenApi` derive 역할 | [utoipa docs](https://docs.rs/utoipa/latest/utoipa/) |
