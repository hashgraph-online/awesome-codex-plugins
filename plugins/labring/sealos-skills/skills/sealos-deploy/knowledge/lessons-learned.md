# Lessons Learned from Real Deployments

This document captures patterns and solutions from actual Sealos deployment experiences to prevent repeated mistakes.

---

## Case Study: EverShop (Public URL + Image Detection)

**Project**: EverShop - Node.js e-commerce platform using node-config
**GitHub**: `evershopcommerce/evershop`
**Issues Encountered**: 2 (public URL misconfiguration, image detection miss)

### Issue 1: Hardcoded localhost Base URL

- **Symptom**: App deployed successfully but all frontend API calls failed (404/CORS errors)
- **Root Cause**: App uses node-config with `getConfig('shop.homeUrl', 'http://localhost:3000')` — when no config override exists, all generated URLs point to localhost
- **Detection Signal**: `packages/evershop/src/lib/util/getBaseUrl.ts` contains fallback to `http://localhost:3000`
- **Fix**: Created ConfigMap with `config/default.json` containing `{"shop":{"homeUrl":"https://<public-url>"}}`, mounted via `subPath` to avoid overwriting other config files
- **Generalized Pattern**: **Public URL via file-based config** — many apps (especially Node.js with node-config, PHP with config files) read their public URL from config files rather than env vars. When `localhost` fallback is detected in source code, a ConfigMap override is required.
- **Status**: Pattern added to `conversion-mappings.md` (Strategy B: ConfigMap)

### Issue 2: Docker Hub Image Not Found

- **Symptom**: `detect-image.mjs` returned `{ "found": false }`, triggering unnecessary Docker build
- **Root Cause**: Script only checked `<github-owner>/<github-repo>` (i.e., `evershopcommerce/evershop`), but official Docker image is at `evershop/evershop`
- **Detection Signal**: Docker Hub namespace differs from GitHub org — common when project name is shorter than org name
- **Fix**: Added fallback check for `<repo-name>/<repo-name>` pattern in `detect-image.mjs`
- **Other Known Examples**:
  - GitHub `nextcloud/server` → Docker Hub `nextcloud/nextcloud`
  - GitHub `gogs/gogs` → Docker Hub `gogs/gogs` (same, but org ≠ repo in other cases)
- **Status**: Fallback added to `detect-image.mjs`

### Generalized Lessons

1. **Public URL Detection is Critical**: Always scan source code for `localhost` fallback patterns during Phase 5.2. Missing this causes subtle runtime failures (app loads but API calls fail).
2. **Image Detection Needs Multiple Strategies**: Don't assume Docker Hub namespace matches GitHub org. Check `<repo>/<repo>` as fallback.
3. **Config File Overrides via ConfigMap**: When an app uses file-based config (not env vars) for its public URL, use a ConfigMap with `subPath` mount to inject only the needed override without replacing the entire config directory.

---

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
  - "Login or setup works with deploy-time credentials"
  - "At least one authenticated API/page works"
  - "Random authenticated missing path returns 404"
  - "Footprint shows expected ready/desired counts and zero restarts"
```

For Syncthing, the validated runtime used UID/GID `1000`, generated GUI config in an initContainer, authenticated with dynamic CSRF cookie/header flow, and stayed stable at `100m/128Mi` limits with `10m/12Mi` requests.

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
    require: "create or refresh the namespace image pull Secret automatically before deploy/update"
  else:
    fallback: "package must be public, or the operator must provide registry pull credentials another way"
  skip_when:
    - "Phase 2 reused an existing public image"

verification:
  visibility_check: "gh api /user/packages/container/<repo> -q .visibility"
  anonymous_pull_check: "GET ghcr token, then HEAD/GET manifest from ghcr.io/v2/.../manifests/<tag>"

fixes:
  preferred: "create/update the app-scoped imagePullSecret from gh auth token during deploy"
  fallback_1: "make the GHCR package public"
  fallback_2: "push to Docker Hub instead"
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
