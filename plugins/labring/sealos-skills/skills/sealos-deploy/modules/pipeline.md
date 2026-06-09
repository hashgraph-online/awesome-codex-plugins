# Deployment Pipeline

After preflight passes, execute Phase 1–6 in order.

`SKILL_DIR` refers to the directory containing this skill's SKILL.md. Sibling skills are at `<SKILL_DIR>/../`.

Use `ENV` from preflight to choose between script mode (Node.js available) and fallback mode (AI-native).

## Artifact Directory

All pipeline outputs are written under `.sealos/` in `WORK_DIR`:

```
<WORK_DIR>/.sealos/
├── config.json                   ← user configuration overrides (manual, committed to git)
├── state.json                    ← deployment state (auto-maintained after Phase 6)
├── analysis.json                 ← project analysis snapshot (regenerated each deploy)
├── build/                        ← created only if Phase 4 actually runs
│   └── build-result.json         ← Phase 4 result (`success` or `failed`)
└── template/
    └── index.yaml                ← Phase 5 Sealos template
```

**File responsibilities:**
- `config.json` — optional user overrides (port, base_image, build_command, etc.). Created manually by user, committed to git. All fields optional.
- `analysis.json` — project analysis snapshot written after Phase 1 (language, framework, score, etc.). Regenerated each deploy.
- `state.json` — deployment state written after Phase 6 success. Contains `last_deploy` and `history`. Enables UPDATE mode on subsequent runs.

**Note:** When reading dockerfile-skill modules (analyze.md, generate.md, build-fix.md), they reference `docker-build/` as their default output path. In this pipeline, always write to `.sealos/build/` instead. Similarly, template output goes to `.sealos/template/` instead of `template/`.

JSON artifacts under `.sealos/` are governed by explicit schemas in `<SKILL_DIR>/schemas/`:
- `config.schema.json`
- `analysis.schema.json`
- `build-result.schema.json`
- `state.schema.json`

Validate them with:

```bash
node "<SKILL_DIR>/scripts/validate-artifacts.mjs" --dir "$WORK_DIR"
```

Writers should validate on write; readers should validate before trusting resume/update state.

At the very start of the pipeline (before Phase 1), create the base artifact directory:

```bash
mkdir -p "$WORK_DIR/.sealos" "$WORK_DIR/.sealos/template"
```

Create `"$WORK_DIR/.sealos/build"` lazily when Phase 4 starts. If Phase 2 finds an existing image and skips Phase 4, `build/` should remain absent rather than exist as an empty directory.

**Read user config (if exists):**
If `.sealos/config.json` exists, read it. User-provided values take priority over auto-detection and AI inference throughout the pipeline.

```json
{
  "port": 8080,
  "node_version": "20",
  "start_command": "node dist/main.js",
  "build_command": "pnpm build:prod",
  "system_deps": ["ffmpeg"],
  "base_image": "node:20-slim",
  "env_overrides": { "NODE_ENV": "production" },
  "skip_phases": ["assess"]
}
```
All fields are optional. If a field is present, it overrides the corresponding auto-detected value.

## Deployment Mode Detection

After preflight, determine whether this is a **first deploy** or an **update** of an existing deployment.

### Step 1: Check for previous deployment state

Read `.sealos/state.json` in `WORK_DIR`. If it exists and contains a `last_deploy` key with `app_name`, proceed to Step 2.

If no `last_deploy` key or file doesn't exist → proceed to **Step 1.5** (attempt discovery from cluster).

### Step 1.5: Discover existing deployment from cluster (migration)

Projects deployed by an older version of the skill may have no `last_deploy` section in state.json (or no state.json at all). If `ENV.kubectl` is true and `~/.sealos/kubeconfig` exists, attempt to discover an existing deployment by project name:

```bash
# Derive the namespace from the sealos kubeconfig
NAMESPACE=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  config view --minify -o jsonpath='{.contexts[0].context.namespace}' 2>/dev/null)

# Search for a deployment whose name starts with the repo name
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get deploy -n "$NAMESPACE" \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}' 2>/dev/null \
  | grep -i "^$REPO_NAME"
```

**If a match is found** (e.g., `evershop-uvbp0n0n	zhujingyang/evershop:20260309`):

1. Query the full details to reconstruct the `deployed` state:
```bash
# Get the ingress host
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get ingress/<app_name> -n "$NAMESPACE" \
  -o jsonpath='{.spec.rules[0].host}' 2>/dev/null
```

2. Present to user for confirmation:
```
Found an existing deployment that appears to match this project:

  App:       evershop-uvbp0n0n
  Image:     zhujingyang/evershop:20260309
  URL:       https://evershop-4ha6b4mh.gzg.sealos.run
  Namespace: ns-qiqovyrm

  Is this the deployment you want to update? (y/n)
```

3. If user confirms → write the reconstructed `last_deploy` section to `.sealos/state.json` (create file if needed), then proceed to Step 2.

4. If user says no, or no match found → **DEPLOY mode** (skip to Resume Detection below).

### Step 2: Verify deployment is still running (requires kubectl)

If `ENV.kubectl` is false:
- Inform user: `"Found previous deployment record for {app_name}, but kubectl is not available. Will create a new instance instead."`
- → **DEPLOY mode**

If `ENV.kubectl` is true, query the cluster:
```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get deployment/<app_name> -n <namespace> \
  -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null
```

- Command fails (deployment deleted or kubeconfig expired) → **DEPLOY mode** (remove `.sealos/state.json` or clear `last_deploy`)
- Command returns current image → proceed to Step 3

### Step 3: Ask user

Present the detected state and let the user choose:

```
Detected existing deployment:
  App:   <app_name>
  Image: <image>
  URL:   <url>

  1. Update this deployment (rebuild & push new image)
  2. Deploy as a new instance

Default: Update
```

- User picks **Update** → **UPDATE mode** (jump to Update Path below)
- User picks **New instance** → **DEPLOY mode** (rename state.json to state.json.bak)

---

## Resume Detection

**Only applies in DEPLOY mode.** Check for artifacts from a previous incomplete deploy using file existence:

| Condition | Meaning | Behavior |
|-----------|---------|----------|
| `.sealos/state.json` has `last_deploy` | Already deployed | Enter UPDATE mode (handled above) |
| `.sealos/analysis.json` exists | Phase 1 completed | Ask user: skip assessment? |
| `Dockerfile` exists | Phase 3 completed | Skip Dockerfile generation |
| `.sealos/build/build-result.json` exists and `outcome: "success"` | Phase 4 completed | Ask user: skip rebuild? |
| `.sealos/template/index.yaml` exists | Phase 5 completed | Ask user: skip template generation? |

If any artifacts exist, report to user:
`"Found artifacts from a previous deploy attempt. [list found artifacts]."`
Ask: `"Resume from where it left off? Or restart from Phase 1?"`

