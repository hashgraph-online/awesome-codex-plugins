---
name: sealos-deploy
description: Deploy compatible server, static-web, worker, scheduled-job, or reviewed remote-desktop workloads from GitHub or local source to Sealos Cloud, then run the default Runtime Truth Pass against the returned App URL, public route, authentication flow, logs, database state, and full resource footprint. Reject unsupported desktop, mobile, CLI, library, extension, hardware-dependent, mixed, and unidentified targets before readiness scoring or build. Use when the user asks to deploy a repository to Sealos or another cloud platform, or invokes "/sealos-deploy".
metadata:
  author: labring
  compatibility: Sealos auth/workspace are required for deploys. Docker, buildx, and gh CLI are required only when the selected path needs local build/push. git is required when cloning from a GitHub URL or when git metadata is needed. Node.js 18+ remains an optional accelerator. Phase 5 requires Python 3.8+ with PyYAML; root Compose conversion also requires kompose and may require crane when image tags are floating.
---

# Sealos Deploy

## Identity and Discovery

- **Owner:** `sealos-deploy` (`/sealos-deploy` and deploy, update, publish, or cloud-runtime requests).
- **Class:** `composite-orchestration` across readiness, Dockerfile, template, build, deployment, and Runtime Truth.
- **Canaries:** `DEP-KUBECONFIG-SCOPE`, `DEP-CONFIRM-MUTATION`, `DEP-REDACT`, and `DEP-RUNTIME-TRUTH`.
- **Contract:** Read [`references/deploy-contract.md`](references/deploy-contract.md) after the canaries pass. It defines the typed phase handoffs, owned `.sealos` artifacts, terminal states, and the read-only Canvas boundary.

## Scope and Boundaries

Accept a local path or GitHub URL and scope all work to the selected namespace/app. Preserve the current DEPLOY/UPDATE phase order, `.sealos` artifact inventory, one log file, dependency handoffs, and cleanup footprint. All Kubernetes commands use `KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify`; unsupported workloads stop before scoring/build.

## Risk and Confirmation

Keep auth/workspace, kubeconfig scope, system-tool installation, public exposure, credential changes, deletion, rollback, and cleanup confirmation visible before module detail. Redact passwords, tokens, cookies, env values, kubeconfig, Secret data, and full connection strings. A quality gate and actual Runtime Truth evidence are acceptance conditions.

For every gated mutation, report the exact operation, impact, confirmation, and post-action evidence. Keep sanitized logs, state, diagnostics, and footprint evidence free of secret data.

## Lifecycle Workflow

For each request, run preflight/auth/workspace, detect mode, enforce eligibility, assess/detect/build or reuse, generate/validate the template, deploy or update, run Runtime Truth, and record state/cleanup evidence. Emit request-scoped `success`, `stopped`, or `error`; the existing phase modules below remain authoritative for detailed behavior.

## Progressive Disclosure

Load `modules/` and helper scripts one phase at a time after the corresponding canaries pass. Preserve typed readiness → Dockerfile → Docker-to-Sealos handoffs, `.sealos/analysis.json`, `.sealos/build/build-result.json`, `.sealos/template/index.yaml`, `.sealos/state.json`, and delivery evidence; do not hide phase order behind a generic deploy shortcut.

## Output, Stop, and Error States

- `success`: actual returned App URL/live identity, route and port match, setup/login proof, recent logs/events, workload convergence, database/object evidence, full footprint, and saved deploy state.
- `stopped`: unsupported eligibility, missing auth/tool, unresolved configuration, or unconfirmed public/destructive/cleanup boundary with the safe next action.
- `error`: failed preflight, build/template/deploy/runtime/rollback/cleanup step and recovery action with sensitive values redacted.

## Handoffs

Readiness, Dockerfile, and Docker-to-Sealos inputs use typed `target`, `inputArtifact`, `allowedAction`, `failureReturn`, and `responseOwner` fields. A verified deploy can hand `target: sealos-canvas`, `inputArtifact: sanitized .sealos/state.json and Runtime Truth`, `allowedAction: read-only topology inspection`, `failureReturn: runtime/state diagnostic`, and `responseOwner: sealos-deploy`.

