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
- `data.prerequisites[]` has one entry per failed node: `node`, `owner`
  (`project` or `package`), `package`, `path`, `message`, `blocks` (the required
  models behind it), `plan_relation`, `previous_run` and `options`.

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
apply. Dex describes routes and generates no repair.

| `kind` | When | What it takes |
|---|---|---|
| `project_edit` | The project owns the node | An ordinary `transform plan` |
| `project_override` | A package model no reader pins | A project model of the same name with the repair, plus `+enabled: false` for it under `models.<package>` in `dbt_project.yml`, in one plan |
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

`dispatch` and a dependency source or pin go through `transform classify` and any
admission a host applies, like every other executable edit. Describing a repair does
not authorize an unrelated dependency change.

## 3. Keep the meaning

When a column inferred from all-NULL data has the wrong type, state the intended type
where the project can keep it:

- a seed: `+column_types` in `dbt_project.yml`. A seed already built in dev keeps
  its old types on a plain reload; on DuckDB `transform build` notices the change
  and rebuilds the seed with `dbt seed --full-refresh`, and elsewhere build with
  `--full-refresh`. Check the type with
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

## 5. When no repair is in scope

Report the deliverable as incomplete and name the exact prerequisite (`node`, `owner`,
`message`) and the remedy you tried. Writing the requested SQL file does not complete
it. For a refactor, repair the prerequisite first so the baseline builds, then run
`transform compare`.
