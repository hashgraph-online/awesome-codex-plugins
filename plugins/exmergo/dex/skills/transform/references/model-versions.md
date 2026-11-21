# A new version of a model: native dbt versions

"Build v2 of `dim_teams` with `display_label` instead of `team_label`. It becomes
the default later, not yet." That asks for a native dbt model version, not a new
model. A new `dim_teams_v2.sql` with its own YAML entry will build, and its tests
and declaration can pass, but none of the following holds for it:

- `ref('dim_teams', v=2)` resolves to it;
- `ref('dim_teams')` keeps resolving to v1;
- dbt knows the two belong to one model.

A green build does not show the difference. `data.model_versions` does.

| | Independent `dim_teams_v2` | Version 2 of `dim_teams` |
|---|---|---|
| Node | `model.<project>.dim_teams_v2` | `model.<project>.dim_teams.v2` |
| `ref('dim_teams', v=2)` | does not resolve | v2 |
| `ref('dim_teams')` | unchanged, by accident | `latest_version`, by declaration |
| Selected as | `dim_teams_v2` | `dim_teams.v2`, or every version as `dim_teams` |
| Declared as | a second plain entry | `"model": "dim_teams.v2"`, into its `versions:` item |
| Promotion | a rename and a rewrite of every reader | `latest_version: 2`, one reviewable plan |

In this file, "v2" always means the `- v: 2` item in `dim_teams`'s `versions:`
list: node `model.<project>.dim_teams.v2`, label `dim_teams.v2`.

## 1. Version the model, keeping v1 where it is

One plan with three edits: the new version's SQL, the YAML entry with its
`versions:` list, and any consumer of the new version.

```json
{"edits": [
  {"path": "models/marts/dim_teams_v2.sql", "kind": "model_sql",
   "content": "select team_id, team_label as display_label from {{ ref('stg_teams') }}\n"},
  {"path": "models/marts/_marts.yml", "kind": "schema_yml", "content": "<below>"}],
 "declarations": [{"model": "dim_teams.v2", "description": "One row per team.",
   "grain": ["team_id"],
   "columns": {"team_id": {"role": "key"}, "display_label": {"role": "dimension"}}}]}
```

```yaml
models:
  - name: dim_teams
    description: One row per team.
    latest_version: 1          # v1 stays the default until a separate promotion
    columns:                   # shared: every version inherits these
      - name: team_id
        tests: [unique, not_null]
      - name: team_label
    versions:
      - v: 1
        defined_in: dim_teams  # v1 keeps the existing dim_teams.sql
        config:
          alias: dim_teams     # and the warehouse relation it already had
      - v: 2                   # built from dim_teams_v2.sql
        columns:
          - include: all
            exclude: [team_label]
          - name: display_label
```

The three choices that keep existing readers working:

- **`latest_version: 1`.** Without it, the highest version becomes the default,
  and every unversioned `ref('dim_teams')` moves to v2 in the same change.
- **`defined_in: dim_teams` on v1.** Only the latest version may live in the
  unsuffixed `dim_teams.sql`. Naming the file explicitly keeps the mapping when
  v2 is promoted later. Without it, the promotion plan is refused with
  `version_file_missing`.
- **`alias: dim_teams` on v1.** dbt builds every version as `<name>_v<N>` by
  default. Versioning an existing model would otherwise move its table to
  `dim_teams_v1` and leave the old `dim_teams` table stale for every warehouse
  reader. The plan warns when a relation moves (`relation_changes`).

Do not keep a plain `- name: dim_teams_v2` entry beside the version. Dbt would
see two models built from one file, and the plan refuses it with
`version_file_collision`.

## 2. Declare each version where it lives

A declaration names one version by its label. It renders into that version's
item under `versions:`, and every other byte stays as it was.

- `"model": "dim_teams.v2"` writes v2's `description` and `config.meta.dex`, and
  v2's own column entries.
- `"model": "dim_teams"` writes the shared top-level entry, which every version
  inherits.
- `"model": "dim_teams_v2"` (the file stem) is refused, naming the label.

dbt merges a version's `config` into the shared entry's. Lists are concatenated
and mappings merged, so a `grain` stated at both levels would come back
doubled. A model-level fact (`grain`, `population`, `assumptions`, `history`)
is therefore stated at one level only: Dex refuses one already stated at the
other level, naming the move.

A version replaces an inherited column wholesale with a same-named entry of its
own, and dbt would then parse that column's tests twice. When a declaration
gives v2 a fact about an inherited column (`team_id`), Dex overrides it the way
dbt reads an override:

