# Frappe / Bench Conversion Notes

Use this reference when a project mentions Frappe, ERPNext, HRMS, `bench`, `frappe/bench`, `frappe_docker`, or commands such as `bench new-site`, `bench start`, `bench set-mariadb-host`, or `bench set-redis-*`.

## Runtime Model

Frappe repositories are often app modules, not standalone web servers. Treat `docker/` compose files and init scripts as authoritative startup evidence.

Two common models:

- **Development bench model**: `frappe/bench:*` runs `bench init`, `bench get-app`, `bench new-site`, `bench install-app`, then `bench start`.
- **Prebuilt production image model**: `frappe/erpnext:*` or `ghcr.io/frappe/<app>:<tag>` already contains apps and normally uses separate web, frontend, websocket, worker, scheduler processes.

Do not mix these models blindly. If a repo's `docker/docker-compose.yml` uses `frappe/bench:latest` plus a mounted `init.sh`, do not assume a detected prebuilt GHCR image has the same startup contract.

## Template Rules

- Database services from Compose (`mariadb`, `mysql`, `redis`) should follow the Sealos database strategy. Redis must use the KubeBlocks Redis `Cluster` and its generated Secret (`${{ defaults.app_name }}-redis-redis-account-default`) unless the user explicitly asks for raw containers.
- If using a prebuilt Frappe image with mounted `sites` and `logs` PVCs, set pod `securityContext.fsGroup: 1000` so the `frappe` user can write mounted volumes.
- Init containers that run `bench init`, `bench new-site`, `bench migrate`, or app install steps must set explicit resources from the Sealos ladder. Do not rely on namespace defaults; `64Mi` memory is too small. Use at least:
  - light config init: `limits.memory: 256Mi`, `requests.memory: 25Mi`
  - `bench new-site` / app install / migrate: `limits.memory: 2048Mi`, `requests.memory: 204Mi`
  - choose matching ladder CPU values and derive CPU requests the same way, for example `limits.cpu: 500m` → `requests.cpu: 50m`
- Bootstrap scripts must be idempotent and recover from partial initialization:
  - create `sites/common_site_config.json` if a fresh PVC hides the image's bundled file
  - use `bench new-site --force` for first-site creation when the database may contain residue from a previous failed attempt
  - check both filesystem site state and database readiness; a `sites/<site>` directory alone does not prove the Frappe database is valid
- Prefer the source docs' site name when it is part of the documented flow (`hrms.localhost` in development docs). For public Sealos access, ensure the frontend's site-name/header behavior matches the generated Ingress host or an intentionally configured default site.

## Administrator Credentials

Frappe reserves `Administrator` and `Guest` as built-in account names. Use `admin` as the recommended default login name when a template asks the deployer to choose an administrator username.

`bench new-site --admin-password` sets the built-in `Administrator` user's password. It does not change the login name.

When the user explicitly asks to enter ERPNext/Frappe administrator credentials:

- Declare `admin_username` and `admin_password` in the Template CR `spec.inputs`.
- Pass both values to init scripts as direct env values. Keep MariaDB, Redis, and PostgreSQL connection credentials on KubeBlocks secrets.
- Run `bench new-site` with the deployer-provided password for the built-in `Administrator` user.
- After the site exists, set the built-in user's `User.username` to the deployer-provided login name through Frappe ORM or `bench execute`.
- Enable `allow_login_using_user_name` for the site so username login works.
- Clear Frappe cache after changing user/login settings.
- Write the init ready marker only after the username, login setting, cache clear, migrations, and app installs have completed.

Example bootstrap sequence:

```bash
bench new-site "$SITE_NAME" \
  --mariadb-root-username "$DB_ROOT_USER" \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_PASSWORD" \
  --force

bench --site "$SITE_NAME" execute frappe.client.set_value \
  --kwargs "{'doctype':'User','name':'Administrator','fieldname':'username','value':'${ADMIN_USERNAME}'}"
bench --site "$SITE_NAME" set-config allow_login_using_user_name 1
bench --site "$SITE_NAME" clear-cache
touch "$READY_MARKER"
```

## Failure Signatures

- `Permission denied` writing `sites/apps.txt`: mounted PVC ownership is wrong; add `fsGroup: 1000` or a volume-permission init.
- `OOMKilled` / exit `137` in `create-site`: init resources are too small.
- `pymysql.err.ProgrammingError: ('DocType', 'Patch Log')`: a prior failed init left a site directory or database residue; reset the failed site/database or rerun `bench new-site --force`.
- Ingress returns `no healthy upstream`: usually not an Ingress problem; check Service endpoints, Pod readiness, and init container state first.
- Login with the configured username fails while `Administrator` works: the template only set the `Administrator` password. Set `User.username`, enable username login, clear cache, and recreate the ready marker after those steps succeed.
