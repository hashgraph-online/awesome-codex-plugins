# Cloudflare Workers

Target guide for Cloudflare, covering Workers with Static Assets, Workers Builds, and Workers Containers. Read it after `rules/target-detection.md` routes here. Pages appears only as a migration source: Cloudflare tells new projects to start on Workers, so this guide never sets up a new Pages project.

## Contents

- Canonical Configuration
- Authentication
- Identify And Deploy
- Success Test
- Status And Logs
- Change Settings
- Rollback
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

Start new projects on Workers with Static Assets, not Pages. The Pages product page says Workers "supports most Pages use cases and offers a broader feature set" and asks you to start new projects with Workers; Pages is not deprecated, so an existing Pages project keeps running until it is migrated.

| File found | Path | Command |
|---|---|---|
| `wrangler.jsonc` | Wrangler, recommended for new projects | project-local `wrangler` |
| `wrangler.json` / `wrangler.toml` | Wrangler, supported | project-local `wrangler` |
| `cloudflare.config.ts` | `cf` CLI, open beta | `cf`, never Wrangler |

`cloudflare.config.ts` belongs to the `cf` CLI, which is in open beta. That path needs Node.js 22.18 or newer, requires `"type": "module"`, and does not run on Bun. Do not add Wrangler to that project: Wrangler and `cf` load configuration under different rules, and adding Wrangler starts a second, conflicting toolchain.

For a Wrangler project the minimum is `name`, `main`, and `compatibility_date`. An assets-only Worker may omit `main`, and must then omit `assets.binding`. Names allow letters, digits, and hyphens only, no underscore, at most 255 characters, and 63 characters when the Worker gets a `workers.dev` hostname.

| Purpose | Keys |
|---|---|
| Entry point | `main` |
| Runtime | `compatibility_date` (`yyyy-mm-dd`), `compatibility_flags` (`["nodejs_compat"]`) |
| Static assets | `assets.directory`, `assets.binding`, `assets.not_found_handling` (`single-page-application`, `404-page`, `none`), `assets.run_worker_first` (bool or up to 100 patterns) |
| Routing | `routes[]` (`pattern`, `zone_name`, `custom_domain`), `workers_dev`, `preview_urls` |
| Environments | `env.<name>` |
| Plain values | `vars`, `define` (build-time substitution) |
| Secret check | `secrets.required` |
| Observability | `observability.enabled`, `observability.head_sampling_rate`, `observability.logs.invocation_logs` |
| Storage bindings | `kv_namespaces`, `r2_buckets`, `d1_databases`, `queues`, `services`, `hyperdrive` |
| Execution | `limits.cpu_ms` (default 30000, max 300000), `upload_source_maps` |
| Containers | `containers[]`, `durable_objects.bindings`, `exports.<Class>` |

`assets.not_found_handling` defaults to `none`, so a single-page app that relied on Pages matching behaviour returns 404 on a deep link until the key is set explicitly.

Environments do not inherit bindings or `vars`. `env.staging` must declare its own `kv_namespaces`, `d1_databases`, and `vars`; only a subset of scalar settings is inherited. A deploy that "succeeds" into a staging environment and then reads `undefined` from `env.DB` is this omission, not a runtime fault.

A binding without its ID (or an R2 bucket without `bucket_name`) makes Wrangler create the resource and write the new ID back into the configuration file. Read the configuration and list existing resources before deploying; an accidental deploy can add billable objects to the account.

`vars` in the configuration overwrite values edited in the dashboard on the next deploy. Set `keep_vars: true` (or `--keep-vars`) to keep the dashboard values, and treat the file as the source of truth otherwise. Deployments never delete secrets.

Next.js: the framework guide recommends `vinext` (a Vite plugin, still beta) for new applications, through `npx vinext check`, `npx vinext init`, then `npx @vinext/cloudflare deploy`. The OpenNext adapter (`@opennextjs/cloudflare`) is now the path for maintaining an existing application. Running `wrangler deploy` with no configuration file auto-detects the framework and may rewrite a Next.js project onto `vinext` interactively, so never use that path in a non-interactive run.

| Pages concept | Workers equivalent |
|---|---|
| `pages_build_output_dir` | `assets.directory` |
| Automatic SPA and 404 detection | Explicit `assets.not_found_handling` |
| Functions run before static assets | Assets served first; set `assets.run_worker_first` |
| `_worker.js` advanced mode | `main`, plus `.assetsignore` for `_worker.js` |
| `functions/` file routing | `wrangler pages functions build --outdir=./dist/worker/` |
| `_routes.json`, middleware | `assets.run_worker_first` patterns |
| Auto-excluded `node_modules`, `.git`, `.DS_Store` | Written into `.assetsignore` by hand |

