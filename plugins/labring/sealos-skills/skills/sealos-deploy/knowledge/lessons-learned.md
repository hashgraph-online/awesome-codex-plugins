# Lessons Learned from Real Deployments

This document captures patterns and solutions from actual Sealos deployment experiences to prevent repeated mistakes.

## Contents

- [Consolidated Patterns](#consolidated-patterns)
  - [KubeBlocks Redis Readiness Lag](#kubeblocks-redis-readiness-lag)
  - [Root Entrypoint Handoff and Persistent Storage Permissions](#root-entrypoint-handoff-and-persistent-storage-permissions)
  - [Startup-Fatal Bootstrap Credential Validation](#startup-fatal-bootstrap-credential-validation)
  - [GHCR Push Succeeds but Cluster Pull Fails](#ghcr-push-succeeds-but-cluster-pull-fails-prevents-imagepullbackoff)
  - [Public URL Misconfiguration](#public-url-misconfiguration-prevents-runtime-api-failures)
  - [Docker Hub Namespace Mismatch](#docker-hub-namespace-mismatch-prevents-unnecessary-builds)
  - [Launchpad Public Address Missing](#launchpad-public-address-missing-while-the-url-works)
  - [BillionMail Safe Entry and DB Bootstrap](#billionmail-safe-entry-and-db-bootstrap-prevents-access-denied-and-init-loops)
  - [ERPNext / Frappe Admin Username](#erpnext--frappe-admin-username-prevents-login-smoke-mismatch)
  - [Multi-Component Runtime Bundle Drift](#multi-component-runtime-bundle-drift-prevents-post-login-route-mismatch)
  - [Image-Bundled Dependency Path Hidden by PVC](#image-bundled-dependency-path-hidden-by-pvc-prevents-api-backed-features)
  - [Ephemeral Storage Preservation](#ephemeral-storage-preservation-during-template-updates)
- [Consolidated Runtime Truth Contract](#consolidated-runtime-truth-contract)

## Consolidated Patterns

### KubeBlocks Redis Readiness Lag

Redis Sentinel can report readiness before the primary Redis component and the default account Secret appear. Treat final Cluster Ready/Running state, `${APP_NAME}-redis-redis-account-default`, `${APP_NAME}-redis-redis-redis.${NAMESPACE}.svc.cluster.local`, and successful application registration/login as the acceptance signal.

### Root Entrypoint Handoff and Persistent Storage Permissions

Images that start as root and then switch identity through `su-exec`, `gosu`, or `setpriv` can fail when a template drops all capabilities while the handoff path is still active.

Syncthing showed the concrete pattern:

```yaml
detection:
  symptoms:
    - "chown: /var/syncthing: Operation not permitted"
    - "su-exec: setgroups(1000): Operation not permitted"
    - "Pod CrashLoopBackOff after persistent storage is mounted"

fixes:
  preferred:
    - "Verify the final UID/GID and run the Pod directly as that identity"
    - "Set runAsNonRoot, runAsUser, runAsGroup, fsGroup, fsGroupChangePolicy, and RuntimeDefault seccomp"
    - "Use an initContainer for official offline config generation when available"
    - "Keep the main container close to the official startup command"

verification:
  - "First boot logs are clear"
  - "Login or setup works with the selected account-flow credentials"
  - "At least one authenticated API/page works"
  - "Documented authenticated API negative route returns 404, or a unique missing static asset is used for SPA fallback"
  - "Footprint shows expected ready/desired counts and zero restarts"
```

For Syncthing, the validated runtime used UID/GID `1000`, generated GUI config in an initContainer, authenticated with dynamic CSRF cookie/header flow, and stayed stable at `100m/128Mi` limits with `10m/12Mi` requests.

### Startup-Fatal Bootstrap Credential Validation

- **Symptom**: The main process exits before serving HTTP with password-policy, invalid root configuration, or account reconciliation validation; resource increases leave the signature unchanged.
- **Root cause**: The template injects an optional root overlay into a release with functional first-user signup, or startup enforces credential rules beyond the Template input schema.
- **Decision**: Classify the exact selected release. Signup mode omits optional administrator/root bootstrap injection. Mandatory deployer-supplied mode uses required inputs with exact English constraints and pre-deploy validation. Mandatory generated mode constructs the documented format deterministically, retains the resolved credential, and proves redacted login.
- **Repair**: Patch the source Template and highest writable live declarative owner, roll out a fresh Pod, wait through reconciliation, and inspect historical key names with values redacted. Recommend credential rotation.
- **Verification**: First-boot logs stay clear, the selected signup/login flow succeeds from a fresh session, and one authenticated page or API route works.

### GHCR Push Succeeds but Cluster Pull Fails (Prevents `ImagePullBackOff`)

```yaml
detection:
  trigger:
    - "Phase 4 built a ghcr.io/<user>/<repo>:<tag> image locally"
    - "Deployment later stalls with ImagePullBackOff or ErrImagePull"
  root_causes:
    - "GitHub Container Registry package visibility is still private"
    - "Cluster has no imagePullSecret for ghcr.io"

decision:
  if_local_gh_cli_is_available:
    require: "for a fresh deploy, deploy first and immediately create the namespace image pull Secret with the real returned instance name; for an update, refresh the known same-named Secret before changing the image"
  else:
    fallback: "package must be public, or the operator must provide registry pull credentials another way"
  skip_when:
    - "Phase 2 reused an existing public image"

verification:
  local_build_rule: "treat a newly pushed GHCR image as private and require the pull Secret without probing visibility or anonymous access"

fixes:
  required: "create/update the app-scoped imagePullSecret from gh auth token; after a fresh deploy, rely on kubelet pull retries instead of recreating the Pod"
  forbidden: "do not attempt REST, GraphQL, package settings, or other visibility mutations to make the package public"
  alternate_registry: "push to Docker Hub only when the user selected that public-image flow"
```

### Public URL Misconfiguration (Prevents Runtime API Failures)

```yaml
detection:
  # Scan source code for these patterns
  env_var_patterns:
    - "BASE_URL"
    - "SITE_URL"
    - "APP_URL"
    - "NEXTAUTH_URL"
    - "PUBLIC_URL"
    - "EXTERNAL_URL"
  config_file_patterns:
    - "getConfig(.*[Uu]rl"
    - "homeUrl"
    - "baseUrl"
    - "siteUrl"
    - "http://localhost"

  # Decision
  strategy:
    env_var_supported: "Strategy A — add env var with public URL"
    config_file_only: "Strategy B — create ConfigMap with minimal config override"
```

### Docker Hub Namespace Mismatch (Prevents Unnecessary Builds)

```yaml
detection:
  # Primary: <github-owner>/<github-repo>
  primary: "${github_owner}/${github_repo}"

  # Fallback 1: <repo-name>/<repo-name> (when owner ≠ repo)
  fallback_repo_repo: "${github_repo}/${github_repo}"

  # Fallback 2: README scan for docker pull/run references
  fallback_readme: "scan README.md for image references"
```

### Launchpad Public Address Missing While The URL Works

```yaml
detection:
  symptoms:
    - "The public URL serves the application while Launchpad shows no public address"
    - "The App shortcut points to a host that differs from the current public network"
    - "Launchpad edit/save creates random network and Service names"

root_causes:
  - "The root Prefix Ingress uses backend.service.port.name instead of port.number"
  - "The numeric Ingress backend port does not match Service.spec.ports[].port"
  - "A split StatefulSet governing Service causes Launchpad to rewrite immutable serviceName during an edit"
  - "The App URL retains a replaced Ingress host"

fixes:
  - "Use a numeric root Ingress backend port while keeping the Service port name"
  - "For single-component StatefulSets without a headless requirement, align spec.serviceName with the public application Service"
  - "Preserve documented HA/headless topology and expose it through a separate public application Service"
  - "Repair the template-owned resources, then verify Launchpad API state before HTTP smoke"

verification:
  - "sealos-launchpad-network.mjs reports ok: true"
  - "The Launchpad network port matches the public Service port"
  - "The App URL host matches the Launchpad public or custom domain"
  - "The manager-labeled Ingress backend resolves to a Service with ready endpoints"
  - "sealos-footprint.mjs identifies any orphan network resources before cleanup"
```

### BillionMail Safe Entry and DB Bootstrap (Prevents `access denied` and Init Loops)

```yaml
detection:
  symptoms:
    - "Pod is Running but login APIs return access denied"
    - "Root URL and configured App URL behave differently in a fresh session"
    - "Init container waits forever on application-specific database checks"
    - "Startup logs mention pg_indexes, relay compatibility objects, or missing PostgreSQL search_path"
    - "PostgreSQL bootstrap logs show syntax error at or near \"$\""
    - "PostgreSQL bootstrap logs show syntax error at or near \":\" for ALTER ROLE ... :'app_password'"

runtime_entry:
  final_config:
    safe_path: ""
    app_url: "root Sealos App URL"
    main_container_working_dir: "/opt/billionmail/core"
    main_container_command: "mkdir -p template && exec ./billionmail"
  command_boundary:
    keep_in_main_container:
      - "official entrypoint or short exec wrapper only"
    move_out_of_main_container:
      - "file preparation and permission repair"
      - "certificate/log-file setup"
      - "database bootstrap and compatibility objects"
      - "relay/search-path repair"
  verification:
    - "GET /api/get_validate_code returns success from the root App URL"
    - "POST /api/login succeeds with generated admin credentials"
    - "An authenticated page or API route works after login"
    - "Live pod main container command stays short and ends in exec"

database_bootstrap:
  principle: "Make critical compatibility objects idempotent and self-healing in init containers"
  verify_live_state:
    - "public.pg_indexes compatibility view exists"
    - "relay compatibility objects exist"
    - "application role search_path resolves expected public schema objects"
  ttl_job_note: "A completed or cleaned-up Job is only historical evidence; the database state is the acceptance signal"

quoting_rules:
  - "Prefer shell-level guard queries plus simple SQL over inline DO $$ blocks"
  - "Use single-quoted heredocs for psql -v variable interpolation"
  - "Do not put :'var' psql syntax inside psql -c strings"

generalized_pattern:
  - "The Sealos App URL must be the URL that succeeds from a fresh browser session"
  - "Path-based safe entrances need root-path smoke tests because launchers may normalize or revisit root"
  - "Post-rollout log scans are part of acceptance for login-gated web apps"
```

### ERPNext / Frappe Admin Username (Prevents Login Smoke Mismatch)

```yaml
detection:
  symptoms:
    - "Template exposes admin username/password inputs"
    - "Login succeeds with Administrator but fails with the configured username"
    - "bench new-site completed and the ready marker exists"
  root_cause: "bench new-site --admin-password sets the built-in Administrator password; it does not rename the login identity"

template_contract:
  administrator_inputs:
    - "Declare admin_username and admin_password in spec.inputs when deployers must choose credentials"
    - "Pass application admin credentials as direct env values to the Frappe init path"
    - "Keep database credentials on KubeBlocks secrets"
  reserved_names:
    - "Administrator"
    - "Guest"
  recommended_default_username: "admin"

init_sequence:
  - "Run bench new-site with the deploy-time admin password"
  - "Set User.username for the built-in Administrator user to the deploy-time admin username"
  - "Enable allow_login_using_user_name"
  - "Clear Frappe cache"
  - "Write the ready marker after username/login settings, migrations, and app installs finish"

runtime_truth:
  - "Login smoke uses the exact admin username/password collected during deploy"
  - "Password values are masked in logs, summaries, and final output"
```

### Multi-Component Runtime Bundle Drift (Prevents Post-Login Route Mismatch)

```yaml
detection:
  trigger:
    - "Login or registration succeeds, then the browser lands on a 404/route mismatch page"
    - "Browser network logs show API route 404/5xx after authentication"

  root_causes:
    - "Console/frontend image comes from a different official release than the API image"
    - "An official frontend/console service was omitted from the deployed topology"
    - "Ingress or gateway routes do not cover the official public entry paths"
    - "Public URL or endpoint env/config no longer matches the exposed route"

fixes:
  preferred:
    - "Lock API, console/frontend, workers, realtime, and gateway components to one official compose/release source"
    - "Expose each official public entry path through the matching Service and Ingress rule"
    - "Verify login with final URL, page title, visible authenticated content, network 4xx/5xx list, and backend route logs"
```

### Image-Bundled Dependency Path Hidden by PVC (Prevents API-Backed Features)

```yaml
detection:
  symptoms:
    - "A dependent component reports Ready while API-backed features fail or stay incomplete"
    - "Logs contain failed to setup runner dependencies"
    - "Logs mention a missing dependency manifest such as dependencies/python-requirements.txt"
    - "kubectl exec shows the mounted path contains only lost+found"

root_cause:
  pattern: "A host-directory Compose mount was converted to a fresh PVC at a path where the image already ships required dependency metadata"

fixes:
  preferred:
    - "Inspect the official image, source tree, or release tag for the missing file"
    - "Remove the PVC and volumeMount when the image provides the required dependency/config metadata"
    - "Keep PVCs for user data, uploads, model caches, and writable runtime state"

verification:
  - "Template API dry-run shows storage removed from that component"
  - "Fresh deployment logs omit the missing dependency manifest error"
  - "Setup/login and one API-backed action work from the real App URL"
```

### Ephemeral Storage Preservation During Template Updates

```yaml
detection:
  trigger:
    - "An existing template already defines resources.requests.ephemeral-storage or resources.limits.ephemeral-storage"
    - "The current task is CPU/memory resource tuning, runtime debug, README refresh, or unrelated template cleanup"

rule:
  preserve:
    - "Keep existing ephemeral-storage request and limit values unchanged"
    - "Treat CPU/memory ladder tuning as independent from ephemeral-storage fields"
  change_only_with:
    - "Live evidence of EphemeralStorage, eviction, or disk-pressure failures"
    - "Source documentation that defines a different ephemeral storage requirement"

verification:
  - "git diff -U0 -- template/<app>/index.yaml | rg ephemeral-storage returns no lines for unrelated changes"
```

## Consolidated Runtime Truth Contract

The following rules combine the reusable runtime, authentication, route, Job, log, footprint, Secret, and S3/database lessons. Apply them to every live deployment and keep app-specific examples below this contract aligned with them.

### Runtime identity, root routes, and authentication

- Read the actual Instance/App names and App URL host from the Template API response or live App resource. A requested `app_name` can produce a different Instance or ingress host.
- Run the Launchpad public-network check before HTTP smoke. For an HTTP Ingress with several paths, the root Prefix path `/` appears first; its numeric backend port matches the public Service port and its host matches the App URL.
- Exercise the configured entrance path and `/` from a fresh session. Pick the entry that reaches the real first-run or login screen without SSR/browser failure text.
- Use the exact selected account-flow values for registration/login/setup. JSON-token flows and cookie-session flows are both valid; cookie-session flows derive the dynamic CSRF header from the CSRF cookie before posting credentials and reuse the session on authenticated routes.
- Redact passwords, bearer tokens, cookies, CSRF values, captcha payloads, and derived credentials from command output, logs, and reports.

### Jobs, logs, and database final state

- Keep database bootstrap and compatibility repair in idempotent initContainers or Jobs while the main container stays close to the official entrypoint and ends wrappers with `exec`.
- A completed or TTL-expired Job proves execution history. Acceptance requires the live database final state: required databases, tables/views, extensions, indexes, roles, grants, search paths, and migration markers.
- PostgreSQL custom-database Jobs wait for database readiness and create the target database idempotently. Migration-dependent workers gate on required tables or app-specific markers, not only a database port.
- Capture a no-baseline log report after readiness, then compare after the stability window. A `Succeeded` Pod with zero exit codes is completed workload evidence; failed or non-zero completion remains blocking. Completed init output may be retained as `historicalCompletedInit: true` when completion time and exit code predate `baseline.generatedAt`, Pod UID/restarts/completion markers stay unchanged, and output is unchanged; the scan uses the baseline timestamp as the log increment boundary. Active init/main failures, restart deltas, readiness flaps, advancing Warning Events, unresolved referenced Secrets, OOM/CrashLoop, and repeated tracebacks fail acceptance.

### Footprint and object storage

- Inventory `Instance`, App, workloads, CronJobs, Jobs, Services, Ingresses, PVCs, KubeBlocks Clusters, and `ObjectStorageBucket` resources before cleanup or handoff.
- `sealos-footprint.mjs` must complete every requested listing successfully before `cleanupComplete: true` is accepted. Permission errors keep cleanup unresolved even when the visible resource list is empty.
- Managed or private S3 acceptance requires authenticated upload, application read/download with matching content, proxy or time-bounded presigned delivery, restricted anonymous raw-object access, and smoke-object deletion when supported. Optional S3 requires independent local and managed-bucket branch evidence.

### Runtime-derived secrets and S3/DB coupling

- A template may carry a quoted opaque seed in `spec.defaults` only when the runtime library deterministically derives and validates the final credential before `exec`. The seed and derived value stay out of reports, and the application must fail before serving traffic when validation fails.
- S3 and database readiness are separate contracts. Verify approved KubeBlocks Secret keys and required database objects alongside managed object-storage Secret wiring and the `ObjectStorageBucket`; a Ready Pod or successful Job alone does not prove either data plane.
