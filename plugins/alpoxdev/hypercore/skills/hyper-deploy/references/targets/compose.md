# Docker Compose

Target guide for a repository that deploys with `compose.yaml` on one Docker host, local or reached over SSH. Read it after `rules/target-detection.md` routes here. When the deploy also builds a `Dockerfile`, the image rules live in the Docker image guide; this one owns the project model, the deploy sequence, and what a rollback cannot restore.

## Contents

- Canonical Configuration
- Remote Host
- Validate And Deploy
- Success Test
- Status And Logs
- Change And Redeploy
- Rollback
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

Two files, merged in order: `compose.yaml` for the development shape and `compose.production.yaml` for the differences production needs. Never a single file with conditionals, and never a top-level `version` key.

```yaml
# compose.yaml
name: shop
x-db-url: &db_url postgres://shop:${DB_PASSWORD:?DB_PASSWORD is required}@db:5432/shop

services:
  web:
    image: ghcr.io/example/shop-web:${TAG:?TAG is required}
    build: { context: ., secrets: [npm_token] }
    ports: ["127.0.0.1:8080:8080"]
    environment:
      NODE_ENV: production
      DATABASE_URL: *db_url
    secrets: [db_password]
    depends_on:
      db: { condition: service_healthy, restart: true }
      migrate: { condition: service_completed_successfully }
    healthcheck:
      test: ["CMD", "node", "dist/healthcheck.js"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    restart: unless-stopped

  migrate:
    image: ghcr.io/example/shop-web:${TAG:?TAG is required}
    build: { context: . }
    command: ["node", "dist/migrate.js"]
    environment: { DATABASE_URL: *db_url }
    depends_on:
      db: { condition: service_healthy }
    restart: "no"

  db:
    image: postgres:18
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
    volumes: ["db_data:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop -d shop"]
      interval: 10s
      retries: 5
      start_period: 30s
    restart: unless-stopped

secrets:
  db_password: { environment: DB_PASSWORD }
  npm_token: { environment: NPM_TOKEN }

volumes:
  db_data:
```

```yaml
# compose.production.yaml
services:
  web:
    ports: !override ["127.0.0.1:8080:8080"]
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
  db:
    ports: !reset []
```

| Rule | Why |
|---|---|
| `compose.production.yaml` instead of one file with branches | The production file holds only the difference; the development file stays runnable |
| No top-level `version` | It is obsolete; Compose prints a warning and ignores it for schema selection |
| `depends_on` in long form with `condition` | The short list form waits only until the dependency is *started*, not until it is usable |
| `condition: service_completed_successfully` for a migration service | The migration must finish before the app starts; `service_healthy` on a job would block forever |
| `healthcheck` on every long-running service; `restart: unless-stopped` for servers, `"no"` for jobs | Without a health check nothing defines "healthy", so any wait passes on `running` alone; `unless-stopped` honours a manual stop and still restarts after a crash, while a restarting job loops forever |
| `${VAR:?message}` for required values | Interpolation fails with that message instead of silently producing an empty string |
| `127.0.0.1:8080:8080` | Publishing on all interfaces exposes the port to the internet regardless of the host firewall |

Environment handling has three separate mechanisms and mixing them is the most common "the variable is empty" cause:

| Source | Feeds | Precedence |
|---|---|---|
| Shell environment | interpolation of `${VAR}` in the Compose file | highest of the interpolation sources |
| `--env-file <file>` | interpolation, and `COMPOSE_*` self-configuration | overrides the project `.env` |
| `.env` in the project directory | interpolation only | lowest, and only when `--env-file` is absent |
| `env_file:` on a service | the container's environment | below `environment:`, above the image `ENV` |
| `environment:` on a service | the container's environment | above `env_file:` |

- A `.env` value is never passed to the container by itself; it only becomes a container variable through `environment:` or `env_file:`.
- `docker compose config --environment` prints the variables interpolation actually used. It is the fastest way to see which file supplied a value.

Secrets, not environment variables, for anything secret:

- A service gets a secret only through its own `secrets:` entry; declaring it at the top level grants nothing.
- It is mounted read-only at `/run/secrets/<name>` and is supported on Linux containers only.
- `environment:` as a secret source works with Compose but not with `docker stack deploy`. Prefer `file:` when the file is deployed with the project.
- Images that follow the `_FILE` convention (`postgres`, `mysql`) read `POSTGRES_PASSWORD_FILE=/run/secrets/db_password`; that keeps the value out of `docker inspect` entirely.

