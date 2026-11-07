# 데이터베이스와 SQLx 경계

> 영속성은 repository 뒤에 두고 풀은 한 번 부트스트랩해 공유합니다

---
## 안정 SQLx 기준선

2026-11-05에 확인한 대로 `sqlx`는 0.9.0이고 MSRV는 1.94입니다. 0.9 계열은 예전의 결합된 이름 대신 런타임과 TLS 기능을 분리하고(`runtime-tokio`, `tls-rustls`, `tls-native-tls`), 선택적 `sqlx.toml` 설정 파일을 추가하며, 쿼리 함수가 `impl SqlSafeStr`을 받도록 바꿉니다. 따라서 동적으로 만든 쿼리에는 `AssertSqlSafe`가 필요합니다. 저장소는 `launchbadge` 조직에서 `transact-rs`로 옮겼고 옛 링크는 리디렉션됩니다.

- 영속 코드를 바꾸기 전에 `Cargo.toml`, `Cargo.lock`, 풀 builder, 쿼리 방식, 마이그레이션 디렉터리, `.sqlx/` 존재 여부, `DATABASE_URL` 출처를 확인합니다.
- crate마다 쿼리 모드를 한 번 정합니다. `DATABASE_URL`이나 커밋한 `.sqlx` 데이터를 쓰는 컴파일 시점 검사 매크로(`query!`, `query_as!`) 또는 명시적 행 매핑을 쓰는 런타임 검사 `query`/`query_as`입니다. 조용히 섞지 않습니다.
- 0.9.0 소스에서 기본 `max_connections`는 10이고 기본 `acquire_timeout`은 30초입니다. 이 값은 렌더링된 문서에 적혀 있지 않으므로 보고할 때 소스에서 확인한 값이라고 밝힙니다.
- 행이 없는 것은 인프라 실패가 아닙니다. `sqlx::Error::RowNotFound`는 보통 `404`로 의도적으로 매핑합니다.
- 풀은 부트스트랩에서 한 번 만들고 `AppState`에 둡니다. `Pool` 복제는 참조 카운트 핸들이라 저렴하지만, 요청마다 연결하는 것은 그렇지 않습니다.
- 마이그레이션은 커밋하고 불변으로 유지합니다. 적용한 마이그레이션을 수정하거나 로컬 상태를 통과시키려고 이력을 다시 번호 매기지 않습니다.
- 계약에 필요한 열만 선택하고 DTO로 매핑합니다. 페이지네이션 경계를 검증하고 정렬을 결정적으로 만듭니다.
- 제약 조건, not-found와 conflict 매핑, 롤백 동작, 시작 시 풀 생명주기를 테스트합니다.

## 핵심 규칙

handler는 전송 관심사만 소유합니다. 추출, 검증, service 호출, 응답 구성입니다. service는 유스케이스 오케스트레이션을 소유합니다. repository는 쿼리를 소유합니다. 데이터베이스 경계는 풀 생성, 쿼리 메타데이터, 마이그레이션을 소유합니다.

handler가 `sqlx::query!`, `PgPool`, `SqlitePool`, `MySqlPool`, `sqlx::migrate!`를 직접 import하면 경계 위반입니다. 사용자가 공식 기본값이나 아주 작은 개념 증명을 명시적으로 요청한 경우는 예외입니다.

## 승인된 배치

```text
src/
├── db/
│   ├── mod.rs
│   └── pool.rs              # 풀 생성과 연결 옵션
├── repositories/
│   └── users.rs             # 쿼리, 행 매핑, axum 타입 없음
├── services/
│   └── users.rs             # 트랜잭션, repository 간 워크플로
├── routes/
│   └── users/
│       ├── handlers.rs
│       └── dto.rs
└── main.rs                  # 풀을 만들고 app(state)를 호출

migrations/
└── 20260101000000_create_users.sql
.sqlx/                       # 컴파일 시점 쿼리를 쓰면 커밋
```

- `db/pool.rs`는 타입이 있는 설정으로 풀을 만들고 연결 옵션을 아는 유일한 곳입니다.
- `repositories/<domain>.rs`는 SQL을 소유하고 행을 도메인이나 DTO 모양으로 매핑합니다.
- `services/<domain>.rs`는 트랜잭션 경계와 비즈니스 결정을 소유합니다.
- `routes/<domain>/`은 풀, 쿼리 매크로, 마이그레이션을 import하면 안 됩니다.

## 풀 생성

```rust
use std::time::Duration;

use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;

pub async fn connect(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(10)
        .min_connections(1)
        .acquire_timeout(Duration::from_secs(5))
        .connect(database_url)
        .await
}
```