Static asset limits are 20,000 files on Free and 100,000 on Paid, 25 MiB per file.

## Authentication

Set both variables; a token alone leaves Wrangler guessing the account:

```sh
[ -n "${CLOUDFLARE_API_TOKEN:-}" ] && echo token-set
[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] && echo account-set
npx --no-install wrangler whoami --json
```

`CLOUDFLARE_API_TOKEN` takes precedence over `CLOUDFLARE_API_KEY` with `CLOUDFLARE_EMAIL`, and over an OAuth login. `wrangler whoami` exits non-zero when unauthenticated, so it is the one check to run before any writing command. Build the token from the "Edit Cloudflare Workers" template and scope it to the account and zone the deploy needs; `wrangler login` OAuth cannot be narrowed that way.

Never use `--temporary` for a real deploy. It publishes to a temporary account and issues a claim URL valid for 60 minutes, after which the deployment is gone; it exists for a first demo without an account.

Never pass a token on the command line, print it, or copy it into the report. Check presence with a test that prints nothing.

## Identify And Deploy

Run the project-local binary (`npx --no-install wrangler`, or the `wrangler` in `node_modules/.bin`) and read its `--help`; do not fall back to a global install. State the Worker name, the environment, and the config file before deploying.

```sh
npx --no-install wrangler deploy --env staging --strict --dry-run
npx --no-install wrangler deploy --env staging --strict
```

- `--dry-run` compiles and validates without uploading. Add `--outdir` to read the bundle size.
- `--strict` prevents a deploy that would override remote settings in a non-interactive environment. Keep it on for every agent-run deploy.
- `--env <name>` selects `env.<name>`. In a Vite-plugin project the environment is chosen at build time with `CLOUDFLARE_ENV`, because `--env` at deploy time cannot change an already flattened configuration.
- `WRANGLER_OUTPUT_FILE_PATH=<file>` writes newline-delimited JSON events (`wrangler-session`, `deploy`, `version-upload`, `command-failed`) with `version_id` and target URLs. Parse that file instead of matching success text.

`wrangler deploy` creates a version and moves 100% of traffic to it at once. To separate upload from release:

```sh
npx --no-install wrangler versions upload --tag "$GIT_SHA" --message "$MSG"
npx --no-install wrangler versions deploy <NEW_ID>@10% <OLD_ID>@90% -y
npx --no-install wrangler versions deploy <NEW_ID>@100% -y
```

The first deployment of a Worker must be `wrangler deploy`: `versions upload` fails when no version exists yet. It also cannot carry a Durable Object class lifecycle change or Service Worker syntax. During a gradual deploy the same user can reach different versions across consecutive requests, so a 10% step passing does not make the new version correct.

With Containers, `wrangler deploy` activates the new Worker first and then builds, pushes, and rolls out the image. These steps are not transactional: an image or rollout failure can land after the Worker is already live.

## Success Test

Success is the active version being this run's version, plus an HTTP response and a quiet error log.

```sh
npx --no-install wrangler deployments status --json
npx --no-install wrangler versions list --json
curl -sS -o /dev/null -w '%{http_code}\n' https://<route>/
npx --no-install wrangler tail --format json --status error --version-id <ID>
```

- `deployments status --json` names the active version and the percentage of traffic it holds. That version ID must equal the one this run produced. An exit code of `0` from `deploy` alone proves nothing.
- `wrangler tail` runs until interrupted. Bound it: run it with a timeout or a line count, capture a 30–60 second window, and require `outcome` of `ok` with an empty `exceptions` array. At most ten clients can tail one Worker, and a busy Worker samples.
- HTTP: a 200 on the route, with the expected body or cache headers. For a static-asset app also request a deep link, which is where `not_found_handling` shows up.

Containers add a second terminal state. Deploy success means only that the rollout started:

```sh
npx --no-install wrangler containers instances <APP_ID> --json
```

Every instance of this run's version must be `running` and the previous version's instances gone. On a first deploy the image still provisions for several minutes, during which the Worker URL answers but container routes fail.

## Status And Logs

