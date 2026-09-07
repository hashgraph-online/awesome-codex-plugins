# Deployment Pipeline

After preflight passes, execute the deployment eligibility gate, then Phase 1–6 in
order.

After eligibility passes and before Phase 1, execute Phase 0.5 Template Fast Path
when a GitHub repository reference is available.

`SKILL_DIR` refers to the directory containing this skill's SKILL.md. Sibling skills are at `<SKILL_DIR>/../`.

Use `ENV` from preflight to choose between script mode (Node.js available) and fallback mode (AI-native).

## Phase 0.4: Deployment Eligibility Gate

Run this gate before creating `.sealos/`, detecting deployment mode, matching a
template, readiness scoring, Dockerfile generation, image detection, or build.

Read and apply the canonical policy:
`<SKILL_DIR>/../cloud-native-readiness/knowledge/deployment-eligibility.md`.

When Node.js is available, run:

```bash
node "<SKILL_DIR>/scripts/workload-eligibility.mjs" "$WORK_DIR"
```

The script is read-only and prints the decision to stdout. Keep the parsed object as
`ELIGIBILITY_DECISION` in the current execution context; never write it to `.sealos/`
or another project file.

| Exit | Status | Action |
|------|--------|--------|
| `0` | `eligible` | Continue with the requested repository root |
| `2` | `ineligible` | Report workload type/evidence and STOP |
| `3` | `needs_review` | Inspect evidence; keep deployment blocked until explicitly resolved |
| other | execution error | Report the classifier error and STOP |

Parse stdout even for exits `2` and `3`; those are classification results, not script
failures. A mixed repository remains `needs_review` in this workflow: list the
detected units and STOP rather than selecting and deploying a nested directory.

For other `needs_review` results, inspect entry points and runtime evidence. Continue
only when the requested root itself can be explicitly resolved as `eligible`; record
that in-memory decision with `source: "ai-review"` and specific repository-relative
evidence. An ordinary desktop/mobile client cannot be overridden by a Dockerfile,
readiness score, registry image, or user willingness to proceed.

If Node.js is unavailable, perform the same review manually and keep the result in
memory. Missing or ambiguous evidence fails closed. No `.sealos/config.json` field or
resume state may skip or override this gate.

## Artifact Directory

All pipeline outputs are written under `.sealos/` in `WORK_DIR`:

```
<WORK_DIR>/.sealos/
├── config.json                   ← user configuration overrides (manual, committed to git)
├── template-match.json           ← Phase 0.5 template fast-path decision
├── deploy-handoff.json           ← typed phase handoff envelope (when emitted)
├── state.json                    ← deployment state (auto-maintained after Phase 6)
├── analysis.json                 ← project analysis snapshot (regenerated each deploy)
├── runtime-truth.json            ← sanitized live evidence (written before state)
├── build/                        ← created only if Phase 4 actually runs
│   └── build-result.json         ← Phase 4 result (`success` or `failed`)
└── template/
    └── index.yaml                ← Phase 5 Sealos template
```

**File responsibilities:**
- `config.json` — optional user overrides (port, base_image, build_command, etc.). Created manually by user, committed to git. All fields optional.
- `analysis.json` — project analysis snapshot written after Phase 1 (language, framework, score, etc.). Regenerated each deploy.
- `state.json` — deployment state written after Phase 6 success. Contains `last_deploy` and `history`. Enables UPDATE mode on subsequent runs.
- `runtime-truth.json` — sanitized Runtime Truth evidence written before verified state; it never contains credentials or raw Secret/ConfigMap values.
- `deploy-handoff.json` — optional typed envelope for a phase boundary; it records source, owner, preconditions, evidence, redaction, terminal state, and the next action.

**Note:** When reading dockerfile-skill modules (analyze.md, generate.md, build-fix.md), they reference `docker-build/` as their default output path. In this pipeline, always write to `.sealos/build/` instead. Similarly, template output goes to `.sealos/template/` instead of `template/`.

JSON artifacts under `.sealos/` are governed by explicit schemas in `<SKILL_DIR>/schemas/`:
- `config.schema.json`
- `template-match.schema.json`
- `analysis.schema.json`
- `build-result.schema.json`
- `state.schema.json`
- `deploy-handoff.schema.json`

Validate them with:

```bash
node "<SKILL_DIR>/scripts/validate-artifacts.mjs" --dir "$WORK_DIR"
```

Writers should validate on write; readers should validate before trusting resume/update state.

## Typed Dependency Boundaries

Every receiving phase validates the upstream handoff before reading the next input. The
validated summary contains `source`, `owner`, `preconditions`, `inputArtifact`,
`allowedAction`, `failureReturn`, `responseOwner`, `evidence`, and `redaction`.

| Boundary | Accepted evidence | Stopped return | Error return |
| --- | --- | --- | --- |
| Eligibility → assess | eligible decision with repository-relative evidence | unsupported or ambiguous workload, before `.sealos/` work | classifier execution failure |
| Readiness → Dockerfile | validated analysis plus readiness owner and evidence | missing or stale analysis, with the readiness owner | schema or redaction violation |
| Dockerfile/build → template | validated Dockerfile/build result and explicit image tag | build pending or image reuse not verified | build/template handoff failure |
| Template → deploy | quality-gated template and delivery evidence | missing config or unconfirmed mutation | API/template error with sanitized detail |
| Deploy → Runtime Truth/Canvas | live identity, runtime report, and sanitized artifact paths | runtime pending or unreadable handoff | failed smoke, logs, rollout, or footprint |

