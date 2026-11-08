# 테스트

> 라우터는 포트 없이 테스트하고 영속성은 실제 데이터베이스로 테스트합니다

---
## 안정 기준선

2026-11-05에 확인한 대로 `tower` 0.5는 `util` 기능 뒤에서 `ServiceExt::oneshot(self, req)`를 제공하고, `axum-test` 21.1.0은 요청 builder가 있는 `TestServer::new(app)`을 제공합니다. `oneshot`은 서비스를 소비하므로 요청 하나짜리 테스트 도우미입니다. 테스트 상태에서 라우터가 값싸게 `Clone`되지 않으면 요청마다 새 라우터를 만듭니다.

- 상태 코드, 헤더, 본문, layer, extractor 동작은 `oneshot`으로 라우터를 직접 테스트합니다. 포트도, 경쟁도, 대기도 없습니다.
- 테스트에 쿠키, multipart, 유창한 요청 builder가 필요하면 `axum-test` `TestServer`를 씁니다.
- repository 테스트에는 실제 데이터베이스를 쓰고, 이상적으로는 끝에 롤백하는 트랜잭션이나 테스트마다 격리된 스키마를 씁니다. 테스트를 운영 데이터로 향하게 하지 않습니다.
- 저장소가 이미 SQLx 테스트 매크로를 쓰면 `#[sqlx::test]`를 씁니다. 아니면 fixture에서 일회용 데이터베이스를 마이그레이션합니다.
- 성공 경로만이 아니라 오류 봉투, 검증 실패, 변경한 성공 경로를 덮습니다.
- OpenAPI 게시가 계약의 일부이면 문서화한 공개 라우트 계열마다 통합 테스트를 하나 유지합니다.
- 필드 수준 단언으로 충분한데 직렬화된 본문 전체를 단언하지 않습니다. 지나치게 구체적인 테스트는 무관한 변경에서 깨집니다.
- 프레임워크 배선(등록했으니 라우트가 존재함)을 테스트하지 않습니다. API가 약속한 동작을 테스트합니다.

## 핵심 규칙

테스트는 운영이 쓰는 같은 조립 함수를 테스트 상태로 실행하고 관찰 가능한 HTTP 동작을 단언합니다.

## 라우터 테스트 패턴

```rust
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use http_body_util::BodyExt;
use tower::ServiceExt;

#[tokio::test]
async fn returns_404_envelope() {
    let app = crate::app(crate::state::test_state()).await;

    let response = app
        .oneshot(
            Request::builder()
                .uri("/missing")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);

    let body = response.into_body().collect().await.unwrap().to_bytes();
    let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
    assert_eq!(json["code"], "not_found");
}
```

## axum-test 패턴

```rust
use axum_test::TestServer;

#[tokio::test]
async fn creates_a_user() {
    let server = TestServer::new(crate::app(crate::state::test_state()).await).unwrap();

    let response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({ "email": "a@example.com", "name": "A" }))
        .await;

    response.assert_status_created();
    let body: serde_json::Value = response.json();
    assert_eq!(body["email"], "a@example.com");
}
```

`TestResponse`의 메서드 이름은 설치된 버전에 따라 다릅니다. `assert_status_created`가 있다고 가정하지 말고 현재 API를 확인합니다.

## 데이터베이스 테스트 패턴

```rust
#[sqlx::test]
async fn repository_finds_user(pool: sqlx::PgPool) -> sqlx::Result<()> {
    sqlx::query("INSERT INTO users (id, email) VALUES ($1, $2)")
        .bind(uuid::Uuid::new_v4())
        .bind("a@example.com")
        .execute(&pool)
        .await?;

    let repo = crate::repositories::users::UsersRepository::new(pool);
    let found = repo.find_by_email("a@example.com").await?;

    assert!(found.is_some());
    Ok(())
}
```

`#[sqlx::test]`는 crate의 테스트 설정에 따라 테스트마다 테스트 데이터베이스를 준비하고 마이그레이션합니다. 의존하기 전에 저장소에서 그 설정을 확인합니다.

## 검토 체크리스트

- 변경한 동작에 service 함수만이 아니라 라우터를 통과하는 테스트가 있습니다.
- 테스트가 운영이 쓰는 같은 조립 함수를 씁니다.
- layer와 extractor를 우회하지 않고 실행합니다.
- 오류와 검증 경로에 각각 테스트가 하나 이상 있습니다.
- 데이터베이스 테스트가 격리되어 있고 운영을 가리키지 않습니다.
- 테스트가 벽시계 대기나 고정 포트에 의존하지 않습니다.
- 단언이 우발적인 직렬화 순서가 아니라 안정적인 계약 필드를 겨냥합니다.
- 건드린 crate에서 `cargo test`가 통과하고, 무시한 테스트가 있으면 보고합니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| `ServiceExt::oneshot`, `util` 기능, 한 번 소비 의미 | [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html) |
| `TestServer`, 직접 디스패치 또는 임의 포트, 요청·응답 흐름 | [axum-test](https://docs.rs/axum-test/latest/axum_test/) |
| 단언을 위한 본문 수집 | [http-body-util](https://docs.rs/http-body-util/latest/http_body_util/trait.BodyExt.html) |
| `#[sqlx::test]` 매크로 | [sqlx::test](https://docs.rs/sqlx/latest/sqlx/attr.test.html) |
