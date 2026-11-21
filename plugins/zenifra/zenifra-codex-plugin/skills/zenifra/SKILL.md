---
name: zenifra
description: Use when the user wants to manage Zenifra projects, profiles, organizations, deployments, builds, authentication, or supported Git providers from Codex.
---

# Zenifra

Use the Zenifra CLI for product operations.

## Public repository boundary

This skill lives in a public repository and is limited to the public Zenifra CLI (npm package `@zenifra/cli`, command `zenifra`) and documented product concepts. Never commit or paste passwords, TOTP codes, API keys, access tokens, connection strings, customer data, private project identifiers, or unredacted command output. Never mention or expose private architecture, internal infrastructure, internal service names, operational runbooks, or development-tool details. Do not call private or undocumented API endpoints to compensate for a missing CLI command.

## Safe operation rules

- Treat read-only commands and mutating commands differently. Listing, plan catalogs, project info, URLs, logs, metrics, capabilities, builds, deployments, billing usage, database status and masked connections, Armazem status/buckets/file listings/usage, identity, profile inspection, Git-provider/connection/repository reads, and GitHub or Forgejo source settings reads are read-oriented; create, deploy, GitHub or Forgejo deployment settings, stop, resume, delete, image, exposure, environment, instance, autoscaling, credential rotation, logout with `--revoke`, and profile changes have side effects.
- Before a mutation, verify the exact profile, API base, organization, project, branch or commit, and intended values. Production mutations require explicit user scope; never infer them from a name such as `prod`.
- Use `--idempotency-key` for project creation and Key Value, Cache, or Queue credential rotation when a retry may happen. Retry only with the same key and only after inspecting the previous response; do not mask authentication, authorization, validation, setup, or cleanup failures with generic retries.
- After every external mutation, read back the final state. A successful request or an accepted asynchronous operation is not proof that the desired state was reached.
- When a requested capability is not exposed by the CLI, say so instead of inventing a command or using an undocumented endpoint. Project deletion is available as `zenifra project delete --project <project-id> --yes`; without `--yes`, the CLI does not send a removal request. Require explicit authorization and read the exact project first.

## Mutation workflow

Before any production mutation, make the target explicit:

1. Run `zenifra whoami --json` to inspect the effective profile, API base, authentication mode, and selected organization without displaying credentials. Use `zenifra profile show --json` when you also need saved profile metadata.
2. For a user-login profile, run `zenifra orgs --json` and select the organization with `zenifra org set --org <id>` or pass `--org <id>` for one command. An OAuth grant belongs to the account; it does not change organization membership.
3. Read the current plan catalog with `zenifra plans` and confirm the project type, plan, payment mode, storage, exposure, deploy source, port, instances, and initial environments. Check the current `capabilities.*` fields instead of inferring availability from price or descriptive features. In particular, use `capabilities.logs`, `capabilities.metrics`, and `capabilities.healthcheck` for those product capabilities. `--json` preserves the public catalog response for automation.
4. Use an idempotency key for project creation and Key Value, Cache, or Queue credential rotation. If a request times out, inspect the resulting project or operation before retrying with the same key.
5. After the mutation, read the project status. For HTTP projects, also read the URL and follow the build or deployment identifier until it reaches a terminal state. For Scheduled Jobs, follow the run history instead.

If the target uses another saved profile, select it with `zenifra profile list` and `zenifra profile use <name>`, then run `zenifra whoami --json` again. Do not pass `--profile` to operational commands unless that command's help explicitly supports it. Environment overrides can change the effective API or authentication; use `whoami` to check the effective target without printing credentials, and do not inspect local profile files.

Treat an HTTP project as ready only after the public URL, DNS/TLS, and the product health or OAuth behavior expected for that project have been checked. A Scheduled Job has no public URL: treat it as ready only after project information confirms the expected Job configuration and a scheduled run reaches a terminal state; read that run's logs when permission allows. A created project or successful API response alone is not readiness.

## Project lifecycle

- Stop a project with `zenifra project stop --project <project-id>` and resume it with `zenifra project resume --project <project-id>`. Both commands confirm the resulting state; read the project again when the final state matters to a later action.
- Delete a project only after an exact project read and an informed, target-specific confirmation. Immediately before deletion, tell the user exactly what will be deleted by showing the project name, project ID, project type, selected organization, and effective API base; include the public URL when one exists, and state that project deletion is destructive. Ask for an explicit and unambiguous affirmative response for that exact target. Earlier generic authorization does not count, even when the user previously allowed other mutations or deployments. Only after receiving this confirmation may you add `--yes` and run `zenifra project delete --project <project-id> --yes`. Without `--yes`, the CLI does not send a removal request. Verify the final absence or deleted state through the supported read behavior before reporting completion.
- If a lifecycle request times out or is interrupted, inspect the project before retrying. Do not assume either success or failure from the local timeout alone.

