# Repairing a prerequisite so the repair lasts

A deliverable is not done while something upstream stops it from building, and a
repair that the next `dbt deps` or source reload undoes is not a repair.

## 0. Settle which layer the request asks to change

A green build is not the measure here. The request is, and the same failure has a
different correct answer depending on what was asked. Decide the target before
choosing a route, and do not move to another layer because it is easier to repair.

| The request says | Target | Supported route | Postcondition to check | Report |
|---|---|---|---|---|
| "Modify our data", "fix the source types", "make the data match the package" | The input | A project seed: its CSV or `+column_types` in `dbt_project.yml`, then a build. A source a loader owns: none from Dex | The original relation's column types (`explore profile`, with `--target dev` for a seed) and its row count | For a loader's source, the type the loader must produce, and any migration as a reviewable file marked not run. That part of the request is incomplete |
| "Make it build", "adapt the project to the package", "we cannot change the raw data" | The project | `project_edit`, `project_override`, `macro_dispatch` or `pinned_dependency`, from `data.prerequisites` | The deliverable is built and keeps every row, and the input is unchanged | The route, and the `--cold-deps` evidence that it survives a reinstall |
| Neither | Whatever the contract settles: a seed is project-owned, a declared source is the loader's | As above, for the settled target | As above | The choice, as an assumption with its evidence tier |

- A project override does not fulfil an input request, however well it builds.
  Doing both is fine where it helps: say which part is which.
- An input request is not write authority. Dex is read-only against data, so a
  loader's source is never changed through `explore query`, a raw database client
  or a hand-edited database file. That part stays with whoever loads the source.
- A project request never changes the input, even where the input is a seed Dex
  could rebuild.
- `--cold-deps` shows a project repair survives a reinstall. It says nothing about
  whether the data changed, so it is not evidence for an input request.

## 1. Read what stopped it

Build with the plan named, and read the envelope in this order:

```bash
dex transform build --target dev --verify --for-plan <plan-id>
```

- `data.completion.deliverables` says which required models were built, failed or
  skipped, and what blocked each one. A skipped model's relation in dev predates
  this run, whatever it holds.
- `data.completion.blockers[]` names each failed node, and its `next` is the one
  command that repairs it: `repair: dex transform repair <node>` for a package
  model the project can override, `repair: transform plan on <path>` for the
  project's own. It sits in the bounded block, so it survives a cut-off read.
- `data.prerequisites[]` has one entry per failed node: `node`, `owner`
  (`project` or `package`), `package`, `path`, `message`, `blocks` (the required
  models behind it), `plan_relation`, `previous_run`, `options` and the same
  `next`.

`plan_relation` separates a failure you inherited from one you may have caused:

| Value | Meaning |
|---|---|
| `independent` | The node neither is nor descends from anything the plan edits. This plan did not break it, so it is pre-existing relative to the plan |
| `edited` | The plan edits this node. It may be a regression |
| `downstream_of_edit` | The node descends from an edit. It may be a regression |
| `undetermined` | No plan was named, or the plan edits a macro, the project config, the packages or a test file, any of which can reach any node |

Only `independent` is a claim. Dex holds no baseline run, so `edited` and
`downstream_of_edit` say the plan could be the cause, not that it is.

`previous_run` reports an earlier status, invocation ID, timestamp and selection,
or `available: false` with a reason code. A previous failure is useful historical
context, but the earlier run may have used another selection or source tree.
Keep `plan_relation` as reported; this evidence is not a baseline comparison.
The context survives pricing and confirmation retries without another build.
Ordinary and cold runs have separate histories. `completion.blockers` carries
`previous_status` when known.

On a verified build, `verification.scope` names successful models and
`scope_not_built` names failed, skipped or otherwise unsuccessful models.
`evidence.coverage.covered` includes those unsuccessful nodes when they appear in
run results; use `built` and `not_built` to distinguish successful execution.

## 2. Choose a route `options` supports

