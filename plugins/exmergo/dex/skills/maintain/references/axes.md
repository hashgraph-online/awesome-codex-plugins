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
  Apache Ossie or SLayer. A repository with a semantic layer and no dbt project still gets
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
  `null` is a format that does not read declarations).
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
temporal), `declared_relation_missing` (a table gone since the baseline), and
`declared_dependency_dropped` (a join, measure or filter lost to another drop).
Each carries the model's whole removal under `data.removal`, which is what
`maintain reconcile` plans.

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
  `declared_grain_not_unique` (declared, never held), and
  `join_cardinality_exceeded` (a join whose declared arity, SLayer's
  `cardinality`, does not hold: the side it says is unique is not).
- A join that declares no cardinality is named in `warnings` as unchecked.

## `maintain semantic [<objects>]`: definition drift

Definitions changed, added, or removed against the baseline; a source relation
that is gone; a dimension, entity, measure, or declared key naming a column that
is gone; a relationship whose endpoint or column pairs no longer resolve, which
is `high` because a join nothing can resolve is a broken layer; and categorical
dimensions whose set of values widened or narrowed underneath their metrics.

The cardinality half needs a semantic model that names a transformation model.
Ossie names none, so on an Ossie layer this command is free and offers no scan.

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
declaration newly added; `maintain snapshot --project-only` baselines them
without re-measuring the warehouse, which is also how an intended declaration
change is accepted. `maintain reconcile` answers these findings with advisories
only: a declaration is a human's decision, so Dex never rewrites one to match the
baseline.

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
  and models the project declares that built no relation.
- **Row population**: `row_loss` where a model holds materially fewer rows than
  its **driving parent** (the relation in its FROM clause, followed through the
  CTE chain, as distinct from anything it joins) and nothing in its SQL accounts
  for the shortfall; `row_fanout` where it holds materially more. Each names the
  join and its key and states both counts. A model with a `WHERE`, `GROUP BY`,
  `DISTINCT`, `QUALIFY`, `LIMIT`, a semi or anti join, or a set operation is never
  reported for loss, and an incremental model is skipped outright. A model that
  generates its rows in SQL, such as `range(...)` or a `VALUES` clause, has no
  parent relation. That is named in `notes`. A real parent relation that is
  absent from the warehouse is still a warning.
- **Column contract**: `column_missing`, `column_undeclared` and
  `column_type_mismatch`, the built relation's columns against `schema.yml`.
- **Grain**: `grain_broken`, from one source per model, in this order: the
  grain the model's declaration states (`config.meta.dex.grain`, so a
  composite grain is checked with no `dbt_utils` test), a `unique` test, a
  `unique_combination_of_columns` test, a semantic model's primary entity,
  then a naming guess. `data.source` says which one. A declared grain is
  counted in the declared-fact statement below, so it is priced with it.
- **Join contract**: `join_zero_overlap` and `join_orphans`, every equality
  join's measured overlap.
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

  `null_rule: never` is not checked here: it renders as a `not_null` test.
  `data.suppressed` names `unit`, `additivity` and `population` whenever one
  did not run: nothing declares it, the relation is empty, the column is all
  NULL or aggregated away, too few observations to call, or the scan is
  offered.

A project that does not compile is reported first and suppresses everything
else. `data.suppressed` names every class that did not run and why.

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
| `semantic` | definition drift free as everywhere; the dimension-cardinality half needs a `model_ref`, which SLayer has none of, so it is free and offers no scan |
| `reconcile` | stores the `declared_*` removals as a second plan, `data.semantic_plan_id`, through `semantic slayer update`. A whole model is never removed; that and a type conflict's alternative stay advisory |
| `verify` | checks the dbt project only; SLayer's declared keys are measured by `grain`, not here |

What SLayer does not declare is not drift: it has no entities, no measures in
MetricFlow's sense (a saved measure is a formula), no per-measure time
dimension, and no `model_ref`. Read `unavailable` rather than reporting an
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

## What each axis costs

| Axis | Cost |
|---|---|
| `schema`, `volume`, semantic definitions | free metadata, everywhere |
| `grain`, semantic dimension cardinality | scans; billed handshake on a metered connector |
| `verify` build status | free (artifacts on disk) |
| `verify` row counts | free object metadata, except a view, which keeps no count: those are batched into one aggregate-only statement, priced, and returned in `data.offer` |
| `verify` declared facts | one aggregate statement per declared relation, plus one window probe per relation with an `additive` column; priced into the same single `data.offer` |

On DuckDB there is no gate, so `verify` measures every count and its findings
come back `exact`.
