# Axum 공식 문서 요약

last_verified_at: 2026-11-05

## 목차

- 안정 버전 패키지 현황
- 공식 문서에서 확인한 사항
- 0.8에서 문제가 되는 변경
- 이 스킬에 미치는 영향
- 출처

## 안정 버전 패키지 현황

2026-11-05에 docs.rs와 axum 체인지로그에서 확인했습니다. 이는 근거 자료로 남기는 현황이며 자동 업그레이드 대상이 아닙니다.

| 패키지 | 안정 버전 | 확인한 호환성 |
|---|---:|---|
| `axum` | 0.8.9 | MSRV 1.80, `tokio` 선택 기능, `json`, `query`, `form`, `matched-path`, `original-uri`, `tower-log`, `tracing`, `multipart`, `ws`, `macros` 기능 |
| `axum-core` | 0.5.x | `#[async_trait]`가 트레이트의 반환 위치 `impl Trait`로 대체됨 |
| `axum-macros` | 0.5.x | `#[debug_handler]`, `#[derive(FromRequest)]`, `#[derive(FromRef)]` |
| `axum-extra` | 0.10.x | `Host`, `TypedHeader`, `CookieJar` 및 그 밖의 선택형 추출기 |

구현에서는 설치된 `Cargo.toml`과 `Cargo.lock`이 우선합니다. 확인일 이후에 의존성을 바꾸기 전에는 docs.rs를 다시 확인합니다.

## 공식 문서에서 확인한 사항

1. `Router<S>`는 `S` 타입의 상태가 빠진 라우터입니다. `serve`에는 `Router<()>`만 넘길 수 있습니다. `with_state`는 상태를 한 번 주입합니다. `nest`와 `merge`는 같은 상태 타입을 요구합니다.
출처: [Router](https://docs.rs/axum/latest/axum/struct.Router.html), [State](https://docs.rs/axum/latest/axum/extract/struct.State.html)

2. 추출기는 왼쪽에서 오른쪽으로 실행됩니다. 마지막을 제외한 모든 추출기는 `FromRequestParts`를 구현하고, 마지막 추출기는 `FromRequest`를 구현해 본문을 소비할 수 있습니다. 본문을 소비하는 추출기는 정확히 하나만 허용되며, axum이 그 위치를 컴파일 시점에 강제합니다.
출처: [extract](https://docs.rs/axum/latest/axum/extract/index.html)

3. `State`는 라우터마다 두는 전역 값입니다. 요청에서 나온 데이터는 `Extension`, 직접 만든 추출기, 또는 요청 확장에 둡니다. `FromRef`는 하위 상태를 제공합니다.
출처: [State](https://docs.rs/axum/latest/axum/extract/struct.State.html)

4. `Router::layer`는 앞서 추가한 모든 라우트를 감싸므로 마지막 호출이 가장 바깥 계층이 됩니다. `ServiceBuilder`는 첫 번째 계층을 먼저 실행합니다. `route_layer`는 라우트가 일치할 때만 실행됩니다.
출처: [middleware](https://docs.rs/axum/latest/axum/middleware/index.html)

5. axum은 실패하지 않는 서비스를 전제합니다. 실패할 수 있는 계층에는 그 위에 `HandleErrorLayer`가 필요합니다.
출처: [middleware error handling](https://docs.rs/axum/latest/axum/middleware/index.html)

6. `axum::serve(listener, app)`은 `TcpListener`와 make-service를 받고, `with_graceful_shutdown`을 제공합니다.
출처: [serve](https://docs.rs/axum/latest/axum/fn.serve.html), [Serve](https://docs.rs/axum/latest/axum/serve/struct.Serve.html)

7. `fallback`은 일치하는 라우트가 없는 경로를 처리하고, `method_not_allowed_fallback`은 알려진 경로에 지원하지 않는 메서드가 들어온 경우를 처리합니다. 후자가 없으면 axum은 `Allow` 헤더와 함께 405를 반환합니다.
출처: [Router](https://docs.rs/axum/latest/axum/struct.Router.html)

8. `Json`, `Query`, `Path`, `Form`의 거부는 타입이 정해져 있고, 핸들러마다 `Result<T, T::Rejection>`으로 처리할 수 있습니다.
출처: [extract](https://docs.rs/axum/latest/axum/extract/index.html)

## 0.8에서 문제가 되는 변경

- 경로 문법이 `/:id`와 `/*rest`에서 `/{id}`와 `/{*rest}`로 바뀌었습니다. 예전 문법은 시작할 때 패닉을 일으킵니다.
- `Router`와 `MethodRouter`에 추가하는 핸들러와 서비스는 `Sync`여야 합니다.
- `Option<Path<T>>`는 더 이상 모든 오류 상황을 삼키지 않으며, `Option<Query<T>>`는 `OptionalFromRequestParts` 구현을 잃었습니다.
- `Host`가 `axum-extra`로 옮겨졌습니다.
- `Serve::tcp_nodelay`가 제거되었습니다. `serve`는 리스너에 대해 제네릭이며 `serve::ListenerExt`가 스트림 속성을 설정합니다.
- 0.8.9에서 MSRV가 1.80으로 올랐습니다.

출처: [axum CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md), [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md)

## 이 스킬에 미치는 영향

- 이 스킬은 경로나 미들웨어 규칙을 적용하기 전에 설치된 axum 계열 버전을 확인합니다. 0.7 문법은 스타일 선택이 아니라 마이그레이션에서 발견한 문제로 다룹니다.
- 구성과 상태 규칙은 일반적인 "앱 객체" 모델이 아니라 `Router<S>`의 의미를 따릅니다.
- 미들웨어 규칙은 문서에 나온 순서를 그대로 담습니다. 계층 순서가 미묘한 동작 변화를 일으키는 가장 흔한 원인이기 때문입니다.

## Sources
> Checked 2026-11-05.
| 주장 | 출처 | 확인일 |
|---|---|---|
| 라우터 상태, `with_state`, `nest`, `merge`, `fallback`, `route_layer` | <https://docs.rs/axum/latest/axum/struct.Router.html> | 2026-11-05 |
| 추출기 순서와 거부 처리 | <https://docs.rs/axum/latest/axum/extract/index.html> | 2026-11-05 |
| 상태와 `FromRef` | <https://docs.rs/axum/latest/axum/extract/struct.State.html> | 2026-11-05 |
| 계층 순서와 `HandleErrorLayer` | <https://docs.rs/axum/latest/axum/middleware/index.html> | 2026-11-05 |
| `serve`와 정상 종료 | <https://docs.rs/axum/latest/axum/fn.serve.html> | 2026-11-05 |
| 0.8 호환성 깨는 변경과 MSRV | <https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md> | 2026-11-05 |
