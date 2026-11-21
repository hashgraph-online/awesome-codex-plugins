# 엔진 선택

실행 시작 전에 이 규칙을 먼저 씁니다. import를 하기 전이나 질의를 쓰기 전에 어떤 엔진이 답할지, 그 엔진이 없을 때 어떻게 할지, 어떤 파일 형식을 직접 읽는지 정합니다.

## 1. 프로브 우선

작업 디렉터리에서 bundled 프로브를 실행합니다.

```bash
bash <skill-dir>/scripts/probe-engines.sh
```

JSON 객체 하나만 출력하고 파일을 쓰지 않습니다.

```json
{"schemaVersion":1,"platform":"darwin",
 "python3":{"path":"/usr/local/bin/python3","version":"3.13.1"},
 "packages":{"duckdb":{"version":"1.3.2"},"polars":null,"pyarrow":{"version":"0.17.0"},
             "numpy":{"version":"2.1.3"},"matplotlib":null},
 "duckdbCli":{"path":"/opt/homebrew/bin/duckdb","version":"v1.3.2"},
 "memory":{"freeBytes":5019926528,"source":"vm_stat"}}
```

- 프로브는 설치 배포 메타데이터(`pip list`, 그다음 `dist-info` 스캔)를 읽고 아무것도 import하지 않습니다. 버전이 `null`이면 그 인터프리터의 메타데이터에서 해당 배포를 찾지 못한 것이므로 패키지가 없다고 보고, 프로브가 출력하지 않은 버전을 짐작하지 않습니다.
- import는 질의 실행에서 일어납니다. 그때의 import 실패는 없는 전제 조건이며 프로브보다 우선합니다. 프로브가 버전을 출력했더라도 import가 실패하면 `prerequisite_missing`으로 보고합니다.
- `python3`은 있지만 패키지가 `null`이면 해당 엔진에는 쓸 수 없는 인터프리터입니다. 파일 질의는 `duckdb` CLI 필드가 담당합니다.
- 플랫폼이 가용 메모리 값을 내지 않으면 `memory`는 `null`입니다. `null`은 "모름"이지 "0"이 아닙니다.
- `--help`는 사용법을 출력하고 0으로 끝납니다. `--self-test`는 임시 디렉터리에서 `python3`와 `duckdb`를 스텁으로 두고 JSON 형태를 시험해 모든 검사가 통과하면 0으로 끝납니다. 그 밖의 인자는 2로 끝납니다.

## 2. 엔진 선택

| 질문 형태 | 엔진 | 이유 |
|---|---|---|
| 파일에 필터, 그룹 집계, 조인, 윈도, 부분 질의 | 파일을 겨냥한 DuckDB | SQL이 CSV와 Parquet, JSON을 적재 없이 원위치에서 읽고 메모리 한도를 넘으면 디스크로 넘깁니다 |
| 파생 컬럼이 많거나 컬럼별 조건 처리, 문자열 파이프라인, 재구조화 | lazy scan 위 Polars | 표현 체인이 중첩 SQL보다 잘 최적화되고 `unpivot`, `pivot`이 재구조화를 담당합니다 |
| RAM을 넘는 규모에서 DataFrame 형태 | Polars 스트리밍(`collect(engine="streaming")`) | lazy 계획을 청크 단위로 실행합니다([`references/polars-api.md`](../references/polars-api.md)) |
| 집계 너머의 수치 연산: 통계, 선형대수, FFT, 표본 | 설치된 numpy | SQL과 DataFrame으로 다루지 않습니다 |
| 결과의 차트 | 설치된 matplotlib | 차트를 요청받았을 때만([`rules/charts.md`](charts.md)) |
| 작은 파일이고 설치된 엔진이 없으며 정확한 답이 필요 | Python 표준 라이브러리(`csv`, `json`, `statistics`) | 의존성이 없고 작은 파일의 동작이 정확합니다 |