## Verification

Use the existing eligibility, artifact, quality-gate, footprint, live-smoke, rollout, Runtime Truth, and cleanup checks. Baseline cases `deploy-positive-runtime-truth` and `deploy-violating-missing-runtime-proof` must preserve actual App URL/live identity, auth/cleanup confirmation, log scans, and redaction.

## Compatibility

Sealos auth/workspace are required for deploys. Docker, buildx, and gh CLI are required only when the selected path needs local build/push. git is required when cloning from a GitHub URL or when git metadata is needed. Node.js 18+ remains an optional accelerator. Phase 5 requires Python 3.8+ with PyYAML; root Compose conversion also requires kompose and may require crane when image tags are floating.

## Brain Managed Mode

The skill has two deliberately separate execution modes:

- **Local mode** is the existing interactive workflow. It is selected when `SEALAI_DEPLOY_MODE` is absent or has any value other than `managed`; its auth, prompts, Template API flow, and output remain unchanged.
- **Managed mode** is selected only when `SEALAI_DEPLOY_MODE=managed`. The Devbox Codex is the deployment executor: it analyzes, builds, applies, observes, diagnoses, repairs, and verifies with the injected kubeconfig. Brain is the task control plane and form owner; it is not a second Kubernetes executor.

Managed mode is non-interactive. Do not start OAuth, install tools, ask for confirmation in the turn, or replace a missing callback with a file, webhook, curl request, or a Brain-side apply. Before doing any work, confirm that the Codex tool registry contains both exact MCP tools `template_ready` and `deployment_completed`. If either tool is unavailable, stop with a managed-mode fatal error; never claim a deployment result.

Brain supplies these task-scoped values through the environment:

```text
SEALAI_DEPLOY_MODE=managed
SEALAI_DEPLOY_TASK_ID=<task id>
SEALAI_PROJECT_ID=<Brain project id>
SEALAI_NAMESPACE=<target namespace>
SEALAI_INPUTS_PATH=/run/sealai/deployment/inputs.json
SEALAI_TURN_DEADLINE_AT=<absolute deadline>
```

Use the injected kubeconfig/context for every Kubernetes command. Do not perform login or switch workspace. Keep the input file and kubeconfig out of prompts, logs, Timeline text, and generated artifacts; read the input file only when the managed flow says to do so.

The actual Sealos Instance name is owned by the Template/Skill path. Brain does not pre-allocate it and the managed adapter does not add Brain identity labels or `extraLabels`.

Deploy compatible cloud workloads to Sealos Cloud, stopping unsupported targets
before build or deployment.

## kubectl Safety Rules (all phases)

All kubectl commands MUST use the Sealos kubeconfig:
```
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify
```

System tool installation requires user confirmation. If `docker`, `gh`, or `kubectl` is missing and the skill can install it for the current platform, ask first and only run the install command after the user explicitly replies `y`.

**`kubectl delete` requires user confirmation.** Before deleting any resource (deployment, service, ingress, PVC, database, etc.), always ask:
```
WARNING: About to delete <resource kind>/<resource name>. This data cannot be recovered. Confirm? (y/n)
```
Only proceed after user confirms. This applies even if the pipeline logic suggests deletion — always ask first.

**Template API cleanup must include Instance CRs.** Deployments created through `scripts/deploy-template.mjs` create `instances.app.sealos.io/<app-name>` in addition to App/workload resources. A cleanup is incomplete until `instances.app.sealos.io`, `apps.app.sealos.io`, workloads, Services, Ingresses, PVCs, and Pods are all checked.

Use this check when cleaning Template API test deployments:
```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" \
  get instances.app.sealos.io,app,statefulset,deployment,svc,ingress,pvc,pod | grep "$APP"
```

Delete in this order after confirmation:
```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete instances.app.sealos.io "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete app "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete statefulset "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete deployment "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete ingress "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete svc "$APP" --ignore-not-found --wait=false
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" get pvc -o name | grep "$APP" | while read -r PVC; do
  KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify -n "$NS" delete "$PVC" --ignore-not-found --wait=false
done
```

