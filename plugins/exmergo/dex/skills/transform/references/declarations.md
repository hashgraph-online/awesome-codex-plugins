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

`drafted` is never written into the project. Each fact carries the `evidence` it
rests on, and a fact the cache cannot support is left out rather than guessed:

| Drafted | When |
|---|---|
| `grain` | the `GROUP BY` keys when the model aggregates; otherwise a key the driving relation's profile *proved* unique, selected unchanged, with every join an equality on a key proven unique on its joined side. Any other join, a right or full join, a set operation or an `UNNEST` gives `{"value": null, "withheld": "<why>"}` |
| `columns.<c>.from` | the upstream `relation.column` a column passes through from unchanged, followed through CTEs |
| `columns.<c>.role` | `key` for a single-column drafted grain; `foreign_key`, with `references`, for a column carrying a join `explore relationships --verify` measured with no orphans. A join measured with orphans would fail the `relationships` test a `references` renders, so it is `references: {"value": null, "withheld": "<the orphan rate>"}` instead |
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

When `transform plan` or `semantic define|update|plan` creates, edits or declares a
model under `transform.marts_paths` (`.dex/config.yml`, default `[models/marts]`,
relative to the dbt project, subfolders included) and the model's post-change YAML
carries a declaration, the engine derives the MetricFlow semantic model the
declaration already states:

| Declaration | Semantic model |
| --- | --- |
| a single-column `grain` | the primary entity (`order_id` becomes entity `order`) |
| a composite `grain`, or none | no primary entity, and none guessed: MetricFlow needs one for any dimension or measure, so the derivation is `failed` with the limitation named. Add `primary_entity:` and pass it to `semantic plan` yourself |
| `foreign_key` | a foreign entity. With `references`, it takes the entity name the referenced model's semantic model already gives that column, so the join resolves; otherwise the column's name less `_id`, with a note |
| `dimension` | a categorical dimension |
| `time` | a time dimension: `day` for a date, `day` for a timestamp (noted, since finer is the author's choice), the truncated grain where the SQL truncates (`date_trunc('month', ...)`), `day` with a note where the type cannot be read. A column whose type is known not to be temporal is left out. The first time column is `defaults.agg_time_dimension`, and a note names the others |
| `measure` with `aggregation` | a measure: `sum`, `count`, `count_distinct`, `min`, `max`, `average` (`avg`, `mean`), `median`, `sum_boolean`. Anything else (`percentile` needs parameters a declaration does not carry), a missing aggregation, or `non_additive` with a summing aggregation is left out and named. A model with no time column carries no measure, since MetricFlow aggregates over one |
| `semi_additive` | `non_additive_dimension: {name: <default time dimension>, window_choice: max}`: each period reports its last value, which suits a balance or a season-to-date total. MetricFlow's own default is `min`; the note asks you to confirm |
| `description` | carried onto the semantic model, dimensions and measures (MetricFlow's schema has no entity description, and a note says so) |

Metrics are never derived. A measure is what a column holds; a metric is a
business definition, and it stays the author's.

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
      "limitations": []
    }
  },
  "next": "save this object as a file and pass it to `semantic plan --definitions-file <file>` ...",
  "notes": ["the project has no dbt semantic layer and no MetricFlow time spine ..."]
}
```

Per model, `status` is one of:

| `status` | Meaning |
| --- | --- |
| `included` | in this plan |
| `proposed` | passed every check; in `definitions` |
| `failed` | a check failed, the grain is composite, or a semantic model or measure name is already declared (renaming is yours, never the engine's); `reason` or `validation` says which. `content` is kept for you to fix, never offered |
| `unvalidated` | a check could not run (dbt absent, or the plan's own edits do not parse), so it is neither offered nor included |
| `skipped` | an authored semantic model already sits on the mart (never overwritten), or the declaration names nothing a semantic model carries |

The key is absent when the plan touches no declared mart. Under `semantic.vendor:
ossie` or `slayer` nothing is derived and a warning names the vendor's own
authoring verb.

## `data.decisions`

The plan, apply and build envelopes carry `data.decisions`: every assumption
declared on the models the command touched, as `{model, decision, chosen,
evidence}`. It is read back from the project's YAML, so the three commands report
the same list. An empty list means the touched models declare no assumption.
