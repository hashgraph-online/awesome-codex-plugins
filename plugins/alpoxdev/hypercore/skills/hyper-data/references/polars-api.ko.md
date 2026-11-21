# Polars API 노트 (1.x)

Polars 파이프라인을 쓰기 전에 이 참조를 읽습니다. 현재 이름과 학습 데이터에 배인 예전 표기를 나란히 적습니다. 예전 표기는 1.x에서 실패하거나 경고하거나 조용히 다른 뜻으로 동작합니다. 이 참조는 스냅샷이며 살아 있는 문서가 아닙니다. `last_verified_at` 줄은 이 노트를 소스 스냅샷과 대조한 마지막 시점이며, 설치된 버전이 다르면 실행에서는 실제 문서로 다시 확인합니다.

> `last_verified_at: 2026-11-09`

## 1. 현재 이름

| 쓸 것 (1.x) | 쓰지 말 것 (예전) |
|---|---|
| `pl.scan_csv(...)`, `pl.scan_parquet(...)`, 이어서 `.collect()` | 큰 파일에 eager `read_csv`, `read_parquet` |
| `.group_by(...)` | `.groupby(...)` |
| `pl.len()` | `pl.count()` |
| `.collect(engine="streaming")` | `.collect(streaming=True)` |
| `.unpivot(...)` | `.melt(...)` |

## 2. lazy 우선

```python
out = (pl.scan_csv("data.csv")
       .filter(pl.col("value") > 100)
       .group_by("category")
       .agg(pl.col("value").sum().alias("total"), pl.len().alias("n"))
       .sort("total", descending=True)
       .collect())
```

- `scan_csv`와 `scan_parquet`는 계획을 만들고, 필터와 투영이 파일 읽기로 내려가며, 실행은 `collect()`에서 한 번 일어납니다.
- eager `read_*`는 대화형으로 고치는 작은 파일용입니다. 메모리를 넘는 파일에서는 프레임 전체를 적재해 계산 위치 규칙([`rules/placement.md`](../rules/placement.md) §3)을 무너뜨립니다.
- `pl.len()`은 집계에서 행을 셉니다. `pl.count()`는 예전 이름으로 1.x에서 실패하거나 경고합니다.

## 3. RAM을 넘는 스트리밍

```python
out = (pl.scan_parquet("huge.parquet")
       .filter(pl.col("status") == "active")
       .group_by("region").agg(pl.len())
       .collect(engine="streaming"))
```

- 스트리밍은 lazy 계획만 실행합니다. 계획을 끝까지 lazy로 두며, 중간 `collect()`는 계획을 eager 조각으로 깨뜨려 청크가 끊깁니다.
- `streaming=True`는 같은 플래그의 예전 표기이며 1.x에서 `engine="streaming"`이 되는 곳에서는 실패하거나 경고합니다.

## 4. 재구조화

- `unpivot`는 넓은 컬럼을 긴 형태로 녹이고, `pivot`은 다시 넓게 펼칩니다. 예전 이름 `melt`는 같은 연산의 개명 목표입니다.
- SQL에서 중첩 CASE 식이 필요한 재구조화는 여기서 합니다. 표현 체인 안에 두면 최적화기가 전체 파이프라인을 봅니다.

## 5. DuckDB 전달

두 엔진은 Arrow를 말하므로 혼합 파이프라인에 직렬화 비용이 들지 않습니다.

```python
import duckdb
df = duckdb.sql("SELECT * FROM 'orders.csv' o JOIN 'items.csv' i USING (id)").pl()
shaped = df.with_columns((pl.col("qty") * pl.col("price")).alias("rev"))
duckdb.register("shaped", shaped)
out = duckdb.sql("SELECT category, SUM(rev) AS total FROM shaped GROUP BY 1").pl()
```

- `.pl()`은 pyarrow가 설치돼 있어야 합니다. 전달 전에 설치 여부를 확인하고, 없으면 `ModuleNotFoundError`가 납니다.
- `.pl()`을 우선합니다. pandas가 설치돼 있고 사용자나 프로젝트 요구, 엔진 제약으로 필요할 때만 `.df()`를 씁니다.

## 6. 버전 이동

- 어느 이름이 통하는지는 설치된 버전이 정합니다. 프로브([`rules/engine-selection.md`](../rules/engine-selection.md) §1)가 예전 Polars를 보이면 위 개명이 적용되지 않을 수 있습니다. 설치된 버전의 문서를 다시 확인하고 보고서에 어떤 표기로 돌렸는지 적습니다.
- 새 이름은 이 참조에 더할 수 있으며, 예전 이름은 경고 목록으로만 남기고 권장 표기로 쓰지 않습니다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 1.x 개명(`group_by`, `pl.len()`, `unpivot`, `collect(engine="streaming")`)과 lazy-scan 레시피 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| Arrow 전달 레시피와 `.pl()`의 pyarrow 요구 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| 스트리밍 레시피와 계획을 끝까지 lazy로 두는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |

### Evidence grade

`VENDOR` - Polars 1.x 이름은 고정 커밋의 소스 스냅샷에서 우리말로 다시 쓴 vendor 사실입니다. `last_verified_at: 2026-11-09`가 마지막 확인 시점이며, 설치된 버전의 문서를 먼저 따릅니다.