The receiving phase consumes each report once and passes its verified summary forward.
It keeps the existing fast path, image reuse, and lazy `.sealos/build/` creation. A
failed handoff returns to its named owner with one recovery action; it does not trigger
a second repository-wide source scan or silently substitute a guessed artifact.

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

Read `.sealos/state.json` in `WORK_DIR` and validate it with the artifact validator before
using any field. If it exists and contains a `last_deploy` key with `app_name`, proceed to
Step 2. A malformed state, incomplete provenance, unredacted handoff, or invalid Runtime
Truth block returns `stopped` with the exact artifact path and reconciliation action.

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
- Return `stopped`: `state_live_identity_unavailable` with the safe action to restore the
  selected Sealos kubeconfig or explicitly choose a new instance. Keep the state file for
  reconciliation and perform no mutation.

If `ENV.kubectl` is true, query the cluster:
```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get deployment/<app_name> -n <namespace> \
  -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null
```

- Command fails (deployment deleted or kubeconfig expired) → `stopped` with
  `state_live_identity_unavailable`; keep the state artifact and ask for reconciliation.
- Command returns current image → compare app name, namespace, image, URL host, and
  readiness with the validated `last_deploy` record before proceeding to Step 3.
- Any mismatch → `stopped` with `state_live_identity_mismatch`; show only field names and
  the safe reconciliation action. UPDATE never mutates a guessed target.

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

If any artifacts exist, validate each artifact before offering resume. Report to user:
`"Found artifacts from a previous deploy attempt. [list found artifacts]."`
Ask: `"Resume from where it left off? Or restart from Phase 1?"`

If restart → remove `.sealos/analysis.json`, `.sealos/build/`, `.sealos/template/index.yaml` and start fresh.

Keep `.sealos/build/` absent when the image-reuse handoff is `validated` and Phase 4 does
not run. A directory created only by a failed or skipped build is a stale artifact and
returns `stopped` until the user chooses a fresh build or the artifact is reconciled.

---

## Phase 0.5: Template Fast Path

Run this phase after preflight has resolved `WORK_DIR`, `GITHUB_URL`, and `REPO_NAME`, and before Phase 1 assessment.

The goal is to avoid source analysis, Dockerfile generation, image builds, and template generation for repositories that are already represented by a known Sealos template.

With Node.js:

```bash
node "<SKILL_DIR>/scripts/detect-template.mjs" \
  --github-url "$GITHUB_URL" \
  --work-dir "$WORK_DIR" \
  --skill-dir "<SKILL_DIR>"
```

The script writes `.sealos/template-match.json` every time it runs.

Decision:

- `matched=false` → continue to Phase 1 normally.
- `matched=true` and `materialized=false` → report the matched template name and continue to Phase 1 normally; this is only a recommendation because no deployable template YAML was available.
- `matched=true` and `materialized=true` → skip Phase 1 through Phase 5 because `.sealos/template/index.yaml` already exists. Continue with Phase 5.5 configuration and Phase 6 deployment.

The fast path is configured in `<SKILL_DIR>/config.json` under `template_fast_path.templates`. A template entry must include `name` and `source_repos`; it materializes only when it also provides valid Sealos Template YAML through one of:

- `template_yaml`
- `template_path`
- `template_url`

Template YAML must include:

```yaml
apiVersion: app.sealos.io/v1
kind: Template
```

If a matched entry cannot materialize YAML, do not treat it as a deployable result and do not skip build or template generation.

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

### 2.S Source-Ready Static Site Image Path

Before registry discovery, check the in-memory eligibility decision. When its reason
codes contain `SOURCE_READY_STATIC_SITE`, the requested project has a root
`index.html`, a public asset tree that can be served without transformation, and no
higher-priority build, server-runtime, container, or sensitive-file signal.

Set `STATIC_NGINX_IMAGE_BUILD=true` and update `.sealos/analysis.json` with
`language: "html"`, `framework: "static_html"`, `package_manager: null`, port
`8080`, and `image_ref: null`. Skip existing-image discovery for this source-only
tree and continue to Phase 3. Phase 3 must generate the pinned static Nginx
Dockerfile, and Phase 4 must build and push it through the same registry path as
every other locally built image.

This path is intentionally evidence-based and fail-closed. File count, extension,
and directory depth are not deployment decisions. Preserve arbitrary regular public
assets and their relative paths, including nested directories, while excluding
repository metadata through `.dockerignore`. Give an existing container contract
precedence over this path. Route build/runtime manifests and server-source signals
through ordinary analysis. Stop for possible secrets, symbolic links, or a missing
root `index.html`. Never silently omit a business asset from the image.

The remaining Phase 2 instructions apply when `STATIC_NGINX_IMAGE_BUILD` is false.

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
<SKILL_DIR>/../dockerfile-skill/templates/static-nginx.dockerfile
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