`options` lists each route with `supported`, and `how` or the `reason` it does not
apply. Dex drafts the `project_override` route for you (section 2a); the others it
describes.

| `kind` | When | What it takes |
|---|---|---|
| `project_edit` | The project owns the node | An ordinary `transform plan` |
| `project_override` | A package model no reader pins | `dex transform repair <node>` (its `repair` field) drafts it: a project model of the same name with the repair, plus `+enabled: false` for it under `models.<package>` in `dbt_project.yml`, in one plan |
| `macro_dispatch` | The node calls a package macro that goes through `adapter.dispatch` | A project macro plus a `dispatch` search order. `macros` names the candidates; check the failing logic is really in one |
| `pinned_dependency` | A repaired revision of the package exists | A pin in `packages.yml` |

A package model is not always overridable, and `project_override` says so where it
can tell:

- A reader using `ref('<package>', '<model>')` binds to the package's own node, so
  disabling that node fails to compile.
- A versioned model, a Python model, and a node that is not a model (a seed, a
  snapshot, a test) are refused too.

An override without the disable fails to parse: dbt refuses two resources with one
database representation.

When the package also documents the model in a YAML entry, `project_override`
names that file as `package_entry`. dbt gives the package's entry to your override:
the package's lookup misses its disabled model and falls back to the project's model
of the same name, so the override takes the package's description, columns and tests.
A second entry for the same name, in any project file, fails dbt's parse as two
entries for one resource. That holds on every dbt version Dex supports, and no YAML
construct gets around it. So the override carries no declaration and no YAML entry
of its own. `transform plan` refuses either one before dbt runs, naming both files.
Plan the override without it, and declare the models that read it instead; the
procedure owes no declaration for the override, `transform plan` does not warn that
it declares nothing, and `transform declare` skips it as `package_documented`. The
package's own tests run against the override, so a test that fails there is a
finding about your repair.

## 2a. Draft the override with `transform repair`

A blocker of the request's own deliverables is part of the request: the
project-side repair is how the request completes, not scope creep. For a package
model, let Dex write it:

```bash
dex explore profile <the input the failing model reads>   # the evidence
dex transform repair <node> [<node>...]                   # the draft, as a plan
```

Name every failed package model in one call: each override disables its node in
the same `dbt_project.yml`, so separate plans would conflict when applied.

The draft restates the package's SQL as `<model path>/overrides/<node>.sql`, the
mechanical part done for you: package macros called unqualified are qualified
(`get_task_columns()` becomes `asana_source.get_task_columns()`), each `var()`
gives the override what it gave the package (a relation var is inlined, which
also removes a `var('task')` cycle; a pass-through list a macro reads by name is
set under `vars.<project>`), and the package's `materialized`, `schema` and
`alias` are restated. It disables the package's node in `dbt_project.yml`, in
place.

The conversion is read from the error and the data, never guessed. Only the
columns of the type the error names, inside the calls it names, change, and only
where the cached profile settles what they hold:

| The profile shows | The draft writes | `meaning_changing` |
|---|---|---|
| every value NULL | a cast through text (`cast(cast(c as varchar) as timestamp)`) | false |
| unix epoch seconds or milliseconds | the warehouse's epoch reader (`epoch_ms(...)`, `timestamp_seconds(...)`) | true: relay it as a decision |
| ISO dates or timestamps in text | a parse (`cast(c as timestamp)`) | false |
| anything else, or nothing profiled | the column as the package wrote it, `unresolved`, with the reason and the profile to run | |

