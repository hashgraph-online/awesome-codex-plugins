# Engine Selection

Use this rule at the start of every run, before importing an engine or writing a query. It decides which engine answers the question, what to do when that engine is missing, and which file formats are read directly.

## 1. Probe First

Run the bundled probe from the working directory:

```bash
bash <skill-dir>/scripts/probe-engines.sh
```

It prints exactly one JSON object and writes nothing:

```json
{"schemaVersion":1,"platform":"darwin",
 "python3":{"path":"/usr/local/bin/python3","version":"3.13.1"},
 "packages":{"duckdb":{"version":"1.3.2"},"polars":null,"pyarrow":{"version":"0.17.0"},
             "numpy":{"version":"2.1.3"},"matplotlib":null},
 "duckdbCli":{"path":"/opt/homebrew/bin/duckdb","version":"v1.3.2"},
 "memory":{"freeBytes":5019926528,"source":"vm_stat"}}
```

- The probe reads installed-distribution metadata (`pip list`, then a `dist-info` scan); it imports nothing. A `null` version means that interpreter's metadata showed no such distribution, so treat the package as unavailable and never guess a version the probe did not print.
- The import itself happens in the query run. An import failure there is a missing prerequisite, and it outranks the probe: report `prerequisite_missing` even when the probe printed a version.
- When `python3` is present but a package is `null`, the interpreter is unsuitable for that engine; the `duckdb` CLI field carries the file-query route.
- `memory` is `null` when the platform reports no free-memory figure. A `null` memory means "unknown", never "zero".
- `--help` prints usage and exits 0; `--self-test` exercises the JSON shape with stubbed `python3` and `duckdb` in a temporary directory and exits 0 when every check passes; any other argument exits 2.

## 2. Choosing the Engine

| Question shape | Engine | Why |
|---|---|---|
| Filter, group-by, join, window, or subquery over files | DuckDB against the files | SQL reads CSV, Parquet, and JSON in place with no load step and spills to disk past its memory limit |
| Many derived columns, per-column conditional logic, string pipelines, reshapes | Polars on a lazy scan | Expression chains optimize better than nested SQL; `unpivot` and `pivot` are built for reshapes |
| Work larger than RAM, DataFrame-shaped | Polars streaming (`collect(engine="streaming")`) | Executes the lazy plan in chunks ([`references/polars-api.md`](../references/polars-api.md)) |
| Numeric work beyond aggregation: statistics, linear algebra, FFT, sampling | numpy when installed | SQL and DataFrames do not cover these |
| A chart of the result | matplotlib when installed | Only when a chart is requested ([`rules/charts.md`](charts.md)) |
| Small file, no engine installed, exact answer needed | The Python standard library (`csv`, `json`, `statistics`) | No dependency, exact small-file behavior |

- One run may use both engines: query in DuckDB, hand the result to Polars for the reshape, or the reverse. Both speak Arrow, so the handoff is zero-copy when pyarrow is installed.
- A DuckDB `.df()` conversion needs pandas; without pandas use `.pl()` through pyarrow. Never let the conversion choose an engine for you.
- A remembered "this library is faster" claim does not choose the engine. When the choice materially changes the run, time both on the actual data.

## 3. Missing Engine

- Report the missing engine as a prerequisite and stop that route with `prerequisite_missing` ([`rules/query-evidence.md`](query-evidence.md) §4). Name the missing package or CLI and the install command that would provide it.
- Never install a package, download an engine, or change the interpreter to make the run work. Installation is an explicit setup decision outside this skill, and a run that quietly installs is not the run the reader asked for.
- When one engine is missing but another route can answer the question exactly, use that route and say in the report which engine was missing.
- The standard library is not a fallback for an aggregation the question genuinely requires large files to answer: a file larger than memory answered through `csv` row loops is a placement failure ([`rules/placement.md`](placement.md)), not an engine choice.

## 4. File Formats

- CSV, Parquet, and JSON are read directly by DuckDB or Polars. A Parquet file keeps column statistics that let a filter skip row groups; a CSV file is scanned as a stream.
- Excel files (`.xlsx`, `.xls`) are never read directly. Export the sheet to CSV or Parquet first and keep the export under `.hyper/data/<slug>/` beside the report, never next to the source file, so the run changes no tracked file; the export step is part of the report, not a silent preprocessing.
- A database export (a `.sql` dump, a CSV taken from a query, or a parquet export) is read as the file it is. When the question is about data that lives in a database the user can query, aggregate inside that database and return the result rows; never pull the whole table down to compute a sum locally.
- Remote files over `https` or S3 keep their own format. DuckDB reads Parquet and CSV remotely with projection and predicate pushdown when the storage supports it; CSV generally means scanning the stream. Only claim reduced network reads when the engine reports them.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Probing installed engines before importing, DuckDB for SQL-shaped work, Polars for DataFrame-shaped work | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md`, `references/execution-surfaces.md` (mechanism reference, re-authored) |
| Zero-copy Arrow handoff between the two engines, `.pl()` before `.df()` | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/polars-lane.md` (mechanism reference, re-authored) |
| Exporting spreadsheets to CSV or Parquet first | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md` (mechanism reference, re-authored) |
| A missing engine is a prerequisite, never an install | user instruction, 2026-11-09 (issue #25) |

### Evidence grade

`LOCAL` - the probe's JSON shape, the engine table, and the missing-engine stop are this package's chosen design. The mechanism rows are re-authored from a public repository at a pinned commit that carries no license; no text or code was copied.