| Question | Command |
|---|---|
| Which version and percentage is live | `wrangler deployments status --json` |
| What versions exist | `wrangler versions list --json`, `wrangler versions view <ID> --json` |
| Machine-readable deploy result | `WRANGLER_OUTPUT_FILE_PATH` ND-JSON |
| Live runtime logs | `wrangler tail --format json --status error --search "<text>" --version-id <ID>` |
| Stored runtime logs | Workers Logs in the dashboard, or the Cloudflare API; needs `observability.enabled` |
| Container instances | `wrangler containers instances <APP_ID> --json`, `wrangler containers info <ID>` |
| Build status and logs | `GET /accounts/{account_id}/builds/workers/{worker_tag}/builds`, then `GET /accounts/{account_id}/builds/builds/{build_uuid}/logs` |

Builds are identified by `script_tag`, not by name, and the Builds API accepts only a user-scoped token. Build logs are retained for 90 days. Workers Logs keeps 3 days on Free and 7 days on Paid, with a 256 KB cap per log line.

## Change Settings

`wrangler secret put KEY` creates a new version and deploys it immediately. It is a deploy, not a settings edit: it moves production traffic, so it sits in the same approval tier as a deploy, and it is not a way to prepare a secret for a later release.

| Goal | Command |
|---|---|
| Secret live now | `wrangler secret put KEY`, or `wrangler secret bulk secrets.json` (up to 100; `null` deletes) |
| Secret staged on a version | `wrangler versions secret put KEY` |
| Secrets uploaded with the code | `wrangler deploy --secrets-file .env.production` |
| Fail the deploy when a secret is missing | `secrets.required: ["KEY"]` in the configuration |
| Local development | `.dev.vars` or `.dev.vars.<env>`, and not `.env` beside it |

`--secrets-file` parses dotenv syntax, including `$VAR` expansion against the process environment, so point it only at a file whose contents you control. Secrets absent from a `--secrets-file` deploy are preserved from the previous version, and no deploy deletes a secret.

Previews are the recommended way to test a change before production (`wrangler preview`, project-local Wrangler 4.135.0 or newer). Version URLs (`<version-prefix>-<worker>.workers.dev`) are the older mechanism, keep the `preview_urls` key, are not generated for Workers with a Durable Object, and cannot be read through Workers Logs or `wrangler tail`. Both serve the production resources, and preview URLs are public unless Cloudflare Access is configured; say so before handing one out. The old `--preview-alias` branch previews are superseded by Previews.

## Rollback

```sh
npx --no-install wrangler rollback [<VERSION_ID>] --message "rollback: <reason>"
```

A rollback immediately creates a new deployment with the chosen version and moves traffic to it, so it is a forward action, not a rewind. Without a version ID it takes the previous version. `--message` skips the confirmation prompt.

- Only the last 100 versions can be rolled back to, the same window gradual deployments use.
- A rollback restores Worker code only. Resources bound to the Worker, their data, D1 contents, KV entries, R2 objects, and Queues are not changed.
- A rollback is refused after a Durable Object class lifecycle change, or when a bound resource the target version expects no longer exists. Deleting an image that a version used also breaks a rollback to that version.
- Rolling back a database is a different operation with a different risk: `wrangler d1 time-travel restore <DB> --bookmark <BM>` overwrites the database in place, cancels in-flight queries, and is destructive. `wrangler d1 migrations apply --remote` changes schema and data. Both need explicit approval and a stated bookmark or backup.

## Failure Table