If restart → remove `.sealos/analysis.json`, `.sealos/build/`, `.sealos/template/index.yaml` and start fresh.

---

## Phase 1: Assess

`WORK_DIR`, `GITHUB_URL`, `REPO_NAME`, and README context are already resolved in preflight (Step 2).
Use those directly — no need to re-derive.

### 1.2 Deterministic Scoring

**If Node.js available:**
```bash
node "<SKILL_DIR>/scripts/score-model.mjs" "$WORK_DIR"
```
Output: `{ "score": N, "verdict": "...", "dimensions": {...}, "signals": {...} }`

**If Node.js not available (fallback):**
Perform the scoring yourself by reading project files and applying these rules:

1. Detect language: `package.json` → Node.js, `go.mod` → Go, `requirements.txt` → Python, `pom.xml` → Java, `Cargo.toml` → Rust
2. Detect framework: read dependency files for known frameworks (Next.js, Express, FastAPI, Gin, Spring Boot, etc.)
3. Check HTTP server: does the project listen on a port?
4. Check state: external DB (PostgreSQL/MySQL/MongoDB) vs local state (SQLite)?
5. Check config: `.env.example` exists?
6. Check Docker: `Dockerfile` or `docker-compose.yml` exists?

Score 6 dimensions (0-2 each, max 12). For detailed criteria, read:
`<SKILL_DIR>/../cloud-native-readiness/knowledge/scoring-criteria.md`

**Decision:**
- `score < 4` → STOP. Tell user: "This project scored {N}/12 ({verdict}). Not suitable for containerized deployment because: {dimension_details for 0-score dimensions}."
- `score >= 4` → CONTINUE.

### 1.3 AI Quick Assessment

Use structured signals from Phase 1.2 score-model output directly:
- `signals.primary_language` — primary language (priority-sorted when multiple detected)
- `signals.framework` — detected frameworks
- `signals.package_manager` — detected package manager (npm/yarn/pnpm/bun/pip/go/etc.)
- `signals.port` — detected port (from framework defaults)
- `signals.databases` — detected database types (postgres/mysql/mongodb/redis/sqlite)
- `signals.runtime_version` — runtime version with source (e.g., `{ node: "22", source: "engines" }`)
- `signals.is_monorepo`, `signals.has_docker`, `signals.has_env_example`

Focus AI effort on what the script cannot detect: env_vars classification,
complexity_tier assessment, and port override from source code (if `port_source` is "unknown").

Based on the score result and your own analysis of the project, assess:

1. Read key files: `README.md`, `package.json`/`go.mod`/`requirements.txt`, `Dockerfile` (if exists)
2. Check: Is this a web service, API, or worker with network interface?
3. Determine: ports, required env vars, database dependencies, special concerns

If the score is borderline (4-6), also read:
- `<SKILL_DIR>/../cloud-native-readiness/knowledge/scoring-criteria.md` — detailed rubrics
- `<SKILL_DIR>/../cloud-native-readiness/knowledge/anti-patterns.md` — disqualifying patterns

**STOP conditions:**
- Desktop/GUI application (Electron without server, Qt, GTK)
- Mobile app without backend
- CLI tool / library / SDK (no network service)
- No identifiable entry point or build system

Record for later phases: `language`, `framework`, `ports`, `env_vars`, `databases`, `has_dockerfile`

**Env var classification** (for Phase 5.5 interactive configuration):
When recording `env_vars`, also classify each one:
- `auto` — can be auto-generated (random secrets, internal URLs, DB connections)
- `required` — user must provide (external API keys, admin email, SMTP, OAuth)
- `optional` — has sensible default, user may customize (log level, feature flags)

Sources for env var detection:
- `.env.example` or `.env.sample` — most reliable source of required env vars
- `docker-compose.yml` `environment:` section
- README sections about configuration/environment
- Source code imports of `process.env.*` or `os.environ[]`

### Write analysis.json

After Phase 1 completes, write `.sealos/analysis.json` with the full analysis snapshot:

```json
{
  "generated_at": "<ISO timestamp>",
  "project": {
    "github_url": "<GITHUB_URL>",
    "work_dir": "<WORK_DIR>",
    "repo_name": "<REPO_NAME>",
    "branch": "<BRANCH or null>"
  },
  "score": { "total": "<N>", "verdict": "<verdict>", "dimensions": {} },
  "language": "<signals.primary_language>",
  "all_languages": ["<all detected languages from signals.language>"],
  "framework": "<detected framework>",
  "package_manager": "<npm|yarn|pnpm|bun|pip|go|cargo|maven|gradle>",
  "port": "<primary port>",
  "databases": ["<detected database types>"],
  "runtime_version": { "<language>": "<major version>", "source": "<detection source>" },
  "env_vars": {},
  "has_dockerfile": false,
  "complexity_tier": "<L1|L2|L3>",
  "image_ref": null
}
```

If `.sealos/config.json` exists, apply user overrides: e.g., if `config.json` has `"port": 8080`, use that instead of the auto-detected value. Priority: user config > script detection > AI inference.

The `image_ref` field is set to `null` initially. It will be filled in Phase 2 (if existing image found) or Phase 4 (after build).

### Present Analysis Summary

After writing `.sealos/analysis.json`, present a concise repository analysis summary to the user.
This summary should expose only the key conclusions, not the full artifact contents.

Recommended format:

```text
Repository Analysis:
  - Type: <web app | api | worker | cli | library>
  - Language: <language>
  - Framework: <framework or "none detected">
  - Port: <port or "not detected">
  - Database: <postgres/mysql/redis/... or "none detected">
  - Dockerfile: <yes/no>
  - Score: <N>/12 (<verdict>)
  - Decision: <continue | stop>
```

Output rules:
- Keep the summary short and decision-oriented
- Do not dump the full `env_vars` object or dimension-by-dimension internals unless the user asks
- Do not add a default "full details" block after this summary
- If the assessment stops the pipeline, briefly state the top blocker(s)
- If the assessment continues, state the next phase in one short line

---

## Phase 2: Detect Existing Image

**If Node.js available:**
```bash
# With GitHub URL:
node "<SKILL_DIR>/scripts/detect-image.mjs" "$GITHUB_URL" "$WORK_DIR"
# Local project without GitHub URL:
node "<SKILL_DIR>/scripts/detect-image.mjs" "$WORK_DIR"
```
The script auto-detects GitHub URL from `git remote` if only a directory is given.

Output: `{ "found": true, "image": "...", "tag": "...", ... }` or `{ "found": false }`

**If Node.js not available (fallback — use curl):**