## GitHub deployment settings

Version-triggered GitHub deployment settings require a published `@zenifra/cli` version 0.4.0 or later. Installing the plugin does not install or update the CLI. Before using these commands, check `zenifra help project github` and use them only when the installed CLI exposes them.

Read a project's repository, branch, deployment mode, and version settings with `zenifra project github --project <project-id> [--json]`. Project creation still starts its initial build from the selected branch; the selected mode controls later repository events. Changing deployment settings changes which future events start builds, so first verify the effective API, selected organization, exact project, and repository. Use a mode and tag pattern the user already specified without asking for redundant confirmation; clarify only missing or ambiguous inputs. For production, require explicit user scope. Then read the settings again to verify the effective state.

The project wizard and `deploy-settings set` use the same four exclusive modes:

- `manual` disables automatic branch and version-triggered builds. The user can still request a manual deploy with `zenifra deploy --project <project-id> --branch <branch>`.
- `branch` enables builds for pushes to the project's configured branch and disables tag/release triggers.
- `tag` enables builds when a tag is created and its name matches the required `--tag-pattern`; branch and release triggers are disabled.
- `release` enables builds when a release is published and its tag matches the required `--tag-pattern`; branch and tag triggers are disabled. Prereleases are excluded by default. Use `--include-prereleases true` only when the user explicitly asks to deploy prereleases.

Read or set the mode with the public CLI:

```bash
zenifra project github --project <project-id> [--json]
zenifra project github deploy-settings set --project <project-id> --mode <manual|branch|tag|release> [--tag-pattern <pattern>] [--include-prereleases <true|false>] [--json]
```

`--tag-pattern` is required for `tag` and `release`, and is not accepted for `manual` or `branch`. It matches the tag name and supports an exact name or the `*` and `?` wildcards; it is not a regular expression and does not match a release title. `--include-prereleases` is accepted only for `release` and defaults to `false`. Treat including prereleases as a separate permission; a general request for release deployments does not authorize it. A configured trigger is not evidence that a later build or deployment succeeded. When a matching event occurs, follow the returned build through its terminal state and read the project back.

## Forgejo source deployments

For Forgejo connections, repositories, project sources, or deployment triggers, read [the Forgejo workflow](references/forgejo.md) before acting. The published end-user CLI requirement is `@zenifra/cli` 0.5.0 or later; installing this plugin does not install or update the CLI. Check the installed command help. An explicitly authorized development workspace may use its local CLI build when that help exposes the operation. Keep GitHub projects on the GitHub workflow above.

## Domains and MCP OAuth

The primary project URL and a custom domain are separate values. Do not add the primary URL again as a custom domain. After adding a custom domain, wait for DNS/TLS and read the project URL back before reporting success. For an MCP connection, verify the exact `/mcp` URL, protected-resource discovery, and the unauthenticated `401` bearer challenge; that `401` is expected before OAuth authorization.

The MCP server publishes raw tool names without a product prefix: `get_context`, `list_projects`, `get_project`, `get_project_metrics`, `list_builds`, `get_project_logs`, `get_build_logs`, `list_deployments`, `get_project_health`, `list_healthcheck_failures`, `get_project_network`, `get_project_autoscaling`, `list_autoscaling_events`, `list_project_instances`, `get_valkey_status`, `list_ai_keys`, `get_ai_usage`, `get_project_billing`, `list_transactions`, `get_object_storage`, `list_object_storage_buckets`, and `list_object_storage_objects`. A client may prepend its configured server name, so server `zenifra` plus raw tool `get_context` can appear as `zenifra_get_context`. Never add the server namespace to a tool name that already contains it.

For MCP reads, start with `get_context`, then use `list_projects` or `get_project` to confirm the project type and exact authorized ID. Choose tools that match that type: application logs, health checks, network analytics and their failures apply to HTTP projects; `get_valkey_status` applies to Key Value, Cache, and Queue projects. For Armazém, call `get_object_storage` first to get the service ID (it is `null` when the connection was not given access to it), then `list_object_storage_buckets`, then `list_object_storage_objects` one folder at a time, following `next_continuation_token`. These tools only read; uploads, downloads, deletions and access keys go through the CLI or the console. Use `list_project_instances` before passing an instance to metrics or logs, and use `list_builds` before requesting `get_build_logs` with a build ID. Continue build logs from `next_cursor`; stop when `finished` is true or no new chunks are returned. Use explicit time ranges and bounded pages. Empty lists, unavailable observations and null values must remain distinct from zero or success.