| # | Signature | Cause | Fix |
|---|---|---|---|
| 1 | `Missing entry-point: The entry-point should be specified via the command line … or the main config field` | No configuration at the build root, or `main` missing | Add `main`, or fix the Builds root directory |
| 2 | `The name in your Wrangler configuration file … must match the name of your Worker` | Config `name` differs from the dashboard Worker | Make `name` match, unless `env.<name>` suffixing applies |
| 3 | `Could not route to /client/v4/accounts/<ID>/workers/services/… [code: 7003]` | A different `account_id` pinned in the config | Remove it and use `CLOUDFLARE_ACCOUNT_ID` |
| 4 | `The build token selected for this build has been deleted or rolled` | Stale build token | Issue a new token and update the Builds setting |
| 5 | `Build was timed out` | 20-minute build ceiling | Split the build, cache dependencies, narrow `path_includes` |
| 6 | Deploy succeeds; the site returns 404 or a blank page | `assets.directory` does not match the build output, or an SPA without `not_found_handling` | Fix the directory, set `not_found_handling: "single-page-application"` |
| 7 | `npm ci` fails in the build but passes locally | The build image's npm is older than the lockfile's | Pin `"packageManager": "npm@x.y.z"` |
| 8 | `10027` on upload | Bundle over the 64 MiB Worker size limit | Remove or split dependencies; check with `--dry-run --outdir` |
| 9 | `10021` with `Script startup exceeded CPU time limit` | Too much work in top-level scope | Make initialisation lazy; keep startup near 1 second and 128 MB |
| 10 | Runtime `1102` and `Worker exceeded resource limits` | CPU limit exceeded (Free 10 ms, Paid default 30 s) | Raise `limits.cpu_ms` up to 300000, or split the work |
| 11 | `1102` with `Exceeded Memory` | 128 MB isolate limit | Stream with `TransformStream`; move large values to R2, KV, or D1 |
| 12 | `1101` with `The script will never generate a response` | Unresolved promise or an unclosed WebSocket | Add a no-floating-promises lint, close the server, accept the WebSocket |
| 13 | `1042`, or a same-zone fetch failing | A Worker fetching another Worker in the same zone through a route | Use a service binding or a Custom Domain |
| 14 | `1019` | More than 16 chained Worker invocations | Flatten the call chain |
| 15 | Environment variables disappear after a deploy | `deploy` overwrote dashboard `vars` | Set `keep_vars: true` or `--keep-vars`, and keep the file canonical |
| 16 | A binding is `undefined` at runtime | `env.<name>` does not declare that binding or `vars`; they are not inherited | Declare bindings per environment |
| 17 | Deploy fails with a missing secret | `secrets.required` is declared and the secret is absent | `wrangler secret put`, or `--secrets-file` |
| 18 | Adding a Custom Domain fails | An existing CNAME on that hostname, or the zone is not owned | Remove the CNAME first, then add the domain |
| 19 | `versions upload` fails on a new Worker | `versions upload` cannot create the first version | Run `wrangler deploy` once |
| 20 | `versions upload` returns `10211` | Pending Durable Object migration, Wrangler below 4.131.0 | Run `wrangler deploy`, or upgrade Wrangler |
| 21 | A D1 migration fails | SQL error or a constraint violation | That migration alone is rolled back; fix it and reapply; use `PRAGMA defer_foreign_keys = true` |

### Containers

Workers do not open a port and have no health check, so a port or healthcheck failure exists only in this path. Applying Docker-shaped diagnosis to a Worker without Containers is a wrong diagnosis.

| # | Signature | Cause | Fix |
|---|---|---|---|
| 22 | The Worker works; container routes return 5xx | First-deploy provisioning, or an image or rollout failure (non-transactional) | Wait several minutes, then read `containers instances` and the image build log |
| 23 | `Container is not listening to port 8080` | The container process has not opened the port yet | Poll with a retry loop, and bind `0.0.0.0` on the expected port |
| 24 | Container reports `internal error` | Docker socket not detected | Set `DOCKER_HOST` |
| 25 | A Python container fails only after deploy with `UnicodeEncodeError: 'idna' codec can't encode …` | The deployment hostname is 64 characters, beyond the DNS label limit | Use a server that does not resolve its hostname, such as `socketserver` |

## Approval Required

| Action | Tier |
|---|---|
| `--dry-run`, `wrangler versions upload`, `deployments status`, `versions list`, `tail`, `containers instances`, Builds API reads, config edits in the repository | proceed |
| Deploy or redeploy to production, `wrangler secret put` in production (it deploys immediately) | named environment |
| `wrangler rollback` in production, `versions deploy` promotion to 100%, `wrangler delete`, `d1 migrations apply --remote`, `d1 execute --remote`, `d1 time-travel restore`, `containers images delete`, `wrangler secret delete`, route or Custom Domain changes, disabling `workers_dev` or `preview_urls`, deleting a Preview, `--containers-rollout=immediate` | explicit approval |
| Logging in, creating an account or project, installing a global CLI, printing a token | never |

Before a rollback, state that it restores code only and leaves bound resources and data at their current state.

## Checked

> Volatile. Checked 2026-11-07 against the sources below; recheck the live page when a decision depends on a flag, a limit, or a recommendation.

