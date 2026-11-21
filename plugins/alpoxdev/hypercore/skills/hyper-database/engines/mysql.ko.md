# MySQL과 MariaDB

MySQL(InnoDB), Percona Server, MariaDB 엔진 가이드입니다. 자체 호스팅과 매니지드(RDS, Aurora MySQL, Cloud SQL, Azure, PlanetScale Vitess)를 모두 다룹니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. Vitess나 PlanetScale이면 `engines/distributed-sql.md`의 플랫폼 절도 함께 읽습니다. 발견 사항은 `MY-*` ID를 인용하고, MariaDB 전용 규칙은 `MY-MDB-*`를 씁니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 MySQL 26.10, 9.7, 8.4 매뉴얼과 MariaDB 릴리스 모델에서 확인했습니다. 업그레이드 결정이 이 내용에 달려 있으면 다시 확인합니다.

| Fact | Value |
|---|---|
| 릴리스 트랙 | LTS(프리미어 지원 5년에 확장 지원 3년)와 Innovation(다음 Innovation 릴리스까지만 지원) |
| LTS 라인 | 8.4 LTS와 9.7 LTS. 9.7이 마지막 순차 번호 라인입니다 |
| 버전 번호 체계 | 2026년 7월부터 달력 버전 `YY.M.P`(26.7.0이 첫 릴리스, 현재 Innovation 매뉴얼은 26.10)를 씁니다. 달력 버전만으로는 그 릴리스가 LTS인지 알 수 없습니다 |
| 업그레이드 경로 | LTS에서 다음 LTS로만 가능하고 하나를 건너뛸 수 없습니다(8.4에서 9.7로, 8.4에서 이후 달력 버전 LTS로는 안 됨). 9.7 LTS만 첫 달력 버전 계보로 직접 업그레이드합니다. Innovation 다운그레이드는 논리 덤프와 적재가 필요합니다 |
| MariaDB | MySQL과 버전 호환이 아닙니다. 11.3부터 연간 약 네 번 릴리스하고 네 번에 한 번꼴로 LTS를 내며 3년 유지합니다. 시리즈별로 어느 라인이 LTS인지 확인합니다 |

## 2. 타입과 키

| ID | Severity | Rule |
|---|---|---|
| MY-TYP-01 | high | `utf8mb4`를 쓰고(8.x 서버 기본값은 `utf8mb4_0900_ai_ci`) `utf8` 별칭은 절대 쓰지 않습니다. 이 별칭은 `utf8mb3`이고 이모지 같은 4바이트 문자를 저장하지 못합니다. 문자 집합은 DDL에 명시합니다. |
| MY-TYP-02 | high | 시점은 관례상 UTC를 담는 `DATETIME`에 저장하거나, `TIMESTAMP`의 세션 시간대 변환과 `2038-01-19 03:14:07` UTC라는 한계를 받아들입니다. 새 컬럼이 2038 제한을 모르는 채 물려받게 두지 않습니다. |
| MY-TYP-03 | high | 엄격한 SQL 모드(`STRICT_TRANS_TABLES`)를 켜 둡니다. 없으면 잘못된 날짜가 `0000-00-00`이 되고 잘림이 경고로만 처리됩니다. |
| MY-TYP-04 | high | 모든 InnoDB 테이블은 짧고 단조 증가하는 기본 키를 선언합니다(`BIGINT UNSIGNED AUTO_INCREMENT`, 또는 `BINARY(16)`의 시간 순 UUID). 기본 키가 클러스터형 인덱스이자 행 순서입니다. 없으면 InnoDB는 첫 번째 non-null 유일 키나 숨은 6바이트 행 ID를 씁니다. |
| MY-TYP-05 | medium | 보조 인덱스는 기본 키 폭에서 예산을 잡습니다. 모든 보조 인덱스 항목이 기본 키 전체를 담으므로 넓거나 무작위인 키는 모든 인덱스를 부풀리고 삽입을 흩뜨립니다. |
| MY-TYP-06 | medium | 금액에는 `DECIMAL(p,s)`를 씁니다. `FLOAT`/`DOUBLE`은 근사값입니다. |
| MY-TYP-07 | low | `ENUM`은 값을 뒤에 추가하는 방식으로만 안전하게 확장할 수 있습니다. 순서를 바꾸거나 중간에 삽입하면 저장된 값이 다시 번호 매김됩니다. 변하는 집합에는 조회 테이블을 선호합니다. |
| MY-TYP-08 | medium | MySQL `JSON`은 바이너리 문서 타입입니다. 필터에 쓰는 필드는 생성 컬럼이나 함수 인덱스(`INDEX ((CAST(doc->>'$.sku' AS CHAR(32))))`)로 인덱싱합니다. |