Use product-level recovery guidance:

- `401`: sign in again or reconnect the OAuth connection.
- `403`: confirm the selected organization and permissions.
- `404`: confirm the project ID, URL, path, and whether the operation is supported by the selected project type.
- `409`: inspect the existing resource and reuse the same idempotency key when retrying a known operation.
- `429`: wait for the indicated retry interval.
- `502`, DNS/TLS failure, or readiness timeout: inspect project status, build/deployment state, public URL, and logs before retrying.

Do not describe these situations using implementation details or expose raw provider responses.

## Authentication safety

- Prefer the interactive prompt for passwords, TOTP codes, and API keys. Never place passwords, TOTP codes, API keys, tokens, or connection strings in committed examples, shell history, logs, or assistant responses.
- `auth login` may require email, password, and a verification challenge. `--code` is available for automation only when the caller has already handled secret redaction and secure input.
- `auth api-key` validates the `znf_` prefix locally but does not prove that the key is active; verify the first authorized read operation without printing the key.
- Keep user-login tokens and organization API keys conceptually separate. API keys are organization-bound and do not need `org set`; user-login profiles may need `org set`.
- For tests, previews, or temporary validation, set `ZENIFRA_CONFIG_DIR` to a temporary directory so the user's normal profile store is not changed. Remove the temporary directory after verification.

## OAuth login and organization selection

Example hosts under `example.test` are placeholders. Resolve the actual API from the requested target or saved profile before running a command.

- `zenifra auth login --oauth` opens the browser for account sign-in, verification and consent. Without `--oauth`, the existing email/password flow remains available. Do not combine `--oauth` with password, verification-code or API-key flags.
- OAuth grants belong to the user account, not to one organization. They allow access only within the user's current permissions in each organization; consent does not add a role or bypass organization access checks.
- Read permission is required. Requested write permission is an explicit choice in consent; `--read-only` requests only read access. A read-only grant cannot create projects, deploy or change settings, even for an organization owner.
- `zenifra orgs` lists available organizations. `zenifra org set --org <id>` saves the selection in the active profile, so subsequent organization-scoped commands do not need repeated `--org` flags.
- With no selection, the CLI selects and saves the only available organization, or prompts for a choice when several exist. For unattended use, select the organization first or pass `--org <id>` on the command. An explicit `--org` overrides the saved selection only for that command.
- An OAuth login updates or creates the requested `--profile`, makes it active and clears that profile's previous organization selection. API-key profiles remain organization-bound and do not use this selection flow.

```bash
zenifra auth login --oauth --profile staging --api-base https://api.example.test/v1
zenifra orgs
zenifra org set --org <organization-id>
zenifra projects
zenifra create project
zenifra projects --org <another-organization-id>
```

- Without an explicit API base, the CLI uses its profile/override configuration and otherwise defaults to production. Use an explicit environment for tests; do not assume a profile name selects an API.
- `--no-browser` prints the authorization URL to open manually. The browser must run on the same machine as the CLI, or otherwise be able to reach that machine's temporary loopback callback. On a remote or headless server where the browser cannot reach that loopback address, use an organization API key or complete the login on a machine where the callback is reachable. The browser page acknowledges receipt; the terminal confirms that the login was completed and saved. `Ctrl+C` cancels the pending login.
- Tokens are stored in the private local profile and renewed automatically before expiry. Concurrent commands coordinate refresh; do not manually edit or expose tokens. If renewal is rejected, sign in again. Mutations are not automatically replayed.
- OAuth profiles are bound to their API. Changing `--api-base` or `ZENIFRA_API_URL` does not authorize forwarding that profile's token to another API; use another profile and login for that environment.
- `ZENIFRA_API_KEY` still takes precedence for a command and produces a warning when replacing an OAuth profile credential. Check this precedence when diagnosing unexpected authorization behavior without printing the key.
- `zenifra auth logout` is local-only by default and clears the profile authentication. For an OAuth profile, `zenifra auth logout --revoke` revokes only that profile's OAuth connection; it does not invalidate the user's other logins. Revocation is also available in the Console's connected integrations. A failed remote revocation preserves the local profile; do not remove it and claim cleanup succeeded.
- For a password-login profile, `auth logout --revoke` invalidates the user's server login sessions. API keys must be revoked through the organization. Distinguish these effects before choosing a logout mode.