Profiles keep optional services (a backup job, an admin UI) out of the default start; core services must not carry one, or a plain `up` starts an incomplete stack.

Remote `include` and `extends` references are executable content: Compose applies a file as written, `privileged`, host bind mounts, `network_mode: host`, and host `provider` hooks included, so a nested include you never read grants all of it. Review the `docker compose config` output, which resolves includes, extends, overrides, and interpolation into one model, and pin a remote include to a digest.

Merge rules that decide what production actually runs:

| Field kind | Merge behaviour |
|---|---|
| Single value (`image`, `command`, `mem_limit`) | the later file replaces the value |
| `ports`, `expose`, `dns`, `tmpfs`, `env_file` | concatenated, so a removed port stays unless `!override`/`!reset` is used |
| `environment`, `labels` | merged by key, later value wins |
| `volumes`, `devices` | merged by container mount path |
| All relative paths | resolved against the first file given with `-f`, not against the file that contains them |

`!reset` removes a value the base file set (`ports: !reset []`, `environment: {FOO: !reset null}`); `!override` replaces a sequence instead of appending to it. Both are the only reliable way to take a published port away in an overlay.

## Remote Host

A single-host deploy reaches the server through the Docker socket, which is root-equivalent on that machine. Two supported ways:

```sh
docker context create prod --docker host=ssh://deploy@vps.example.com --description "production"
docker context use prod && docker info --format '{{.Name}} {{.ServerVersion}}'
# or per command, without a context:
DOCKER_HOST=ssh://deploy@vps.example.com docker info --format '{{.Name}} {{.ServerVersion}}'
```

- The SSH user must be able to reach the Docker socket on the remote host. Membership of the `docker` group is equivalent to root.
- `DOCKER_HOST` and `DOCKER_CONTEXT` override the selected context; the `--context` and `--host` flags override both. Always confirm with `docker info` which engine receives the command.
- `~/.ssh/config` with `ControlMaster auto`, `ControlPath`, and `ControlPersist yes` avoids a new SSH handshake per call, which matters for a deploy that issues dozens of them.
- TLS instead of SSH (`DOCKER_HOST=tcp://host:2376`, `DOCKER_TLS_VERIFY=1`, `DOCKER_CERT_PATH`) has the same authority model: anyone holding the client key can direct the daemon, so treat the key as a root password.
- Never run a writing command while the local `default` context is selected by accident. Confirm the context, then say which host and which project name the run targets.

## Validate And Deploy

Validate without changing anything, then deploy with a wait and a timeout.

```sh
docker compose -f compose.yaml -f compose.production.yaml config -q
docker compose -f compose.yaml -f compose.production.yaml config --images --services --profiles
docker compose -f compose.yaml -f compose.production.yaml --dry-run up -d
docker compose -f compose.yaml -f compose.production.yaml pull
docker compose -f compose.yaml -f compose.production.yaml up -d --wait --wait-timeout 180 --remove-orphans
```

| Command | What it proves |
|---|---|
| `config -q` | The files parse, merge, and interpolate, and every `${VAR:?}` has a value; `--images --services --profiles` names what the run touches |
| `--dry-run up -d` | The plan: what would be created, pulled, and started, with no state change |
| `pull`, then `up -d --wait --wait-timeout` | The images are reachable with the current credentials before anything stops, and then every container is running and healthy, or the command fails at the timeout |

- `config -q` with every `-f` flag the deploy uses, in the same order. A validation on the base file alone validates a model that will not run.
- `--dry-run` is a global Compose flag; keep it in front of the subcommand. A `pull` first turns "image not found" or an expired credential into a pre-deploy error instead of a half-replaced stack.
- `--wait` implies detached mode and `--wait-timeout` bounds it; without the timeout a service that never becomes healthy hangs until the client gives up.
- `--remove-orphans` removes containers of services deleted from the file. It is safe when the project name is right and destructive of unrelated containers when it is not.
- Name the project explicitly (`-p <project>`, or the top-level `name`) so a deploy cannot adopt containers from another directory's project.
- Expect a short gap on restart. Compose stops the old container and starts the new one unless a proxy or a rolling deploy tool sits in front, and there is no zero-downtime guarantee.

