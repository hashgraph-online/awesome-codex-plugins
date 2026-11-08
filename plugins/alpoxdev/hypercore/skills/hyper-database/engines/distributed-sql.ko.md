# 분산·서버리스 SQL 플랫폼

와이어 프로토콜 엔진의 동작을 바꾸는 플랫폼의 엔진 가이드입니다. Vitess와 PlanetScale, CockroachDB, TiDB, Neon, Supabase, Turso와 libSQL, Cloudflare D1을 다룹니다. 와이어 프로토콜 가이드(`engines/postgres.md`, `engines/mysql.md`, `engines/sqlite.md`)를 먼저 읽고, 그다음 감지한 플랫폼 절만 읽습니다. 발견 사항은 `DS-*` ID를 인용합니다.

> 자주 바뀝니다. 아래 플랫폼 제한, 기본값, 라이선스는 2026-11-07에 각 벤더 문서에서 확인했습니다. 설계가 어떤 수치에 달려 있으면 실제 페이지를 다시 확인합니다.

## 1. Vitess와 PlanetScale(MySQL)

| ID | Severity | Rule |
|---|---|---|
| DS-VT-01 | high | 외래 키 제약은 샤딩되지 않은 키스페이스에서만 동작하고 PlanetScale에서는 데이터베이스별로 기본이 꺼져 있습니다. 샤딩할 스키마는 참조 무결성을 애플리케이션에서 유지하며, 조인에 필요한 인덱스와 배치 고아 검사를 갖춥니다. |
| DS-VT-02 | high | 모든 테이블에 null이 아닌 유일 키가 필요합니다. 무중단 스키마 변경이 이 키로 행을 복사합니다. |
| DS-VT-03 | high | safe migrations가 켜져 있으면(운영 표준) 직접 DDL이 거부됩니다. 변경은 브랜치에서 deploy request로 갑니다. 롤백은 `down` 마이그레이션이 아니라 배포 후 30분 되돌리기 창을 중심으로 계획합니다. |
| DS-VT-04 | high | instant 배포는 되돌릴 수 없고 테이블의 잠금을 잡은 쿼리를 종료합니다. 둘 다 받아들일 수 있는 곳에만 씁니다. |
| DS-VT-05 | medium | 개발 브랜치는 스키마만 복사하고 데이터는 복사하지 않습니다. 데이터에 의존하는 마이그레이션(백필, 새 유일 키)은 복구한 데이터에서 예행합니다. |
| DS-VT-06 | medium | 이식하기 전에 지원하지 않는 MySQL 기능을 확인합니다. 저장 프로그램, `LOCK TABLES`, 일부 재귀 쿼리와 `JSON_TABLE` 쿼리입니다. 전역 시간대는 UTC입니다. |
| DS-VT-07 | medium | 샤딩 키(Vindex)는 지배적인 접근 패턴에서 고릅니다. 그것이 없는 쿼리는 모든 샤드로 흩어집니다. |

PlanetScale은 PostgreSQL 제품도 운영합니다. 이 절의 규칙은 그중 Vitess(MySQL) 제품에만 적용됩니다.

## 2. CockroachDB

| ID | Severity | Rule |
|---|---|---|
| DS-CR-01 | high | 기본 격리는 `SERIALIZABLE`입니다. 경합을 볼 수 있는 모든 트랜잭션은 SQLSTATE `40001`(메시지가 `restart transaction`으로 시작)에 상한이 있는 백오프로 재시도합니다. 커밋 마감 시한에 실패한 트랜잭션은 재시도하지 말고 줄입니다. |
| DS-CR-02 | high | 큰 테이블의 키를 단조 증가하는 `INT`/`SERIAL`이나 타임스탬프로 잡지 않습니다. 단일 범위 핫스폿이 생깁니다. 무작위 UUID, 분포가 고른 컬럼을 앞세운 복합 키, 또는 순차 컬럼에 해시 샤딩 인덱스(`USING HASH`)를 씁니다. |
| DS-CR-03 | medium | CockroachDB 문서는 UUIDv4를 권하고 다른 UUID 버전은 대체로 검증되지 않았다고 말합니다. 이 엔진에서는 이 권고가 일반적인 UUIDv7 선호(DM-12)를 덮어씁니다. |
| DS-CR-04 | medium | `READ COMMITTED`가 있지만 갱신 손실을 막지 못합니다. 성능을 위한 반사적 선택으로 바꾸지 않습니다. |
| DS-CR-05 | medium | 큰 삽입과 삭제는 배치로 처리하고 만료에는 행 수준 TTL을 씁니다. |
| DS-CR-06 | high | 자체 호스팅 CockroachDB는 2024년 라이선스 변경 이후 CockroachDB Software License에 따른 소스 공개 방식이고, 무료 Core 에디션은 폐지되었습니다. 선택하기 전에 라이선스 조건과 텔레메트리 요구 사항을 확인합니다. |

