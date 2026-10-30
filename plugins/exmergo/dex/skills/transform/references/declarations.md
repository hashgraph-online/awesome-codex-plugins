# Declarations: what a model means

A declaration is a structured statement of what a model means: what one row is,
which rows are in, what each column is, and what was assumed. It travels in the
same payload as the edits, beside them, and works on `transform plan` and on
`semantic define|update|plan`. What you must and must not do is in `SKILL.md`;
this file is the payload's shape and what each field becomes.

## The payload

```json
{"edits": [...],
 "declarations": [
   {"model": "fct_orders",
    "description": "One row per order placed through the web store.",
    "grain": ["order_id"],
    "population": {
      "rule": "Completed and shipped orders; cancelled and returned orders are excluded.",
      "filters": [{"column": "status", "excludes": ["cancelled", "returned"]}]
    },
    "columns": {
      "order_id":    {"role": "key", "description": "..."},
      "customer_id": {"role": "foreign_key", "references": "dim_customers.customer_id", "null_rule": "never"},
      "ordered_at":  {"role": "time", "description": "..."},
      "order_total": {"role": "measure", "aggregation": "sum", "additivity": "additive", "unit": "currency:USD"},
      "share_of_day":{"role": "measure", "aggregation": "sum", "additivity": "non_additive", "unit": "fraction"}
    },
    "assumptions": [
      {"decision": "Which order statuses count as revenue",
       "chosen": "completed and shipped",
       "evidence": "precedent",
       "detail": "every model reading stg_orders.status excludes cancelled and returned"}
    ]}
 ]}
```

`edits` may be left out when the payload only declares models that already
exist.

## Fields

