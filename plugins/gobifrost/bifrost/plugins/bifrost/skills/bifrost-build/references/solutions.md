# Solution Workspaces

A Solution is a portable definition installed on a Bifrost instance. Apps, workflows, forms, agents, tables, configs, claims, and declared file locations owned by an install are deploy-managed: edit local source and deploy rather than mutating their live records.

## Definition and install selection

`bifrost.solution.yaml` defines the portable Solution: slug, name, version, `allow_outbound_access`, `allow_inbound_access`, and optional git/logo fields. It carries neither an install ID nor install scope. Both access flags are install-local settings (patchable after install); the descriptor only supplies defaults for fresh installs.

`allow_outbound_access` gates this install reaching shared `_repo` resources. `allow_inbound_access` (default on) gates outside callers targeting this install per-call with `solution=`. Both off is deterministic isolation. Set either at create with `bifrost solution create --allow-outbound-access`/`--allow-inbound-access` (or the `--no-` forms), and change it after install with `bifrost solution update --allow-inbound-access`/`--no-allow-inbound-access`. Read `solution-resource-access.md` for the runtime behavior.

The CLI selects an instance through `--url`, `BIFROST_API_URL` in the local
`.env`, or the selected default profile. It resolves an install from the
portable slug. When multiple accessible installs share that slug, it stops and
prints the valid `--solution <id>` choices.

An explicit `solution bind` may remember one install in `.env` for repeated
work, but creation does not bind automatically. Optional local selectors are:

- `BIFROST_API_URL`
- `BIFROST_SOLUTION_ID`
- `BIFROST_SOLUTION_SLUG`
- `BIFROST_SOLUTION_ORG_ID`
- `BIFROST_SOLUTION_SCOPE`

Do not commit `.env`. It is local command selection, not portable source.

Create a new workspace and install:

```bash
bifrost solution create . --slug dispatch --name "Dispatch"
```

`solution init` is an alias. To explicitly remember one existing install:

```bash
bifrost solution bind --solution <install-id-or-unique-slug>
```

`solution create` and `solution install` use the standard org targeting behavior: omit targeting for the caller's home org, use `--org <ref>` for another org, or `--global` for a global install. `solution start` resolves a unique existing install or requires `--solution` when several are visible. Deploy also reuses a unique existing install; when none exists it refuses to guess the new install's scope and requires `--org <ref>` or `--global`.

## Source layout and ownership

```text
bifrost.solution.yaml
.env                         # optional local selectors; uncommitted
.bifrost/
├── apps.yaml
├── workflows.yaml
├── forms.yaml
├── agents.yaml
├── tables.yaml
├── configs.yaml
├── claims.yaml
└── files.yaml
apps/<slug>/                 # standalone_v2 app source
functions/                   # Python source
modules/                     # optional Solution-owned Python modules
```

The `.bifrost/*.yaml` files are Solution source of truth. Edit content fields of already-owned entities, then deploy. Preserve manifest identity keys; introduce an existing loose entity through capture/pull rather than inventing its managed identity.

Forms and agents store portable content inline under their UUID in their manifests. Environment-specific organization, access, role, creator, and timestamp data remain outside that portable content. Do not move those fields into the shareable content block.

Runtime file bytes are not source. Declare their locations in `.bifrost/files.yaml` and access them through managed-file APIs; read `files.md`.

## Add apps and workflows

Scaffold every new app:

```bash
bifrost solution scaffold-app operations
```

The command creates source and its app manifest entry. Read `apps-v2.md`, `app-quality.md`, and `web-sdk-v2.md` before implementation.

Place workflow code under `functions/`. Every callable that should become a workflow entity also needs a `.bifrost/workflows.yaml` entry:

```yaml
workflows:
  <fresh-uuid>:
    id: <fresh-uuid>
    name: list_items
    path: functions/items.py
    function_name: list_items
```

Deploy creates/updates the row. Do not run `bifrost workflows register` for Solution-owned code. Use portable refs such as `functions/items.py::list_items` from apps, forms, and agents.

For logos, the Solution catalog logo and app header logo are independent. `bifrost.solution.yaml` uses a Solution-root-relative path; the app manifest uses a path relative to that app's source directory. Set and verify both when both surfaces should be branded.

## Add or adopt other entities

For a net-new Solution-owned form, agent, table, config declaration, or claim, add a fresh UUID-keyed entry to the corresponding `.bifrost` manifest when its shape is known. Deploy creates the managed row. Do not create a loose entity merely to manufacture an identity.