## 3. TiDB

| ID | Severity | Rule |
|---|---|---|
| DS-TI-01 | high | 쓰기 부하가 큰 테이블에서는 `AUTO_INCREMENT` 기본 키를 피합니다(핫스폿). `AUTO_RANDOM`을 씁니다. 자동 증가 값은 유일하지만 서버별 배치로 할당되므로 빈틈이 없거나 정렬되어 있다고 절대 가정하지 않습니다. |

## 4. Neon(PostgreSQL)

| ID | Severity | Rule |
|---|---|---|
| DS-NE-01 | high | 서버리스와 엣지 코드는 풀링 연결 문자열(트랜잭션 모드의 PgBouncer)을 씁니다. 마이그레이션, `pg_dump`, 논리 복제, `LISTEN`, 세션 `SET`, SQL 수준 `PREPARE`는 직접 연결을 씁니다. |
| DS-NE-02 | medium | 커넥션 풀러의 클라이언트 연결 10,000개는 슬롯이지 동시성이 아닙니다. 실제 동시성은 컴퓨트 크기에 따라 달라지는 `max_connections`로 제한되고, 사용자와 데이터베이스 풀마다 별도입니다. |
| DS-NE-03 | medium | 컴퓨트는 기본적으로 5분 유휴 후 0으로 줄고 수백 밀리초에 깨어납니다. 클라이언트는 연결 시간 제한을 설정하고 첫 쿼리를 재시도합니다. |
| DS-NE-04 | medium | 브랜치는 데이터를 포함한 copy-on-write 복제본입니다. 프리뷰나 테스트 실행마다 하나씩 쓰고 삭제합니다. 특정 시점 복구는 설정된 이력 창으로 제한되므로 필요해지기 전에 설정합니다. |

## 5. Supabase(PostgreSQL)

| ID | Severity | Rule |
|---|---|---|
| DS-SB-01 | critical | 노출된 스키마의 모든 테이블에 행 수준 보안(RLS)을 켭니다. 그곳에서 RLS가 없는 테이블은 권한이 있는 어떤 역할이든 읽고 쓸 수 있습니다. 필요 없는 기본 권한은 `anon`과 `authenticated`에서 회수합니다. |
| DS-SB-02 | high | 동작마다 정책 하나를 씁니다. `UPDATE` 정책에는 사용자가 소유권을 바꾸지 못하도록 `WITH CHECK`가 필요하고, `UPDATE`는 행을 맞추기 위해 `SELECT` 정책도 필요합니다. |
| DS-SB-03 | high | 뷰는 `security_invoker = true`로 만들지 않으면 RLS를 우회합니다. |
| DS-SB-04 | critical | `service_role` 키는 RLS를 우회합니다. 서버 측에만 둡니다. |
| DS-SB-05 | medium | 정책은 `using ((select auth.uid()) = user_id)` 형태로 써서 함수가 문마다 한 번만 평가되게 하고, 정책 컬럼에 인덱스를 만듭니다. |
| DS-SB-06 | high | 공유 커넥션 풀러의 트랜잭션 모드는 준비된 문(prepared statement)을 지원하지 않습니다. 서버리스 클라이언트는 트랜잭션 커넥션 풀러에 `prepare: false`와 인스턴스당 하나의 풀을 씁니다. 직접, 세션, 풀링 백엔드는 플랫폼 자체 서비스와 `max_connections` 예산 하나를 공유합니다. |
| DS-SB-07 | medium | 데이터베이스 테스트 스위트에서 역할마다 정책을 시험합니다(모든 동작에 허용과 거부). |

## 6. Turso, libSQL, Cloudflare D1(SQLite)

