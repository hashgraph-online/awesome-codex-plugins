# Placement

Use this rule before the first query on any file larger than a few tens of megabytes, on remote data, or on data that lives in a database. It decides where the computation lives so one question does not re-scan a file ten times or swap the machine.

## 1. Probe Before Computing

Three facts decide placement: file size, free memory, and (when unclear) a row estimate from a streaming scan.

- File size is `os.path.getsize()` or `ls -l`; it is not the working set.
- Free memory comes from the probe's `memory.freeBytes` when present. Physical RAM is not free memory; a machine with 32 GB installed and 2 GB free does not hold a 10 GB working set.
- A row estimate comes from a streaming count, never from loading the file: DuckDB `SELECT count(*) FROM 'data.csv'` streams the scan.

Estimate the working set from the columns the question touches. CSV typically expands 2-5x in memory because string columns dominate; Parquet expands less predictably because compressed columns can inflate 10x when decompressed. A 4 GB Parquet file can be a 40 GB working set.

## 2. Load Once: Within About 25% of Free Memory

This threshold is a package choice, not a vendor guarantee: load into memory only when the working set stays within about 25% of free RAM, and the session will run repeated queries against it.

- Load once and iterate: `CREATE TABLE t AS SELECT ...` in DuckDB, or a collected DataFrame in Polars. One scan up front turns every later query from a file re-scan into milliseconds.
- Prune at load time: select only the columns the question touches and drop obvious dross, so the resident table is the working set, not the raw file.
- The 25% line exists because the OS, the interpreter, and every other process also need memory. A working set at 90% of free RAM swaps; a working set at 25% does not.

## 3. In Place or Streaming: Single-Pass or Larger Than Memory

- A single-pass question queries the file directly (`FROM 'data.csv'`). Loading first is pure waste.
- Larger than RAM, SQL-shaped: cap DuckDB and let it spill.
  ```sql
  SET memory_limit = '4GB';
  SET temp_directory = '/tmp/duckdb_spill';
  ```
  Aggregations, sorts, and window functions then run out-of-core. Slower, but bounded.
- Larger than RAM, DataFrame-shaped: Polars streaming on a lazy plan.
  ```python
  out = (pl.scan_parquet("huge.parquet")
         .filter(pl.col("status") == "active")
         .group_by("region").agg(pl.len())
         .collect(engine="streaming"))
  ```
  Keep the plan lazy end to end; an intermediate `collect()` breaks it into eager pieces.
- Hand-rolled chunk loops are the last resort. The engines' own out-of-core paths are faster and simpler than a manual read-N-rows loop.

## 4. Push the Query to the Data

- Remote files over `https` or S3: DuckDB reads Parquet and CSV with projection and predicate pushdown when the storage supports it. Parquet can prune row groups; CSV generally means scanning the stream. Confirm the format and the preinstalled extension first; never claim reduced reads without the engine reporting them.
- Data in a database the user can query: aggregate there at the reader's required grain and return the result rows. A group-by result is kilobytes; the source table is gigabytes.
- Data on another machine the user can execute on: run the query there and return the aggregate. Decision rule: when the result is much smaller than the data, move the query; when local iteration on one slice is planned, move a pruned copy of that slice once and then work locally.
- Never load a dataset larger than free memory fully into memory. Swapping stalls the whole machine; streaming merely takes longer. When the probe says the working set is close to free RAM, choose streaming, not hope.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Loading once only within about a quarter of free RAM, and streaming or querying in place beyond that | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/SKILL.md`, `references/placement.md` (mechanism reference, re-authored) |
| Moving the query to the data when the result is much smaller than the input | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/placement.md` (mechanism reference, re-authored) |
| The in-place SQL and streaming-plan recipes | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/placement.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - the 25% threshold is this package's chosen threshold, labeled as one here. It is the mechanism's heuristic, not a measured optimum for every machine, and the probe's free-memory figure is what the threshold compares against.