- 한 실행에서 두 엔진을 같이 쓸 수 있습니다. DuckDB로 질의한 결과를 Polars로 넘겨 재구조화하거나 그 반대로 합니다. 두 엔진은 Arrow를 말하므로 pyarrow가 설치되면 복사 없이 넘깁니다.
- DuckDB의 `.df()` 변환은 pandas가 필요합니다. pandas가 없으면 pyarrow를 통해 `.pl()`을 씁니다. 변환 방식이 엔진을 고르게 두지 않습니다.
- "이 라이브러리가 더 빠르다"는 기억은 엔진을 고르는 근거가 아닙니다. 선택이 실행을 크게 바꾸면 실제 데이터로 두 쪽을 재서 고릅니다.

## 3. 없는 엔진

- 없는 엔진을 전제 조건으로 보고 그 경로는 [`rules/query-evidence.md`](query-evidence.md) §4의 `prerequisite_missing`으로 끝냅니다. 빠진 패키지나 CLI 이름과 그것을 구하는 설치 명령을 적습니다.
- 실행이 되도록 패키지를 설치하거나 엔진을 내려받거나 인터프리터를 바꾸지 않습니다. 설치는 이 스킬 밖의 명시적 설정 결정이며, 몰래 설치하는 실행은 읽는 사람이 요청한 실행이 아닙니다.
- 엔진 하나가 없어도 다른 경로로 질문에 정확히 답할 수 있으면 그 경로를 쓰고, 어느 엔진이 없었는지 보고서에 적습니다.
- 표준 라이브러리는 정말로 큰 파일이 필요한 집계를 답하는 대안이 아닙니다. 메모리를 넘는 파일을 `csv` 행 루프로 다루는 일은 엔진 선택이 아니라 계산 위치 실패입니다([`rules/placement.md`](placement.md)).

## 4. 파일 형식

- CSV, Parquet, JSON은 DuckDB나 Polars가 직접 읽습니다. Parquet은 컬럼 통계를 그대로 받아 필터가 행 그룹을 건너뜁니다. CSV는 스트림으로 읽습니다.
- Excel 파일(`.xlsx`, `.xls`)은 직접 읽지 않습니다. 시트를 먼저 CSV나 Parquet으로 내보내고 내보낸 파일을 원본 옆이 아니라 `.hyper/data/<slug>/` 아래 보고서 옆에 둡니다. 그래야 실행이 추적 대상 파일을 바꾸지 않습니다. 내보내기 단계는 조용한 전처리가 아니라 보고서에 적는 일입니다.
- 데이터베이스 추출 파일(`.sql` 덤프, 질의에서 뽑은 CSV, parquet 내보내기)은 그 파일인 그대로 읽습니다. 질문이 사용자가 질의할 수 있는 데이터베이스 안에 있는 데이터를 겨냥하면 그 데이터베이스 안에서 집계하고 결과 행만 받습니다. 합계를 구하면서 테이블 전체를 내려받지 않습니다.
- `https`나 S3 위 원격 파일도 자기 형식을 유지합니다. DuckDB는 스토리지가 지원하면 투영과 술어 푸시다운으로 원격 Parquet과 CSV를 읽습니다. CSV는 대개 스트림 스캔입니다. 엔진이 줄인다고 보고할 때만 네트워크를 덜 썼다고 적습니다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| import 전에 설치된 엔진을 확인하고 SQL 형태는 DuckDB, DataFrame 형태는 Polars를 쓰는 선택 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md`, `references/execution-surfaces.md` (mechanism reference, re-authored) |
| 두 엔진 사이의 Arrow 복사 없는 전달과 `.df()`보다 `.pl()` 우선 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| 스프레드시트를 먼저 CSV나 Parquet으로 내보내는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md` (mechanism reference, re-authored) |
| 없는 엔진은 설치가 아니라 전제 조건이다 | user instruction, 2026-11-09 (issue #25) |

### Evidence grade

`LOCAL` - 프로브의 JSON 형태, 엔진 표, 없는 엔진에서의 멈춤은 이 패키지가 고른 설계입니다. 메커니즘 행은 라이선스가 없는 공개 저장소의 고정 커밋에서 우리말로 다시 쓴 것이며 텍스트나 코드를 복사하지 않았습니다.
