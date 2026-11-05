# Retiring a feature flag, or making it permanent

"We no longer use this feature; remove its flag" and "make this feature
permanent" both remove a variable's spelling, and they keep opposite behavior.
No search for the name can tell which one happened: a retirement that kept the
enabled branch reports no remaining reads and still builds. Where the output
table is empty, row comparison cannot tell either, so the output schema is what
has to be checked.

| | Retire | Make permanent |
|---|---|---|
| Keeps | The behavior with the feature off | The behavior with the feature on |
| CTEs, joins, outputs of the feature | Removed | Kept, unconditional |
| Tests, docs, semantic references to its outputs | Removed | Kept |
| Conditional machinery and the variable | Removed | Removed |

A flag's default says what the project did, not what the request wants. A
`True` default never means the enabled branch survives.

A flag that stays, with both behaviors kept, is a toggle rather than a
retirement: [feature-toggles.md](feature-toggles.md).

## 1. Find every read

```bash
dex transform references <flag> --kind var
```

`data.targets[].files[]` lists the reads by file, and `package` marks a read inside
an installed package, which is out of scope. `data.indeterminate` lists reads
Dex could not name. Read a flag used in a model's config in YAML too.

## 2. Write each read edit, and state the outcome

Dex removes the definition and never rewrites a read, so the payload carries
every SQL and YAML edit, with a `retirement` contract beside them:

```json
{"edits": [{"path": "models/rpt_orders.sql", "kind": "model_sql", "content": "..."}],
 "retirement": {
   "behavior": "retire",
   "retained_value": false,
   "packages": "out_of_scope",
   "outputs": {"rpt_orders": {"expected": ["order_id", "amount"],
                              "removed": ["region_label"]}},
   "metrics": {"retained": ["revenue"], "removed": ["revenue_by_region"]},
   "assumptions": [{"decision": "Which behavior survives", "chosen": "feature off",
                    "evidence": "request", "detail": "the ticket says it is no longer used"}]}}
```

| Field | Meaning |
|---|---|
| `behavior` | `retire` or `permanent`, for the reader |
| `retained_value` | Required. The flag value whose behavior survives: usually `false` to retire and `true` to make permanent, and the reverse for a flag spelled `disable_x`. Any scalar |
| `packages` | `out_of_scope`, the only accepted value. Installed packages are never edited |
| `outputs` | Required. Per model, `expected` is every column it outputs afterwards, and `removed` is what goes. Name each model the feature's columns reach |
| `metrics` | Metrics that must remain or be gone. Remove a metric in the same payload as its column |
| `assumptions` | The ambiguity you resolved, with its evidence tier. Reported in `data.decisions` |

If the request protects a package, its models keep their behavior even where
they read a flag of the same name.

```bash
dex transform remove var <flag> --edits-file payload.json
```

## 3. Read `data.retirement`

Compiled SQL only, in a throwaway copy, so it reads no rows and judges an empty
table. Each entry in `models[]` has `status` and `branches`: the columns at
`retained_value`, at the other value of a boolean flag, and in the proposal.

| `checks[].check` | What it means |
|---|---|
| `proposal_differs_from_retained_branch` | The proposal's columns are not the retained branch's. Fix the SQL, or `retained_value` if the contract named the wrong branch |
| `removed_output_present`, `expected_output_missing`, `unexpected_output` | The proposal against `outputs` |
| `reads_outside_retained_branch`, `dropped_retained_read` | The model's direct inputs differ from the branch's. A join kept with no output column still moves rows |
| `unused_cte` | A CTE the proposal never reads and the branch does not have |
| `removed_column_still_read` | A removed column still read in SQL, schema YAML or a semantic definition |
| `output_model_missing` | A model with declared outputs that the proposal does not define |

`status: unchecked` is not clean, and `reason_code` says why: `compile_unavailable`
(no dbt or no working dev profile), `unreadable_select` (a star over a relation
hides the columns) or `no_declared_outputs` (a model the plan rewrites with no
`outputs` entry). A flag that is not boolean has no other branch to compile, so
`other_branch: non_boolean_flag`.

`orphaned_models` names models nothing reads any more, which you decide about:
delete one in the payload if the feature was its only reason to exist.
`project_scoped_definition_left` means `dbt_project.yml` still sets the flag under
this project's own `vars:` scope, which `transform remove` does not edit: remove it
with a `project_yml` edit in the payload. `package_scope` lists package readers, whether each has a default, packages that
define the name, and `vars:` entries scoped to a package. None of these is edited.