1. Parse owner/repo from `GITHUB_URL` (if empty, try `git -C "$WORK_DIR" remote get-url origin`)
2. If still no GitHub URL, skip Docker Hub / GHCR checks and only scan project files for image references
3. Docker Hub check (try `<owner>/<repo>`, then `<repo>/<repo>` if different):
```bash
curl -sf "https://hub.docker.com/v2/namespaces/<owner>/repositories/<repo>/tags?page_size=10"
# If not found and owner != repo:
curl -sf "https://hub.docker.com/v2/namespaces/<repo>/repositories/<repo>/tags?page_size=10"
```
4. GHCR check:
```bash
TOKEN=$(curl -sf "https://ghcr.io/token?scope=repository:<owner>/<repo>:pull" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
curl -sf -H "Authorization: Bearer $TOKEN" "https://ghcr.io/v2/<owner>/<repo>/tags/list"
```
5. **docker-compose.yml scan** — AI reads `docker-compose.yml` / `docker-compose.yaml` (already in Phase 1 context) and extracts `image:` fields. Exclude infrastructure images (postgres, mysql, redis, mongo, etc.). For each candidate, verify with curl against Docker Hub or GHCR.
6. **CI workflow scan** — AI reads `.github/workflows/*.yml` and extracts `docker push` targets, `images:` fields, and `tags:` references. Verify each candidate.
7. Search `README.md` for `ghcr.io/` references, `docker run/pull` commands, and `hub.docker.com/r/<ns>/<repo>` URLs
8. **Docker Hub search API** (catch-all) — if nothing found above:
```bash
curl -sf "https://hub.docker.com/v2/search/repositories/?query=<repo>&page_size=5"
# For each result, fetch detail and check if full_description mentions github.com/<owner>/<repo>
curl -sf "https://hub.docker.com/v2/repositories/<ns>/<repo>/"
```
9. For any candidate, verify amd64: `docker manifest inspect <image>:<tag>`

Prefer versioned tags (`v1.2.3`) over `latest`.

### Phase 2 Post-Verification (AI)

After Phase 2 produces a result, the AI should cross-validate:

1. **If `source` is `dockerhub` or `ghcr`** (direct owner/repo match) — high confidence, no extra validation needed.
2. **If `source` is `compose`, `ci-workflow`, `dockerhub-readme`, or `dockerhub-search`** — cross-check with project context:
   - Does the README mention this image or its namespace?
   - Does `docker-compose.yml` reference it?
   - Does the Docker Hub repo description link back to this GitHub project?
   - If multiple signals agree → high confidence. If only one signal → note as medium confidence in your assessment.
3. **If `found: false`** — the AI should use its Phase 1 analysis context to attempt one more check: if Phase 1 identified a Docker image name from project docs or code that the script didn't find, try verifying it manually with curl.

### Update analysis.json

If an existing image is found, update `.sealos/analysis.json` to set `image_ref` to `{image}:{tag}`.

**Decision:**
- Found amd64 image → record `IMAGE_REF = {image}:{tag}`, **skip to Phase 5**
- Not found → continue to Phase 3

---

## Phase 3: Dockerfile

### 3.1 Check Existing Dockerfile

If `WORK_DIR/Dockerfile` exists:
1. Read it and assess quality
2. Reasonable (multi-stage or appropriate for language) → use directly, go to Phase 4
3. Problematic (uses `:latest`, runs as root, missing essential deps) → fix, then Phase 4

### 3.2 Generate Dockerfile

If no Dockerfile exists, generate one.

**Load the appropriate template from the internal dockerfile-skill:**
```
<SKILL_DIR>/../dockerfile-skill/templates/golang.dockerfile
<SKILL_DIR>/../dockerfile-skill/templates/nodejs-express.dockerfile
<SKILL_DIR>/../dockerfile-skill/templates/nodejs-nextjs.dockerfile
<SKILL_DIR>/../dockerfile-skill/templates/python-fastapi.dockerfile
<SKILL_DIR>/../dockerfile-skill/templates/python-django.dockerfile
<SKILL_DIR>/../dockerfile-skill/templates/java-springboot.dockerfile
```

Read the template matching the detected language/framework, then adapt it:
- Replace placeholder ports with detected ports
- Adjust build commands based on actual package manager (npm/yarn/pnpm/bun)
- Add system dependencies if needed
- Set correct entry point

**Pre-load Phase 1 analysis for analyze.md:**

Read `.sealos/analysis.json` before running analyze.md. The following fields are available
as pre-loaded context, so analyze.md can skip its overlapping detection steps:
`language`, `framework`, `package_manager`, `port`, `databases`, `has_dockerfile`, `complexity_tier`.

**For detailed analysis guidance, read:**
```
<SKILL_DIR>/../dockerfile-skill/modules/analyze.md    — 17-step analysis process
<SKILL_DIR>/../dockerfile-skill/modules/generate.md   — generation rules and best practices
```

**Validate generated Dockerfile:**

After generating the Dockerfile, run validation if Node.js is available:
```bash
node "<SKILL_DIR>/../dockerfile-skill/scripts/validate-dockerfile.mjs" "$WORK_DIR/Dockerfile" --port=<detected_port> --json
```
If validation reports errors, fix the Dockerfile before proceeding to Phase 4.
If Node.js is not available, manually verify the Validation Checklist in generate.md.

**Key Dockerfile principles:**
- Multi-stage build (builder + runtime)
- Pin base image versions (never `:latest`)
- Run as non-root user (USER 1001)
- Proper `.dockerignore`

Also generate `.dockerignore`:
```
.git
node_modules
__pycache__
.env
.env.local
*.md
.vscode
.idea
.sealos
```

---

## Phase 4: Build & Push

### 4.0 Choose Image Destination

Registry selection is deferred to this phase because it's only needed when building.
If Phase 2 found an existing image, this phase is skipped entirely.

Before any login step, tell the user:

```text
This app will be built locally with Docker.
Choose where to push the image:

  1. GHCR (recommended) — agent can run `gh auth login` and finish browser auth with you
  2. Docker Hub — public images only; use your existing `docker login` session, or run `docker login` in another terminal
```

Default to **GHCR** when the user says "either is fine".

Important:
- This choice is about the image registry only. Local builds still require Docker either way.
- If the user chooses GHCR, use `gh auth login` as the preferred interactive auth path.
- If the user chooses Docker Hub, treat that path as public-image only.
- If the user chooses Docker Hub and there is no active Docker Hub session, stop and ask the user to run `docker login` in another terminal before continuing.

**If the user chooses GHCR:**
```bash
gh auth status 2>/dev/null
```
If authenticated:
```bash
GH_USER=$(gh api user -q .login)
gh auth token | docker login ghcr.io -u "$GH_USER" --password-stdin
REGISTRY=ghcr
```
Important:
- Before the first GHCR push, ensure the local `gh` session has `write:packages`.
- For GHCR, `write:packages` is sufficient for both pushing and later creating the app-scoped image pull Secret. GitHub CLI may not show a separate `read:packages` entry even though pull access works.
- If the current session is missing GHCR package access, refresh with:
  `node "<SKILL_DIR>/scripts/gh-refresh-scopes.mjs" write:packages`