- URL은 handler가 아니라 타입이 있는 설정에서 읽습니다.
- `acquire_timeout`은 요청 타임아웃보다 짧게 설정해, 포화된 풀이 요청을 매다는 대신 빠르고 의도한 오류를 내게 합니다.
- 시작이 데이터베이스에서 블록되면 안 될 때만 `connect_lazy`를 쓰고 실패 모드를 문서화합니다.
- 연결 문자열을 절대 로그에 남기지 않습니다. 보통 자격 증명이 들어 있습니다.

## 쿼리 모드

| 모드 | 사용 시점 | 요구 사항 |
|---|---|---|
| `query!` / `query_as!` | 팀이 컴파일 시점 SQL 검사를 원함 | 빌드 시점 `DATABASE_URL` 또는 커밋한 `.sqlx` 데이터, 문자열 리터럴 SQL |
| `sqlx::query` / `query_as` | 동적 필터, 런타임 생성 SQL, CI에 데이터베이스가 없음 | 수동 행 매핑, 사용자 입력을 SQL에 절대 보간하지 않음 |
| `FromRow`와 함께 쓰는 `sqlx::query_as::<_, T>` | 안정적인 도메인 행 타입이 있음 | 열 이름이 필드와 일치해야 함 |
| `AnyPool` | 드라이버를 런타임에 골라야 함 | 줄어든 타입 범위를 감수, 애플리케이션 코드에서는 드묾 |

오프라인 모드:

1. `cargo install sqlx-cli`
2. `DATABASE_URL`을 설정하고 데이터베이스를 마이그레이션한 상태에서 `cargo sqlx prepare`(또는 `--workspace`)
3. `.sqlx/` 커밋
4. `DATABASE_URL` 없이 빌드하고, 값이 남아 있을 수 있으면 `SQLX_OFFLINE=true` 설정
5. CI를 `cargo sqlx prepare --check`로 게이트

0.9에서 `sqlx::query`는 `impl SqlSafeStr`을 받고, 이것은 `&'static str`과 `AssertSqlSafe`에 구현되어 있습니다. 런타임 생성 쿼리는 의도적으로 감싸야 하며, 그 래퍼는 검토 신호이지 사용자 입력 보간 허가가 아닙니다.

## 트랜잭션

```rust
pub async fn transfer(&self, from: Uuid, to: Uuid, amount: i64) -> Result<(), AppError> {
    let mut tx = self.pool.begin().await?;

    sqlx::query("UPDATE accounts SET balance = balance - $1 WHERE id = $2")
        .bind(amount)
        .bind(from)
        .execute(&mut *tx)
        .await?;

    sqlx::query("UPDATE accounts SET balance = balance + $1 WHERE id = $2")
        .bind(amount)
        .bind(to)
        .execute(&mut *tx)
        .await?;

    tx.commit().await?;
    Ok(())
}
```

- 하나의 단위로 커밋하거나 롤백해야 하는 다단계 쓰기에는 명시적 트랜잭션을 씁니다.
- 트랜잭션 경계는 handler가 아니라 service 계층에 둡니다.
- 같은 트랜잭션에 참여하는 repository에는 `&mut *tx`나 제네릭 executor를 넘깁니다.
- 버려진 트랜잭션은 롤백됩니다. 그러나 제어 흐름을 그 동작에 기대면 의도가 숨으므로 명시적으로 커밋하거나 롤백합니다.
- 숨은 중첩 트랜잭션을 피합니다. 세이브포인트는 있지만 의도적으로 써야 합니다.

## 스키마와 마이그레이션

- `sqlx migrate add <name>`은 `migrations/<timestamp>_<name>.sql`을 만들고, `-r`은 짝을 이루는 `.up.sql`/`.down.sql` 파일을 만듭니다.
- `sqlx migrate run`은 대기 중인 마이그레이션을 적용하고, `sqlx migrate revert`는 마지막 것을 되돌립니다. 둘 다 `DATABASE_URL`이나 `--database-url`이 필요합니다.
- 저장소가 다른 출처를 설정하지 않으면 마이그레이션 디렉터리를 워크스페이스 루트에 둡니다.
- 요청 handler에서 마이그레이션을 생성, 실행, 되돌리지 않습니다.
- 라우트 변경의 일부로 테이블, 열, 인덱스, 마이그레이션 파일 이름을 자동 변경하지 않습니다.
- 스키마 변경이 공개 응답에 영향을 주면 DTO, 검증, OpenAPI 스키마, 테스트를 같은 변경에서 함께 갱신합니다.
- `sqlx.toml`이 있으면 쿼리 메타데이터, 마이그레이션 테이블 이름, 다중 데이터베이스 설정의 기준으로 삼습니다.