| Field | Values |
|---|---|
| `role` | `key`, `foreign_key`, `dimension`, `time`, `measure`, `attribute` |
| `additivity` | `additive`; `semi_additive` (does not add across time: a balance, a running or season-to-date total); `non_additive` (a ratio, a share, a distinct count) |
| `unit` | `currency:<ISO code>`, `fraction` (0 to 1), `percent` (0 to 100), `count`, or a plain unit such as `days` |
| `null_rule` | `never`, or a sentence saying what NULL means in this column |
| `references` | `<model>.<column>`, a model, seed or snapshot the project has |
| `evidence` | `request` (what the user asked for), `contract` (the project's declared columns, tests or metric filters), `precedent` (how sibling models decide the same thing), `data` (what profiling showed), `default` (the conventional analytics-engineering choice) |

A field Dex does not know is refused by name, so a typo cannot silently drop
part of a declaration.

## What it renders into

The declaration is written into the model's **existing** YAML entry, wherever in
the project it lives. A model with no entry gets one beside its SQL, named for
it, which is where the scaffold puts one. Dex never writes a second entry for a
model, which dbt refuses.

| Declared | Written as |
|---|---|
| `description` (model or column) | dbt's own `description` |
| a single-column `grain` | `data_tests: [unique, not_null]` on that column |
| `null_rule: never` | `not_null` on that column |
| `foreign_key` with `references` | a `relationships` test (`arguments: {to, field}`) |
| `grain`, `population`, `assumptions` | model `config.meta.dex` |
| `role`, `null_rule`, `aggregation`, `additivity`, `unit`, `references` | column `config.meta.dex` |

A test the column already lists is kept as written, under the key it already
uses. Declaring again merges: a key the new declaration states replaces the old
one, and a key it leaves out is kept. Every byte outside the keys above, comments
included, stays where it was.

## What is checked

Refused, with the fix named:

- a model the project and the plan do not have;
- a declared column or grain column the model's SELECT list does not produce
  (skipped, with a warning, when the SELECT list cannot be read statically);
- a `references` target that is not `<model>.<column>`, names nothing, or names
  a column the target does not produce;
- an unknown `role`, `additivity` or `evidence`, or an unknown field;
- a population filter listing values on a column that looks like personal data.

Warned, never refused: a missing description, grain, population, assumptions or
column role (one warning per missing field), a measure without its aggregation,
additivity or unit, an assumption missing its decision, chosen value or evidence,
and a model the plan writes SQL for with no declaration at all. Where the SQL
already implies the decision, the warning names it: `fct_orders declares no
population rule; its SQL filters on status`.

A plan carrying declarations or `schema_yml` edits is parsed by dbt against a
throwaway copy of the post-change project before it is stored, and degrades to a
named warning where dbt is not installed.

## `data.declarations`: drafted, declared, missing

For every model a plan creates, edits or declares, the plan envelope carries
`data.declarations.<model>` with three parts. It is computed from the `.dex/`
cache and the post-change repository only, so it scans nothing and costs nothing
on any connector.

```json
{"drafted": {
   "grain": {"value": ["order_id"],
             "evidence": "order_id is a proven unique key of raw_orders, carried through unchanged"},
   "columns": {
     "customer_id": {"from": "raw_orders.customer_id",
                     "role": {"value": "foreign_key", "evidence": "the join ... was verified, no orphans"},
                     "references": {"value": "customers.customer_id", "evidence": "..."},
                     "nullable": {"value": false, "evidence": "..."}},
     "region": {"from": "customers.region",
                "nullable": {"value": true, "evidence": "it comes from the outer side of the left join ..."}},
     "discount_rate": {"from": "raw_orders.discount_rate",
                       "unit": {"value": "fraction", "evidence": "... a hypothesis about the unit, not a certified one"}}},
   "domains": [{"column": "raw_orders.status", "used_in": ["where"],
                "values": ["shipped", "cancelled"], "elided": 0, "complete": true}],
   "precedent": [{"column": "raw_orders.status",
                  "this_model": [{"usage": "where", "expression": "status <> 'cancelled'"}],
                  "readers": 5,
                  "groups": [{"usage": "where", "expression": "NOT status IN ('cancelled', 'returned')",
                              "count": 4, "models": ["fct_revenue", "..."], "elided_models": 0},
                             {"usage": "none", "count": 1, "models": ["fct_gross_orders"], "elided_models": 0}],
                  "elided_groups": 0, "completeness": "complete", "limits": []}],
   "inputs": [{"relation": "raw_orders", "profiled": true, "identifier": "shop.main.raw_orders"}],
   "incomplete": []},
 "declared": {"description": "...", "grain": ["order_id"], "population": {...}, "columns": {...}},
 "missing": ["assumptions", "columns.amount.unit"]}
```

`transform plan` never writes `drafted` into the project; only `transform declare`
does, and only the subset described under "Declaring models that already exist".
Each fact carries the `evidence` it rests on, and a fact the cache cannot support is left out rather than guessed:

| Drafted | When |
|---|---|
| `grain` | the `GROUP BY` keys when the model aggregates; otherwise a key the driving relation's profile *proved* unique, selected unchanged, with every join an equality on a key proven unique on its joined side. Any other join, a right or full join, a set operation or an `UNNEST` gives `{"value": null, "withheld": "<why>"}` |
| `columns.<c>.from` | the upstream `relation.column` a column passes through from unchanged, followed through CTEs |
| `columns.<c>.role` | `key` for a single-column drafted grain; `foreign_key`, with `references`, for a column carrying a join `explore relationships --verify` measured with no orphans. A join measured with orphans would fail the `relationships` test a `references` renders, so it is `references: {"value": null, "withheld": "<the orphan rate>"}` instead. Where the column joins cleanly to several relations (the raw table, its staging model, a dimension), a parent whose column is not unique and the model itself are passed over, a model of this project wins over a seed or snapshot and those over a raw table, and the model nearest this one in the project tree breaks a tie; `evidence` names the other clean parents. A warehouse that reports `STG_CUSTOMERS` resolves to the project's `stg_customers`. The joins read are the input column's; where those reach only raw tables (a staging model over a source, on a warehouse whose build lives in another schema) and the model is already built and profiled, the built relation's own clean joins are read instead, so `stg_orders.customer_id` references `stg_customers` |
| `columns.<c>.pii` | the upstream column's PII flag, category and confidence |
| `columns.<c>.nullable` | `true` on the outer side of a left, right or full join whatever the upstream NULL rate; otherwise from the upstream NULL fraction |
| `columns.<c>.additivity` | `semi_additive` where `explore profile --check-cumulative` found the upstream column never decreasing |
| `columns.<c>.unit` | `fraction` for a non-integer column profiled entirely in 0 to 1; `percent` for one named like a percentage profiled in 0 to 100. A hypothesis, never a certified unit |
| `domains` | the cached value domain of each column the SQL filters (`where`, `having`, `qualify`) or branches on (`case`), capped by `profile_value_domain_cap` with the rest counted in `elided`. A PII-flagged column's values are never drafted: `values` is null and `withheld` says why |
| `precedent` | for each upstream column the SQL filters, branches on or aggregates, what the project's other models reading the same relation do with it: `this_model` (this model's own uses), then `groups`, one per filter conjunct (`where`, `having`, `qualify`), `CASE` condition (`case`) or aggregation (`aggregation`), with `count` and `models`, and `usage: none` for readers that keep every value. See below |
| `inputs` | every relation the SQL reads; one the cache has not profiled is `profiled: false` with the `command` that would profile it |
| `incomplete` | why part of the SQL was not read: a macro or jinja block, a set operation, an unqualified column in a multi-relation select |

