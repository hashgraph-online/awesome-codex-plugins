# SQLx 공식 문서 요약

last_verified_at: 2026-11-05

## 목차

- 안정 버전 패키지 현황
- 공식 문서에서 확인한 사항
- 쿼리와 오프라인 모드
- 마이그레이션과 트랜잭션
- 이 스킬에 미치는 영향
- 출처

## 안정 버전 패키지 현황

2026-11-05에 crates.io, docs.rs, SQLx 체인지로그에서 확인했습니다.

| 패키지 | 안정 버전 | 비고 |
|---|---:|---|
| `sqlx` | 0.9.0 | MSRV 1.94, 런타임과 TLS 기능이 분리됨, 선택형 `sqlx-toml` 기능 |
| `sqlx-cli` | 0.9.x | `prepare`, `migrate`, `database` 하위 명령, CLI TLS 기능 이름은 `rustls`/`native-tls` |

업스트림 저장소가 `launchbadge/sqlx`에서 `transact-rs/sqlx`로 옮겨졌습니다. 예전 링크는 리다이렉트됩니다.

## 공식 문서에서 확인한 사항

1. 런타임 기능은 `runtime-tokio`와 `runtime-async-std`이고, TLS 기능은 `tls-rustls`(`tls-rustls-ring` 또는 `tls-rustls-aws-lc-rs` 포함)와 `tls-native-tls`입니다. 예전 버전에 있던 런타임+TLS 결합 기능 이름은 더 이상 없습니다.
출처: [sqlx docs](https://docs.rs/sqlx/latest/sqlx/), [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

2. `Pool`은 `Send + Sync + Clone`이고, 복제는 참조 계수로 처리하는 저렴한 핸들입니다. `PoolOptions`가 `max_connections`와 `acquire_timeout`을 설정합니다. 0.9.0 소스의 기본값은 연결 10개와 획득 타임아웃 30초이지만, 렌더링된 문서에는 기본값이 적혀 있지 않습니다.
출처: [Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html), [PoolOptions](https://docs.rs/sqlx/latest/sqlx/self/struct.PoolOptions.html), [v0.9.0 options source](https://github.com/transact-rs/sqlx/blob/v0.9.0/sqlx-core/src/pool/options.rs)

3. `query!`는 `DATABASE_URL`이나 커밋된 `.sqlx` 데이터를 기준으로 SQL을 컴파일 시점에 검사하고 익명 구조체를 반환합니다. `query_as!`는 명시적으로 선언한 구조체에 매핑하며 `FromRow`를 요구하지 않습니다.
출처: [query!](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [query_as!](https://docs.rs/sqlx/latest/sqlx/macro.query_as.html)

4. 0.9에서 `query*` 함수는 `impl SqlSafeStr`를 받고, 이 트레이트는 `&'static str`과 `AssertSqlSafe`에 구현되어 있습니다. 동적으로 만든 SQL은 의도적으로 감싸야 합니다.
출처: [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

5. `sqlx.toml`은 `DATABASE_URL`의 이름을 바꾸고, 타입 재정의를 설정하며, 마이그레이션 테이블 이름을 바꿀 수 있습니다. 라이브러리는 `sqlx-toml` 기능을 기본으로 켜지 않지만 CLI는 켭니다.
출처: [sqlx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md)

6. 트랜잭션은 `Pool::begin`이나 `Connection::begin`으로 시작하고 `commit`이나 `rollback`으로 끝나며, 드롭되면 롤백됩니다. `&mut *tx`는 트랜잭션 안에서 쓰는 실행기 형태입니다.
출처: [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html)

## 쿼리와 오프라인 모드

1. `cargo install sqlx-cli`
2. `DATABASE_URL`을 설정하고 데이터베이스를 마이그레이션한 상태에서 `cargo sqlx prepare` 또는 `cargo sqlx prepare --workspace`를 실행합니다.
3. `.sqlx/`를 커밋합니다.
4. `DATABASE_URL` 없이 빌드합니다. 값이 남아 있을 수 있으면 `SQLX_OFFLINE=true`를 씁니다.
5. CI에서 `cargo sqlx prepare --check`로 검사합니다.

출처: [query! offline mode](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli)

## 마이그레이션과 트랜잭션

- `sqlx migrate add <name>`은 `migrations/<timestamp>_<name>.sql`을 만듭니다.
- `sqlx migrate add -r <name>`은 짝을 이루는 `.up.sql`과 `.down.sql` 파일을 만듭니다.
- `sqlx migrate run`은 대기 중인 마이그레이션을 적용하고, `sqlx migrate revert`는 마지막 마이그레이션을 되돌립니다.
- `sqlx migrate info`는 적용된 상태와 대기 중인 상태를 보고합니다.
- 드롭된 트랜잭션은 롤백되지만, `commit`/`rollback`을 명시하면 의도가 드러납니다.

출처: [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli), [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html)

## 이 스킬에 미치는 영향

- 이 스킬은 시작할 때 한 번 만드는 풀, 크레이트마다 하나의 쿼리 모드, 커밋된 마이그레이션 이력을 요구합니다.
- 0.9의 기능 이름 변경 때문에 예전 `runtime-tokio-native-tls` 줄을 그대로 복사해 온 경우는 선호 문제가 아니라 발견한 문제로 다룹니다.
- `AssertSqlSafe`는 동적 SQL을 드러내기 위해 존재하므로 검토 표시로 다룹니다.

## Sources
> Checked 2026-11-05.
| 주장 | 출처 | 확인일 |
|---|---|---|
| 0.9.0 변경, MSRV, 기능 분리, `AssertSqlSafe`, `sqlx.toml` | <https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md> | 2026-11-05 |
| Pool과 `PoolOptions` 동작 | <https://docs.rs/sqlx/latest/sqlx/struct.Pool.html> | 2026-11-05 |
| 컴파일 시점 쿼리 매크로와 오프라인 모드 | <https://docs.rs/sqlx/latest/sqlx/macro.query.html> | 2026-11-05 |
| 마이그레이션 명령과 이름 규칙 | <https://github.com/transact-rs/sqlx/tree/main/sqlx-cli> | 2026-11-05 |
| 트랜잭션 생명주기 | <https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html> | 2026-11-05 |