## Database guidance

- Use `zenifra database` for every managed database: PostgreSQL, MariaDB, ClickHouse, Key Value, Cache, and Queue. Each command takes `--project <project-id>` and `--json`, reads the project type first, and picks the right flow; HTTP projects and Scheduled Jobs are refused because they are not databases.
- Read-oriented: `zenifra database status --project <project-id>` and `zenifra database connection --project <project-id>`. The connection is always masked.
- `zenifra database credentials rotate --project <project-id>` has side effects and breaks applications that still use the old credential. Require explicit authorization, and check which applications use the database before rotating.
  - PostgreSQL, MariaDB, and ClickHouse renew immediately and print the new password exactly once, together with each connected application's project ID and the variable names that must receive the new password. There is no operation to follow, and `database credentials status` explains that.
  - Key Value, Cache, and Queue return an asynchronous operation. Use `--wait`, or the returned operation identifier with `zenifra database credentials status --project <project-id> --operation <operation-id>`. Use `--idempotency-key` when a retry may happen.
- Prefer `--connection-file <path>` with a private destination the user chose. The CLI writes the connection with the new credential in a file with mode 600 and keeps it out of the output. It never stores the password in the profile or a log. Never paste the password or connection into chat, a report, a commit, or a public example.
- Key Value, Cache, and Queue connections: the file preserves the exact connection string returned by the backend. If a consuming client requires `rediss://` instead of the backend-returned scheme, adapt the value only in that client's private configuration, keeping the host, port, credentials, and parameters unchanged. Never alter the CLI output or the saved backend value.
- For Key Value, Cache, and Queue metrics, query `zenifra project metrics capabilities --project <project-id>` before requesting a snapshot when access is unknown. `availability: unavailable` with a null snapshot is a valid result while the first snapshot is not ready. Do not convert `null` or `unavailable` into zero and do not claim that a metric was collected.
- The snapshot's `memory.used_bytes` is the memory currently used by the database; `memory.limit_bytes` is its configured limit and may differ from the instance capacity.
- The legacy top-level `memory` value in the metrics response is current instance/container usage in bytes, not provisioned capacity. Do not label it as capacity unless the API exposes a dedicated capacity field.
- Profiles are `key_value`, `cache`, and `queue`. Cache adds hits, misses, and hit ratio; Key Value adds key inventory; Queue must not receive an invented queue-depth value. In the API, these three use `type_project: valkey`; `zenifra projects --type key-value|cache|queue` filters each profile; in the plans catalog Key Value is part of `zenifra plans --type database`, and Cache and Queue have `zenifra plans --type cache` and `--type queue`.

## Scheduled Jobs guidance

