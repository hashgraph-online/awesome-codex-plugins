---
name: docker-to-sealos
description: Convert Docker Compose files or installation docs into production-grade Sealos templates. Use when user has a docker-compose.yml and wants a Sealos or Kubernetes template, wants to migrate from Docker Compose to Sealos, needs to convert container orchestration configs to Sealos format, or mentions compose-to-template conversion. Also triggers on "/docker-to-sealos".
---

# Docker to Sealos Template Converter

## Overview

Convert Docker Compose files or installation docs into production-grade Sealos templates.
Execute end-to-end automatically (analysis, conversion, validation, output) without asking users for missing fields.

## Governance and Rule Priority

Use the following precedence to prevent rule drift:

1. `SKILL.md` MUST rules (this file)
2. `references/sealos-specs.md` and `references/database-templates.md`
3. `references/conversion-mappings.md` and `references/example-guide.md`

If lower-priority references conflict with higher-priority MUST rules, update the lower-priority files.
Do not keep conflicting examples.

## Workflow

### Step 1: Analyze input

Extract from Docker Compose/docs:

- application services vs database services
- volumes/config mounts/object storage requirements
- ports, dependencies, service communication
- env vars and secret usage
- startup-time validation rules for bootstrap credentials, API keys, salts, secrets, and feature flags
- multi-service web roles: browser entry, REST API, OpenAI/API gateway, docs, workers, and one-shot jobs
- resource limits/requests and health checks
- if official Kubernetes installation docs/manifests are available, also extract app-runtime behavior from them (bootstrap admin fields, external endpoint/protocol assumptions, health probes, startup/init flow, migration ordering)
- if official compose/docs provide multiple cooperating services, record the official runtime bundle source, component list, image versions, public entry routes, and critical env vars

### Step 2: Infer metadata

Infer and normalize:

- app name, title, description, categories
- official URL, gitRepo, icon source (prefer square/circular icon-first assets such as app icons, favicons, or avatars; avoid rectangular wordmark/text logos)
- locale/i18n metadata

### Step 3: Plan resources in strict order

Generate resources in this order:

1. Template CR
2. ObjectStorageBucket (if needed)
3. Database resources (ServiceAccount → Role → RoleBinding → Cluster → Job if needed)
4. App workload resources (ConfigMap/Secret → Deployment/StatefulSet → Service → Ingress)
5. App resource (last)

### Step 4: Apply conversion rules

Apply field-level mappings from `references/conversion-mappings.md`, including:

- image pinning and annotation mapping
- port/service/ingress conversion
- env var conversion and dependency ordering
- storage conversion and vn naming (`scripts/path_converter.py`)
- service-name to Kubernetes FQDN conversion
- for DB URL/DSN envs (for example `*_DATABASE_URL`, `*_DB_URL`), when Kubeblocks `endpoint` is host:port, inject `host`/`port`/`username`/`password` via approved `secretKeyRef` envs and compose the final URL with `$(VAR)` expansion
- edge gateway normalization: when Compose includes Traefik-like edge proxy plus business services, skip the proxy workload and expose business services via Sealos Ingress directly
- TLS offload normalization for Sealos Ingress: when a business service exposes both 80 and 443, drop 443 from workload/service ports and remove in-container TLS certificate mounts (for example `/etc/nginx/ssl`, `/etc/ssl`, `/certs`) unless official Kubernetes docs explicitly require HTTPS backend-to-service traffic
- multi-service web normalization: expose the verified browser entry in the App resource, expose API/gateway/docs only when they are intended public surfaces, and keep workers private with no Service/Ingress
- URL topology: browser-facing env vars must use public HTTPS URLs, while server-to-server env vars must use Kubernetes Service FQDNs unless the app explicitly requires public callbacks
- prefer `scripts/compose_to_template.py --kompose-mode always` as deterministic conversion entrypoint (require `kompose` for reproducible workload shaping)
- when official Kubernetes installation docs/manifests exist, perform a dual-source merge: use Compose as baseline topology, then align app-runtime semantics with official Kubernetes guidance
- when official compose/docs define a multi-component runtime bundle, keep runtime-required components, entry routes, critical env vars, and component image versions aligned to one official release/compose source

