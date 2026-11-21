# Instance `_repo` Source

Use this reference when source is loose instance content rather than owned by a Solution. The instance `_repo` is source storage; it is not the same thing as global entity scope. A file stored there may back an org-scoped, role-restricted entity.

The commands below mutate the selected instance immediately. Confirm the connection, organization, access level, and roles before writing.

## Direct file workflow

Use the Files CLI as the ordinary file tool:

```bash
bifrost files list workflows/
bifrost files search "old_function"
bifrost files stat workflows/example.py --json
bifrost files read workflows/example.py
bifrost files write workflows/example.py \
  --from-file /tmp/example.py \
  --expected-version 'sha256:...'
```

For exact options, read `../generated/cli-reference.md`.

`files search` covers workspace source and every Solution install's deployed source. Solution hits print as `slug:path  (read-only Solution source)`, so check them before you change a shared workflow they use. Results come 25 per page. When more exist, the output ends with a `More results:` command; run it unchanged. To find where something lives first, add `--files` for one line per matching file, then narrow with `--include` or `--solution`.

`files write` replaces the complete text content. For an existing file:

1. Run `files stat --json` and retain its opaque `version`.
2. Read the current file and preserve unrelated content in a local temporary copy.
3. Write the complete replacement with `--expected-version <version>`.
4. Read the remote file back and validate the result.

For a new path, use `files write ... --create-only`. For a delete, pass the
current version with `files delete ... --expected-version <version>`.

A guarded conflict exits with code 4 and does not change the remote file. Read
the current version and content, merge deliberately, rerun tests, and retry
with the new version. Never bypass a conflict with an unguarded replacement.

Confirm the exact target before deleting. The CLI file surface is text-only; use the Python or web Files SDK for binary content.

Without `--solution`, the commands target instance `_repo` in the default `workspace` location—even when invoked from a Solution directory. On commands that support it, `--solution <install>` instead targets installed Solution runtime/user files. It never edits local Solution source.

## Source and records are separate

Writing a file does not create its platform record:

| Source | Required live record |
|---|---|
| A decorated function in `_repo` | One scoped workflow registration for every callable that should execute |
| A directory under `apps/<slug>/` | An `inline_v1` app record with matching `repo_path`/slug and access controls |
| A Python helper module | None; it becomes available only when imported by eligible workflow code |

Verify both layers after a change: read the source and get/execute the corresponding entity.

## Module-first organization

Search `_repo` before creating business or integration logic. Reuse and extend
an existing module when it already owns the behavior; workflows should usually
validate inputs, call modules, and shape results rather than contain the domain
implementation.

Preserve the repository's existing structure. When there is no established
convention, organize by domain:

```text
modules/<domain>/
workflows/<domain>/
tests/modules/<domain>/
tests/workflows/<domain>/
apps/<app-slug>/
```

Keep shared modules free of workflow decorators. Put registration-facing
functions under `workflows/`, and keep tests aligned with the source they cover.

## Optional local Workspace development

Use a dedicated non-Solution directory when the user wants a local working
copy of loose `_repo` source. Confirm its `.env` and selected connection, then
pull only into an empty or clean directory. Edit and run tests with ordinary
local tools; use `bifrost run <file> -w <function>` for a local workflow.

There is no remote pytest command. For direct Workspace work, test downloaded
module/workflow source locally when practical, then execute the registered
workflow against the selected instance. Do not invent a platform test runner.

Before sending changes back, re-read or stat every remote target and use the
guarded Files commands above. A broad local sync must not guess through a
conflict. Workspace record changes and workflow registrations still use their
dedicated CLI commands.

## Loose workflows

Write the Python file first, then register every decorated function that should be executable:

```bash
bifrost workflows register \
  --path workflows/example.py \
  --function-name run \
  --org "Org A" \
  --access-level role_based \
  --role-ids operators
```

Registration creates a stable UUID and applies organization/access/role boundaries. One source file may have multiple registrations.

- Editing a registered function body does not require registration again.
- Renaming or moving it requires `bifrost workflows replace <existing-ref> --path <new-path> --function-name <new-name>` to preserve the UUID and dependents.
- Registering the renamed function instead creates a new entity and leaves references on the old UUID.
- Use `bifrost workflows remap` only when intentionally consolidating two existing workflow records.
- Execute the registered ref after writing to verify worker behavior and permissions.

A Solution with `allow_outbound_access: true` can fall back only to an eligible registered loose workflow. Merely placing a decorated function in `_repo` does not make it callable through workflow resolution. To call another install's workflow directly, pass `solution=` (install UUID or slug) to `workflows.execute`; the target's `allow_inbound_access` gate decides, and the child run starts as that install. See `solution-resource-access.md`.

Read `workflows.md` for decorators, testing, dependencies, and tool naming.

## Inline v1 apps

Use v1 only to maintain an existing inline app or when the user explicitly requires a loose app. New apps should be v2 apps inside a Solution.

Create the record before its source files:

```bash
bifrost apps create \
  --name "Finance Dashboard" \
  --slug finance-dashboard \
  --organization "Org A" \
  --access-level role_based \
  --role-ids finance \
  --app-model inline_v1
```

Then write files under `apps/finance-dashboard/` with `bifrost files`. Validate the app record and rendered preview after each material change. App npm dependencies live on the app record and are changed with `bifrost apps set-deps`; they are unrelated to worker Python requirements.

Read `apps-v1.md` for the inline runtime/import model and `app-quality.md` for the completion contract.

## Live entities

Loose forms, agents, tables, configs, integrations, claims, roles, organizations, and event sources/subscriptions are live records. Discover them through `list`/`get`, then use their dedicated create/update/delete verbs. Do not use `.bifrost/*.yaml` as live discovery outside a Solution.

The common org-targeting rule for supported write commands is:

- omit the org flag for the caller's home org;
- use `--org <uuid-or-name>` for a specific org;
- use `--global` for global scope when the entity permits it.

Some older command groups have different aliases. Check the exact command in `../generated/cli-reference.md` instead of guessing.

Read `entities.md` for cross-entity rules and non-obvious semantics.

## Verification and handoff

After mutation:

- read back changed files;
- get the app/workflow/entity record and confirm organization/access/roles;
- execute or render the primary path;
- test a caller who should have access and, when material, one who should not;
- report every live change in the final handoff.