| Fact | Value |
|---|---|
| New projects | Workers with Static Assets; Pages is not deprecated but is no longer the starting point |
| Config for new Wrangler projects | `wrangler.jsonc`; TOML still works |
| `cf` CLI path | `cloudflare.config.ts`, open beta, Node.js 22.18+, no Bun |
| Next.js | `vinext` beta recommended; OpenNext for existing apps |
| Worker size | 64 MiB uncompressed |
| Static assets | 20,000 files Free, 100,000 Paid, 25 MiB each |
| Builds | 20 minutes max, 6 concurrent, 8 GB memory |
| Rollback window | last 100 versions |
| D1 time travel retention | 7 days Free, 30 days Paid |
| Containers | Workers Paid plan, 50 GB image storage per account, 15-minute `SIGTERM` grace |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| `wrangler.jsonc` is recommended for new projects and some features are JSON-only | <https://developers.cloudflare.com/workers/wrangler/configuration/> |
| New projects start on Workers; Workers covers most Pages use cases | <https://developers.cloudflare.com/pages/> |
| Pages migration mapping, explicit SPA handling, `.assetsignore` | <https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/> |
| `cloudflare.config.ts` is open beta under the `cf` CLI | <https://developers.cloudflare.com/cf/projects/cloudflare-config/> |
| `deploy` creates a version and moves 100% of traffic | <https://developers.cloudflare.com/workers/versions-and-deployments/> |
| `versions upload` fails on a first upload | <https://developers.cloudflare.com/workers/versions-and-deployments/deployment-management/> |
| Only the last 100 versions support gradual deploys and rollback | <https://developers.cloudflare.com/workers/versions-and-deployments/gradual-deployments/>, <https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/> |
| A rollback does not change bound resources | <https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/> |
| `--strict`, `versions`, `rollback`, `tail` flags | <https://developers.cloudflare.com/workers/wrangler/commands/workers/> |
| `wrangler secret put` deploys immediately; `secrets.required`; `--secrets-file` | <https://developers.cloudflare.com/workers/configuration/secrets/> |
| `WRANGLER_OUTPUT_FILE_PATH` ND-JSON events | <https://developers.cloudflare.com/workers/wrangler/system-environment-variables/> |
| `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` for CI | <https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/> |
| Builds limits and build command | <https://developers.cloudflare.com/workers/ci-cd/builds/configuration/>, <https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/> |
| Build logs API and 90-day retention | <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/> |
| Workers Logs retention and default observability | <https://developers.cloudflare.com/workers/observability/logs/workers-logs/> |
| Error codes 10021, 10027, 1019, 1042, 1101, 1102 | <https://developers.cloudflare.com/workers/observability/errors/>, <https://developers.cloudflare.com/workers/platform/limits/> |
| `vinext` recommended for Next.js, OpenNext for existing apps | <https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/>, <https://developers.cloudflare.com/workers/framework-guides/web-apps/opennext/> |
| Temporary deployments are claimable for 60 minutes | <https://developers.cloudflare.com/workers/platform/claim-deployments/> |
| Version URLs are not generated for Durable Object Workers | <https://developers.cloudflare.com/workers/versions-and-deployments/version-urls/> |
| Previews are the recommended pre-production test | <https://developers.cloudflare.com/workers/previews/compare-workflows/> |
| A Custom Domain cannot be added over an existing CNAME | <https://developers.cloudflare.com/workers/configuration/routing/custom-domains/> |
| `wrangler deploy` with no config auto-detects the framework | <https://developers.cloudflare.com/workers/get-started/prompting/> |
| Containers deploy is non-transactional | <https://developers.cloudflare.com/containers/guides/deploy/> |
| Deploy success means the rollout started | <https://developers.cloudflare.com/containers/configuration/rollouts/> |
| Container port 8080 readiness and troubleshooting | <https://developers.cloudflare.com/containers/guides/local-dev/> |
| Container limits and image storage | <https://developers.cloudflare.com/containers/platform/limits/> |
| D1 migrations capture a backup and roll back the failing migration | <https://developers.cloudflare.com/d1/reference/migrations/>, <https://developers.cloudflare.com/workers/wrangler/commands/d1/> |
| D1 time travel restore is destructive and in place | <https://developers.cloudflare.com/d1/reference/time-travel/> |
| Use the project's Wrangler version, prefer `cf` on `cloudflare.config.ts` projects, treat `secret put` as a deploy | <https://github.com/cloudflare/skills> |

### Evidence grade

`LOCAL` - the section order, approval tiers, and failure triage are this package's design over Cloudflare's first-party documents above. The CLI was not run locally in this environment, so every flag and exit behaviour is quoted from the documentation rather than observed. Previews, `vinext`, and `cloudflare.config.ts` are beta or open beta and may change without a deprecation notice; re-read the live page before relying on them.