`declared` is what the model's YAML entry says once the plan lands: this
payload's declaration merged over whatever the entry already carried. `missing`
names each intent field nobody has supplied (`description`, `grain`,
`population`, `assumptions`, `columns.<c>.role`, and a measure's `aggregation`,
`additivity` and `unit`), and each is also a warning. Where the drafted grain and
the declared one disagree, a warning says so.

### Precedent

Precedent is evidence, not a rule. Every group is listed, conflicting ones
included, and none is called the majority: four models excluding cancelled orders
and one keeping them is the case worth reading before writing a sixth. Decide,
then record the decision in the declaration with `evidence: precedent`, naming the
models you followed.

- A column is the same column only where the SQL resolves to it through its
  aliases and CTEs. `status` on another relation is not precedent.
- Readers are the models that `ref()` or `source()` the relation directly. A
  model reading a downstream model built from it is not counted.
- Groups are by sqlglot's rendering of each fragment, not by logical
  equivalence: `status not in ('a', 'b')` and `status <> 'a' and status <> 'b'`
  are two groups.
- `completeness` uses the `transform references` vocabulary. It is `incomplete`
  when a reader could not be read statically (a macro, a jinja block), when a
  `ref()` could not be resolved, or when a use of the column could not be traced;
  each reason is in `limits`, and such a reader is never counted as one that
  keeps every value.
- Capped at 10 groups and 5 model names per group, with the rest counted in
  `elided_groups` and `elided_models`.
  `transform references <model.column> --usage --full` returns the same answer
  uncapped, before any SQL is written.

### Literals the column never holds

