# Handler와 Extractor

> handler는 타입이 있고 얇게 유지하며 순서를 올바르게 지킵니다

---
## 안정 axum 0.8 기준선

2026-11-05에 확인한 대로 handler는 인자가 `FromRequestParts`(마지막을 제외한 전부) 또는 `FromRequest`(본문을 소비하는 마지막 인자)를 구현하는 `async fn`입니다. Extractor는 왼쪽에서 오른쪽으로 실행됩니다. 본문을 소비하는 extractor는 정확히 하나여야 하고, axum은 그것이 마지막 인자인지 컴파일 시점에 강제합니다. axum-core 0.5부터 `FromRequestParts`는 trait에서 반환 위치 `impl Trait`를 쓰므로 `#[async_trait]`이 더 이상 필요 없고, 새 코드에 남아 있으면 `hypercore-only` 스타일 위반입니다.

- `State`, `Path`, `Query`, `HeaderMap`, 인증 extractor를 `Json`, `Form`, `Bytes`, `String`보다 앞에 둡니다.
- `T: IntoResponse`인 `Result<T, AppError>`를 반환합니다. 모든 분기에서 오류 응답을 직접 만들지 않습니다.
- handler 하나가 잘못된 JSON과 의미상 실패를 구분해야 할 때만 `Result<Json<T>, JsonRejection>`을 씁니다.
- 0.8에서 `Path<(A, B)>`는 경로 매개변수 개수와 정확히 일치해야 합니다. 불일치는 조용한 부분 파싱이 아니라 거부입니다.
- `serde_json::Value`보다 타입이 있는 DTO를 선호합니다. `Value`는 전송 경계에 있을 수 있지만 service로 넘어가면 안 됩니다.
- handler가 `Handler`를 만족하지 못하면 `axum-macros`의 `#[axum::debug_handler]`를 씁니다. trait의 벽 대신 표적이 분명한 오류를 냅니다.
- extractor에 비즈니스 분기를 넣지 않습니다. 사용자 정의 extractor는 신원이나 모양을 검증하고, 정책은 service가 정합니다.

## 핵심 규칙

- 작은 라우트에는 인라인 handler를 써도 됩니다.
- 분리한 handler는 기능별로 묶인 평범한 함수로 유지합니다. controller 구조체로 감싸지 않습니다.
- handler는 전송 오케스트레이션만 소유합니다. 추출, 검증 호출, service 호출, 응답 구성입니다.
- handler 모듈에는 SQL, 풀 생성, 마이그레이션 호출이 없습니다.

## 권장 패턴

```rust
use axum::{extract::{Path, State}, Json};

use crate::{dto::user::CreateUser, error::AppError, state::AppState};

pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUser>,
) -> Result<(StatusCode, Json<UserDto>), AppError> {
    let user = state.users.create(payload).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

pub async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<UserDto>, AppError> {
    Ok(Json(state.users.get(id).await?))
}
```

## 사용자 정의 extractor 패턴

같은 검증이나 인증 경계가 여러 handler에서 반복되면 사용자 정의 extractor를 씁니다.

```rust
use axum::{
    extract::{FromRequest, Request},
    Json,
};
use serde::de::DeserializeOwned;
use validator::Validate;

use crate::error::AppError;

pub struct ValidatedJson<T>(pub T);

impl<T, S> FromRequest<S> for ValidatedJson<T>
where
    T: DeserializeOwned + Validate,
    S: Send + Sync,
{
    type Rejection = AppError;

    async fn from_request(req: Request, state: &S) -> Result<Self, Self::Rejection> {
        let Json(value) = Json::<T>::from_request(req, state).await?;
        value.validate()?;
        Ok(Self(value))
    }
}
```

extractor가 handler와 같은 `AppError`를 반환하므로 검증 실패와 도메인 실패가 하나의 봉투를 공유합니다. `Json::<T>::from_request`는 `JsonRejection`으로 거부하므로, 위 코드의 `?`가 컴파일되려면 `AppError`에 `#[from] axum::extract::rejection::JsonRejection` 변형이 필요합니다.

## 응답 규칙

- JSON에는 `Json<T>`를, 빈 본문에는 `StatusCode`를, 상태가 의미를 가지면 `(StatusCode, Json<T>)` 같은 튜플을 반환합니다.
- `AppError`에 `IntoResponse`를 한 번만 구현합니다. handler마다 상태 매핑을 복제하지 않습니다.
- 204 응답에는 `NoContent`를 씁니다.
- 응답 DTO는 데이터베이스 행과 분리합니다. `rules/axum/database.md`를 봅니다.

## 검토 체크리스트

- extractor가 유효한 순서로 나오고 본문 extractor가 마지막입니다.
- 공유 상태를 전역이 아니라 `State`로 추출합니다.
- 요청에서 나온 값을 `unwrap()`하지 않습니다.
- handler가 공유 오류 타입과 함께 `Result`를 반환합니다.
- DTO가 타입이 있고 service 호출 전에 검증됩니다.
- handler가 `sqlx`나 provider SDK를 import하지 않습니다.
- 사용자 정의 extractor가 공유 오류 봉투를 재사용합니다.
- 새 extractor 구현에 `#[async_trait]`이 없습니다.
- handler 모듈이 읽기 좋게 유지됩니다. 분기를 설명하는 데 긴 주석이 필요한 handler는 service에 속합니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Extractor 순서, 본문을 소비하는 extractor 하나, `Result<T, T::Rejection>`, 사용자 정의 extractor | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| 본문 extractor 앞의 `State` 배치와 `FromRef` 하위 상태 | [axum State](https://docs.rs/axum/latest/axum/extract/struct.State.html) |
| 0.8 계열에서 반환 위치 `impl Trait`가 `#[async_trait]`을 대체 | [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md) |
| 0.8의 `Path` 튜플 길이 검사 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `#[debug_handler]` 동작 | [axum-macros](https://docs.rs/axum-macros/latest/axum_macros/attr.debug_handler.html) |
