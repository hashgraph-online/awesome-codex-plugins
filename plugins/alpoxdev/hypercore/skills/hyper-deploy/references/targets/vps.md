# VPS (A Server You Manage)

Target guide for a Linux server you reach yourself, with or without Docker: Kamal, Coolify, Dokploy, a proxy plus `docker rollout`, or systemd behind Caddy. Read it after `rules/target-detection.md` routes here. When the repository also carries a compose file, read [compose.md](compose.md) as the second guide.

Most failures here are not build failures. They are a container bound to a loopback address, a health check that cannot run inside the image, an image built for the wrong CPU, a missing secret, or a published port that bypasses the firewall.

## Contents

- Choose The Path
- Kamal
- Coolify And Dokploy
- Proxy And TLS
- Server Baseline
- Diagnosis Order
- Failure Table
- Approval Required
- Checked
- Sources

## Choose The Path

Decide from what the server already runs, not from preference. Record the deciding fact in the target line.

| Order | Condition on the server and repository | Path | Why |
|---|---|---|---|
| 1 | Docker present, `Dockerfile` or compose in the repository, one app or a small set | Kamal (`config/deploy.yml`) | One configuration file holds the proxy, health check, rollback, and secrets; zero-downtime replacement and rollback are built in |
| 2 | Several apps and domains on one server, and a GUI is wanted | Coolify (`Authorization: Bearer`) or Dokploy (`x-api-key`) | The panel owns the proxy and per-app settings; deployments trigger over an API |
| 3 | Compose already is the asset, no control panel, and a proxy can sit in front | Caddy or Traefik plus `docker rollout <service>` | Scale to two instances, wait for healthy, remove the old container; no panel to run |
| 4 | The app is not containerised | systemd unit plus Caddy reverse proxy | Keep the process under a unit and terminate TLS in the proxy |

Rules that apply to every path:

- `docker rollout` needs a proxy and refuses a service that declares `container_name` or `ports`; two containers cannot share one name or one host port.
- Kamal replaces the v1 Traefik setup with `kamal-proxy`. Configuration copied from a v1 article (`traefik` keys, `.env` for secrets, `app_port: 3000`) breaks on Kamal 2.
- Coolify and Dokploy treat "Docker Swarm" differently: Dokploy is built on Swarm, Coolify marks Swarm as deprecated for scaling. Do not carry one tool's advice into the other.
- Before any path: confirm the image architecture matches the host, the app binds `0.0.0.0`, a health endpoint exists, the secrets are present, 80 and 443 are open, DNS A/AAAA point at the host, and a backup exists.

## Kamal

`config/deploy.yml` is canonical; `config/deploy.<destination>.yml` merges over it and is selected with `-d <destination>`. Kamal rejects unrecognised keys, so a typo fails loudly instead of being ignored.

| Key | Use |
|---|---|
| `service`, `image` | Container name prefix and image repository |
| `servers` | Hosts, or roles with their own hosts |
| `registry` | Username plus a password read from a secret name |
| `env.secret` | Names read from `.kamal/secrets`, never inline values |
| `proxy.host` / `proxy.hosts` | Hostnames the proxy routes; without one, all requests are forwarded |
| `proxy.app_port` | Port the container exposes, default `80` |
| `proxy.ssl` | Automatic HTTPS through Let's Encrypt; needs one server and `host` set |
| `proxy.healthcheck.path`, `interval`, `timeout` | Default path `/up`, hit once a second until the deploy timeout |
| `builder.arch` | `amd64` or `arm64`; set it when the host differs from the build machine |
| `builder.remote` | `ssh://docker@builder` for builds that do not match the local architecture |
| `readiness_delay` | Seconds after the container runs before readiness, default `7`; applies only without a proxy or health check |
| `deploy_timeout` | Seconds to wait for readiness, default `30` |
| `drain_timeout`, `stop_timeout` | Seconds to drain and to stop after `SIGTERM` |
| `retain_containers` | Old containers and images kept, default `5` |
| `accessories.<name>` | Databases and caches, managed separately from the app |

Deploy order is the diagnosis order: registry login, build and push, pull, ensure `kamal-proxy`, start the new container, switch traffic when `GET /up` answers `200 OK`, stop the old container, prune. A failure before the switch leaves the previous version serving; a failure after it is a runtime problem, not a deploy problem.

