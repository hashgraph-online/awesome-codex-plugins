# Maintain axes: what each command detects, holds, and costs

Lookup detail for the maintain subcommands. What you must and must not do is in
`SKILL.md`; this file says what a finding means and where it comes from.

## The baseline: `maintain snapshot`

`maintain snapshot` pins the current `.dex/cache.json`, so the grain baseline is
the exact-distinct verdicts `explore map` already computed, plus per-layer
fingerprints of the dbt project and of the semantic layer.

- **The two project layers are fingerprinted independently.** The transform
  layer comes from the dbt project; the semantic layer comes from whichever vendor
  `semantic.vendor` names, which may be dbt's own or a native format such as
  Apache Ossie, SLayer or Cube. A repository with a semantic layer and no dbt project still gets
  a baseline and runs every free axis: `transform_layer` comes back null. The
  warning that no project was fingerprinted is reserved for the case where
  neither layer answered.
- A native semantic layer contributes its definitions per dataset and per
  metric, each with a content hash, the relation behind it, the column each field
  resolves to, its declared keys in the arity they were written, and its
  relationships with every ordered column pair. Whether that side was captured is
  itself recorded, so a baseline written before it reports the relationship axis
  as unchecked rather than clean.
- Each dbt model's **declaration** is fingerprinted per model and per column: the
  model's and each column's `description`, and every key under their
  `config.meta.dex` (grain, population, assumptions; a column's role, additivity,
  unit, aggregation, null rule, references). One hash per field, never the
  declared text, so a population filter's values do not land in `.dex/`. Hashes
  are taken over a canonical form: reflowing a description, reordering a grain or
  a filter's values, or moving the entry to another YAML file is not a change.
  `data.transform_layer.declared_model_count` says how many models were
  fingerprinted (`0` is a project that declares nothing, which is a baseline;
  `null` is a format that does not read declarations). A native dbt versioned
  model is fingerprinted per version, from the entry dbt builds each version
  from, under its label (`dim_teams.v2`), so drift names the version whose
  declaration moved.
- Without a cache it captures a metadata-only baseline and says so. It warns
  when the cache it pinned is thin (objects without column detail) or older than
  the profile freshness window, because either makes "accept current state" only
  partly true.
- Past 50 objects, `explore map` profiles the top 25 by rank and enters the rest
  as metadata alone. The snapshot envelope reports `column_detail_count` against
  `dataset_count` plus a warning naming what it could not cover.
- The baseline records the engine release that wrote it (`tool_version`). Every
  axis that reads it warns when that release is not the running one, because
  drift measured across an engine change can reflect the engine as well as the
  warehouse. Re-running `maintain snapshot` re-pins it at the running release.
- `--project-only` refreshes the transform and semantic fingerprints without
  opening the warehouse, carrying the existing `warehouse` block,
  `warehouse_from`, and `cache_updated_at` forward. It requires an existing
  snapshot and refuses connection-target flags (`--connector`, `--path`,
  `--scope`, `--project`, `--dataset`).

## `maintain check`

Sweeps every axis against the snapshot and returns one report ranked by blast
radius. Read-only. `check` warns when the baseline looks stale.

## `maintain schema [<objects>]`: structural drift

Source columns and tables added, dropped, retyped, or renamed; nullability
changes; declared sources the warehouse no longer honors; a model added,
removed, or content-changed since the baseline. Free.

Under `semantic.vendor: slayer` the SLayer models are also held to the warehouse
by SLayer's own `validate-models` rules, run on the metadata Dex captured and
never through a SLayer datasource: `declared_column_missing`,
`declared_type_conflict` (SLayer's type buckets: number, string, boolean,
temporal, and a list; a column that became a list is `remedy_kind: reingest`
with the warehouse's `element_type`, and reconcile states it as a `type: ARRAY`
declaration rather than `slayer ingest`), `declared_relation_missing` (a table gone since the baseline), and
`declared_dependency_dropped` (a join, measure or filter lost to another drop).
Each carries the model's whole removal under `data.removal`, which is what
`maintain reconcile` plans.

Under `semantic.vendor: cube` the same four codes hold the cubes and views to
the warehouse by Dex's own rules (Cube compares a model only inside a Cube
server, which Dex never starts): a member whose `sql`, filter or segment reads a
column the table no longer has, a `time` dimension on a column that is not
temporal or a `number` dimension or summing measure on text, a cube's table gone
since the baseline, and a member, join or view include lost to another drop.
Each carries its cube's or view's removal under `data.removal`.

## `maintain volume [<objects>]`: freshness drift

Row counts that collapsed, spiked, or went to zero: the "is the data still
flowing?" axis, distinct from "did the shape change?". Free metadata. An object
the warehouse keeps no count for (a view anywhere, an external table on
BigQuery) is named in `warnings` as not compared.

## `maintain grain [<objects>]`: grain drift

A key that now has duplicates, a changed row-per-entity cardinality, or an
increased join fanout. It also re-verifies the grains the repository
*declares*: a dbt model-level `unique_combination_of_columns`, and a semantic
layer's own key declarations. A multi-column declaration is measured as one
complete composite, never one column at a time. Aggregates only.

- A native semantic layer's keys reach this axis and nothing else reaches them,
  since such a layer is never the transformation project. They take the
  identical billed handshake on a metered warehouse.
- The composites it re-probes are the ranked, artifact-suppressed set
  `explore profile` reported.
- Below `maintain.grain_min_rows` rows (default 100), a uniqueness-regression
  finding is damped to `low`, and the damping is named in the finding's `data`
  (`severity_floor_applied`, `grain_min_rows`).
- A single-column key that is not the grain, and is still unique together with
  a column the baseline read as constant, reads `medium`: the rows were added
  along that column (a second tenant, region or repository), and
  `data.still_unique_as` names the combination. A real duplicate repeats that
  combination too, so it stays `high`, and a lost grain always does. The same
  finding says whether the dataset's grain still holds (`data.grain_holds`),
  from the count the axis already takes; that alone never lowers the severity,
  because a surrogate grain stays unique through a real duplicate.
