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
`get_relation()` and `is_incremental()` use Dex's scoped inventory; direct
database handles and other unsupported adapter introspection refuse. A truncated
macro result refuses rather than producing an incomplete model.

Compilation that reads no warehouse data needs no spend confirmation. For
compile-time queries on billed connectors, the first discovered work is quoted
through the existing `--confirm --budget` handshake. Its estimate is partial:
subsequent queries share the command and daily ceilings. A stopped compilation
stores no plan and reports any completed spend; re-running may repeat queries.
See the cost-controls reference for the shared budget mechanism.

- `data.row_attribution`: on a model that already exists, every predicate, join,
  source, and grain change is named and measured on its own against the prior
  model, alongside the whole-model net. Column expressions, aliases, and ordering
  report nothing. On DuckDB the deltas are measured automatically; on a billed
  connector the changes are named for free and measuring needs `--attribute-rows`
  plus `--confirm --budget`. `attributed: false` carries the reason (macro SQL, a
  jinja conditional, a renamed CTE, an unprofiled parent). Advisory: nothing here
  refuses a plan.
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
  declares, in both directions, silent where the model declares none.
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

## `transform apply [plan-id]` and `transform plans`

`apply` writes a plan into the dbt project: the latest unapplied plan of any kind
when no id is given. If a human edited a file after planning, nothing is written
and the divergence comes back as diffs with `needs_confirmation`. `plans` lists
stored plans, pending and applied, newest first.

An apply that wrote at least one file returns `data.commit_trailer`, the line
`Co-authored-by: Dex <dex@exmergo.com>`. End the message of the commit that
carries those files with it, after a blank line: the forge credits Dex as a
co-author through it. An apply that wrote nothing, or stopped at
`needs_confirmation`, returns no trailer, because there is nothing of Dex's to
commit.

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
narrows), and a second run after apply moves to the next batch. Fields, skip
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
- On DuckDB, a seed whose CSV header no longer matches its table in the dev
  target (a column added, dropped or reordered) is rebuilt with
  `dbt seed --full-refresh` before the build, only when the build selects it.
  `data.full_refresh` names it and a warning says why, so no `dbt seed` step
  is needed by hand.
- Each node in `data.nodes` carries dbt's `unique_id` beside a readable `name`.
- `data.outcome` says what the run established: `empty_selection`, `unrelated`,
  `stale`, or `validated`. `--for-plan <id>` adds `coverage`.

### `--full-refresh`

Passes dbt's `--full-refresh`, which drops and rebuilds each selected
incremental model and seed instead of adding to it. Use it after you change an
incremental model's logic: an incremental run only adds or merges new rows, so
the rows the old logic wrote stay in the dev table until the model is rebuilt.
It is not a routine build. A full rebuild scans the model's whole history.

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
- Dev target only, like every build. `--verify` works the same way afterwards.
  Its row-population check still skips incremental models, so a green
  verification does not show the rebuilt rows are right: check them yourself,
  for example with `explore profile <relation> --target dev --refresh`.
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
  `additivity_contradicted`, `population_contradicted`, and a declared grain no
  `unique` test in the build covers (`grain_broken`, `source: declaration`).
  See declarations.md, "Checked against the built relation".
- On a billed connector the sweep's row counts are a `(row counts)` line in the
  build's estimate, and the declared-fact statements a `(declared facts)` line.
  A cold dev target that cannot be priced upfront is priced again after the
  build, against the reservation it already holds.

## `transform compare [plan-id] [--model <m>] [--map old=new] [--key <column>] [--accept-type <column>] [--target dev]`

Whether a stored plan keeps one model's results. Use it on a refactor, after
`transform plan` and before `transform apply`: `data.refactor_comparison_offer` on
the plan names the command. A green build and a matching row count do not establish
this, since a join rewrite can keep both and still change a measure.

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
| `inputs_unsynchronized` | build the named parents on dev. A plan that changes a seed or snapshot, or a macro or project setting that changes how an untouched parent compiles, cannot be compared, because dev holds the old rows. This plan stays uncompared: once it is applied the baseline is gone (`plan_applied`). After applying and building, a further change needs its own new, unapplied plan to compare |
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

A plan that changes a macro or project configuration compiles both sides through
their ancestors, and is compared when no untouched parent's SQL moved. Refused in
values-free mode.

## `transform test --scaffold <model>`

Plans a `unit_tests:` skeleton: a `given` block per `ref()`/`source()` input
carrying only the columns the model reads, typed from the cache, and an `expect:`
stub that fails until filled in.

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
the project and never touches the warehouse.
