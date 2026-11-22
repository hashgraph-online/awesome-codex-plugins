# Shipped macros

`transform macro` lists the macros Dex ships. `transform macro <name>` proposes
scaffolding one into the project's macro directory as a plan, applied with
`transform apply` like any other. The user's copy is theirs to edit; re-running
the command diffs it against the shipped version (a warning says whether it is
customized or stale), and applying that plan overwrites deliberately.

## `generate_schema_name`

The override `transform init --layered-schemas` scaffolds, so each layer folder
builds into its own `<layer>_<target name>` schema.

## `dex_unique_combination`

The generic test a declared composite grain renders
([declarations](declarations.md#dex_unique_combination-a-composite-grain)), where
`declarations.render_tests` turns it on. A declaration plan adds it for you; this
command scaffolds or diffs it on its own. It fails with the count of rows beyond
the first of each grain value, and never selects a key. The SQL goes through
dbt's dispatch, `default__dex_unique_combination` holds on every connector, and
a project overrides one warehouse with its own
`<adapter>__dex_unique_combination(model, columns)` macro.

## `dex_population_filter`

The generic test a declared population filter renders
([declarations](declarations.md#dex_population_filter-a-population-filter)), one
per `includes` or `excludes` list, where `declarations.render_tests` turns it on.
A declaration plan adds it for you; this command scaffolds or diffs it on its
own. It fails with the count of rows whose column breaks the list (a NULL breaks
an `includes` list and never an `excludes` one), and never selects a value. The
SQL goes through dbt's dispatch, `default__dex_population_filter` holds on every
connector, and a project overrides one warehouse with its own
`<adapter>__dex_population_filter(model, column_name, includes, excludes)` macro.
The cast a text comparison makes is dispatched apart, as
`dex_population_filter_text(column_name)`: ClickHouse cannot cast a NULL to its
non-Nullable `String`, so its variant is `toString`. So is each text literal,
`dex_population_filter_literal(text)`, written as `maintain verify` writes it:
a quote doubled on DuckDB, Postgres and Trino, and a backslash escaped on
BigQuery, Snowflake, Databricks, Redshift and ClickHouse, where it starts an
escape sequence.

## `dex_parent_population`

The generic test a declared parent population renders
([declarations](declarations.md#dex_parent_population-a-parents-population)),
twice per declared `population.parent`, once per `direction` (`missing`,
`unexpected`), where `declarations.render_tests` turns it on. A declaration plan
adds it for you; this command scaffolds or diffs it on its own. It fails with
the count of distinct eligible parent keys the model lacks (`missing`) or of
distinct model keys the parent lacks (`unexpected`), and never selects a key.
The `filters` argument scopes the eligible parents, each applied where the
parent has its column, read from the parent's metadata when the test runs. The
SQL goes through dbt's dispatch, `default__dex_parent_population` holds on every
connector, and a project overrides one warehouse with its own
`<adapter>__dex_parent_population(model, parent, key, direction, filters)`
macro. The text cast and the text literal of a filter comparison are dispatched
apart, as `dex_parent_population_text(column_name)` and
`dex_parent_population_literal(text)`, written per warehouse as
`dex_population_filter`'s are.

## `dex_unit_range`

The generic test a column declared a fraction renders
([declarations](declarations.md#dex_unit_range-a-fraction)), where
`declarations.render_tests` turns it on; a `percent` column renders none. A
declaration plan adds it for you; this command scaffolds or diffs it on its own.
It fails with the count of rows whose value sits below 0 or above 1 (a NULL
never counts), and never selects a value. It reads the column's type from the
relation's metadata and compares a column only where its type is a number as
`maintain verify` reads one (a numeric type name, and no boolean or temporal
one), so text, a boolean, a date, a UUID or JSON is not compared; dbt's own
`Column.is_number()` is not used, since it reads `DECIMAL(2,1)`, `FLOAT64` and `NUMBER(38,0)` as no
number. The SQL goes through dbt's dispatch, `default__dex_unit_range` holds on
every connector, and a project overrides one warehouse with its own
`<adapter>__dex_unit_range(model, column_name)` macro.

## `dex_join_coverage`

The generic test an INNER join a declared `references` requires (or a LEFT
join to a parent the model filters) renders
([declarations](declarations.md#dex_join_coverage-a-join-a-references-requires)),
where `declarations.render_tests` turns it on. A declaration plan adds it for
you; this command scaffolds or diffs it on its own. It reads the join's two
inputs (`child`, `parent`, their key columns, and the `child_where` and
`parent_where` filters the model applies before joining) and fails with the
count of eligible driving rows that find no parent row, matching the parent's
`DISTINCT` keys through a hit flag, so a duplicated parent key multiplies
nothing and a warehouse that fills an unmatched column with a default still
counts a miss. A row with a NULL key component is left out unless `null_keys`
is `unmatched`. It never selects a key. The SQL goes through dbt's dispatch,
`default__dex_join_coverage` holds on every connector, and a project overrides
one warehouse with its own `<adapter>__dex_join_coverage(model, child,
child_columns, parent, parent_columns, child_where, parent_where, null_keys)`
macro.

## `dex_referenced_key`

The generic test a column another model's `references` names renders on that
parent column, in the parent's YAML entry
([declarations](declarations.md#dex_referenced_key-a-key-a-references-names)),
where `declarations.render_tests` turns it on. A declaration plan adds it for
you; this command scaffolds or diffs it on its own. It fails with the count of
rows repeating a non-NULL value of the column, beyond the first of each, so a
join to that key cannot multiply rows unnoticed. NULLs never count. It never
selects a key. The SQL goes through dbt's dispatch,
`default__dex_referenced_key` holds on every connector, and a project overrides
one warehouse with its own `<adapter>__dex_referenced_key(model, column_name)`
macro.

## `dex_temporal_contract`

The generic test each measure of a declared `history` renders on the model
([declarations](declarations.md#dex_temporal_contract-a-historys-measures)),
where `declarations.render_tests` turns it on. A declaration plan adds it for
you; this command scaffolds or diffs it on its own. It fails with the count of
entities whose measure column disagrees with what the snapshot's versions and
the declared policy give, the `mismatched_entities` of `maintain verify`'s
`temporal_*_mismatch` finding for that measure. It never selects a key or a
value, and refuses to compile when a policy the measure depends on is not given.
The SQL goes through dbt's dispatch, `default__dex_temporal_contract` holds on
every connector, and a project overrides one warehouse with its own
`<adapter>__dex_temporal_contract(model, snapshot, entity, status_column, target,
measure, measure_column, order_column, time_column, initial_observation,
null_status, provenance)` macro; the text cast, text literal, timestamp type and
previous-version read are dispatched on their own
(`dex_temporal_contract_text`, `_literal`, `_timestamp`, `_lag`).

## `dex_freshness`

The generic test a time column's declared `freshness` renders
([declarations](declarations.md#dex_freshness-a-time-columns-freshness)), where
`declarations.render_tests` turns it on. A declaration plan adds it for you;
this command scaffolds or diffs it on its own. It takes `max_lag_seconds` and
fails with one row (holding `1` and the limit) when no row's value sits within
that many seconds of the warehouse's clock, or when the column holds no value.
It counts the rows within the limit, so it never computes the newest value or
the lag, which would disclose it. Each row's lag is whole epoch seconds read in
one statement, a timestamp with no time zone read as UTC, so a value exactly
at the limit passes; a column that is no date or timestamp is a compile error.
The SQL goes through dbt's dispatch, `default__dex_freshness` holds on DuckDB,
and each other warehouse has its own `<adapter>__dex_freshness_epoch(expression,
kind)` and `<adapter>__dex_freshness_now()`, the expressions `maintain verify`
sends; a project overrides one warehouse with its own
`<adapter>__dex_freshness(model, column_name, max_lag_seconds)` or either piece.

## `unpivot_json_object`

Turns a JSON object column with dynamic keys (the NoSQL-sourced shape: a
Firestore, Mongo, or DynamoDB document keyed by a related entity's id) into one
row per top-level key. It renders a complete SELECT:

```sql
select id, key as related_id, value as attrs
from (
  {{ unpivot_json_object(relation=ref('stg_entities'),
                         json_column='attributes', passthrough=['id']) }}
)
```

The contract on every connector: one row per top-level key, `key` a plain string,
`value` the warehouse's native semi-structured type, a NULL object yields no rows,
and a nested object's own field names never surface as top-level keys.

| Connector | `value` type | String-typed source column |
|---|---|---|
| BigQuery | JSON | pass `parse_json(payload)` as `json_column` |
| Snowflake | VARIANT | pass `parse_json(payload)` |
| Databricks | VARIANT (needs DBR 15.3+ or a current SQL warehouse) | pass `parse_json(payload)` |
| Redshift | SUPER | pass `json_parse(payload)` |
| Postgres | jsonb | accepted directly |
| DuckDB | JSON | accepted directly |
| ClickHouse | raw JSON text in a String | accepted directly |
| Trino | json | pass `json_parse(payload)` |

Two BigQuery quirks are absorbed by the macro: a JSON path argument must be a
compile-time literal (the macro reads values with the subscript operator, which
accepts a computed key), and `JSON_KEYS` recurses into nested objects unless
depth-limited (the macro pins depth 1). When a planned model calls the macro and
the project lacks it, the plan warns and names the scaffold command.
