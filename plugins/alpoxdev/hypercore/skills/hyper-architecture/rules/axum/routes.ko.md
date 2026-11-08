# 라우트 구조

> axum 라우트 구성 규칙

---
## 안정 axum 0.8 기준선

2026-11-05에 확인한 대로 axum은 0.8.9이고 Rust 1.80 이상을 요구합니다. 경로 매개변수는 `{name}`을 쓰고 와일드카드는 `{*rest}`를 씁니다. 0.7의 `:name`과 `*rest` 문법은 동작을 조용히 바꾸지 않고 시작 시 패닉을 냅니다. 매칭은 `matchit`이 처리하므로 우선순위는 `.route()`를 호출한 순서가 아니라 경로의 구체성에서 나옵니다.

- 기능마다 `Router<AppState>`를 반환하는 `routes()` 함수를 하나 두고, 이를 병합하거나 중첩하는 루트 구성을 하나 둡니다.
- 등록 순서가 어떤 라우트가 이기는지 정한다고 가정하지 않습니다. 정적 세그먼트가 매개변수를 이기고, 매개변수가 와일드카드를 이깁니다. 겹치는 라우트는 테스트로 확인합니다.
- `nest("/api", router)`는 안쪽 라우터에 접두사를 붙이고 바깥 상태 타입을 유지합니다. 안쪽 라우터가 공유 상태를 추출하면 `Router<AppState>`여야 합니다.
- `merge(other)`는 경로와 fallback을 합칩니다. 형제 기능 라우터에는 이것을 쓰고, 실제 접두사 경계에는 `nest`를 씁니다.
- `route_service(path, service)`는 임의의 tower 서비스용입니다. 일반 handler는 `.route()`를 씁니다.
- `fallback(handler)`는 일치하지 않는 경로를 처리합니다. 라우트 등록 순서와 무관하지만, 중첩 라우터가 의도적으로 자신의 fallback을 소유하지 않는 한 루트에 정확히 하나만 있어야 합니다.
- `method_not_allowed_fallback(handler)`는 알려진 경로에 지원하지 않는 메서드가 들어온 경우를 처리합니다. 이게 없으면 axum은 `Allow` 헤더와 빈 본문을 담은 405를 반환합니다.
- `Router::layer`는 자신보다 먼저 추가된 모든 것에, fallback까지 포함해 적용됩니다. `Router::route_layer`는 라우트가 일치할 때만 적용됩니다. 의도적으로 고릅니다.
- 버전 접두사는 조립 경계에 둡니다. 기능 모듈마다 `/api/v1`을 반복하지 않습니다.
- axum 0.8은 `Host` extractor를 `axum-extra`로 옮겼습니다. 코어 import를 전제로 호스트 라우팅을 설계하지 않습니다.

## 권장 소규모 구조

```text
src/
├── app.rs
├── main.rs
└── routes/
    ├── mod.rs
    ├── health.rs
    └── users.rs
```

## 권장 대규모 구조

```text
src/routes/
├── mod.rs              # 마운트 테이블, 비즈니스 로직 없음
├── health.rs
├── users/
│   ├── mod.rs          # pub fn routes() -> Router<AppState>
│   ├── handlers.rs
│   ├── dto.rs
│   └── tests.rs
└── billing/
    ├── mod.rs
    ├── handlers.rs
    ├── dto.rs
    └── service.rs
```

`routes/mod.rs` 또는 `app.rs`가 유일한 마운트 테이블로 남습니다. 기능 폴더는 자신의 handler 함수, DTO, 기능 전용 layer를 소유합니다.

## 규칙

