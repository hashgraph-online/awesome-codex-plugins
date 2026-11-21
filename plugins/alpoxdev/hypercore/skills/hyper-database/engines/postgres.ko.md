# PostgreSQL

PostgreSQL 엔진 가이드입니다. 자체 호스팅과 매니지드(RDS, Cloud SQL, Azure, Neon, Supabase, PlanetScale Postgres 등)를 모두 다루며 pgvector, PostGIS, TimescaleDB를 포함합니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤, 모드가 필요로 하는 엔진 중립 규칙과 함께 읽습니다. 발견 사항은 `PG-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 <https://www.postgresql.org/support/versioning/>에서 확인했습니다. 업그레이드나 지원 종료 결정이 이 내용에 달려 있으면 실제 페이지를 다시 확인합니다.

| Fact | Value |
|---|---|
| 지원 기간 | 각 메이저 버전은 첫 릴리스 후 5년 동안 지원합니다 |
| 현재 메이저 | 18(첫 릴리스 2025-09-25, 현재 마이너 18.6). 19는 2026-10-15에 RC 1이었습니다 |
| 곧 지원 종료 | 14의 최종 릴리스는 2026-11-12이고 13 이하는 지원되지 않습니다 |
| 권고를 바꾸는 PostgreSQL 18 추가 사항 | `uuidv7()`; 가상 생성 컬럼(virtual generated column)이 기본; 비동기 I/O(`io_method`); B-tree 스킵 스캔; `NOT NULL` 제약을 `NOT VALID`로 추가 가능; `CHECK`와 외래 키에 `NOT ENFORCED` 사용 가능; `initdb`가 데이터 체크섬을 기본으로 활성화; `pg_upgrade`가 옵티마이저 통계를 유지; MD5 비밀번호는 폐기 예정 |

## 2. 타입과 키

| ID | Severity | Rule |
|---|---|---|
| PG-TYP-01 | medium | 정수 키에는 `serial`(소유 시퀀스의 특이 동작, 권한과 덤프의 예외 상황)이 아니라 `bigint GENERATED ALWAYS AS IDENTITY`를 씁니다. |
| PG-TYP-02 | medium | UUID 키에는 `uuid`를 씁니다. 18 이상에서 쓰기 부하가 큰 테이블은 `gen_random_uuid()` 대신 `uuidv7()`(또는 애플리케이션)으로 v7을 생성합니다. |
| PG-TYP-03 | low | `varchar(n)` 대신 `text`를 쓰고, 길이 제한이 업무 규칙이면 `CHECK (length(x) <= n)`을 붙입니다. `char(n)`은 공백을 채우므로 거의 원하지 않는 형태입니다. |
| PG-TYP-04 | high | 시점에는 `timestamptz`를 쓰고, 이벤트 시각에 시간대 없는 `timestamp`는 절대 쓰지 않습니다. |
| PG-TYP-05 | high | 금액에는 `numeric(p,s)`나 정수 최소 단위를 쓰고, `money`(로캘 의존)나 `float`은 절대 쓰지 않습니다. |
| PG-TYP-06 | medium | 저장하는 문서에는 `json`이 아니라 `jsonb`를 씁니다. GIN 인덱스(포함 관계만 필요하면 `jsonb_path_ops`)나 필터에 쓰는 추출 필드의 표현식 인덱스로 인덱싱합니다. |
| PG-TYP-07 | low | 값이 제거되거나 순서가 바뀔 수 있으면 `CREATE TYPE ... AS ENUM`보다 `CHECK`나 조회 테이블을 선호합니다. enum 값은 추가할 수 있지만 삭제할 수 없습니다. |
| PG-TYP-08 | medium | 자주 읽는 행에 큰 바이너리를 저장하지 않습니다. TOAST가 큰 값을 행 밖으로 옮기지만 넓은 행은 여전히 I/O 비용을 냅니다. 파일은 오브젝트 스토리지에 두고 키만 행에 둡니다. |

## 3. 인덱스

| ID | Severity | Rule |
|---|---|---|
| PG-IDX-01 | high | 운영 중인 테이블의 인덱스는 트랜잭션 블록 밖에서 `CREATE INDEX CONCURRENTLY` / `DROP INDEX CONCURRENTLY`로 만들고 지웁니다. 일반 `CREATE INDEX`는 완료될 때까지 쓰기를 막습니다. 동시 생성이 실패하면 `INVALID` 인덱스가 남으므로 지우고 다시 시도합니다. 파티션 부모에 대한 동시 생성은 지원되지 않습니다. 각 파티션에 동시 생성한 뒤 부모 인덱스를 `ON ONLY`로 만들고 attach합니다. |
| PG-IDX-02 | high | 조인이나 부모 삭제에 쓰는 모든 외래 키 컬럼에 인덱스를 만듭니다. PostgreSQL은 이를 자동으로 만들지 않습니다. |
| PG-IDX-03 | medium | 복합 B-tree 컬럼은 동등 조건 컬럼을 먼저 두고 범위나 정렬 컬럼을 뒤에 둡니다. 상위 N개 조회는 `ORDER BY` 방향과 맞춥니다. |
| PG-IDX-04 | medium | 뜨거운 부분집합(`WHERE status = 'active'`, `WHERE deleted_at IS NULL`)에는 부분 인덱스를, 조건부 유일성에는 부분 유일 인덱스를 씁니다. 플래너는 쿼리의 `WHERE`가 인덱스 조건자를 증명 가능하게 함의할 때만 이를 사용하며, 리터럴 자리에 파라미터를 쓴 형태(`status = $1`)는 맞지 않습니다. |
| PG-IDX-05 | medium | 커버링 인덱스 온리 스캔에는 `INCLUDE` 컬럼을 씁니다. 인덱스 온리 스캔은 최근에 vacuum된 가시성 맵이 필요합니다. |
| PG-IDX-06 | medium | 연산자에 따라 타입을 고릅니다. 동등과 범위에는 B-tree, `jsonb`·배열·전문 검색에는 GIN, 범위·기하·배제 제약에는 GiST, 시간 순으로 정렬된 아주 큰 추가 전용 테이블에는 BRIN, 순수 동등에만 hash를 씁니다. |
| PG-IDX-07 | medium | 인덱스를 지우기 전에 `pg_stat_user_indexes.idx_scan = 0`으로 업무 주기 하나를 통과하는 동안의 미사용·중복 인덱스를 찾습니다. 읽기를 처리하는 복제본에서도 확인합니다. 모든 인덱스는 쓰기마다 비용을 매기고 해당 컬럼의 HOT 갱신을 막습니다. |
| PG-IDX-08 | low | `WHERE` 절의 함수(`lower(email)`)에는 대응하는 표현식 인덱스가 필요합니다. |

## 4. 쿼리

| ID | Severity | Rule |
|---|---|---|
| PG-QRY-01 | high | 실행 계획은 일회용 복사본에서 `EXPLAIN (ANALYZE, BUFFERS)`로 읽습니다. 공용 데이터베이스에서는 일반 `EXPLAIN`을 쓰고, 쓰기를 `BEGIN; EXPLAIN ANALYZE ...; ROLLBACK;`으로 감싸는 것은 사용자의 허락이 있을 때만 합니다. 롤백은 시퀀스 증가, 밖으로 호출하는 트리거(`NOTIFY`는 보류되지만 `dblink`, 외부 테이블, HTTP 확장은 아님), 실행 중에 건 잠금을 되돌리지 않으므로 실행 전에 이를 알립니다. |
| PG-QRY-02 | medium | 계획에서 예상 행 수와 실제 행 수를 비교합니다. 10배 이상 차이는 오래된 통계(`ANALYZE`), 상관된 컬럼(`CREATE STATISTICS`), 또는 sargable하지 않은 조건자를 가리킵니다. |
| PG-QRY-03 | medium | 깊은 목록은 큰 `OFFSET`이 아니라 키셋 페이지네이션(`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT n`)으로 나눕니다. |
| PG-QRY-04 | medium | N+1 접근은 조인, `= ANY($1)` 배치 조회, 또는 ORM의 즉시 로딩으로 고칩니다. `pg_stat_statements`나 로그에서 동일한 문이 반복되는 형태로 탐지합니다. |
| PG-QRY-05 | medium | 멱등 업서트에는 `INSERT ... ON CONFLICT`를 쓰고 두 번째 읽기를 피하려고 `RETURNING`을 씁니다. 18 이상에서는 `RETURNING OLD.*, NEW.*`가 두 이미지를 모두 반환합니다. |
| PG-QRY-06 | medium | 테이블 안의 작업 큐에는 `SELECT ... FOR UPDATE SKIP LOCKED`를 쓰고 트랜잭션은 짧게 유지합니다. |
| PG-QRY-07 | low | NULL 허용 컬럼이 있는 `IN (subquery)`보다 `EXISTS`를, `NOT IN`(서브쿼리가 `NULL`을 내면 행이 하나도 나오지 않음)보다 `NOT EXISTS`를 선호합니다. |

## 5. 스키마 변경

| ID | Severity | Rule |
|---|---|---|
| PG-DDL-01 | high | 모든 마이그레이션 세션은 `SET lock_timeout = '5s'`(또는 더 낮게)와 `statement_timeout`으로 시작합니다. 대부분의 `ALTER TABLE` 형태는 `ACCESS EXCLUSIVE`를 잡고, 대기 중인 `ACCESS EXCLUSIVE` 요청은 그 테이블의 이후 모든 쿼리를 막습니다. |
| PG-DDL-02 | medium | 상수 기본값으로 컬럼을 추가하는 것은 메타데이터만 바꿉니다(11 이상). 자주 바뀌는 기본값(`now()`는 stable이라 괜찮고, `random()`이나 `gen_random_uuid()`는 volatile)은 테이블 재작성을 일으킵니다. |
| PG-DDL-03 | high | 외래 키나 `CHECK`는 `NOT VALID`로 추가하고 별도 단계에서 `VALIDATE CONSTRAINT`합니다. 검증은 더 약한 잠금(`SHARE UPDATE EXCLUSIVE`)을 잡고 쓰기를 막지 않습니다. |
| PG-DDL-04 | high | 큰 테이블에서 컬럼을 `NOT NULL`로 만들려면 18 이상에서는 `NOT NULL` 제약을 `NOT VALID`로 추가하고 검증합니다. 이전 버전에서는 `CHECK (col IS NOT NULL) NOT VALID`를 추가하고 검증한 뒤 `SET NOT NULL`(검증된 check가 증명하면 12 이상은 스캔을 건너뜀)을 하고 check를 지웁니다. |
| PG-DDL-05 | high | 큰 테이블에 유일 제약이나 기본 키 제약을 추가할 때는 유일 인덱스를 `CONCURRENTLY`로 만든 뒤 `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX`를 씁니다. |
| PG-DDL-06 | high | 컬럼 타입 변경은 보통 `ACCESS EXCLUSIVE` 아래에서 테이블과 인덱스를 재작성합니다. expand/contract(`rules/schema-changes.md` §3)를 씁니다. `varchar(n)`을 넓히거나 제한을 없애는 것은 메타데이터만 바꿉니다. |
| PG-DDL-07 | medium | `CREATE INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY`, `VACUUM`은 트랜잭션 안에서 실행할 수 없습니다. 그런 마이그레이션은 도구에서 비트랜잭션으로 표시합니다. |
| PG-DDL-08 | medium | CI에서 PostgreSQL 마이그레이션 린터(Squawk 또는 프레임워크의 동등 도구)로 마이그레이션을 검사하고, 차단 잠금 발견 사항은 high로 취급합니다. |

## 6. MVCC, Vacuum, 팽창

| ID | Severity | Rule |
|---|---|---|
| PG-OPS-01 | critical | 트랜잭션 ID 나이(`age(datfrozenxid)`, `age(relfrozenxid)`)를 감시합니다. 랩어라운드는 단일 사용자 모드로의 셧다운을 강제합니다. `autovacuum_freeze_max_age`보다 훨씬 먼저 경고합니다. |
| PG-OPS-02 | high | 오래 도는 트랜잭션과 `idle in transaction` 세션(`idle_in_transaction_session_timeout`)을 종료하거나 막습니다. 이들은 버려진 복제 슬롯과 준비된 트랜잭션처럼 클러스터 전체의 vacuum을 지연시킵니다. |
| PG-OPS-03 | medium | autovacuum을 끄지 않고 뜨거운 테이블마다 조정합니다(`autovacuum_vacuum_scale_factor`를 낮추고 `autovacuum_vacuum_cost_limit`을 높임). `pg_stat_user_tables`의 `n_dead_tup`과 `last_autovacuum`을 확인합니다. |
| PG-OPS-04 | medium | 운영 중인 테이블에 `VACUUM FULL`을 절대 쓰지 않습니다(`ACCESS EXCLUSIVE`를 잡고 테이블을 재작성함). `pg_repack`이나 expand/contract를 쓰는 재구성을 씁니다. |
| PG-OPS-05 | medium | 갱신이 많은 테이블은 `fillfactor`를 낮춰 HOT 갱신을 허용하고, 자주 바뀌는 컬럼의 인덱싱을 피합니다. |

## 7. 연결과 설정

| ID | Severity | Rule |
|---|---|---|
| PG-CFG-01 | high | 연결마다 프로세스가 하나입니다. `max_connections`는 수백 수준으로 유지하고 클라이언트가 많으면 PgBouncer나 제공자의 커넥션 풀러를 앞에 둡니다. 트랜잭션 모드에서는 세션 `SET`, 세션 어드바이저리 락, `LISTEN`, 트랜잭션을 넘는 임시 테이블을 피합니다. |
| PG-CFG-02 | medium | 전용 호스트에서는 `shared_buffers`를 RAM의 25% 근처로 시작하고 `effective_cache_size`를 50~75% 근처로 잡습니다. `work_mem`은 정렬이나 해시 노드마다 동시성만큼 곱해도 메모리를 고갈시키지 않게 정합니다. |
| PG-CFG-03 | medium | `pg_stat_statements`와 느린 문 로깅(`log_min_duration_statement`)을 켜고, 가능한 호스트에서는 `log_lock_waits`와 `auto_explain` 샘플링도 켭니다. |
| PG-CFG-04 | medium | 원본 저장소에는 `synchronous_commit = on`을 유지합니다. 끄면 충돌 시 마지막 커밋을 잃을 위험이 있고 손상은 아닙니다. |

## 8. 복제, 백업, 업그레이드

| ID | Severity | Rule |
|---|---|---|
| PG-REP-01 | high | 고가용성과 읽기 복제본에는 물리 스트리밍 복제를, 선택 테이블·버전 간 업그레이드·마이그레이션에는 논리 복제를 씁니다. `pg_stat_replication` 지연과 `pg_replication_slots`의 슬롯마다 보유한 WAL을 감시합니다. 비활성 슬롯은 디스크를 채웁니다. |
| PG-REP-02 | high | 베이스 백업과 연속 WAL 아카이빙(pgBackRest, Barman, WAL-G, 또는 제공자의 PITR)으로 백업하고 복구 시험을 합니다. `pg_dump`만으로는 특정 시점 복구가 안 됩니다. |
| PG-REP-03 | high | 메이저 업그레이드는 `pg_upgrade`(`--link`로 속도를 높이고 롤백을 예행)나 새 클러스터로의 논리 복제를 씁니다. 확장은 대상에서 호환되는 버전으로 존재해야 합니다. |
| PG-REP-04 | medium | 논리 복제는 DDL과 시퀀스 값을 전달하지 않습니다. 스키마 변경은 양쪽에 적용하고 컷오버 때 시퀀스를 다시 맞춥니다. |

## 9. 보안

| ID | Severity | Rule |
|---|---|---|
| PG-SEC-01 | high | 15 이전에 만든 클러스터는 `PUBLIC`의 `public`에 대한 `CREATE`를 회수하고, 애플리케이션별 역할을 쓰며, 특정 스키마에만 DML을 부여합니다. 이후 생성될 테이블에는 `ALTER DEFAULT PRIVILEGES`를 씁니다. |
| PG-SEC-02 | high | `scram-sha-256` 비밀번호 인증과 TLS(`pg_hba.conf`의 `hostssl`)를 씁니다. MD5는 18에서 폐기 예정입니다. |
| PG-SEC-03 | critical | 행 수준 보안(RLS)은 `ENABLE`하고 보통 `FORCE ROW LEVEL SECURITY`를 함께 씁니다. 모든 명령에 정책을 쓰고 애플리케이션 역할로 시험합니다. 테이블 소유자와 `BYPASSRLS` 역할은 정책을 건너뜁니다. |
| PG-SEC-04 | medium | `SECURITY DEFINER` 함수는 `search_path`를 명시적으로 설정합니다. |

## 10. 확장

| ID | Severity | Rule |
|---|---|---|
| PG-EXT-01 | medium | pgvector에서는 구축 시간과 메모리를 대가로 재현율(recall)과 지연 시간을 얻으려면 HNSW를, 데이터가 안정적이고 빠른 구축이 필요하면 IVFFlat을 고릅니다. 데이터 적재 후 인덱스를 만들고, 연산자 클래스를 조회 거리와 맞추며(`vector_cosine_ops`, `vector_l2_ops`, `vector_ip_ops`), 후처리 필터링이 `LIMIT`보다 적은 행을 낼 수 있으므로 필터를 신중히 씁니다. |
| PG-EXT-02 | medium | 선언적 파티셔닝(시간 기준 range, 테넌트 기준 list)은 보존(detach 후 오래된 파티션 drop)과 프루닝에 도움이 됩니다. 모든 유일 키는 파티션 키를 포함해야 하고, 파티션이 너무 많으면 계획 수립이 느려집니다. |
| PG-EXT-03 | low | 확장을 전제로 설계하기 전에 매니지드 서비스가 필요한 버전의 확장을 지원하는지 확인합니다. |

## 11. 검증 명령

```sql
-- statement hot spots
SELECT queryid, calls, total_exec_time, mean_exec_time, rows, query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
-- unused indexes
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC;
-- blocking chains
SELECT pid, pg_blocking_pids(pid), wait_event_type, state, now() - xact_start AS xact_age, query
FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
-- wraparound headroom
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
-- server version (PG-DDL-04 and other rules branch on it)
SHOW server_version;
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 버전 표, 지원 기간, 지원 종료 날짜 | <https://www.postgresql.org/support/versioning/> |
| PostgreSQL 18 추가 사항: `uuidv7()`, 가상 생성 컬럼 기본, AIO, 스킵 스캔, `NOT NULL ... NOT VALID`, `NOT ENFORCED`, 체크섬 기본 활성화, MD5 폐기 | <https://www.postgresql.org/docs/release/18.0/> |
| `EXPLAIN ANALYZE`가 문을 실행함 | <https://www.postgresql.org/docs/current/sql-explain.html> |
| `ALTER TABLE` 형태와 `VALIDATE CONSTRAINT`가 잡는 잠금 수준 | <https://www.postgresql.org/docs/current/sql-altertable.html>, <https://www.postgresql.org/docs/current/explicit-locking.html> |
| `CREATE INDEX CONCURRENTLY` 동작과 유효하지 않은 인덱스 | <https://www.postgresql.org/docs/current/sql-createindex.html> |
| 트랜잭션 ID 랩어라운드와 autovacuum | <https://www.postgresql.org/docs/current/routine-vacuuming.html> |
| 피해야 할 관행(`serial`, `money`, `timestamp`, `char(n)`, `NOT IN`) | <https://wiki.postgresql.org/wiki/Don%27t_Do_This> |
| pgvector 인덱스 타입과 연산자 클래스 | <https://github.com/pgvector/pgvector> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
