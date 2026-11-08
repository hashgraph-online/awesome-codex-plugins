# Adding or changing a feature toggle that stays

"Hide the fee columns when `enable_fees` is false" keeps both behaviors: the
project ships with the flag, and either value has to build a correct project.
The change is done when **no model of the project** outputs a governed column
with the flag off, and every model that outputs one today still does with it on.
Gating the models that feed the mart you were thinking of is not enough: a
ledger nothing in the marts reads, an intermediate the mart never selects from,
and a model that inherits the column through `select *` all still produce it.
An empty table is no evidence either way, since a row comparison of nothing
passes; only its columns are.

| | Toggle (this recipe) | Retire or make permanent |
|---|---|---|
| The flag afterwards | Stays, read in the SQL | Gone |
| Behaviors that survive | Both, one per value | One |
| Contract | `toggle` on `dex transform plan` | `retirement` on `dex transform remove var` (`feature-retirement.md`) |

## 1. Find every producer before writing anything

```bash
dex transform references fee_amount fees --kind column --full
dex transform references <flag> --kind var --full
```

The first lists every model, YAML entry and semantic definition that names a
governed column, across the whole project, connected to the mart or not. The
second lists the flag's existing reads, if it already exists. `--full` lifts
the cap of 200 occurrences and 50 files; without it the answer can stop short
with no file named. Read `data.completeness` and `data.limits`: `incomplete`
means some files could not be read, so the list may be short. Resolve each entry
under `data.indeterminate` by reading its line, since it may or may not name
what you asked about. Dex re-checks the models from compiled SQL in step 3; it
does not re-check tests or semantic definitions, so the search is what finds
those.

## 2. Write the gated edits, with a `toggle` contract

Gate each producer's governed columns (`{% if var('enable_fees') %}, fee_amount{% endif %}`),
give the flag its value in `dbt_project.yml` (a `project_yml` edit), and state the
toggle beside the edits:

```json
{"edits": [
   {"path": "models/marts/fct_order_lines.sql", "kind": "model_sql", "content": "..."},
   {"path": "models/finance/ledger_entries.sql", "kind": "model_sql", "content": "..."},
   {"path": "dbt_project.yml", "kind": "project_yml", "content": "..."}],
 "toggle": {
   "variable": "enable_fees",
   "on_value": true,
   "off_value": false,
   "columns": ["fee_amount", "fees"],
   "exempt_models": ["stg_orders"],
   "assumptions": [{"decision": "Whether staging keeps the raw fee column",
                    "chosen": "staging passes the source through",
                    "evidence": "default",
                    "detail": "the request names the reporting models"}]}}
```

| Field | Meaning |
|---|---|
| `variable` | The flag. The plan's tree must read it, or the plan is refused |
| `on_value`, `off_value` | Required, never inferred from the default. Usually `true` and `false`, the reverse for a flag spelled `disable_x` |
| `columns` | Every output column the feature governs, by name, in any model |
| `exempt_models` | Models allowed to keep a governed column with the flag off, such as a staging model that passes a source column through. State why in `assumptions` |
| `packages` | `out_of_scope`, the only value. Installed packages are never edited |
| `assumptions` | The ambiguity you resolved, with its evidence tier. Reported in `data.decisions` |

```bash
dex transform plan "hide fee columns behind enable_fees" --edits-file payload.json
```

Only `transform plan` takes `toggle`. Every other command refuses it rather than
dropping it unread, and a payload cannot carry `toggle` and `retirement` together.

A disabled model that reads the flag is edited through the same plan. dbt
compiles no SQL for a disabled model, so Dex compiles it once more in the
throwaway copy with an in-file `config(enabled=true)` to hold its SQL to the
same read-only checks, and warns that it is not built. Do not edit it outside
the plan.

## 3. Read `data.toggle`

Dex compiles **every model of the project** in a throwaway copy three times: the
proposal at `on_value`, the proposal at `off_value`, and the tree before the plan
at `on_value`. The checks read compiled SQL and never probe a table's rows, so an
empty table is judged like a full one. Compiled SQL is the judge: a select list
or a `group by` count gated with `{% if var(...) %}` is plain SQL once compiled,
so a model whose source text the reference scan cannot parse is still judged at
both values, and that scan's "could not parse the SQL for columns" is not a
limit here. A `*` over another model, a seed or a profiled source is resolved
from that relation in the same compile. Compiling can still query the warehouse
where a macro does (`run_query` and other introspective macros), which a
metered connector bills.
`models[]` lists each producer and each model with a problem, with its columns on
each value under `branches` (`"disabled"` where the model is off at that value);
the rest are counted in `models_clean`. `contract.producers` is every model that
outputs a governed column with the flag on.

