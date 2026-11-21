# Railway

Target guide for Railway, read after `rules/target-detection.md` routes here. It covers the current authoring file for new work, the deprecated configuration files that still exist in older repositories, non-interactive deploy and verification commands, diagnostics, and what a rollback does not restore.

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

New work uses Infrastructure as Code: one authoring file at `.railway/railway.ts` (generally available), with `.railway/railway.py` and `.railway/railway.go` in beta. Keep exactly one of the three files, and install the matching package next to it (`npm install railway` for TypeScript, `pip install railway-sdk` for Python, `go get github.com/railwayapp/railway-go-sdk@v0.3.0` for Go). The CLI finds the nearest authoring file by walking up from the current directory, so `--file` is only needed when a second file exists.

```ts
import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const web = service("web", {
    build: "pnpm build",
    start: "pnpm start",
    healthcheck: "/health",
    healthcheckTimeout: 60,
    env: { NODE_ENV: "production", STRIPE_SECRET_KEY: preserve() },
  });

  return project("my-app", { resources: [web] });
});
```

| Purpose | Authoring form |
|---|---|
| Build and start | `build`, `start` |
| Health gate | `healthcheck` (path), `healthcheckTimeout` (seconds; platform default 300) |
| Between build and deploy | `preDeploy` (one command string) |
| Scale | `replicas: 3`, or a region map such as `{ "us-west2": 2 }` |
| Source | `source: github("owner/repo", { branch: "main" })`, or `image("ghcr.io/acme/api:1.2.3", { autoUpdates: { type: "patch" } })` |
| Variables | `env: { KEY: "value" }`, cross-service `db.env.DATABASE_URL`, shared `ctx.shared.NAME` → `${{shared.NAME}}`, existing value `preserve()` |
| Storage | `volume("data", { region, sizeMB })` plus `volumeMounts: { "/data": data }` |
| Environment-dependent state | `defineRailway((ctx) => …)` with `ctx.environment`, `ctx.isEnvironment(name)` |

Config as Code (`railway.toml` / `railway.json`) is deprecated. Existing files keep working for services that already use them until **2026-12-01** (hard cutoff). New services cannot opt into it. A service cannot be managed by both systems: `railway config plan` stops and names the service that must be migrated first. Plan migrations with `railway config migrate` (dry run by default), write with `--apply`, and remove the old files only after the cutover with `--apply --delete-files`; `railway config migrate cutover` switches a service off Config as Code and `railway config migrate status` shows what remains. Never hand-write a new `railway.toml`.

Builders: Railpack is the default and needs no configuration for Node, Python, Go, PHP, Java, Ruby, Deno, Rust, Elixir, shell scripts, and static HTML. A `Dockerfile` switches the build to the Dockerfile path and must be named exactly `Dockerfile` with a capital D; any other name or location needs `RAILWAY_DOCKERFILE_PATH`. Nixpacks is in maintenance mode upstream and is not offered here as a choice; do not set it. Railpack settings come from `RAILPACK_*` service variables or its own config file.

## Authentication

Two token types exist and only one may be set at a time.

| Variable | Scope | Use |
|---|---|---|
| `RAILWAY_TOKEN` | one project and one environment | deploy, redeploy, logs, variables, `config apply` for that environment |
| `RAILWAY_API_TOKEN` | account and workspace | creating or deleting environments, work across several projects, the MCP server |

Setting both makes the CLI error out. The MCP server rejects project tokens because it needs a user identity for billing and audit, so an MCP-driven run needs `RAILWAY_API_TOKEN`. Never pass a token as a command-line argument; it lands in shell history and the process list.

```sh
[ -n "${RAILWAY_TOKEN:-}" ] && echo project-token-set
[ -n "${RAILWAY_API_TOKEN:-}" ] && echo account-token-set
railway whoami
```

The presence test prints nothing sensitive; `railway whoami` confirms which identity the CLI resolved. Do not run `railway whoami` before the token check when both are cheap, since an unauthenticated call fails instead of telling you which variable is missing.

## Identify And Deploy

Start with the context, not with a deploy:

```sh
railway status --json
```

Then name the project, environment, and service explicitly on every writing command instead of relying on the linked directory. `--project` requires `--environment`; pass `--service` too when the project has more than one.

```sh
railway up --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --detach --json -m "<release summary>"
railway up --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --ci -m "<release summary>"
```