## 3. 인덱스와 쿼리

| ID | Severity | Rule |
|---|---|---|
| MY-IDX-01 | medium | 복합 인덱스는 동등 조건 컬럼을 먼저 두고 범위나 정렬 컬럼 하나를 뒤에 둡니다. 첫 범위 컬럼 뒤의 컬럼은 탐색에 쓰이지 않습니다. |
| MY-IDX-02 | medium | 커버링 인덱스(선택하는 모든 컬럼이 인덱스에 있음)는 클러스터형 인덱스 조회를 피합니다. `EXPLAIN`에 `Using index`가 나옵니다. |
| MY-IDX-03 | medium | 인덱스를 없애려면 먼저 `INVISIBLE`로 만듭니다(빠르고, 유지되며, 유일성도 계속 강제함). 계획과 지연 시간을 지켜본 뒤 지웁니다. 기본 키는 invisible로 만들 수 없습니다. |
| MY-IDX-04 | medium | 실행 계획은 일회용 복사본에서 `EXPLAIN FORMAT=TREE`나 `EXPLAIN ANALYZE`로 읽습니다. `EXPLAIN ANALYZE`는 문을 실행합니다. 뜨거운 쿼리에서 `type: ALL`, `Using filesort`, `Using temporary`를 살핍니다. |
| MY-QRY-01 | medium | 깊은 목록은 큰 `OFFSET` 대신 키셋 페이지네이션으로 나눕니다. |
| MY-QRY-02 | medium | 기본 `REPEATABLE READ`에서 잠금 읽기와 갱신의 범위 스캔은 갭 잠금과 넥스트 키 잠금을 잡습니다. 조건자에 인덱스를 만들어 `UPDATE ... WHERE`가 범위가 아니라 몇 행만 잠그게 하고 그 트랜잭션을 짧게 유지합니다. |
| MY-QRY-03 | medium | 교착은 동시성 아래에서 정상입니다. 로그로 남기고(`innodb_print_all_deadlocks`) 트랜잭션을 한 번 재시도하며 잠금 순서를 고칩니다. |
| MY-QRY-04 | low | `INSERT ... ON DUPLICATE KEY UPDATE`와 `REPLACE`는 다르게 동작합니다. `REPLACE`는 삭제 후 삽입하므로 삭제 트리거와 캐스케이드가 발동합니다. |

## 4. 무중단 스키마 변경

| ID | Severity | Rule |
|---|---|---|
| MY-DDL-01 | high | 모든 `ALTER TABLE`에 알고리즘과 잠금을 명시합니다(`ALGORITHM=INSTANT` 또는 `ALGORITHM=INPLACE, LOCK=NONE`). 그러면 조용히 차단 복사로 폴백하지 않고 문이 실패합니다. 8.4에서 컬럼 추가와 삭제는 `INSTANT`가 기본입니다. |
| MY-DDL-02 | high | `INSTANT` 컬럼 변경은 행 버전 수에 상한이 있고(테이블당 64, 9.1.0부터 255. `INFORMATION_SCHEMA.INNODB_TABLES.TOTAL_ROW_VERSIONS` 참조) `ROW_FORMAT=COMPRESSED` 테이블, `FULLTEXT` 인덱스가 있는 테이블, 임시 테이블에서는 쓸 수 없습니다. 상한 전에 재구성을 계획합니다. |
| MY-DDL-03 | high | 컬럼 데이터 타입을 바꾸면 테이블을 재작성하고 동시 DML을 허용하지 않습니다. 기본 키 추가나 변경도 재작성합니다. 크고 뜨거운 테이블에는 gh-ost나 `pt-online-schema-change`를 씁니다. |
| MY-DDL-04 | high | 모든 DDL은 테이블의 열린 트랜잭션이 끝날 때까지 잡고 있는 메타데이터 잠금을 기다리고, 대기 중인 DDL은 이후 쿼리를 막습니다. 마이그레이션 세션에서 `lock_wait_timeout`을 낮게 잡고 `performance_schema.metadata_locks`를 확인하며, 긴 트랜잭션을 먼저 종료하거나 기다립니다. |
| MY-DDL-05 | high | DDL은 트랜잭션이 아닙니다. 여러 문을 가진 마이그레이션이 중간에 실패하면 반쯤 적용된 상태로 남습니다. 마이그레이션마다 변경 하나를 유지하고, 도구가 허용하면 문마다 멱등하게 만듭니다. |
| MY-DDL-06 | medium | 보조 인덱스 추가는 동시 DML이 가능한 `INPLACE`지만 완료 전에 테이블의 트랜잭션이 끝나기를 기다립니다. |

## 5. 설정, 복제, 운영