Where the SQL compares a column directly to literals (`=`, `<>`, `IN`, `NOT IN`)
and the cache holds that column's complete value domain, a literal the domain does
not contain is a warning, naming any value that matches it ignoring case and
whitespace ("compares stg_orders.status to 'Cancelled', which none of its 3
profiled values is; 'cancelled' matches it ignoring case and whitespace"). It is
silent when the domain was capped (`elided` above 0), when the column carries a
PII flag at any confidence, when the comparison wraps the column in a function,
and when the literal's type differs from the column's values. Never a refusal: a
filter on a value that does not exist yet is sometimes the intent.

### Contradictions

On a model that already exists, `data.declarations.<model>.contradictions` lists
each declared rule this plan's SQL and the post-change declaration disagree on.
Each entry is also a warning. A new model carries no key; an empty list means
nothing was contradicted.

```json
{"check": "population", "status": "contradicted",
 "rule": "population.filters status excludes ['cancelled']", "column": "status",
 "stale": "sql", "prior": "status <> 'cancelled'", "preexisting": false,
 "row_delta": 2}
```

| `check` | Fires when |
|---|---|
| `population` | the predicate implementing a declared `population.filters` entry is removed or changes the values it keeps. `excludes` is met by `<>`/`NOT IN` on exactly those values, or by an `IN` list that leaves them out; `includes` by `=`/`IN` on exactly those values |
| `grain` | the drafted grain (the `GROUP BY` keys, or a carried key) differs from the declared grain, or a declared grain column leaves the SELECT list |
| `columns` | a column whose declaration states a role, unit, additivity or another `config.meta.dex` field leaves the SELECT list. It names what the column was declared as, beside the plain `schema.yml` divergence warning |
| `additivity` | the model takes `SUM` of an upstream column its own model declares `semi_additive` or `non_additive`, or `AVG` of one declared `non_additive` with a `fraction` or `percent` unit. `declared_on` names that upstream model. A running total the cumulative check found and nothing declares fires too, without `declared_on`; a column declared `additive` never does |

Three states are compared: the prior SQL and declaration, the authored SQL and
the post-change declaration, and what this plan changed between them.

| What the plan did | `stale` |
|---|---|
| changed the SQL, left the declaration, and they now disagree | `sql` |
| changed the declaration, left the SQL, and they now disagree | `declaration` (or the plan is half done) |
| changed both, and they still disagree | `either` |
| changed both, and they agree | nothing reported |
| touched neither side of a rule that already disagreed | nothing reported |

`preexisting: true` marks a rule that already disagreed before this plan and
that this edit touches. `status: unchecked` (with `reason`, and no `stale`) is a
rule the plan touched that Dex could not read the SQL for: a macro or jinja
predicate, a function around the column (`lower(status) <> 'x'`), a subquery, a
set operation, or a grain no key proves. It never claims the rule was removed.
Comparison is on sqlglot's reading of the SQL, so a reformat, an alias rename,
`!=` for `<>`, and `NOT IN ('a', 'b')` for `<> 'a' AND <> 'b'` are silent.

A contradicted population is paired with row attribution's report of the same
predicate. Where attribution measured it (DuckDB, or `--attribute-rows` with the
cost handshake on a billed connector), `row_delta` is its delta and the warning
cites it; where it did not, the warning carries attribution's reason. Nothing
here runs a query of its own, refuses a plan, or blocks apply.

## Declaring models that already exist: `transform declare`

A plan declares the models it creates or edits. Models written before
declarations existed have none, and dex never adds them unasked. To adopt them,
select some and let one plan propose what dex already measured:

```bash
dex transform declare stg_orders,stg_customers fct_orders
dex transform declare --edits-file intent.json   # every model, with intent
```

The selector is the one `maintain verify` takes: model names, repeatable and
comma-separated, case-insensitive, and none for every model. It is read from the
repository, so nothing is compiled.

**What is proposed.** Per model, only the fields its YAML does not already state:

| Drafted fact | Written as | Only when |
| --- | --- | --- |
| `grain` | `config.meta.dex.grain`, plus `unique` and `not_null` on a single column | no grain is declared |
| `role: key` | the column's `role` | the column has no role |
| `role: foreign_key` | the column's `role` | the column has no role |
| `references` | `references` and a `relationships` test | the column's role is absent or `foreign_key`, and the parent is a model, seed or snapshot of this project (a join verified to a raw table stays in `drafted`) |
| `additivity: semi_additive` | the column's `additivity` | no additivity is declared |

The unit shape, NULL facts, PII flags and value domains are evidence, not
declarations. They stay in `data.declarations.<model>.drafted` and are never
written. Intent (`description`, `population`, `assumptions`) is never drafted.

**Supplied intent.** The payload is the `transform plan` payload with
`declarations` only (`edits` are refused; SQL changes go through `transform plan`).
A supplied declaration wins over the draft field by field, and its model is
considered first. A supplied model the selector does not select is refused, and
so is a malformed one, exactly as in `transform plan`.

**Each model is accounted for.** `data.proposed` lists each model in the plan with
`fields` (every drafted fact written, with its evidence) and `supplied` (the
paths the payload stated). `data.skipped` lists every other selected model:

| `reason` | Meaning |
| --- | --- |
| `not_a_model` | no `.sql` model of that name under the model paths |
| `python_model` | a Python model; dex drafts from SQL only |
| `versioned` | a model with `versions:`; declare each version by hand |
| `sql_unreadable` | the SQL could not be read statically (`detail` says why) |
| `unprofiled_inputs` | the cache has not profiled what it reads; `commands` holds the `explore profile` call for each. Nothing is scanned |
| `nothing_drafted` | the cache proves no key, verified join or running total for it |
| `complete` | it already declares every fact dex can draft |
| `not_writable` | its YAML cannot be spliced predictably (a flow-style entry), or a drafted fact does not fit the SELECT list; the rest of the batch still plans |

A skipped model also carries `missing`, the intent it still owes.

**The cap.** At most 25 models are proposed per plan; `--limit N` narrows that and
never widens it. Skipped models do not count. The models left over are counted in
`data.elided_count` and in `notes`. Apply the plan and run the same command again:
the models just declared are now `complete`, so the next batch is proposed.

**Nothing to propose** returns `ok` with `plan_id: null`, no diff, and a note.

Otherwise the declarations go through the same path as a `transform plan`
declaration: rendered into the existing entry (shared files included, every
other byte kept), gated by dbt's parse, and drafted, with `data.declarations`,
`data.decisions` and, for a declared mart, `data.semantic_proposal`. Free on
every connector: it reads the repository and the cache and opens no connection.

## Checked against the built relation

`transform build --verify` and `maintain verify` hold each declaration to the
relation dbt built, with aggregate-only statements (no row leaves the
warehouse):

| Declared | Finding | Severity |
|---|---|---|
| `grain` | `grain_broken`, `data.source: declaration`, with the duplicate count | high (low below `maintain.grain_min_rows`) |
| `unit: fraction` with a value outside 0 to 1 | `unit_out_of_range`, with the observed `min` and `max` | medium |
| `unit: percent` with every value within 0 to 1 | `unit_out_of_range`; a question rather than proof, since small percentages land here too | medium |
| `additivity: additive` on a running total | `additivity_contradicted`, with the entity, the ordering column and the decrease fraction | medium |
| `population.filters` value still present | `population_contradicted`, with the count of contradicting rows, never the rows | high |

`null_rule: never` needs no check of its own: it renders as a `not_null` test,
which the build runs. A single-column `grain` renders as a `unique` test, so the
build path leaves it to that test; `maintain verify` ranks the declared grain
first among its grain sources, so one model's grain is checked once.

The additivity probe orders the column by the declaration's own entity and time
columns: a composite grain naming both, else the `foreign_key` (or `key`) and
`time` roles, else the relation's first id-shaped and temporal columns. Declare
the roles where that guess would be wrong.

A check that could not run is named in `data.suppressed` (`unit`, `additivity`,
`population`, and `grain` on the build path) with the reason: nothing in scope
declares it, the relation is empty, the column is all NULL, the column was
aggregated away (a rollup cannot carry its population rule's column, so the rule
is checked upstream or not at all), too few observations, or the scan is offered.
A population filter's values are compared as text when the declared values and
the column's type disagree. A unit's range is withheld for a column that looks
like personal data.

## Read back by `explore --use-project`

`explore profile` and `explore map` with `--use-project` return each declared
model's declaration as `declaration` on the relation it builds: grain (with
`grain_status` comparing it with the measured keys), population, and each
column's role, unit, additivity and `references`. A `references` is also a
declared join, `declared_by: declaration <model>.<column>`. It is read from the
YAML on every run and never cached, so a later session reads the rule the
project records rather than one remembered from the conversation that wrote it.

