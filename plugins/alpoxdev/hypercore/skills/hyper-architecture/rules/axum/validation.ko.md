# 요청 검증

> 전송 경계에서 검증하고 타입이 있는 도메인 값을 안쪽으로 넘깁니다

---
## 안정 패키지 기준선

2026-11-05에 확인한 대로 `validator`는 0.21.0입니다. derive 기반 검증 crate이며 axum 통합이 아닙니다. axum에는 내장 validator가 없으므로 검증 extractor가 통합 지점입니다. `serde`는 모양과 타입을 처리하고, `validator`는 타입으로 표현할 수 없는 규칙을 처리합니다. `validator` 문서의 설치 스니펫에는 여전히 `version = "0.16"`이 나오므로 그 스니펫이 아니라 공개된 crate 버전과 `Cargo.lock`을 신뢰합니다.

- 동작에 영향을 주는 외부 제어 `Path`, `Query`, 헤더, 쿠키, JSON, 폼, multipart 값을 모두 검증합니다.
- 요청 DTO로 역직렬화하고 검증한 다음 도메인 타입으로 변환합니다. DTO를 repository에 넘기지 않습니다.
- 검증 오류 봉투는 하나로 유지합니다. 의미상 잘못된 입력에 `422`를, 문법이 깨진 입력에 `400`을 쓰거나 그 반대로 하되, 정책을 한 번 문서화하고 모든 곳에 적용합니다.
- serde 거부와 규칙 거부를 구분합니다. `JsonRejection`은 콘텐츠 타입 누락, 문법, 역직렬화를 덮고, `ValidationErrors`는 규칙 위반을 덮습니다.
- `Path`와 `Query` DTO도 검증합니다. 경로의 `Uuid`는 이미 타입 안전하지만 페이지네이션 경계, 정렬 허용 목록, 필터 길이는 그렇지 않습니다.
- 본문 크기 제한도 검증의 일부입니다. 업로드나 큰 페이로드를 받으면 `DefaultBodyLimit`을 명시적으로 설정합니다.
- 이 스킬에 맞추기 위해 검증 crate를 추가하거나 교체하지 않습니다.

## 핵심 규칙

service 로직이 소비하기 전에 요청 데이터를 검증하고, handler 전반에서 실패 모양을 동일하게 유지합니다.

## 승인된 선택지

| 형태 | 선호 |
|---|---|
| 모양과 타입만 | DTO의 `serde` derive |
| 필드 규칙(길이, 범위, 이메일, 정규식) | `validator` derive와 검증 extractor |
| 필드 간 규칙 | 구조체의 `validator` `custom` 또는 타입이 있는 오류를 동반한 명시적 service 검사 |
| 경로·쿼리 경계 | handler의 명시적 검사 또는 작은 검증 extractor |
| 업로드 제약 | `DefaultBodyLimit`과 전체 본문 파싱 전 크기 검사 |

## 예시

```rust
use serde::Deserialize;
use validator::Validate;

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUser {
    #[validate(email)]
    pub email: String,
    #[validate(length(min = 1, max = 100))]
    pub name: String,
    #[validate(range(min = 18, max = 120))]
    pub age: u8,
}

pub async fn create_user(
    State(state): State<AppState>,
    ValidatedJson(payload): ValidatedJson<CreateUser>,
) -> Result<(StatusCode, Json<UserDto>), AppError> {
    let user = state.users.create(payload.into()).await?;
    Ok((StatusCode::CREATED, Json(user)))
}
```

`ValidatedJson`은 `rules/axum/handlers.md`에서 옵니다. 거부 타입이 `AppError`이므로 검증 실패와 도메인 실패가 하나의 본문을 공유합니다.

## 오류 매핑

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("validation failed")]
    Validation(#[from] validator::ValidationErrors),
    #[error("invalid request")]
    BadRequest(&'static str),
    #[error("unauthorized")]
    Unauthorized,
    #[error("not found")]
    NotFound,
    #[error(transparent)]
    Database(#[from] sqlx::Error),
}
```

`Validation(...)`은 필드 오류와 함께 `422`로, `BadRequest(...)`는 내부 정보 없이 `400`으로 매핑합니다. 원시 페이로드를 절대 되돌려 보내지 않습니다.

## 검토 체크리스트

- 사소하지 않은 요청 DTO가 `Validate`를 갖추고 service 호출 전에 검증됩니다.
- JSON 본문뿐 아니라 경로, 쿼리, 헤더, multipart 입력도 검증합니다.
- 오류 봉투 하나가 serde 거부와 규칙 위반을 함께 덮습니다.
- 검증 실패가 필드 값이나 내부 경로를 노출하지 않습니다.
- 필드 간 규칙이 한 곳에 있고 handler마다 중복되지 않습니다.
- 큰 페이로드가 가능한 곳에는 본문 제한이 명시되어 있습니다.
- 명시한 필요 없이 새 검증 의존성을 추가하지 않았습니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `validator` derive 사용, 내장 규칙, `ValidationErrors` 모양, 현재 버전 0.21.0 | [validator](https://docs.rs/validator/latest/validator/), [ValidationErrors](https://docs.rs/validator/latest/validator/struct.ValidationErrors.html) |
| `JsonRejection` 변형과 `Result<Json<T>, JsonRejection>` 처리 | [axum extract](https://docs.rs/axum/latest/axum/extract/index.html) |
| `DefaultBodyLimit` 동작 | [axum DefaultBodyLimit](https://docs.rs/axum/latest/axum/extract/struct.DefaultBodyLimit.html) |