## Success Test

Compose reports success only when every service is running and, where a health check exists, healthy.

```sh
docker compose -f compose.yaml -f compose.production.yaml ps --format json
```

- Every service in the output must have `"State": "running"`, and `"Health": "healthy"` for each service that defines a health check. `"Health": ""` means the service has no health check.
- The exit code of `up --wait` covers the same condition but must be read with the process list: a service that exited `0` after the wait window is a failure the exit code no longer shows. Then request the app through its published address, using the same health endpoint the container probes.

Without a healthcheck, `--wait` only confirms the service is running.

That sentence is the whole trap: a service with no `healthcheck` produces no healthy state, so `up --wait` returns as soon as the container is up, and an app that crashes one second later, or answers 500, was "successfully deployed". On a stack whose services lack health checks, treat `up --wait` as a start check and add an explicit request before claiming the deploy.

## Status And Logs

| Question | Command |
|---|---|
| Current state of every container, or only the running ones | `docker compose ps --all --format json`, `docker compose ps --status=running` |
| Why a container stopped | `docker inspect --format '{{.State.Status}} {{.State.ExitCode}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' <container>` |
| Last health probe output | `docker inspect --format '{{json .State.Health}}' <container>` |
| Bounded logs for one service; recent events including restarts and OOM | `docker compose logs --no-color --tail=200 --since=15m <service>`, `docker compose events --json --since=30m` |
| Which host port a service really publishes, and what runs inside it | `docker compose port <service> 8080`, `docker compose top` |

Exit codes that decide the diagnosis: `0` for a long-running service means the command finished, so the process forked or the entrypoint returned; `137` is `SIGKILL` from the OOM killer or a stop that outlived its grace period; `143` is `SIGTERM`, the normal stop.

A container that is `running` with no traffic is missing a health check, bound to `127.0.0.1` inside the container, or publishing another port; `docker compose port` answers the last one.

## Change And Redeploy

| Change | Command | Caveat |
|---|---|---|
| New image for one service | `docker compose build web && docker compose up --no-deps -d web` | `--no-deps` leaves dependencies alone, including connections and DNS entries the service cached; use it only when the dependency addresses did not change |
| New environment value or config | `docker compose up -d <service>` | `restart` does not apply Compose changes at all; a variable changed in the file needs a recreate |
| Everything recreated | `docker compose up -d --force-recreate` | Recreates containers whose image and configuration did not change, so every service has a gap |
| Dependency images changed too | `docker compose up -d --always-recreate-deps <service>` | Recreates the dependencies with the service, which is what `--no-deps` avoids |
| Only re-read the file | `docker compose config -q` | Validation, no state change |

- `docker compose restart` restarts the existing containers with their existing configuration, so file changes are not picked up; use `up -d` when the file changed.
- `--force-recreate` scope is the *selected services*. Without a service argument it is the whole project, which is a full-stack gap; pass the service names.
- `up -d <service>` without `--no-deps` also recreates the dependencies whose configuration changed, which is usually what you want after editing a shared base.
- An image tag that stays the same after a rebuild needs `--pull always` or a digest change, or the host keeps the old image. Tag by Git SHA and the problem disappears.

## Rollback

Compose has no atomic rollback. The real mechanism is the previous image tag plus another `up -d`:

```sh
TAG=<previous-sha> docker compose -f compose.yaml -f compose.production.yaml up -d --wait
```

- State this before running it: the deploy restores the *previous image and configuration*; it does not restore database contents, named volumes, uploaded files, or anything a migration changed. If the previous version cannot read the migrated schema, the rollback needs a forward fix or a database restore, and the restore is a separate approval.
- The `deploy:` `rollback_config` belongs to Swarm and other orchestrators; plain Compose ignores it, so it is never offered as a rollback plan. The previous tag must still exist, which is why the tag is the Git SHA. Prefer a forward fix when a failed deploy left the previous container serving; a failed build or `pull` never touched the running stack.

## Failure Table