- When `build-push.mjs` or `ensure-image-pull-secret.mjs` runs inside a TTY, it will now ask once whether it should refresh missing GHCR scopes and, on `y`, run `gh auth refresh` in the same PTY before continuing.
- If `gh auth refresh` exits successfully but the scopes are still missing, the script will immediately fall back to a full `gh auth login --web --scopes ...` in the same PTY and only continue after re-checking the scopes.
- A successful GHCR push does **not** guarantee Sealos can pull the image.
- For private GHCR packages, keep the deployment path GHCR-first and create an image pull Secret from the local `gh` CLI session before applying or updating workloads.
- Do **not** surface raw registry host/username/password/email as user-facing template inputs when local `gh auth status` is already available.

If `build-push.mjs` or `ensure-image-pull-secret.mjs` returns:
```json
{
  "action": "gh_scope_refresh_required",
  "tty_required": true,
  "suggested_command": "node <SKILL_DIR>/scripts/gh-refresh-scopes.mjs write:packages"
}
```
then the agent should:
1. Ask the user once: `Missing GitHub Packages permission for GHCR. Refresh now? (y/n)`
2. If the current script is already running in a PTY, answer `y` there and let it continue in-place
3. Otherwise run the `suggested_command` in the **current PTY/TTY session**
4. If `gh` prompts `Press Enter to open github.com in your browser...`, send `Enter` in the same PTY
5. After the refresh command exits successfully, retry the exact failed command automatically

Do not tell the user to open a separate terminal when the current agent session can run a PTY command.

If `gh` is installed but not authenticated, explicitly tell the user that GHCR push requires GitHub CLI login, then trigger:
```bash
gh auth login
```
After successful login, retry GHCR authentication and continue.

**If the user chooses Docker Hub:**
```bash
docker info 2>/dev/null | grep "Username:"
```
If a Docker Hub session exists, use it:
```bash
DOCKER_HUB_USER=<extracted username>
REGISTRY=dockerhub
```

Treat this path as **public image only**.
Do not add Docker Hub private-image credential prompts or Docker Hub pull-secret automation in `sealos-deploy`.

If no Docker Hub session exists, tell the user:
```
Docker Hub push requires a local Docker Hub login session.
Please run `docker login` in another terminal, then continue this deploy.
```

### 4.1 Build & Push

Tag format: `<owner-or-user>/<repo-name>:YYYYMMDD-HHMMSS` (e.g., `ghcr.io/zhujingyang/kite:20260304-143022`). The timestamp ensures same-day rebuilds never collide.

Before invoking the build helper, create the build artifact directory:

```bash
mkdir -p "$WORK_DIR/.sealos/build"
```

**If Node.js available:**
```bash
node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "<repo-name>" --registry ghcr
node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "<repo-name>" --registry dockerhub --user "<user>"
```
Run the command that matches the user's chosen destination:
- GHCR: `node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "<repo-name>" --registry ghcr`
- Docker Hub: `node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "<repo-name>" --registry dockerhub`

Output: `{ "success": true, "image": "...", "registry": "ghcr" }` or `{ "success": false, "error": "..." }`

For GHCR success, record whether the image is anonymously pullable. If Phase 4 built a GHCR image and it is still private, continue with the GHCR image and let Phase 6 create/update the pull Secret automatically from `gh auth token`.
If Phase 2 reused an existing public image, do **not** trigger the GHCR pull-secret flow.

**If Node.js not available (fallback — run docker directly):**
```bash
TAG=$(date +%Y%m%d-%H%M%S)
```

If the user chose GHCR:
```bash
GH_USER=$(gh api user -q .login)
gh auth token | docker login ghcr.io -u "$GH_USER" --password-stdin
IMAGE="ghcr.io/$GH_USER/<repo-name>:$TAG"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push -f Dockerfile "$WORK_DIR"
```

If the user chose Docker Hub:
```bash
DOCKER_HUB_USER=$(docker info 2>/dev/null | sed -n 's/^ Username: //p')
IMAGE="$DOCKER_HUB_USER/<repo-name>:$TAG"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push -f Dockerfile "$WORK_DIR"
```

If `$IMAGE` is a GHCR image, immediately verify it is anonymously pullable before proceeding:

```bash
TOKEN=$(curl -fsSL "https://ghcr.io/token?scope=repository:$GH_USER/<repo-name>:pull" | sed -n 's/.*"token":"\\([^"]*\\)".*/\\1/p')
curl -fsSLI \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json" \
  "https://ghcr.io/v2/$GH_USER/<repo-name>/manifests/$TAG"
```

If that check returns 401/403 or the package visibility is still private, continue with the build but mark that Phase 6 must create/update the namespace image pull Secret before rollout.
If the run is using an existing public image instead of a new local build, skip this secret-creation path.

### 4.2 Error Handling

If build fails:
1. Read the error output
2. Load error patterns from internal skill:
   ```
   <SKILL_DIR>/../dockerfile-skill/knowledge/error-patterns.md
   ```
3. Match the error → apply fix to Dockerfile → retry
4. Also consult if needed:
   ```
   <SKILL_DIR>/../dockerfile-skill/knowledge/system-deps.md
   <SKILL_DIR>/../dockerfile-skill/knowledge/best-practices.md
   ```
5. Max 3 retry attempts
6. If still failing → inform user with the specific error and suggest manual review

### 4.3 Record Result

Always write `.sealos/build/build-result.json` when Phase 4 runs:

- Success: `outcome: "success"` plus pushed image metadata
- Failure: `outcome: "failed"` plus the captured error message

This avoids leaving an empty `build/` directory after a failed build and makes resume/debug behavior inspectable.

On success, record `IMAGE_REF` from the build output. The build result file is at `.sealos/build/build-result.json`.

### Update analysis.json

On successful build, update `.sealos/analysis.json` to set `image_ref` to the built image reference.

---

## Phase 5: Generate Sealos Template

### 5.1 Load Sealos Rules

Read the internal skill's specifications:
```
<SKILL_DIR>/../docker-to-sealos/SKILL.md                       — 7-step workflow + MUST rules
<SKILL_DIR>/../docker-to-sealos/references/sealos-specs.md     — Sealos ordering, labels, conventions
<SKILL_DIR>/../docker-to-sealos/references/conversion-mappings.md — field-level Docker→Sealos mappings
```

If the project uses databases, also read:
```
<SKILL_DIR>/../docker-to-sealos/references/database-templates.md
```

If the project mentions Frappe, ERPNext, HRMS, or `bench`, also read:
```
<SKILL_DIR>/../docker-to-sealos/references/frappe-bench.md
```

### 5.2 Generate Template

Read `.sealos/analysis.json` and use `image_ref`, `port`, `databases`, and `env_vars` as inputs.