## Derived semantic model: `data.semantic_proposal`

When `transform plan`, `transform declare` or `semantic define|update|plan` creates,
edits or declares a model under `transform.marts_paths` (`.dex/config.yml`, default
`[models/marts]`, relative to the dbt project, subfolders included) and the model's
post-change YAML carries a declaration, the engine derives the semantic definition
the declaration already states, **in whichever semantic layer the repository
reads** (`semantic.vendor`). Every vendor sits behind one hook
(`SemanticDerivationSource`), so the envelope has one shape with a `vendor` field:

| `semantic.vendor` | What a declared mart gets |
| --- | --- |
| `dbt` (default) | a MetricFlow semantic model, spliced into the dbt plan |
| `slayer` | a SLayer model file, stored as a plan of its own beside the dbt plan |
| `cube` | a Cube model file, stored as a plan of its own beside the dbt plan |
| `ossie` | an Ossie dataset, appended to the configured document holding its parents and stored as a plan of its own beside the dbt plan |

Three rules hold for every vendor. Metrics are never derived: a measure is what a
column holds, a metric is a business definition, and it stays the author's. Nothing
is guessed or renamed: an aggregation with no equivalent, a composite grain a layer
cannot key on, a name already declared are each named. And **a population is
metadata, never a filter**: the derived definition sits on the mart, whose SQL
already enforces the population, so a filter would apply the rule twice and diverge
silently the day the two disagree. It is carried structured under the vendor's
metadata key `dex`, and as one sentence at the end of the description
(`Population: <rule>; status is one of 'paid' or 'shipped'.`), where an agent
reading the catalog meets it.

Per model, `carried` lists every declared field that reached the definition
(`grain`, `population`, `columns.amount.unit`) and `not_carried` names every one
that did not, with why. A declared field never disappears without a word.

### MetricFlow (`semantic.vendor: dbt`)