| # | Signature | Cause | Fix | Check | Tier | Source |
|---|---|---|---|---|---|---|
| 1 | `dependency failed to start: container … is unhealthy` | A `service_healthy` dependency never became healthy | Read `State.Health.Log`, fix the probe or raise `start_period` | `compose ps --format json` shows `"Health": "healthy"` | proceed | <https://docs.docker.com/compose/how-tos/startup-order/> |
| 2 | `up --wait` returned, the app answers 500 or is dead | No health check defined, so the wait only saw `running` | Add a `healthcheck` and re-run with `--wait` | `ps --format json` shows a health status, and the wait fails on an unhealthy service | proceed | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| 3 | Variable is empty in the container | Set in `.env` but not passed through `environment:` or `env_file:`; or set in the wrong file | Pass it through `environment:`, and confirm with `docker compose config --environment` | `docker inspect --format '{{json .Config.Env}}' <container>` shows the value | proceed | <https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/> |
| 4 | A changed variable has no effect after `restart` | `restart` keeps the existing container configuration | `docker compose up -d <service>` to recreate | the new value appears in `docker inspect` | proceed | <https://docs.docker.com/reference/cli/docker/compose/restart/> |
| 5 | Published port unreachable from outside, works on the host | Docker's published ports bypass ufw's `INPUT` chain, or the bind is `127.0.0.1` | Publish on `127.0.0.1` and put a proxy in front, or open the cloud firewall/security group | request from outside the host succeeds | explicit approval (firewall change) | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| 6 | Container `running`, nothing answers | The app binds `127.0.0.1` inside the container, or listens on another port than the one published | Bind `0.0.0.0`, align `ports` with the real port | `docker compose port <svc> <port>` and a `curl` from the host | proceed | <https://docs.docker.com/reference/compose-file/services/> |
| 7 | Secret is readable in `docker inspect` output | Passed as an environment variable instead of a secret | Move it to `secrets:` and use the `_FILE` convention where the image supports it | `docker inspect` shows a path, not the value | explicit approval if the value must be rotated | <https://docs.docker.com/compose/how-tos/use-secrets/> |
| 8 | A published port reappears after an overlay meant to remove it | Sequence fields are concatenated, not replaced | `ports: !reset []` or `ports: !override [...]` in the overlay | `docker compose config` shows only the intended ports | proceed | <https://docs.docker.com/reference/compose-file/merge/> |
| 9 | Container exits `137` repeatedly | Out of memory | Raise the container limit or reduce memory, and confirm with `docker compose events --json` | no OOM event for 30 minutes | explicit approval if it raises a resource limit with cost | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| 10 | Compose applies settings nobody wrote, or warns about remote sources | A remote `include` or `extends` resolved into the model | Read `docker compose config` output in full; pin the remote reference to a digest | the resolved model matches the reviewed configuration | explicit approval if the remote content must be replaced | <https://docs.docker.com/compose/trust-model/> |

## Approval Required