Secrets moved in Kamal 2 from `.env` and `.env.rb` to `.kamal/secrets`, plus `.kamal/secrets-common` and `.kamal/secrets.<destination>`. Values are `$ENV_VAR` or a command substitution such as `$(op read ...)`. `.env` is not loaded automatically any more, and values from `.kamal/secrets` are not exported into the configuration either.

```sh
kamal deploy -d staging            # build, push, release, switch
kamal deploy --lock-wait           # poll for the deploy lock instead of failing at once
kamal app version                  # what is running now
kamal app details                  # container state per host
kamal details                      # app plus proxy plus accessories
kamal app logs -n 200              # bounded runtime log
kamal app containers -q            # image tags still available for rollback
kamal audit                        # audit log from the servers
```

- A deploy that takes the lock automatically fails immediately when another deploy holds it; `--lock-wait` polls instead (`--lock-wait-timeout`, default 900, and `--lock-wait-interval`, default 15). A lock taken manually with `kamal lock acquire` is never waited on.
- `kamal rollback <sha>` restores the previous image only. State it as a production action that needs explicit approval in this run, and state that databases, volumes, and migrations are not restored. Old containers are pruned after 3 days by default, so a later rollback target may no longer exist.
- Accessories are not updated by `kamal deploy` and have no zero-downtime deployment. A migration that restarts a database accessory is a planned interruption, not a rolling one.
- Never run `kamal config` for diagnosis. It prints the combined configuration including secrets.

## Coolify And Dokploy

Both panels deploy over an API. The trigger only queues work.

| Panel | Trigger | Auth header | Response meaning |
|---|---|---|---|
| Coolify | `GET /api/v1/deploy?uuid=<uuid>&force=false`, or `POST` with `{"uuid":"...","force":false}` | `Authorization: Bearer $COOLIFY_TOKEN` | A queued deployment UUID; the deployment page must show it finish |
| Dokploy | `POST /api/application.deploy` with `{"applicationId":"..."}` | `x-api-key: $DOKPLOY_API_KEY` | An accepted call; `application.one` reports `applicationStatus` / `composeStatus` as `idle`, `running`, `done`, or `error` |

```sh
curl --fail-with-body --header "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/api/v1/deploy?uuid=$COOLIFY_UUID&force=false"
curl --fail-with-body --request POST "$DOKPLOY_URL/api/application.deploy" \
  --header "x-api-key: $DOKPLOY_API_KEY" --header 'Content-Type: application/json' \
  --data '{"applicationId":"'"$DOKPLOY_APP_ID"'"}'
```

- An accepted request is not a success. Coolify says explicitly not to treat an accepted API request as proof that every resource became healthy. Read the deployment record, then the health check, then the URL.
- Coolify builds from source before it touches the running container, so a failed build leaves the current version serving. A rolling replacement needs a health check; with host port mappings, a fixed container name, or a preview it falls back to stop-then-start and briefly drops traffic.
- Dashboard-configured HTTP checks run inside the application container. The final image must contain `curl` or `wget`; installing either on the host alone is not enough, and without one the container is always unhealthy. A `HEALTHCHECK` in the Dockerfile takes precedence for a non-Compose Dockerfile app.
- Dokploy stops the current container and starts the new one by default, which produces a Bad Gateway on every deploy. Zero downtime needs a Swarm health check plus `"FailureAction": "rollback"` and `"Order": "start-first"` in the update configuration; the check runs inside the container (`curl -f http://localhost:<port>/health`), so the image needs `curl`.
- Dokploy's Volume Backups work only with Docker named volumes. A `../files` bind mount, or an absolute host path (which Dokploy cleans up during deployments), cannot be backed up that way.
- Reading `composeStatus` needs `applicationId`; reading it proves a state, not that a health check passed. Neither panel documents a general deployment-status endpoint that returns the terminal result together with a health verdict, and this guide did not verify one. State that limit instead of inventing a poll.
- A rollback in either panel swaps an image. It does not reverse a migration, restore a volume, or change an external service. Kamal behaves the same way.

## Proxy And TLS

