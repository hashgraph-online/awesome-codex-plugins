# Deploy Workflow

Use this rule once the target is known. It owns mode selection, the phases of each mode, the diagnosis order, and the report path. Approval tiers live in `rules/safety-gates.md`; the readiness scripts live in `rules/preflight.md`; completion evidence lives in `rules/validation.md`.

## 1. Pick The Mode

Pick from the requested output, then confirm it with repository files.

| Requested output | Mode | Edits allowed |
|---|---|---|
| A readiness verdict, or a fix to the blocker that prevents it | `preflight` | Files tied to a reproduced lint, typecheck, or build failure |
| The same verdict with "validate only", "고치지 말고", or "do not edit" | `preflight` validate-only | The report only |
| Deployment configuration where none exists, and a first deployment | `setup` | New configuration files: `Dockerfile`, `.dockerignore`, compose files, platform configuration, health endpoint wiring |
| A deployment of existing configuration to a named environment | `deploy` | None, unless the readiness step fixes a blocker |
| A change to an existing deployment's settings | `change` | The configuration file or platform setting the request names |
| A failed, crashing, unhealthy, or misbehaving deployment | `diagnose` | The file or setting the root cause points to |

When the request mixes outputs ("set it up and deploy to staging"), run the modes in this order and stop at the first one that stops: `preflight`, `setup` or `change`, `deploy`. `diagnose` takes over whenever a deployment in this run fails.

## 2. Identify Before Writing

Before the first command that writes to a platform, a server, or a registry:

1. Name the target identity: the project, environment, and service IDs or names, the Worker name and environment, the image repository and tag, or the host and Compose project.
2. Name the environment and whether it is production. A request that names no environment deploys to a non-production one when the target has it; when the only environment is production, ask one question first.
3. Confirm the credential variable the guide names is set, without printing its value. When it is missing, stop and name the variable.
4. Read the CLI's `--help` for the exact subcommand and flags the run will use, and record the CLI version.

A linked directory, a default environment, or a CLI prompt answer is not an identity. State it, then act.

## 3. Mode Phases

### `preflight`

Follow `rules/preflight.md`: stack detection, a full baseline run, triage, narrow fixes, and a fresh full proof run. A passing run is a readiness verdict, not approval to deploy.

### `setup`

1. Read the guide's canonical configuration section; use the format the guide marks as current, never a deprecated one.
2. Write the smallest configuration that builds and starts the app: build and start commands, the listening address `0.0.0.0` and the platform's port variable where the target routes by port, and a health endpoint where the target checks health.
3. Validate locally where the guide names a validator (`docker compose config -q`, `wrangler deploy --dry-run`, `railway config plan`).
4. Deploy once to a non-production environment and run the `deploy` phases 2-4 below.

### `deploy`

1. Run the readiness step when the repository has a supported stack (`rules/preflight.md`); a failing proof stops the deploy.
2. Run the guide's deploy command with the identity from section 2 passed explicitly.
3. Record the deployment ID or version the command returned.
4. Poll the guide's status command for that ID until it reaches a terminal state, within the guide's timeout. Then run the health check.

### `change`

1. Read the current setting with the guide's read command and record it.
2. Show the planned change as a diff, a plan output, or before-and-after values. A change that the platform applies immediately (for example a Cloudflare secret, which creates a deployment) is treated as a deploy.
3. Apply it, redeploy when the platform needs one, and run `deploy` phases 3-4.

### `diagnose`

1. Read in this order and stop narrowing when the cause is visible:
   1. what is serving now: the active deployment or version and its state
   2. the build log of the failed deployment
   3. the deploy and runtime log of the failed deployment
   4. runtime state and health: exit code, restart count, health probe output, memory
   5. the proxy, network, DNS, and TLS path
   6. an internal request from inside the network or container
2. Match the evidence against the guide's failure table. Record the symptom, the log or state line, the cause, and the fix.
3. Fix the cause in the file or setting it points to. Prefer a fix and a redeploy over a rollback: a failed deployment usually leaves the previous version serving.
4. Redeploy and compare the same signal before and after. A fix is proven only when the signal that showed the failure now shows success and the deployment reaches its terminal state.
5. Count one attempt per redeploy for the same root cause. At three attempts, stop with `exhausted` and report what was tried and the next evidence to collect.

A rollback is proposed, not run, unless the user approved it in this run (`rules/safety-gates.md`).

## 4. Common Failure Signatures

Each target guide carries its own table. These signatures recur across targets and are checked first:

| Signature | Usual cause | Check |
|---|---|---|
| Connection refused, 502, "failed to respond", health check unavailable | The app listens on `127.0.0.1` or another port | The start command and the port variable the platform sets |
| Health check timeout | Slow start, a wrong path, or a probe tool missing in the image | Startup log timing, the health path, `curl` or `wget` in the image |
| Exit code 137 or "Killed process" | Out of memory, or a forced stop after a timeout | Memory metrics and the stop timeout |
| `exec format error`, "no matching manifest" | An image built for the wrong CPU architecture | The image's platform and the host's architecture |
| A variable reads empty at runtime | Set at build time only, set in another environment, or not redeployed after a staged change | The platform's variable list for this environment |
| The deploy "succeeded" and nothing changed | The command reached another project, environment, or service, or the build was skipped | The deployment ID's identity and state |

## 5. Report Path

Write `.hyper/deploy/<slug>/report.md` from `references/report-template.md`. `<slug>` is a short kebab-case name of the run; add `-2`, `-3` when the folder exists for a different run. `preflight` also keeps its tracked state in `.hyper/deploy/<slug>/flow.json` when `rules/preflight.md` calls for it.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| A detached Railway upload confirms only that the deployment is queued; success is the deployment's `SUCCESS` state | <https://github.com/railwayapp/railway-skills> |
| A failed source build leaves the current application version running | <https://coolify.io/docs/core/build-deployment-model> |
| `wrangler secret put` creates and deploys a new version | <https://developers.cloudflare.com/workers/configuration/secrets/> |
| Apps must bind `0.0.0.0` and the injected `PORT` | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| Exit code 137 means SIGKILL | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| An arm64 host cannot run an amd64 image without emulation | <https://docs.docker.com/build/building/multi-platform/> |

### Evidence grade

`LOCAL` - the mode order, the diagnosis order, and the three-attempt budget are this package's design. The signatures are adapted from the cited platform documents, read on 2026-11-07.
