# 검증, 테스트, 런타임 생태계 요약

last_verified_at: 2026-11-05

## 목차

- 안정 버전 패키지 현황
- validator
- axum-test
- thiserror와 tracing
- 이 스킬에 미치는 영향
- 출처

## 안정 버전 패키지 현황

2026-11-05에 docs.rs와 crates.io 메타데이터에서 확인했습니다.

| 패키지 | 안정 버전 | 비고 |
|---|---:|---|
| `validator` | 0.21.0 | 파생 기반 검증, axum 통합 없음 |
| `axum-test` | 21.1.0 | `TestServer`, 요청 빌더, 직접 디스패치 또는 임의 포트 |
| `thiserror` | 2.0.21 | 오류 열거형 파생 |
| `tracing` | 0.1.44 | 구조화된 스팬과 이벤트 |
| `tracing-subscriber` | 0.3.23 | 구독자와 `EnvFilter` 설정 |
| `tokio` | 1.54.1 | 런타임, `TcpListener`, 시그널 처리 |
| `http-body-util` | 0.1.x | 테스트 검증용 `BodyExt::collect` |

## validator

- 구조체에 `Validate`를 파생하고 필드에 `#[validate(...)]`를 붙입니다.
- 내장 규칙에는 `email`, `url`, `length`, `range`, `must_match`, `contains`, `does_not_contain`, `custom`, `regex`, `non_control_character`, `required`가 있고, `credit_card`는 `card` 기능이 필요합니다.
- `validate()`는 `Result<(), ValidationErrors>`를 반환합니다.
- `ValidationErrors`는 `HashMap<Cow<'static, str>, ValidationErrorsKind>`이고, `field_errors()`는 오류 본문에 쓰는 필드 단위 맵을 반환합니다.
- 렌더링된 문서의 설치 예제에는 아직 `version = "0.16"`이 나옵니다. 그 예제는 공개된 0.21.0보다 오래된 내용입니다.

출처: [validator](https://docs.rs/validator/latest/validator/), [ValidationErrors](https://docs.rs/validator/latest/validator/struct.ValidationErrors.html)

## axum-test

- `TestServer::new(app)`는 기본적인 경우 axum `Router`를 받습니다. 서버는 핸들러로 직접 디스패치하거나 임의 포트에 바인딩할 수 있습니다.
- 요청은 서버에서 만듭니다. 예를 들어 `server.post("/users").json(&value).await`처럼 씁니다.
- 응답은 상태와 본문 도우미를 제공하며, 정확한 검증 메서드 집합은 설치된 버전에 따라 다릅니다.
- 쿠키, 헤더, 멀티파트 도우미는 크레이트의 모듈에 있습니다.

출처: [axum-test](https://docs.rs/axum-test/latest/axum_test/)

## thiserror와 tracing

- `#[derive(thiserror::Error)]`에 `#[error("...")]`와 `#[from]`을 더하면 `AppError`가 쓰는 오류 열거형이 만들어집니다.
- `tracing::error!`, `warn!`, `info!`, `#[instrument]`가 로깅 수단입니다. 핸들러와 서비스는 `println!` 대신 이것을 씁니다.
- `tracing_subscriber::registry().with(EnvFilter::from_default_env())`는 바이너리에서 흔히 쓰는 초기화 경로입니다.

출처: [thiserror](https://docs.rs/thiserror/latest/thiserror/), [tracing](https://docs.rs/tracing/latest/tracing/), [tracing-subscriber](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/)

## 이 스킬에 미치는 영향

- 공식 axum 통합이 없으므로 검증은 검증된 추출기(validated extractor)로 구현합니다.
- 라우터 테스트는 기본으로 `tower::ServiceExt::oneshot`을 쓰고, 빌더나 쿠키 지원이 값을 할 때 `axum-test`를 씁니다.
- 오류와 로깅 규칙은 `thiserror`와 `tracing`을 전제합니다. 둘은 생태계 기본값이지 프레임워크 요구 사항이 아닙니다.

## Sources
> Checked 2026-11-05.
| 주장 | 출처 | 확인일 |
|---|---|---|
| validator 규칙과 오류 타입 | <https://docs.rs/validator/latest/validator/> | 2026-11-05 |
| axum-test `TestServer` 흐름 | <https://docs.rs/axum-test/latest/axum_test/> | 2026-11-05 |
| thiserror 파생 | <https://docs.rs/thiserror/latest/thiserror/> | 2026-11-05 |
| tracing과 구독자 설정 | <https://docs.rs/tracing/latest/tracing/> | 2026-11-05 |
| tokio 런타임과 시그널 | <https://docs.rs/tokio/latest/tokio/> | 2026-11-05 |
