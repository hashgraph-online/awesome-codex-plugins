# Transform commands: fields and flags

Lookup detail for the transform subcommands. What you must and must not do is in
`SKILL.md`; this file says what a field means and what a flag changes.

## `transform plan "<intent>" --edits-file <path|->`

Validates the edits and returns them as diffs with a plan id; nothing is applied.
`--scaffold <table>` (repeatable) generates a staging skeleton (`stg_<table>.sql`
plus per-model YAML with key tests and PII meta) from the `.dex/` cache, instead
of or on top of hand-authored edits.

Model SQL with Jinja `for`/`if` control flow is compiled by dbt in a throwaway
copy containing all edits, then checked as a single read-only SELECT. dbt and a
dev profile passing the usual build preflight are required; failed or missing
compilation stores no plan. The
authored Jinja remains the reviewable edit. Compile-time SELECTs from
`run_query`, statement blocks and `adapter.execute` pass through Dex's query
firewall, scoped read-only connector, PII screening, query limits and cost guard.
`get_relation()` and `is_incremental()` use Dex's scoped inventory, and
`adapter.get_columns_in_relation()` (what `dbt_utils.star`,
`get_filtered_columns_in_relation` and Fivetran's `fill_staging_columns` call) is
answered from that inventory's column metadata: names and types, no rows, free on
every connector. Each listing counts toward `query.max_statements` and is named in
`warnings`; a relation outside the inventory is answered with no columns and named.
A raw `DESCRIBE`, `SUMMARIZE`, `SHOW`, `PRAGMA` or `information_schema` read, the
dispatched `get_columns_in_relation` macro called directly included, still
refuses, naming `adapter.get_columns_in_relation`. Direct database handles and
other unsupported adapter introspection refuse. A truncated
macro result refuses rather than producing an incomplete model.

Packages: dbt parses or compiles nothing whose declared packages are not
installed, so a plan that needs dbt's parse (a `schema_yml`, `project_yml`,
snapshot, seed or semantic edit, a declaration, a delete) or a control-flow
compile is refused first, in Dex's words, naming each missing package and
`transform deps`. The check reads the tree as the plan leaves it (#1166): a
package the plan's own `packages_yml` edit declares is checked too, and one it
stops declaring is not. A plan never installs anything, so declaring a package
and using it is two plans: the `packages_yml` edit on its own (it needs no parse,
so it is stored), applied, then `transform deps`, then the plan that uses it.

Compilation that reads no warehouse data needs no spend confirmation. For
compile-time queries on billed connectors, the first discovered work is quoted
through the existing `--confirm --budget` handshake. Its estimate is partial:
subsequent queries share the command and daily ceilings. A stopped compilation
stores no plan and reports any completed spend; re-running may repeat queries.
See the cost-controls reference for the shared budget mechanism.

- `data.refactor_comparison_offer`: present when the plan rewrites a model that
  already exists, and placed ahead of the large fields. `per_model` lists each
  rewritten model with its own `transform compare` command and
  `static_attribution`: `unattributed` (a change Dex could not isolate, such as
  macro-generated SQL), `unmeasured` (named but not counted: on a billed
  connector without `--attribute-rows`, past a cap, or a count that failed),
  `none` (row attribution reported no change that moves rows, so a value change
  is invisible to it) or `attributed`.
  `recommended_before_apply` is true unless every model is `attributed`, and
  `why` says so in one line. `data.next` names the comparison ahead of
  `transform apply`. `baseline_ready` says whether the comparison can run now:
  `false` when an upstream model's latest build attempt, ordinary or
  `--cold-deps`, left it `error` or `skipped`. Each such input is under
  `per_model[].blocked_inputs` (`model`, `status`, `owner`: `project` or
  `package`, and `package`), and `why` and `data.next` lead with the repair: a
  plan of its own, applied and built (`--cold-deps` for a package's node),
  with this plan left unapplied until it is compared. Read free from the run
  results and manifest already on disk (#1114). `mixed_with_repair` names the
  blocked inputs this plan itself repairs (it edits them, or edits the project,
  packages or a macro while one is blocked), with a warning: such a plan's
  comparison can only read the failed build, so the repair has to be split out. If the change should keep the model's results, run it
  before applying: once applied, the plan's baseline is gone. Nothing scans at
  plan time, and nothing refuses: a change meant to alter results needs no
  comparison. The released `models` and `command` fields are unchanged.
- `data.row_attribution`: on a model that already exists, every predicate, join,
  source, and grain change is named and measured on its own against the prior
  model, alongside the whole-model net. Column expressions, aliases, and ordering
  report nothing. On DuckDB the deltas are measured automatically; on a billed
  connector the changes are named for free and measuring needs `--attribute-rows`
  plus `--confirm --budget`. `attributed: false` carries the reason (macro SQL, a
  jinja conditional, a renamed CTE, a changed `UNION`, `INTERSECT` or `EXCEPT`
  whose branches are not compared, an unprofiled parent). Advisory: nothing here
  refuses a plan.
- `data.change_scope` (#1115): on each model that already exists, what the edit
  changes beside its request, read statically from both versions with no query.
  `population` is `changed` when an authored predicate, join, driving relation,
  `DISTINCT` or `GROUP BY` can move rows (row attribution's own reading), `kept`
  when nothing can, `unchecked` when the model could not be rendered (a macro, an
  `{% if %}`) or a set operation it shares with the prior version changed (a
  `WHERE` added to one `UNION` branch), since branches are not compared. `outputs` is `changed`, `kept`, or `unchecked` where the final
  select projects a star and nothing else changed. A star with a changed CTE
  column is `changed` and still carries a `reason` saying removals and
  additions could not be read, so read `reason` whatever the state. Both states
  describe this model's own SQL: `kept` is not proof a roster kept its rows, since
  a model the plan does not edit is not listed and one reading a filtered model
  loses those rows anyway. Each entry in
  `changes` has an `axis` (`population` or `output`), a `kind` and a `scope`:
  `column_removed`, `column_added`, `type_changed` (the outer cast target),
  `aggregate_changed` (`count(*)` to `count(col)`, a changed function or
  `DISTINCT`), `null_handling_changed` (a `coalesce`, `ifnull` or `nullif` added
  or removed) and `expression_changed`, compared by output name in the final
  select and in every CTE both versions share; table qualifiers and formatting
  are ignored. A population change, a removed column and a changed type,
  aggregate or NULL treatment get a `status`: `declared` where an assumption's
  `column` names the output column or a column the predicate reads (the
  assumption is copied, with a note when its evidence is `default`), else
  `undeclared` and a warning. An added column and a rewritten formula are listed
  without one. `population` at the top lists the models by state, so a broad
  filter shows which rosters kept every row. Capped at 25 models and 8 changes a
  model, undeclared first, with cuts counted in `elided`. A `--for-plan` build
  carries the unsettled entries into `data.completion.obligations.change_scope`,
  with an `unread` entry (`unchecked`) for a model either axis could not read
  (`outputs_unread: true` marks a star whose removals were not read even where
  `outputs` is `changed`), and an `elided` entry (`unchecked`) for a model whose
  changes the cap cut or that `beyond_cap` names, so a capped report never reads
  as complete.
  Advisory: nothing here refuses a plan.
- `data.identifier_conversions` (#861): each conversion the plan adds to an
  identifier column, on a new model or an edited one. A conversion is a `cast`, a
  safe cast (`try_cast`, BigQuery `safe_cast`, Snowflake `try_to_number`) or a
  `lower`, `upper` or `trim`, in a filter, a join or a projection. An identifier
  is a declared key, foreign key or grain column, a join key, a profiled grain, or
  an id-shaped name (`key_basis` says which). A conversion the prior model already
  had is the existing contract, not reported. Gated like row attribution and
  priced in its one handshake (`(identifier conversions)`). Each entry carries:
  - `measured`: aggregate counts over the rows that reach the conversion (its
    own filter removed, every other filter in the scope kept, so an intentional
    exclusion is not counted again): `input_rows`, `null_key_rows` (never a
    failure), `input_entities`, `failed_rows`/`failed_entities` (a hard cast is
    measured as its safe form), `retained_entities`, `converted_entities`,
    `collided_keys` and `colliding_source_entities` (`7` and `007` become one
    key), `representation_changed_entities` (`007` read back as `7`), and on a
    join `matched_entities` against the other side's distinct keys that pass
    its own `WHERE` and `ON` conjuncts (`partner_filters`, #1073).
    `denominator` states the population in words.
  - `own_filters` (#1171): on a join, the converted side's own filters applied
    to the rows counted: its `WHERE` conjuncts and, where the join drops its
    rows (an inner join, or the side a `LEFT` or `RIGHT` join does not keep),
    its `ON` conjuncts. On the kept side of an outer join an `ON` conjunct
    removes none of its rows and is not applied. A conjunct converting the key
    itself is the conversion's effect and stays counted.
    `scope_filters_not_applied` names, as `{filter, reason}`, each `WHERE` or
    `ON` conjunct that narrows neither side's rows in the counts because it
    reads both sides, another relation, or a column whose relation is not
    stated.
  - `later_filters_applied` (#1073): a row-by-row `WHERE` conjunct in a later
    CTE, on the one chain of scopes that read the conversion's scope as their
    `FROM`, carried back onto the rows counted, as `scope: predicate`. A
    conjunct reading the conversion's own output is its effect and stays
    counted. `later_filters_not_applied` names, as `{scope, reason}` plus
    `filter` when a specific predicate was skipped (a join, `HAVING`, `QUALIFY`
    or `LIMIT` carries none), whatever else a later scope does to those rows: a filtering join, `HAVING`,
    `QUALIFY`, `LIMIT`, a filter on the conversion's output or the join's
    other side, or a scope read twice or through a join or set operation.
  - `identity`: on an edited model, the prior and authored model's distinct keys
    in one output column, as text: `kept`, `lost`, `gained` and both row counts.
    `identity_changed` holds even when the row counts are equal.
    `identity_reason_code` says why it is absent: `new_model`, `baseline_failed`
    (the prior model does not run today), `no_shared_key_column`.
  - `status`: `lossless`; `declared` when an assumption's `column` names the
    column (its evidence tier is under `assumption`); `undeclared`, also a
    warning listing the contract-compatible options (compare as text,
    normalize, a bridge or a namespace, or record the exclusion); or `unchecked`
    with a `reason_code`: `counting_off`, `awaiting_confirmation`,
    `unprofiled_input` (the reason names the `explore profile` to run),
    `unsupported_expression` (a rewrite such as `regexp_replace` or a regex
    filter), `unsupported_scope` (a grouped, deduplicated or windowed scope, or
    a UNION branch, subquery or nested CTE, under `scope: "(unaligned)"`),
    `no_safe_cast_on_connector` (Postgres has no cast that returns NULL; a
    cast to `smallint`, `integer` or `bigint` is measured through a guarded
    cast instead),
    `unrenderable_sql`, `probe_refused`, `probe_failed`, `cap_reached` (4
    measurable conversions per model, 8 per plan).
  - What decides the status is what the conversion itself does: identifiers it
    fails on anywhere, and merges and respellings outside a filter (in a filter
    the converted key is never an output). Join matches are reported and never
    decide it, since a key that was an orphan before is not this conversion's
    loss. The identity comparison covers the whole edit, so it decides only for
    a projection that defines the compared column. A respelling is counted only
    for a text source: a numeric source's text form differs by formatting.
  Shape alone never makes an identifier invalid or a duplicate, so nothing here
  says so. No statement projects a value, PII-flagged keys included, and a
  failed statement reports its exception type rather than the warehouse's
  message, which for a failed cast quotes the value. Never a refusal.
- `data.declarations.<model>`: for every model the plan creates, edits or
  declares, `drafted`, `declared` and `missing`. Free on every connector: it reads
  the `.dex/` cache and the repository and opens no connection. Shape in
  `declarations.md`. Absent when the plan touches no model. `drafted.precedent`
  says what the project's other models do with each column this one filters,
  branches on or aggregates, grouped and counted.
- Contradiction warnings: on a model that already exists, a declared rule the
  edit breaks, also listed under `data.declarations.<model>.contradictions`
  (`check`, `status`, `rule`, `stale`, `prior`, `authored`, `preexisting`,
  `row_delta`). Shape and states in `declarations.md`. Never a refusal.
- Literal warnings: a value compared directly to a column whose cached domain is
  complete and does not hold it, naming any case- or whitespace-insensitive
  match. Silent on a capped domain or a PII-flagged column; never a refusal.
- Shape warnings: the authored SELECT list against the columns `schema.yml`
  declares, in both directions, silent where the model declares none. A `*` is
  followed through CTEs, subqueries and joins, then to a `ref()`'d model's SQL as
  the plan leaves it, then to a cached profile, which the warning names because a
  profile can be stale. A skipped comparison says which case stopped it, such as a
  `*` over a relation with no profile (and the `explore profile` that supplies
  one), a macro standing in for a column, or a set operation.
- The resolved-key convention: a model exposing a raw foreign key where at least
  three siblings sharing its folder and layer prefix all resolve theirs, none
  passes one through, and the project holds a parent to resolve against. It names
  its precedent and its parent, judges only models the plan authors, and is the
  one check a project can decline (`conventions.resolved_keys: false`).
- `data.semantic_proposal`: for a declared model under `transform.marts_paths`
  (default `[models/marts]`), the semantic definition its declaration states in
  the configured layer (`vendor`). MetricFlow: added to the plan
  (`mode: included`) where the project has a dbt semantic layer and a time spine,
  offered for `semantic plan --definitions-file` (`mode: proposed`) where it does
  not, validated by MetricFlow's schemas, the metric-input check and dbt's parse
  of a throwaway copy, never skipped. SLayer: a model file stored as a second
  plan (`plan_id`; apply both) where its path is under `semantic.slayer.models`,
  proposed with the `dex config set` that adopts it otherwise. Cube: a model
  file of its own, `<dir>/<mart>.yml`, on the same terms against
  `semantic.cube.files`. Per model,
  `carried` and `not_carried` account for every declared field. Absent when no
  declared mart was touched. Shape and statuses in `declarations.md`.
- `data.model_versions`: for each native dbt versioned model the plan touches
  (its YAML entry, a version's file, or a model that refs it), each version's
  `label`, `file`, `file_source` and `relation`, the `default` an unversioned
  `ref()` resolves to before and after, every consumer's `ref` and what it
  resolves to before and after (`changed`), `relation_changes`,
  `contract_changes`, and `manifest`. dbt's parse of the post-change project
  confirms node ids, files, relations and each consumer's `depends_on`:
  `confirmed`, `contradicted` with coded `mismatches`, or `unchecked` with a
  `reason_code`. A version with no file, two versions on one file, or a plain
  entry beside a version is refused by code. A promotion and a moved relation
  are warnings. `independent_models` names a new `<model>_v<N>` copy that is not
  a version. Recipe: [model-versions.md](model-versions.md).
- `data.toggle`: present when the payload carries a `toggle` contract
  (`variable`, `on_value`, `off_value`, `columns`, `exempt_models`, `packages`,
  `assumptions`). It is the one command that takes one. Every model of the
  project is compiled in a throwaway copy at each value, and the tree before the
  plan at `on_value`. No check probes a table's rows; compiling can still query
  the warehouse where a macro does (`run_query`). Returned fields:
  - `verdict`: `satisfied`, `contradicted` or `unchecked`.
  - `completeness` and `limits`, for example a disabled model that reads the
    flag. The reference scan's "could not parse the SQL for columns" is not one:
    the compiled SQL is the judge (#1156).
  - `models`: each producer and each model with a problem, with its `branches`
    and `checks`. A model that does not compile at either value is `unchecked`
    (`compile_failed`) on its own record; the rest are still judged.
  - `macro_reads`: each read of the flag in a project macro, with the `models`
    whose compiled SQL calls it. `dynamic_reads`: each `var()` whose name is not
    a literal, with its model or callers; listed, not a limit, since the compile
    gives the flag its value wherever it is read.
  - `not_compiled`: each disabled model that reads the flag (`model`, `path`),
    which no compile reached; the verdict is incomplete for those alone.
  - `models_clean`, `contract.producers` and `package_scope`.

  The checks are `governed_column_present_when_off`,
  `governed_column_read_when_off`, `governed_column_lost_when_on`,
  `ungoverned_column_lost`, `ungoverned_columns_differ` and
  `branch_compile_failed`, each also a warning. A plan whose tree never reads the
  variable is refused. Recipe: [feature-toggles.md](feature-toggles.md).

## `transform apply [plan-id]` and `transform plans`

`apply` writes a plan into the dbt project: the latest unapplied plan of any kind
when no id is given. If a human edited a file after planning, nothing is written
and the divergence comes back as diffs with `needs_confirmation`. `plans` lists
stored plans, pending and applied, newest first.

When no id is given, the envelope names the plan it picked:
`data.resolved_plan` is `{plan_id, intent, created_at, resolved_from:
"latest_unapplied"}`, and a `warnings` line names the same plan, on a refusal
after the pick too. Check that it is the plan you meant. `export`, `ground`, `classify` and `compare` take the same
default and report it the same way. An id that is given but empty (`apply ""`,
which is what `apply "$(dex transform plan ...)"` passes when the plan failed) is
refused with `reason: request`, as are an empty `--plan-file`, `--for-plan` and
`--for-plan-file`. An unquoted empty substitution leaves no argument at all, so
it still means "latest": take the id from the plan's envelope, or quote the
substitution.

An apply that wrote at least one file returns `data.commit_trailer`, the line
`Co-authored-by: Dex <dex@exmergo.com>`. End the message of the commit that
carries those files with it, after a blank line: the forge credits Dex as a
co-author through it. An apply that wrote nothing, or stopped at
`needs_confirmation`, returns no trailer, because there is nothing of Dex's to
commit.

A plan that rewrote existing models also returns `data.refactor_comparison`: one
entry per rewritten model with its `static_attribution`, and per model compared on
the plan (a downstream mart counts), with the last `transform compare` verdict
recorded (`status`, `reason_code`, `compared_at`, and `inputs_built_by`: the
invocation, time and kind of the latest build among the compared model's
upstream models), or
`status: not_compared`. It is reported, never enforced. A `notes` line names the rewrites when nothing on the
plan was compared and static attribution established nothing, and any model whose
last comparison was `different` or `not_checked`, so a refactor that went in
unverified says so in the envelope rather than in nobody's memory.

## `transform references <name> [more...] [--kind <k>] [--full] [--usage]`

Where each name is used across model SQL, `schema.yml`, `dbt_project.yml`,
macros, semantic YAML, seed headers, and installed packages. Repo-only and free.

- `--kind` narrows to `model`, `source`, `seed`, `snapshot`, `macro`, `var`,
  `column`, `metric`, `entity`, `dimension`, or `measure`. Leave it off when
  unsure what the project calls the thing; the answer will say.
- `data.completeness` is `complete` only when every reason to doubt the answer is
  ruled out; `data.limits` names each remaining one, and `data.indeterminate`
  lists the call sites Dex could not resolve (for example
  `{{ ref(var('x')) }}`), each with a file and a line.
- A bare column name is matched project-wide (`scope: name_matched`); a qualified
  `model.column` is resolved through the `ref()` graph, and same-named columns
  outside that lineage are marked `same_name_elsewhere`.
- A versioned model is named by its base name, which selects every version
  (`dim_teams.team_label`), or by a version's label, which selects one
  (`dim_teams.v2.team_label`). The target lists the selected `versions`, and
  each occurrence names the versions it belongs to: a version's file and its
  own `versions:` entry that version, a top-level column entry every version
  that inherits it through `include`, and a consumer the version its
  `ref('dim_teams')` or `ref('dim_teams', v=N)` resolves to. Names in an
  `include` or `exclude` list are reported as `yaml_version_include` and
  `yaml_version_exclude`. A label alone (`dim_teams.v2`) is answered as that
  version: its file and the `ref()` calls that resolve to it. A `ref()` that
  pins its version with an expression (`v=var('x')`) is a limit, and `rename`
  and `remove` refuse while it stands.
- Capped at 200 occurrences across 50 files; `--full` lifts both.
- `--usage` also reports how other models use each qualified `model.column`
  (or `source_table.column`): each target gains `usage`, the same `readers`,
  `groups` and `elided_groups` as `drafted.precedent`, and its limits fold into
  `data.completeness`. Ask it before writing a filter. A bare column name is
  refused, because a column of the same name on another relation is a different
  column. `--full` lifts its caps too.

## `transform rename <kind> <old> <new> [--edits-file <f>]`

Generates every edit a rename needs (the definition, every model that selects
it, every `schema.yml` that documents or tests it, every semantic reference, and
a seed header) and stores them as one plan. Kinds: `column`, `var`, `model`,
`seed`, `snapshot`, `macro`, `source`. Repo-only and free.

- A bare column name is refused, and the refusal lists the models defining a
  column of that name. A report may be imprecise; a rewrite may not.
- On a versioned model, `dim_teams.<column>` renames every version that has the
  column (its file selects it or its YAML declares it) and that version's
  consumers; `dim_teams.v2.<column>` renames v2 and its consumers only. A
  top-level column entry other versions still inherit is kept for them: the
  renamed version excludes it and declares its own entry under the new name,
  and `notes` says so. A model-level test shared with a version the rename does
  not reach is refused. `transform remove column` takes the same names.
- It refuses on a reference it could not resolve statically, a name an installed
  package also defines, a column handed to a macro as a literal string, and a
  SELECT list it cannot read.
- A bare `select *` is not a refusal: it carries the column through under the new
  name, and `notes` says so.
- SQL is rewritten by splicing only the identifiers, so comments and formatting
  survive.
- `data.sites` counts occurrences per reference form, in the same vocabulary as
  `transform references`.

## `transform remove <kind> <name> [--edits-file <f>]`

Removes the definition and refuses while any read survives, naming each with a
file and a line. Same kinds and refusals as `rename`. Hand-authored read edits
passed with `--edits-file` are validated and stored in the same plan, so the
removal stays atomic. A YAML entry is removed with the comment lines written
directly above it at its own indent; a comment set apart by a blank line stays.

On `var`, a `retirement` key in the payload states which behavior survives the
flag, and the plan, `transform compare` and `build --verify --for-plan` hold the
change to it: [feature-retirement.md](feature-retirement.md). Stars over untouched
models, seeds and profiled sources are resolved with the toggle check's catalog
(#1170). A reference scan whose only limits are column parses runs the full
contract (#1172): `data.retirement.column_reads` reports how far
`removed_column_still_read` reached (`complete`, `partial` with the `unchecked`
files, or `not_applicable`), reading unparsed files from compiled SQL where it
can. Where the scan cannot finish for another reason (unread YAML, an unreadable
package, a dynamic `var()` read), `"scope": "authored"` in that contract keeps
the output and metric checks and reports discovery as `unchecked` under
`data.retirement.discovery`. `transform rename` and every other `remove` kind
still refuse on any limit.

## `transform place <column> --targets <a,b> --expr "<sql>" [--explain]`

Finds the lowest model in the `ref()` graph that every target descends from and
that already projects the inputs `--expr` reads, defines the column there, and
threads it down every chain, with a `schema.yml` entry at the ancestor and at each
target. The inputs are parsed from `--expr`. `data.reasoning` names the ancestor,
why it is the lowest, which targets descend from it, and the chain. `--explain`
returns the reasoning and stores no plan.

`data.strategy` is `per_target` when there is no common ancestor, the lowest one
lacks an input, or two candidates tie. Dex will not go further upstream to pull
an input down, because that turns one placement into an unbounded rewrite. The
fallback duplicates the derivation in each target, and those copies will drift.

## `transform declare [<model>...] [--edits-file <f>] [--limit N] [--intent "<text>"]`

Proposes declarations for models that already exist, as one plan. Each selected
model gets only the measured facts its YAML does not state, plus any intent the
payload's `declarations` supply. Every model not proposed is listed in
`data.skipped` with the reason. The plan is capped at 25 models (`--limit` only
narrows), and a second run after apply moves to the next batch. A versioned
model is selected by version (`dim_teams.v2`, or every version with
`dim_teams`) and proposed into that version's `versions:` item. Fields, skip
reasons and the cap: `declarations.md`, "Declaring models that already exist".

## `transform build --target dev [--select <s>] [--full-refresh] [--verify] [--for-plan <id>] [--no-install-deps]`

Runs `dbt build` against a dev target, with a cost preflight first.

- dbt has no dry-run, so the engine compiles the project and prices each node
  itself. On BigQuery the first unconfirmed call returns `needs_confirmation`
  with `estimated_bytes` and a `per_table_bytes` breakdown; each statement is then
  capped server-side by the profile's `maximum_bytes_billed`, and billed bytes are
  reported afterward.
- `data.upper_bounds` names the `per_table_bytes` lines that are upper bounds:
  incremental models whose batch filter is a watermark subquery, which a dry run
  cannot prune on and the job does. They will likely bill less. An over-ceiling
  refusal names them too, so tell the user how much of the estimate they are
  before they choose a budget. Inside committed `budget.ceiling` and
  `budget.session_ceiling`, a build is confirmed with `--confirm` alone and needs
  no number from anyone.
- A refusal over the ceiling carries a calibration line from `.dex/spend.jsonl`.
  Builds over-estimate most on a partitioned or clustered warehouse.
- dbt runs with its working directory pinned to the project dir, so relative
  paths in `profiles.yml` resolve against the project. When packages are declared
  and `dbt_packages/` is missing, the engine runs `dbt deps` first;
  `--no-install-deps` refuses instead.
- A failed node gets a `data.prerequisites` entry naming its owner, its relation
  to the plan and the repairs dbt supports. `--cold-deps` reinstalls packages into
  an isolated copy and builds from it, to prove a repair survives. See
  [prerequisite-repairs.md](prerequisite-repairs.md).
- On DuckDB, a seed whose CSV header no longer matches its table in the dev
  target (a column added, dropped or reordered), or whose declared
  `+column_types` no longer match the table's column types, is rebuilt with
  `dbt seed --full-refresh` before the build, only when the build selects it.
  Without it, a reload keeps the type the table was first built with.
  Removing a previously applied type declaration restores CSV inference with
  the same refresh. Successful-load history survives pricing, narrow selections
  and cold builds; use `--full-refresh` explicitly if that history is unavailable.
  `data.full_refresh` names it and a warning says why, so no `dbt seed` step
  is needed by hand.
- Each node in `data.nodes` carries dbt's `unique_id` beside a readable `name`.
- `data.outcome` says what the run established: `empty_selection`, `unrelated`,
  `partial`, `skipped`, `indeterminate` (nothing failed, but a node reported a
  status dex does not recognize, such as `partial success`), `stale`, `failed`,
  or `validated`. `data.evidence.generated` lists only the relations this run's
  successful nodes produced. `--for-plan <id>` adds `coverage`; an empty one is
  refused rather than read as absent.
- `data.completion` is the first key of `data`: a bounded summary of all of the
  above. Read it first. See below.

### `data.completion`

`data.nodes` and `data.evidence.nodes` hold one entry per node, so on a project
of a few hundred models they push everything else past the point where a
truncated read stops. `data.completion` comes first and is held to 4096 bytes
serialized (`COMPLETION_BUDGET_BYTES`), so the answer survives `head -c 4096`.
It is derived from the evidence, the verification sweep and the manifest, and it
changes no status: `success` is still dbt's exit and `outcome` is unchanged. The
failed-build envelope carries it too, and Python callers get the same typed
`BuildCompletion` on `BuildResult.completion`.

| Field | What it says |
|---|---|
| `outcome` | `data.outcome`, repeated so the block stands alone |
| `process` | dbt's own `success`, `returncode` and `node_counts` by status. A process result, not a check |
| `change` | the `plan_id` and `source` (`for_plan`, `for_plan_file`) the build was asked to validate, and the `selector` (cut at 200 characters; the whole one is in `data.evidence.selection`) |
| `deliverables` | `coverage`: `known`, `unknown` (no plan named, so nothing says what the build was for) or `undetermined` (the plan's edits name no buildable node). Then `required`, and `built`, `failed`, `skipped`, `missing` and `stale` as `{count, names, elided}`. `blocked` names each required deliverable that did not build and the node that `cause`d it, walked back through skipped parents, a failing data test on a parent included. A skipped or failed deliverable is never counted as built: whatever relation it has in dev predates this run, and `note` says so |
| `blockers` | the failed nodes, with the ones that stopped a deliverable first, and dbt's message cut to 160 characters (the whole message is in `data.evidence.nodes`) |
| `assurance` | over the required deliverables, or over every built model with no plan: `asserted` (a passing data test reads it, or a verification record judged it `satisfied`), `failed_checks` (a data test on it failed or warned, or a record was `contradicted`; `checks` lists each failure with its `kind`, `data_test` with the test's `name` or the record list such as `join_coverage` with its `finding` and `join`, so a join measured against a default threshold is not read as a failed test, #1162) and `build_only` (it built and nothing checked its rows; a unit test reads fixtures, so it does not count) |
| `verification` | `ran` (and `reason` when it did not), `finding_count` including the ones past the 50-finding cap (`findings_dropped`), `by_severity`, the `top` five as `{code, identifier, severity}`, the `suppressed` class names, and `offered` when the sweep's scan was offered rather than run |
| `obligations` | the declared contracts the sweep held the build to (`join_coverage`, `parent_population`, `temporal_contracts`, and the column contract's unchecked models), counted `by_status`, with the `contradicted` ones named with their `finding` and the `unchecked` ones with their `reason_code`, and the models that declare no columns under `no_declared_columns`. `checked: false` when the sweep did not run. An empty `by_status` from a sweep that ran means nothing declared a contract it could hold the build to, which is not the same as every contract holding |
| `obligations.identifier_conversions`, `obligations.change_scope` | the plan's identifier conversions and change-scope entries that are not settled, on the required models (#861, #1115) |
| `obligations.incremental_replay` | each required incremental model the plan edited: `satisfied` when a unit test overriding `is_incremental` to true passed in this build, `contradicted` (`incremental_test_failed`) when one failed, otherwise `unchecked` with `full_refresh_only` (the build only full-refreshed it, which never runs the next incremental run) or `no_incremental_test`. Absent when the plan edits no incremental model (#1130) |
| `obligations.comparison` | with `--for-plan`, each required model the plan rewrote, held to its recorded `transform compare` verdict: `equivalent` or `as_expected` is `satisfied`, `different` or `unexpected` is `contradicted`, and no verdict is `unchecked` with `not_compared` (or `compared_elsewhere` where another rewrite in the plan was compared), as is a `not_checked` verdict with its own code. A `--for-plan-file` build carries none, since verdicts are recorded on the stored plan (#1157) |
| `refactor_comparison` | with `--for-plan`, each model the plan rewrote and any model compared on it (a downstream mart included), with its recorded `transform compare` verdict, or `not_compared` |
| `details` | where the full evidence is, in reading order |
| `elided` | every cut the budget forced, counted. Counts are never cut, and each unfinished list keeps at least one name |

A complete result (one required mart, built, its test passed, one class
suppressed):

```json
{"outcome": "validated", "process": {"success": true, "returncode": 0, "node_counts": {"pass": 1, "success": 1}},
 "change": {"plan_id": "p7c1e", "source": "for_plan"},
 "deliverables": {"coverage": "known", "required": 1, "built": {"count": 1, "names": ["fct_orders"], "elided": 0}, "...": "...", "blocked": []},
 "blockers": [], "assurance": {"basis": "required", "asserted": {"count": 1, "names": ["fct_orders"], "elided": 0}, "...": "..."},
 "verification": {"ran": true, "finding_count": 0, "suppressed": ["temporal"], "...": "..."},
 "obligations": {"checked": true, "by_status": {"satisfied": 1}, "...": "..."},
 "details": ["data.evidence", "data.verification", "data.nodes"], "elided": {}}
```

An incomplete build (300 staging models succeeded, a prerequisite errored, and
the report the plan changed was skipped):

```json
{"outcome": "failed", "process": {"success": false, "returncode": 1, "node_counts": {"error": 1, "skipped": 1, "success": 300}},
 "change": {"plan_id": "p3f9a", "source": "for_plan"},
 "deliverables": {"coverage": "known", "required": 1, "built": {"count": 0, "names": [], "elided": 0},
   "skipped": {"count": 1, "names": ["rpt_team_activity"], "elided": 0}, "...": "...",
   "blocked": [{"deliverable": "rpt_team_activity", "status": "skipped", "cause": "int_team_members"}],
   "note": "not rebuilt by this run; any relation it has in the dev target predates this run and was not verified by it"},
 "blockers": [{"node": "int_team_members", "status": "error", "message": "Runtime Error in model int_team_members: Conversion Error: ..."}],
 "verification": {"ran": false, "reason": "not requested; re-run with --verify to sweep", "...": "..."},
 "obligations": {"checked": false, "...": "..."}, "...": "..."}
```

Unknown coverage (no `--for-plan`, so the block cannot say whether the change's
deliverables were built, and nothing checked the rows of the three models that
did):

```json
{"outcome": "validated", "change": {},
 "deliverables": {"coverage": "unknown", "required": 0, "...": "...",
   "note": "no plan was named, so nothing says which nodes this build was for; pass --for-plan <id> (or --for-plan-file) to learn whether the change's deliverables were built"},
 "assurance": {"basis": "built_models", "asserted": {"count": 0, "names": [], "elided": 0},
   "build_only": {"count": 3, "names": ["stg_source_000", "stg_source_001", "stg_source_002"], "elided": 0}},
 "...": "..."}
```

`"...": "..."` marks fields left out here; the real block always carries every
field.

### `--full-refresh`

Passes dbt's `--full-refresh`, which drops and rebuilds each selected
incremental model and seed instead of adding to it. Use it after you change an
incremental model's logic: an incremental run only adds or merges new rows, so
the rows the old logic wrote stay in the dev table until the model is rebuilt.
It is not a routine build. A full rebuild scans the model's whole history.

A full refresh runs only the model's full program, never its
`{% if is_incremental() %}` branch. When the defect is in what the next
incremental run skips or duplicates, a green full refresh is not the evidence:
test the branch with the incremental unit test `transform test --scaffold`
writes, and build again without the flag. Recipe:
[incremental-repairs.md](incremental-repairs.md).

- Name the model with `--select`. With no `--select`, every incremental model
  and seed dbt's default selection reaches is rebuilt: the whole project, unless
  the project defines a default selector, which narrows it. A warning gives the
  count of what this build actually selected.
- The cost preflight compiles with `--full-refresh`, so each rebuilt incremental
  model is priced as the full rebuild that runs, not as a batch. On BigQuery its
  line is therefore not an upper bound. A model whose `full_refresh: false` keeps
  its incremental branch keeps its watermark filter too, and its line is still
  named under `data.upper_bounds`.
- `data.full_refresh` is `{requested, models, seeds, not_refreshed, success}`.
  `not_refreshed` names models whose own `full_refresh: false` config makes dbt
  ignore the flag, so their old rows stay.
- `data.evidence.invocation.full_refresh` is `true`.
- Dev target only, like every build. `--verify` also compares the rows of each
  incremental model in `data.full_refresh.models` with its driving parent, so
  `row_loss` and `row_fanout` apply to it as to a table, and the parent's count
  is in the upfront estimate. Three kinds of model keep the skip, named in
  `warnings`: an incremental model this build did not rebuild, one in
  `not_refreshed`, and a microbatch model, which rebuilds only from its `begin`.
  These are row counts, and a model with a filter or an aggregate is never
  reported for loss, so a green verification does not show the rebuilt rows are
  right: check values with `explore profile <relation> --target dev --refresh`.
- The DuckDB stale-seed rebuild above is skipped, because the build already
  rebuilds every seed it selects.

### Where the build writes dbt's artifacts

Every dbt invocation Dex runs on the project writes to one artifact directory,
resolved once per command by `transform.artifacts` in `.dex/config.yml`. That
covers the build, the compile that prices it, and the seed check.

- `isolated` (the default) writes to `<target-path>/dex/<dbt-version>/`, for
  example `target/dex/dbt-1.12.5/`. The project's own `target/` is never
  written. A CI image, a teammate's install or a grader running another dbt
  version therefore never trips on artifacts Dex's dbt left behind. One case
  this prevents: dbt 1.12 leaves a snapshot's compiled `.sql` path as a
  directory, and dbt 1.10 fails opening it as a file.
- `shared` writes the project's own target path, for tooling that reads
  artifacts there. Dex first refuses (`reason: guard`) when that directory holds
  a snapshot path another runtime left as a directory, or a `manifest.json` from
  a different dbt minor version. The refusal names the recovery (`dbt clean`
  with that runtime, or unset the setting). Dex deletes nothing.
- The target path resolves the way dbt resolves it: `DBT_ENGINE_TARGET_PATH`
  (dbt 1.12's spelling), then `DBT_TARGET_PATH`, then `target-path` in
  `dbt_project.yml`, then `target`. Dex cannot render a `target-path` written
  with Jinja and falls back to `target` for it; set `DBT_TARGET_PATH` to the
  rendered path so readers, and the `shared` policy, use the directory dbt
  does.
- `data.artifact_directory` names the directory the build wrote. Readers such
  as `maintain verify`, local `explore semantic`, `transform ground` and
  `--use-project` take the newer of Dex's directory and the project's own, so
  they read a Dex build right after it, and your own `dbt parse` after that.
  A build's own `--verify` sweep reads only the directory it wrote and only its
  own invocation's run results.
- If the `run_results.json` on disk names a different dbt invocation than the
  run's own log, its nodes are dropped and the build is reported as failed, not
  successful.

### `--verify`

Sweeps the nodes this build touched with the `maintain verify` checks and
reports under `data.verification`. A green build says dbt executed; it does not
say the model holds the rows it should. An inner join written where a left join
was meant loses rows, raises nothing, and passes every uniqueness and not-null
test over the smaller result.

- `ran` is always present. When it ran, `findings` is ranked as `maintain verify`
  ranks it, `scope` names the models covered, and `suppressed` names each class
  that could not run and why.
- Findings never enter `errors` and never change the status; a pointer line in
  `warnings` names the count.
- A failed build still reports which node failed and which were skipped because
  of it, usually a faster read than the dbt log.
- It also checks what each built model declares: `unit_out_of_range`,
  `additivity_contradicted`, `population_contradicted`, the declared parent
  (`parent_population_missing`, `parent_population_unexpected`), a declared
  `history` temporal contract (`temporal_*`, with one record per contract under
  `data.verification.temporal_contracts`), and a declared grain no `unique` test
  in the build covers (`grain_broken`, `source: declaration`). See
  declarations.md, "Checked against the built relation".
- It reads the dev namespace, and the namespaces dbt derived from it for this
  build's manifest (`<dev schema>_<name>`, where a package or a folder sets
  `+schema`), so a package parent or a joined package model built there is
  judged rather than reported unbuilt (#1155). `notes` names each one read.
- It measures the coverage of every equality join the built models write, as
  `maintain verify` does: `data.verification.join_coverage` holds one record
  per join, and `join_no_match`, `join_orphans`, `join_zero_overlap`,
  `join_field_all_null` and `join_field_newly_null` are its findings.
- With `--for-plan` or `--for-plan-file`, it holds each versioned model the
  plan touches to the manifest this build wrote, with no statement:
  `data.verification.model_versions` has one record per version (`check:
  version`, its `unique_id` and `build_status`), per default (`check: default`)
  and per consumer (`check: ref`, its `depends_on`), each `satisfied`,
  `contradicted` (`version_missing`, `version_not_built`,
  `version_file_mismatch`, `version_default_contradicted`,
  `version_ref_misresolved`) or `unchecked`, and each reaches
  `data.completion.obligations`. Deliverables name versions by label, so one
  version building never answers for another.
- With a plan carrying a `toggle`, `data.verification.toggle` judges the built
  relations' columns from metadata at the value this build gave the flag, read
  from `dbt_project.yml` or the default every read states. An empty table is
  judged the same way.
  - Built off: every model, with finding `toggle_column_present_when_off` (high).
  - Built on: every producer, with finding `toggle_column_missing_when_on` (high).
  - The other value: one record per producer, `unchecked` with
    `branch_not_built`.
  - `value_unknown` where the value could not be read.

  On an off build, a `column_missing` for a governed column that `schema.yml`
  documents is the toggle working and is not reported. Each record reaches
  `data.completion.obligations`.
- It compares each built model's columns with its `schema.yml`, using the
  detector `maintain verify` runs: `column_missing`, `column_undeclared` and
  `column_type_mismatch`. This reads metadata only, so it adds no statement and no
  estimate line. `data.verification.column_contract` says what it reached, because
  no findings over no comparison is not a clean contract:

  ```json
  {"checked": ["fct_orders"],
   "no_declared_columns": ["stg_events"],
   "unchecked": [{"model": "fct_returns", "reason_code": "not_built"}]}
  ```

  `reason_code` is `not_built` (it failed or was skipped, so any relation there is
  an earlier run's), `no_relation` (the manifest names none), `relation_not_found` (none or
  several in Dex's read scope, as with a custom schema) or `metadata_unreadable`.
  When nothing could be compared, `suppressed` names it:
  `"column_contract": "no model this build ran declares columns in schema.yml"`.
- On a billed connector the sweep's row counts are a `(row counts)` line in the
  build's estimate, the declared-fact statements a `(declared facts)` line, and
  the join coverage statements a `(join overlap probes)` line.
  A cold dev target that cannot be priced upfront is priced again after the
  build, against the reservation it already holds.

## `transform compare [plan-id] [--model <m>] [--map old=new] [--key <column>] [--accept-type <column>] [--expect <json> | --expect-file <f>] [--target dev]`

Whether a stored plan keeps one model's results, or, with `--expect`, whether it
changes them only as stated (see [below](#an-intended-change---expect)). Use it on a refactor, after
`transform plan` and before `transform apply`: `data.refactor_comparison_offer` on
the plan names the command. A green build and a matching row count do not establish
this, since a join rewrite can keep both and still change a measure.

Each verdict except `awaiting_confirmation` and `plan_applied` is recorded on the
stored plan, keyed by model, so `transform apply` and a `transform build
--for-plan` report whether each rewrite was compared and what came back. The
latest comparison of a model replaces the earlier one. Recording moves no plan
digest: the portable document carries the edits alone.

With no plan id, `compare` uses the latest unapplied plan and names it in
`data.resolved_plan` and a `warnings` line on every verdict; an empty id is
refused.

Before compiling anything, it reads, per upstream model, the latest build that
attempted it: an ordinary build's `run_results.json` or a `--cold-deps` build's
(written apart, under `cold/`), whichever ran last, with the manifest of the
newest. A compile is not an attempt. A parent that latest attempt left `error` or
`skipped` is `inputs_unsynchronized`, naming the parent, its status and, for a
package's model, its package. Its dev relation is older than its SQL, and both
sides would read it, so a verdict would hold only for inputs the project no
longer produces. The detail names the order that clears it: the repair in a plan
of its own, applied and built (`--cold-deps` for a package's model), then this
plan compared, still unapplied. A model the plan itself rewrites is compiled
inline and not judged this way, and no run results at all changes nothing.

A verdict carries `inputs_built_by` (`invocation_id`, `generated_at`, `cold`) where
an upstream build exists (`null` where no build attempted the compared model's
upstream models; not set on `awaiting_confirmation` or `plan_applied`, which are
never recorded): the latest build among those models, so an `equivalent`
can be tied to the repaired state it read. It names one run: other inputs may
come from earlier builds, so `cold: true` does not mean every input came from a
cold build. It is recorded on the plan with the verdict.

- Read `data.status`, then `data.reason_code`. `equivalent` holds for
  `data.input_scope` at `data.compared_at`, on the dev relations as they stand. Say
  that when you report it. It is not a proof for future inputs.
- `different` with `schemas_differ`: read `data.schema`. A rename is a difference
  until `--map old=new` states it. Types are compared exactly, so `INTEGER` to
  `BIGINT` is a difference too, and the rows are then not compared. If the change
  is intended, `--accept-type <column>` states it: within one family (text, exact
  numeric, float) the rows are then compared and the change is reported under
  `accepted_type_changes`. Across families it is `invalid_type_acceptance`, since a
  common type could make unequal values equal. A blank-padded `CHAR` is in no family.
- `different` with `rows_differ`: `data.multiset` counts excess rows on each side,
  so equal distinct rows with different duplicates still show. `data.keyed` adds
  keys missing, added and changed, when `--key` or the declared grain is unique on
  both sides; otherwise `keyed_reason` is `key_not_unique`.
- `not_checked` is not a pass. Fix what the code names:

| `reason_code` | What to do |
|---|---|
| `plan_applied`, `plan_stale` | plan the change again against the tree as it is |
| `baseline_not_compilable`, `proposed_not_compilable` | the model does not compile on that side; `detail` quotes a compile error, and a connection failure says to run `dbt compile` |
| `inputs_unsynchronized` | build the named parents on dev; one the last build left `error` or `skipped` needs its failure repaired first, in a plan of its own, applied and built (`--cold-deps` where a package owns it). A cold build counts. A plan that changes a seed or snapshot, or a macro or project setting that changes how an untouched parent compiles, cannot be compared, because dev holds the old rows. This plan stays uncompared: once it is applied the baseline is gone (`plan_applied`). After applying and building, a further change needs its own new, unapplied plan to compare |
| `nondeterministic_expression` | the model calls a random, uuid or current-time function, or samples, so two runs can differ on their own |
| `unsupported_type` | the named column cannot be grouped on this connector; `detail` names it and its type |
| `baseline_refused`, `proposed_refused` | before anything reaches the warehouse, that side's compiled SQL is not a single SELECT; fix the model |
| `firewall_refused` | the firewall refused the generated comparison, which can happen to a valid model, for example over a relation with no usable profile; `explore profile --target dev` the relations it names, then compare again |
| `baseline_not_executable`, `proposed_not_executable` | reading that side's output schema failed, so the warehouse would not plan it, or it returns no columns; `detail` is an exception class or a message Dex wrote, never warehouse text. Run the model on dev |
| `comparison_unreadable` | pricing or running the comparison failed, or its result could not be read as counts, or an output column uses a name the comparison reserves; `detail` is an exception class or a message Dex wrote, never warehouse text. A reserved name needs an alias; otherwise compare again, and if it persists, run the statement's model on dev |
| `invalid_mapping`, `invalid_key`, `invalid_type_acceptance`, `duplicate_output_name` | fix the flag, or give the model unique output names |
| `awaiting_confirmation` | the priced ask, as on any metered command |
| `comparison_unsupported_on_connector` | this connector has no `describe_query` |

What counts as one value is the warehouse's own grouping, measured on every
connector: NULL groups with NULL and not with `''` or `0`; NaN groups with NaN;
`-0.0` groups with `0.0`, so a change in zero's sign is not reported; `'a'` differs
from `'a '` and from `'A'` on these connectors with their default collation for
`VARCHAR`. A case-insensitive collation or a blank-padded `CHAR` column on your
warehouse applies its own equality here. Floats have no tolerance.

Column names in `--key` and `--map` match case-insensitively when that names one
column, so `--key team_id` works on Snowflake, which reports `TEAM_ID`. On ClickHouse
a joined `select t.id` builds a column named `t.id`, so a rewrite that changes the
join can report a real rename; alias the column.

The nondeterminism check knows built-in functions only. A nondeterministic UDF or
an unordered `LIMIT` can show as `different` with no real change, so compare again
if a `rows_differ` looks unexplained.

A plan with a `toggle` compiles both sides at its `on_value`, named in
`data.baseline_vars` and `data.proposed_vars`, so `equivalent` means "with the
feature on, the proposal returns today's results". The off value is
`data.toggle`'s to judge.

A plan that changes a macro or project configuration compiles both sides through
their ancestors, and is compared when no untouched parent's SQL moved. Refused in
values-free mode.

### An intended change: `--expect`

Most repairs are meant to change rows: backfill missing days, drop archived
entities, pick up late arrivals. Compared without an expectation they read
`different`, which says nothing about whether only the intended rows moved.
`--expect '<json>'` (or `--expect-file <f>`, `-` for stdin) states the change,
and the verdict becomes `as_expected` (`matches_expected_change`) or `unexpected`
(`unexpected_change`) (#1157):

```json
{"added":   "none" | "any" | {"where": "<predicate>"},
 "removed": "none" | "any" | {"where": "<predicate>"},
 "changed_columns": ["<column>", "..."],
 "key": "unchanged"}
```

- Every field is optional: `added` and `removed` default to `"none"`,
  `changed_columns` to none, and `key` to `"unchanged"` (`"any"` lets the key
  stop being unique). `{"expected_change": {...}}` is accepted too.
- `added.where` is read on each added row of the proposal, `removed.where` on
  each removed row of the baseline. A predicate names output columns (either
  side's spelling of a `--map` rename) and must be a deterministic row-by-row
  condition: comparisons, `IN` over literals, `BETWEEN`, `LIKE`, `IS`, boolean
  logic, `coalesce`, casts, `lower`/`upper`/`trim`. No arithmetic, function or
  aggregate. A predicate that is NULL on a row does not match it.
- An exclusion is usually stated by a column the model does not output, so one
  subquery shape is allowed: `<column> IN (SELECT <column> FROM <relation>
  [WHERE <row predicate>])`, one relation, no join, grouping or limit.
  `ref('<model>')` names a relation either side reads. The relation is read once
  as a distinct list (profiled on demand like an input) and does not join the
  compared `input_scope`.
- With a key (`--key`, else the declared grain) unique on the baseline, the
  counts are keys: added, removed, and changed (a key on both sides whose row
  moved), each `{total, matching, unexpected}`; `columns` names each column that
  changed on how many keys and whether `changed_columns` allows it; `grain` says
  whether the key `holds` on the proposal and how many keys repeat. With no key,
  or one that repeats on the baseline, the counts are rows (excess
  multiplicity), a changed row reads as one removed and one added, and
  `changed_columns` is refused without a key.
- `findings` names each failed clause: `unexpected_added`, `unexpected_removed`,
  `unexpected_changed_column`, `grain_not_held` (a backfill that crosses days
  with another dimension repeats the day), or `schema_changed` (state a rename
  with `--map`, a type change with `--accept-type`).
- `unexpected_keys` names up to five keys per failed class (`added`, `removed`,
  `changed`): key columns only, read through the query firewall, so a key whose
  column is flagged as PII is withheld (`samples_withheld: firewall_refused`) and
  the counts stand. It is the one place `transform compare` returns values, and
  the command stays refused in values-free mode.
- An expectation that does not fit (a column that is not an output, a
  `changed_columns` naming a key column, a predicate outside the whitelist) is
  `not_checked` with `invalid_expectation` and `detail` naming the field, and is
  not recorded. Malformed JSON is refused before anything compiles.
- On a metered connector the expectation's statements (rows, keys and the key
  sample) are priced into the same single ask, as `(expected change rows)`,
  `(expected change keys)` and `(expected change key sample)`; the sample runs
  only when a class failed.
- The verdict is recorded on the plan with a digest of the expectation, and a
  `--for-plan` build reads it into `obligations.comparison`: `as_expected` is
  `satisfied` and `unexpected` is `contradicted` (`unexpected_change`).
- With no key compared, the report says `key: "unchanged"` was not judged (a
  note, and `grain.holds: null`); pass `--key` to have it checked. A key column
  whose name reads like a credential's (`token_count`) withholds the sample
  (`samples_withheld: key_name_withheld`), since the envelope refuses such a
  name.

## `transform test --scaffold <model>`

Plans a `unit_tests:` skeleton: a `given` block per `ref()`/`source()` input
carrying only the columns the model reads, typed from the cache, and an `expect:`
stub that fails until filled in.

- A `RANGE` frame with a day or week interval bound, ordered by a date or
  timestamp column of one input, gets boundary rows for that input: the current
  day, the last day the window includes, the first it excludes, and a gap a
  row-count frame would cross. The partition is held constant and the aggregated
  column is numbered 1, 10, 100, 1000. `data.window_boundaries` says what each
  date tests; you still write `expect:`.
- A window it cannot reach (an ordering expression other than a whole-day
  function of a date column, a month unit, a non-temporal column, or a
  bare-number `RANGE` bound over an arbitrary expression) is a warning with a
  reason code, and the input keeps one example row.
- The full loop, with a worked example: `${CLAUDE_SKILL_DIR}/references/test-strength.md`.

On a model whose only jinja control flow is `{% if is_incremental() %}` (with an
optional `{% else %}`), it plans two tests in the one file:

- `test_<model>`, the full build, with dbt's `is_incremental: false` override,
  which dbt requires on every unit test of an incremental model.
- `test_<model>_incremental`, with `is_incremental: true` and a `this` fixture
  written as typed SQL (`format: sql`), so it runs before the model was ever
  built. A `this` column is typed from the input column the full build passes
  through to it, then from the cached profile of the model's own relation;
  otherwise the scaffold refuses and names the `explore profile ... --target dev`
  that would type it.

`data.incremental` is `{tests, watermark}`, and absent for any other model.
`watermark` is `{column, operator, input, this_column}` where the branch compares
one column with a subquery over `{{ this }}` (`operator` as read with the column
on the left), or `null`. Where it is read, the watermark's input gets one row
before, on and after the current watermark plus one NULL, each commented with
what it probes. Where it is not, or where Dex cannot place the boundary (more
than one input reads the watermark column, or the column is text or boolean),
the input gets the single example row the full test has: read the fixture, and
add the boundary rows yourself. Recipe: [incremental-repairs.md](incremental-repairs.md).

## `transform test --mutate <model> [--max-mutants <n>] [--check-equivalence|--no-check-equivalence] [--downstream|--no-downstream]`

Plants one standard analytics defect at a time in the model's compiled SQL (a
flipped boundary, a dropped or negated filter, a swapped join type, a removed
`CASE` branch, an inverted ratio, a shifted window frame, `sum` for `max`), runs
the model's own tests against each, and reports which defects nothing caught.

- Read `data.counts`, then the survivors, listed first. Each carries `defect` (what
  would now be wrong) and `suggested_test` (the test that would catch it).
- Each survivor's `equivalence.status` says which test to suggest, and
  `suggested_test` already follows it. `distinguishable` changes the model's
  output on the dev data, so an assertion over that data would catch it today;
  these are listed first. `equivalent` produces exactly the model's rows there,
  so only a unit test fixture that reaches the case can catch it. The comparison
  is four counts, never a row. It runs on its own on DuckDB; on BigQuery or
  Snowflake it needs `--check-equivalence` and joins the same single estimate;
  other connectors report `not_checked`, which carries a `reason`.
- `score` is a ratio of two small integers over one model.
- A window frame bound moves one step wider. An interval bound also moves one
  unit narrower, and each window mutant carries `frame`: `last_included` and
  `first_excluded` are the offsets a boundary fixture needs rows at, in `unit`.
- `data.unsupported_sites` lists the frame bounds no mutant moved, each with a
  `reason_code` (a column or expression offset, a fraction, a compound
  interval, the frame's other bound). Their boundaries are untested; say so.
- `--downstream` also runs the tests of the models that read this one, against
  each mutant (on by default on DuckDB, opt-in and priced into the same estimate
  elsewhere). A defect only those caught is `caught_downstream`, named in
  `caught_downstream_by`: it could not ship, but the model's own suite missed it,
  so `score` still counts it as a miss and `score_with_downstream` counts it as
  caught. `data.downstream` lists the routed models, the tests that ran, the ones
  excluded (a unit test on a downstream model, a test that also reads a relation
  the mutant cannot reach) and why, and a `reason` when it was off.
- `baseline.excluded` names tests already failing against the unmutated model;
  every verdict is relative to the tests that passed.
- An incremental model's `{% if is_incremental() %}` branch is compiled a second
  time with the branch taken, and its own comparisons and filters are planted
  there (#1132). Only unit tests overriding `is_incremental` to true run against
  them. `data.incremental` holds the branch's `mutants`, `counts`, `score`,
  `baseline`, `tests` and `cap` share, apart from the full build's; with no such
  test every branch mutant survives and `suggested_test` names one.
- Capped at 20 mutants (`--max-mutants` narrows, never widens), sampled across
  defect classes; `cap.elided` reports the cut.
- Mutants build as ephemeral models in a throwaway copy, so nothing is written
  and no relation is created or replaced. Dev-target only. On a billed connector
  the batch is one estimate and one `--confirm`; a budget that runs out leaves
  the rest `not_run`.
- Refused for free when the model has no tests (its own, or downstream ones when
  `--downstream` is on), is a Python model, belongs to a package, or has no
  mutable SQL.

## `transform deps`

Installs or refreshes dbt packages. No confirmation needed: it writes only inside
the project and never touches the warehouse. It installs the packages the project
already declares in `packages.yml`, at the versions `package-lock.yml` pins where
the lockfile matches it (dbt resolves them again where it does not): that is
not installing or upgrading a tool, and a request not to update tools does not rule
it out.
It is the step between a plan that declares a package and a plan that uses it,
since `transform plan` installs nothing.