- `--detach` (alias `--no-wait`) returns once the upload is accepted and the build is **queued**. With `--json` it prints `{"deploymentId": …, "logsUrl": …}`; keep the ID.
- `--ci` streams build logs only and exits with the deployment's verdict as its exit code. `--json` implies CI behaviour for an authenticated deploy.
- Outside CI mode, the CLI also returns right after upload when stdout is not a terminal. Omitting `--detach` in an agent run does not mean the command waited; poll for the ID either way.
- A non-interactive run with no linked project fails with `NOT_AUTHENTICATED` or a no-project error instead of creating one. Scripts and CI never create projects implicitly, so the project must exist and be named.

`railway deploy` and `railway down` are not code deploys and are never used for a release: `railway deploy` provisions a template into the project (`--template postgres`), and `railway down` removes the most recent deployment from the service. Code goes out with `railway up` (or the equivalent `railway deployment up`).

## Success Test

Success is this run's `deploymentId` reaching `SUCCESS`, a quiet runtime log window, and a 2xx from the service URL.

```sh
railway deployment list --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --limit 10 --json
railway logs <DEPLOYMENT_ID> --lines 100 --json
curl -sS -o /dev/null -w '%{http_code}\n' https://<domain>/health
```

- Match on the ID returned by `railway up`, never on "the newest deployment". A concurrent newer deploy from another source is not this run's result.
- `--ci` exiting `0` is not sufficient on its own: a build that matches no watch pattern can end as `SKIPPED` with exit `0`, and a detached or non-TTY run can exit `0` after upload alone.
- States run `QUEUED` → `INITIALIZING` → `BUILDING` → `DEPLOYING` (plus `WAITING` behind GitHub checks) → `SUCCESS`. `FAILED`, `CRASHED`, `SKIPPED`, `SLEEPING`, `NEEDS_APPROVAL`, `REMOVING`, and `REMOVED` are not success; report the state as it is and the next action. `NEEDS_APPROVAL` waits for a human and must not be polled as if it were still building.
- The health check is a one-time gate at deploy, not continuous monitoring. A service with an attached volume cannot be zero-downtime even with a health check, because only one deployment may hold the volume.

## Status And Logs

Every log command needs a bound; without `--lines`, `--since`, or `--until` the CLI streams until interrupted.

| Question | Command |
|---|---|
| Current context and resources | `railway status --json`, `railway environment config --json` |
| Deployment history and states | `railway deployment list --limit 10 --json` |
| Build log | `railway logs --build --lines 400 --json` |
| Runtime log for one deployment | `railway logs <DEPLOYMENT_ID> --lines 200 --json` |
| Runtime log of the newest deployment, even a failed one | `railway logs --latest --lines 200 --json` |
| Error-only window | `railway logs <DEPLOYMENT_ID> --lines 200 --filter "@level:error" --json` |
| HTTP failures | `railway logs --http --status ">=400" --lines 100 --json` |
| Dropped network flows | `railway logs --network --status dropped --lines 100 --json` |
| Failed DNS lookups | `railway logs --dns --status failed --since 1h --lines 100 --json` |
| CPU, memory, volume, HTTP metrics | `railway metrics --since 1h --json`, `--memory`, `--http`, `--raw` |
| Domain and certificate state | `railway domain list --json`, `railway domain status <domain> --json` |
| Variables | `railway variable list --json` (prints values; do not paste the output) |
| Cron runs | `railway cron list` |

`railway logs` accepts HTTP, network, and DNS filters (`@httpStatus:>=500`, `@path:/api`, `@peer_kind:internet`, `@rcode:NXDOMAIN`) and one log type per call. The deploy log defaults to the most recent successful deployment, so pass the ID when diagnosing a failure.

## Change Settings

Variables are staged: setting one records a pending change that reaches the service on the next deploy. `railway variable set` triggers that deploy unless `--skip-deploys` is set.

```sh
railway variable set DATABASE_URL --service <SERVICE> --environment <ENV> --stdin
railway variable set LOG_LEVEL=debug --service <SERVICE> --environment <ENV> --skip-deploys
railway variable delete OLD_KEY --service <SERVICE> --environment <ENV>
```

- `--stdin` reads the value from stdin, so the secret never appears in the argument list. `KEY=VALUE` on the command line is for non-secrets only.
- `--skip-deploys` records the change without deploying; the value is not live until a deploy runs.
- `variable list --json` and `-k/--kv` print raw values. Read them only when needed and never copy them into the report.
- Sealed variables are writable but their value is never readable: they cannot be un-sealed, are not returned by `railway variables` or `railway run`, are not copied into pull-request environments or when duplicating an environment or service, are not shown in environment diffs, and do not sync with external integrations. A duplicate environment therefore arrives without them, and a run that assumes otherwise fails at startup.