- Read only the Jobs catalog with `zenifra plans --type jobs [--json]`. Job plan IDs use the `job-` prefix, `payment_mode` is `per_minute`, and JSON monetary values such as `price_per_minute`, run `amount`, and cycle `total_amount` are expressed in BRL cents and may be fractional. Preserve those JSON values; human-readable cost and minute displays may use up to six decimal places for the per-minute price and up to four for amounts and totals. The catalog is the source of the current rate, so do not hard-code prices. An explicit `--type jobs` request must report that Scheduled Jobs is unavailable; the API response uses code `SCHEDULED_JOBS_UNAVAILABLE`. Do not substitute another catalog.
- The CLI V1 creates Scheduled Jobs from a ready OCI image. Confirm the `job-*` plan, `per_minute` billing, image reference and access, five-field UTC cron, storage, and initial environment variables. Jobs do not use a public URL, port, exposure, or instances. The CLI V1 accepts only `config.image` and does not support `config.github`, `job.command`, or `job.args`; use the documented advanced API for GitHub sources or explicit commands/arguments.
- Use `zenifra create project --name <name> --plan <job-plan> --payment-mode per_minute --config @<job-config.json> --idempotency-key <key>` or the interactive wizard. A Job config uses `type_project: job`, an OCI `image`, `job.cron`, `storage`, and a required `envs` array. Use `envs: []` when there are no variables or an array of `{name, value}` objects; do not omit `envs`.
- `billed_minutes` rounds duration up with a minimum of 1 and a maximum of 60. A terminal amount is `billed_minutes × price_per_minute`, stored exactly and never rounded up (a R$0.0005 run is stored as `amount: 0.05`), and persisted with the rate in effect. Duration runs from the container's real start to its finish, so scheduling and image download time are not charged; the cycle summary adds those persisted amounts and does not recalculate them from the current catalog.
- List the current billing-cycle runs with `zenifra project runs --project <project-id> [--page <n>] [--limit <n>] [--json]`. The public runs, logs, metrics, total cost, run count, and billed minutes reset on the scheduled cycle date independently of financial settlement. Read run logs with `project.logs.read` and run metrics with `project.metrics.read`. If the catalog or response says a capability is unavailable, treat it as unavailable and do not invent a route; when an existing route returns `403`, the capability exists but the principal lacks the matching permission. A run that crosses the boundary stays in the cycle where it started; older run and metric records remain retained internally, while persisted financial records remain available for audit and are not deleted by the public cycle reset. Follow pagination and preserve unknown duration, billed minutes, or amount as unknown rather than zero. After terminal usage is materialized, terminal cost is visible before financial settlement.
- The API-only `GET /v1/project/:id/job-runs/cost-summary` with `project.billing.read` returns `total_amount`, `executed_runs`, `billed_minutes`, `cycle_started_at`, and `next_reset_at`; the CLI has no equivalent cost-summary command.
- Read one run's logs with `zenifra project runs logs --project <project-id> --run <run-id> [--json]`. Cancel an active run only with explicit authorization and the `project.job-run.cancel` permission by using `zenifra project runs cancel --project <project-id> --run <run-id> [--json]`; cancellation allows up to 30 seconds for graceful shutdown before forced cleanup.
- Exit code `0` means success; any non-zero code, including `1`, means failure. There is no automatic retry and no parallel run when an occurrence overlaps an active run. The CLI does not expose a cost-summary or schedule-update command; say so and use only the documented API/Console instead of inventing one or calling an undocumented endpoint.

## Armazem (object storage) guidance

- Use `zenifra storage` (alias `zenifra armazem`) when the user wants buckets, files, access keys, or object storage usage for the organization. The Armazem uses an industry-standard object storage API: endpoint `https://armazem.zenifra.com`, region `br-sp1`. Each organization has one Armazem.
- The Armazem is a beta for invited organizations. Start with `zenifra storage status [--json]`. If it is not available yet, say so and point the user to the console's Armazem page to ask to join the beta; do not try to work around it. If it is available but not created, `zenifra storage create [--name <name>]` creates it.
- Read-oriented: `storage status`, `storage buckets`, `storage files --bucket <name> [--prefix <folder/>] [--continuation-token <token>]`, `storage files info --bucket <name> --key <key>`, `storage keys`, and `storage usage [--month YYYY-MM]`. `storage files` lists one folder level per call; follow the returned `next_continuation_token` and do not claim one page is the whole bucket.
- With side effects: `storage buckets create --bucket <name>`, `storage buckets delete --bucket <name> --yes`, `storage files upload --bucket <name> --file <path> [--key <key>]`, `storage files download --bucket <name> --key <key> [--output <path>]` (writes a local file and refuses to overwrite without `--yes`), `storage files delete --bucket <name> --key <key> --yes`, `storage files share --bucket <name> --key <key>`, `storage keys create --name <name> [--buckets <a,b|*>] [--access <read|read_write|full>] [--allowed-ips <ip,cidr>]`, and `storage keys revoke --access-key <id> --yes`. Confirm the bucket, key, and intended effect before each one.
- Uploads and downloads go straight to the Armazem through signed links and stream from disk; files can have up to 20 GiB. A share link lets anyone with it download the file for 7 days, so create one only when the user asks.
- `storage buckets delete` removes only an empty bucket. A bucket with files can be removed only in the console, with a verification code; the CLI explains this and sends nothing else. Do not delete files one by one to empty a bucket unless the user explicitly asks for that.
- `storage keys create` shows the secret access key exactly once. Tell the user to store it in a secret manager right away; never paste it into chat, a report, a commit, or a file the user did not choose. Prefer the narrowest `--buckets`, `--access`, and `--allowed-ips` that fit the request; without `--buckets`, the key reaches every bucket with `full` access.
- `storage usage` shows the current month or one of the previous 12 in BRL; `--json` values are in cents and include the free allowance already used.

## Output and asynchronous operations

