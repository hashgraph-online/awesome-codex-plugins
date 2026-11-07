# Solution Runtime Resource Access

Read this reference when Solution code needs anything outside its install.

Two install-local gates control cross-boundary access. Outbound,
`allow_outbound_access` (formerly `global_repo_access`, still accepted), lets an
install fall back to shared `_repo` resources. Inbound,
`allow_inbound_access` (default on), lets outside callers target this install
per-call (see below). Both off is deterministic isolation. Neither is install
scope, and neither grants blanket access to global resources. Outbound gates
shared fallback for resource types that also have a Solution-owned tier:
`_repo` modules, registered loose workflows, tables, and managed files.

Config values, integrations/OAuth, and knowledge are shared instance resources with their own org/global resolution regardless of this flag. Normal authentication, organization, role, policy, and external-user checks always remain active.

## Runtime matrix

| Resource | `allow_outbound_access: false` | `allow_outbound_access: true` | Write boundary |
|---|---|---|---|
| Python modules | Install source only | Install source, then eligible instance `_repo` module | Code changes through its owning source/deploy or direct `_repo` file write |
| Workflows | Own install only | Own install, then eligible registered loose install-org/global workflow | Each workflow executes as its own record/owner |
| Tables | Own Solution table only | Own table, then loose install-org/global table by name | Shared fallback table is read-only from Solution context |
| Managed files | Own declared location only | Own tier, then eligible install-org/global reads in the declared location | Writes/deletes target the Solution-owned tier |
| Config/secrets | Shared org/global cascade | Same | Mutations change shared environment state |
| Integrations/OAuth | Shared org mapping/defaults | Same | Mapping/token changes affect shared environment state |
| Knowledge | Shared org/global namespace | Same | No private Solution tier |

For an org install, eligible shared fallback searches the install org and then global. It does not search sibling Solutions or arbitrary organizations.

Forms, agents, apps, event sources, and claims are installed entities, not general shared SDK lookups. Never infer access to them from this flag.

## How context is carried

A deployed app's scaffolded provider sends its app identity on workflow, table, and file requests. The server resolves that app to its active Solution install. A Solution workflow carries its `solution_id` in execution context. Local `solution start` supplies equivalent install context through its proxy.

Do not hand-build app/Solution headers or mix an app identity with a different explicit Solution. Mismatches are rejected.

## Inbound targeting (per-call `solution=`)

To reach another install from your own code, pass `solution=` to the scoped
operation: `workflows.execute`, `tables.query`, `tables.get`, `tables.insert`,
`files.read`, and `events.emit`. The value is an install UUID or slug.

- The ref resolves **inside the already-resolved org scope** (the same `scope=`
  rules and org/role checks apply). A slug belonging to another org reads as
  not-found.
- Unset keeps the default: your own install, then eligible shared fallback.
- The **target's** `allow_inbound_access` decides. Own-install calls (caller ==
  target) always pass. A sealed target reads as not-found, so a denied target
  never falls through to a loose same-path workflow.
- `workflows.execute(solution=...)` starts the child run **as that install**, so
  the child's default SDK calls inherit the target's install context.
- The caller's own install comes from the signed engine claim, never from a
  request field you send. An explicit `solution=` also suppresses table
  auto-create.
- Targeting is resolution plus install context, not a delegated user identity.
  Authorization still runs as the target: its policies, roles, and org
  boundaries decide each read/write. If the target workflow gates on an
  authenticated actor (`context.user_id`, `context.org_id`), verify what the child
  run actually receives instead of assuming it inherits your caller.

Set the gate at create time (`bifrost solution create --allow-inbound-access` /
`--no-allow-inbound-access`), at install time via `allow_inbound_access` in
`bifrost.solution.yaml`, or after install with
`bifrost solution update --allow-inbound-access` / `--no-allow-inbound-access`.

## Modules and workflows

Module imports resolve install-owned source first. A sealed Solution stops there. An open Solution may import eligible `_repo` modules.

Workflow resolution follows this order:

1. Resolve a matching workflow owned by the caller's install.
2. If shared fallback is disabled, stop.
3. Resolve an eligible registered loose workflow in the install org, then global.

Use portable `path::function` refs. Without an explicit per-call target, a caller resolves only its own install's workflow (or loose shared fallback) — never a sibling Solution's, including by UUID. To target another install, pass `solution=` (install UUID or slug) alongside `scope=` on SDK calls such as `workflows.execute`, `tables.query`, `files.read`, and `events.emit`; the solution ref resolves inside the already-resolved org scope, so org/role checks apply unchanged. The target's `allow_inbound_access` decides: sealed installs answer only their own install's calls, and everything else reads as not-found.

When an open Solution invokes a loose workflow, it executes as that loose row (`solution_id` remains absent). Its imports and SDK calls use loose org/global context, not borrowed Solution ownership. Treat this as a trust boundary and permission the loose workflow explicitly.

## Tables

The install's own table name wins. With shared fallback enabled, a miss may resolve a loose install-org/global table by name. External table UUIDs stay hidden from Solution lookup.

Shared fallback tables are read-only from the Solution. Policies filter/deny rows after the table resolves. Python query behavior can translate some missing-table reads into an empty `DocumentList`; verify setup explicitly when absence matters.

## Managed files

The location must be declared in `.bifrost/files.yaml`; `workspace` is not a Solution runtime location.

With fallback enabled, read/list/exists and supported signed-read operations may search the Solution tier, then eligible install-org/global tiers. File policies apply at each tier. Writes and deletes always target Solution-owned storage and do not modify a shared fallback file.

Read `files.md` for the application/file-operation contract.

## Configs and integrations

Solution manifests declare config/integration requirements, not isolated values or credentials.

`config.get()` uses the instance's org/global config cascade. `config.set()` and `config.delete()` can mutate that shared namespace when authorized. An install setup check may require an org-specific value even when runtime lookup finds a global fallback; inspect both tiers when status and runtime disagree.

`integrations.get()` resolves the caller's org mapping and integration/global defaults. Keep it server-side. Mapping changes, OAuth flow, and token/config replacement change shared environment state.

## Knowledge

Knowledge is an org/global namespace with its own access rules. Installing a Solution does not create a private knowledge tier and neither access flag seals or opens it.

## Local preview

`bifrost solution start` runs local app/workflow source while proxying resource access to the selected live instance:

- local workflow refs execute transiently first;
- a missing local ref can fall back upstream only when shared fallback allows it;
- table/file/config/integration/knowledge reads and writes are real;
- policies and org/role boundaries remain active.

Validate boundary-sensitive behavior against both local preview and a deployed install. They should agree about fallback eligibility even though local workflow execution is transient and deployed execution is durable.

## Portability and security checklist

- Prefer install-owned resources when the Solution should work elsewhere without manual dependencies.
- Document every required loose module, registered workflow, shared table/file, config key, integration mapping, and knowledge namespace.
- Keep secrets behind workflows.
- Test an allowed and denied viewer, not only a platform admin.
- Verify shared tables are not mutated and shared files are not overwritten from Solution context.
- Report shared environment writes and reduced self-containment before deploy.
