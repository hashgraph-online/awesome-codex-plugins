---
name: cloud-native-readiness
description: Determine whether a repository contains a supported cloud workload, then assess eligible targets for cloud-native readiness with a 0-12 score. Use for containerization readiness, Docker/Kubernetes compatibility, deployment feasibility, workload eligibility, or pre-deployment assessment. Also triggers on "/cloud-native-readiness".
---

# Cloud Native Readiness Assessment Skill

## Identity and Discovery

- **Owner:** `cloud-native-readiness` (`/cloud-native-readiness` and readiness, containerization, deployment-feasibility, or workload-eligibility requests).
- **Class:** `read-only-observation` with a typed handoff to `dockerfile-skill` only after eligibility and route evidence pass.
- **Canaries:** `CNR-ELIGIBILITY-STOP` and `CNR-ROUTE-HANDOFF`.

## Scope and Boundaries

Accept a local path or GitHub URL and inspect repository evidence. This entry assesses eligibility, readiness, and existing artifacts; it does not write project files or score an unsupported target. A standalone readiness request keeps its report in the request result and does not create `.sealos/analysis.json`; composed deploy orchestration may persist a sanitized handoff snapshot under its own contract. A Dockerfile handoff carries the readiness report as its input artifact and leaves packaging mutations to the receiving owner.

## Risk and Confirmation

Load `knowledge/deployment-eligibility.md` before scoring. An unsupported or unresolved workload stops before artifact detection, scoring, Dockerfile generation, or deployment. Keep source paths, environment values, and any credentials redacted in the report; preserve the current fail-closed eligibility boundary.

## Lifecycle Workflow

For each request, select the repository, run eligibility, assess eligible targets, detect Docker artifacts, and route only when the decision matrix allows it. The request ends with `success`, `stopped`, or `error`; each result carries the selected source, workload type, redaction status, and the strongest evidence reached. The existing three-phase Assess → Detect → Route workflow remains the domain extension below.

## Progressive Disclosure

Load `modules/assess.md`, `modules/detect.md`, and `modules/route.md` one level deep when their phase is reached. Load the deployment-eligibility knowledge before the first score. Do not load Dockerfile detail or invoke the handoff after an eligibility stop.

## Output, Stop, and Error States

- `success`: selected source, eligible workload type, score dimensions, artifact inventory, concerns, recommendation, verification evidence, and any typed handoff are present.
- `stopped`: selected source, workload type, eligibility or confirmation reason codes, observed evidence, redaction result, and safe next action are present; no downstream artifact is claimed.
- `error`: selected source, failed phase/helper or artifact, sanitized diagnostic, redaction result, and recovery action are present.

## Handoffs

When eligible and the route requires packaging, send the complete typed handoff below for an assessment-only request. The receiving skill re-checks its own scope and canaries.

```yaml
target: dockerfile-skill
inputArtifact: readiness report with source, project language/framework/package manager, dependencies/configuration, workload, score, dimensions, concerns, and artifact inventory
allowedAction: generate Docker packaging within the receiving skill's owned file scope
failureReturn: readiness findings and the failed route condition
responseOwner: cloud-native-readiness
```

## Verification

Use `workload-eligibility.mjs`, `score-model.mjs`, the current readiness eval evidence, and the baseline traces `readiness-positive-eligible` and `readiness-violating-ineligible`. Verify eligibility before score/build, preserve report fields, and redact credential-shaped values.

## Readiness Report Contract

Keep this payload request-scoped and repository-relative. A downstream handoff may reuse it without repeating discovery.

```yaml
source:
  kind: local-path | github-url
  display: redacted repository identifier
project:
  language: detected language
  framework: detected framework or null
  package_manager: detected package manager or null
  dependencies: redacted external dependency types and versions
  configuration: redacted configuration and environment-key observations
workload:
  type: server | static-web | worker | scheduled-job | reviewed-remote-desktop | unresolved
  eligibility: eligible | ineligible | needs_review
assessment:
  score: 0-12 or null when stopped
  dimensions: six named scores when eligible
  concerns: redacted findings
artifacts:
  status: complete | partial | none
  inventory: repository-relative paths and quality observations
recommendation: report-only | package | remediate | stop
verification:
  helper: eligibility and/or scoring helper invoked
  evidence: observed result and redaction status
handoff: typed tuple or none
terminal_state: success | stopped | error
safe_next_action: request-scoped next action
```

The payload never contains passwords, tokens, kubeconfig contents, environment values, or complete connection strings.

## Overview

This skill evaluates a repository's readiness for cloud-native microservice deployment through a 3-phase workflow:

1. **Assess** - Reject unsupported workload types, then score eligible targets
2. **Detect** - Check if Docker artifacts already exist (Dockerfile, docker-compose, container images)
3. **Route** - If artifacts exist, return the result directly; if not, invoke `dockerfile-skill` to containerize

## Workflow

```
cloud-native-readiness
  │
  ├─ Phase 1: Cloud-Native Assessment
  │    ├─ Eligibility fails or needs review → Report evidence, END
  │    └─ Eligible → Calculate readiness score
  │
  ├─ Phase 2: Existing Artifacts Detection
  │    ├─ Found Dockerfile/docker-compose/image → Report existing setup, END
  │    └─ Not found → Continue
  │
  └─ Phase 3: Route to dockerfile-skill
       └─ Invoke /dockerfile to generate Docker configuration
```