For complex content, the entity CLI can be used deliberately as a scaffolder: create the loose record from a neutral directory selecting the same instance and intended scope, then capture and pull its canonical manifest. This is optional for net-new work, not the ownership model.

To adopt an existing loose entity, capture it into the target install, pull its canonical manifest entry, then deploy:

```bash
bifrost solution capture <install-id> --table <ref> --form <ref> --agent <ref>
bifrost solution pull --solution <install-id>
bifrost solution deploy
```

Capture selectors are singular and repeatable (`--workflow`, `--table`, `--app`, `--form`, `--agent`, `--claim`, and `--config`). The loose entity must already be eligible for the install's scope. An org install captures entities in that org; a global install captures global entities. Capture is not a cross-tenant move.

Capture changes server ownership but does not write local source. Always pull after capture. Deploy blocks captured-but-unpulled entities to prevent a full-replace reconcile from deleting them. For a larger v1-to-v2 adoption, use `bifrost:migrate`.

Within a net-new bundle, forms and agents may reference a new Solution workflow by its portable locator; deploy owns both definitions. A separate preliminary deploy is needed only when a live CLI scaffolding step must resolve the workflow before capture.

## Connected local development

```bash
bifrost solution start
bifrost solution start operations --port 3000
```

Open the proxy origin printed by the command. The Vite server runs behind it on another port. App and local workflow changes hot-reload without deploy.

The preview is connected to the selected live instance and resolved install:

- local workflow execution is transient;
- tables, runtime files, configs, integrations, and knowledge use real environment state;
- an open Solution may fall back to eligible shared resources;
- authorization and policies remain active.

Test boundary-sensitive behavior both through `solution start` and a deployed install. Read `solution-resource-access.md` when any shared resource is involved.

## Deploy

```bash
bifrost solution deploy
bifrost solution deploy --solution <install-id>
bifrost solution deploy --org "Customer Org"  # creates there when missing
bifrost solution deploy --global               # creates globally when missing
```

Deploy is a full replacement of managed definitions. A unique slug match is reused automatically. With no match, deploy requires an explicit org/global target, creates the install there, and then deploys; it never chooses the new scope implicitly. It preserves environment data according to each resource's contract, but removed managed entities are reconciled as deletions. Review the diff, captured/pulled state, policies, and production impact first.

For a sealed Solution (`allow_outbound_access: false`), deploy vendors imported instance `_repo` Python modules into the bundle. Runtime is self-contained, but the selected instance remains a build-time source. If the Solution should own and version a module, move it into local `modules/`; local source is bundled directly and is not vendored. With shared fallback enabled, deploy skips vendoring and resolves eligible `_repo` modules at runtime.

Live create/update commands against Solution-managed records return a deploy-ownership conflict. Update their local manifest content instead. Do not work around the guard by creating duplicate loose entities.

## One definition, many installs

Use one slug/repository for the same product installed in several organizations. Each install has its own ID, scope, entity rows, config values, and runtime data. A unique slug match is selected automatically; otherwise choose from the printed options with `--solution <id>`, or explicitly bind one for repeated work.

Fork to a new slug only when the product source genuinely diverges. If a slug is ambiguous on one instance, target the install ID.

`allow_outbound_access` is separate from install scope. It gates fallback to eligible shared modules, registered loose workflows, tables, and files. Configs, integrations/OAuth, and knowledge follow their own shared instance rules. Read `solution-resource-access.md` before enabling it.

## Package, install, and backup

```bash
bifrost solution export <solution-ref> --mode shareable --out dispatch.zip
bifrost solution install dispatch.zip --org "Customer Org"
```

Shareable exports contain portable source, manifests, schemas, declarations, and setup requirements—not secrets, table rows, or runtime file bytes.

Full exports are backups. Use a password for encrypted secrets; `--include-data` may include table rows and runtime files. Installing with `--replace-secrets` or `--replace-data` can overwrite environment state and requires explicit production review.

## Pre-deploy checklist

- Confirm the selected instance with `bifrost auth default` or `--url`, and confirm the resolved install shown by the command.
- Confirm every new workflow has a manifest row and portable references.
- Pull after every capture and review manifest identity/content changes.
- Run tests, app build/type checks, and connected preview.
- Verify app quality and both themes where declared.
- Review tables, policies, configs, integrations, file locations, and shared dependencies.
- Tell the user what deploy will replace or mutate and obtain approval before targeting production.