Generate the template at `.sealos/template/index.yaml` (overrides the default `template/` path from docker-to-sealos skill).

**Public URL detection:**
After generating the base template, check if the app needs its public URL configured:

1. Search source code for common URL config patterns:
   - Env vars: `BASE_URL`, `SITE_URL`, `APP_URL`, `NEXTAUTH_URL`, `PUBLIC_URL`, `EXTERNAL_URL`
   - Config files: `getConfig(.*[Uu]rl`, `homeUrl`, `baseUrl`, `siteUrl` in config patterns
   - Docker Compose env vars referencing `localhost` or placeholder URLs

2. If public URL is needed via env var:
   - Add the appropriate env var to the Deployment with value `https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}`

3. If public URL is needed via config file (e.g., node-config):
   - Create a ConfigMap with the minimal config file
   - Add volumeMount and volume to the Deployment
   - Follow ConfigMap MUST rules (labels, naming, ordering before Deployment)

**Critical MUST rules (always apply):**
- `metadata.name`: hardcoded lowercase, no variables
- Image tag: exact version, **never `:latest`**
- PVC requests: `<= 1Gi`
- Container defaults: `cpu: 200m/20m`, `memory: 256Mi/25Mi`
- Init containers must define explicit resources; do not rely on namespace defaults. For expensive init work such as framework install, database migration, asset compilation, or `bench new-site`, allocate enough memory for the task.
- `imagePullPolicy: IfNotPresent`
- `revisionHistoryLimit: 1`
- `automountServiceAccountToken: false`
- `template.spec.imagePullSecrets: [{ name: ${{ defaults.app_name }} }]` for managed workloads
- **App CRD** (last resource): only `spec.data.url`, `spec.displayType`, `spec.icon`, `spec.name`, `spec.type` — no other fields (no `menuData`, `nameColor`, `template`, etc.)
- **App CRD fixed enums**: `spec.displayType` must be `normal`; `spec.type` must be `link`

### 5.3 Validate

Run validation if Python is available:
```bash
python "<SKILL_DIR>/../docker-to-sealos/scripts/quality_gate.py" 2>/dev/null
```

If Python is not available, validate manually by checking the MUST rules above against the generated YAML.

Template is written to `.sealos/template/index.yaml`. No separate checkpoint file — the template file's existence is sufficient for resume detection.

---

## Phase 5.5: Interactive Configuration

After generating the template, guide the user through application configuration before deployment.
This is a **critical** step — most applications need user-specific configuration to function properly.

### 5.5.1 Extract Configuration from Template

Parse the generated template YAML and categorize all environment variables and inputs:

**Category A — Auto-managed (no user action needed):**
- `defaults.*` values: `app_name`, `app_host`, random passwords/keys (`${{ random(N) }}`)
- Database connections via `secretKeyRef`: host, port, username, password from Kubeblocks secrets
- Object storage credentials via `secretKeyRef`
- Composed URLs that reference auto-managed vars (e.g., `DATABASE_URL` built from `$(DB_HOST):$(DB_PORT)`)
- Internal service FQDNs (`*.${{ SEALOS_NAMESPACE }}.svc.cluster.local`)

**Category B — User-required inputs:**
- Template `inputs` with `required: true` and no sensible default
- Env vars with empty or placeholder values that the app cannot function without
- Common examples: admin email, external API keys (OpenAI, SMTP credentials, OAuth client ID/secret)

**Category C — Optional with defaults:**
- Template `inputs` with `required: false` and reasonable defaults
- Env vars user might want to customize but app works without changes
- Common examples: log level, feature toggles, upload size limits, signup enabled/disabled

**Category D — Fixed values (informational):**
- Hardcoded env vars like `NODE_ENV=production`
- Port numbers, internal paths

### 5.5.2 Present Configuration Summary

Display a structured summary to the user. Example:

```
Configuration for <app-name>:

  Auto-configured (no action needed):
    - APP_NAME: unique generated name
    - DB credentials: from PostgreSQL service (auto-provisioned)
    - SECRET_KEY: auto-generated 32-char random string
    - REDIS_URL: auto-composed from service credentials

  Requires your input:
    1. ADMIN_EMAIL — Administrator email address (required)
    2. OPENAI_API_KEY — OpenAI API key for AI features (required)
    3. SMTP_HOST — SMTP server for sending emails (required if email needed)

  Optional (defaults shown, customize if needed):
    - LOG_LEVEL: "info"
    - MAX_UPLOAD_SIZE: "10M"
    - ENABLE_SIGNUP: "true"
```

### 5.5.3 Collect User Input

**For required inputs:**
1. Ask the user for each value
2. If user doesn't have a value, explain what it's used for and how to obtain it
   - Example: "OPENAI_API_KEY is needed for AI features. Get one at https://platform.openai.com/api-keys"
3. If user wants to skip a feature-gating input (e.g., SMTP), explain which features will be unavailable and set an empty value

**For optional inputs:**
1. Show the default values
2. Ask: "Do you want to change any of these? (press Enter to keep defaults)"
3. Only update values the user explicitly wants to change

**For unfamiliar env vars:**
If the AI is unsure what a variable does, read the project README, `.env.example`, or source code to explain it to the user before asking for a value.

### 5.5.4 Apply Configuration to Template

Update the template's `inputs` section with user-provided values:

```yaml
# Before (generated)
inputs:
  ADMIN_EMAIL:
    description: 'Administrator email address'
    type: string
    default: ''
    required: true

# After (user configured)
inputs:
  ADMIN_EMAIL:
    description: 'Administrator email address'
    type: string
    default: 'admin@example.com'
    required: true
```

Write the updated template back to `.sealos/template/index.yaml`.

Record all user choices as `CONFIG` for use in Phase 6:
```
CONFIG.args = { ADMIN_EMAIL: "admin@example.com", OPENAI_API_KEY: "sk-..." }
```
These `args` will be passed to the Template API's `args` field (Phase 6.2), which overrides or supplies `spec.inputs` in the template.

### 5.5.5 Deployment Confirmation

Before proceeding to Phase 6, present a final summary and ask for confirmation:

```
Ready to deploy <app-name> to Sealos Cloud:

  Image:    zhujingyang/app:20260309
  Region:   https://usw-1.sealos.io
  Database: PostgreSQL 16 (auto-provisioned)
  Config:   3 required inputs configured, 2 optional defaults kept

  Proceed with deployment? (y/n)
```

Wait for user confirmation before continuing to Phase 6.

Configuration is applied directly to `.sealos/template/index.yaml`. No separate checkpoint — the template contains the final configured state.

---

## Phase 6: Deploy to Sealos Cloud

### 6.1 Construct Deploy URL

The template deploy API uses a fixed `template.` subdomain prefix on the region domain:

```
Region example:     https://usw-1.sealos.io
Deploy URL example: https://template.usw-1.sealos.io/api/v2alpha/templates/raw
```

Do not send requests to the literal placeholder form `https://template.<region-domain>/...`.
Always derive `REGION_DOMAIN` first, then build `DEPLOY_URL` from the real value.

Extract the region from `~/.sealos/auth.json` (saved during preflight auth):
```bash
REGION=$(jq -r '.region' ~/.sealos/auth.json)
REGION_DOMAIN=$(printf '%s' "$REGION" | sed -E 's#^https?://##; s#/$##')
DEPLOY_URL="https://template.${REGION_DOMAIN}/api/v2alpha/templates/raw"
```

### 6.2 Deploy Template

Read kubeconfig, **encode it with `encodeURIComponent`**, and send as `Authorization` header.

Request body fields:
- `yaml` (required) — the full template YAML string
- `args` (optional) — template variable key-value pairs that override or supply `spec.inputs` fields. Values from Phase 5.5 `CONFIG.args`.
- `dryRun` (optional, boolean) — if true, validates resources against K8s API without creating anything. Returns 200 with preview.

**With Node.js (preferred):**
```bash
node "<SKILL_DIR>/scripts/deploy-template.mjs" ".sealos/template/index.yaml" --dry-run
node "<SKILL_DIR>/scripts/deploy-template.mjs" ".sealos/template/index.yaml" --args-json '{"ADMIN_EMAIL":"user@example.com"}'
```

This script is the preferred execution path because it:
- reads `~/.sealos/auth.json` directly instead of fragile shell parsing
- derives `REGION_DOMAIN` from the real `region` value
- always posts to the concrete `DEPLOY_URL`
- emits structured JSON on success or failure

**Without Node.js (curl fallback):**
```bash
# encodeURIComponent via Python (almost always available)
KUBECONFIG_ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.stdin.read(), safe=''))" < ~/.sealos/kubeconfig)

# Build JSON body with args — use jq if available
TEMPLATE_YAML=$(cat .sealos/template/index.yaml)
jq -n --arg yaml "$TEMPLATE_YAML" \
  --argjson args '{"ADMIN_EMAIL":"user@example.com"}' \
  '{yaml: $yaml, args: $args}' | \
  curl -sf -X POST "$DEPLOY_URL" \
    -H "Authorization: $KUBECONFIG_ENCODED" \
    -H "Content-Type: application/json" \
    -d @-
```

**Without jq:**
The AI should read the template YAML (already in context), construct the JSON body directly, write it to a temp file, and curl it:
```bash
# AI writes properly escaped JSON to temp file including args from Phase 5.5
cat > /tmp/sealos-deploy-body.json << 'DEPLOY_EOF'
{"yaml": "<AI inserts JSON-escaped template YAML here>", "args": {"ADMIN_EMAIL": "user@example.com"}}
DEPLOY_EOF

curl -sf -X POST "$DEPLOY_URL" \
  -H "Authorization: $KUBECONFIG_ENCODED" \
  -H "Content-Type: application/json" \
  -d @/tmp/sealos-deploy-body.json

rm -f /tmp/sealos-deploy-body.json
```

### 6.3 Handle Response

All error responses use a unified format:
```json
{ "error": { "type": "...", "code": "...", "message": "...", "details": ... } }
```

| Status | Meaning | Action |
|--------|---------|--------|
| 201 | Deployed successfully | Extract instance name and resources from response |
| 200 | Dry-run preview (`dryRun: true`) | Show resource preview and quota |
| 400 | Validation error — `INVALID_PARAMETER` (missing yaml/name) or `INVALID_VALUE` (bad YAML, missing required args) | Read `error.message`, fix template or provide missing `args`, retry |
| 401 | `AUTHENTICATION_REQUIRED` — missing or invalid kubeconfig | Re-run auth: `node sealos-auth.mjs login`, or switch workspace: `node sealos-auth.mjs switch <ns>` |
| 403 | `FORBIDDEN` — insufficient permissions | Inform user, check kubeconfig namespace permissions |
| 409 | `ALREADY_EXISTS` — instance already exists | Inform user, suggest different app name |
| 422 | `RESOURCE_ERROR` — K8s rejected resource spec | Read `error.details` for K8s rejection reason, fix template |
| 503 | `SERVICE_UNAVAILABLE` — K8s cluster unreachable | **Fall back to kubectl (6.4)** |

On 201 success, the response contains:
```json
{
  "name": "myapp-abcdefgh",
  "uid": "...",
  "resourceType": "instance",
  "displayName": "...",
  "createdAt": "...",
  "args": { ... },
  "resources": [
    { "name": "myapp-abcdefgh", "uid": "...", "resourceType": "deployment", "quota": { "cpu": 0.1, "memory": 0.25, "storage": 0, "replicas": 1 } }
  ]
}
```
Extract the instance name and present to user.

### 6.3.1 Post-Deploy Readiness Verification

After a 201 response, do not assume the app is usable. Verify Kubernetes readiness:

```bash
NAMESPACE=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  config view --minify -o jsonpath='{.contexts[0].context.namespace}')

KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get pod,svc,endpoints,ingress -n "$NAMESPACE" -l app=<app-name>
```

For the public app Service, endpoints must be non-empty before the Ingress can serve traffic. If the URL returns `no healthy upstream` or HTTP 503:

1. Check `endpoints/<app-name>`; empty endpoints means the backend Pod is not Ready.
2. Check Pod init container status and previous logs:
   ```bash
   KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
     logs pod/<pod> -n "$NAMESPACE" -c <init-container> --previous --tail=200
   ```
3. Look for common signatures:
   - `OOMKilled` or exit `137`: increase init container memory and recreate the Pod.
   - `Permission denied` on mounted paths: add `fsGroup` or a one-shot permission repair for existing PVCs.
   - App-specific migration/bootstrap errors: repair the failed bootstrap state, then rerun the init path.
4. Only report the app as usable after the endpoint exists and an HTTP request to the public URL returns a non-5xx response.

### 6.4 Fallback: kubectl apply (when Template API is unavailable)

If the Template API returns 503/500 or is unreachable, deploy directly via kubectl using the local kubeconfig.

**Step 1 — Gather cluster context:**
```bash
# User namespace
NAMESPACE=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify config view --minify -o jsonpath='{.contexts[0].context.namespace}')

# Cluster domain (from region URL)
CLOUD_DOMAIN=$(jq -r '.region' ~/.sealos/auth.json | sed -E 's#^https?://##; s#/$##')

# TLS secret name (from existing ingress, or default)
CERT_SECRET=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.tls[0].secretName}' 2>/dev/null || echo "wildcard-cert")
```

**Step 2 — Render template variables:**

The template YAML from Phase 5 contains `${{ }}` variables. The AI must replace them with actual values:

