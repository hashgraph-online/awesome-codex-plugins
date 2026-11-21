# 계산 위치

수십 MB를 넘는 파일이나 원격 데이터, 데이터베이스에 있는 데이터에 첫 질의를 하기 전에 이 규칙을 씁니다. 계산이 어디에서 도는지를 정해 질문 하나가 파일을 열 번 다시 읽지 않거나 기계를 스왑으로 몰지 않게 합니다.

## 1. 계산 전에 프로브를 돌립니다

배치를 좌우하는 사실은 셋입니다. 파일 크기, 가용 메모리, 분명하지 않으면 스트리밍 스캔으로 구한 행 추정치입니다.

- 파일 크기는 `os.path.getsize()`나 `ls -l`입니다. 파일 크기가 작업 집합이 아닙니다.
- 가용 메모리는 프로브의 `memory.freeBytes`를 씁니다. 물리 메모리는 가용 메모리가 아닙니다. 32 GB를 달았고 2 GB가 빈 기계는 10 GB 작업 집합을 담지 못합니다.
- 행 추정치는 스트리밍 개수로 구합니다. 파일을 적재해서 세지 않습니다. DuckDB `SELECT count(*) FROM 'data.csv'`는 스캔을 스트리밍합니다.

작업 집합은 질문이 닿는 컬럼 기준으로 추정합니다. CSV는 문자열 컬럼이 많아 메모리에서 대개 2-5배로 부풀습니다. Parquet는 압축 컬럼이 풀리며 10배까지 부풀 수 있어 팽창이 더 불규칙합니다. 4 GB Parquet 파일이 40 GB 작업 집합일 수 있습니다.

## 2. 한 번 적재: 가용 메모리의 약 25% 이내일 때만

이 임계값은 패키지가 고른 선택이며 vendor 보장이 아닙니다. 작업 집합이 가용 RAM의 약 25% 이내에 머물고 세션에서 같은 데이터에 질의를 반복할 때만 메모리에 적재합니다.

- 한 번 적재하고 반복합니다. DuckDB `CREATE TABLE t AS SELECT ...`나 Polars로 모은 DataFrame입니다. 처음 한 번의 스캔으로 이후의 모든 질의가 파일 재스캔에서 밀리초 단위로 바뀝니다.
- 적재할 때 가지치기합니다. 질문이 닿는 컬럼만 고르고 명백히 필요 없는 것은 빼서, 상주 테이블이 원본 파일이 아니라 작업 집합이 되게 합니다.
- 25% 선은 운영체제와 인터프리터와 다른 프로세스에도 메모리가 필요하기 때문입니다. 가용 RAM의 90% 작업 집합은 스왑을 일으키고, 25% 작업 집합은 일으키지 않습니다.

## 3. 원위치 또는 스트리밍: 한 번만 지나가거나 메모리보다 클 때

- 한 번만 지나가는 질문은 파일을 직접 질의합니다(`FROM 'data.csv'`). 먼저 적재하는 것은 순수한 낭비입니다.
- RAM을 넘고 SQL 형태면 DuckDB에 상한을 두고 디스크로 넘기게 합니다.
  ```sql
  SET memory_limit = '4GB';
  SET temp_directory = '/tmp/duckdb_spill';
  ```
  집계와 정렬, 윈도 함수가 out-of-core로 돕니다. 느리지만 상한이 있습니다.
- RAM을 넘고 DataFrame 형태면 lazy 계획 위 Polars 스트리밍을 씁니다.
  ```python
  out = (pl.scan_parquet("huge.parquet")
         .filter(pl.col("status") == "active")
         .group_by("region").agg(pl.len())
         .collect(engine="streaming"))
  ```
  계획을 끝까지 lazy로 둡니다. 중간 `collect()`는 계획을 eager 조각으로 깨뜨립니다.
- 손으로 짜는 청크 루프는 마지막 수단입니다. 엔진이 가진 out-of-core 경로가 손으로 짠 루프보다 빠르고 단순합니다.

## 4. 질의를 데이터로 보냅니다

- `https`나 S3 위 원격 파일: 스토리지가 지원하면 DuckDB가 투영과 술어 푸시다운으로 Parquet과 CSV를 읽습니다. Parquet는 행 그룹을 가지칠 수 있고 CSV는 대개 스트림 스캔입니다. 형식과 미리 설치된 확장을 먼저 확인하고, 엔진이 줄인다고 보고할 때만 줄인다고 적습니다.
- 사용자가 질의할 수 있는 데이터베이스에 있는 데이터: 그곳에서 읽는 사람이 필요한 집계 단위로 집계하고 결과 행만 받습니다. 그룹 집계 결과는 수 KB이고 원본 테이블은 수 GB입니다.
- 사용자가 실행할 수 있는 다른 기계에 있는 데이터: 그곳에서 질의를 실행하고 집계 결과를 받습니다. 판단 기준은 다음과 같습니다. 결과가 데이터보다 훨씬 작으면 질의를 이동하고, 한 조각을 반복해서 자주 돌리면 그 조각의 가지친 사본을 한 번만 옮긴 뒤 로컬에서 다룹니다.
- 가용 메모리보다 큰 데이터셋을 메모리에 전부 적재하지 않습니다. 스왑은 기계 전체를 멈추고, 스트리밍은 그저 오래 걸립니다. 프로브가 작업 집합이 가용 RAM에 가깝다고 말하면 희망이 아니라 스트리밍을 고릅니다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 가용 메모리의 약 4분의 1 이내일 때만 한 번 적재하고 그 너머는 스트리밍하거나 원위치에서 질의하는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md`, `references/placement.md` (mechanism reference, re-authored) |
| 결과가 입력보다 훨씬 작으면 질의를 데이터로 보내는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/placement.md` (mechanism reference, re-authored) |
| 원위치 SQL과 스트리밍 계획 레시피 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/placement.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - 25% 임계값은 이 패키지가 고른 임계값이며 여기서 그 점을 이름 붙였습니다. 이 메커니즘의 휴리스틱이지 모든 기계에서 잰 최적값이 아니며, 임계값이 비교하는 대상은 프로브의 가용 메모리 값입니다.