## Usage

```
/cloud-native-readiness              # Assess current directory
/cloud-native-readiness <path>       # Assess specific path
/cloud-native-readiness <github-url> # Clone and assess
```

## Quick Start

When invoked, read and execute [modules/assess.md](modules/assess.md) first. Continue to
[modules/detect.md](modules/detect.md) and [modules/route.md](modules/route.md) only when
the assessment report resolves the requested root as `eligible`. An `ineligible`,
unresolved `needs_review`, or error result ends the request with its evidence and safe
next action before artifact detection or downstream routing.

## Phase 1: Cloud-Native Readiness Assessment

Load and execute: [modules/assess.md](modules/assess.md)

Apply [knowledge/deployment-eligibility.md](knowledge/deployment-eligibility.md)
before assigning a readiness score. Continue only when the requested root is
classified `eligible`.

**Evaluates 6 dimensions** (each scored 0-2):

| Dimension | What to check |
|-----------|---------------|
| Statelessness | Does the app store state locally (sessions in memory, local file writes)? |
| Config Externalization | Are configs hardcoded or driven by env vars / config files? |
| Horizontal Scalability | Can multiple instances run without conflicts? |
| Startup/Shutdown | Does the app start fast and handle SIGTERM gracefully? |
| Observability | Does it have health checks, structured logging, metrics? |
| Service Boundaries | Is it a focused service or a tightly-coupled monolith? |

**Scoring**:
- **10-12**: Excellent — fully cloud-native ready
- **7-9**: Good — ready with minor adjustments
- **4-6**: Fair — needs some refactoring before containerization
- **0-3**: Poor — significant rework needed, not recommended for containerization now

**Output**: Structured readiness report with score, findings, and recommendations.

## Phase 2: Existing Artifacts Detection

Load and execute: [modules/detect.md](modules/detect.md)

**Checks for**:
- `Dockerfile` / `Dockerfile.*` (multi-stage, multi-service)
- `docker-compose.yml` / `docker-compose.yaml` / `compose.yml`
- `.dockerignore`
- `DOCKER.md` or docker-related documentation
- Container registry references (ghcr.io, docker.io, ECR, GCR, ACR)
- Kubernetes manifests (`k8s/`, `kubernetes/`, `deploy/`, `helm/`, `charts/`)
- CI/CD pipeline with Docker build steps (`.github/workflows/`, `.gitlab-ci.yml`)

**Output**: Inventory of existing Docker/K8s artifacts with quality assessment.

## Phase 3: Routing Decision

Load and execute: [modules/route.md](modules/route.md)

**Decision Matrix**:

An `ineligible` or unresolved `needs_review` result always stops before artifact
detection or Dockerfile generation. Apply the score matrix only to `eligible` targets.

| Readiness Score | Artifacts Exist | Action |
|-----------------|-----------------|--------|
| ≥ 7 | Yes, complete | Report existing setup. Done. |
| ≥ 7 | Yes, partial | Report gaps, suggest improvements. Done. |
| ≥ 7 | No | Invoke `dockerfile-skill` to generate. |
| 4-6 | Any | Report issues + remediation steps. Optionally proceed with `dockerfile-skill`. |
| 0-3 | Any | Report blockers. Do NOT invoke `dockerfile-skill`. |

## Readiness Report Format

The final output MUST use this format:

For a stopped eligibility result, report its workload type, reason codes, evidence,
and next action without inventing a readiness score.

```markdown
# Cloud-Native Readiness Report

## Summary
- **Project**: {name}
- **Eligibility**: {eligible | ineligible | needs_review} — {workload type}
- **Score**: {score}/12 ({rating})
- **Verdict**: {Ready | Ready with caveats | Needs work | Not recommended}

## Assessment Details

### ✅ Strengths
- {what's already cloud-native friendly}

### ⚠️ Concerns
- {issues that need attention}

### ❌ Blockers (if any)
- {critical issues preventing containerization}

## Dimension Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Statelessness | {0-2} | {detail} |
| Config Externalization | {0-2} | {detail} |
| Horizontal Scalability | {0-2} | {detail} |
| Startup/Shutdown | {0-2} | {detail} |
| Observability | {0-2} | {detail} |
| Service Boundaries | {0-2} | {detail} |

## Existing Docker Artifacts
- {inventory or "None found"}

## Recommendation
- {next steps}
```

## Supporting Resources

- **Deployment Eligibility**: [knowledge/deployment-eligibility.md](knowledge/deployment-eligibility.md) — Supported workload types and fail-closed routing
- **Assessment Criteria**: [knowledge/criteria.md](knowledge/criteria.md) — Detailed scoring rubrics
- **Anti-Patterns**: [knowledge/anti-patterns.md](knowledge/anti-patterns.md) — Common cloud-native anti-patterns
- **Examples**: [examples/](examples/) — Sample readiness reports

## Integration with dockerfile-skill

When routing to `dockerfile-skill`, pass the assessment context:

1. The readiness report findings inform Dockerfile generation decisions
2. Detected external services map directly to `docker-compose.yml` services
3. Identified concerns become Dockerfile comments / `DOCKER.md` caveats
4. The assessment's config externalization findings drive ENV/ARG setup

**Handoff**: When invoking `dockerfile-skill`, include a summary of:
- Detected language/framework/package manager
- External service dependencies
- Config externalization status
- Any special concerns (stateful components, long startup, etc.)