- `app.rs` 또는 `lib.rs`가 루트 조립을 소유하고, `main.rs`는 이를 부트스트랩하기만 합니다.
- `routes/mod.rs`는 하나뿐인 명백한 마운트 테이블입니다.
- 거대한 `Router::new()` 체인 하나보다 루트에서 병합하는 기능별 `routes()` 함수를 선호합니다.
- 기능에 파일이 둘 이상 필요하면 라우트 폴더를 씁니다.
- 아주 작은 운영 엔드포인트는 단일 파일 라우트로 두어도 됩니다.
- handler가 둘 이상이거나, 요청 DTO, 기능 미들웨어, OpenAPI 메타데이터, 서비스 오케스트레이션이 있으면 라우트를 폴더로 나눕니다.
- 버전 접두사는 조립 경계에 둡니다.
- 라우트 모듈에서 SQLx 쿼리 매크로, 풀, 마이그레이션 도우미를 import하지 않습니다.
- 기능 라우트 모듈을 다른 기능 라우트 모듈에서 import하지 않습니다.
- 루트 fallback은 한 번만 등록하고, 중첩 라우터 곳곳에 fallback을 흩뿌리지 않습니다.
- 경로 우선순위를 호출 순서에 기대지 않습니다. `matchit`이 정하고, 충돌하는 라우트는 시작 시 패닉을 냅니다.

## 마운트 패턴

```rust
use axum::Router;

use crate::routes::{billing, health, users};
use crate::state::AppState;

pub fn app(state: AppState) -> Router {
    Router::new()
        .merge(health::routes())
        .nest("/api/v1", api_routes())
        .fallback(crate::handlers::not_found)
        .with_state(state)
}

fn api_routes() -> Router<AppState> {
    Router::new()
        .merge(users::routes())
        .merge(billing::routes())
}
```

## 확장 패턴

```rust
// routes/users/mod.rs
use axum::{routing::get, Router};

use crate::state::AppState;

mod handlers;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/users", get(handlers::list).post(handlers::create))
        .route("/users/{id}", get(handlers::get).patch(handlers::update))
}
```

```rust
// routes/mod.rs
pub mod billing;
pub mod health;
pub mod users;
```

## 비준수 징후

- 단일 조립 함수 없이 `Router::new()` 조각이 무관한 파일에 흩어져 있습니다.
- 기능 모듈이 자체 리스너, 풀, tracing subscriber를 만듭니다.
- 라우트 모듈이 `sqlx::query!`, `PgPool`, `sqlx::migrate!`를 import합니다.
- 본문이 서로 다른 fallback이 여러 중첩 라우터에 정의되어 있습니다.
- 라우트 파일 하나에 DTO, 긴 handler, 기능 layer, 비즈니스 로직이 함께 있습니다.
- 버전 접두사가 한 번 정의되지 않고 기능마다 반복됩니다.
- 등록 순서를 암묵적 우선순위 장치로 사용합니다.
- layer가 일치하지 않는 경로까지 덮어야 하는데 `route_layer`를 쓰거나, 덮으면 안 되는데 `layer`를 씁니다.

## 검토 체크리스트

- 명백한 조립 함수가 하나 있습니다.
- 마운트는 형제에 `merge`를, 실제 접두사에 `nest`를 씁니다.
- 루트 fallback이 한 번 정의되고 표준 오류 봉투를 반환합니다.
- 경로 매개변수가 `{name}` 문법을 쓰고 겹치는 라우트를 테스트합니다.
- 405 동작이 설계상 없거나 의도적으로 처리되어 있습니다.
- 큰 기능은 거대한 평면 파일이 아니라 하위 앱 모듈을 씁니다.
- 기능 경계가 명확해서 새 라우트에 뻔한 자리가 있습니다.
- 라우트가 사소하지 않으면 영속 작업이 service/repository 경계를 통과합니다.
- 라우트 구조가 포트 없이 `app(test_state)`를 테스트할 수 있게 유지됩니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `{param}` / `{*wildcard}` 경로 문법 변경, 구 문법의 패닉, `route_service`, `nest`, `merge`, `fallback`, `method_not_allowed_fallback`, `route_layer` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html), [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `matchit` 기반 우선순위와 충돌 패닉 | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html), [matchit](https://docs.rs/matchit/latest/matchit/) |
| 0.8.9의 최소 Rust 버전 1.80 | [axum 0.8.9 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| 0.8에서 `Host` extractor가 `axum-extra`로 이동 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