| ID | Severity | Rule |
|---|---|---|
| MY-CFG-01 | medium | 전용 호스트에서 `innodb_buffer_pool_size`를 주 메모리 조정값으로 잡고(흔히 RAM의 절반 훨씬 위) 하드웨어를 늘리기 전에 버퍼 풀 적중률을 확인합니다. |
| MY-CFG-02 | high | 원본 저장소에는 `innodb_flush_log_at_trx_commit = 1`과 `sync_binlog = 1`을 유지합니다. 다른 값은 마지막 1초의 커밋을 처리량과 맞바꿉니다. |
| MY-CFG-03 | medium | 느린 쿼리 로그와 Performance Schema 문 다이제스트를 켜고 총 지연 시간이 큰 상위 다이제스트를 검토합니다. |
| MY-REP-01 | high | GTID 기반 복제(`gtid_mode=ON`, `enforce_gtid_consistency=ON`)를 쓰고 복제본 지연을 감시합니다. 긴 트랜잭션과 큰 DDL은 직렬로 재생되며 지연 급증을 만듭니다. |
| MY-REP-02 | high | 물리 도구(Percona XtraBackup, MySQL Enterprise Backup, clone 플러그인, 또는 제공자의 스냅숏)와 특정 시점 복구용 바이너리 로그 보존으로 백업합니다. 큰 데이터베이스에서 `mysqldump`만으로는 PITR이 안 됩니다. 복구 시험을 합니다. |
| MY-SEC-01 | high | `caching_sha2_password`를 쓰고 TLS를 요구하며(`require_secure_transport=ON`) 애플리케이션 사용자에게 스키마별 권한을 부여합니다. 애플리케이션이 `root`로 접속하게 두지 않습니다. |

## 6. MariaDB 차이

| ID | Severity | Rule |
|---|---|---|
| MY-MDB-01 | high | MariaDB `JSON`은 `JSON_VALID` 검사를 붙인 `LONGTEXT` 별칭입니다. 값은 텍스트로 저장되고 문자열로 비교되며, 중복 키는 첫 번째를 유지합니다. MySQL의 JSON 인덱싱이나 비교 가정을 그대로 옮기지 않습니다. |
| MY-MDB-02 | high | MySQL `JSON` 컬럼을 MariaDB로 행 기반 복제하는 것은 동작하지 않습니다. MariaDB GTID는 MySQL GTID와 형식이 다릅니다. |
| MY-MDB-03 | medium | MySQL과 동등하다고 가정하지 말고 MariaDB 시리즈별 기능 하한을 확인합니다. instant `ADD COLUMN`, invisible 컬럼, 시스템 버전 테이블은 MariaDB 고유의 규칙과 제한이 있습니다. |

## 7. 검증 명령

```sql
-- statement hot spots
SELECT digest_text, count_star, sum_timer_wait/1e12 AS total_s, avg_timer_wait/1e9 AS avg_ms
FROM performance_schema.events_statements_summary_by_digest ORDER BY sum_timer_wait DESC LIMIT 20;
-- unused indexes (sys schema)
SELECT * FROM sys.schema_unused_indexes;
-- metadata lock waits
SELECT * FROM performance_schema.metadata_locks WHERE lock_status = 'PENDING';
-- instant-DDL headroom
SELECT name, total_row_versions FROM information_schema.innodb_tables ORDER BY total_row_versions DESC LIMIT 10;
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 달력 버전 체계, 호환 계보, LTS와 Innovation 지원, 업그레이드 경로 | <https://dev.mysql.com/doc/refman/26.10/en/mysql-releases.html>, <https://dev.mysql.com/doc/refman/8.4/en/mysql-releases.html> |
| `INSTANT` 기본값, 행 버전 상한 64(9.1.0부터 255), 타입과 기본 키 변경의 동작 표 | <https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html> |
| 클러스터형·보조 인덱스 구조, 숨은 행 ID | <https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html> |
| `TIMESTAMP`와 `DATETIME` 범위 및 시간대 변환 | <https://dev.mysql.com/doc/refman/8.4/en/datetime.html> |
| `utf8`은 `utf8mb3`의 별칭, 서버 기본 문자 집합과 콜레이션 | <https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html>, <https://dev.mysql.com/doc/refman/8.4/en/charset-server.html> |
| 메타데이터 잠금이 트랜잭션 종료까지 유지됨 | <https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html> |
| invisible 인덱스 동작 | <https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html> |
| 기본 격리 수준과 넥스트 키 잠금 | <https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html> |
| MariaDB 릴리스 모델과 `JSON` 타입 | <https://mariadb.com/docs/release-notes/community-server/about/release-model>, <https://mariadb.com/docs/server/reference/data-types/string-data-types/json> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
