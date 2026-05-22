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
- Init containers that run `bench init`, `bench new-site`, `bench migrate`, or app install steps must set explicit resources. Do not rely on namespace defaults; `64Mi` memory is too small. Use at least:
  - light config init: `requests.memory: 128Mi`, `limits.memory: 256Mi`
  - `bench new-site` / app install / migrate: `requests.memory: 512Mi`, `limits.memory: 2Gi`
- Bootstrap scripts must be idempotent and recover from partial initialization:
  - create `sites/common_site_config.json` if a fresh PVC hides the image's bundled file
  - use `bench new-site --force` for first-site creation when the database may contain residue from a previous failed attempt
  - check both filesystem site state and database readiness; a `sites/<site>` directory alone does not prove the Frappe database is valid
- Prefer the source docs' site name when it is part of the documented flow (`hrms.localhost` in development docs). For public Sealos access, ensure the frontend's site-name/header behavior matches the generated Ingress host or an intentionally configured default site.

## Failure Signatures

- `Permission denied` writing `sites/apps.txt`: mounted PVC ownership is wrong; add `fsGroup: 1000` or a volume-permission init.
- `OOMKilled` / exit `137` in `create-site`: init resources are too small.
- `pymysql.err.ProgrammingError: ('DocType', 'Patch Log')`: a prior failed init left a site directory or database residue; reset the failed site/database or rerun `bench new-site --force`.
- Ingress returns `no healthy upstream`: usually not an Ingress problem; check Service endpoints, Pod readiness, and init container state first.