Caddy provisions HTTPS automatically once all of these hold: the domain's A/AAAA records point at the server, ports 80 and 443 are open externally, Caddy can bind or receive those ports, the data directory is writable and persistent, and the hostname appears in the configuration. It redirects HTTP to HTTPS by default. A wildcard certificate needs the DNS-01 challenge; the default HTTP-01 and TLS-ALPN challenges cannot issue one.

```caddyfile
app.example.com {
  reverse_proxy 127.0.0.1:3000 {
    health_uri /health
    health_interval 5s
    lb_try_duration 15s
  }
}
```

Active health checks need `health_uri` or `health_port`. `lb_try_duration` keeps a request retrying across backends for that window, which is what covers a container swap. Caddy has no Docker label discovery built in; address the container by service name and port, or by a loopback published port.

Traefik discovers containers through Docker labels (`traefik.http.routers.<name>.rule`, `traefik.docker.network`, `traefik.http.services.<name>.loadbalancer.server.port`). `providers.docker.exposedByDefault` defaults to `true`, so a container with no labels can still become routable; set it to `false` and label deliberately. Mounting `docker.sock` gives the proxy control over the Docker daemon, which is root-equivalent on that host: read-only mounts still expose the API, so prefer a socket proxy and never publish the socket over TCP.

ACME needs Let's Encrypt to reach the host: HTTP-01 through port 80, TLS-ALPN-01 through port 443. A proxy that terminates TLS must be the only thing on those ports.

## Server Baseline

- Docker publishes a container port on all interfaces by default and diverts that traffic in the `nat` table before ufw's `INPUT` chain, so a ufw rule blocking the port does not block it. Either bind the published port to loopback (`-p 127.0.0.1:3000:3000`) and let only the proxy out, or add rules to the `DOCKER-USER` chain, which is processed before Docker's own accept rules. Do not edit Docker's generated chains.
- ufw is disabled by default on Ubuntu. Read `sudo ufw status verbose` before claiming a host is firewalled; "ufw is enabled" is an assumption until that line says `Status: active`.
- SSH: key-only login, and root restricted. `PasswordAuthentication no` and `PermitRootLogin prohibit-password` (or `without-password`) are practice rather than a quote from a page; verify with `sudo sshd -t` before restarting `sshd`, because a broken config can lock out the only way in. Kamal connects as root over SSH with a key by default, so a password-only automation elsewhere stops working when keys become mandatory.
- Back up what cannot be rebuilt: named volumes or the database's own dump, `.kamal/secrets`, the panel's `.env` (Coolify asks for `/data/coolify/source/.env`), and the proxy's certificate store. A backup that has never been restored is a guess.
- Keep the build off a small production host where possible: build in CI, push to a registry, and let the host only pull and run.

## Diagnosis Order

Read in this order and stop as soon as the cause is visible:

1. What is serving now: `kamal app version` or `kamal details`, `docker compose ps`, or the panel's current deployment state. A failed deploy usually leaves the previous version running.
2. The deploy log of the failed attempt: Coolify or Dokploy deployment logs, `kamal deploy -v` output, `docker compose` output.
3. Container state and health on the host: `docker ps -a`, `docker inspect --format '{{.State.Health.Status}} {{.State.ExitCode}}'`, then `docker logs <container> --tail 200`.
4. The proxy path: `kamal proxy logs`, `docker logs coolify-proxy --tail 50`, `journalctl -u caddy -n 100`, and `curl -I https://<host>` for the TLS and redirect chain.
5. From inside the network: `docker exec <container> curl -fsS localhost:<port>/health`, then `curl -fsS https://<host>/health` from outside.
6. Host resources when nothing above explains it: `df -h`, `free -m`, `dmesg -T | grep -i -E 'oom|killed process'`.

A fix and redeploy comes before a rollback: the failed deploy usually did not replace anything. Count one attempt per redeploy for the same root cause, at most three.

## Failure Table