Every contradiction is a warning. Correct the payload and run the command again.

## 4. Compare against the kept branch

```bash
dex transform compare <plan-id> --model rpt_orders
```

A plan with a contract compiles its baseline at `retained_value`, named in
`data.baseline_vars`, so `equivalent` means the proposal returns exactly what the
chosen branch returns, schema and rows. A dropped column is not a difference to
explain away with a mapping: `different` means the wrong branch survived.
`inputs_unsynchronized` can mean a package parent reads the flag and now compiles
differently, which no comparison of this model can settle: relay it.

## 5. Apply, build and read the contract's records

```bash
dex transform apply <plan-id>
dex transform build --target dev --verify --for-plan <plan-id>
```

`data.verification.retirement` holds one record per output and metric, judged from
the built relation's columns, with no added statement. `retirement_output_present`,
`retirement_output_unexpected` and `retirement_output_missing` are high-severity
findings, and each record reaches `data.completion.obligations`. `not_built` means
the relation in dev predates this run and proves nothing.

## When discovery cannot finish: `scope: authored`

The full retirement refuses while the reference scan has a limit, because a
reader it could not see would survive the change unchecked. A project with
Jinja-heavy macros, or installed packages such as `dbt_utils`, can hold SQL the
column scan cannot parse, and a macro such as
`var('using_' ~ name, true)` names its variable at run time. The refusal names
each file.

Do not fall back to a plain `transform plan` there: it refuses a `retirement` key,
so nothing would check the outputs. Add `"scope": "authored"` to the same contract
and run the same command:

```json
{"retirement": {"behavior": "retire", "retained_value": false,
                "scope": "authored",
                "outputs": {"rpt_orders": {"expected": ["order_id", "amount"],
                                           "removed": ["region_label"]}}}}
```

What changes, and what does not:

| | Full (`scope` omitted) | `scope: authored` |
|---|---|---|
| Admitted when | the scan finishes | the scan cannot finish; a scoped contract on a project whose scan finishes is refused, so drop `scope` there |
| Outputs and metrics | checked at plan, compare and build | the same checks |
| Literal reads the scan found, reads in YAML | refused until edited | refused until edited |
| Dynamic var reads in this project | refused until rewritten | listed under `data.retirement.discovery.dynamic_reads`, not refused |
| `outputs` models | any | must be models this project defines; a package model or a misspelling is refused |
| `metrics.removed` | any | must be metrics this project defines before the payload; a package metric or a misspelling is refused |
| Models the payload rewrites | unchecked without an `outputs` entry | refused without one |
| Global reference discovery | complete | `unchecked`, with `reason_code: discovery_incomplete` |

`data.retirement.discovery` says what was not read: `limits` (project files, the
first 10, with `limits_elided`), `package_limits` (a count per package), `unread`,
and `dynamic_reads`. The first warning names the outputs the checks cover and says
the plan does not show the feature retired everywhere. `removed_column_still_read`
covers only the files the scan read.

After the build, `data.verification.retirement` carries one more record,
`check: reference_discovery`, which is always `unchecked` and reaches
`data.completion.obligations.unchecked`. A satisfied output record says that
output is right. It does not say every reader of the flag was found. Relay both.
The scope and the discovery summary travel in the stored plan and in the plan
document, inside its digest.

## Dynamic readers and repeats

- A read in this project that names no literal variable (`var(flag_name)`) is
  refused by file and line, since it may read this flag. Rewrite it to name its
  variable, or remove it, in the same payload.
- A read written in YAML (`enabled: "{{ var('flag') }}"`) is refused the same way.
- A dynamic read in a package is reported, not refused, and not edited. Read that
  line; if it reads this flag, pin the value under a package-scoped `vars:` entry.
- A package read with no default stops compiling when the definition goes, and
  the plan warns. Keep a package-scoped `vars:` entry, or disable that model.
- Running the same payload after the retirement is applied is a no-op:
  `data.plan_id` is null and `data.retirement.status` is `already_complete`. A
  payload that changes a file is a new plan, which is how a retirement that kept
  the wrong branch gets corrected after the flag's name has gone.