When `STATIC_NGINX_IMAGE_BUILD=true`, copy
`<SKILL_DIR>/../dockerfile-skill/templates/static-nginx.dockerfile` as the project
Dockerfile without adding a ConfigMap publication path or a frontend build stage.
The pinned unprivileged Nginx image serves the recursively copied source-ready asset
tree on port `8080`. Copy
`<SKILL_DIR>/../dockerfile-skill/templates/static-nginx.dockerignore` to
`$WORK_DIR/.dockerignore`; do not use the generic ignore list below, because arbitrary
public assets such as Markdown downloads must not be silently omitted.

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
- Multi-stage build when compilation is required; source-ready static sites use the single-stage pinned Nginx template
- Pin base image versions (never `:latest`)
- Run as a non-root user (for example USER 1001, or the static Nginx image's USER 101)
- Proper `.dockerignore`

For non-static-image paths, also generate `.dockerignore`:
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
Dockerfile
.dockerignore
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
- Treat every locally built and newly pushed GHCR image as private by default. Do not run a visibility or anonymous-pull probe; proceed immediately to the built-in image pull Secret path. For a fresh deploy, wait for the Template API to return the real instance name, then create the same-named Secret immediately. For an update, refresh the Secret before swapping the image because the real instance name is already known from state.
- Do not attempt to make the package public during deployment. Do not probe or call GitHub REST endpoints, GraphQL mutations, package settings, or other visibility-changing paths; package visibility is not a deployment prerequisite.
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

Tag format: `<lowercase-owner-or-user>/<lowercase-repo-name>:YYYYMMDD-HHMMSS` (e.g., `ghcr.io/zhujingyang/kite:20260304-143022`). Normalize the registry namespace and repository name to lowercase before constructing the image reference. The timestamp ensures same-day rebuilds never collide.

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

For GHCR success, `build-push.mjs` returns `requires_image_pull_secret: true`. Continue immediately with the GHCR image and let Phase 6 create/update the pull Secret automatically from `gh auth token`. Do not check or change package visibility.
If Phase 2 reused an existing public image, do **not** trigger the GHCR pull-secret flow.

**If Node.js not available (fallback — run docker directly):**
```bash
TAG=$(date +%Y%m%d-%H%M%S)
```

If the user chose GHCR:
```bash
GH_USER=$(gh api user -q .login)
gh auth token | docker login ghcr.io -u "$GH_USER" --password-stdin
IMAGE="ghcr.io/$(printf '%s' "$GH_USER" | tr '[:upper:]' '[:lower:]')/<lowercase-repo-name>:$TAG"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push -f Dockerfile "$WORK_DIR"
```

If the user chose Docker Hub:
```bash
DOCKER_HUB_USER=$(docker info 2>/dev/null | sed -n 's/^ Username: //p')
IMAGE="$(printf '%s' "$DOCKER_HUB_USER" | tr '[:upper:]' '[:lower:]')/<lowercase-repo-name>:$TAG"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push -f Dockerfile "$WORK_DIR"
```

If `$IMAGE` is a newly built GHCR image, mark that Phase 6 must create/update the namespace image pull Secret. A fresh deploy must use the real instance name returned by the Template API; an update may refresh the known same-named Secret before rollout. Do not run visibility or anonymous-pull probes and do not attempt any package-visibility mutation.
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
<SKILL_DIR>/../docker-to-sealos/references/example-guide.md    — representative template structure
<SKILL_DIR>/../docker-to-sealos/references/must-rules-map.yaml — executable rule coverage
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
Do not create another template-generation artifact.

Before conversion or validation, require Python with PyYAML. Do not install it from this workflow:

```bash
PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ] || ! "$PYTHON_BIN" -c 'import yaml' >/dev/null 2>&1; then
  echo "Phase 5 requires Python with PyYAML; install it outside this workflow and retry." >&2
  exit 1
fi
```

When a supported root Compose file exists, use the deterministic converter as the generation baseline. Use `--dry-run` so the only written template artifact remains `.sealos/template/index.yaml`. Missing required converter capabilities or converter failure is a hard stop, not permission to hand-write around the failure.

```bash
COMPOSE_FILE=""
for candidate in docker-compose.yml docker-compose.yaml compose.yml compose.yaml; do
  if [ -f "$WORK_DIR/$candidate" ]; then
    COMPOSE_FILE="$WORK_DIR/$candidate"
    break
  fi
done

if [ -n "$COMPOSE_FILE" ]; then
  APP_NAME="$(
    "$PYTHON_BIN" -c \
      'import json, sys; value = json.load(open(sys.argv[1], encoding="utf-8"))["project"]["repo_name"]; print(value.rsplit("/", 1)[-1])' \
      "$WORK_DIR/.sealos/analysis.json"
  )" || {
    echo "Unable to read the app name from analysis.json; Phase 5 stopped." >&2
    exit 1
  }
  GITHUB_URL="$(
    "$PYTHON_BIN" -c \
      'import json, sys; value = json.load(open(sys.argv[1], encoding="utf-8"))["project"]["github_url"]; print(value or "")' \
      "$WORK_DIR/.sealos/analysis.json"
  )" || {
    echo "Unable to read the GitHub URL from analysis.json; Phase 5 stopped." >&2
    exit 1
  }
  GENERATED_TEMPLATE="$(
    "$PYTHON_BIN" "<SKILL_DIR>/../docker-to-sealos/scripts/compose_to_template.py" \
      --compose "$COMPOSE_FILE" \
      --app-name "$APP_NAME" \
      --git-repo "$GITHUB_URL" \
      --kompose-mode always \
      --no-fetch-logo \
      --dry-run
  )" || {
    echo "Deterministic Compose conversion failed; Phase 5 stopped." >&2
    exit 1
  }
  printf '%s\n' "$GENERATED_TEMPLATE" > "$WORK_DIR/.sealos/template/index.yaml"
fi
```

For converted templates, apply the resolved `analysis.json.image_ref` only to the application workload that it represents, then add the documented application-specific runtime semantics. Treat the converter's database classification as immutable: application-specific edits must not replace a KubeBlocks database `Cluster` with a Deployment, StatefulSet, Service, or other generic workload.

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
- For a locally built GHCR image, add `template.spec.imagePullSecrets: [{ name: ${{ defaults.app_name }} }]`. The Template API resolves this to the real generated instance name; the same-named Secret is created immediately after the deploy response. Omit it for anonymously pullable existing images and Docker Hub public images.
- Every `spec.defaults.<name>.value` and every present `spec.inputs.<name>.default` must deserialize as a YAML string; quote numeric-, boolean-, and null-like values, while infrastructure fields such as replicas and ports remain numeric
- **App CRD** (last resource): only `spec.data.url`, `spec.displayType`, `spec.icon`, `spec.name`, `spec.type` — no other fields (no `menuData`, `nameColor`, `template`, etc.)
- **App CRD fixed enums**: `spec.displayType` must be `normal`; `spec.type` must be `link`

### 5.3 Validate

Run the complete sibling quality gate:
```bash
"$PYTHON_BIN" "<SKILL_DIR>/../docker-to-sealos/scripts/quality_gate.py" \
  --artifacts "$WORK_DIR/.sealos/template/index.yaml"
```

Any non-zero exit stops Phase 5. Fix the existing `index.yaml` and rerun the complete gate before interactive configuration. In particular, `R052` means a Template default was parsed as a YAML number, boolean, or null instead of the string required by the Template CRD.

Template is written to `.sealos/template/index.yaml`. No separate checkpoint file — the template file's existence is sufficient for resume detection.

### Managed-mode handoff after Phase 5.3

When `SEALAI_DEPLOY_MODE=managed`, the generated template must pass through the managed adapter before Brain sees it. This is the only managed mutation of the template artifact:

```bash
MANAGED_TEMPLATE_RESULT=$(node "<SKILL_DIR>/scripts/managed-adapter.mjs" \
  prepare-template "$WORK_DIR/.sealos/template/index.yaml")
TEMPLATE_SHA=$(printf '%s' "$MANAGED_TEMPLATE_RESULT" | jq -r '.sha256')
```

Run the complete quality gate against the exact file. The SHA sent to Brain must be computed from those final bytes; never hash a rendered copy. The adapter does not inject a Brain-owned Instance name, identity labels, or `extraLabels`.

After the gate passes, call the task-scoped MCP tool exactly once for this template revision:

```text
template_ready({ sha256: TEMPLATE_SHA })
```

The tool response is the control decision, not a suggestion:

- `decision: "continue"` — continue to deployment using the same final template.
- `decision: "awaiting_user"` — end the current Codex turn immediately, before any Template API request, `kubectl apply`, or other deployment mutation. Brain extracts `spec.inputs` from this template, renders the existing form, and resumes the same task after the user submits it.
- Any error, missing decision, stale task, or unavailable tool — stop managed mode as fatal. Do not write a substitute report or retry through another transport.

Do not create `inputs-required.json` or another control/checkpoint file. The Template's `spec.inputs` is the sole form declaration.

After apply, run the Skill's normal readiness and runtime-truth checks yourself. When those checks pass, report the actual resources created in the task namespace:

```text
deployment_completed({
  workloads: [
    { apiVersion, kind, name, namespace },
    // include the current Ready Pod or Pods when available
  ],
  // optional: the tenant-owned public URL when the deployment exposes one
  publicUrl: "https://<tenant-domain-app-url>"
})
```

Brain only performs a small Ready check on these references and, when `publicUrl` is provided, probes it for a 2xx response. A `repair` response means continue diagnosing and repairing in this Codex turn; Brain does not apply, inspect logs, or debug for you.

---

## Phase 5.5: Interactive Configuration

After generating the template, guide the user through application configuration before deployment.
This is a **critical** step — most applications need user-specific configuration to function properly.

Before categorizing inputs, load `<SKILL_DIR>/../docker-to-sealos/references/bootstrap-account-modes.md` and classify the exact selected release as functional first-user signup, mandatory bootstrap credentials, or optional root reconciliation. For mandatory bootstrap, record whether credentials are deployer-supplied or runtime-generated. Record the selected mode in the deployment analysis.

### Managed-mode configuration override

In managed mode Brain owns the form. The Codex turn never asks the user questions and never copies submitted values into the prompt or `.sealos/template/index.yaml`:

1. On the initial turn, follow the managed handoff above. If `template_ready` returns `awaiting_user`, stop the turn; do not poll or sleep waiting for the form.
2. After Brain resumes the same task, read the fixed file named by `SEALAI_INPUTS_PATH` (it must equal `/run/sealai/deployment/inputs.json`) as a JSON object. Do not search for another input file and do not invent defaults for missing required keys.
3. Pass that file to the Template API deploy helper without printing its contents:

   ```bash
   node "<SKILL_DIR>/scripts/deploy-template.mjs" \
     "$WORK_DIR/.sealos/template/index.yaml" \
     --args-file "$SEALAI_INPUTS_PATH"
   ```

   If the template has no inputs, continue with an empty argument object and do not require an input file.
4. Re-run the final quality gate against the unchanged template immediately before deployment. User values are request arguments, not a second template artifact.

The interactive/local configuration procedure below applies only when `SEALAI_DEPLOY_MODE` is not `managed`; leave it unchanged for local runs.

### 5.5.1 Extract Configuration from Template

Parse the generated template YAML and categorize all environment variables and inputs:

**Category A — Auto-managed (no user action needed):**
- `defaults.*` values: `app_name`, `app_host`, random passwords/keys (`${{ random(N) }}`)
- Database connections via `secretKeyRef`: host, port, username, password from Kubeblocks secrets
- Object storage credentials via `secretKeyRef`
- Composed URLs that reference auto-managed vars (e.g., `DATABASE_URL` built from `$(DB_HOST):$(DB_PORT)`)
- Internal service FQDNs (`*.${{ SEALOS_NAMESPACE }}.svc.cluster.local`)
- Functional first-user signup: the registration flow owns the initial account, so optional administrator/root inputs and bootstrap env/config are absent
- Runtime-generated mandatory bootstrap: the selected runtime deterministically constructs the exact documented credential format, retains the resolved credential in a Secret or documented live runtime source, and exposes no administrator input unless deployer selection is documented

**Category B — User-required inputs:**
- Template `inputs` with `required: true` and no sensible default
- Template `inputs` with `required: true` and `default: ''` for non-administrator fields; the empty default means the deployer must provide the value before deploy
- Deployer-supplied mandatory bootstrap identity/password inputs: every documented field is required, omits `default`, and carries the exact upstream constraints in its English description
- Env vars with empty or placeholder values that the app cannot function without
- Common examples: mandatory bootstrap username/email/password, external API keys (OpenAI, SMTP credentials, OAuth client ID/secret)

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
    1. ADMIN_USERNAME — Administrator login username (required)
    2. ADMIN_PASSWORD — Administrator login password (required)
    3. OPENAI_API_KEY — OpenAI API key for AI features (required)

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
4. For deployer-supplied mandatory bootstrap credentials, collect every documented identity/password field, validate each value against the exact selected-release rules, and preserve the value byte-for-byte through Template API args and live login.

**For optional inputs:**
1. Show the default values
2. Ask: "Do you want to change any of these? (press Enter to keep defaults)"
3. Only update values the user explicitly wants to change

**For unfamiliar env vars:**
If the AI is unsure what a variable does, read the project README, `.env.example`, or source code to explain it to the user before asking for a value.

### 5.5.4 Apply Configuration to Template

Keep user-required `inputs` definitions in the template and pass user-provided values through Template API args. The following example represents a deployer-supplied mandatory bootstrap flow; replace its description constraints with the exact selected-release rules:

```yaml
inputs:
  ADMIN_USERNAME:
    description: 'Administrator login username'
    type: string
    required: true
  ADMIN_PASSWORD:
    description: 'Administrator password. Use 12-128 characters including uppercase, lowercase, number, and symbol.'
    type: string
    required: true
```

Record all user choices as `CONFIG` for use in Phase 6:
```
CONFIG.args = { ADMIN_USERNAME: "admin", ADMIN_PASSWORD: "<secret>", OPENAI_API_KEY: "sk-..." }
```
These `args` will be passed to the Template API's `args` field (Phase 6.2), which overrides or supplies `spec.inputs` in the template.

For runtime-generated mandatory bootstrap, keep administrator inputs absent unless the selected release documents deployer selection. Construct and validate the exact documented credential format before the server starts, retain the resolved credential in a Kubernetes Secret or documented live runtime source, and reserve retrieval for the redacted live login smoke.

### 5.5.5 Deployment Confirmation

Immediately before presenting the deployment confirmation, run the complete quality gate again against the exact final template:

For deployer-supplied mandatory bootstrap credentials, complete the release-specific value validation first. A validation failure returns to Phase 5.5.3 while preserving the user's original value for correction and keeping credentials out of logs. For runtime-generated mandatory bootstrap, verify deterministic format construction, startup validation, and resolved-credential retention before deployment.

```bash
"$PYTHON_BIN" "<SKILL_DIR>/../docker-to-sealos/scripts/quality_gate.py" \
  --artifacts "$WORK_DIR/.sealos/template/index.yaml"
```

This final run is required even if Phase 5.3 already passed. Any non-zero exit stops the workflow before Phase 6; fix the existing template and rerun the gate. Do not deploy while the gate is failing.

After the final gate passes, present a summary and ask for confirmation:

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

### Managed-mode execution

In managed mode the Codex performs the deploy itself with the injected user kubeconfig and `SEALAI_NAMESPACE`. Do not call Sealos OAuth or ask Brain to apply the YAML. Use the managed-aware `deploy-template.mjs` path (or an equivalent direct `kubectl`/Template API operation) only after the `template_ready` decision permits continuation, and keep all apply, patch, log, and exec operations inside this Codex turn. Local mode continues to use the auth and kubeconfig instructions below.

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

`deploy-template.mjs` sends the original args to Template API and emits only `args_supplied` plus an allowlisted response. Credential values, raw response messages, nested response details, and request exception text stay out of stdout/stderr.

**With Node.js (preferred):**
```bash
node "<SKILL_DIR>/scripts/deploy-template.mjs" ".sealos/template/index.yaml" --dry-run

DEPLOY_ARGS_FILE=$(mktemp "${TMPDIR:-/tmp}/sealos-template-args.XXXXXX")
chmod 600 "$DEPLOY_ARGS_FILE"
trap 'rm -f "$DEPLOY_ARGS_FILE"' EXIT

# Serialize Phase 5.5 CONFIG.args directly to this file without printing values.
node "<SKILL_DIR>/scripts/deploy-template.mjs" \
  ".sealos/template/index.yaml" --args-file "$DEPLOY_ARGS_FILE"

rm -f "$DEPLOY_ARGS_FILE"
trap - EXIT
```

This script is the preferred execution path because it:
- reads `~/.sealos/auth.json` directly instead of fragile shell parsing
- derives `REGION_DOMAIN` from the real `region` value
- always posts to the concrete `DEPLOY_URL`
- emits structured JSON on success or failure

Use `--args-json` only for values confirmed to be non-sensitive. Passwords, tokens, API keys, email addresses, and other account values use the private `--args-file` path. On POSIX systems, the helper rejects argument files that grant access to group or other users.

**Without Node.js (curl + jq fallback):**
```bash
umask 077
DEPLOY_ARGS_FILE=$(mktemp "${TMPDIR:-/tmp}/sealos-template-args.XXXXXX")
DEPLOY_BODY_FILE=$(mktemp "${TMPDIR:-/tmp}/sealos-template-body.XXXXXX")
DEPLOY_RESPONSE_FILE=$(mktemp "${TMPDIR:-/tmp}/sealos-template-response.XXXXXX")
trap 'rm -f "$DEPLOY_ARGS_FILE" "$DEPLOY_BODY_FILE" "$DEPLOY_RESPONSE_FILE"' EXIT

# Serialize Phase 5.5 CONFIG.args directly to DEPLOY_ARGS_FILE without printing values.
# encodeURIComponent via Python.
KUBECONFIG_ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.stdin.read(), safe=''))" < ~/.sealos/kubeconfig)

jq -n \
  --rawfile yaml .sealos/template/index.yaml \
  --slurpfile args "$DEPLOY_ARGS_FILE" \
  '{yaml: $yaml, args: $args[0], dryRun: false}' > "$DEPLOY_BODY_FILE"

if ! HTTP_STATUS=$(curl -sS -o "$DEPLOY_RESPONSE_FILE" -w '%{http_code}' -X POST "$DEPLOY_URL" \
  -H "Authorization: $KUBECONFIG_ENCODED" \
  -H "Content-Type: application/json" \
  --data-binary @"$DEPLOY_BODY_FILE"); then
  jq -n '{success: false, response: {details_omitted: true}}'
  exit 1
fi

if jq -e . "$DEPLOY_RESPONSE_FILE" >/dev/null 2>&1; then
  jq --arg status "$HTTP_STATUS" '
    ($status | tonumber) as $statusCode |
    . as $body |
    {
      success: ($statusCode >= 200 and $statusCode < 300),
      status: $statusCode,
      response:
        (({
          ok: $body.ok,
          success: $body.success,
          name: $body.name,
          uid: $body.uid,
          resourceType: $body.resourceType,
          createdAt: $body.createdAt
        } | with_entries(select(.value != null)))
        + (if ($body.resources | type) == "array" then {
            resources: [$body.resources[] as $resource | ({
              name: $resource.name,
              uid: $resource.uid,
              resourceType: $resource.resourceType,
              kind: $resource.kind,
              quota: (($resource.quota // {}) | ({
                cpu,
                memory,
                storage,
                replicas
              } | with_entries(select(.value != null))))
            } | with_entries(select(.value != null)))]
          } else {} end)
        + (if ($body.error | type) == "object" then {
            error: ({
              type: $body.error.type,
              code: $body.error.code,
              details_omitted: true
            } | with_entries(select(.value != null)))
          } else {} end))
    }
  ' "$DEPLOY_RESPONSE_FILE"
else
  jq -n --arg status "$HTTP_STATUS" \
    '{success: false, status: ($status | tonumber), response: {details_omitted: true}}'
fi

rm -f "$DEPLOY_ARGS_FILE" "$DEPLOY_BODY_FILE" "$DEPLOY_RESPONSE_FILE"
trap - EXIT
```

This fallback requires `jq` so request construction and response allowlisting stay structured. Use the Node.js helper when `jq` is unavailable.

### 6.3 Handle Response

Template API error bodies may contain a message and nested details. `deploy-template.mjs` exposes only the safe diagnostic fields:
```json
{
  "success": false,
  "status": 400,
  "args_supplied": 2,
  "response": {
    "error": { "type": "ValidationError", "code": "INVALID_VALUE", "details_omitted": true }
  }
}
```

| Status | Meaning | Action |
|--------|---------|--------|
| 201 | Deployed successfully | Extract instance name and resources from response |
| 200 | Dry-run preview (`dryRun: true`) | Show resource preview and quota |
| 400 | Validation error — `INVALID_PARAMETER` (missing yaml/name) or `INVALID_VALUE` (bad YAML, missing required args) | Use `error.type/code`, rerun the local quality gate, compare required inputs with `args_supplied`, inspect the selected release's schema, then repair and retry |
| 401 | `AUTHENTICATION_REQUIRED` — missing or invalid kubeconfig | Re-run auth: `node sealos-auth.mjs login`, or switch workspace: `node sealos-auth.mjs switch <ns>` |
| 403 | `FORBIDDEN` — insufficient permissions | Inform user, check kubeconfig namespace permissions |
| 409 | `ALREADY_EXISTS` — instance already exists | Inform user, suggest different app name |
| 422 | `RESOURCE_ERROR` — K8s rejected resource spec | Use `error.type/code`, rerun the local quality gate, inspect rendered resource fields and server-side dry-run through the redacted helper, then repair the template |
| 503 | `SERVICE_UNAVAILABLE` — K8s cluster unreachable | **Fall back to kubectl (6.4)** |

On 201 success, the helper's allowlisted response contains:
```json
{
  "name": "myapp-abcdefgh",
  "uid": "...",
  "resourceType": "instance",
  "displayName": "...",
  "createdAt": "...",
  "resources": [
    { "name": "myapp-abcdefgh", "uid": "...", "resourceType": "deployment", "quota": { "cpu": 0.1, "memory": 0.25, "storage": 0, "replicas": 1 } }
  ]
}
```
Extract the instance name and present to user.

### 6.3.1 Create the Pull Secret Using the Real Instance Name

For a locally built GHCR image, do **not** create the pull Secret before the Template
API call. The requested repository/app name is not authoritative, and the API may
generate a different Instance, App, and Deployment identity.

Immediately after the `201` response:

1. Read `REAL_APP_NAME` from the top-level response `name`. This is the authoritative
   Secret name and the value resolved from `${{ defaults.app_name }}`.
2. Read `NAMESPACE` from the active kubeconfig context.
3. Create the Secret named exactly `$REAL_APP_NAME` before starting readiness waits:

```bash
REAL_APP_NAME="<response.name>"
NAMESPACE=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  config view --minify -o jsonpath='{.contexts[0].context.namespace}')

node "<SKILL_DIR>/scripts/ensure-image-pull-secret.mjs" \
  "$NAMESPACE" "$REAL_APP_NAME" "$IMAGE_REF"
```

The Template may create a Pod before the Secret exists, so a short initial
`ErrImagePull` or `ImagePullBackOff` is expected. Do not delete or recreate the Pod,
do not change package visibility, and do not replace the image. Kubelet retries image
pulls automatically and should recover after the same-named Secret appears.

Secret creation is a blocking post-deploy step: verify the Secret exists and that
the live Deployment references `$REAL_APP_NAME` in `spec.template.spec.imagePullSecrets`
before accepting readiness. If `response.name` is missing, empty, or does not match
the rendered Secret reference, stop instead of guessing from the repository name.

Skip this subsection when Phase 2 reused an existing public image or the selected
registry was the Docker Hub public-image flow.

### 6.3.2 Post-Deploy Readiness Verification

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
   - Password policy, invalid bootstrap configuration, or root reconciliation validation: return to the account-mode classification and Phase 5.5 credential contract before changing resources.
   - App-specific migration/bootstrap errors: repair the failed bootstrap state, then rerun the init path.
4. Only report the app as usable after the endpoint exists and an HTTP request to the public URL returns a non-5xx response.
5. Continue to Phase 6.5 before writing deployment state or reporting success.

For templates with KubeBlocks-supported databases, runtime truth must include the database control plane and generated connection surface:

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get cluster,component,instanceset,secret,svc -n "$NAMESPACE" \
  | grep -E '<app-name>|redis|postgres|mysql|mongo|broker'
```

Acceptance requires the KubeBlocks `Cluster` to be Ready/Running, each expected `Component` and `InstanceSet` to converge, the account Secret to exist, and the application environment to point at the expected Service FQDN. For Redis, verify both `redis` and `redis-sentinel` components, `${APP_NAME}-redis-redis-account-default`, and `${APP_NAME}-redis-redis-redis.${NAMESPACE}.svc.cluster.local`. For MongoDB, verify `${APP_NAME}-mongo-mongodb-account-root` or the matching `mongodb` suffix variant before judging app initialization.

### 6.3.3 Runtime Truth Pass for Authenticated Apps

For web apps with login or registration, verify the authenticated runtime state after the readiness checks pass:

1. Complete login or registration through the real browser form or the documented login API.
2. Capture the final browser URL, document title, and key visible text from the authenticated page.
3. Record browser network requests with HTTP 4xx/5xx status, including method, URL path, status, and response summary.
4. Check backend logs for the same failing route paths and status codes.
5. Mark the runtime pass successful only when the authenticated page loads, expected post-login content is visible, and app API requests complete without new 4xx/5xx failures.

For login success followed by 404, route mismatch, or SDK endpoint errors:

1. Record the exact failing URL and API path from browser network logs.
2. Compare the failing path with backend logs to confirm the service that answered it.
3. Compare the template against the official runtime bundle source: component image versions, console/frontend service, API service, gateway/Ingress path, and public URL env/config.
4. Repair the template by aligning the bundle versions, restoring the missing route/service, or correcting reverse-proxy path handling.
5. Redeploy and rerun the browser login pass.

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

For a locally built GHCR image, `${{ defaults.app_name }}` from the rendered
resources is the authoritative `REAL_APP_NAME` in this fallback path. Immediately
after `kubectl apply`, create the same-named pull Secret before starting readiness
waits:

```bash
REAL_APP_NAME="<rendered defaults.app_name>"
node "<SKILL_DIR>/scripts/ensure-image-pull-secret.mjs" \
  "$NAMESPACE" "$REAL_APP_NAME" "$IMAGE_REF"
```

The rendered Deployment must already reference `$REAL_APP_NAME` in
`spec.template.spec.imagePullSecrets`. Do not delete or recreate a Pod that entered
`ErrImagePull` or `ImagePullBackOff`; kubelet will retry after the Secret appears.
Skip this step for an existing public image or the Docker Hub public-image flow.

**Step 4 — Handle apply errors:**

| Error | Fix |
|-------|-----|
| `unknown field "spec.xxx"` in App CR | Remove the unknown field and retry |
| PodSecurity warnings | Deployment may proceed; fix compatible securityContext warnings before runtime acceptance when the image runs as non-root |
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

### 6.5 Runtime Truth Pass

Execute `<SKILL_DIR>/modules/runtime-truth.md` after every Template API or kubectl fallback deploy. Complete its Launchpad network, App URL, login, log, Event convergence, object-storage, and footprint gates before writing deployment state or reporting success.

Write the allowlisted result to `.sealos/runtime-truth.json`, validate its redaction and
identity fields, and keep the report `verified` only after the full stability window. A
deploy response without this report is `stopped` with `runtime_pending`.

### Write state.json

**This is critical for enabling future updates.** After a successful deploy, write `.sealos/state.json`:

```json
{
  "version": "1.0",
  "last_deploy": {
    "app_name": "<instance name, e.g. evershop-uvbp0n0n>",
    "app_host": "<ingress host prefix, e.g. evershop-4ha6b4mh>",
    "namespace": "<K8s namespace from kubeconfig>",
    "region": "<Sealos control-plane region domain, e.g. usw-1.sealos.io>",
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
  ],
  "runtime_truth": {
    "status": "verified",
    "captured_at": "<final Runtime Truth timestamp>",
    "identity": {
      "app_name": "<same live app name>",
      "namespace": "<same live namespace>",
      "image": "<same verified image>",
      "url": "<same verified public URL>"
    },
    "evidence_paths": [".sealos/runtime-truth.json"],
    "redaction_status": "complete",
    "stability_window_seconds": 60,
    "checks": ["network", "app-url", "auth", "logs", "events", "footprint"]
  },
  "provenance": {
    "source": "sealos-deploy/runtime-truth",
    "owner": "sealos-deploy",
    "artifact_paths": [".sealos/analysis.json", ".sealos/template/index.yaml", ".sealos/runtime-truth.json"],
    "redaction_status": "complete"
  }
}
```

Validate this complete state artifact before returning `success`. The `last_deploy` section
is the resume hint; live App/Deployment identity remains the UPDATE authority. Canvas
receives only the sanitized state and Runtime Truth paths after this validation passes.

The `history` array is append-only — every subsequent update (via Update Path) adds an entry. See the **Update History** section at the end of this file for the full schema and rules.

Sources for each field:
- `app_name`: from Template API response `name` or the rendered `defaults.app_name` (kubectl apply)
- `app_host`: from the rendered `defaults.app_host` value, or parsed from the Ingress host
- `namespace`: from kubeconfig context
- `region`: control-plane/API region from `~/.sealos/auth.json` `region` field (strip `https://`); this may differ from the App runtime domain
- `image`: from `analysis.json` `image_ref`
- `docker_hub_user`: from Phase 4 `DOCKER_HUB_USER` (null if Phase 2 found existing image)
- `repo_name`: from `analysis.json` `project.repo_name`
- `url`: the exact `APP_URL` verified by the Runtime Truth Pass, read from the live App resource or deployment response; never reconstruct it from `app_host` and `region`

---

## Cleanup

If `WORK_DIR` was created via `mktemp` (remote GitHub URL clone), remove it:
```bash
rm -rf "$WORK_DIR"
```

Do NOT clean up if `WORK_DIR` is the user's local project directory.

### Safety Contract: Full-Footprint Cleanup

For test deployments, obtain explicit confirmation immediately before deletion and collect
the complete footprint with `sealos-footprint.mjs`. Cleanup is complete only when the
report has `collectionOk: true`, `cleanupComplete: true`, and an empty filtered list for
every selected resource kind:

- `instances.app.sealos.io` and `apps.app.sealos.io`
- Deployments, StatefulSets, DaemonSets, CronJobs, Jobs, and Pods
- Services and Ingresses
- PVCs
- KubeBlocks `Cluster`, `Component`, and related InstanceSets
- managed `ObjectStorageBucket` resources and their app-scoped Secrets

A kubectl listing error, permission error, timeout, or unavailable kubeconfig leaves
cleanup unresolved even when the visible list is empty. Keep the last footprint report,
the named owner references, and the safe recovery action. Delete the Sealos `Instance`
and application resources before database RBAC. Keep KubeBlocks ServiceAccount, Role, and
RoleBinding resources until the database `Cluster` finalizer has converged. A stuck
`Cluster` or `Component` requires recorded finalizers and owner references before any
last-resort recovery.

### Safety Contract: Rollback and Branch Boundary

Ask for explicit rollback confirmation before `rollout undo`, image reversal, or any
resource mutation triggered by a failed update. Retain the previous image, previous
validated state, failed rollout evidence, post-rollback live identity, and a fresh
Runtime Truth report. A rollback with incomplete evidence returns `error` and keeps
`last_deploy.image` at the previous value.

The main-like branch owns OAuth deployment, UPDATE, Runtime Truth, rollback, cleanup, and
Canvas handoff. `brain-deploy-preview` stays prepare-only with assessment, optional
Railpack evidence, Dockerfile preparation, `build-request.json`, sandbox Kaniko or image
reuse, template generation, and `delivery-manifest.json`. Preview work does not invoke
OAuth deploy, UPDATE, Runtime Truth, or Canvas.

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

Before Phase U1, validate `.sealos/state.json` and reconcile it with a live App/Deployment
identity. UPDATE requires matching app name, namespace, current image, URL host, and ready
workload evidence. A missing kubectl context, malformed state, or mismatch returns
`stopped` with `state_live_identity_mismatch` and leaves the selected resources unchanged.

All kubectl commands use the Sealos kubeconfig:
```
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify
```

**Reminder:** `kubectl delete` requires user confirmation — see SKILL.md "kubectl Safety Rules".

## Context from Mode Detection

These values are read once from the validated `.sealos/state.json` `last_deploy` section:

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

After Runtime Truth succeeds, update `.sealos/state.json`:
- Set `last_deploy.image` to `NEW_IMAGE`
- Set `last_deploy.last_updated_at` to current ISO timestamp
- Set `runtime_truth.identity` to the live app, namespace, image, and URL that passed the
  final report
- Set `runtime_truth.status` to `verified`, retain the evidence paths, and record the
  measured stability window
- Set `provenance` with the producing owner and repository-relative artifact paths
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

Keep `last_deploy.image` at the previous value when rollback or final Runtime Truth fails.
Record the rollback and failed evidence with redacted fields, and return `error` until the
previous live identity and Runtime Truth report are verified.

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