| Variable | Value |
|----------|-------|
| `${{ defaults.app_name }}` | Generate: `<app>-<random8>` (e.g., `edict-xn22k4ie`) |
| `${{ defaults.app_host }}` | Generate: `<app>-<random8>` (e.g., `edict-2v4jryz1`) |
| `${{ defaults.<key> }}` | Other defaults: generate per their `value` pattern |
| `${{ inputs.<key> }}` | User-provided values from Phase 5.5 `CONFIG.args` |
| `${{ random(N) }}` | Random alphanumeric string of length N |
| `${{ SEALOS_CLOUD_DOMAIN }}` | `CLOUD_DOMAIN` from Step 1 |
| `${{ SEALOS_CERT_SECRET_NAME }}` | `CERT_SECRET` from Step 1 |
| `${{ SEALOS_NAMESPACE }}` | `NAMESPACE` from Step 1 |

**Important:** `${{ inputs.xxx }}` values come from the user in Phase 5.5. If any required input was not provided, the AI must ask the user now before proceeding.

The AI reads the template YAML, performs all variable substitutions, and produces rendered K8s resource documents.

**Step 3 — Split and apply:**

The rendered YAML is a multi-document file (separated by `---`). Split it into individual resources:

1. **Skip** the first document (`kind: Template`) — this is the Sealos template metadata, not a K8s resource
2. **Apply** the remaining documents (Deployment, Service, Ingress, App, etc.) via kubectl:

```bash
# AI writes the rendered resources (without the Template CR) to a temp file
cat > /tmp/sealos-deploy-rendered.yaml << 'EOF'
<rendered Deployment + Service + Ingress + App YAML>
EOF

KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify apply -f /tmp/sealos-deploy-rendered.yaml -n "$NAMESPACE"
rm -f /tmp/sealos-deploy-rendered.yaml
```

**Step 4 — Handle apply errors:**

| Error | Fix |
|-------|-----|
| `unknown field "spec.xxx"` in App CR | Remove the unknown field and retry |
| PodSecurity warnings | Warnings are non-blocking — deployment still proceeds |
| `Forbidden` | Kubeconfig may be expired — re-run auth |
| `already exists` | Resource exists from a previous deploy — use `kubectl apply` (idempotent) |

**Step 5 — Verify deployment:**
```bash
# Wait for pod to be ready (max 120s)
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  wait --for=condition=available deployment/<app-name> -n "$NAMESPACE" --timeout=120s

# Get pod status
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get pods -l app=<app-name> -n "$NAMESPACE"
```

App URL: `https://<app_host>.<CLOUD_DOMAIN>`

### Write state.json

**This is critical for enabling future updates.** After a successful deploy, write `.sealos/state.json`:

```json
{
  "version": "1.0",
  "last_deploy": {
    "app_name": "<instance name, e.g. evershop-uvbp0n0n>",
    "app_host": "<ingress host prefix, e.g. evershop-4ha6b4mh>",
    "namespace": "<K8s namespace from kubeconfig>",
    "region": "<Sealos region domain, e.g. gzg.sealos.run>",
    "image": "<IMAGE_REF used in this deploy>",
    "docker_hub_user": "<DOCKER_HUB_USER, or null if existing image was used>",
    "repo_name": "<REPO_NAME>",
    "url": "<public app URL>",
    "deployed_at": "<current ISO timestamp>",
    "last_updated_at": "<current ISO timestamp>"
  },
  "history": [
    {
      "at": "<current ISO timestamp>",
      "action": "deploy",
      "image": "<IMAGE_REF>",
      "method": "<template-api or kubectl-apply>",
      "status": "success",
      "note": "Initial deployment"
    }
  ]
}
```

The `last_deploy` section is what **Deployment Mode Detection** reads on subsequent runs to decide between DEPLOY and UPDATE mode. Without it, every `/sealos-deploy` creates a new instance.

The `history` array is append-only — every subsequent update (via Update Path) adds an entry. See the **Update History** section at the end of this file for the full schema and rules.

Sources for each field:
- `app_name`: from Template API response `name` or the rendered `defaults.app_name` (kubectl apply)
- `app_host`: from the rendered `defaults.app_host` value, or parsed from the Ingress host
- `namespace`: from kubeconfig context
- `region`: from `~/.sealos/auth.json` `region` field (strip `https://`)
- `image`: from `analysis.json` `image_ref`
- `docker_hub_user`: from Phase 4 `DOCKER_HUB_USER` (null if Phase 2 found existing image)
- `repo_name`: from `analysis.json` `project.repo_name`
- `url`: constructed from `app_host` and `region`

---

## Cleanup

If `WORK_DIR` was created via `mktemp` (remote GitHub URL clone), remove it:
```bash
rm -rf "$WORK_DIR"
```

Do NOT clean up if `WORK_DIR` is the user's local project directory.

---

## Output

On success, present to user:

```
✓ Assessed: {language} + {framework}, score {N}/12 — {verdict}
✓ Image: {IMAGE_REF} ({source: existing/built})
✓ Template: .sealos/template/index.yaml
✓ Configured: {N} inputs set ({M} required, {K} optional)
✓ Deployed to Sealos Cloud ({region})

App URL: https://<app-access-url>

To update this deployment later, run: /sealos-deploy
```

If any `inputs` were configured, also show:
```
Configuration applied:
  ADMIN_EMAIL: admin@example.com
  OPENAI_API_KEY: sk-***...*** (masked)
```
Mask sensitive values (API keys, passwords) — show only first 3 and last 3 characters.

---
---

# Update Path

**This section is only executed in UPDATE mode** (entered via Deployment Mode Detection above).

The update path skips Assess, Detect Image, Dockerfile, and Template generation — it reuses the existing deployment and only pushes a new image.

All kubectl commands use the Sealos kubeconfig:
```
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify
```

**Reminder:** `kubectl delete` requires user confirmation — see SKILL.md "kubectl Safety Rules".

## Context from Mode Detection

These values are already known from `.sealos/state.json` `last_deploy` section:

```
APP_NAME      = last_deploy.app_name       (e.g., "evershop-uvbp0n0n")
NAMESPACE     = last_deploy.namespace      (e.g., "ns-qiqovyrm")
REGION        = last_deploy.region         (e.g., "gzg.sealos.run")
CURRENT_IMAGE = last_deploy.image          (e.g., "zhujingyang/evershop:20260309")
DOCKER_HUB_USER = last_deploy.docker_hub_user
REPO_NAME     = last_deploy.repo_name
APP_URL       = last_deploy.url
```

---

## Phase U1: Build & Push

Ask the user what changed:

```
What would you like to update?

  1. Code changed — rebuild and push new image (default)
  2. Just restart the current deployment (no rebuild)
```

### Option 1: Rebuild

