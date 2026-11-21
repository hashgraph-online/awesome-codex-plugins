# tower와 tower-http 공식 문서 요약

last_verified_at: 2026-11-05

## 목차

- 안정 버전 패키지 현황
- 공식 문서에서 확인한 사항
- 계층 순서 규칙
- 이 스킬에 미치는 영향
- 출처

## 안정 버전 패키지 현황

2026-11-05에 docs.rs와 crates.io 메타데이터에서 확인했습니다.

| 패키지 | 안정 버전 | 비고 |
|---|---:|---|
| `tower` | 0.5.3 | `util` 기능 뒤에 있는 `Service`, `Layer`, `ServiceBuilder`, `ServiceExt` |
| `tower-http` | 0.7.1 | Trace, CORS, 압축, 타임아웃, 요청 ID, 제한, 정적 파일 계층 |
| `tower-layer` | 0.3.x | 모든 tower 미들웨어가 사용하는 `Layer` 트레이트 |
| `tower-service` | 0.3.x | `Service` 트레이트 |

설치된 `Cargo.lock`이 우선합니다. 계층 기능 이름은 미들웨어마다 다르므로, 추가하기 전에 설치된 크레이트의 기능 목록을 확인합니다.

## 공식 문서에서 확인한 사항

1. axum에는 별도의 미들웨어 체계가 없고 tower를 통합해 씁니다. 모든 tower와 tower-http 미들웨어가 axum에서 동작합니다.
출처: [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

2. `ServiceBuilder`는 처음 추가한 `.layer()`가 요청을 먼저 받도록 계층을 구성합니다. `Router::layer`는 앞서 추가한 라우트에 적용되므로 마지막 `.layer()` 호출이 가장 바깥 계층이 됩니다.
출처: [axum middleware ordering](https://docs.rs/axum/latest/axum/middleware/index.html), [ServiceBuilder](https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html)

3. `ServiceExt::oneshot`은 서비스를 소비하고 준비되면 한 번 호출합니다. 소켓 없이 라우터를 시험하는 표준 방법입니다.
출처: [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html)

4. 서비스가 오류를 반환할 수 있는 계층은 `HandleErrorLayer`와 짝을 이뤄야 합니다. axum이 실패하지 않는 서비스를 전제하기 때문입니다. `TimeoutLayer`와 속도 제한 계층이 흔한 사례입니다.
출처: [axum middleware error handling](https://docs.rs/axum/latest/axum/middleware/index.html), [HandleErrorLayer](https://docs.rs/axum/latest/axum/error_handling/struct.HandleErrorLayer.html)

5. `tower-http`는 `TraceLayer`, `CorsLayer`, `CompressionLayer`, `TimeoutLayer`, `SetRequestIdLayer`, `PropagateRequestIdLayer`를 바로 쓸 수 있는 계층으로 제공합니다.
출처: [tower-http](https://docs.rs/tower-http/latest/tower_http/)

6. `ServiceBuilder::map_request`, `map_response`, `then`, `and_then`은 `Service` 구현을 새로 쓰지 않고 작은 임시 변환을 처리합니다.
출처: [axum middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

## 계층 순서 규칙

| 구성 | 요청 순서 |
|---|---|
| `router.layer(A).layer(B).layer(C)` | C, B, A, 핸들러 |
| `ServiceBuilder::new().layer(A).layer(B).layer(C)` | A, B, C, 핸들러 |
| `route_layer` | 라우트가 일치할 때만 실행 |
| `layer` | 일치한 경로와 일치하지 않은 경로 모두에서 실행하며 폴백도 포함 |

어느 경우든 응답 순서는 요청 순서의 역순입니다.

## 이 스킬에 미치는 영향

- 이 스킬은 계층 스택을 위에서 아래로 읽을 수 있기를 요구하며, 이 때문에 `ServiceBuilder`를 선호합니다.
- `route_layer`와 `layer`의 구분은 인증이나 추적이 404를 관찰하는지를 바꾸므로 판단 기준으로 삼습니다.
- 실패할 수 있는 계층이 있으면 `HandleErrorLayer`의 위치를 확인합니다.

## Sources
> Checked 2026-11-05.
| 주장 | 출처 | 확인일 |
|---|---|---|
| axum이 tower와 tower-http 미들웨어를 사용 | <https://docs.rs/axum/latest/axum/middleware/index.html> | 2026-11-05 |
| `ServiceBuilder` 순서 | <https://docs.rs/tower/latest/tower/struct.ServiceBuilder.html> | 2026-11-05 |
| `ServiceExt::oneshot` | <https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html> | 2026-11-05 |
| `HandleErrorLayer`와 실패 가능 계층 | <https://docs.rs/axum/latest/axum/error_handling/struct.HandleErrorLayer.html> | 2026-11-05 |
| tower-http 계층 목록 | <https://docs.rs/tower-http/latest/tower_http/> | 2026-11-05 |