| Action | Tier |
|---|---|
| `config -q`, `config --environment`, `config --images`, `--dry-run up`, `pull`, `ps`, `logs` with a bound, `docker inspect`, `compose port`, `compose top`, editing Compose files in the repository | proceed |
| `up -d`, `build`, `--force-recreate`, `restart`, `down` without `-v` in a non-production project | proceed |
| The same in production | named environment |
| `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, `down --rmi`, removing a named volume from the file, a `!reset` of a volume, a migration service against real data, publishing a new public port, a firewall or DNS change, a rollback that would need a database restore | explicit approval |
| Logging in, creating a host or an account, installing Compose globally, printing a secret from `.env`, `env_file`, or `docker inspect` | never |

`docker compose down -v` deletes the named volumes declared in the file and the anonymous volumes attached to the containers. The database, the uploads, and the queue state go with them, and nothing in the stack can rebuild them. State the volume names and what is in them before asking, and never run it as cleanup after a failed deploy.

## Checked

> Volatile. Checked 2026-11-07 against the sources below and the local CLI; re-read the page when a flag or a default decides the run.

| Fact | Value |
|---|---|
| Local CLI | Docker 27.3.1, Compose v2.30.3-desktop.1, buildx v0.18.0-desktop.2 |
| `--wait` / `--dry-run` | `--wait` implies detached mode and waits for running or healthy, bounded by `--wait-timeout`; `--dry-run` is global and prints the plan with no state change |
| Env order | interpolation: shell > `--env-file` > project `.env`. Container: `run -e` > interpolated `environment`/`env_file` > `environment` > `env_file` > image `ENV` |
| Secrets | Read-only at `/run/secrets/<name>`, Linux containers only; `environment` source unsupported by `docker stack deploy` |
| Merge / `version` | Single values replaced, `ports`/`expose`/`dns`/`tmpfs` concatenated, `environment`/`labels` merged by key, `volumes` merged by mount path, `!reset`/`!override` otherwise; the top-level `version` key is obsolete and warns |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Use an additional `compose.production.yaml` for production differences; redeploy one service with `build web` then `up --no-deps -d web` | <https://docs.docker.com/compose/how-tos/production/> |
| `--wait` waits for running or healthy and implies detached mode; `--wait-timeout` bounds it; `--force-recreate`, `--no-deps`, `--remove-orphans`, `--always-recreate-deps` | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| `config` merges, resolves, and validates, with `-q`, `--images`, `--services`, `--profiles`, `--environment`; Dry Run mode tests a command without changing the stack | <https://docs.docker.com/reference/cli/docker/compose/config/>, <https://docs.docker.com/reference/cli/docker/compose/> |
| Compose does not wait for readiness on start; `condition: service_healthy` and `service_completed_successfully`; `restart: true` on a dependency | <https://docs.docker.com/compose/how-tos/startup-order/> |
| Short-form `depends_on` does not wait for healthy | <https://docs.docker.com/reference/compose-file/services/> |
| Interpolation precedence: shell, `--env-file`, project `.env`; `${VAR:?error}`; `config --environment` | <https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/> |
| Container precedence: `run -e`, interpolated `environment`/`env_file`, `environment`, `env_file`, image `ENV` | <https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/> |
| Secrets mount at `/run/secrets/<name>`, are granted per service, Linux only, `_FILE` convention; sources are `file` or `environment`, and `environment` is unsupported by `docker stack deploy` | <https://docs.docker.com/compose/how-tos/use-secrets/>, <https://docs.docker.com/reference/compose-file/secrets/> |
| Merge rules, paths relative to the base file, `!reset`, `!override` | <https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/>, <https://docs.docker.com/reference/compose-file/merge/> |
| Core services should not carry profiles | <https://docs.docker.com/compose/how-tos/profiles/> |
| Compose treats every file as trusted; includes and extends can carry privileged settings, name conflicts warn instead of merging, and remote references belong pinned to a digest | <https://docs.docker.com/compose/trust-model/>, <https://docs.docker.com/reference/compose-file/include/> |
| `restart` does not reflect changes to the Compose file; `ps --format json` emits `State`, `Health`, `ExitCode` per container; `logs` takes `--tail`, `--since`, `--no-color`; `down -v` removes named and anonymous volumes; `pull` fetches images without starting containers | <https://docs.docker.com/reference/cli/docker/compose/restart/>, <https://docs.docker.com/reference/cli/docker/compose/ps/>, <https://docs.docker.com/reference/cli/docker/compose/logs/>, <https://docs.docker.com/reference/cli/docker/compose/down/>, <https://docs.docker.com/reference/cli/docker/compose/pull/> |
| Contexts and `DOCKER_HOST`/`DOCKER_CONTEXT` precedence; the SSH context, the remote user's socket access, and TLS keys being root-equivalent | <https://docs.docker.com/engine/manage-resources/contexts/>, <https://docs.docker.com/engine/security/protect-access/> |
| Docker's published ports bypass ufw's `INPUT`/`OUTPUT` chains | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| `exited=137` is a `SIGKILL` | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `deploy.rollback_config` is orchestrator behaviour, not Compose rollback | <https://github.com/compose-spec/compose-spec/blob/main/deploy.md> |
| The `version` top-level element is obsolete and produces a warning | <https://github.com/compose-spec/compose-spec/blob/main/04-version-and-name.md> |
| State exactly what a destructive Docker command deletes and get explicit confirmation | <https://github.com/docker/skills> |

### Evidence grade

`DIRECT` for the CLI surface: Compose v2.30.3 and Docker 27.3.1 were present on 2026-11-07 and every flag above was read from `--help`. `SECONDARY` for the merge and precedence tables, the trust model, and the secret semantics, which are quoted from Docker's and compose-spec's documentation and were not exercised against a live multi-file project here. The absence of an atomic rollback is a design property of single-host Compose, not a version fact; it stays true while the `deploy:` rollback settings remain orchestrator-only.