Infrastructure changes go through plan and apply, never a hand edit of live settings:

```sh
railway config plan --environment <ENV> --detailed-exit-code
railway config plan --out railway-plan.json
railway config apply --plan railway-plan.json --yes --confirm-destructive
```

- `plan` only reads; variable values appear as `«hidden»` unless `--show-values` is passed.
- `--detailed-exit-code` makes `plan` exit `2` when changes are pending and `0` when none are, which is the CI drift gate.
- A non-interactive apply of a destructive change needs both `--yes` and `--confirm-destructive`. `apply` always runs a fresh plan and rejects a plan whose environment etag or `.railway/` tree no longer matches, so re-plan after any concurrent change.
- `railway config pull --include-variables` decrypts non-sealed values, including unsealed secrets, into `.railway/railway.ts`. Never run it in an agent flow; keep imported values as `preserve()`.

## Rollback

Rolling back to an arbitrary earlier deployment is a dashboard action; the CLI has no rollback subcommand.

- A rollback restores the previous Docker image **and** the custom variables from that deployment, so a variable changed since then is reverted too.
- It only works inside the plan's image retention window: Free and Trial 24 hours, Hobby 72 hours, Pro 120 hours, Enterprise 360 hours. Past that the option disappears and only a redeploy remains.
- It restores code and service variables only. Databases, volumes and their data, buckets, and any resource bound to the service are not restored, and a schema migration that already ran stays run.
- Before proposing one, state the retention window, that variables revert, and that data does not.

Alternatives, in order of preference when the cause is not the image:

| Command | Rebuilds | Use when |
|---|---|---|
| `railway redeploy --service <SERVICE> --yes` | no, same image | the build is fine and the container needs to restart from a known image |
| `railway redeploy --from-source --yes` | yes, latest commit or image | the failure is stale code |
| `railway redeploy --commit <SHA> --yes` | yes, that commit once | a specific commit must be tried without pinning it |
| `railway restart --service <SERVICE> --yes` | no, same container | the process is wedged at runtime |

`railway down` removes the most recent deployment; it is not a rollback and does not return the service to an earlier image.

## Failure Table

| # | Signature | Cause | Fix | Check | Tier | Source |
|---|---|---|---|---|---|---|
| 1 | `Application failed to respond` (502), health check reporting `service unavailable` or `status 400` | App bound to `localhost` or a hard-coded port; target port differs from the listening port | Bind `0.0.0.0` and read `PORT`; align the domain target port or set a `PORT` variable | `railway logs --http --status ">=400"`, then `curl -I https://<domain>/health` returns 2xx | proceed | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| 2 | `No start command could be found` | Railpack could not detect a start command | Set `start` in the authoring file or the start command in service settings (for example `uvicorn main:app --host 0.0.0.0 --port $PORT`) | redeploy reaches `SUCCESS` and the app log shows it listening | proceed | <https://docs.railway.com/deployments/troubleshooting/no-start-command-could-be-found> |
| 3 | Deployment ends `FAILED` around 300 seconds | Health check timed out, or `healthcheck.railway.app` is not allowed by the app's host filter | Raise `healthcheckTimeout` or `RAILWAY_HEALTHCHECK_TIMEOUT_SEC`, remove startup delay, allow the health check host | `SUCCESS` plus a 2xx on the health path | proceed | <https://docs.railway.com/deployments/healthchecks> |
| 4 | `KeyError`, `undefined`, or a connection to an empty host | Variable missing from the environment, or set but never deployed | Set it with `--stdin`, then deploy so the staged change lands | runtime log starts clean, HTTP log shows 200 | proceed | <https://docs.railway.com/variables> |
| 5 | Dependency install fails, wrong package manager, `Cannot find module` | Builder misdetected the project, or the build ran from the wrong directory | Set `build` explicitly, and `RAILPACK_*` variables for the runtime version; move the service root rather than the whole repo | rebuild log shows the intended command, then `SUCCESS` | proceed | <https://docs.railway.com/builds/railpack> |
| 6 | Container exits immediately, `exec format error`, or a restart loop with no app log | Image built for the wrong CPU architecture (arm64 built locally, deployed to amd64) | Rebuild with `docker build --platform linux/amd64`, push, then `railway redeploy --from-source` | `SUCCESS` and an app log line | proceed | <https://docs.railway.com/guides/private-container-registry> |
| 7 | Exit code 137, repeated restarts | Out of memory | Reduce memory use or raise replicas within the plan | `railway metrics --since 1h --memory` stable and no restart for 30 minutes | explicit approval (cost) | <https://docs.railway.com/deployments/troubleshooting/slow-deployments> |
| 8 | `Pre-deploy command timed out after N seconds`, deploy stops | Migration failed or hung; pre-deploy has no volumes and needs its own dependencies | Fix the command, keep it under the 1–3600 second cap, do not touch the volume there | redeploy reaches `SUCCESS`, migration log exits 0 | explicit approval (schema change) | <https://docs.railway.com/deployments/pre-deploy-command> |
| 9 | `ENOTFOUND redis.railway.internal` | Client resolves A records only in an IPv6-only legacy environment, or the service is in another project or environment | Set `family=0` for ioredis and bullmq, confirm same project and environment, use the public URL from outside | `railway logs --dns --status failed` empty and the app connects | proceed | <https://docs.railway.com/databases/troubleshooting/enotfound-redis-railway-internal> |
| 10 | Deployment is `SKIPPED`, "no changed files match watch patterns" | Watch paths excluded the changed files, or a failing GitHub check suite skipped it | Fix watch paths, or `railway redeploy --from-source` | a new deployment reaches `SUCCESS` | proceed | <https://docs.railway.com/deployments/github-autodeploys> |
| 11 | Custom domain returns 404, certificate error | Only the CNAME was added; the TXT verification record is missing, or the certificate needs a retry | Add both records exactly as shown, then `railway domain certificate retry` | `curl -I https://<domain>` returns 200, `railway domain status` shows a valid certificate | proceed | <https://docs.railway.com/networking/domains/working-with-domains> |
| 12 | `EACCES` on writes, or data gone after a deploy | Volume mounted at the wrong path, written by a non-root user, or written during build or pre-deploy | Mount under `/app/...`, set `RAILWAY_RUN_UID=0` for a non-root image, write at runtime only | restart and confirm the file persists | explicit approval (volume change) | <https://docs.railway.com/volumes> |
| 13 | Cron never runs, previous run still active | The process does not exit; schedule is closer than 5 minutes or not in UTC | Make the job terminate and close its connections, use a schedule at least 5 minutes apart in UTC | `railway cron list` shows a completed run at the next slot | proceed | <https://docs.railway.com/cron-jobs> |
| 14 | Exit code `0` but nothing deployed | Upload only, detached or non-TTY return, or a skipped build | Apply the success test above against this run's deployment ID | `deployment list --json` shows that ID as `SUCCESS` | proceed | <https://docs.railway.com/cli/up> |