- Finding codes: `key_lost_uniqueness` (proven unique at baseline, not now),
  `declared_grain_not_unique` (declared, never held),
  `join_orphans_increased` (a baseline join's orphan fraction rose),
  `declared_join_orphans` (a join declared now, at 20% orphaned or more,
  `high` from 50%, that the baseline never measured or measured at or above
  that bound already; `data.baseline` is `absent`, `unmeasured` or
  `measured`; the joins come from the project and from a native semantic
  layer, not from a dbt layer's entities), and
  `join_cardinality_exceeded` (a join whose declared arity, SLayer's
  `cardinality` or Cube's `relationship`, does not hold: the side it says is
  unique is not).
- A join that declares no cardinality is named in `warnings` as unchecked.
- A key or join whose table nothing counted (no free row count, and a scan
  that does not count, as on Databricks) is named in `warnings` as not
  verified, never passed. Where the scan counts (Postgres, Trino), the check
  runs without a free count.

## `maintain semantic [<objects>]`: definition drift

Definitions changed, added, or removed against the baseline; a source relation
that is gone; a dimension, entity, measure, or declared key naming a column that
is gone; a relationship whose endpoint or column pairs no longer resolve, which
is `high` because a join nothing can resolve is a broken layer; and categorical
dimensions whose set of values widened or narrowed underneath their metrics.

The cardinality half needs a semantic model that names a table, through a
transformation model (dbt) or directly (SLayer's `sql_table`, a Cube's
`sql_table`), and categorical dimensions recorded against it. Ossie records
none, so on an Ossie layer this command is free and offers no scan.

**Declaration drift** is the third free focus of this axis. A declaration
records what a model means, so changing it changes what the model's numbers
mean with the SQL untouched, which the schema axis's `model_changed` cannot see.
Each finding names the model (`identifier`, `data.model`), the column where it
is one, and the field:

- `declaration_changed`: one field of a declaration present on both sides was
  changed, newly set, or cleared (`data.field`, `data.change` of `changed`,
  `added` or `removed`). A changed population, grain, additivity, unit or
  aggregation is `high`; a role, references, null rule, assumptions, or a
  `meta.dex` key Dex does not define is `medium`; a description is `low`. A
  cleared field ranks one step lower, capped at `medium`, and a newly set one is
  `low`.
- `declaration_added` / `declaration_removed`: a model or a column that declares
  something now and declared nothing at the baseline, or the reverse, with the
  fields under `data.fields`. A model whose whole declaration is gone is one
  finding listing its columns, and `data.model_present: false` says the model
  itself was removed too.

Each one names under `impacted_metrics` the metrics over a semantic model built
on that model. `data.declaration_drift` says whether this focus ran:
`{"checked": true, "baseline_declared_models", "declared_models"}`, or
`{"checked": false, "reason"}` with a warning. A baseline pinned before
declarations were fingerprinted is unchecked, never clean and never every
declaration newly added. So is a versioned model on a baseline that keyed its
declaration by the bare name, before declarations were read per version: it is
named under `data.declaration_drift.unchecked_models`, with
`unchecked_reason: baseline_predates_versions` and a warning, and is never
reported as removed. `maintain snapshot --project-only` baselines them without
re-measuring the warehouse, which is also how an intended declaration
change is accepted. `maintain reconcile` answers these findings with advisories
only: a declaration is a human's decision, so Dex never rewrites one to match the
baseline.

A native semantic layer (Ossie, SLayer, Cube) is compared the same way, from
each definition's own declaration: every key of the `dex` block in its
`ai_context` (Ossie) or `meta` (SLayer, Cube) and in each member's, a member's
fields keyed by the column it reads, and its primary key as the `grain`, so a
changed primary key is a `high` grain change and a `grain` written in the `dex`
block is not read. The finding names the definition (`commerce.orders`, a SLayer
model, a cube) and carries `data.layer: semantic` and `data.vendor`. With no
transformation project, `data.declaration_drift` is the layer's own status, with
its `vendor`; beside a dbt project the layer's status rides under
`data.declaration_drift.semantic_layer`, and `checked` is true only when both
were compared. A baseline pinned before native declarations were fingerprinted,
a layer whose declarations could not be read, and a change of vendor are
`checked: false` with a `reason`, never clean; `maintain snapshot
--project-only` baselines them.

The baseline records which vendor read the layer, and for SLayer the release and
model format version. A change in any of them is reported first
(`semantic_vendor_changed`, `semantic_format_changed`), and definitions are not
compared by content across it, because an upgrade changes every hash without a
definition changing.

## `maintain verify [<selector>]`: is the project right now

Needs no baseline. The classes of finding:

- **Build status**: nodes that failed; nodes skipped because a parent failed
  (naming the one that actually failed, through a chain of skipped parents);
  nodes that warned rather than failed (`node_warned`, ranked low, because a
  project running relationship tests at `severity: warn` has warnings by design);
  and models the project declares that built no relation. Each node is judged
  by the latest dated run that attempted it (#1524): every building
  `run_results.json` in the project's target path and in Dex's artifact
  directory, ordered by dbt's `generated_at`, plus the per-node record each
  `transform build` keeps in `dex_node_runs.json` (statuses only), since Dex's
  builds overwrite one file. Never the run results beside the newest manifest:
  a `dbt parse` rewrites a manifest and runs nothing. A compile is never read,
  and a node the current manifest no longer has is not reported. A run no dbt
  log names is still read, with a warning and `logged: false`, since a rotated
  log is no proof it came from elsewhere. Each finding names its run under `data.run`
  (`invocation_id`, `generated_at`, `command`, `artifact`, `cold`, `source`,
  `invoked_by`: `dex`, `outside_dex` or `unknown`, `logged` and `latest`), and `detail`
  says so in words, marking a failure read from an earlier run than the latest.
  A skip names its failed parent from its own run only.
  `data.build_status_runs` lists the runs read.
- **Row population**: `row_loss` where a model holds materially fewer rows than
  its **driving parent** (the relation in its FROM clause, followed through the
  CTE chain, as distinct from anything it joins) and nothing in its SQL accounts
  for the shortfall; `row_fanout` where it holds materially more. Each names
  every join beside its own key and states both counts. A fan-out on a model
  whose declared grain (a declaration, a `unique` or
  `unique_combination_of_columns` test, or a primary entity, never the naming
  guess) the same run proved unique is capped at `low`, with
  `data.grain_proven`: the extra rows are the grain the model declares (anchors
  times windows, a date spine times entities), not duplicates. A fan-out
  through joins whose key Dex cannot read (a range or inequality join) is
  capped at `medium`, with `data.join_key_read: false`. Both caps name
  themselves in `data.severity_cap_applied`, and the finding stays listed. A
  model with a `WHERE`, `GROUP BY`,
  `DISTINCT`, `QUALIFY`, `LIMIT`, a semi or anti join, or a set operation is never
  reported for loss, and an incremental model is skipped outright (on
  `transform build --full-refresh --verify`, only one the build did not rebuild,
  or a microbatch model). A model that
  generates its rows in SQL, such as `range(...)` or a `VALUES` clause, has no
  parent relation. That is named in `notes`. A model whose driving parent is
  the project's time spine (a `time_spine:` config, or the
  `metricflow_time_spine` name) or a model generated in SQL
  (`dbt_utils.date_spine` included) is not compared either, since the spine
  supplies anchors rather than a population, and `notes` names it (#988). A
  model that only joins a spine keeps its check. A real parent relation that is
  absent from the warehouse is still a warning.
- **Column contract**: `column_missing`, `column_undeclared` and
  `column_type_mismatch`, the built relation's columns against `schema.yml`.
- **Grain**: `grain_broken`, from one source per model, in this order: the
  grain the model's declaration states (`config.meta.dex.grain`, so a
  composite grain is checked with no `dbt_utils` test), a `unique` test, a
  `unique_combination_of_columns` test, a semantic model's primary entity,
  then a naming guess. `data.source` says which one. A declared grain is
  counted in the declared-fact statement below, so it is priced with it.
  `data.grain_coverage` (#1223) holds one record per declared key, whichever
  source declared it (`model`, `columns`, `source`, `status`, `reason`,
  `measured`), so a key that held is stated rather than read out of an absent
  finding. `status` is `proven` (the exact distinct count reached the row
  count), `broken` (beside its `grain_broken` finding), `not_applicable`
  (`empty_relation`), `unchecked` or `not_planned` (`priority`: a key from a
  lower-ranked source the model's checked keys displaced; one on the same
  columns as a checked key is judged by it and gets no record of its own).
  `unchecked` names its `reason`: `no_relation`, `ambiguous`,
  `metadata_unreadable`, `missing_columns`, `scan` (the connector could not
  run the count), `scan_offered`, `no_count`, `refused` or `not_measured`. The
  naming guess has no record, and the field is absent when the grain class is
  suppressed. Only `proven` is a pass. `measured` carries the row and distinct
  counts where both were read; the warehouse's own words stay in `notes`.
- **Join contract** (#228, #857): every equality join's coverage, measured
  with one aggregate probe per driving relation and recorded under
  `data.join_coverage`, one record per join:
  - `declared`: what the declaration says about the join. It is `required` when
    a column it supplies is declared `null_rule: never` on a LEFT join, or the
    column carrying the driving key declares a `references` that names the
    joined relation, whatever its `role` and on a LEFT join too (#1459): a
    `references` means every non-null value exists in the parent, which is how
    the `relationships` test it renders reads it, so a missing reference is
    written as a NULL and passes both. A version label
    (`dim_teams.v2.team_id`) names that version's relation, and a bare name
    the version an unversioned `ref()` resolves to. `optional` is set when every column it supplies
    states a NULL rule other than `never`. NULL keys are `excluded`, or
    counted `unmatched` where the key's column is `null_rule: never`.
  - `measured` and `coverage`: eligible, matched and unmatched rows and
    distinct keys, NULL-key rows apart. Coverage is `null` when nothing is
    eligible.
  - `key_conversion` (#861), on a join that compares a key through a cast or a
    `lower`, `upper` or `trim` (`try_cast(a.k as int) = b.k`): each side's keys
    as the probe applied them, a hard cast measured as its safe form. Keys the
    conversion fails on stay eligible and unmatched, and are counted apart as
    `measured.conversion_failed_rows` and `conversion_failed_keys`, so a failed
    cast reads differently from a missing parent.
  - `effective_input` (#1085, #1324), on a join one of whose sides is read
    through a filtering or grouped CTE or subquery: per side, the physical
    `relation`, the scopes it was read `through` and the `filters` the probe
    applied to it. The measured counts are over those rows, so a key present
    only in rows the filter drops is not a match. Carried only when every
    filtering hop reads one relation, its only reducing clause is a `WHERE`,
    and each conjunct is a row-by-row condition over columns and literals
    (comparisons, `IN` over a literal list, `BETWEEN`, `LIKE`, `IS`, boolean
    logic, `coalesce`, casts and `lower`/`upper`/`trim`, as in
    `where coalesce(_fivetran_active, true)`) that traces to the key's own
    physical relation. A side grouped by *exactly* the join's key columns
    (a direct `GROUP BY` over one input, with no `HAVING`, window, `LIMIT`,
    set operation or grouping modifier (`ROLLUP`, `CUBE`, `GROUPING SETS`,
    `GROUP BY ALL`), and optionally the supported `WHERE`) also carries
    `grouped_by`, the key columns it groups by. That side is probed over its
    groups, never the ungrouped relation underneath, and its own denominator
    is `measured.group_rows`. Its aggregate outputs are attributed through the
    model's final projections, so `null_rule: never` on a renamed output
    (`o.total_amount as spend`) still makes the join required, and an
    aggregate the model does not project is not treated as supplied. A grouping by anything else (an extra column, a
    subset of a composite key, an expression, or a grouping inside another
    grouping) stays `filtered_cte`.
  - `status`: `satisfied`, `contradicted` (with the finding), `not_applicable`
    (an empty input or all-NULL keys: no coverage, which is not full coverage)
    or `unchecked`, with a `reason_code`: `non_equality_join`,
    `unsupported_key_expression` (a key rewritten by a function other than a
    cast, `lower`, `upper` or `trim`), `no_safe_cast_on_connector` (a cast key
    on Postgres, which has no cast that returns NULL, to a type other than
    `smallint`, `integer` or `bigint`: those are measured through a guarded cast), `key_and_filter_condition`, `ambiguous_using`, `unresolved_column`,
    `set_operation_cte` (a column read through a UNION CTE, which is not a
    warehouse table), `filtered_cte` (a reducing scope of any other shape: a
    `GROUP BY` other than exactly the join's key columns, `DISTINCT`, `LIMIT`,
    `HAVING`, `QUALIFY`, a join beside the
    filter, a subquery or clock function in it, or a filter on a computed or
    window column such as `rn = 1`, or a join that can drop rows of the
    relation the key is read from: an inner, bare, comma or CROSS join, a
    RIGHT join with the key on its left, or a LEFT join with the key on its
    joined side; the reason names the scope and the shape),
    `unparseable_sql`, `relation_not_found`,
    `probe_refused` or `scan_offered`.

  Findings:
  - `join_no_match` (high): a nonempty eligible population matched nothing.
    No threshold. `low` when every column the join supplies is declared as
    allowed to be NULL.
  - `join_orphans` and `join_zero_overlap`: on a required join any unmatched
    row (`threshold_source: contract`, high). With `declarations.render_tests`
    on, an INNER join so required also renders `dex_join_coverage`, a build
    test reading the same two inputs and failing with the same
    `unmatched_rows` (#1456); a LEFT one to the whole parent leaves that to
    `relationships`.
    Otherwise the stated defaults,
    0.2 and 0.9 of eligible rows (`threshold_source: default`). On a LEFT join
    with no requirement (no `references` on its driving key), unmatched rows are the optional relationship the join
    writes: no `join_orphans`, and `join_zero_overlap` at medium. On an INNER
    join with no requirement whose unmatched rows the declaration accounts for
    (an `assumptions` entry whose `column` names the driving key column, or a
    `population.filters` entry on it), the join is the model's filter: the
    record is `satisfied`, keeps its measured counts, and names the entry
    under `unmatched_accounted_for` (`by`: `assumption` or
    `population_filter`, the `column`, and the `withheld_finding` the default
    would have raised). `join_no_match` still stands (#1162).
  - `join_field_all_null` (high): a column the join supplies, declared
    `null_rule: never`, NULL on every row. `join_field_newly_null` (medium):
    one with no rule, NULL on every row, where the exploration cache profiled
    the same relation with values in it. Otherwise the column is listed on the
    record as `derived_columns_all_null`, not reported.
- **Declared facts** (#496), each an aggregate-only statement against the
  built relation:
  - `unit_out_of_range` (medium): a column declared `fraction` with values
    outside 0 to 1, or declared `percent` whose values all sit within 0 to 1.
    States the observed `min` and `max`; the second case is a question, not
    proof, since genuinely small percentages land there too.
  - `additivity_contradicted` (medium): a column declared `additive` that the
    cumulative detector reads as a running total. The probe orders by the
    declaration's own entity and time columns (a composite grain, or the
    `foreign_key` and `time` roles).
  - `population_contradicted` (high): a value a `population.filters` entry
    excludes still present (for `includes`, any other value or NULL), as a
    count and never as rows.
  - `parent_population_missing` (high) and `parent_population_unexpected`
    (high), for a model declaring `population.parent` (#857): eligible parent
    keys with no row in the model, and model keys the parent does not have,
    as distinct-key counts. A population filter whose column the parent also
    has is applied to the parent first (`excluded_by_filters`); one it lacks is
    named in `filters_unapplied` and drops the missing finding to medium.
    Unexpected keys are never the population. Each declared parent has a
    record under `data.parent_population` with the same statuses as a join.
    The parent may be an installed package's model (#1155), measured on the
    relation the manifest names for it; with `--target dev` (and on a build's
    `--verify`) a package that sets `+schema` is read in the
    `<dev schema>_<name>` namespace dbt built it into.
  - `population_delta` (high with orphan keys, medium with missing parents,
    low for parents kept with no children), on `transform build --verify`
    only, for a built model that declares no `population.parent` (#1228): the
    same counts against the parent dex drafts for it, plus the rows whose child
    columns are all NULL or zero (a sign of parents kept with no children, not
    proof: children whose amounts sum to zero read the same). It asks which rows the model is for rather
    than calling any of them wrong. Its records are under
    `data.verification.population_delta` (`satisfied`, `needs_decision`,
    `settled`, `not_applicable`, `unchecked`), and it is never named in
    `suppressed`. Not every such model gets one: with `--for-plan` only the
    plan's models are drafted (one the draft cannot reach is `unchecked`),
    without it at most 25, and a model nothing could be drafted for is named in
    `notes`, so an absent record does not mean the model was checked.
    `maintain verify` measures declared parents only.
  - `temporal_transition_count_mismatch`, `temporal_latest_transition_mismatch`
    and `temporal_first_attainment_mismatch` (high), `temporal_population_missing`
    and `temporal_population_unexpected` (high), and
    `temporal_provenance_contradicted` (medium), for a model declaring `history`
    (#1027): its columns against what the snapshot's versions and the declared
    policy give, as entity counts. Each contract has a record under
    `data.temporal_contracts`, keeping the snapshot's execution, the assertions
    checked, and what stayed unchecked apart. `no_history_observed` and every
    `unchecked` reason are not clean: see the transform skill's `declarations.md`,
    "Temporal contracts".
  - `freshness_exceeded` (high on a `capture` basis, medium on `business`), for
    a time column declaring `freshness` (#1460): its newest value trails the
    warehouse's clock by more than `max_lag`, read in one statement as whole
    epoch seconds, or it holds no value at all (`reason: no_rows` or
    `all_null`), since no rows is not fresh. Each declared freshness has a
    record under `data.freshness` (`satisfied`, `contradicted`, or `unchecked`
    with `not_temporal`, `column_missing`, `probe_refused` or `scan_offered`).
    A `business` time can be legitimately old after a quiet period or a
    backfill, which the finding says; a `capture` time cannot.
  - `deadline_missed` (high on a `capture` basis, medium on `business`), for a
    time column whose `freshness` declares a daily `deadline` in a `timezone`
    (optionally on `days` only): the deadline has passed today on the
    warehouse's clock and the column holds no value from today's local
    midnight on (`reason: not_today`, `no_rows` or `all_null`). The day is read
    from the runner's clock in that zone, as Elementary's `data_freshness_sla`
    reads it, and the check is counts only. Each deadline has its own record
    under `data.freshness` (`check: deadline`, beside a lag's `check:
    max_lag`), `not_applicable` before the deadline (`before_deadline`) or on a
    day `days` leaves out (`not_scheduled`). On a `business` time a nightly
    load of the previous day's events misses every day: the deadline belongs on
    the load time.

  `null_rule: never` is not checked here: it renders as a `not_null` test.
  `data.suppressed` names `unit`, `additivity`, `population`,
  `parent_population`, `temporal` and `freshness` whenever one
  did not run: nothing declares it, the relation is empty, the column is all
  NULL or aggregated away, too few observations to call, or the scan is
  offered.
- **Declared foreign keys, on a project format with no dbt artifacts**
  (#1197). dbt runs a `relationships` test itself and build status reads its
  result, so on dbt this does not run. Any other project format (one named
  under `project.format`) has each declared foreign key measured against its
  parent with the join contract's coverage probe, priced in the same single
  offer, and one record per key under `data.foreign_key_coverage`:
  - `model`, `column`, `to_model`, `to_column` and `source`, as the format
    declared the key, so two keys to the same parent stay apart.
  - `relation` and `to_relation`: where the format places each side, through
    `model_relations` (a source parent through `source_relations`). A model the
    format places nowhere is never looked up by name, since a same-named table
    elsewhere is not the relation it declared.
  - `measured` and `coverage` as on a join, with `null_keys: excluded`: a NULL
    child value is not constrained, as in dbt, and is counted apart.
  - `status`: `satisfied`, `contradicted` (with the finding), `not_applicable`
    (`empty_input`, `all_keys_null`) or `unchecked` with a `reason_code`:
    `no_declared_relation`, `relation_not_found`, `metadata_unreadable`,
    `column_not_found`, `probe_refused` or `scan_offered`. None of these is
    clean.

  `foreign_key_orphans` (high): any non-NULL child value the parent lacks
  (`threshold_source: contract`, threshold 0), stated as row and distinct-value
  counts. `data.suppressed` names `foreign_key_contract` when no key ran: the
  format declares none (in scope), declares nothing readable, or the warehouse
  is unreachable.

A project that does not compile is reported first and suppresses everything
else. `data.suppressed` names every class that did not run and why.

## `maintain coverage [<selector>] [--mutate]`: where the tests are

Needs no baseline and costs nothing: it reads a fresh `dbt parse` of a
throwaway copy of the project and opens no connection. It reports, it never
gates: `status` is `ok` whatever the coverage. `--mutate` is the one exception:
it refreshes stale and missing mutation scores, and that runs dbt (see below).

- **Sections.** `models`, `sources`, `snapshots` and `seeds` hold the root
  project's enabled resources. An ephemeral model is counted and marked
  `ephemeral`: dbt inlines it into its own tests and the models that read it.
  Package and disabled resources are in no denominator; `excluded` counts and
  names them with the reason, and counts disabled tests and tests on an excluded
  resource.
- **Own tests.** `own_tests` counts `generic` (attached to the resource),
  `singular` (a test file that reads it), `unit` (a unit test on that model) and
  `freshness` (a source's declared check) apart, and `severity` splits its data
  tests into `error` and `warn`. `tested` is true when any own test exists.
- **Downstream.** `downstream_tests.count` is the data tests on the resources
  that read this one, and `on` names those resources. They never count as its
  own coverage. A unit test on a downstream model is not one: it reads fixtures.
- **Incremental.** `incremental.incremental_branch_tests` names the unit tests
  that override `is_incremental` to true. Empty means no test runs the next
  incremental run, whatever the full build's tests say.
- **Columns.** `documented` is what `schema.yml` documents, `asserted` the
  documented columns a generic test is attached to, `unasserted` the gaps, and
  `undocumented_tested` the tested columns `schema.yml` does not document, which
  count nowhere. A column a singular test only reads is not asserted; it is
  `referenced` (below).
- **Referenced.** `columns.referenced_columns` lists each column a singular test
  reads, with the `roles` it is read in (`predicate` for WHERE, HAVING, QUALIFY
  and CASE conditions, `join`, `aggregation`, `grouping`, `projection`), the
  `tests` that read it, and whether it is `documented` and `asserted`. Columns
  only a singular test reads sort first. `columns.referenced` counts the
  documented ones, `columns.referenced_only` those no generic test asserts, and
  `summary.<section>.columns_referenced_only` is that count as its own ratio,
  never added to `columns_asserted`. Judge by role: a `join` read asserts
  nothing about the key, while a `predicate` read usually does. A singular test
  is rendered statically (`ref()`, `source()`, a `var()` with a literal
  default). One that other Jinja generates is read from the newest compiled
  manifest on disk, but only where that manifest holds the test with the same
  checksum. `data.singular_tests` counts the tests read (`resolved`, `partial`,
  `unresolved`), says where each was `read_from`, and names every test read in
  part or not at all with a `reason_code`: `macro_generated`, `jinja_block`,
  `unparseable`, `ambiguous_relation`, `unknown_relation`, `untraced_columns`
  (an unqualified column in a select over several relations, which needs a
  catalog this command does not read), `reads_no_column` or `no_sql`. Such a
  test is never read as reading nothing. Names and counts only: no SQL,
  expression or literal.
- **Summary.** `data.summary` leads the payload. Every ratio is
  `{numerator, denominator, of}`, and `of` names the denominator. Presence, unit
  tests, downstream-only protection, incremental branches and asserted columns
  are separate ratios; there is no blended coverage percentage.

A generic test is named by the test it applies (`not_null`,
`dbt_utils.unique_combination_of_columns`) and its column, never by its node
name: dbt names an `accepted_values` test after the values it accepts.

Lists are capped (25 resources per section with untested ones first, 12 tests
and 12 column names per resource, 10 downstream names, 25 excluded resources),
each cut counted in `data.elided` and named in `notes`; `--full` lifts them. The
summary always counts everything. A project that does not parse is reported
first and suppresses the inventory. Where dbt cannot parse at all (dbt or
`profiles.yml` missing, a declared package not installed), the newest manifest
on disk is read, `data.manifest.source` is `artifact` with its `generated_at`,
and a warning says tests changed since then are not reflected.

### Three more answers, each on its own

Presence, last-run status, mutation strength and declaration coverage are
separate questions. Report each with its own denominator; never fold them into
one coverage number.

- **Last run.** Each test carries `last_run`: `pass`, `fail`, `warn`, `error`,
  `skipped`, or `not_run` when the latest run did not include it. `not_run` is
  never a pass. `data.last_run` names the one run read (the newest
  `run_results.json` a `dbt build`, `test` or `run` wrote, from Dex's artifact
  directory or the project's target path) with its `generated_at` and
  `age_seconds`. Quote the age with the status: a status describes that run, not
  the project now. With no run results every test is `not_run` and a note says
  so; results from an invocation no dbt log names are not attributed. A source's
  freshness check reports no `last_run`: `dbt source freshness` writes its own
  artifact.
- **Strength.** A model carries `strength`, the score its last
  `transform test --mutate` recorded. `fresh` means the model's SQL as written and its own tests
  are what the run measured, and every downstream test it ran still reads the
  same. `stale` lists what `changed` (`model_sql`, `own_tests`,
  `downstream_tests`); its score is shown with its age and is not current.
  `missing` has no record, and `untestable` has no test, own or downstream, so
  `--mutate` would refuse it. `score` (the model's own tests) and
  `score_with_downstream` stay apart, and `complete: false` marks a run the
  budget stopped. `summary.models.strength` counts each status and bands the
  fresh scores; there is no project mutation score. A score counts only the
  defects Dex plants. The digest reads the SQL as written: a change in a macro
  the model calls, a parent's SQL, or a materialization set in
  `dbt_project.yml` does not stale it, so refresh after such a change
  yourself. Refresh one with `dex transform test --mutate <model>`, or every
  stale and missing one with `--mutate` (below). `untestable` with a `reason`
  (`no_mutable_sql`) is a model a run refused for its SQL alone: no comparison,
  filter, join, CASE, division, window frame or aggregate to plant a defect in.
  It reads `missing` again once its SQL or tests change.
- **Refresh (`--mutate`).** Runs `transform test --mutate` for each `stale` and
  `missing` model, then reports the sections as they now stand. Models run in
  the order the selector names them; with no selector, `missing` before
  `stale`, upstream before downstream, then by name. At most 25 run per call:
  `--max-models` narrows that and is refused above 25. `refresh.elided` names
  the rest, and running the command again continues with them.
  - On a metered connector every model is planned and priced first for free,
    and the batch is confirmed once (`needs_confirmation` with a line per
    model). Each run then draws on what the confirmed budget has left. A model
    the budget stopped part way is `complete: false`, and every model after it
    is under `refresh.not_run` with `reason_code: budget`. Free on DuckDB. Dev
    target only (`--target`).
  - `refresh.skipped` lists models a run would refuse, read off the manifest at
    no cost and not counted toward the cap: Python models, models with a
    `sql_header`, and, on a metered connector, a model only
    downstream tests read (`downstream_only`), since routing a mutant through
    them is opt-in there (`transform test --mutate <model> --downstream`).
  - Each version of a versioned model is a model of its own: it reads its own
    strength and is refreshed by its label (`fct.v2`).
  - A model whose tests pass no baseline is recorded too: it reads `missing`
    with `last_refusal`, and a refresh retries it after the models it has not
    tried yet, so it never holds the first slots. It never replaces a score
    that still describes the model.
  - `refresh.refused` lists the runs that refused, with a `reason_code` and the
    reason.
  - `refresh.refreshed` lists the models measured, with what each `was`, its
    scores, and whether it was `recorded`.
  - Refused in values-free mode, since `transform test --mutate` is not
    reviewed for it.
- **Declarations.** `data.declarations.facts` holds one record per declared fact
  on the selected models: `fact` (`grain`, `key`, `foreign_key`, `references`,
  `null_rule`, `population_filter`, `population_parent`, `population_rule`,
  `unit`, `additivity`, `history`, `freshness` (a lag and a deadline are two
  records), `continuity`), `column`, and
  `checked_by`: `dbt_test` (the generic `tests` that assert it run on every `dbt build`), `dex_verify` (the
  `verify` finding codes that can judge it on `maintain verify` or
  `transform build --verify`; that verify *can* judge it, not that it ran), `both`, `none`,
  or `prose` for a population stated only as a rule, which nothing can run.
  Unchecked facts come first. `summary.facts.checked` leaves prose out of its
  denominator, and `models_undeclared` counts models with no declaration apart
  rather than as zero coverage. A `references` counts as `dex_verify` only where
  the model reads the referenced model, since verify judges it through a join
  the model's SQL writes. Every record names its `source`, `dbt` or the vendor.
  A native semantic layer's keys and joins come from the fingerprint `maintain
  grain` re-verifies: a key names `declared_grain_not_unique`, a join
  `declared_join_orphans`, plus `join_cardinality_exceeded` where it is declared
  `many_to_one` or `one_to_one`, and a `many_to_many` join neither. What its
  `dex` metadata states reads `none`. A fact a dbt model and the layer both
  declare on one relation, spelled alike (a quoted part keeps its case, so
  `DB.SCHEMA.ORDERS` and `"DB"."SCHEMA"."ORDERS"` are two), is listed per source
  with `also_declared_by` and counted once.

## `maintain reconcile [<class>]`

Proposes the dbt edits that bring the project back in sync, as reviewable diffs,
optionally scoped to `schema`, `volume`, `grain`, or `semantic`. It composes every
layer's declarations first, so a grain the semantic layer already declares is not
proposed as though nothing declared it.

- `mechanical`: on a dex-scaffolded staging model it edits each drifted column
  into the model and nothing else: one projection added to or removed from the
  list the model names its columns in, and one entry in whichever YAML file
  already declares the model (a shared `models/schema.yml` included; Dex never
  writes a second declaration beside it, and never invents a test). The model is
  never regenerated, so a hand-written cast, rename or filter survives. On a
  project format that places a declaration but authors no staging model, it
  edits the drifted columns into that declaration.
- A dropped column the model's own logic still reads (`status as order_status`,
  `md5(status)`, a `where` on it) is advisory and names the use, since what that
  logic becomes is a decision. A model downstream that still reads the dropped
  column is named in `warnings`. Drift the project already reflects (an applied
  plan added the column) is advisory and stores no plan: re-run
  `maintain snapshot` to baseline it.
- `advisory`: the decision surfaced, at most backed by a test edit. It declines
  that test where the test would be wrong: if a model declares a composite grain
  covering the column, no column-level `unique` is proposed on it, and the warning
  names the combination.
- Type changes: nothing Dex writes declares a type, and the type it holds is the
  connector's own spelling (Snowflake reports `NUMBER(38,0)` and `NUMBER(10,2)`
  both as `FIXED`), so the proposal names both spellings.

## Cube layers (`semantic.vendor: cube`)

Every axis runs on a Cube layer, beside a dbt project or with none, and none
starts a Cube server or Node: each reads the configured model files and the
metadata Dex captured through its own connection. The wrapper installs the
`[cube]` extra for every `maintain` command where the vendor is `cube`.

| Axis | On Cube |
|---|---|
| `snapshot` | fingerprints each cube and view, each measure (as `cube.member`), each primary key (a composite one whole), and each join with its ordered pairs and arity; records `vendor: cube` and the validator release. Each compiled-only definition is recorded by its content (`opaque_definitions`) |
| `schema` | adds the four `declared_*` codes on Dex's metadata: `declared_relation_missing` (a cube's table gone since the baseline), `declared_column_missing` (a member whose `sql`, filter or segment reads a column the table no longer has), `declared_type_conflict` (a `time` dimension on a column that is not temporal, a `number` dimension or a summing measure on text), and `declared_dependency_dropped` (a member, join or view include that reads something that goes). A table neither the connection nor the baseline lists is a note, not a finding, and an expression Dex cannot read is named in `warnings` as unchecked |
| `volume` | unchanged: it reads the warehouse, not the layer |
| `grain` | measures every `primary_key` (a composite one whole) and every join's `relationship` (`join_cardinality_exceeded`; a `one_to_many` join is checked on its one side). Cube requires a `relationship`, so a join without one does not load; a join whose `sql` is not an equality of columns is named in `warnings` as unverified |
| `semantic` | definition drift free as everywhere, with `definition_changed` on a cube naming its table; a compiled-only definition whose content changed is `compiled_only_changed`; the dimension-cardinality half re-counts every non-time dimension that is one column (offered as a scan on a billed connector) |
| `reconcile` | stores the `declared_*` removals as a second plan, `data.semantic_plan_id`, through `semantic cube update`, cutting only the entries that go. A cube whose table is gone is never removed, and a view source whose join path walks a removed join, and the join it walks, stay advisory |
| `verify` | checks the dbt project only; Cube's keys and joins are measured by `grain`, not here |

A compiled-only file or element (JS, Jinja, `extends`) is compared by its content
alone, never structurally: a change is reported as `compiled_only_changed`, what
changed is not read, and the warning saying so rides every `maintain semantic`
and `maintain check` while the layer holds one, so the layer never reads clean.

A measure whose `filters` read a dropped column goes with the column rather than
losing its filter, because a filter removed quietly changes what the number
counts.

## Databricks Metric View layers (`semantic.vendor: databricks`)

Every layer-neutral axis runs on a Metric View layer, beside a dbt project or with
none, without a workspace connection to read it: each reads the configured files
and the metadata Dex captured through its own connection. The wrapper installs the
`[metric-views]` extra for every `maintain` command where the vendor is
`databricks`.

| Axis | On Metric Views |
|---|---|
| `snapshot` | fingerprints each view, each joined table that is not another view's source (`view.join.path`, with the fields that read it and its `rely` key), each measure (as `view.measure`), and each join with its ordered pairs, oriented child to parent; records `vendor: databricks`, the ported converter commit and `format_version: 1.1`, and each file's declared `version` under `definition_versions` |
| `schema` | adds the four `declared_*` codes, each naming the view, the element (`dimensions['region']`, `measures['revenue']`, `joins['customer.nation']`, `filter`, `source`) and the column. `declared_column_missing`: a field, measure, `filter`, join `on`/`using`, or query `source` reads a column its table no longer has. `declared_relation_missing`: the view's `source` (the whole view) or a join's `source` gone since the baseline. `declared_type_conflict`: a `date`/`date_time` format on a column that is not temporal, a number, currency, percentage or byte format on text, or `SUM`/`AVG` over text. `declared_dependency_dropped`: a field, measure (through `MEASURE()` too), window, or nested join that loses an input to another removal. A relation neither the connection nor the baseline lists, and an expression Dex cannot read, are named in `warnings` as unchecked |
| `volume` | unchanged: it reads the warehouse, not the layer |
| `grain` | measures each `rely.at_most_one_match` key (`declared_grain_not_unique`, worded as the view's claim and carrying `declared_by: databricks`, `claim: unique`, since Databricks trusts the flag and returns wrong numbers when it is false) and each join's declared arity (`join_cardinality_exceeded`, a `many_to_one` join whose joined side is not unique, `rely` or not) |
| `semantic` | definition drift free as everywhere: a view, measure or join added, removed or changed, and a field reading a column the warehouse no longer has. A view re-saved in a spec version Dex does not read is `semantic_format_changed` for that file, naming it and both versions; the other views are still compared by content |
| `reconcile` | the schema findings' removals are cut out of the view files and stored as a `semantic databricks update` plan under `data.semantic_plan_id`, validated by the reader before it is stored: each removed field, measure and join (a nested join goes with its parent), and a contradicted `format` (the member stays). Every other byte is kept and `on:` stays text. Advisory, never written: a view or join whose `source` is gone, a `filter` reading a dropped column (the view's population), a query `source` reading one, a removal a `materialization` names, one that would leave no field and no measure, and a file already holding a key Databricks refuses |
| `verify` | checks the dbt project only |

## Snowflake Semantic View layers (`semantic.vendor: snowflake`)

Every layer-neutral axis runs on a Semantic View layer, beside a dbt project or
with none, without a Snowflake connection to read it. The wrapper installs the
`[semantic-views]` extra for every `maintain` command where the vendor is
`snowflake`.

| Axis | On Semantic Views |
|---|---|
| `snapshot` | fingerprints each logical table (`view.table`, with its members' columns and its primary and unique keys, each key's claim recorded under `key_claims`: `primary` for `primary_key`, `unique` for each `unique_keys` entry), each table and view-level metric, and each key-equality relationship with its ordered pairs and arity (`many_to_one`, `one_to_one` or `many_to_many`); records `vendor: snowflake` and Dex's rule-set revision as `format_version`, and each table's primary key as its declaration (`declarations`), since a Semantic View has no metadata key. The hash covers a canonical form, so a view read back from Snowflake (upper-case names, defaulted `access_modifier` and `data_type`) fingerprints as its file |
| `schema` | adds the four `declared_*` codes, each naming the view, the element (`tables['orders'].dimensions['region']`, `tables['orders'].primary_key`, `relationships['orders_customers']`, `tables['paid'].base_table.definition`, `metrics['aov']`) and the column, from the metadata Dex captured with no Snowflake object created (#1293). `declared_column_missing`: a dimension, time dimension, fact or metric, a relationship's columns on either side, a `primary_key` or `unique_keys` entry, or a `base_table.definition` query reads a column its table no longer has. `declared_relation_missing`: a logical table's `base_table` gone since the baseline. `declared_type_conflict`: `SUM`/`AVG` over text (`high`: Snowflake creates the view and fails every query reading it), a time dimension over a column that is not temporal (`medium`: Snowflake answers with the column's values, so it is advised and never cut), and a declared `data_type` in another family than the warehouse's (`low`: Snowflake ignores it and records the column's own). `declared_dependency_dropped`: everything the reader would then refuse, to a fixpoint: a member reading a removed member, a member reading across a removed relationship, a derived metric reading a removed metric. A relation neither the connection nor the baseline lists, a `definition` Dex cannot read, and an expression the reader refused are named in `warnings` as unchecked |
| `volume` | unchanged: it reads the warehouse, not the layer |
| `grain` | measures each primary and unique key and each relationship's arity, worded as the view's claim with `declared_by: snowflake` and `claim` (`primary` or `unique` for a key, the arity for a relationship), since Snowflake trusts a declared key without checking it and a query through a relationship to a duplicated key counts its rows more than once. A key that never held is `declared_grain_not_unique`; one measurement proved unique at the baseline lapses as `key_lost_uniqueness` and names the claim too. `join_cardinality_exceeded` says Snowflake infers the arity from the referenced table's key. An ASOF or range relationship states no arity and is named unchecked |
| `semantic` | definition drift free as everywhere: a table, member, metric or relationship added, removed or changed. A changed primary key is `declaration_changed` on `grain`. A move to a newer pinned rule set is `semantic_format_changed`, not every definition changed |
| `reconcile` | the schema findings' removals are cut out of the view files and stored as a `semantic snowflake update` plan under `data.semantic_plan_id`, validated by the reader, strict rules included, before it is stored: each removed dimension, time dimension, fact, metric, derived metric and relationship, with the comments written directly above it, and a contradicted `data_type` (the member stays). An emptied list is written `[]`, which Snowflake accepts. Every other byte is kept. Advisory, never written: a logical table whose `base_table` is gone (never removed automatically), a key naming a dropped column, a `definition` query reading one, a time dimension over text, a removal the reader would refuse or that leaves the view no member, and a file already holding what authoring refuses. A key or relationship arity the data contradicts is advice naming `semantic snowflake update` |
| `verify` | checks the dbt project only |

A deployed semantic view is never inventoried: `SHOW VIEWS` does not list one,
and a plain `SELECT` on one fails, so no profile or grain probe reaches it.

## SLayer layers (`semantic.vendor: slayer`)

Every axis runs on a SLayer layer, and none opens a SLayer datasource or SLayer
storage: each reads the configured model files and the metadata Dex captured
through its own connection. The wrapper installs the `[slayer]` extra for every
`maintain` command where the vendor is `slayer`; without it a command refuses
with `reason: prerequisite` and names the install.

| Axis | On SLayer |
|---|---|
| `snapshot` | fingerprints each model (minus the values SLayer caches), each saved measure, each declared key, and each join with its ordered pairs and `cardinality`; records the vendor, the SLayer release and the model format version |
| `schema` | adds the four `declared_*` codes, SLayer's `validate-models` rules on Dex's metadata. A model backed by `sql` or `source_queries` is named as not compared |
| `volume` | unchanged: it reads the warehouse, not the layer |
| `grain` | measures every `primary_key` (a composite one whole) and `unique` column, and every join's declared `cardinality` (`join_cardinality_exceeded`); a join with none is named in `warnings` as unchecked |
| `semantic` | definition drift free as everywhere; the dimension-cardinality half re-counts every non-temporal column on the model's `sql_table` (offered as a scan on a billed connector) |
| `reconcile` | stores the `declared_*` removals as a second plan, `data.semantic_plan_id`, through `semantic slayer update`. A whole model is never removed; that and a type conflict's alternative stay advisory |
| `verify` | checks the dbt project only; SLayer's declared keys are measured by `grain`, not here |

What SLayer does not declare is not drift: it has no entities, no measures in
MetricFlow's sense (a saved measure is a formula), no per-measure time
dimension, and no `model_ref` (a model names its table directly). Read `unavailable` rather than reporting an
absent element kind.

Two things look like drift and are not:

- **A format-version mismatch in a file.** The reader refuses a model file in
  any format `version` but the pinned release's current one, names it in
  `warnings`, and its definitions come back as `definition_removed` because the
  file was not read. Repair the file with `semantic slayer update`, then re-run.
- **A release or format upgrade of the layer.** Reported once as
  `semantic_format_changed`, with definitions not compared by content until
  `maintain snapshot` baselines the new format. Added and removed definitions are
  still reported.

## `maintain diagnose`: a source that arrived late

A completeness or freshness test (`relationships`, `dex_parent_population`,
`dex_freshness`, or Elementary's `volume_anomalies`, `freshness_anomalies` and
`data_freshness_sla`) can fail because the loader landed rows after the run
that read them. Diagnosis answers it as `source_arrived_late` (owner `loader`)
for each source the failing test's lineage reads.

- **The capture column** is the source's dbt `loaded_at_field`, else a column a
  model reading the source directly declares with `freshness.basis: capture`.
  `evidence.capture_source` says which. A business timestamp is never read as
  an arrival time.
- **The event column** places a row in a run's window: the test's own time
  column, else (when the test names none, or names the capture column) the one
  `time` column the tested model declares (`evidence.event_source`).
- **The windows**: the failing run's is the rows whose event time falls after
  the last passing run's start and through its own; the last pass's is the
  window of the same width before its start. For a freshness test that names
  `max_lag_seconds`, each window is that lag before its run's start
  (`window_basis`). Each carries `window_rows`, `late_rows` and
  `null_capture_rows`. The last pass's `late_rows` counts only rows that
  landed after it and before the failing run: a row still missing at the
  failing run is the failure's own lateness.
- **Confirmed** when the failing window has late rows and the last pass's has
  none. Rows with no capture time, where they leave the answer open, make it
  `no_capture_time`. **Ruled out** on `arrived_before_run` (no late rows) or
  `lateness_unchanged` (the last pass's window was late too). **Not checked**
  on `no_capture_time`, `no_run_times`, `window_unknown`,
  `source_not_listed`, `firewall_refused`, `warehouse_refused` or
  `scan_offered`.
- `corroborated_by` lists a freshness test that failed on the same lineage in
  the range. It is evidence only, and never changes the answer.
- The read is six counts per source, priced with the other checks, and
  offered alone under `price.checks.arrival_offered` when only it does not
  fit. It reads the source as it stands now, so a row deleted since is not
  seen and a redelivered row reads as late.

## `maintain diagnose`: who reads the broken column

`maintain diagnose` takes each open incident to a cause. One field of a
diagnosis answers the question a person reading a metric asks first: does this reach me?
`data.diagnoses[].semantic_readers` (#1478) names the semantic-layer objects
that read the failing test's columns, read from dbt's semantic layer the way
`maintain snapshot` fingerprints it, with no warehouse query.

- `readers`: each entity, dimension and measure of a semantic model on the
  tested model itself whose column is a tested one, with its `semantic_model`, `model`, `kind`, `name` and
  `column`. A measure carries `metrics`: every metric whose input is the
  measure, and every metric built on those.
- `unresolved`: a member on the tested model whose expression is computed
  (`computed_expression`), and a semantic model whose `model` names nothing Dex
  can read (`model_unresolved`). Dex cannot say which column it reads, or
  whether it reads one; nothing here guesses. A test on a versioned model
  lists the members that read its column here too (`version_unresolved`,
  with the `column`), since the fingerprint does not record which version a
  semantic model's `ref()` resolves to.
- `status`: `read` (the lists stand; an empty `readers` means no resolved
  member on the tested model reads the column, and an `unresolved` one
  still may), `absent` (no semantic layer), `unreadable`
  (`unparsed_files`, each named in `unread_files`; `project_unreadable`;
  `no_project`), or
  `not_read` with `reason` `no_tested_column` or `vendor_not_covered` (a native
  `semantic.vendor`, which this release does not match to a dbt model).

Report these beside the cause: name the semantic models and metrics, and say
which objects are unresolved rather than leaving them out. A semantic model on
a model built from the tested one (a mart over a staging model) is not
followed, as every `read` says in its `detail`, so an empty list is not proof
that no metric downstream reads the column.

## What each axis costs

| Axis | Cost |
|---|---|
| `schema`, `volume`, semantic definitions | free metadata, everywhere |
| `grain`, semantic dimension cardinality | scans; billed handshake on a metered connector |
| `verify` build status | free (artifacts on disk) |
| `verify` row counts | free object metadata, except a view, which keeps no count: those are batched into one aggregate-only statement, priced, and returned in `data.offer` |
| `coverage` | free everywhere: a `dbt parse` of a copy, no connection |
| `coverage --mutate` | one `transform test --mutate` per stale or missing model, priced and confirmed once for the batch on a metered connector; free on DuckDB |
| `verify` declared facts | one aggregate statement per declared relation, plus one window probe per relation with an `additive` column; priced into the same single `data.offer` |

On DuckDB there is no gate, so `verify` measures every count and its findings
come back `exact`.