Reuse the **exact same build logic as Phase 4** — same Dockerfile, same explicit registry choice, same build-push.mjs or fallback.
Default to the registry used by `CURRENT_IMAGE`, but let the user switch if they want.

```bash
# With Node.js:
node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "$REPO_NAME" --registry ghcr
node "<SKILL_DIR>/scripts/build-push.mjs" "$WORK_DIR" "$REPO_NAME" --registry dockerhub

# Without Node.js:
TAG=$(date +%Y%m%d-%H%M%S)
NEW_IMAGE="<selected-user>/$REPO_NAME:$TAG"
docker buildx build --platform linux/amd64 -t "$NEW_IMAGE" --push -f Dockerfile "$WORK_DIR"
```

Record `NEW_IMAGE` from the output.

If build fails → same error handling as Phase 4.2 (read error-patterns.md, fix Dockerfile, retry up to 3 times).

### Option 2: Restart only

No build needed. Use the current image:
```
NEW_IMAGE = CURRENT_IMAGE
```

Will trigger a rollout restart in Phase U2.

---

## Phase U2: Apply Update

### Image update (Option 1 — new image built):

If `NEW_IMAGE` starts with `ghcr.io/`, create or refresh the app-scoped pull Secret and make sure the existing Deployment references it before swapping images:

```bash
node "<SKILL_DIR>/scripts/ensure-image-pull-secret.mjs" "$NAMESPACE" "$APP_NAME" "$NEW_IMAGE" "$APP_NAME"
```

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  set image deployment/$APP_NAME \
  $APP_NAME=$NEW_IMAGE \
  -n $NAMESPACE
```

### Restart only (Option 2 — no new image):

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  rollout restart deployment/$APP_NAME \
  -n $NAMESPACE
```

---

## Phase U3: Verify Rollout

### Wait for new pods to be ready:

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  rollout status deployment/$APP_NAME \
  -n $NAMESPACE --timeout=120s
```

### On success:

Update `.sealos/state.json`:
- Set `last_deploy.image` to `NEW_IMAGE`
- Set `last_deploy.last_updated_at` to current ISO timestamp
- Append an entry to `history` (see Update History below)

Present to user:
```
✓ Updated: <APP_NAME>
✓ Image: <CURRENT_IMAGE> → <NEW_IMAGE>
✓ Rollout: complete

App URL: <APP_URL>

To update again later, run: /sealos-deploy
```

### On failure:

Auto-rollback:
```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  rollout undo deployment/$APP_NAME \
  -n $NAMESPACE
```

Append a **failed** entry to `history` in `.sealos/state.json` (see Update History below).

Report to user:
```
✗ Rollout failed — automatically rolled back to previous version.

Debug:
  kubectl logs deployment/<APP_NAME> -n <NAMESPACE> --tail=50
```

Do NOT update `last_deploy.image` on failure — it stays at the old value.

---

## Update History

Every update (successful or failed) appends an entry to `history` in `.sealos/state.json`. This provides a traceable log of all changes to the deployment.

```json
{
  "version": "1.0",
  "last_deploy": {
    "app_name": "morphic-dc21ad72",
    "image": "zhujingyang/morphic:20260310-143022"
  },
  "history": [
    {
      "at": "2026-03-09T18:37:30Z",
      "action": "deploy",
      "image": "ghcr.io/miurla/morphic:668daf0e",
      "method": "kubectl-apply",
      "status": "success",
      "note": "Initial deployment"
    },
    {
      "at": "2026-03-09T20:15:00Z",
      "action": "set-env",
      "changes": ["OPENAI_API_KEY=sk-***", "OPENAI_BASE_URL=https://..."],
      "method": "kubectl-set-env",
      "status": "success",
      "note": "Fix: default openai provider not enabled"
    },
    {
      "at": "2026-03-10T14:30:22Z",
      "action": "set-image",
      "previous_image": "ghcr.io/miurla/morphic:668daf0e",
      "image": "zhujingyang/morphic:20260310-143022",
      "method": "kubectl-set-image",
      "status": "success"
    },
    {
      "at": "2026-03-11T09:00:00Z",
      "action": "set-image",
      "previous_image": "zhujingyang/morphic:20260310-143022",
      "image": "zhujingyang/morphic:20260311-090000",
      "method": "kubectl-set-image",
      "status": "failed",
      "note": "CrashLoopBackOff — rolled back"
    }
  ]
}
```

### History entry fields

| Field | Required | Description |
|-------|----------|-------------|
| `at` | yes | ISO 8601 timestamp of the operation |
| `action` | yes | What changed: `deploy`, `set-image`, `set-env`, `patch`, `restart` |
| `status` | yes | `success` or `failed` |
| `method` | yes | kubectl command used: `kubectl-apply`, `kubectl-set-image`, `kubectl-set-env`, `kubectl-patch`, `kubectl-rollout-restart` |
| `image` | if image changed | New image reference |
| `previous_image` | if image changed | Image before the update |
| `changes` | if env/config changed | Array of changes (mask sensitive values: `sk-***`) |
| `note` | no | Free-text reason or context for the change |

### Rules

- **Always append, never rewrite** — history is append-only. Never delete or modify previous entries.
- **Mask secrets** — API keys, passwords, tokens: show only first 3 chars + `***` (e.g., `sk-***`).
- **Initial deploy counts** — the first entry should be `action: "deploy"` written by Phase 6 checkpoint.
- **Failed updates count** — record failures so the user can see what was attempted and why it didn't work.
- **Keep it bounded** — if history exceeds 50 entries, trim the oldest entries (keep the first `deploy` entry and the most recent 49).
### 6.1.5 Ensure Image Pull Secret (locally built private GHCR path only)

Before calling the Template API or `kubectl apply`, check whether this run actually passed through Phase 4 local build and push.
This step is only for cases where:
- Phase 4 built a new GHCR image locally with Docker
- That GHCR image is not anonymously pullable

Do **not** run this step when:
- Phase 2 reused an existing public image
- The selected registry was Docker Hub public image flow

The template itself should reference the app-scoped pull Secret name via:

```yaml
imagePullSecrets:
  - name: ${{ defaults.app_name }}
```

If the run meets the locally built private-GHCR conditions above, create or update the app-scoped pull Secret in the target namespace using the local `gh` CLI session:

```bash
node "<SKILL_DIR>/scripts/ensure-image-pull-secret.mjs" "$NAMESPACE" "$APP_NAME" "$IMAGE_REF"
```

Behavior:
- Uses `gh api user -q .login` and `gh auth token`
- Creates/updates a `docker-registry` Secret named exactly like the app (`$APP_NAME`)
- When a deployment name is provided, also patches `spec.template.spec.imagePullSecrets` to include that app-scoped Secret
- Keeps registry credentials out of the generated template inputs
- Do not call it for existing public images

This step should run for both fresh deploys and in-place updates before rollout, but only on the locally built private-GHCR path.
