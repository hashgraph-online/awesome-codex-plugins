# Polars API Notes (1.x)

Use this reference before writing a Polars pipeline. Spelled-in-full current names are listed beside the older spellings that training data teaches, because the older spellings fail, warn, or silently change meaning in 1.x. This reference is a snapshot, not a living document: the `last_verified_at` line records when the notes were last checked against the source snapshot, and a run that depends on a name here re-checks the live documentation when the installed version disagrees.

> `last_verified_at: 2026-11-09`

## 1. Current Names

| Use (1.x) | Not (older) |
|---|---|
| `pl.scan_csv(...)`, `pl.scan_parquet(...)`, then `.collect()` | eager `read_csv`, `read_parquet` on big files |
| `.group_by(...)` | `.groupby(...)` |
| `pl.len()` | `pl.count()` |
| `.collect(engine="streaming")` | `.collect(streaming=True)` |
| `.unpivot(...)` | `.melt(...)` |

## 2. Lazy First

```python
out = (pl.scan_csv("data.csv")
       .filter(pl.col("value") > 100)
       .group_by("category")
       .agg(pl.col("value").sum().alias("total"), pl.len().alias("n"))
       .sort("total", descending=True)
       .collect())
```

- `scan_csv` and `scan_parquet` build a plan; filters and projections push down to the file read, and the plan executes once at `collect()`.
- Eager `read_*` is for small files mutated interactively. On a file larger than memory it loads the whole frame and defeats the placement rule ([`rules/placement.md`](../rules/placement.md) §3).
- `pl.len()` counts rows in an aggregation; `pl.count()` is an older name that fails or warns in 1.x.

## 3. Streaming Past RAM

```python
out = (pl.scan_parquet("huge.parquet")
       .filter(pl.col("status") == "active")
       .group_by("region").agg(pl.len())
       .collect(engine="streaming"))
```

- Streaming executes lazy plans only. Keep the plan lazy end to end; an intermediate `collect()` breaks it into eager pieces and the chunks stop.
- `streaming=True` is the older spelling of the same flag; in 1.x it fails or warns where `engine="streaming"` works.

## 4. Reshapes

- `unpivot` melts wide columns into long form; `pivot` spreads them back. The older `melt` name is the rename target of the same operation.
- Wear reshapes where SQL would need nested CASE expressions; keep them inside the expression chain so the optimizer sees the whole pipeline.

## 5. DuckDB Handoff

Both engines speak Arrow, so a mixed pipeline pays no serialization cost:

```python
import duckdb
df = duckdb.sql("SELECT * FROM 'orders.csv' o JOIN 'items.csv' i USING (id)").pl()
shaped = df.with_columns((pl.col("qty") * pl.col("price")).alias("rev"))
duckdb.register("shaped", shaped)
out = duckdb.sql("SELECT category, SUM(rev) AS total FROM shaped GROUP BY 1").pl()
```

- `.pl()` requires pyarrow installed. Confirm it is present before the handoff; without it the call raises `ModuleNotFoundError`.
- Prefer `.pl()`. `.df()` is an alternative only when pandas is installed and the user, project, or available-engine constraints require it.

## 6. Version Drift

- The installed version decides which names work. When the probe ([`rules/engine-selection.md`](../rules/engine-selection.md) §1) shows an older Polars, the renames above may not apply; re-check the installed version's documentation and say in the report which spelling ran.
- Newer names may be added to this reference; older names are kept beside them only as a warning list, never as a recommended spelling.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The 1.x renames (`group_by`, `pl.len()`, `unpivot`, `collect(engine="streaming")`) and the lazy-scan recipe | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| The Arrow handoff recipe and the pyarrow requirement for `.pl()` | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| The streaming recipe and keeping the plan lazy end to end | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |

### Evidence grade

`VENDOR` - the Polars 1.x names are vendor facts re-authored from a source snapshot at a pinned commit. `last_verified_at: 2026-11-09` is the last check; the installed version's own documentation wins over this snapshot when they disagree.