| Declaration | Semantic model |
| --- | --- |
| a single-column `grain` | the primary entity (`order_id` becomes entity `order`) |
| a composite `grain`, or none | no primary entity, and none guessed: MetricFlow needs one for any dimension or measure, so the derivation is `failed` with the limitation named. Add `primary_entity:` and pass it to `semantic plan` yourself |
| `foreign_key` | a foreign entity. With `references`, it takes the entity name the referenced model's semantic model already gives that column, so the join resolves; otherwise the column's name less `_id`, with a note |
| `dimension` | a categorical dimension |
| `time` | a time dimension: `day` for a date, `day` for a timestamp (noted, since finer is the author's choice), the truncated grain where the SQL truncates (`date_trunc('month', ...)`), `day` with a note where the type cannot be read. A column whose type is known not to be temporal is left out. The first time column is `defaults.agg_time_dimension`, and a note names the others |
| `measure` with `aggregation` | a measure: `sum`, `count`, `count_distinct`, `min`, `max`, `average` (`avg`, `mean`), `median`, `sum_boolean`. Anything else (`percentile` needs parameters a declaration does not carry), a missing aggregation, or `non_additive` with a summing aggregation is left out and named. A model with no time column carries no measure, since MetricFlow aggregates over one |
| `semi_additive` | `non_additive_dimension: {name: <default time dimension>, window_choice: max}`: each period reports its last value, which suits a balance or a season-to-date total. MetricFlow's own default is `min`; the note asks you to confirm |
| `non_additive` | `config.meta.dex.additivity: non_additive` on the measure, since MetricFlow reads any measure as one it may add up |
| `description` | carried onto the semantic model, dimensions and measures (MetricFlow's schema has no entity description, and `not_carried` says so) |
| `population`, `assumptions` | the semantic model's `config.meta.dex`, and the population sentence in its description |
| `unit`, `null_rule` | the entity's, dimension's or measure's `config.meta.dex` |

What happens to the derivation depends on the project:

- **With a dbt semantic layer** (a semantic model is declared and a time spine
  is present), a derivation that passes every check is added to the same plan,
  spliced into the project's one semantic-model file (or
  `<mart folder>/<model>_semantic.yml` where there is none, or several) with
  every other byte untouched. `mode` is `included`, and a warning names the file.
- **Without one**, nothing is added. `mode` is `proposed`, `time_spine` says
  whether a spine exists, and `definitions` holds each derivation ready to pass:
  save the whole `data.semantic_proposal` object as a file and run
  `semantic plan --definitions-file <file>`. Adopting MetricFlow and a time spine
  is the project owner's decision, so the engine never bootstraps either.

Before a derivation is offered or included it passes MetricFlow's schemas, the
metric-input check, and dbt's parse of a throwaway copy of the project. In a
project with no time spine, that copy alone gets a temporary spine so dbt can
parse it at all; the project never sees it. The parse runs for a derivation even
under `semantic plan --no-parse`, which still applies to the rest of the plan,
because a semantic YAML dbt cannot parse breaks every dbt command in the project.

```json
"semantic_proposal": {
  "vendor": "dbt",
  "mode": "proposed",
  "time_spine": "missing",
  "definitions": [{"kind": "semantic_model", "path": "models/marts/fct_orders_semantic.yml", "content": "name: fct_orders\n..."}],
  "models": {
    "fct_orders": {
      "status": "proposed",
      "semantic_model": "fct_orders",
      "path": "models/marts/fct_orders_semantic.yml",
      "content": "name: fct_orders\n...",
      "validation": {"schema": {"result": "passed"}, "references": {"result": "passed"}, "parse": {"result": "passed", "detail": "parsed with a throwaway time spine in the copy only; the project has none"}},
      "notes": ["..."],
      "limitations": [],
      "carried": ["description", "grain", "population", "columns.order_total.unit"],
      "not_carried": {}
    }
  },
  "next": "save this object as a file and pass it to `semantic plan --definitions-file <file>` ...",
  "notes": ["the project has no dbt semantic layer and no MetricFlow time spine ..."]
}
```

### SLayer (`semantic.vendor: slayer`)

One model file per mart, `models/<data_source>/<mart>.yaml` under
`semantic.slayer.base_dir`:

| Declaration | SLayer model |
| --- | --- |
| `grain` | `primary_key: true` on each grain column, a composite grain included |
| any role | a column, typed from the SQL's casts or the cache's profile (`INT`, `DOUBLE`, `BOOLEAN`, `DATE`, `TIMESTAMP`, `TEXT`); a summed measure of unknown type is `DOUBLE`, with a note |
| the first `time` column | `default_time_dimension` (only where its type is known to be a date or a timestamp) |
| `foreign_key` with `references` | a `many_to_one` join to the SLayer model already sitting on the parent's table; where none does, no join and a note |
| `measure` with `aggregation` | a saved measure named `<column>_<agg>`, formula `<column>:<agg>`: `sum`, `avg` (`average`, `mean`), `min`, `max`, `count`, `count_distinct`, `median`. SLayer keeps columns and measures in one namespace, so a name a column already holds fails the derivation rather than being renamed |
| `semi_additive` | no saved measure, named in `limitations`: SLayer's `last` reports one row's value on the last period, not the total across entities on it, so `<column>:last` is the author's call |
| `description` | the model's and each column's `description` |
| `population`, `assumptions` | the model's `meta.dex`, and the population sentence in its description |
| `unit`, `null_rule`, `additivity` | the column's `meta.dex` |

`data_source` is the one the configured models share; models over more than one
are not guessed between (`failed`). `sql_table` is, in order: the `database.schema`
that the SLayer models on this dbt project's other models already read (so a mart
lands where its siblings do); else the relation the compiled manifest names, with a
note, since that is whatever target last compiled the project (often dev); else the
bare table name, as a limitation, since dex's catalog then claims no relation. A
model already on the mart's table is `skipped`; one holding its name on another
table is `failed`.