The draft is compiled and bound on dev before it is stored (DuckDB `limit 0`,
BigQuery's free dry run), and a further typing error that binding reveals is
converted the same way. `data.repair` says what was read and done; its `status`
is `resolved` only when every failure was converted and the draft binds; a
draft converted but never bound (no dbt, no connection, or a warehouse with no
free check) is `unbound`, and the build is the first check of its types.

Read the diff, then apply and build it as its own plan:

```bash
dex transform apply <plan-id>
dex transform build --target dev --verify --for-plan <plan-id> --cold-deps
```

`data.completion.obligations.repair` holds the build to `repair_built`,
`repair_tests` (the package's own tests, run on the override), `repair_cold_deps`,
`repair_row_count`, and `repair_conversion` while a conversion stays unresolved
or an `unbound` draft has not built. The draft never adds a filter, so the package's own
filters stand and the override holds the rows the package would have: a Fivetran
staging model still drops `_fivetran_deleted` rows, which can leave fewer rows
than the raw source. A draft left `unresolved` is still a plan: edit the
column it names (or profile the input and repair again) before applying it.

Writing the override by hand is still possible. Copy the package model's SQL as
it stands, column-listing macros included: a Fivetran
staging model's `fill_staging_columns(adapter.get_columns_in_relation(...))` or a
`dbt_utils.star(ref(...))` plans through `transform plan` like any other model, since
Dex answers the column listing from metadata. Never apply the override outside Dex
because a plan refused it: relay the refusal instead.

`dispatch` and a dependency source or pin go through `transform classify` and any
admission a host applies, like every other executable edit. Describing a repair does
not authorize an unrelated dependency change.

## 3. Keep the meaning

When a column inferred from all-NULL data has the wrong type, state the intended type
where the project can keep it:

- a seed: `+column_types` in `dbt_project.yml`. A seed already built in dev keeps
  its old types on a plain reload; on DuckDB `transform build` notices the change
  and rebuilds the seed with `dbt seed --full-refresh`. Elsewhere, rebuild only
  that seed with `transform build --target dev --select <seed> --full-refresh`,
  since the default selection would also rebuild every incremental model, then
  build what reads it as a separate step. Check the type with
  `explore profile <dev namespace>.<seed> --target dev`;
- a model, your own or an override: an explicit cast to the intended type, valid on
  your warehouse. BigQuery refuses a cast from an integer to a timestamp, so an
  all-NULL integer column goes through a string first:
  `cast(cast(legacy_ts as string) as timestamp)`;
- a source table you do not load: state the type the loader must produce, and report
  it. Dex does not write to the warehouse. If the request was to change that data,
  the request is not complete, whatever the project now builds (see section 0).

Type every column the failing expression combines, not only the one that broke:
`coalesce(due_at, due_on)` needs both sides to agree. A seed's inferred types differ
by warehouse (BigQuery reads `2024-01-04 09:00:00` as `DATETIME`, DuckDB as
`TIMESTAMP`), so a repair that types only the all-NULL column can still fail there.

Never filter rows out to make a cast succeed. Check the row count after the repair,
and read `data.identifier_conversions` on the plan. An identifier the cast cannot
convert may belong to a second legitimate scheme, and a cast can merge two keys
(`7` and `007`). Those counts show both, even when the row count holds.

These look finished and are not:

- **An edit under `dbt_packages/`.** The next `dbt deps` replaces it.
- **An `ALTER TABLE` on the warehouse or a hand-edited local database.** Nothing
  reproduces it after a reload, even though `dbt deps` leaves it in place.

## 4. Prove it survives a reinstall

```bash
dex transform build --target dev --verify --for-plan <plan-id> --cold-deps
```

`--cold-deps` copies the project without `dbt_packages/`, runs `dbt deps` in the copy
(honouring `package-lock.yml`), and builds from there under the same dev-only and cost
gates. It rebuilds the dev relations. Your own `dbt_packages/` is not touched, and an
ordinary build never does this, because it may reach the network.

`data.cold_verification` reports `reinstalled`, `reinstalled_at`, `dbt_runtime`, the
`packages` with their pins, `lock_digest`, `installed_tree_digest`, `artifact_directory`
and `installed_edits`: the `changed`, `added` and `removed` files your installed tree
held that the reinstall did not reproduce. A non-empty list means something passing
locally depended on an edit that a reinstall discards.

Limits:

- A `local:` package is linked rather than copied, so an edit through `dbt_packages/`
  writes to its source and survives a reinstall. It is listed under
  `installed_edits.not_compared` and a note says so.
- A failed install stops with `reinstalled: false` and builds nothing. It never falls
  back to the installed tree.
- With no package lockfile, the reinstall resolves versions afresh, and a note says so.

Installing the packages the project already declares is not installing a tool.
`dex transform deps`, the build's own install and `--cold-deps` fetch what
`packages.yml` names, at the versions `package-lock.yml` pins where it matches
(dbt resolves them again where it does not). A cold build of a project with a
relative `local:` package rewrites that path in its copy and drops the lockfile
there, so it resolves every package afresh: read `data.cold_verification`
(`packages`, `lock_digest`, `notes`) for the versions it actually installed.
A request not to
install or upgrade tools (dbt, Dex, Python packages) does not rule them out.

## 5. A refactor whose baseline is blocked

A refactor is proven by `transform compare`, which compiles the old and new SQL
over the inputs the dev target holds. When a prerequisite fails, those inputs are
whatever an earlier build left, so the comparison is `not_checked`
(`inputs_unsynchronized`) until the repair is built. The order matters:

1. **Plan the refactor and read the offer.** `data.refactor_comparison_offer`
   says `baseline_ready: false` and lists each blocked input under
   `per_model[].blocked_inputs` with its `owner` (and `package`). Do not apply
   this plan: applying it discards the baseline (`plan_applied`).
2. **Repair the prerequisite in a plan of its own**: for a failed package
   model, the `repair` its `blocked_inputs[]` entry names (`dex transform repair
   <model>`, section 2a), every failed one in one call. A `skipped` input names
   no repair: it was skipped because something upstream failed, so find that
   failed node in the build's `data.prerequisites` and repair it, and the skipped
   input rebuilds with it. Otherwise use a supported route from
   `data.prerequisites`. Apply it.
3. **Build the repair.** Where a package owns the node, build it cold:

   ```bash
   dex transform build --target dev --verify --for-plan <repair plan> --cold-deps
   ```

   For a project model, a plain build is enough. Either way, build every input
   the offer lists under `blocked_inputs`, the `skipped` ones too, or leave the
   build unnarrowed: a later build rewrites the run results, so an input it
   leaves out loses its `skipped` status and the comparison would read that
   input's stale relation. `transform compare` reads the latest attempt of each
   input, a cold build's included.
4. **Compare the refactor's plan** (the one from step 1, still unapplied). If the
   repair changed a file that plan edits, the comparison is `plan_stale`: plan
   the refactor again first. `equivalent` carries `inputs_built_by`, where an
   upstream build exists, naming the latest build among the model's upstream
   models.
   Other inputs may come from earlier builds, so `cold: true` does not mean
   every input came from that cold build. Relay it with `input_scope` and
   `compared_at`.
5. **Apply and build the refactor** with `--for-plan`. `data.completion`
   carries the recorded verdict.

Never put the repair in the refactor's plan. Its comparison would read the
failed build for the baseline, so it can never be usable: the plan carries
`mixed_with_repair`, a warning names the split, and `data.next` asks for it.

## 6. When the repair cannot be made

A blocker of the request's own deliverables is in scope, so stop only when the
repair cannot be made: `transform repair` refuses the node (the override route is
refused, or the draft does not compile) and no other route the build's
`data.prerequisites` marks `supported` (`macro_dispatch`, `pinned_dependency`)
resolves it, or a conversion stays `unresolved` with no profile or request that
settles it. Then report the deliverable as incomplete
and name the exact prerequisite (`node`, `owner`, `message`) and the remedy you
tried. Writing the requested SQL file does not complete
it. A refactor left blocked has no comparison: say so, rather than citing a
`not_checked` verdict or a manual spot check as equivalence. Where the request
needs a change to data only its loader can make, that part stays incomplete
however the build turns out: a project override does not fulfil it (doing both
is fine where you say which part is which), and nothing routes around the guard.