## DTO와 계약 경계

- 데이터베이스 행은 API DTO가 아닙니다. 명시적으로 매핑하고 내부 ID, 소프트 삭제 플래그, 감사 열, 비밀을 제외합니다.
- 영속성 변경 후 OpenAPI 스키마, 검증 DTO, 응답 타입이 서로 일치해야 합니다.
- 페이지네이션, 정렬, 필터링, 부분 선택은 쿼리 계약과 문서화된 매개변수에 속합니다.
- `sqlx::Error` 텍스트를 클라이언트에 노출하지 않고 `AppError`에서 변환합니다.

## 비준수 징후

- handler가 `sqlx::query!`, `PgPool`, `SqlitePool`, `MySqlPool`, `sqlx::migrate!`를 import합니다.
- handler가 요청마다 풀이나 연결을 만듭니다.
- repository가 `axum::extract::State`를 받거나 HTTP 응답을 만듭니다.
- 마이그레이션 파일을 생성하고 커밋하지 않았거나, 설정한 디렉터리가 존재하지 않습니다.
- service가 트랜잭션 없이 의존적인 쓰기를 여러 번 수행합니다.
- 공개 응답이 내부 필드가 있는 원시 행을 직렬화합니다.
- CI에서 `query!` 매크로를 쓰는데 `.sqlx/`가 없습니다.
- 런타임 생성 쿼리가 사용자 입력을 바인딩하지 않고 보간합니다.
- 적용한 마이그레이션을 수정하거나 번호를 다시 매겼습니다.

## 자동 수정 경계

안전한 로컬 수정:

- handler의 직접 쿼리를 해당 도메인의 기존 repository로 옮깁니다.
- 건드린 쿼리에 빠진 repository 함수를 추가합니다.
- 요청마다 만드는 풀을 공유 `AppState` 풀로 교체합니다.
- 대상 모양이 명확하면 건드린 공개 응답에 DTO 매핑을 추가합니다.
- 이미 테스트가 있는 건드린 다단계 쓰기에 명시적 트랜잭션을 추가합니다.

명시적 근거 없이 자동 적용하지 않음:

- SQLx를 다른 ORM이나 드라이버로 바꾸거나 Postgres를 다른 엔진으로 교체합니다.
- 운영 마이그레이션을 생성, 수정, 적용, 삭제합니다.
- 스키마 테이블, 열, 인덱스, 마이그레이션 폴더 이름을 변경합니다.
- 테스트 없이 트랜잭션 경계를 다시 작성합니다.
- crate 전반에 새 데이터베이스 추상화 계층을 도입합니다.

## 검토 체크리스트

- 건드린 handler가 SQLx 매크로나 풀 타입을 import하지 않습니다.
- 풀 생성이 중앙화되고 시작 시 한 번 실행됩니다.
- 설정이 handler 안의 `std::env::var`가 아니라 타입이 있는 설정에서 흐릅니다.
- repository 함수가 SQL을 숨기고 axum 타입에 의존하지 않습니다.
- 쿼리 모드가 일관되고 필요할 때 `.sqlx`가 커밋되어 있습니다.
- 다단계 쓰기에 트랜잭션이 명시되어 있습니다.
- 마이그레이션 이력이 커밋되어 있고 수정되지 않았습니다.
- DTO, OpenAPI 스키마, 응답 타입이 일치합니다.
- 영속 동작이 가장 작은 유용한 repository, service, 요청 수준 테스트로 덮여 있습니다.

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| SQLx 0.9.0 MSRV 1.94, 런타임과 TLS 기능 분리, `SqlSafeStr`와 `AssertSqlSafe`, `sqlx.toml` | [SQLx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md) |
| 풀 동작, `acquire_timeout`, `max_connections`, 저렴한 복제 | [Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html), [PoolOptions](https://docs.rs/sqlx/latest/sqlx/self/struct.PoolOptions.html), [v0.9.0 options source](https://github.com/transact-rs/sqlx/blob/v0.9.0/sqlx-core/src/pool/options.rs) |
| `query!`와 `query_as!`의 컴파일 시점 검사, `DATABASE_URL`, 오프라인 모드 | [query!](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [query_as!](https://docs.rs/sqlx/latest/sqlx/macro.query_as.html) |
| 마이그레이션 이름 규칙, `migrate run`/`revert`, `prepare --check`, CLI 기능 이름 | [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli) |
| 트랜잭션 begin/commit/rollback과 `&mut *tx` executor | [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html) |