- Human output is for direct inspection. `--json` preserves the public response for ordinary commands; do not parse table columns as an API contract.
- `deploy watch --json` emits one JSON object per line while streaming build events, not one final JSON document. `builds logs --follow` similarly streams incremental output.
- Build log entries expose their source. `event` identifies a detailed build event; `summary` is the terminal summary fallback for older builds and may contain only one line. Preserve that distinction and do not report a summary as missing logs or invent unavailable build steps.
- Project creation, deployment, and credential rotation may be asynchronous. Capture the returned identifier, poll with the supported command, and report the terminal state or the actual blocker.
- Environment values and credentials are masked by default. Never use `--show-values` unless the user explicitly requires it, and never include the revealed value in a report.

## Error handling and pagination

- Distinguish authentication failures, authorization failures, validation failures, plan restrictions, rate limits, network timeouts, and asynchronous operation failures. Report the actual category and next supported action.
- A `401` means the credential or session needs attention; a `403` means the authenticated principal lacks permission; a metrics plan restriction must not be treated as a transient network error; a `429` may include a retry interval.
- Projects, builds, deployments, autoscaling events, and billing usage are paginated. Use the returned pagination fields and do not claim that one page is the complete result.
- For deploys where the exact revision matters, pass `--commit-sha` and preserve the supplied identifier literally. Verify the resulting build's commit before claiming that the intended revision was published.

## Command

Prefer the public CLI command when it is installed:

```bash
zenifra <command>
```

Inside this workspace, use the local CLI project as fallback:

```bash
node zenifra-cli/bin/zenifra.mjs <command>
```

## Common Workflows

- Command-specific help: `zenifra help <command>` or `zenifra <command> --help`
- Command group help: `zenifra auth`, `zenifra profile`, `zenifra project`, `zenifra org`
- Inspect effective identity and target without credentials: `zenifra whoami --json`
- Browser login on the active profile: `zenifra auth login --oauth`
- Password login on the active profile: `zenifra auth login`
- Browser login on an explicit environment/profile: `zenifra auth login --oauth --profile staging --api-base https://api.example.test/v1`
- Save an org API key on the active profile: `zenifra auth api-key` and enter it at the hidden prompt.
- Save an org API key on another profile: `zenifra auth api-key --profile prod` and enter it at the hidden prompt.
- Clear only local auth from a profile: `zenifra auth logout [--profile <name>]`
- Revoke the OAuth connection (OAuth profile) or server login sessions (password profile), then clear local auth: `zenifra auth logout [--profile <name>] --revoke`
- List profiles: `zenifra profile list`
- Show a profile: `zenifra profile show [name]`
- Add an API-key profile: `zenifra profile add --name staging --description Homologacao --api-base https://api.example.test/v1 --mode api-key` and enter the key at the hidden prompt.
- Switch the active profile: `zenifra profile use staging`
- Edit a profile: `zenifra profile edit staging --description "Homologacao interna"`
- Remove a non-active profile: `zenifra profile remove staging`
- Select organization for a user-login profile: `zenifra org set`
- Compare public plan prices: `zenifra plans`, then filter with the same groups as the console: `--type http`, `--type database` (PostgreSQL, MariaDB and Key Value), `--type analytics`, `--type jobs`, `--type queue`, `--type cache` or `--type storage`, each with `--json` when needed
- List projects: `zenifra projects --type http --page 1 --limit 15`
- Create a project from flags: `zenifra create project --name <name> --plan free --payment-mode hourly --config @project.json`
- Run the interactive project wizard: `zenifra create project`
- Read hourly consumption and compute/storage costs: `zenifra project billing usage --project <project-id> [--from <ISO>] [--to <ISO>] [--page <n>] [--limit <n>] [--json]`
- Read database status and masked connection data: `zenifra database status --project <project-id>` and `zenifra database connection --project <project-id>`
- Rotate a database credential: `zenifra database credentials rotate --project <project-id> [--connection-file <path>]`; for Key Value, Cache, and Queue, follow with `--wait` or `zenifra database credentials status --project <project-id> --operation <operation-id>`
- List Scheduled Job runs: `zenifra project runs --project <project-id> [--page <n>] [--limit <n>] [--json]`
- Read Scheduled Job run logs: `zenifra project runs logs --project <project-id> --run <run-id> [--json]`
- Cancel an authorized active Scheduled Job run: `zenifra project runs cancel --project <project-id> --run <run-id> [--json]`
- Get project info or URL: `zenifra project info --project <project-id>` or `zenifra project url --project <project-id>`
- Stop or resume a project: `zenifra project stop --project <project-id>` and `zenifra project resume --project <project-id>`
- Delete an explicitly authorized project: `zenifra project delete --project <project-id> --yes`
- Read runtime logs: `zenifra project logs --project <project-id> [--instance <instance-id>]`
- Read GitHub build logs: `zenifra builds logs --project <project-id> --build <build-id> [--follow]`
- Read CPU, memory, and network metrics: `zenifra project metrics --project <project-id> [--instance <instance-id>]`
- Read network analytics: `zenifra project network --project <project-id> --view summary`
- Manage HTTP autoscaling: `zenifra project autoscaling --project <project-id>`, `zenifra project autoscaling set --project <project-id> --min <n> --max <n>`, and `zenifra project autoscaling disable --project <project-id>`
- Read HTTP autoscaling history: `zenifra project autoscaling events --project <project-id> [--direction <scale_up|scale_down>] [--page <n>] [--limit <n>]`
- Update a project image: `zenifra project image set --project <project-id> --image <image>`
- Manage envs: `zenifra project envs --project <project-id>`, `zenifra project env add/update/remove --project <project-id> --name <name>`
- Manage instances: `zenifra project instances --project <project-id>` and `zenifra project instances set --project <project-id> --count <n>`
- Read GitHub repository and deployment settings: `zenifra project github --project <project-id> [--json]`
- Configure GitHub deployment triggers: `zenifra project github deploy-settings set --project <project-id> --mode <manual|branch|tag|release> [--tag-pattern <pattern>] [--include-prereleases <true|false>] [--json]`
- Trigger GitHub deploy and receive a `build_id`: `zenifra deploy --project <project-id> --branch main`
- Watch that build with live logs: `zenifra deploy watch --project <project-id> --build <build-id>`
- For Forgejo source setup, project creation, and triggers, use [the Forgejo workflow](references/forgejo.md); do not apply GitHub commands to a Forgejo project.
- List builds: `zenifra builds --project <project-id>`
- List deployments/builds: `zenifra deployments --project <project-id>`. OCI-created projects include their initial deployment history.