Anti-example: do not report cleanup complete after only checking `app,statefulset,svc,ingress,pvc,pod`; that misses `instances.app.sealos.io/<app-name>` and leaves the Sealos Instance layer dirty.

## Usage

```
/sealos-deploy <github-url>
/sealos-deploy                    # deploy current project
/sealos-deploy <local-path>
```

## Quick Start

Execute the modules in order:

1. `modules/preflight.md` — Environment checks & Sealos auth
2. `modules/pipeline.md` — Full deployment pipeline (Phase 1–6)
3. `modules/runtime-truth.md` — Post-deploy Runtime Truth Pass (Phase 6.5)

## Logging

Every run MUST write a log file at `~/.sealos/logs/deploy-<YYYYMMDD-HHmmss>.log`.

**At the very start of execution**, create the log file **once**:
```bash
mkdir -p ~/.sealos/logs
LOG_FILE=~/.sealos/logs/deploy-$(date +%Y%m%d-%H%M%S).log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deploy started" > "$LOG_FILE"
```

**Important: create the log file ONLY ONCE at the start. All subsequent writes MUST append (`>>`) to this same `$LOG_FILE`. Do NOT create a second log file.**

**At each phase boundary**, append a log entry to the same file with Bash `>>`:
```
[2026-03-05 14:30:01] === Phase 0: Preflight ===
[2026-03-05 14:30:01] Docker: ✓ 27.5.1
[2026-03-05 14:30:01] Node.js: ✓ 22.12.0
[2026-03-05 14:30:02] Sealos auth: ✓ (region: <REGION from config.json>)
[2026-03-05 14:30:02] Project: /Users/dev/myapp (github: https://github.com/owner/repo)

[2026-03-05 14:30:03] === Phase 1: Assess ===
[2026-03-05 14:30:03] Score: 9/12 (good)
[2026-03-05 14:30:03] Language: python, Framework: fastapi, Port: 8000
[2026-03-05 14:30:03] Decision: CONTINUE

[2026-03-05 14:30:04] === Phase 2: Detect Image ===
[2026-03-05 14:30:05] Docker Hub: owner/repo:latest (arm64 only, no amd64)
[2026-03-05 14:30:05] GHCR: not found
[2026-03-05 14:30:05] Decision: no amd64 image → continue to Phase 3

[2026-03-05 14:30:06] === Phase 3: Dockerfile ===
[2026-03-05 14:30:06] Existing Dockerfile: none
[2026-03-05 14:30:07] Generated: python-fastapi template, port 8000

[2026-03-05 14:30:08] === Phase 4: Build & Push ===
[2026-03-05 14:30:08] Registry: ghcr (auto-detected via gh CLI)
[2026-03-05 14:30:30] Build: ✓ ghcr.io/zhujingyang/repo:20260305-143022
[2026-03-05 14:30:32] GHCR pullability: private package detected — deploy will auto-create image pull Secret from gh CLI
[2026-03-05 14:30:33] IMAGE_REF=ghcr.io/zhujingyang/repo:20260305-143022

[2026-03-05 14:30:34] === Phase 5: Template ===
[2026-03-05 14:30:35] Output: .sealos/template/index.yaml

[2026-03-05 14:30:36] === Phase 6: Deploy ===
[2026-03-05 14:30:36] Deploy URL: https://template.gzg.sealos.run/api/v2alpha/templates/raw
[2026-03-05 14:30:38] Status: 201 — deployed successfully
[2026-03-05 14:30:38] === DONE ===
```

**On error**, log the error details before stopping:
```
[2026-03-05 14:30:10] === ERROR ===
[2026-03-05 14:30:10] Phase: 4 (Build & Push)
[2026-03-05 14:30:10] Error: docker buildx build failed — "npm ERR! Missing script: build"
[2026-03-05 14:30:10] Retry: 1/3
```

**At the very end**, tell the user where the log is:
```
Log saved to: ~/.sealos/logs/deploy-20260305-143001.log
```

## Scripts

Located in `scripts/` within this skill directory (`<SKILL_DIR>/scripts/`):

