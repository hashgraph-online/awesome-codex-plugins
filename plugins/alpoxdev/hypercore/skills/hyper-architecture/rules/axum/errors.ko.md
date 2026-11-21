# 오류와 응답

> 오류 타입 하나, 응답 모양 하나, 내부 정보 노출 없음

---
## 안정 기준선

2026-11-05에 확인한 대로 axum handler는 `IntoResponse`를 구현하는 타입을 반환해 실패를 알립니다. `thiserror` 2.0이 현재 오류 enum용 derive crate입니다. axum의 기본 거부는 평문 본문을 만들므로, 안정적인 JSON 봉투를 원하는 API는 도메인 오류뿐 아니라 거부도 변환해야 합니다. `fallback`은 일치하지 않는 경로를, `method_not_allowed_fallback`은 알려진 경로에 지원하지 않는 메서드가 온 경우를 처리합니다. 후자가 없으면 axum은 `Allow` 헤더와 함께 405를 반환합니다.

- `AppError` enum 하나와 `ErrorBody` DTO 하나를 정의합니다.
- `IntoResponse`를 한 번 구현하고, 각 변형을 상태, 안정적인 기계용 `code`, 안전한 메시지로 매핑합니다.
- 정제된 본문을 반환하기 전에 내부 원인을 `tracing::error!`로 기록합니다.
- SQL 텍스트, 연결 문자열, 백트레이스, 파일 경로, provider 페이로드를 응답에 절대 넣지 않습니다.
- `sqlx::Error::RowNotFound`와 도메인의 "not found"는 의도적으로 404로 매핑합니다. 인프라 변형이 실수로 500이 되게 두지 않습니다.
- extractor 거부를 변환합니다. API가 JSON 봉투를 약속하면 사용자 정의 extractor는 axum 기본 거부가 아니라 `AppError`를 반환해야 합니다. `Json<T>::from_request`는 `JsonRejection`으로 실패하므로, extractor 안에서 `?`가 동작하려면 `#[from] axum::extract::rejection::JsonRejection` 변형이 `AppError`에 있어야 합니다.
- not-found와 method-not-allowed 본문을 같은 봉투로 일관되게 유지합니다.
- 패닉은 오류 처리가 아닙니다. 요청에서 나온 값에 `unwrap()`과 `expect()`를 피하고, 패닉을 연결을 중단시키는 버그로 취급합니다.

## 핵심 규칙

예상한 실패는 응답으로 변환되는 타입 값입니다. 예상하지 못한 실패는 기록하고 일반 500으로 반환합니다.

## 예시

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("validation failed")]
    Validation(#[from] validator::ValidationErrors),
    #[error("invalid request")]
    InvalidRequest(#[from] axum::extract::rejection::JsonRejection),
    #[error("unauthorized")]
    Unauthorized,
    #[error("forbidden")]
    Forbidden,
    #[error("not found")]
    NotFound,
    #[error("conflict")]
    Conflict,
    #[error("database error")]
    Database(#[from] sqlx::Error),
}

#[derive(Serialize, utoipa::ToSchema)]
pub struct ErrorBody {
    pub code: &'static str,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fields: Option<serde_json::Value>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code, message, fields) = match self {
            AppError::Validation(errors) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "validation_failed",
                "request validation failed".to_owned(),
                serde_json::to_value(errors.field_errors()).ok(),
            ),
            AppError::InvalidRequest(_) => (
                StatusCode::BAD_REQUEST,
                "invalid_request",
                "request body is not valid JSON".to_owned(),
                None,
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                "unauthorized",
                "authentication required".to_owned(),
                None,
            ),
            AppError::Forbidden => (
                StatusCode::FORBIDDEN,
                "forbidden",
                "not allowed".to_owned(),
                None,
            ),
            AppError::NotFound => (
                StatusCode::NOT_FOUND,
                "not_found",
                "resource not found".to_owned(),
                None,
            ),
            AppError::Conflict => (
                StatusCode::CONFLICT,
                "conflict",
                "resource conflict".to_owned(),
                None,
            ),
            AppError::Database(err) => {
                tracing::error!(error = %err, "database error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "internal_error",
                    "internal server error".to_owned(),
                    None,
                )
            }
        };

        (status, Json(ErrorBody { code, message, fields })).into_response()
    }
}
```

## Not-Found와 메서드 처리

```rust
use axum::{http::StatusCode, response::IntoResponse, Json};

pub async fn not_found() -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorBody {
            code: "not_found",
            message: "route not found".to_owned(),
            fields: None,
        }),
    )
}
```

조립 루트에 `fallback(not_found)`를 한 번 등록합니다. API 계약이 405와 404를 구분할 때만 `method_not_allowed_fallback`을 추가하고 그 선택을 문서화합니다.

## 검토 체크리스트

- `AppError`가 하나 있고 모든 handler가 그것 또는 그것으로 변환되는 타입을 반환합니다.
- `IntoResponse`가 한 번 구현되고 handler가 오류 본문을 직접 만들지 않습니다.
- 내부 원인을 직렬화하지 않고 기록합니다.
- not-found와 method-not-allowed 응답이 같은 봉투를 씁니다.
- API가 JSON 오류를 약속하는 곳에서 extractor 거부를 변환합니다.
- `sqlx::Error` 변형을 의도적으로 매핑합니다.
- 건드린 코드에서 요청에서 나온 값에 `unwrap()`이나 `expect()`를 쓰지 않습니다.
- 오류 등급마다 실패 하나 이상의 상태와 본문을 테스트가 덮습니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `IntoResponse`가 handler 실패 경로, 튜플 응답, `StatusCode` | [axum response](https://docs.rs/axum/latest/axum/response/index.html), [IntoResponse](https://docs.rs/axum/latest/axum/response/trait.IntoResponse.html) |
| 기본 거부 본문과 `Result<T, T::Rejection>` 처리 | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| `fallback`과 `method_not_allowed_fallback` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html) |
| `thiserror` 2.0 derive | [thiserror](https://docs.rs/thiserror/latest/thiserror/) |