## Create Examples

- HTTP via OCI: `zenifra create project --name app-http-oci --plan free --payment-mode hourly --config @examples/http-project.json`
- HTTP via GitHub: `zenifra create project --name app-http-github --plan basic --payment-mode hourly --config @examples/http-github-project.json`
- PostgreSQL: `zenifra create project --name app-postgres --plan db-basic --payment-mode monthly --config @examples/postgresql-project.json`
- MariaDB: `zenifra create project --name app-mariadb --plan db-basic --payment-mode monthly --config @examples/mariadb-project.json`
- HTTP with autoscaling: `zenifra create project --name app-http-autoscaling --plan premium --payment-mode hourly --config @examples/http-autoscaling-project.json`
- Scheduled Job from a ready OCI image: `zenifra create project --name nightly-report --plan job-basic --payment-mode per_minute --config @job-config.json --idempotency-key <key>`
- When the user prefers prompts instead of JSON, run `zenifra create project` and use the wizard.
- Treat these examples as starting points, not as permission to assume production values.

## Before Creating Projects

- Project creation can generate cost for the customer. Do not guess values that affect billing or infrastructure shape.
- Before suggesting a plan or comparing cost, prefer running `zenifra plans` so the user sees the current HTTP, database, and storage catalogs. Use the current `capabilities.*` fields to decide whether a plan includes logs, metrics, health checks, autoscaling, or another advertised capability. The `db-free` plan supports PostgreSQL and Key Value, not MariaDB.
- Before running `zenifra create project`, confirm the minimum required inputs with the user.
- Always confirm:
  - `type_project`
  - `plan`
  - `payment_mode`
  - storage strategy and capacity
  - initial envs
- For HTTP projects, also confirm the deploy strategy:
  - OCI or image URL flow
  - GitHub flow
  - Forgejo flow described in [references/forgejo.md](references/forgejo.md)
  - exposure: `public` creates route/domain, `private` keeps the app without internet exposure
- For HTTP via OCI, confirm at least:
  - image URL
  - whether the image is public or needs authentication
  - exposure
  - port
  - instances
  - storage
  - envs
- If HTTP autoscaling is requested during creation, also confirm:
  - `config.instances` as the initial minimum instance count
  - `config.autoscaling.max_instances` as a value greater than or equal to `config.instances`
  - `config.autoscaling.target_cpu_utilization_percent` and `config.autoscaling.target_memory_utilization_percent` when provided, each between 1 and 100
  - that the selected paid HTTP plan permits autoscaling
- For HTTP via GitHub, confirm at least:
  - repository owner
  - repository name
  - branch
  - one deployment mode: `manual`, `branch`, `tag`, or `release`
  - a tag pattern for `tag` or `release`
  - whether to include prereleases when using `release` (default: no; enabling them needs an explicit user request)
  - runtime
  - runtime version
  - start/build commands when applicable
  - exposure
  - port
  - instances
  - storage
  - envs
