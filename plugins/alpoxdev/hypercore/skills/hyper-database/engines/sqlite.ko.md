# SQLite

애플리케이션이나 기기에 내장된 SQLite 엔진 가이드이며, SQLite 다이얼렉트인 libSQL과 Cloudflare D1도 다룹니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. Turso나 D1 플랫폼 제한은 `engines/distributed-sql.md`의 플랫폼 절도 함께 읽습니다. 발견 사항은 `SQ-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 <https://www.sqlite.org/changes.html>에서 확인했습니다. 묶여 있는 SQLite 버전이 문제가 되면 다시 확인합니다.

| Fact | Value |
|---|---|
| 현재 릴리스 | 3.54.1(2026-10-16) |
| 손상 수정 하한 | 3.53.0(2026-04-09)과 3.51.3 백포트가 WAL 리셋 시 발생하는 데이터베이스 손상 버그를 고칩니다. WAL 데이터베이스는 이 버전이나 그 이상에서 운영합니다 |
| 기능 하한 | `STRICT` 테이블 3.37.0; `WITHOUT ROWID` 3.8.2; WAL 3.7.0; 외래 키 강제 3.6.19; `NOT NULL`과 `CHECK` 제약을 추가·삭제하는 `ALTER TABLE` 3.53.0 |

SQLite 버전은 애플리케이션이 링크하는 라이브러리(드라이버에 묶인 사본, 운영체제 사본, 또는 플랫폼의 것)이며 개발자 머신의 CLI가 아닙니다. 애플리케이션 자신의 드라이버에서 `SELECT sqlite_version();`으로 확인합니다.

## 2. 적합성

SQLite는 한 애플리케이션 프로세스(또는 한 호스트의 몇 개)가 쓰고 다수가 읽는 구성, 로컬 우선과 내장 데이터, 테스트, 엣지에서의 읽기에 적합합니다. 많은 동시 쓰기, 네트워크 파일 시스템, 여러 호스트의 한 파일 접근에는 적합하지 않습니다(DM-60).

## 3. 타입과 테이블

| ID | Severity | Rule |
|---|---|---|
| SQ-TYP-01 | high | 하한이 허용하면 새 테이블을 `STRICT`로 선언합니다. 없으면 타입은 권고일 뿐이고 `'abc'`가 `INTEGER` 컬럼에 들어갑니다. `STRICT`에서는 `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB`, `ANY`만 허용됩니다. |
| SQ-TYP-02 | high | 일반 rowid 테이블의 모든 기본 키 컬럼에 `NOT NULL`을 명시합니다. SQLite는 `PRIMARY KEY` 컬럼이 `NULL`을 가질 수 있게 하는 역사적 버그를 유지합니다. `STRICT`와 `WITHOUT ROWID` 테이블은 이를 강제합니다. |
| SQ-TYP-03 | medium | 정수 키는 정확히 `INTEGER PRIMARY KEY`로 선언해 rowid 별칭이 되게 합니다. `INT PRIMARY KEY`는 그렇지 않습니다. 삭제된 ID를 절대 재사용하면 안 되는 경우가 아니면 `AUTOINCREMENT`를 건너뜁니다. 테이블과 쓰기 오버헤드가 추가됩니다. |
| SQ-TYP-04 | medium | 정수가 아닌 키로 조회하는 작은 행 테이블에는 `WITHOUT ROWID`를 씁니다. 이는 `last_insert_rowid()`, 증분 BLOB I/O, 갱신 훅을 깨뜨립니다. |
| SQ-TYP-05 | medium | 컬럼마다 시간 인코딩 하나를 고릅니다(UTC의 ISO-8601 `TEXT`, Unix 에포크 `INTEGER`, 줄리안 `REAL`). SQLite에는 datetime 타입이 없습니다. 불리언은 `INTEGER NOT NULL CHECK (x IN (0,1))`로 저장합니다. |
| SQ-TYP-06 | low | 문자열에는 작은따옴표를 씁니다. 어느 컬럼과도 맞지 않는 큰따옴표 문자열은 리터럴이 되어 오타를 감춥니다. `upper()`/`lower()`는 ICU로 빌드하지 않으면 ASCII만 접습니다. |

## 4. 연결과 내구성

| ID | Severity | Rule |
|---|---|---|
| SQ-CFG-01 | high | 모든 연결에서 `PRAGMA foreign_keys = ON`을 실행합니다. 강제는 기본이 꺼져 있고 설정이 연결 단위입니다. |
| SQ-CFG-02 | high | 동시 읽기가 있는 데이터베이스는 `PRAGMA journal_mode = WAL`을 씁니다. 이 설정은 파일에 유지됩니다. WAL 데이터베이스를 네트워크 파일 시스템에 두지 않습니다. 모든 프로세스가 한 호스트의 공유 메모리 인덱스를 필요로 합니다. |
| SQ-CFG-03 | high | 모든 연결에 `PRAGMA busy_timeout`(예: 5000 ms)을 설정하고 `SQLITE_BUSY`를 예상되는 재시도 가능 결과로 다룹니다. WAL 모드에서도 쓰기는 한 번에 하나입니다. |
| SQ-CFG-04 | medium | 쓰기 트랜잭션은 `BEGIN IMMEDIATE`로 열어 읽던 쪽이 쓰기로 바뀔 때 중간에 `SQLITE_BUSY`로 실패하지 않게 하고, 쓰기 트랜잭션은 짧게 유지합니다. |
| SQ-CFG-05 | medium | WAL 모드에서 `synchronous = NORMAL`은 애플리케이션 충돌에는 내구성이 있지만 전원 손실 시 마지막 커밋을 잃을 수 있습니다. 그 손실을 받아들일 수 없으면 `FULL`을 씁니다. |
| SQ-CFG-06 | medium | WAL을 한정합니다. 긴 읽기 트랜잭션은 체크포인트를 막고 WAL이 커집니다. 읽기 시간을 제한하고 한가한 시간대에 `PRAGMA wal_checkpoint(TRUNCATE)`를 실행합니다. |
| SQ-CFG-07 | low | 플래너가 통계를 갖도록 `PRAGMA optimize`를 주기적으로(예: 연결 종료 시) 실행합니다. |

## 5. 스키마 변경

| ID | Severity | Rule |
|---|---|---|
| SQ-DDL-01 | high | `ALTER TABLE`은 이름 변경, 컬럼 추가, 컬럼 삭제(제한 있음)와 3.53.0 이상의 제약 변경을 지원합니다. 그 밖의 변경은 문서화된 재구성을 씁니다. 새 테이블 생성, 복사, 이전 테이블 삭제, 이름 변경, 인덱스·트리거·뷰 재생성을 외래 키를 끈 상태에서 트랜잭션 하나로 하고, 이후 `PRAGMA foreign_key_check`를 실행합니다. |
| SQ-DDL-02 | medium | `PRAGMA user_version`이나 마이그레이션 테이블로 스키마 버전을 추적합니다. 일부 호스팅 SQLite 서비스는 `user_version`을 읽기 전용으로 만들므로 테이블이 이식성 있는 선택입니다. |

## 6. 백업과 무결성

| ID | Severity | Rule |
|---|---|---|
| SQ-OPS-01 | high | 운영 중인 데이터베이스 파일을 `cp`로 복사하지 않습니다. `VACUUM INTO`, 온라인 백업 API(CLI의 `.backup`), 또는 SQLite용으로 만든 복제 도구를 씁니다. `-wal`과 `-shm` 파일은 그런 도구의 일부로만 함께 복사합니다. |
| SQ-OPS-02 | medium | 복구 후와 손상이 의심될 때 `PRAGMA integrity_check`(또는 `quick_check`)를 실행합니다. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 릴리스 날짜, WAL 리셋 손상 수정, 3.53.0의 `ALTER TABLE` 제약 지원 | <https://www.sqlite.org/changes.html> |
| 유연한 타입, `NULL`을 허용하는 `PRIMARY KEY`, 외래 키 기본 비활성, 큰따옴표 문자열, ASCII 전용 대소문자 접기 | <https://www.sqlite.org/quirks.html> |
| `STRICT` 테이블 | <https://www.sqlite.org/stricttables.html> |
| `WITHOUT ROWID` 테이블 | <https://www.sqlite.org/withoutrowid.html> |
| WAL 동작, 단일 쓰기, 네트워크 파일 시스템, 체크포인트, `synchronous` | <https://www.sqlite.org/wal.html> |
| 지원하지 않는 `ALTER TABLE` 변경의 테이블 재구성 절차 | <https://www.sqlite.org/lang_altertable.html> |
| `VACUUM INTO`와 백업 API | <https://www.sqlite.org/lang_vacuum.html>, <https://www.sqlite.org/backup.html> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