Whether it is included depends on the write surface:

- **The path is already listed under `semantic.slayer.models`**: the model is
  validated by exactly the checks `semantic slayer define` runs, read back through
  the SLayer catalog, and stored as **a plan of its own** on the SLayer layer,
  beside the dbt plan, because a plan holds one edit target. `mode` is `included`,
  `plan_id` names that plan, and the hint names both:
  `transform apply <dbt plan>` and `transform apply <plan_id>`. A bare
  `transform apply` takes only the latest, which is the SLayer one.
- **It is not**: `mode` is `proposed`, after the same checks. Listing a file is a
  configuration change with its own confirmation, so `next` names it:
  `dex config set semantic.slayer.models '[..., models/wh/fct_orders.yaml]'`, then
  pass `data.semantic_proposal.definitions` (an edits payload) to
  `semantic slayer define --edits-file`, or re-run the plan to include it.

### Cube (`semantic.vendor: cube`)

One file per mart, `<dir>/<mart>.yml`, where `<dir>` is the one directory the
configured YAML files share (`model/cubes` where they share none):

| Declaration | Cube |
| --- | --- |
| `grain` | `primary_key: true` on each grain dimension, a composite grain included |
| any role but `measure` | a dimension, `sql: "{CUBE}.<column>"`, typed `time`, `number`, `boolean` or `string` from the SQL's casts or the cache's profile; a `time` role is always `time` (with a note where the type could not be read) |
| `measure` with `aggregation` | a measure named after the column, `sql: "{CUBE}.<column>"`: `sum`, `avg` (`average`, `mean`), `min`, `max`, `count`, `count_distinct`. The column is not also a dimension, as MetricFlow does not make it one |
| `median`, `semi_additive` | no measure, named in `limitations` and `not_carried`: Cube has no median type, and no measure that sums across entities but not across time |
| `foreign_key` with `references` | a `many_to_one` join, `{CUBE}.<column> = {<parent>}.<parent column>`, to the cube already on the parent's table; none, or a second key to the same cube, means no join and a note |
| `description` | the cube's and each member's `description` |
| `population`, `assumptions` | the cube's `meta.dex`, and the population sentence in its description; never a measure filter or a segment |
| `unit`, `null_rule`, `additivity` | the member's `meta.dex` |

`sql_table` follows the SLayer order (the siblings' `database.schema`, else the
manifest relation, else the bare name as a limitation), and `data_source` is
written only where `semantic.cube.data_source` is not `default`. A cube already on
the mart's table is `skipped`; a cube or view holding its name is `failed`.
Included and proposed work as for SLayer, against `semantic.cube.files`: listed
paths are stored as a plan of their own (`plan_id`; apply both), others are
proposed with the `dex config set semantic.cube.files '[...]'` that adds them.

### Ossie (`semantic.vendor: ossie`)

One dataset per mart, appended as a new list item to a configured document:

| Declaration | Ossie dataset |
| --- | --- |
| each declared column | a field of the same name, `expression: {sql: <column>}` |
| a column's type, where the SQL or the cache knows it | the field's `datatype` (`Integer`, `Decimal`, `Float`, `Boolean`, `Date`, `DateTime`, `DateTimeTz`, `Time`, `String`) |
| `time` role | `dimension: {is_time: true}` |
| `grain` | `primary_key`, every grain field, a composite grain included |
| `foreign_key` with `references` | a relationship `<mart>_to_<parent>` to the dataset in the same document whose field exposes the referenced column; none means no relationship and a note |
| `measure` with `aggregation` | a dataset-scoped metric `<column>_<agg>`: `SUM`, `AVG` (`average`, `mean`), `MIN`, `MAX`, `COUNT`, `COUNT(DISTINCT ...)`. A measure is also a field, since a dataset metric aggregates its dataset's fields |
| `median`, `semi_additive` | no metric, named in `limitations` and `not_carried` |
| `description` | the dataset's and each field's `description` |
| `population`, `assumptions` | the dataset's `ai_context`: the population sentence as `instructions`, and the declaration under a structured `dex` key; the sentence also closes the description. Never a filter, and never `custom_extensions`, whose opaque string a diff cannot review |
| `unit`, `null_rule`, `additivity` | the field's `ai_context.dex` |

A relationship joins datasets of one model, and a model is one document, so where
it goes follows the foreign keys: the configured document holding the datasets
they reference, or, with no foreign key and one configured document, that one. It
is spliced in, so every other byte of the document stays, and stored as a plan of
its own on the Ossie layer (`plan_id`; apply both). Where the parents span
documents or none holds them, it is `proposed` as a document of its own,
`<dir>/<mart>.ossie.yaml`, with the `dex config set semantic.ossie.files '[...]'`
that adopts it. `source` follows the SLayer order (the siblings' `database.schema`,
else the manifest relation, else the bare name as a limitation). A dataset already
on the mart's table is `skipped`; one holding its name in the target document is
`failed`.

### Declarations on `semantic slayer`, `semantic cube` and `semantic ossie`

`semantic slayer define|update|plan` take the same `declarations` key beside
`edits`. There a declaration **annotates** a SLayer model the payload's edits or
the layer already define (`model` is the SLayer model's name): the declared grain
becomes `primary_key`, descriptions and the population sentence are written, a
`references` adds a `many_to_one` join where none to that model exists, a declared
aggregation adds its `<column>_<agg>` saved measure, and `population`,
`assumptions`, `unit`, `null_rule` and `additivity` land in `meta.dex`. The
declaration wins field by field and nothing else moves; a declaration naming no
defined model is refused. `edits` may be omitted. The result is validated by the
layer's own checks before the plan is stored. `semantic cube` does the same for a
cube (`model` is the cube's name; a view is refused, since it has no table of its
own): grain to `primary_key` on its dimensions, a declared aggregation adds a
measure named after the column, a `references` adds a `many_to_one` join, and
only that cube's entry in its file is rewritten, so every other cube, view and
comment keeps its bytes. `semantic ossie` does the same for a dataset (`model` is
the dataset's name): the grain becomes `primary_key` on the **fields** exposing the
grain columns (a grain column no field exposes is refused by name, since a key
names fields; author the field first), a declared aggregation adds a dataset
metric `<field>_<agg>`, a `references` adds a relationship to the parent dataset's
field in the same document, and the rest lands in `ai_context` as above. Only that
dataset's list item is rewritten, and a relationship is appended, so every other
byte of the document is kept.

Per model, `status` is one of:

| `status` | Meaning |
| --- | --- |
| `included` | in this plan, or for a native layer in the plan named by `plan_id` |
| `proposed` | passed every check; in `definitions` |
| `failed` | a check failed, the grain is composite (MetricFlow), a name is already declared (renaming is yours, never the engine's), or the data source is ambiguous (SLayer); `reason` or `validation` says which. `content` is kept for you to fix, never offered |
| `unvalidated` | a check could not run (dbt absent, or the plan's own edits do not parse), so it is neither offered nor included |
| `skipped` | an authored definition already sits on the mart (never overwritten), or the declaration names nothing a definition carries |

The key is absent when the plan touches no declared mart. Under a vendor whose
layer does not implement the hook nothing is derived and a warning says so.

## `data.decisions`

The plan, apply and build envelopes carry `data.decisions`: every assumption
declared on the models the command touched, as `{model, decision, chosen,
evidence}`. It is read back from the project's YAML, so the three commands report
the same list. An empty list means the touched models declare no assumption.
