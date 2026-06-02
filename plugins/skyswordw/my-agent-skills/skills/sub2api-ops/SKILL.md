---
name: sub2api-ops
description: Use when operating or debugging a Sub2API deployment, including SSH access, Docker Compose health, account cooldowns, OpenAI OAuth 403 or temp_unschedulable incidents, model routing, logs, upgrades, and service documentation.
---

# Sub2API Ops

## Scope

Use this skill for Sub2API operations in a documented server-ops repository. Adapt the placeholders to the target repository's machine and service docs before running commands:

- service doc: `services/sub2api.md`
- machine doc: `machines/<host>.md`
- SSH alias: `<sub2api-host-alias>`
- runtime directory: `/opt/example/sub2api/deploy`
- compose file: `docker-compose.local.yml`

Do not copy secrets, account tokens, OAuth refresh tokens, API keys, or live `.env` values into tracked docs or responses.

## Read First

1. `services/sub2api.md`.
2. `machines/<host>.md`.
3. If OpenClaw, Codex, or OpenAI-compatible routing is involved, read the caller service docs too.
4. For secrets, use documented local or remote secret paths only; never paste secret values into Git-tracked files.

## Health Check Order

Run on the target host:

```bash
ssh <sub2api-host-alias>
cd /opt/example/sub2api/deploy
docker compose -f docker-compose.local.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -sSI http://127.0.0.1:<local-port>/ | head
docker inspect <sub2api-container> --format '{{ index .Config.Labels "org.opencontainers.image.version" }} {{ index .Config.Labels "org.opencontainers.image.revision" }}'
docker compose -f docker-compose.local.yml logs --tail=200 <sub2api-service>
```

Do not call a service outage until container health and local HTTP behavior have been checked.

## Account Cooldown Incidents

For symptoms like `no available accounts`, `temp_unschedulable`, `OpenAI 403`, or a single account not scheduling:

1. Separate account-level state from whole-service health.
2. Inspect the named account first if the user provides one.
3. Check cooldown fields such as `temp_unschedulable_*` and recent operation/error logs.
4. Treat OpenAI OAuth 403 as potentially temporary until logs prove permanent disablement.

Remote DB commands should run inside the Postgres container with the configured user and database, not as host root:

```bash
cd /opt/example/sub2api/deploy
docker compose -f docker-compose.local.yml exec <postgres-service> sh -lc \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select now();"'
```

Keep quoting simple. Avoid snippets that expand JSON, email addresses, or tokens in the wrong shell.

## Upgrade Flow

There are usually two layers:

- app binary/runtime update through the upstream update mechanism;
- Docker image/runtime alignment through `docker compose pull` and recreate.

After using an app-level update mechanism, still verify Docker state:

```bash
cd /opt/example/sub2api/deploy
docker compose -f docker-compose.local.yml pull <sub2api-service>
docker compose -f docker-compose.local.yml up -d --force-recreate <sub2api-service>
docker inspect <sub2api-container> --format '{{ index .Config.Labels "org.opencontainers.image.version" }} {{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

Back up local compose and environment files before risky changes:

```bash
cp -a docker-compose.local.yml "docker-compose.local.yml.pre-update-$(date -u +%Y%m%dT%H%M%SZ).bak"
cp -a .env ".env.pre-update-$(date -u +%Y%m%dT%H%M%SZ).bak"
```

## Routing Checks

For OpenAI-compatible or Codex gateway issues:

- `/v1/models` should return JSON; `/models` may be an HTML frontend depending on host routing.
- Use the service-specific test path instead of unrelated providers.
- When tracing across multiple gateways, inspect both caller config/logs and Sub2API host logs before proposing config changes.
- Keep raw request bodies and tokens out of tracked notes unless fully sanitized.

## Documentation Rules

Update `services/sub2api.md` when deployment directory, compose file, containers, local endpoint, upgrade method, DNS exposure, or secret placement changes. Update the relevant machine doc if SSH host, IP, alias, or reachability changes.