### Step 5: Apply database strategy

- Database services must be generated as KubeBlocks `Cluster` resources. Do not convert PostgreSQL/MySQL/MongoDB/Redis/Kafka Compose database services into raw Kubernetes `Deployment` or `StatefulSet` workloads.
- PostgreSQL must follow the pinned version and structure requirements.
- MySQL/MongoDB/Redis/Kafka must use templates and secret naming from `references/database-templates.md`.
- Add DB init Job/initContainer when application database bootstrap requires it.
- For PostgreSQL custom databases (non-`postgres`), the init Job must wait for PostgreSQL readiness before execution and create the target database idempotently.
- Critical application compatibility objects must be verified in live database state. Use idempotent initContainer self-healing for compatibility views, legacy tables/views, indexes, extensions, search paths, and bootstrap state that the app requires on every cold start.
- One-shot init Jobs may create initial databases or seed state, but app startup gates must verify the final database objects directly. Treat TTL-expired Jobs as historical evidence and rely on database state for acceptance.
- Worker, gateway, and background services that depend on app migrations must wait for the required tables, migration markers, or app-specific readiness objects, not only for the database port.
- Redis readiness probes or initContainers must tolerate authenticated Redis responses such as `NOAUTH` or `Authentication required` when credentials are not needed for readiness.
- PostgreSQL bootstrap shell must use safe quoting patterns. Prefer shell-level existence checks plus simple SQL statements when possible. Use single-quoted heredocs or SQL files for psql variable interpolation, and avoid PL/pgSQL `DO $$` blocks in inline shell commands when a guard query can express the same logic.
- Do not use `psql -c "..."` for `:'var'` variable interpolation. Use `psql -v name=value <<'SQL' ... :'name' ... SQL` or pass already-safe literal SQL.

### Step 6: Generate output files

Always produce:

- `template/<app-name>/index.yaml`
- `template/<app-name>/logo.<ext>` when official icon is resolvable, prioritizing square/circular icon-first artwork and avoiding rectangular wordmark/text logos

Never create:

- `template/<app-name>/README.md`
- `template/<app-name>/README_zh.md`

README authoring is out of scope for this skill. If the Template CR requires README URLs, populate URL fields in `index.yaml` only and leave file creation to a dedicated README skill.

### Step 7: Validate before output

Run validator and self-tests before delivering template output.
If validation fails, fix template/rules/examples first.
For web applications, live validation must include runtime log hygiene: inspect init and main container logs after first readiness, after login or setup, and after one random missing-path HTTP request. Recurring traceback-style warnings are template failures even when pods are Ready.
For login-gated web applications, live validation must prove the real credential/session flow with one authenticated API or page before resource tuning or cleanup.

## MUST Rules (Condensed)

### Naming and metadata

- Template `metadata.name` must be hardcoded lowercase; do not use `${{ defaults.app_name }}`.
- Template CR folder name must match `metadata.name`.
- Template CR must include required metadata fields (`title`, `url`, `gitRepo`, `author`, `description`, `icon`, `templateType`, `locale`, `i18n`, `categories`).
- Template `spec.readme` must point to `https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/<app-name>/README.md`.
- Template `spec.i18n.zh.readme` must point to `https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/<app-name>/README_zh.md`.
- These README fields are URL references in `index.yaml` only; this skill must not create or update the referenced README files.
- `icon` URL must point to template repo raw path for this app on `kb-0.9` branch.
- `template/<app-name>/logo.<ext>` must use square/circular icon-first artwork (for example app icon/favicon/avatar), and must not use rectangular wordmark/text logos.
- `i18n.zh.description` must be written in Simplified Chinese.
- Omit `i18n.zh.title` when it is identical to `title`.
- `categories` must only use predefined values (`tool`, `ai`, `game`, `database`, `low-code`, `monitor`, `dev-ops`, `blog`, `storage`, `frontend`, `backend`).

### App resource