- For PostgreSQL, confirm at least:
  - plan
  - version
  - instances/replicas
  - storage
- For MariaDB, confirm at least:
  - plan
  - version
  - storage
- For Scheduled Jobs, confirm at least:
  - a `job-*` plan and `per_minute` billing
  - a ready OCI image and whether it requires authentication
  - a five-field cron expression interpreted in UTC
  - storage and initial envs
  - that no public URL, port, exposure, or instances are expected
- If the agent is not confident about plan choice, deploy strategy, storage, envs, or any other create-time field that can affect cost or production behavior, ask the user before creating the project.
- If the user has not explicitly confirmed those inputs, prefer asking over inferring.

## Behavior

- The CLI stores profile data under `~/.config/zenifra-cli/profiles.json`.
- If an old `session.json` exists and `profiles.json` does not, the CLI migrates it automatically into the `default` profile and removes the legacy file.
- The active profile is the local source of truth for `apiBaseUrl`, description, and saved credential.
- `zenifra whoami --json` resolves command overrides and profile state to show the effective profile, API base, authentication mode, and selected organization without exposing credentials.
- Profile credentials can be an organization API key, password-login token or OAuth session with automatic renewal. `selectedOrganizationId` applies to password-login and OAuth profiles.
- `ZENIFRA_API_KEY` overrides the active profile credential for the current command only.
- `ZENIFRA_API_URL` overrides the active profile API base for the current command only.
- `ZENIFRA_HTTP_TIMEOUT_MS` configures the per-request HTTP timeout in milliseconds; the default is 300000 (five minutes). A timeout does not prove that project creation failed: check the resulting state before repeating with the same idempotency key.
- The CLI sends `Authorization: Bearer <token>` and `x-organization-id` only when needed.
- Logout and remote revocation depend on the profile authentication mode; follow the OAuth login section above.
- `zenifra plans` is a public read-only command and works without authentication.
- Human plan output includes advertised capabilities; `zenifra plans --json` preserves the public catalog contract, including `capabilities.*` fields.
- `zenifra projects` is paginated; default to `--page 1 --limit 15` and request additional pages only when needed.
- Prefer `--json` when another tool or script will consume the result.
- `zenifra deploy` returns a `build_id`; use it with `zenifra deploy watch --project <project-id> --build <build-id>` to follow the build until completion.
- `zenifra project logs` is for runtime logs. `zenifra builds logs` is for GitHub build logs.
- Build log `source: "event"` entries are detailed events; `source: "summary"` is a legacy terminal fallback and may be a single line.
- Scheduled Job logs belong to a public run ID and use `zenifra project runs logs`; do not use `project logs` or build-log commands for them.
- `zenifra deploy watch` now streams incremental build logs until the build reaches a terminal status.
- OCI project creation records an initial deployment, so use `zenifra deployments --project <project-id>` to inspect its initial deployment history as well as later deployments.
- When a required argument is missing in commands like `zenifra deploy`, `zenifra deploy watch`, `zenifra builds`, or common `project` subcommands, the CLI now prints the command-specific help instead of only a terse validation error.
- `zenifra projects create` was removed; if you see it in old notes, use `zenifra create project` instead.
- Running `zenifra create project` without flags opens the interactive wizard.
- `create project` does not assume silent defaults for `plan` or `payment_mode`.
- Non-interactive HTTP project configs must include `exposure`; use `private` when the user wants automation, workers, internal routines, or anything that should not receive a public domain.
- `examples/http-project.json` is the HTTP OCI example, `examples/http-github-project.json` is the HTTP GitHub example, and the database examples match the current CLI contract.
- Human success output for `create project` is a `Campo | Valor` table, and the displayed domain is normalized to a full `https://...` URL.
- Env values are masked by default, including with `--json`; use `--show-values` only when the full value is required.
- For unanswered product questions, consult `https://docs.zenifra.com/llms.txt`.
- `config.autoscaling` is accepted only for paid HTTP projects. It must use `enabled: true`; free plans and non-HTTP projects must be rejected before the API call.
- The interactive wizard offers autoscaling only when the selected plan reports `permissions.allow_autoscaling === "true"`.
- `zenifra project billing usage` is read-only and returns hourly compute and storage consumption; use `--from`, `--to`, `--page`, and `--limit` for bounded queries and `--json` for automation.