1. it adds the column to v2's `exclude` list;
2. it writes v2's own entry, carrying the inherited description and tests
   forward;
3. it says so in the plan's warnings.

A fact the inherited entry already states needs none of this.

`transform declare dim_teams.v2` proposes for that one version. The bare name
`dim_teams` proposes for every version, and so does no selector at all.

## 3. Read `data.model_versions`

The plan reports each versioned model it touches:

| Key | Meaning |
|---|---|
| `versions` | Each version's `label`, `file`, `file_source` (`defined_in`, `suffix`, `unsuffixed_latest`), `relation` and declared `columns`. Once dbt has parsed the project, each also has its `unique_id` |
| `default` | What an unversioned `ref()` resolves to, `before` and `after` |
| `consumers` | Every model that refs it: the `ref` as written, what it resolves to `before` and `after`, `changed` (it reads a different file), and once parsed, its `depends_on` |
| `relation_changes` | A file whose warehouse relation moves |
| `contract_changes` | A pre-existing version whose declared columns change |
| `manifest` | `confirmed` once dbt's own parse of the post-change project agrees, `contradicted` with `mismatches` (each with a `code`), or `unchecked` with a `reason_code` (`dbt_unavailable`, `no_profile`, `parse_skipped`, `manifest_unreadable`) |
| `independent_models` | A new `<model>_v<N>` file that no `versions:` entry maps. It is a copy, not a version |

The plan refuses a versioned model that dbt would build wrong or silently drop:

| Code | Meaning |
|---|---|
| `version_file_missing` | No file builds a version. dbt only warns, and the version would not exist |
| `version_file_collision` | Two versions share one file; a version's file also has a plain entry; or an unmapped `dim_teams.sql` sits beside the versioned `dim_teams` |
| `latest_version_unknown` | `latest_version` is not one of the versions |
| `defined_in_not_a_stem` | `defined_in` has a directory or an extension in it |
| `version_duplicate` | A `v:` is listed twice |

Model versions need dbt 1.5 or later; a parse by an older dbt is refused by name.

## 4. Apply, build and read the version records

```bash
dex transform apply <plan-id>
dex transform build --target dev --verify --for-plan <plan-id>
```

The deliverables in `data.completion` name versions by label (`dim_teams.v1`,
`dim_teams.v2`), so one version building never answers for another.

`data.verification.model_versions` holds the plan's versioned models against
the manifest this build wrote. It has one record per version (`check: version`,
with its `unique_id` and `build_status`), one for the default
(`check: default`), and one per consumer (`check: ref`, with its compiled
`depends_on`). Each record is `satisfied`, `contradicted` (with a `finding`) or
`unchecked`, and reaches `data.completion.obligations`.

Each version's built columns are held to its own declared columns by the column
contract. So v1 has to keep `team_label`, and v2 has to expose `display_label`.

## 5. Promote in a separate plan

Promotion is one line, `latest_version: 2`, as its own plan.

```json
{"edits": [{"path": "models/marts/_marts.yml", "kind": "schema_yml",
            "content": "<the entry with latest_version: 2>"}]}
```

The plan warns `(a promotion)`, and `consumers` lists each one whose `changed`
is true, with what it read before and after. The plan checks that every moving
consumer reads only columns the new default has: if a moved consumer reads a
column the new default lacks (such as selecting `team_label` when v2 dropped it),
the plan warns, naming the consumer, the column, and the old and new version.
A consumer pinned with `ref('x', v=N)` is not checked because its target does
not move (`changed` is false). A consumer whose select list cannot be read
statically is named as unchecked. The check is warning-only; the plan is not
refused.

The warehouse name is a separate decision, so record it as an assumption:

- **Keep** `alias: dim_teams` on v1. Warehouse readers stay on v1 while dbt
  readers move.
- **Move** the alias to v2. Warehouse readers move too. The plan names the
  relation moves.

## Pitfalls

- A `_v2` copy beside an existing model is named under `independent_models` and
  warned about. It is a version only once `versions:` maps it.
- Promoting while v1 still lives in the unsuffixed `dim_teams.sql` with no
  `defined_in` is refused. Only the latest version may live in that file.
- A version with no file is only a warning to dbt, and Dex refuses it.
- A semantic model is not derived for a version (`data.semantic_proposal`).
  Author one with `semantic plan`, naming the version in its `model:` ref.