| ID | Severity | Rule |
|---|---|---|
| DS-D1-01 | high | D1 데이터베이스 하나는 쿼리를 한 번에 하나씩 처리합니다. 처리량은 대략 쿼리 시간의 역수입니다. 작은 데이터베이스를 많이 두는 방식(테넌트별 또는 사용자별)으로 확장하며, 이는 마이그레이션을 모든 데이터베이스에 실행한다는 뜻입니다. |
| DS-D1-02 | high | D1의 데이터베이스별 제한(크기, 행 크기, 문 크기, 바인딩 파라미터, 쿼리 시간) 안에서 설계합니다. 현재 제한 페이지를 확인합니다. 대량 갱신과 삭제는 약 천 행 단위 배치로 나눕니다. |
| DS-D1-03 | medium | 여러 문이 필요한 작업에는 `db.batch()`를 씁니다. 읽기 복제본은 Sessions API로만 읽기를 처리합니다. |
| DS-TU-01 | medium | Turso 내장 복제본은 로컬에서 읽고 원격 프라이머리에 씁니다. `sync()` 전에는 쓰기 주체만 자기 쓰기를 읽습니다. 복제본 파일을 동기화 중에 열지 않습니다. |
| DS-TU-02 | medium | 호스팅 Turso는 `PRAGMA user_version`을 읽기 전용으로 다루고 일부 저널 프라그마를 무시합니다. 마이그레이션은 테이블로 추적합니다. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Vitess 외래 키는 샤딩되지 않은 키스페이스에서만 동작 | <https://planetscale.com/docs/vitess/foreign-key-constraints> |
| null이 아닌 유일 키 요구, 지원하지 않는 기능, UTC 시간대 | <https://planetscale.com/docs/vitess/troubleshooting/mysql-compatibility> |
| safe migrations가 직접 DDL을 거부 | <https://planetscale.com/docs/vitess/schema-changes/safe-migrations> |
| deploy request, 30분 되돌리기 창, instant 배포 | <https://planetscale.com/docs/vitess/schema-changes/deploy-requests> |
| 브랜치는 스키마만 복사 | <https://planetscale.com/docs/vitess/schema-changes/branching> |
| CockroachDB 기본 `SERIALIZABLE`과 `READ COMMITTED` 동작 | <https://docs.cockroachlabs.com/docs/stable/read-committed> |
| 재시도 오류가 SQLSTATE `40001`을 씀 | <https://docs.cockroachlabs.com/docs/stable/transaction-retry-error-reference> |
| 순차 키가 핫스폿을 만듦, UUIDv4 권고, 배치와 TTL | <https://docs.cockroachlabs.com/docs/stable/performance-best-practices-overview> |
| 해시 샤딩 인덱스 | <https://docs.cockroachlabs.com/docs/stable/hash-sharded-indexes> |
| CockroachDB 라이선스 변경과 Core 폐지 | <https://www.cockroachlabs.com/blog/enterprise-license-announcement/>, <https://docs.cockroachlabs.com/docs/stable/licensing-faqs> |
| TiDB `AUTO_INCREMENT` 핫스폿, `AUTO_RANDOM`, 배치 할당 | <https://docs.pingcap.com/tidb/stable/auto-increment/> |
| Neon 트랜잭션 모드 풀링, 직접 연결 사례, 연결 제한 | <https://neon.com/docs/connect/connection-pooling> |
| Neon 5분 후 0으로 축소 | <https://neon.com/docs/introduction/scale-to-zero> |
| Neon 브랜치와 이력 창 | <https://neon.com/docs/introduction/branching> |
| Supabase RLS 규칙, 뷰, `service_role`, `auth.uid()` 형태 | <https://supabase.com/docs/guides/database/postgres/row-level-security> |
| Supabase 커넥션 풀러, 준비된 문, 공유 연결 예산 | <https://supabase.com/docs/guides/database/connecting-to-postgres>, <https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits> |
| D1 단일 스레드 데이터베이스와 제한 | <https://developers.cloudflare.com/d1/platform/limits/> |
| D1 Sessions API를 통한 읽기 복제 | <https://developers.cloudflare.com/d1/best-practices/read-replication/> |
| Turso 내장 복제본과 호스팅 제한 | <https://docs.turso.tech/features/embedded-replicas/introduction> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
