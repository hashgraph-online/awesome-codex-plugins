# 코드 규약

> Rust 프로젝트 코딩 규칙

---
## 안정 호환 규칙

서식과 lint 수준은 프로젝트 도구가 소유합니다. `rustfmt`와 `clippy`는 대부분 Rust 저장소의 기준선이지만 정확한 lint 집합은 프로젝트 결정입니다. 아래 이름 규칙은 대부분 항목에서 언어가 강제하고 모듈 파일에서는 이 스킬이 강제하며, 그 이상의 보편적 프레임워크 요구 사항은 아닙니다.

- 스타일을 강제하기 전에 `rustfmt.toml`, `clippy.toml`, 워크스페이스 lint 설정, edition, MSRV, 기존 모듈 스타일을 확인합니다.
- 타입 추론과 명시적 공개 시그니처를 보존합니다. 스타일 선호를 만족시키려고 광범위한 `dyn`이나 boxed 오류를 추가하지 않습니다.
- 경계에서는 `unknown`에 해당하는 안전한 타입을 선호합니다. `serde_json::Value`보다 타입이 있는 DTO, 읽기 전용 매개변수에서 `String`보다 `&str`입니다.
- 생성 코드, SQLx 오프라인 메타데이터, 마이그레이션 파일은 소유 도구와 저장소 워크플로가 명시적으로 허용하지 않는 한 손으로 편집하지 않습니다.
- 모듈 이름 변경은 동작 변경입니다. `mod` 선언, `use` 경로, 테스트, 설정을 같은 변경에서 갱신합니다.

## 모듈과 파일 이름

> Rust 모듈 파일은 `snake_case`입니다. TypeScript 스택이 쓰는 kebab-case 규칙이 아니라 컴파일러 lint가 강제하는 언어 규약입니다.

| 유형 | 규칙 | 예 |
|------|------|---------|
| 모듈과 파일 | `snake_case` | `user_profile.rs`, `request_id.rs` |
| 디렉터리 | `snake_case` | `routes/`, `services/`, `repositories/` |
| 타입과 trait | `CamelCase` | `AppState`, `UserRepository` |
| 함수와 메서드 | `snake_case` | `create_user`, `find_by_email` |
| 상수와 static | `SCREAMING_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| crate 이름 | `snake_case` | `api`, `persistence` |

허용되는 예외:

- `Cargo.toml`, `Cargo.lock`, `rustfmt.toml`, `clippy.toml`, `build.rs`처럼 도구가 요구하는 루트 파일
- SQLx가 소유하는 생성 파일과 마이그레이션 산출물
- 이름을 바꾸면 공개 crate API가 깨지는 기존 모듈 이름

`전체 수정` 모드에서는 모든 `mod` 선언, import, 테스트 경로, 설정 참조를 같은 변경에서 갱신할 수 있을 때 모든 모듈 파일을 훑고 `camelCase`나 `kebab-case` 위반을 `snake_case`로 바꿉니다.

---

## Rust 규칙

| 규칙 | 설명 | 예 |
|---|---|---|
| 오류 타입 | `thiserror`를 쓰는 애플리케이션 오류 enum 하나 | `#[derive(thiserror::Error)] pub enum AppError` |
| 물음표 연산자 | `?`와 `From` 변환으로 전파 | `let user = repo.get(id).await?;` |
| 입력에 패닉 없음 | 요청에서 나온 값에 `unwrap()`/`expect()` 없음 | `ok_or(AppError::BadRequest("missing id"))?` |
| 비동기 trait | axum 0.8 extractor에 `#[async_trait]` 없음 | `impl FromRequestParts<S> for Auth` |
| 공유 상태 | 작업 간 공유할 때만 `Arc`, `AppState`는 `Clone` | `#[derive(Clone)] pub struct AppState` |
| 잠금 | `.await`를 넘어 `std::sync::Mutex`를 잡지 않고, 필요하면 `tokio::sync::Mutex` 사용 | `let guard = state.lock.lock().await;` |
| 로깅 | 라이브러리와 handler에서 `println!`이 아니라 `tracing` 매크로 | `tracing::warn!(%id, "not found")` |
| 공개 문서 | 자명하지 않은 공개 항목에 `///` | `/// Returns the user or `AppError::NotFound`.` |
| 가시성 | 모듈은 기본적으로 비공개로 두고 조립 함수와 공개 계약만 노출 | 외부 사용을 의도하지 않았으면 `pub(crate)` |
| 기능 플래그 | 의존성이나 빌드 비용을 바꿀 때만 기능을 추가하고 문서화 | `[features] default = []` |

---

## Import 순서

```rust
use std::sync::Arc;

use axum::{extract::State, Json};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;

use crate::error::AppError;
use crate::repositories::users::UsersRepository;
use crate::state::AppState;

use super::dto::CreateUser;
```

표준 라이브러리, 외부 crate, crate 상대 경로, 로컬 `super`/`self` 순으로 묶습니다. 빈 줄 정책은 `rustfmt`와 프로젝트의 import 설정에 맡기고 formatter와 다투지 않습니다.

---

## 주석 스타일

- 코드 묶음에 방향이 필요할 때만 짧은 블록 주석을 선호합니다.
- 줄마다 설명을 덧붙이지 않습니다.
- 주석은 오래가고 아키텍처를 향하게 유지합니다. 작업, 티켓, 에이전트를 참조하지 않습니다.
- 순서나 트랜잭션 가정처럼 타입 시스템이 표현할 수 없는 불변 조건을 문서화합니다.

## Sources

> Checked 2026-11-05. 이 파일은 이 패키지 자체 참조 밖의 외부 출처를 근거로 삼지 않았습니다. 공식 axum 동작은 [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md)에 위임했고 2026-11-05에 확인했습니다.

| Claim | Source |
|---|---|
| Rust 이름 규칙과 모듈 파일 규칙 | [Rust API guidelines](https://rust-lang.github.io/api-guidelines/naming.html) |
| 프로젝트 도구로서의 `rustfmt`와 `clippy` | [rustfmt](https://rust-lang.github.io/rustfmt/), [clippy](https://doc.rust-lang.org/clippy/) |
| `thiserror` 2.0 derive | [thiserror](https://docs.rs/thiserror/latest/thiserror/) |
