# utoipa 공식 문서 요약

last_verified_at: 2026-11-05

## 목차

- 안정 버전 패키지 현황
- 파생 매크로와 경로 메타데이터
- 라우터 구성과 명세 분리
- Swagger UI 제공
- 버전 주의 사항
- 이 스킬에 미치는 영향
- 출처

## 안정 버전 패키지 현황

2026-11-05에 docs.rs와 utoipa 체인지로그에서 확인했습니다.

| 패키지 | 안정 버전 | 비고 |
|---|---:|---|
| `utoipa` | 6.0.0 | MSRV 1.88, `Version32`를 통한 OpenAPI 3.2 지원, `ToSchema`, `IntoParams`, `ToResponse`, `OpenApi` 파생 |
| `utoipa-axum` | 0.3.0 | `OpenApiRouter`, `routes!`, `split_for_parts` |
| `utoipa-swagger-ui` | 10.0.2 | axum용 `SwaggerUi` 계층, 번들 UI 버전은 별개 |

렌더링된 utoipa 문서는 기본 OpenAPI 버전에 대해 내부적으로 일관되지 않습니다. 기능 목록은 3.1을 언급하지만 `openapi` 모듈은 3.2를 설명합니다. 버전은 명시적으로 선언합니다.

## 파생 매크로와 경로 메타데이터

- `#[derive(ToSchema)]`는 요청이나 응답 타입에 재사용할 스키마를 생성합니다.
- `#[derive(IntoParams)]`는 구조체 필드에서 경로나 쿼리 매개변수를 생성합니다.
- `#[derive(OpenApi)]`는 루트 문서와 그 컴포넌트 레지스트리를 만듭니다.
- `#[utoipa::path(get, path = "/users/{id}", ...)]`는 핸들러에 작업 메타데이터를 붙이며, 라우터 수집기가 읽는 대상입니다.

출처: [utoipa docs](https://docs.rs/utoipa/latest/utoipa/)

## 라우터 구성과 명세 분리

```rust
let (router, api) = OpenApiRouter::new()
    .routes(routes!(get_user, create_user))
    .split_for_parts();
```

- `OpenApiRouter::routes`는 메서드 라우터를 등록하고 핸들러의 경로 메타데이터로 문서를 확장합니다.
- `split_for_parts`는 내부 `axum::Router`와 `OpenApi` 값을 반환합니다.
- `routes!`는 `#[utoipa::path]`가 붙은 핸들러만 수집합니다.
- `routes!`는 같은 경로에 같은 HTTP 메서드를 중복 등록하거나 CONNECT 핸들러를 등록하면 패닉을 일으킵니다.

출처: [OpenApiRouter](https://docs.rs/utoipa-axum/latest/utoipa_axum/router/struct.OpenApiRouter.html), [routes!](https://docs.rs/utoipa-axum/latest/utoipa_axum/macro.routes.html)

## Swagger UI 제공

```rust
let app = Router::new().merge(
    SwaggerUi::new("/swagger-ui")
        .url("/api-docs/openapi.json", ApiDoc::openapi()),
);
```

- `.url(spec_path, openapi)`는 명세 엔드포인트를 붙입니다.
- `.merge(...)`는 UI 라우터를 axum 라우터에 붙입니다.
- axum 통합에는 크레이트의 `axum` 기능과 axum 0.7 이상이 필요합니다.

출처: [utoipa-swagger-ui](https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/)

## 버전 주의 사항

- utoipa 6는 OpenAPI 3.2를 출력할 수 있지만, 많은 클라이언트 생성기는 아직 3.0이나 3.1을 기대합니다. 출력 버전을 명시적으로 고정합니다.
- 번들 Swagger UI 버전은 OpenAPI 버전과 별개 의존성입니다.
- `OpenApiRouter` 옆에 합친 일반 `axum::Router`는 라우트만 더하고 메타데이터는 더하지 않습니다.
- 작업 ID는 고유하고 안정적이어야 합니다. 그렇지 않으면 생성된 클라이언트가 계속 바뀝니다.

## 이 스킬에 미치는 영향

- 이 스킬은 하나의 명세 소스, 하나의 명세 엔드포인트, 명시적인 OpenAPI 버전을 요구합니다.
- 문서화한 핸들러는 런타임이 서비스하는 핸들러와 같아야 합니다. 수집기는 일반 라우트를 찾아내지 않습니다.
- Swagger UI는 JSON 문서와 별개의 노출 결정으로 다룹니다.

## Sources
> Checked 2026-11-05.
| 주장 | 출처 | 확인일 |
|---|---|---|
| utoipa 6.0.0, 파생 매크로, 3.2 지원, MSRV 1.88 | <https://docs.rs/utoipa/latest/utoipa/> | 2026-11-05 |
| utoipa 6.0.0 체인지로그 | <https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md> | 2026-11-05 |
| `OpenApiRouter`, `split_for_parts`, `routes!`의 의미와 패닉 | <https://docs.rs/utoipa-axum/latest/utoipa_axum/> | 2026-11-05 |
| `SwaggerUi` axum 통합 | <https://docs.rs/utoipa-swagger-ui/latest/utoipa_swagger_ui/> | 2026-11-05 |