| # | Signature | Cause | Fix | Check |
|---|---|---|---|---|
| 1 | Proxy returns 502/503, `Connection refused`, Coolify `No available server` | App binds `localhost` or `127.0.0.1` only | Bind `0.0.0.0`, align the internal port with the proxy and the health check | `docker exec <c> curl -fsS localhost:<port>/health` returns 0, then the public URL returns 200 |
| 2 | 502, health check unhealthy, no app error | Port mismatch between the app, `proxy.app_port`, Coolify `Ports Exposes`, or the compose `expose` | Fix the port in one place and redeploy | `docker port <c>`, then the public URL returns 200 |
| 3 | `(unhealthy)`, health check exit `127` | `curl` or `wget` missing from the final image | Install one in the image, or switch to a command check | `docker exec <c> curl -f localhost:<port>/health; echo $?` prints 0 |
| 4 | Deploy times out at `deploy_timeout` / `StartPeriod` | Slow start, wrong path, or too short a readiness window | Raise `readiness_delay`, `deploy_timeout`, or `start_period` after checking the startup log timing | Deploy completes and `GET /up` returns 200 |
| 5 | `DATABASE_URL is not set`, auth failure, empty variable | Secret missing from `.kamal/secrets`, the panel environment, or the compose env; or set without a redeploy | Add it in the source the path reads, then redeploy | The app log shows the value loaded and a smoke request passes |
| 6 | `no buildpack`, `start command not found` | Builder auto-detection picked the wrong strategy | Commit a `Dockerfile` and point the build at it | The deploy log shows Dockerfile build steps |
| 7 | `exec format error`, `no matching manifest` | Image built for the wrong architecture | Build with `--platform linux/amd64` or set `builder.arch`, and use `builder.remote` when the local machine differs | `docker inspect --format '{{.Architecture}}' <image>` matches the host |
| 8 | Exit code 137, `Killed process`, `Out of memory` | Memory limit or host memory exhausted, often during a build on the host | Raise memory or move the build to CI; Dokploy recommends a separate build server | `docker stats` stable after redeploy |
| 9 | Migration error in the deploy log, crash loop | Migration runs inside the release and fails midway | Move it to a separate release step with a backward-compatible schema | App starts and the schema version is the expected one |
| 10 | `no space left on device` | Images, build cache, and stopped containers accumulated | `docker image prune`, `kamal prune`, or the panel's Docker cleanup | `df -h` has headroom |
| 11 | ACME challenge fails, `NXDOMAIN`, no certificate | DNS not pointing at the host, 80/443 closed, or propagation pending; a wildcard without DNS-01 | Correct A/AAAA, open the ports, wait, add DNS-01 for a wildcard | `dig +short A <host>`, `curl -vI https://<host>` shows a valid chain |
| 12 | A port ufw blocks still answers from the internet | Docker publishes on `0.0.0.0` and routes before ufw's `INPUT` chain | Bind to `127.0.0.1` or filter in `DOCKER-USER` | `nc -z <host> <port>` from outside fails |
| 13 | `client version 1.24 is too old` in the proxy log | Proxy's Docker client is older than the daemon's API | Upgrade the proxy to a release that supports the daemon API | Proxy log clean and the URL answers 200 |
| 14 | Deploy fails at once with a lock message | Another deploy holds the Kamal lock | `kamal deploy --lock-wait`, adjusting `--lock-wait-timeout` | The deploy completes |

## Approval Required