| Script | Usage | Purpose |
|--------|-------|---------|
| `workload-eligibility.mjs` | `node workload-eligibility.mjs <repo-dir>` | Read-only fail-closed workload classification; decision is stdout-only |
| `score-model.mjs` | `node score-model.mjs <repo-dir>` | Deterministic readiness scoring (0-12) |
| `detect-template.mjs` | `node detect-template.mjs [--github-url <url>] --work-dir <repo-dir> --skill-dir <SKILL_DIR>` | Detect configured GitHub repo → Sealos template fast-path matches |
| `validate-artifacts.mjs` | `node validate-artifacts.mjs --dir <work-dir>` | Validate `.sealos` JSON artifacts against enforced schemas |
| `detect-image.mjs` | `node detect-image.mjs <github-url> [work-dir]` or `node detect-image.mjs <work-dir>` | Detect existing Docker/GHCR images |
| `build-push.mjs` | `node build-push.mjs <work-dir> <repo> [--registry ghcr\|dockerhub] [--user <user>]` | Build amd64 image & push to the selected registry (Docker Hub path assumes a public image at deploy time; omitting `--registry` keeps auto-detect behavior) |
| `ensure-image-pull-secret.mjs` | `node ensure-image-pull-secret.mjs <namespace> <secret-name> <image-ref> [deployment-name]` | Create/update app-scoped GHCR pull Secret and optionally patch an existing Deployment to reference it |
| `gh-refresh-scopes.mjs` | `node gh-refresh-scopes.mjs write:packages` | Refresh GHCR package access in the current TTY; `write:packages` is sufficient for both push and private pull in this workflow |
| `deploy-template.mjs` | `node deploy-template.mjs <template-path> [--dry-run] [--args-json '{"KEY":"value"}'\|--args-file <file>]` | Resolve the current region, enforce private sensitive-args files on POSIX, post a local template YAML, and emit an allowlisted result with credential values redacted |
| `managed-adapter.mjs` | `node managed-adapter.mjs context\|prepare-template <path>\|sha256 <path>\|read-inputs` | Validate the Brain managed contract and compute the exact template SHA without injecting Instance identity or labels |
| `sealos-launchpad-network.mjs` | `node sealos-launchpad-network.mjs --app <app> --app-url <url> [--expected-port <port>] [--region <url>] [--kubeconfig <path>]` | Read-only Launchpad public-network discovery check with App URL and Service port matching |
| `sealos-footprint.mjs` | `node sealos-footprint.mjs --namespace <ns> --app <app>` | Read-only inventory of Instance/App/workloads/Jobs/KubeBlocks/PVCs/ObjectStorageBuckets for deploy debug and cleanup planning |
| `sealos-live-smoke.mjs` | `node sealos-live-smoke.mjs --url <url> [--captcha-path <path>] [--login-method json-token\|cookie-json] [--login-path <path>] [--username <user>] [--password <pass>] [--token-path <path>] [--auth-path <path>] [--missing-api-path <path>] [--missing-page-path <path>]` | Read-only or credentialed HTTP smoke test for the real Sealos App entry URL, authenticated routes, and API/SPA negative probes |
| `sealos-log-scan.mjs` | `node sealos-log-scan.mjs --namespace <ns> --app <app> [--since 10m] [--tail 300] [--baseline <report.json\|json>] [--min-window-seconds 60]` | Read-only JSON scan of Pod/init/main logs plus Warning Event convergence after readiness, login, and documented API or missing-static-asset checks |
| `sealos-auth.mjs` | `node sealos-auth.mjs check\|login\|list\|switch` | Sealos Cloud authentication & workspace switching |

All scripts output JSON. Run via Bash and parse the result.

For public web applications, run `sealos-launchpad-network.mjs` before HTTP smoke. Acceptance requires `ok: true`, an open public network, the expected Service port, and an App URL host match. The script emits an allowlisted network summary and excludes raw Launchpad application data, environment variables, Secrets, and kubeconfig content.

