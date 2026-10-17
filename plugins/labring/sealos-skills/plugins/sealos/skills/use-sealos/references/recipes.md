# Recipes: popular self-hosted apps on Sealos

Fast lane for known products. Store rows deploy via Path A; image rows deploy
via Path B with the listed ingredients. Treat image-row details as strong
starting points — confirm port/env against the project's compose file when a
deploy misbehaves.

## In the template store (Path A — use these names)

All 21 rows deployed end-to-end on usw-1 (2026-08-12); rows with required
args list them in Notes.

| Product | Template name | Notes |
|---|---|---|
| Metabase | `metabase` | |
| Twenty CRM | `twenty` | |
| Excalidraw | `excalidraw` | stateless |
| Chatwoot | `chatwoot` | pg + redis included |
| LibreChat | `librechat` | mongo + meilisearch included |
| Plausible Analytics | `plausible` | pg + clickhouse included; args: `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `DISABLE_REGISTRATION`, `SECRET_KEY_BASE` |
| Plane | `plane` | multi-service |
| PostHog | `posthog` | heavy; check quota first |
| Gitea | `gitea` | |
| Authentik | `authentik` | |
| Jellyfin | `jellyfin` | |
| Vaultwarden | `vaultwarden` | |
| NocoDB | `nocodb` | args: admin email + password |
| changedetection.io | `changedetection` | |
| Memos | `memos` | |
| Uptime Kuma | `uptime-kuma` | optional external MySQL arg |
| Penpot | `penpot` | multi-service |
| Budibase | `budibase` | multi-service; args: `admin_email`, `admin_password` |
| Rocket.Chat | `rocketchat` (or `rocketchat-micro`) | mongo included; args: `admin_username`, `admin_name`, `admin_email`, `admin_password` |
| Umami | `umami` | pg included |
| Immich | `immich` | heavy: server + ML + pgvector |

Always re-check with `store-list --search` — the store gains templates over
time, so an app listed below may have graduated to Path A.

## Image recipes (Path B)

All rows below were deployed end-to-end on usw-1 (2026-08-12): official image →
generated template → public URL responding. Sizes are validated starting
points, not minimums.

| Product | Image | Port | Persistence | Dependencies / critical env |
|---|---|---|---|---|
| Windmill | `ghcr.io/windmill-labs/windmill:main` | 8000 | — | pg (db `windmill` via init Job); `DATABASE_URL=postgres://...?sslmode=disable`, `MODE=standalone`, `BASE_URL`; give 1c/2Gi |
| Mealie | `ghcr.io/mealie-recipes/mealie:latest` | 9000 | `/app/data` | SQLite by default (pg optional); `BASE_URL=https://<public host>` |
| Miniflux | `miniflux/miniflux:latest` | 8080 | — | pg (db `miniflux`); `DATABASE_URL`, `RUN_MIGRATIONS=1`, `CREATE_ADMIN=1`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `BASE_URL` |
| Keila | `pentacent/keila:latest` | 4000 | — | pg (db `keila`); **runtime.exs hard-requires the full SMTP set at boot**: `MAILER_SMTP_HOST/PORT/USER/PASSWORD/FROM_EMAIL` (placeholders boot fine, mail won't send); `DB_URL`, `URL_HOST` (bare host), `URL_SCHEMA=https`, `URL_PORT=443`, `SECRET_KEY_BASE` (64 chars), `KEILA_USER`/`KEILA_PASSWORD` for a deterministic admin |
| LibreDesk | `libredesk/libredesk:latest` | 9000 | `/libredesk/uploads` | pg (db `libredesk`) + redis; **config.toml file, not env** — render it (initContainer) with db+redis creds and `encryption_key` (exactly 32 chars); start command: `--install --idempotent-install --yes && --upgrade --yes && run`; `LIBREDESK_SYSTEM_USER_PASSWORD` must be 10-72 chars with upper+lower+digit+special |
| Actual Budget | `docker.io/actualbudget/actual-server:latest` | 5006 | `/data` | none |
| Gatus | `twinproduction/gatus:latest` | 8080 | — | config file via ConfigMap at `/config/config.yaml`; runs on 100m/128Mi |
| Misskey | `misskey/misskey:latest` | 3000 | `/misskey/files` | pg (db `misskey`) + redis; render `/misskey/.config/default.yml` via initContainer onto a small PVC (needs db+redis passwords → can't be a ConfigMap); `id: 'aidx'`; WS ingress (`backend-protocol: WS`) |
| Stirling-PDF | `stirlingtools/stirling-pdf:latest` | 8080 | `/usr/share/tessdata` (optional) | none; `:latest` ships with login enabled → expect 401 on `/`, default creds `admin`/`stirling` |
| MeTube | `ghcr.io/alexta69/metube:latest` | 8081 | `/downloads` | none |
| Discourse | `bitnamilegacy/discourse:latest` | 3000 | `/bitnami/discourse` | **`bitnami/discourse` is gone from Docker Hub** (Broadcom archived Bitnami, 2025); `bitnamilegacy` is a frozen archive — flag this to the user, the alternative is Discourse's official launcher build (Path C). pg (db `discourse` + `CREATE EXTENSION hstore; pg_trgm`) + redis; sidekiq as second workload (same image, command `/opt/bitnami/scripts/discourse-sidekiq/run.sh`); `DISCOURSE_HOST/DATABASE_*/REDIS_*/USERNAME/PASSWORD/EMAIL`, `DISCOURSE_PRECOMPILE_ASSETS=no`; give main 2c/4Gi |
| Zabbix | `zabbix/zabbix-server-pgsql:latest` + `zabbix/zabbix-web-nginx-pgsql:latest` | web 8080 | — | pg (db `zabbix`; server auto-creates schema on first boot); two workloads; web needs `ZBX_SERVER_HOST=<server svc FQDN>` + `PHP_TZ`, both need `DB_SERVER_HOST/DB_SERVER_PORT/POSTGRES_*`; login `Admin`/`zabbix` |
| FreeScout | `tiredofit/freescout:latest` | 80 | `/data` | mysql (db `freescout`); `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS`, `SITE_URL=https://<public host>`, `ENABLE_SSL_PROXY=TRUE`, `ADMIN_EMAIL`/`ADMIN_PASS` |
| Apache Guacamole | `guacamole/guacamole:1.6.0` + `guacamole/guacd:1.6.0` | 8080 | — | pg (db `guacamole_db`); **pin web+guacd to the same version**; schema init Job: fetch `001-create-schema.sql` + `002-create-admin-user.sql` from the guacamole-client repo **at the matching tag** and `psql -f` them; env `GUACD_HOSTNAME=<guacd svc FQDN>`, `POSTGRESQL_HOSTNAME/PORT/DATABASE/USERNAME/PASSWORD`, `WEBAPP_CONTEXT=ROOT` (serve at `/` instead of `/guacamole/`); login `guacadmin`/`guacadmin` |
| Komga | `gotson/komga:latest` | 25600 | `/config` | none; JVM — give 1c/1Gi |
| Grocy | `lscr.io/linuxserver/grocy:latest` | 80 | `/config` | none; `PUID=1000`, `PGID=1000`, `TZ` |
| FreshRSS | `freshrss/freshrss:latest` | 80 | `/var/www/FreshRSS/data` | SQLite default; `CRON_MIN` for feed refresh; note the PVC name for the uppercase path must be lowercased (`vn-varvn-wwwvn-freshrssvn-data`) |
| Bagisto | `webkul/bagisto:latest` | 80 | `/var/www/bagisto/storage` | mysql (db `bagisto`); single container ships nginx+php; **with an external DB the entrypoint does NOT migrate** → initContainer (same image, same DB env, storage volume mounted): `mkdir -p storage/framework/{cache/data,sessions,views}`, retry `php artisan migrate --force` until MySQL is up, `php artisan db:seed --force` on first migrate only, and `chown -R www-data storage` **last** (root-run artisan drops root-owned cache files that php-fpm's www-data must rewrite per request — chown-then-migrate 500s); env `MYSQL_AUTOSTART=false`, `APP_URL`, `APP_KEY=base64:$(openssl rand -base64 32)`, `TRUSTED_PROXIES=*`, `DB_HOST/DB_PORT/DB_DATABASE/DB_USERNAME/DB_PASSWORD` |

## Composition patterns

- **Single container, no state** (Excalidraw-class): Deployment + Service +
  Ingress + App. Smallest ladder tier.
- **Single container + files** (Actual, Komga, MeTube): StatefulSet with one
  `volumeClaimTemplates` entry per write path.
- **App + database** (Miniflux, Keila, Umami-class): KubeBlocks block first,
  wire env via `secretKeyRef`; the app usually crash-loops once or twice
  while the database starts — that self-heals, don't intervene for ~3 min.
- **App + pg + redis** (Chatwoot, Misskey, LibreDesk): two KubeBlocks blocks;
  remember the Redis host is the fixed Service FQDN, not from the secret.
- **App + worker sharing one image** (Discourse, Chatwoot-class): second
  Deployment, same image and env, different command, no Service/Ingress.
- **Config-file apps, static content** (Gatus): ConfigMap with `vn-` keys +
  `subPath` mounts per [platform.md](platform.md).
- **Config-file apps that need database credentials** (Misskey, LibreDesk):
  a ConfigMap can't reference secrets, so add a small PVC volume plus a
  busybox initContainer that reads the credentials from `secretKeyRef` env
  and writes the config file onto that volume; the app container mounts the
  same volume at the config path.
- **Web + sidecar daemon** (Guacamole+guacd): separate Deployments; the web
  one talks to the daemon via Service FQDN.
- **Schema-init apps** (Guacamole, Discourse extensions): extend the pg init
  Job — after `CREATE DATABASE`, fetch versioned schema SQL (pin to the image
  version) or run `CREATE EXTENSION`, all idempotent.