| Action | Tier |
|---|---|
| Reading state, deploy logs, container state and health, proxy logs, `kamal app version`, `kamal details`, `kamal app logs`, `docker compose ps`, `curl` checks, editing `config/deploy.yml` or a compose file in the repository | proceed |
| `kamal setup`, `kamal deploy`, `kamal redeploy`, a Coolify or Dokploy deploy trigger, `docker rollout`, a systemd restart, all in a non-production environment | proceed |
| The same commands in production | named environment |
| `kamal rollback`, a panel rollback, `kamal remove`, `kamal accessory remove`, `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, a schema down-migration or a restore against real data, a volume or database deletion, a DNS record change, a firewall rule change, blocking panel access on port 3000 (`docker service update --publish-rm`), overwriting a registry tag | explicit approval |
| Logging in, creating an account or project, installing a global CLI, printing a token or `kamal config` output into chat or a report | never |

Every rollback proposal states what it restores (an image) and that databases, volumes, migrations, and bound resources are not restored. Approval covers the one action it names.

## Checked

> Volatile. Checked 2026-11-07 against the sources below; re-read the live page when a decision depends on a flag, a default, or a plugin.

| Fact | Value |
|---|---|
| Kamal current release | v2.12.0 (2026-06-18) |
| Kamal proxy | `kamal-proxy` replaced Traefik in Kamal 2; `app_port` defaults to 80 |
| Kamal readiness | `/up` polled once a second; `readiness_delay` 7 s, `deploy_timeout` 30 s, `retain_containers` 5 |
| Kamal rollback window | old containers pruned after 3 days by default |
| Kamal lock wait | `--lock-wait-timeout` 900 s, `--lock-wait-interval` 15 s |
| Coolify health check | HTTP check runs inside the container; `curl` or `wget` required in the image |
| Coolify deploy API | `GET` or `POST /api/v1/deploy`, `Bearer` token with `deploy` permission; accepted is not healthy |
| Dokploy default replacement | stop-then-start, Bad Gateway until Swarm health check plus `start-first` |
| Dokploy API | `x-api-key`, `applicationStatus` / `composeStatus` in `idle`, `running`, `done`, `error` |
| Dokploy backups | named volumes only, not `../files` bind mounts |
| Docker and ufw | published ports bypass ufw's `INPUT` chain through the `nat` table |
| Traefik default | `exposedByDefault: true` |
| Caddy automatic HTTPS | A/AAAA plus open 80/443 plus writable data directory |
| `docker rollout` | needs a proxy; refuses `container_name` and `ports` on the target service |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Kamal connects over SSH as root with a key, installs Docker, and needs a registry | <https://kamal-deploy.org/docs/installation/> |
| Deploy switches traffic when `GET /up` answers `200 OK`, in that order | <https://kamal-deploy.org/docs/commands/deploy/> |
| `/up` is polled every second until the deploy timeout; `healthcheck` path and interval; `app_port` default 80; SSL needs one server and `host` | <https://kamal-deploy.org/docs/configuration/proxy/> |
| Unrecognised keys are rejected; destinations merge `config/deploy.<destination>.yml`; `readiness_delay`, `deploy_timeout`, `drain_timeout`, `stop_timeout`, `retain_containers` defaults | <https://kamal-deploy.org/docs/configuration/overview/> |
| Accessories are not updated by a deploy and have no zero-downtime deployment | <https://kamal-deploy.org/docs/configuration/accessories/> |
| `builder.arch` and `builder.remote` for builds that do not match the local architecture | <https://kamal-deploy.org/docs/configuration/builders/> |
| Secrets moved to `.kamal/secrets`; `.env` is no longer loaded | <https://kamal-deploy.org/docs/upgrading/secrets-changes/> |
| Traefik was replaced by `kamal-proxy` in Kamal 2 | <https://kamal-deploy.org/docs/upgrading/overview/> |
| `kamal rollback <sha>`; old containers are pruned after 3 days by default | <https://kamal-deploy.org/docs/commands/rollback/> |
| `kamal app logs`, `app details`, `app version`, `app containers` | <https://kamal-deploy.org/docs/commands/app/> |
| `--lock-wait`, `--lock-wait-timeout` 900, `--lock-wait-interval` 15; a manual lock is never waited on | <https://kamal-deploy.org/docs/commands/lock/> |
| `kamal config` shows the combined configuration including secrets | <https://kamal-deploy.org/docs/commands/view-all-commands/> |
| Latest Kamal release is v2.12.0, published 2026-06-18 | <https://api.github.com/repos/basecamp/kamal/releases/latest> |
| Coolify connects over SSH and prepares the server for Docker workloads | <https://coolify.io/docs/core/what-is-coolify> |
| Bearer token format, `deploy` permission, API access switch, 401 and 403 meanings | <https://coolify.io/docs/api/authorization> |
| Deploy webhook URL shape, `uuid`/`tag`/`force`, an accepted request is not proof of health | <https://coolify.io/docs/core/automation/deploy-webhooks> |
| A failed source build leaves the current version running; rolling versus stop-then-start conditions | <https://coolify.io/docs/core/build-deployment-model> |
| HTTP checks run inside the container and need `curl` or `wget` in the image | <https://coolify.io/docs/applications/configuration/health-checks> |
| `No available server` causes, including port mismatch and unhealthy containers | <https://coolify.io/docs/troubleshoot/applications/no-available-server> |
| A rollback deploys an older image and does not reverse migrations or restore persistent storage | <https://coolify.io/docs/applications/deployments/rollbacks> |
| Back up `/data/coolify/source/.env` | <https://coolify.io/docs/start-with-self-hosted> |
| Dokploy ports 80, 443, 3000; install requirements and Docker Swarm base | <https://docs.dokploy.com/docs/core/installation> |
| API token from `/settings/profile`, `x-api-key` header | <https://docs.dokploy.com/docs/api> |
| `application.deploy` takes `applicationId`; `application.one`; `applicationStatus` values | <https://docs.dokploy.com/docs/api/application> |
| Default deployment stops the running container first and produces Bad Gateway; Swarm health check for zero downtime | <https://docs.dokploy.com/docs/core/applications/zero-downtime> |
| Health check plus `FailureAction: rollback` and `Order: start-first` in production | <https://docs.dokploy.com/docs/core/applications/going-production> |
| Named volumes back up through Volume Backups; `../files` bind mounts do not; absolute host paths are cleaned up | <https://docs.dokploy.com/docs/core/docker-compose> |
| Swarm automatic rollback and registry-based manual rollback | <https://docs.dokploy.com/docs/core/applications/rollbacks> |
| `composeStatus` values `idle`, `running`, `done`, `error` | <https://docs.dokploy.com/docs/api/compose> |
| Automatic HTTPS prerequisites and the HTTP to HTTPS redirect | <https://caddyserver.com/docs/automatic-https> |
| `health_uri`, `health_interval`, `lb_try_duration` for active health checks and retries | <https://caddyserver.com/docs/caddyfile/directives/reverse_proxy> |
| Docker provider labels; `exposedByDefault` defaults to `true` | <https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/> |
| Let's Encrypt must reach the host on 80 for HTTP-01 and 443 for TLS-ALPN-01 | <https://doc.traefik.io/traefik/reference/install-configuration/tls/certificate-resolvers/acme/> |
| Published ports are diverted in the `nat` table before ufw's `INPUT` chain | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| `DOCKER-USER` is processed before Docker's own accept rules; do not edit Docker's chains | <https://docs.docker.com/engine/network/firewall-iptables/> |
| A publish without an address binds all interfaces, even when ufw blocks the port | <https://docs.docker.com/reference/cli/docker/container/run/> |
| Anyone who can drive the Docker daemon has root access to the host | <https://docs.docker.com/engine/security/protect-access/> |
| ufw is initially disabled; `ufw status verbose` | <https://documentation.ubuntu.com/server/how-to/security/firewalls/> |
| Default key-based SSH authentication; `sshd -t` before restarting | <https://documentation.ubuntu.com/server/how-to/security/openssh-server/> |
| Exited status 137 is a `SIGKILL` | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `docker rollout` scales out, waits, then removes old containers; caveats on `container_name`, `ports`, and the required proxy; drain hook | <https://raw.githubusercontent.com/wowu/docker-rollout/master/README.md> |
| `Type=exec` is recommended for long-running services | <https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html> |

### Evidence grade

`SECONDARY` for every vendor claim: each one is quoted from the publisher's own documentation read on 2026-11-07, and no command in this guide was exercised against a live server in this environment. `DIRECT` only for the Caddy, Docker, and Traefik defaults that the same pages state as table values (`app_port` 80, `exposedByDefault` true, ufw disabled). `[INFERENCE]` marks the sshd directives (`PasswordAuthentication no`, `PermitRootLogin prohibit-password`): Ubuntu's page documents key-based authentication and `sshd -t`, not those two lines, so treat them as practice and verify on the host before locking anyone out. Panel deployment-state polling beyond `applicationStatus` is `UNVERIFIED`: neither Coolify nor Dokploy documents an endpoint that returns a terminal deployment result with a health verdict, so a run states the limit and reads the panel's deployment record instead. The Docker and ufw facts rest on Docker's own documentation stating the ufw `INPUT` bypass and naming the `DOCKER-USER` chain; the rules were not exercised on a live host here.