## Approval Required

| Action | Tier |
|---|---|
| `railway status`, `deployment list`, `logs` with a bound, `metrics`, `variable list`, `domain status`, `cron list`, `railway config plan`, editing the authoring file in the repository | proceed |
| `railway up`, `redeploy`, `restart`, a variable change, `railway config apply` in a non-production environment | proceed |
| The same in production | named environment |
| Production rollback (dashboard), `railway down`, service, environment, domain, volume, or bucket deletion, `railway config apply --confirm-destructive` on a production environment, `railway config partials release` or `transfer`, a pre-deploy or manual database migration against real data, an action that adds cost (replicas, plan, region), creating a new public domain or TCP proxy, `config pull --include-variables` | explicit approval |
| Logging in or creating an account or project, installing a CLI globally, printing a token or a `variable list --json` value, unsealing a sealed variable | never |

Approval covers the one action it names. A rollback approval does not cover the deploy that follows it, and a variable approval does not cover the redeploy.

## Checked

> Volatile. Checked 2026-11-07; recheck the live page when a flag, a limit, or the deprecation date decides the run.

| Fact | Value |
|---|---|
| CLI | railway 5.71.0 installed and run locally on 2026-11-07 |
| Flags | every flag used here was re-read from `railway <command> --help` on that binary, not recalled |
| Authoring file | `.railway/railway.ts` (GA); `.py` and `.go` beta; exactly one file |
| Config as Code cutoff | 2026-12-01, hard; new services cannot opt in |
| Builders | Railpack default, Dockerfile when the file is named exactly `Dockerfile`; Nixpacks not offered |
| Health check | 2xx polling at deploy only, default timeout 300 seconds, host `healthcheck.railway.app` |
| Image retention | Free 24 h, Hobby 72 h, Pro 120 h, Enterprise 360 h |
| Pre-deploy | no volumes, private network available, timeout 1–3600 s, no retry |
| Cron | UTC, minimum 5 minutes apart, process must exit |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Config as Code is deprecated, works for legacy services until 2026-12-01, and new services cannot opt in | <https://docs.railway.com/config-as-code> |
| IaC replaces Config as Code; one authoring file; a service cannot be managed by both; `config plan` stops on legacy services | <https://docs.railway.com/infrastructure-as-code> |
| TypeScript DSL: services, build, start, healthcheck, preDeploy, replicas, env, preserve, volumes | <https://docs.railway.com/infrastructure-as-code/reference> |
| `config migrate` flags, cutover, undo, status; `plan --out` then `apply --plan`; `--detailed-exit-code`; redacted values; stale-plan rejection | <https://docs.railway.com/cli/config> |
| Railpack builds with zero configuration and covers the listed languages | <https://docs.railway.com/builds/railpack> |
| The Dockerfile must be named `Dockerfile` with a capital D; `RAILWAY_DOCKERFILE_PATH` for other names | <https://docs.railway.com/builds/dockerfiles> |
| Build and start command overrides; exec-form commands need a shell for `$PORT` | <https://docs.railway.com/builds/build-and-start-commands> |
| `RAILWAY_TOKEN` is project-scoped, `RAILWAY_API_TOKEN` account-scoped, and only one may be set | <https://docs.railway.com/cli/login> |
| Project tokens are scoped to one environment and only deployment actions | <https://docs.railway.com/cli/deploying> |
| The MCP server rejects project tokens | <https://docs.railway.com/ai/mcp-server> |
| `up` flags, `--detach` returning at queue time, non-interactive runs never creating projects, exit code meanings | <https://docs.railway.com/cli/up> |
| Early return when stdout is not a terminal and CI mode is off | <https://raw.githubusercontent.com/railwayapp/cli/master/src/commands/up.rs> |
| `deployment list` with `--limit` and `--json`; `deployment up`, `deployment redeploy` | <https://docs.railway.com/cli/deployment> |
| Log types, `--lines` disabling streaming, filter syntax, `--latest` | <https://docs.railway.com/cli/logs> |
| Deployment states and what Active means with and without a health check | <https://docs.railway.com/deployments/reference> |
| Health check polls 2xx, default 300 s timeout, no monitoring after the deploy, volume services take downtime, health check host name | <https://docs.railway.com/deployments/healthchecks> |
| Pre-deploy runs between build and deploy, no volumes, private network available, no retry, 1–3600 s cap | <https://docs.railway.com/deployments/pre-deploy-command> |
| Variables are staged and deployed; sealed variable constraints | <https://docs.railway.com/variables> |
| Staged changes must be reviewed and deployed | <https://docs.railway.com/deployments/staged-changes> |
| Rollback restores the image and custom variables, is limited by plan retention, and is dashboard-only | <https://docs.railway.com/deployments/deployment-actions> |
| Retention windows per plan | <https://docs.railway.com/pricing/plans> |
| Volumes mount at runtime only, not at build or pre-deploy, and `RAILWAY_RUN_UID=0` for non-root images | <https://docs.railway.com/volumes> |
| Custom domain needs CNAME and TXT, a missing TXT returns 404, propagation up to 72 hours | <https://docs.railway.com/networking/domains/working-with-domains> |
| Cron schedules are UTC, at least 5 minutes apart, and the process must exit | <https://docs.railway.com/cron-jobs> |
| Watch paths can skip a deploy, and a failing check suite skips it immediately | <https://docs.railway.com/deployments/github-autodeploys> |
| Exit 137 is an OOM kill | <https://docs.railway.com/deployments/troubleshooting/slow-deployments> |
| arm64 images built on Apple Silicon crash on Railway without `--platform linux/amd64` | <https://docs.railway.com/guides/private-container-registry> |
| ioredis needs `family=0` against the IPv6-only legacy private network | <https://docs.railway.com/databases/troubleshooting/enotfound-redis-railway-internal> |
| `Application failed to respond` means the app is not listening on `0.0.0.0:$PORT` or the target port is wrong | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| `No start command could be found` means Railpack found no start command | <https://docs.railway.com/deployments/troubleshooting/no-start-command-could-be-found> |
| Never report a deploy as successful without observing `SUCCESS` for that deployment; `--detach` means queued; exit 0 can be a skip | <https://github.com/railwayapp/railway-skills> |

### Evidence grade

`DIRECT` for the CLI surface: railway 5.71.0 was installed and every command and flag above was read from its `--help` on 2026-11-07, and the non-TTY early return was confirmed in the published CLI source. `SECONDARY` for platform behaviour that only a live project can show, such as retention windows and per-plan limits, which are quoted from Railway's own documentation and were not exercised against a project in this environment. The 2026-12-01 cutoff is a documentation banner, not a signed contract; re-read the page before a migration depends on the date.