| `checks[].check` | What it means | Fix |
|---|---|---|
| `governed_column_present_when_off` | The model still outputs the column with the flag off. The usual cause is a producer nobody gated | Gate it, or exempt it with a reason |
| `governed_column_read_when_off` | The flag-off SQL still reads the column, so something it outputs under another name depends on the feature | Gate the expression too |
| `governed_column_lost_when_on` | With the flag on, the model no longer outputs a governed column it outputs today | The on branch must keep today's behavior |
| `ungoverned_column_lost` | A column the toggle does not govern is gone on either value | Keep it, or add it to `columns` |
| `ungoverned_columns_differ` | The two values output different non-governed columns | Same as above |
| `branch_compile_failed` | The model does not compile at one value (for example, a dangling ref). Recorded on that model alone; the rest of the project is still judged | Fix that branch |

`verdict: satisfied` needs every record satisfied **and** `completeness: complete`.
`unchecked` is not clean. A record carries a `reason_code`:

| `reason_code` | Meaning | Next step |
|---|---|---|
| `unreadable_select` | A `*` over a source with no cached profile, or compiled SQL Dex cannot read | `dex explore profile` the source the reason names |
| `compile_failed` | The model does not compile at either value. dbt stops at the first failing model, so Dex sets it aside and compiles the rest again | Fix the model |
| `not_compiled` | A disabled model that reads the flag, itself or through a macro. dbt compiles no SQL for it, so it is named under `not_compiled` and the verdict is incomplete for it alone | Enable it to have it judged, or delete it if it is retired |
| `compile_unavailable` | No dbt or no working dev profile, so nothing compiled | Fix the environment |

Where the flag is read is reported beside the records:

- `reads` lists every literal read, by file and line.
- `macro_reads` lists each read inside a project macro, with the `models` whose compiled SQL calls that macro, directly or through another macro. Their output is judged with the rest.
- `dynamic_reads` lists each `var()` whose name is not a literal, with the model it sits in (or, in a macro, the models calling it). The compile gives the flag its value wherever it is read, so a dynamic read is already inside the compiled SQL that is judged. It is listed so you can confirm it, and does not limit the verdict.

`limits` names what the reading could not cover: the disabled models above, the
tree before the plan failing to compile, or a reference-index limit other than a
column parse. `package_scope` names package models that read the flag; they are
reported and never judged.

Correct the payload and plan again until the verdict is `satisfied`.

## 4. Compare the on value against today

```bash
dex transform compare <plan-id> --model fct_order_lines
```

With a toggle, both sides compile at `on_value` (`data.baseline_vars` and
`data.proposed_vars`), so `equivalent` means the feature on returns exactly what
the project returns today. Run it for each rewritten producer whose values must
not move.

## 5. Apply, build and read the build's records

```bash
dex transform apply <plan-id>
dex transform build --target dev --verify --for-plan <plan-id>
```

`data.verification.toggle` judges the relations this build wrote, from metadata
alone, at the value the build ran with: the flag's value in `dbt_project.yml`, or
the default every read states.

- Built with the flag **off**, every model is checked:
  `toggle_column_present_when_off` (high) names each relation that still has a
  governed column, an empty one included.
- Built with the flag **on**, every producer is checked:
  `toggle_column_missing_when_on` (high) names each one that lost its column.
- The other value has one record per producer, `unchecked` with
  `reason_code: branch_not_built`. The plan judged it from compiled SQL; no build
  wrote it.
- `value_unknown` means the value could not be read, so nothing was judged.

A `schema.yml` that documents a governed column is not reported as
`column_missing` on an off build: dbt cannot make a column's entry conditional,
and the toggle record judges it instead. Every record reaches
`data.completion.obligations`.

To build the other value on dev, flip the flag's value in `dbt_project.yml`
through a reviewed plan that carries the same `toggle`, then build again with
`--verify` and `--for-plan`, and flip it back the same way. There is no `--vars` on
`transform build`.

## What this does not establish

- The values in the on branch: `transform compare` does that, at `on_value`.
- Package models: named under `package_scope`, never judged.
- A disabled model: named under `not_compiled` until it is enabled.
- A metric or semantic definition over a governed column: run
  `dex transform references <column>` and change it in the same payload.