- App resource must use `spec.data.url`.
- App resource `spec.displayType` must be `normal`.
- App resource `spec.type` must be `link`.
- App resource `spec.data.url` must be the browser entry URL that succeeds from a fresh Sealos launch. For apps with safe-path, setup-path, or entrance-path behavior, verify the configured path and root path, then choose the URL that supports login or first-run setup without hidden prior navigation.
- SSR/Next.js/React server apps must not use a path that renders a server-side exception as the App URL or HTTP probe. Treat visible `Application error`, `server-side exception`, `Internal Server Error`, or `Unhandled Runtime Error` text as a failed entry path even if the HTTP status is 2xx/3xx.
- Never use `spec.template` in App resource.
- `cloud.sealos.io/app-deploy-manager` label value must equal resource `metadata.name`.
- `metadata.labels.app` label value must equal resource `metadata.name` for managed app workloads.
- The primary business container name must equal workload `metadata.name` for managed app workloads; sidecar/helper containers may use distinct descriptive names.
- Application `Service` resources must define `metadata.labels.app` and `metadata.labels.cloud.sealos.io/app-deploy-manager`, and both labels must match `spec.selector.app`.
- Runtime component-scoped `ConfigMap` resources must define `metadata.labels.app` and `metadata.labels.cloud.sealos.io/app-deploy-manager`, and both labels must match `metadata.name`; bootstrap-only ConfigMaps used only by init containers to copy initial config into persistent storage must not define either label.
- Application `Service` resources must use the same component name across `metadata.name`, `metadata.labels.app`, `metadata.labels.cloud.sealos.io/app-deploy-manager`, and `spec.selector.app`.
- Root-path `Ingress` resources (`pathType: Prefix`, `path: /`) must use the same component name across `metadata.name`, `metadata.labels.cloud.sealos.io/app-deploy-manager`, and backend `service.name`; non-root or non-Prefix Ingress rules may route to a different backend service.
- Service `spec.ports[*].name` must be explicitly set (required for multi-port services).
- HTTP Ingress must include required nginx annotations (`kubernetes.io/ingress.class`, `nginx.ingress.kubernetes.io/proxy-body-size`, `nginx.ingress.kubernetes.io/server-snippet`, `nginx.ingress.kubernetes.io/ssl-redirect`, `nginx.ingress.kubernetes.io/backend-protocol`, `nginx.ingress.kubernetes.io/client-body-buffer-size`, `nginx.ingress.kubernetes.io/proxy-buffer-size`, `nginx.ingress.kubernetes.io/proxy-send-timeout`, `nginx.ingress.kubernetes.io/proxy-read-timeout`, `nginx.ingress.kubernetes.io/configuration-snippet`) with expected defaults.
- CronJob resources must define labels `cloud.sealos.io/cronjob`, `cronjob-launchpad-name`, and `cronjob-type`; `cloud.sealos.io/cronjob` must equal `metadata.name`, `cronjob-launchpad-name` must be `""`, and `cronjob-type` must be `image`.
- When official application health checks are available, managed workloads must define `livenessProbe`, `readinessProbe`, and (for slow bootstrap apps) `startupProbe`, aligned with official endpoints/commands.
- For public images that are verified to run as a non-root UID, managed app workloads and init Jobs should set restricted-compatible security context (`runAsNonRoot`, `runAsUser`, `runAsGroup`, `fsGroup`, `seccompProfile: RuntimeDefault`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`) unless the image requires root or extra capabilities.

### Official Kubernetes alignment

- If official Kubernetes installation docs/manifests are available, conversion must reference them and align critical runtime settings before emitting template artifacts.
- When official Kubernetes docs/manifests and Compose differ, prefer official Kubernetes runtime semantics for app behavior (bootstrap admin fields, external endpoint/env/protocol, health probes), unless doing so violates higher-priority Sealos MUST/security constraints.
- When official compose/docs provide a multi-component runtime bundle, template artifacts must preserve runtime-required components, public entry routes, critical env vars, and image versions from the same official release/compose source.
- Templates using official multi-component runtime evidence must provide a separate `RuntimeBundleEvidence` YAML file during validation, while final Sealos Template artifacts stay free of runtime-bundle validator metadata.

### Images and pull policy

- Do not use `:latest`.
- Resolve versions with `crane`: prefer an explicit version tag (for example `v2.2.0`), and fallback to digest pin only when a deterministic version tag is unavailable.
- Avoid floating tags (for example `:v2`, `:2.1`, `:stable`); use an explicit version tag or digest.
- Managed workload image references must be concrete and must not contain Compose-style variable expressions (for example `${VAR}`, `${VAR:-default}`); resolve to explicit tag or digest before emitting template artifacts.
- Application `originImageName` must match container image.
- Public-image managed app workloads must omit `template.spec.imagePullSecrets`; private-registry workloads may reference only the app-scoped pull Secret `${{ defaults.app_name }}`.
- The registry pull Secret is runtime-managed by `sealos-deploy` using local `gh` CLI credentials for private GHCR images; do not expose raw registry credential inputs in generated templates.
- All containers must explicitly set `imagePullPolicy: IfNotPresent`.

### Storage

- Do not use `emptyDir`.
- Use persistent storage patterns (`volumeClaimTemplates`) where storage is needed.
- StatefulSet resources with `volumeClaimTemplates` must keep standard workload labels such as `app` and `cloud.sealos.io/app-deploy-manager`, and omit only `cloud.sealos.io/deploy-on-sealos` from both StatefulSet `metadata.labels` and `volumeClaimTemplates[].metadata.labels`.
- `volumeClaimTemplates[].metadata` should include `name` and `annotations`.
- PVC request must be `<= 1Gi` unless source spec explicitly requires less.
- ConfigMap data keys must follow vn naming (`scripts/path_converter.py`), including `/`, `-`, `.`, and other special characters.
- ConfigMaps mounted by managed Deployment/StatefulSet workloads must use `metadata.name == workload.metadata.name`.
- ConfigMap workload volumes must use `<workload-name>-cm`, and every ConfigMap `data` key must be mounted as its own `volumeMount` with `subPath` exactly equal to that key.
- Omit ConfigMap volume `defaultMode` unless the application explicitly needs a non-default mode. ConfigMap scripts invoked through `/bin/sh /path/script` do not need executable bits.
- Avoid long inline startup scripts or heredocs in `command`/`args`; place initialization/start scripts in ConfigMap files and invoke them with a short command.

### Env and secrets

- Non-database sensitive values/inputs use direct `env[].value`.
- Business containers must source database connection fields (`endpoint`, `host`, `port`, `username`, `password`) from approved Kubeblocks database secrets via `env[].valueFrom.secretKeyRef`; exception: Redis `host`/`port` may use Sealos Redis Service FQDN and `6379` when the Redis secret only exposes credentials, and MongoDB `host`/`port` or connection URLs may use the Sealos MongoDB Service FQDN plus `27017` when the MongoDB secret exposes credentials only.
- Business containers must not use custom env/volume `Secret` references except approved Kubeblocks database secrets and object storage secrets.
- A dedicated app-scoped registry pull Secret is allowed only for private-registry images and must be referenced only through `template.spec.imagePullSecrets`; public images must not add pull secrets.
- Database connection/bootstrap may use Kubeblocks-provided secrets, and reserved Kubeblocks database secret names must not be redefined by custom `Secret` resources.
- Env vars must be declared before referenced (for example password before URL composition).
- Follow official app env var naming; do not invent prefixes.
- For split frontend/API/gateway apps, keep public browser URLs and internal service URLs separate. Frontend/browser callback variables use `https://${{ defaults.<host> }}.${{ SEALOS_CLOUD_DOMAIN }}`; backend-to-backend variables use `http://<service>.$(SEALOS_NAMESPACE).svc.cluster.local:<port>` or the fully rendered Service FQDN.
- When the application requires its public URL configured via a file-based config system (e.g., node-config `config/default.json`, PHP config files), create a ConfigMap containing the config file with the public URL set to `https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}`, and mount it to the application's config directory. The ConfigMap must follow standard naming and label conventions.
- For PostgreSQL custom databases (non-`postgres`), include `${{ defaults.app_name }}-pg-init` Job and implement startup-safe/idempotent creation logic (readiness wait + existence check before create).
- For application-specific database compatibility, include an initContainer or startup gate that idempotently creates or repairs required views, aliases, indexes, extensions, privileges, role search paths, and legacy compatibility objects before the business container starts.
- Managed app main container `command`/`args` must stay close to the image's official entrypoint. Keep only official startup commands, Compose-native args, or a short exec wrapper; move file preparation, permission repair, database bootstrap, and compatibility self-healing into initContainers, Jobs, or ConfigMap scripts.
- Shell wrappers in the main business container must `exec` the final process so signal handling remains correct.
- Database bootstrap SQL must be safe under shell execution: prefer shell-level guard queries plus simple SQL, use single-quoted heredocs for psql variables, and avoid unguarded inline `DO $$` blocks.
- `psql -c` must not contain `:'var'` psql variable syntax; use heredocs for SQL that needs `-v` interpolation.

### Database-specific constraints

- Database services must use KubeBlocks `Cluster` resources, not application `Deployment` or `StatefulSet` workloads. `StatefulSet` is allowed for stateful application components only, never for PostgreSQL/MySQL/MongoDB/Redis/Kafka database services.
- PostgreSQL version: `postgresql-16.4.0`.
- PostgreSQL API: `apps.kubeblocks.io/v1alpha1`.
- PostgreSQL RBAC unified naming: `${{ defaults.app_name }}-pg`.
- PostgreSQL RBAC requires `app.kubernetes.io/instance` and `app.kubernetes.io/managed-by` labels.
- Every KubeBlocks database `Cluster` must include `kb.io/database`, `sealos-db-provider-cr`, and `clusterdefinition.kubeblocks.io/name` labels; `sealos-db-provider-cr` must equal `metadata.name` so dbprovider can list and classify the database. Related Pods, Services, and OpsRequests should carry `app.kubernetes.io/instance=<database name>` for detail views.
- PostgreSQL role wildcard permission requirement remains as defined in current spec.
- PostgreSQL cluster must include required labels/fields (`kb.io/database: postgresql-16.4.0`, `clusterdefinition.kubeblocks.io/name: postgresql`, `clusterversion.kubeblocks.io/name: postgresql-16.4.0`, `clusterVersionRef: postgresql-16.4.0`, `disableExporter: true`, `enabledLogs: [running]`, `switchPolicy.type: Noop`, `serviceAccountName`).
- MongoDB cluster must follow upgraded structure (`componentDef: mongodb`, `serviceVersion: 8.0.4`, labels `kb.io/database` and `app.kubernetes.io/instance`).
- MySQL cluster must follow upgraded structure (`kb.io/database: ac-mysql-8.0.30-1`, `clusterDefinitionRef: apecloud-mysql`, `clusterVersionRef: ac-mysql-8.0.30-1`, `tolerations: []`).
- Redis cluster must follow upgraded structure (`componentDef: redis-7`, `componentDef: redis-sentinel-7`, `serviceVersion: 7.2.7`, main data PVC `1Gi`, topology `replication`).
- Database cluster component resources must use `limits(cpu=500m,memory=512Mi)` and `requests(cpu=50m,memory=51Mi)` unless source docs explicitly require otherwise.
- All managed workload container resources must use the Sealos resource ladder: `limits.cpu` only `100m/200m/500m/1/2/3/4/8`, `limits.memory` only `128Mi/256Mi/512Mi/1024Mi/2048Mi/4096Mi/8192Mi/16384Mi`, and `requests` must be derived from `limits` by dropping the last numeric digit (`500m→50m`, `512Mi→51Mi`, `1→100m`, `1024Mi→102Mi`, `4096Mi→409Mi`). Do not invent non-ladder values, and never use `2G/4G/8G/16G` because Sealos Template API quota preview can parse bare `G` memory as 0.
- Secret naming:
  - MongoDB: `${{ defaults.app_name }}-mongo-mongodb-account-root` (or `${{ defaults.app_name }}-mongodb-mongodb-account-root` when the MongoDB cluster name uses `-mongodb`)
  - Redis: `${{ defaults.app_name }}-redis-redis-account-default` (legacy `${{ defaults.app_name }}-redis-account-default` may be accepted for backward compatibility)
  - Kafka: `${{ defaults.app_name }}-broker-account-admin`
  - Do not use legacy naming outside supported exceptions.

### Baseline runtime defaults

Unless source docs explicitly require otherwise, use the lightweight app ladder entry:

- container limits: `cpu=200m`, `memory=256Mi`
- container requests: `cpu=20m`, `memory=25Mi`
- `revisionHistoryLimit: 1`
- `automountServiceAccountToken: false` by default; set it to `true` only when the application has explicit Kubernetes API/service account token requirements, evidenced by Kubernetes integration settings, `serviceAccountName`, or a `sealos.io/service-account-token-reason` workload annotation.
- If a workload emits PodSecurity admission warnings and the image runs as a non-root user, add the restricted-compatible security context before reporting the template ready.

For higher resource needs, move only to another allowed `limits` ladder entry and recompute `requests` from that `limits` value.

### Browser / remote desktop resource validation

For browser, VNC, WebRTC desktop, Xvfb, Selkies, noVNC, Kasm, or remote-desktop-style containers:

- Do not treat a short smoke test as proof of a stable minimum memory value.
- Validate memory with a fresh deployment, not only a patched warm pod.
- Exercise cold start until readiness, a lightweight page, a real/medium page, an interactive/search page, and a 60s post-smoke stability check.
- If observed cgroup memory reaches more than 80% of the limit during smoke, move to the next allowed Sealos memory ladder value.
- Keep requests derived from limits according to the Sealos resource ladder.

Example:
- Bad: Chrome passes a short smoke at `512Mi` but reaches `503Mi`; shipping `512Mi` as the stable minimum is unsafe.
- Good: raise to `1024Mi`, set request to `102Mi`, rerun smoke and stability checks.

For Chrome + Xvfb + Selkies with 4K max display, use at least:
- limits: `cpu=200m`, `memory=1024Mi`
- requests: `cpu=20m`, `memory=102Mi`

### Defaults vs inputs

- `defaults` for generated values (`app_name`, `app_host`, random passwords/keys).
- `inputs` only for truly user-provided operational values (email/SMTP/external API keys, etc.).
- When application administrator credentials are user-configurable, declare both administrator username and password in `spec.inputs` as required inputs with no `default` field, pass them as direct env values, and apply them through the application's documented bootstrap or initialization path. Keep database credentials on KubeBlocks secrets.
- Every `${{ inputs.<name> }}` reference in a template artifact must have a matching `spec.inputs.<name>` declaration in the same Template CR.
- `inputs.description` must be in English.
- Startup-critical `inputs[*].default` values must satisfy the application's documented startup validation. For admin/bootstrap passwords with complexity rules, do not use `''`, weak examples, or bare `${{ random(n) }}` because generated characters may not include required classes; include deterministic required classes around the random segment, for example `"AppName@${{ random(16) }}!1"`.
- If an application exits when a required input is weak or empty, treat the input default as part of the runtime contract. Live validation must include the first boot logs and login/setup path with the generated default value.
- For binary object storage choices, use a boolean input (for example `enable_s3_storage`) and test with `inputs.<name> === 'true'`.

## Validation Commands

Run all checks before final response:

1. `python scripts/path_converter.py --self-test`
2. `python scripts/test_check_consistency.py`
3. `python scripts/test_compose_to_template.py`
4. `python scripts/test_check_must_coverage.py`
5. `python scripts/check_consistency.py --skill SKILL.md --references references --rules-file references/rules-registry.yaml`
6. `python scripts/check_consistency.py --skill SKILL.md --references references --rules-file references/rules-registry.yaml --artifacts template/<app-name>/index.yaml`
7. `python scripts/check_must_coverage.py --skill SKILL.md --mapping references/must-rules-map.yaml --rules-file references/rules-registry.yaml`
8. (CI / one-shot) `python scripts/quality_gate.py --artifacts /abs/path/template/<app-name>/index.yaml` or `DOCKER_TO_SEALOS_ARTIFACTS=/abs/path/template/<app-name>/index.yaml python scripts/quality_gate.py` (without explicit artifacts, it scans `template/*/index.yaml`; set `DOCKER_TO_SEALOS_ALLOW_EMPTY_ARTIFACTS=1` only for dev/debug without artifacts)
9. Live deploy acceptance: after `sealos-deploy` creates the app, verify the actual App URL, login/setup flow for web apps, recent logs, a random missing-path 404 without noisy traceback logs, expected database objects, and full resource footprint before reporting success.

`check_consistency.py` is registry-driven. Keep `references/rules-registry.yaml` in sync with implemented rules.
Registry rule entries support `severity` and optional `scope.include_paths` metadata.

## Output Contract

When conversion is complete, provide:

1. brief conversion summary
2. target file path (`template/<app-name>/index.yaml`)
3. complete template YAML
4. key decisions only where ambiguity existed

Do not create or output README content in this skill. README generation is delegated to another skill.

## Reference Navigation (Progressive Loading)

Load only needed references for current task:

- `references/sealos-specs.md`
  - authoritative ordering, labels, App/Ingress/ConfigMap conventions
- `references/conversion-mappings.md`
  - Docker→Sealos field-level mappings and edge conversions
- `references/database-templates.md`
  - database templates, RBAC structures, secret naming patterns
- `references/frappe-bench.md`
  - Frappe/ERPNext/HRMS/bench conversion patterns, init resources, idempotent site bootstrap, and common failure signatures
- `references/runtime-log-hygiene.md`
  - runtime log acceptance, benign 404 traceback handling, quiet dependency installation, and restricted security context guidance
- `references/example-guide.md`
  - examples and pattern walkthroughs (non-authoritative)
- `references/rules-registry.yaml`
  - machine-readable validation scope/rules list
- `references/must-rules-map.yaml`
  - MUST bullet to enforcement mapping (`rule` or `manual`) for drift control

## Script Utilities

- `scripts/path_converter.py`
  - convert paths to vn names
  - self-test support for regression checks
- `scripts/compose_to_template.py`
  - deterministic compose/docs-to-template generator entrypoint
  - supports `--kompose-mode auto|always|never` (`always` is default) to reuse `kompose convert` workload shapes
  - emits `template/<app-name>/index.yaml`
- `scripts/test_compose_to_template.py`
  - regression tests for compose conversion behavior
- `scripts/check_consistency.py`
  - registry-driven consistency validator
- `scripts/test_check_consistency.py`
  - regression tests for validator behavior
- `scripts/check_must_coverage.py`
  - validate MUST bullet coverage mapping against registry rules
- `scripts/test_check_must_coverage.py`
  - regression tests for MUST coverage validator
## Edge Policies

- Never ask users for missing fields; infer from compose/docs and platform conventions.
- Keep App resource in `spec.data.url` format; never use `spec.template`.
- Keep App resource `spec.displayType: normal` and `spec.type: link`; do not infer alternative enum values.
- Keep business-env, object storage, and DB-secret policy consistent with MUST rules.
- Prefer square/circular icon-first logo assets (app icon/favicon/avatar) and avoid rectangular wordmark/text logos.
- Prefer Sealos-managed ingress over bundled edge proxies: if a Traefik gateway is only acting as ingress/front-proxy and at least one business service exists, do not emit Traefik workload resources.
- Prefer gateway TLS termination in Sealos Ingress over in-container TLS: for dual-port HTTP/HTTPS workloads, keep HTTP service port and remove redundant HTTPS/certificate mounts unless official docs require HTTPS backend.
- Never create `template/<app-name>/README.md` or `template/<app-name>/README_zh.md`; only keep README URL references inside `index.yaml` when required by the template schema.
- Prefer fixing references/examples over adding exceptions when conflicts appear.
- If official Kubernetes installation docs/manifests exist for the target app, do not ignore them; use them to refine runtime semantics beyond Compose defaults.
- If the project mentions Frappe, ERPNext, HRMS, or `bench`, load `references/frappe-bench.md` before generating app workloads.
