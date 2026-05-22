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