Runtime Event acceptance uses two scans. Capture the first report after readiness with no baseline, wait at least 60 seconds, then pass that report through `--baseline` for the final scan. Extend `--min-window-seconds` to cover one full known reconciliation, probe, or scheduled-work period. An initial Warning Event is an observation; a Warning that advances after the baseline, an unresolved referenced Secret, a Ready transition, a Pod replacement, or a restart delta is an active failure.

For intentional fault injection, retain a pre-injection report as evidence. After recovery reaches Ready, capture a fresh recovery baseline and compare the final scan against that recovery baseline after the full stability window.

## Internal Skill Dependencies

This skill references knowledge files from co-installed internal skills. These are **not** user-facing — they are loaded on-demand during specific phases.

`<SKILL_DIR>` refers to the directory containing this `SKILL.md`. Sibling skills are at `<SKILL_DIR>/../`:

```
<SKILL_DIR>/../
├── sealos-deploy/           ← this skill (user entry point) = <SKILL_DIR>
├── dockerfile-skill/        ← Phase 3: Dockerfile generation knowledge
├── cloud-native-readiness/  ← Phase 0.4 eligibility policy + Phase 1 assessment criteria
└── docker-to-sealos/       ← Phase 5: Sealos template rules
```

Paths used in pipeline.md follow the pattern:
```
<SKILL_DIR>/../dockerfile-skill/knowledge/error-patterns.md
<SKILL_DIR>/../dockerfile-skill/templates/<lang>.dockerfile
<SKILL_DIR>/../docker-to-sealos/references/sealos-specs.md
```

## Phase Overview

| Phase | Action | Skip When |
|-------|--------|-----------|
| 0 — Preflight | Capability scan, path-specific warnings, Sealos auth | Initial blockers resolved |
| 0.4 — Eligibility | Confirm the repository root is a supported cloud workload | Any non-eligible result → stop |
| 0.5 — Template Fast Path | Match GitHub repo to a configured Sealos template | No match, or match cannot materialize template YAML |
| 1 — Assess | Clone repo (or use current project), analyze deployability | Score too low → stop |
| 2 — Detect | Route an evidence-confirmed source-ready static tree to the pinned Nginx image build; otherwise find an existing image | Existing image → jump to Phase 5 |
| 3 — Dockerfile | Generate Dockerfile if missing | Already has one → skip |
| 4 — Build & Push | `docker buildx` → GHCR (auto via gh CLI) or Docker Hub (fallback) | — |
| 5 — Template | Generate Sealos application template | — |
| 5.5 — Configure | Guide user through app env vars and inputs | No inputs needed |
| 6 — Deploy | Deploy template to Sealos Cloud | — |
| 6.5 — Runtime Truth Pass | Verify Launchpad public networking, the actual Sealos runtime, logs, Event convergence, App URL, login path, object-storage flow, and resource footprint | User explicitly requests deploy-only output |

## Decision Flow

```
Input (GitHub URL / local path)
  │
  ▼
[Phase 0] Preflight ── fail → guide user to fix and STOP
  │ pass
  ▼
[Phase 0.5] Template fast path
  │
  ├── materialized template match ───────┐
  │                                      │
  ▼                                      │
[Phase 1] Assess ── not suitable → STOP with reason
  │ suitable
  ▼
[Phase 2] Detect existing image
  │
  ├── found (amd64) ────────────────────┐
  │                                     │
  ▼                                     │
[Phase 3] Dockerfile (generate/reuse)   │
  │                                     │
  ▼                                     │
[Phase 4] Build & Push to registry      │
  │                                     │
  ◄─────────────────────────────────────┘
  │
  ▼
[Phase 5] Generate Sealos Template
  ◄──────────────────────────────────────┘
  │
  ▼
[Phase 5.5] Configure ── present env vars → ask user for inputs → confirm
  │
  ▼
[Phase 6] Deploy to Sealos Cloud ── 401 → re-auth
│                                  409 → instance exists
▼
[Phase 6.5] Runtime Truth Pass ── network/runtime/log/login issue → debug template or runtime config
│
▼
Done — app deployed ✓
```

**Execution rule:** Phase 1 must never start while Phase 0 still has unresolved entry blockers. Docker, `gh`, builder, and registry failures must be reported early, but only become hard blockers if the run later requires local build/push.
