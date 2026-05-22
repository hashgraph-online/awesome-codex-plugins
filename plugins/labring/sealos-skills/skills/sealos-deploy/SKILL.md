---
name: sealos-deploy
description: Deploy any GitHub project to Sealos Cloud in one command. Assesses readiness, generates Dockerfile, builds image, creates Sealos template, and deploys — fully automated. Use when user says "deploy to sealos", "deploy this project", "deploy to cloud", "deploy this repo", mentions Sealos deployment, wants to deploy a GitHub URL or local project to a cloud platform, or asks about one-click deployment. Also triggers on "/sealos-deploy".
compatibility: Sealos auth/workspace are required for deploys. Docker, buildx, and gh CLI are required only when the selected path needs local build/push. git is required when cloning from a GitHub URL or when git metadata is needed. Node.js 18+ and Python 3.8+ remain optional accelerators.
metadata:
  author: labring
---

# Sealos Deploy

Deploy any GitHub project to Sealos Cloud — from source code to running application, one command.

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
| `score-model.mjs` | `node score-model.mjs <repo-dir>` | Deterministic readiness scoring (0-12) |
| `validate-artifacts.mjs` | `node validate-artifacts.mjs --dir <work-dir>` | Validate `.sealos` JSON artifacts against enforced schemas |
| `detect-image.mjs` | `node detect-image.mjs <github-url> [work-dir]` or `node detect-image.mjs <work-dir>` | Detect existing Docker/GHCR images |
| `build-push.mjs` | `node build-push.mjs <work-dir> <repo> [--registry ghcr\|dockerhub] [--user <user>]` | Build amd64 image & push to the selected registry (Docker Hub path assumes a public image at deploy time; omitting `--registry` keeps auto-detect behavior) |
| `ensure-image-pull-secret.mjs` | `node ensure-image-pull-secret.mjs <namespace> <secret-name> <image-ref> [deployment-name]` | Create/update app-scoped GHCR pull Secret and optionally patch an existing Deployment to reference it |
| `gh-refresh-scopes.mjs` | `node gh-refresh-scopes.mjs write:packages` | Refresh GHCR package access in the current TTY; `write:packages` is sufficient for both push and private pull in this workflow |
| `deploy-template.mjs` | `node deploy-template.mjs <template-path> [--dry-run] [--args-json '{"KEY":"value"}'\|--args-file <file>]` | Resolve the current region from `~/.sealos/auth.json`, build the correct Template API URL, and post a local template YAML |
| `sealos-auth.mjs` | `node sealos-auth.mjs check\|login\|list\|switch` | Sealos Cloud authentication & workspace switching |

All scripts output JSON. Run via Bash and parse the result.

## Internal Skill Dependencies

This skill references knowledge files from co-installed internal skills. These are **not** user-facing — they are loaded on-demand during specific phases.

`<SKILL_DIR>` refers to the directory containing this `SKILL.md`. Sibling skills are at `<SKILL_DIR>/../`:

```
<SKILL_DIR>/../
├── sealos-deploy/           ← this skill (user entry point) = <SKILL_DIR>
├── dockerfile-skill/        ← Phase 3: Dockerfile generation knowledge
├── cloud-native-readiness/  ← Phase 1: assessment criteria
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
| 1 — Assess | Clone repo (or use current project), analyze deployability | Score too low → stop |
| 2 — Detect | Find existing image (Docker Hub / GHCR / README) | Found → jump to Phase 5 |
| 3 — Dockerfile | Generate Dockerfile if missing | Already has one → skip |
| 4 — Build & Push | `docker buildx` → GHCR (auto via gh CLI) or Docker Hub (fallback) | — |
| 5 — Template | Generate Sealos application template | — |
| 5.5 — Configure | Guide user through app env vars and inputs | No inputs needed |
| 6 — Deploy | Deploy template to Sealos Cloud | — |

## Decision Flow

```
Input (GitHub URL / local path)
  │
  ▼
[Phase 0] Preflight ── fail → guide user to fix and STOP
  │ pass
  ▼
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
  │
  ▼
[Phase 5.5] Configure ── present env vars → ask user for inputs → confirm
  │
  ▼
[Phase 6] Deploy to Sealos Cloud ── 401 → re-auth
  │                                  409 → instance exists
  ▼
Done — app deployed ✓
```

**Execution rule:** Phase 1 must never start while Phase 0 still has unresolved entry blockers. Docker, `gh`, builder, and registry failures must be reported early, but only become hard blockers if the run later requires local build/push.
