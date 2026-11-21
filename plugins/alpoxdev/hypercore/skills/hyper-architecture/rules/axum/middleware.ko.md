# 미들웨어와 Layer

> 설명할 수 있는 순서로 tower layer를 조립합니다

---
## 안정 tower 기준선

2026-11-05에 확인한 대로 axum에는 전용 미들웨어 시스템이 없습니다. tower 서비스를 쓰고, `tower` 0.5와 `tower-http` 0.7이 일반적인 layer를 제공합니다. 미들웨어는 `Router`, `MethodRouter`, 단일 handler에 붙일 수 있습니다.

- `Router::layer`는 호출 **전에** 추가된 모든 라우트를 감쌉니다. 따라서 마지막 `.layer()`가 가장 바깥 layer이고 요청을 가장 먼저 받습니다.
- `ServiceBuilder`는 위에서 아래로 조립합니다. builder 안의 첫 `.layer()`가 요청을 가장 먼저 받습니다. 실행 순서대로 읽히므로 이 형태를 권장합니다.
- `Router::route_layer`는 라우트가 일치할 때만 실행됩니다. `Router::layer`는 일치하지 않는 경로에서도 실행됩니다. 404 응답을 관찰하거나 모양을 바꾸면 안 되는 미들웨어에는 `route_layer`를 씁니다.
- axum은 실패할 수 없는 서비스를 기대합니다. `TimeoutLayer`처럼 실패할 수 있는 layer는 같은 builder에서 **위에** `HandleErrorLayer`를 두어 오류를 응답으로 변환해야 합니다.
- `middleware::from_fn`과 `from_fn_with_state`는 `Service`를 구현하지 않고 비동기 미들웨어를 작성합니다. 미들웨어에 `AppState`가 필요하면 언제나 `from_fn_with_state`를 씁니다.
- `from_extractor`는 extractor이면서 미들웨어인 타입용입니다. 그 밖에는 `from_fn`을 씁니다.
- 직접 만든 대응물 대신 `tower-http`의 `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, `RequestIdLayer`, `PropagateRequestIdLayer`를 씁니다.
- 요청 범위 값은 요청 extension이나 타입이 있는 extractor에 둡니다. 가변 전역이나 `static Mutex`에는 절대 두지 않습니다.

## 권장 순서

```rust
use std::time::Duration;

use axum::{error_handling::HandleErrorLayer, Router};
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    cors::CorsLayer,
    request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer},
    timeout::TimeoutLayer,
    trace::TraceLayer,
};

pub fn layers(router: Router<AppState>) -> Router<AppState> {
    router.layer(
        ServiceBuilder::new()
            .layer(SetRequestIdLayer::x_request_id(MakeRequestUuid))
            .layer(TraceLayer::new_for_http())
            .layer(CorsLayer::permissive())
            .layer(HandleErrorLayer::new(|_: BoxError| async {
                StatusCode::REQUEST_TIMEOUT
            }))
            .layer(TimeoutLayer::new(Duration::from_secs(30)))
            .layer(CompressionLayer::new())
            .layer(PropagateRequestIdLayer::x_request_id()),
    )
}
```

요청은 `SetRequestIdLayer`를 가장 먼저 만나고, 응답은 `PropagateRequestIdLayer`를 통해 나갑니다. 목록을 위에서 아래로 진입 순서로 읽습니다.

## 타입이 있는 미들웨어 패턴

```rust
use axum::{
    extract::{Request, State},
    middleware::Next,
    response::Response,
};

pub async fn require_auth(
    State(state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, AppError> {
    let token = req
        .headers()
        .get(axum::http::header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(AppError::Unauthorized)?;

    let user = state.auth.verify(token).await?;
    req.extensions_mut().insert(user);

    Ok(next.run(req).await)
}
```

필요한 라우터에 `axum::middleware::from_fn_with_state(state.clone(), require_auth)`로 마운트합니다.

## 양보할 수 없는 규칙

| 검사 | 규칙 |
|------|------|
| Layer 순서가 우연히 정해짐 | 차단 |
| 실패할 수 있는 layer에 오류 처리가 없음 | 차단 |
| 미들웨어가 전역을 통해 공유 상태를 변경함 | 차단 |
| 인증이나 테넌시 검사가 handler에만 있음 | 경고 |
| 이유 없이 `route_layer`와 `layer`를 섞어 씀 | 차단 |
| 타임아웃, CORS, 압축, tracing을 직접 구현함 | 경고 |

## 검토 체크리스트

- Layer 순서가 한 번만 작성되고 위에서 아래로 읽힙니다.
- 실패할 수 있는 layer 위에 `HandleErrorLayer`가 있습니다.
- 공유 상태가 `from_fn_with_state`나 상태를 가진 layer를 통해 미들웨어에 도달합니다.
- 요청 범위 값이 extension이나 타입이 있는 extractor를 씁니다.
- 기능 전용 인가는 전역이 아니라 범위가 한정됩니다.
- 미들웨어가 숨은 비즈니스 로직 layer가 되지 않습니다.
- CORS 정책이 명시적이고 `permissive()`와 자격 증명을 결합하지 않습니다.
- 타임아웃이 연결을 끊는 대신 의도한 응답을 반환합니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `.layer()`, `ServiceBuilder`, `route_layer`, `from_fn` 계열, `HandleErrorLayer`, 미들웨어의 상태 전달에 대한 layer 순서 | [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html) |
| `Router::layer`, `Router::route_layer`, `MethodRouter::layer` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html) |
| `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, 요청 ID layer | [tower-http](https://docs.rs/tower-http/latest/tower_http/) |
| `ServiceBuilder` 조립 의미 | [tower ServiceBuilder](https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html) |
