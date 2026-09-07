---
name: dockerfile-skill
description: Generate production-ready Dockerfile for any GitHub project. Supports monorepo, multi-stage builds, workspace detection, and iterative build-fix cycles. Use when user asks to create, generate, write, fix, or improve a Dockerfile, wants to containerize an application, mentions Docker build issues, needs a .dockerignore, or wants to package their app as a Docker image. Also triggers on "/dockerfile".
---

# Dockerfile Generator Skill

## Identity and Discovery

- **Owner:** `dockerfile-skill` (`/dockerfile` and Dockerfile, containerize, build-fix, or Docker build requests).
- **Class:** `local-artifact-mutation` with a validated packaging handoff to `sealos-deploy`.
- **Canaries:** `DFS-RUNTIME-ACCEPT`, `DFS-OWNED-FILES`, and `DFS-REDACT`.

## Scope and Boundaries

Accept a local path or GitHub URL, optionally with a readiness report from `cloud-native-readiness`. Analyze and write only the named packaging artifacts (`Dockerfile`, `.dockerignore`, optional compose/entrypoint/docs and deploy-side build evidence); preserve pre-existing files and project values by default. A replacement requires an explicit request decision recorded before mutation. Build, migration, HTTP, and log validation remain required before a result is accepted.

## Risk and Confirmation

Keep generated secrets, environment values, database URLs, and connection details out of reports. A required package or system-tool installation follows the current project confirmation boundary. Never treat a successful `docker build` as runtime acceptance; the `DFS-RUNTIME-ACCEPT` canary requires migration/table, HTTP, health, and log evidence.

## Lifecycle Workflow

For each request, analyze the project, generate owned packaging, run the closed-loop build/fix phase, and run runtime validation. Emit request-scoped `success`, `stopped`, or `error`; the existing four-phase Deep Analysis → Generate → Build & Fix → Runtime Validation workflow remains the domain extension below.

## Progressive Disclosure

Load `modules/analyze.md`, `modules/generate.md`, and `modules/build-fix.md` one level deep when their phase is reached. Load knowledge/templates only from those owned branches and retain the existing error-pattern routing.

## Output, Stop, and Error States

- `success`: source/provenance, named packaging files, successful image/build identity, migration/database proof, HTTP/health response, quiet runtime logs, verification evidence, and redaction result.
- `stopped`: unresolved analysis, missing precondition, replacement or installation decision, or unavailable runtime input with observed evidence, redaction result, and safe next action; no partial acceptance claim.
- `error`: failed build, migration, HTTP, health, or log step with its artifact, sanitized diagnostic, redaction result, and recovery action.

## Handoffs

Send the complete typed handoff below for direct packaging requests. Deploy must preserve its own eligibility and Runtime Truth gates.

```yaml
target: sealos-deploy
inputArtifact: validated Dockerfile and build/runtime result with source provenance
allowedAction: build or reuse an image within the selected deployment scope
failureReturn: failing packaging, migration, HTTP, health, or runtime-log phase
responseOwner: dockerfile-skill
```

## Verification

Use the runtime validation commands in this entry, `node --check` for changed helpers, and baseline cases `dockerfile-positive-build-runtime` and `dockerfile-violating-build-only`. Verify actual container behavior, migrations, HTTP, logs, file scope, and redaction.

## Packaging Result Contract

Keep the result request-scoped and repository-relative. A build artifact does not
become a successful handoff until the runtime result is accepted.

```yaml
source: local path or GitHub source, with readiness provenance when provided
owned_files: named files planned, created, preserved, or changed
build:
  dockerfile_valid: true | false
  image_identity: redacted tag or digest
  result_artifact: docker-build/build-result.json
runtime:
  migration: applicable | not_applicable | failed
  database_or_state_proof: observed evidence or null
  http_health: accepted response and health evidence or null
  log_analysis: error count and sanitized findings
  result_artifact: docker-build/validation-result.json
verification:
  redaction: pass | fail
  helper_checks: named commands and outcomes
terminal_state: success | stopped | error
safe_next_action: request-scoped recovery or handoff action
```

`success` requires the Dockerfile and build result plus the applicable migration,
HTTP/health, and runtime-log checks. The result never contains passwords, tokens,
environment values, database URLs, or complete connection strings.

## Overview

This skill generates production-ready Dockerfiles through a 4-phase process:
1. **Deep Analysis** - Understand project structure, workspace, migrations, and build complexity
2. **Generate** - Create Dockerfile with migration handling and build optimization
3. **Build & Fix** - Validate through actual build, fix errors iteratively
4. **Runtime Validation** - Verify migrations ran, app works, database populated

## Key Capabilities

- **Workspace/Monorepo Support**: pnpm workspace, Turborepo, npm workspaces
- **Custom CLI Detection**: Auto-detect custom build CLIs (turbo, nx, lerna, rush, or project-specific) and use correct syntax
- **Git Hash Bypass**: Detect and handle projects requiring git commit hash (GITHUB_SHA)
- **Build-Time Env Vars**: Auto-detect and add placeholders for Next.js SSG
- **Error Pattern Database**: 40+ known error patterns with automatic fixes
- **Smart .dockerignore**: Avoid excluding workspace-required files and CLI config dependencies
- **Custom Entry Points**: Support for custom server launchers
- **Migration Detection**: Auto-detect ORM, migrations, handle standalone mode
- **Build Optimization**: Skip heavy CI tasks (lint/type-check) to prevent OOM
- **Runtime Validation**: Verify migrations ran, database populated, app working
- **Native Module Support**: Auto-detect Rust/NAPI-RS modules, multi-architecture builds
- **Static Asset Mapping**: Detect backend's expected static paths and map frontend outputs
- **External Services**: Auto-detect PostgreSQL, Redis, MinIO, ManticoreSearch dependencies
- **Zero Human Interaction**: Auto-generate all config files including secrets

## Usage

```
/dockerfile          # Analyze current directory
/dockerfile <github-url>    # Clone and analyze GitHub repo
/dockerfile <path>       # Analyze specific path
```

## Quick Start

When invoked, ALWAYS follow this sequence:

1. Read and execute [modules/analyze.md](modules/analyze.md)
2. Read and execute [modules/generate.md](modules/generate.md)
3. Read and execute [modules/build-fix.md](modules/build-fix.md)

## Workflow

### Phase 1: Deep Project Analysis

Load and execute: [modules/analyze.md](modules/analyze.md)

**Output**: Structured project metadata including:
- Language / Framework / Package manager
- Build commands / Run commands / Port
- External dependencies (DB/Redis/S3)
- System library requirements
- **Migration system detection** (ORM, migration count, execution method)
- **Build complexity analysis** (heavy operations, memory risk)
- Complexity level (L1/L2/L3)

### Phase 2: Generate Dockerfile

Load and execute: [modules/generate.md](modules/generate.md)

**Input**: Analysis result from Phase 1
**Output**:
- `Dockerfile` (with migration handling, build optimization)
- `.dockerignore` (workspace-aware)
- `docker-compose.yml` (if external services needed)
- `.env.docker.local` (optional placeholder keys only; never secret values)
- `docker-entrypoint.sh` (with migration execution)
- `DOCKER.md` (complete deployment guide)
- Environment variable documentation

**Key Enhancements**:
- Auto-detect Next.js Standalone + ORM → separate deps installation
- Auto-detect heavy build operations → optimized build command
- Auto-generate all config files → zero user input required

### Phase 3: Build Validation (Closed Loop)

Load and execute: [modules/build-fix.md](modules/build-fix.md)

**Process**:
1. Execute `docker buildx build --platform linux/amd64 --load`
2. If success → Proceed to Phase 4
3. If failure → Parse error, match pattern, fix Dockerfile, retry
4. Max iterations based on complexity level

### Phase 4: Runtime Validation

**Critical Addition**: Don't declare success until runtime verification passes!

**Validation Steps**:
1. **Container Startup**: `docker-compose up -d` and verify no crashes
2. **Database Migration**:
  - Query database: `psql -c "\dt"` → verify tables exist
  - Check migration count matches expected (e.g., 76/76)
  - Verify no "relation does not exist" errors
3. **Application Health**:
  - Test HTTP endpoint → 200/302/401 acceptable, 500 is failure
  - Check logs for errors
  - Verify health check endpoint
4. **Success Criteria**: Only declare success if ALL pass

**Why This Matters**:
- Previous: Declared success after `docker build`, but app didn't work at runtime
- Now: Verify migrations ran, database populated, app actually functional
- Prevents silent migration failures (e.g., standalone mode missing ORM deps)

## Supporting Resources

- **Templates**: [templates/](templates/) - Base Dockerfile templates by tech stack
- **Error Patterns**: [knowledge/error-patterns.md](knowledge/error-patterns.md) - Known errors and fixes
- **System Dependencies**: [knowledge/system-deps.md](knowledge/system-deps.md) - NPM/Pip package → system library mapping
- **Best Practices**: [knowledge/best-practices.md](knowledge/best-practices.md) - Docker production best practices
- **Output Format**: [examples/output-format.md](examples/output-format.md) - Expected output structure

## Complexity Levels

| Level | Criteria | Max Build Iterations |
|-------|----------|---------------------|
| L1 | Single language, no build step, no external services, no migrations | 1 |
| L2 | Has build step, has external services (DB/Redis), simple migrations | 3 |
| L3 | Monorepo, multi-language, complex dependencies, build-time env vars, complex migrations (76+) | 5 |

## Common Issues & Solutions

### 1. Database migrations not running - MOST CRITICAL
**Symptom**: `relation "users" does not exist` at runtime
**Cause**: Migrations detected but never executed
**Prevention**: Analysis phase Step 12 detects migrations and configures execution
**Fix**:
- For Standalone + ORM: Install ORM deps separately
- Add runtime migration to entrypoint script
- Verify with `psql -c "\dt"` after container starts

### 2. Out of Memory during build
**Symptom**: Exit code 137, `Killed`, heap out of memory
**Cause**: Build script includes lint/type-check for 39+ workspace packages
**Prevention**: Analysis phase Step 13 detects heavy operations
**Fix**: Skip CI tasks in Docker build, increase NODE_OPTIONS to 8192MB

### 3. Workspace files not found
**Symptom**: `ENOENT: no such file or directory, open '/app/e2e/package.json'`
**Cause**: .dockerignore excludes workspace package.json files
**Fix**: Use `e2e/*` instead of `e2e`, then `!e2e/package.json`

### 4. lockfile=false projects
**Symptom**: `Cannot generate lockfile because lockfile is set to false`
**Cause**: Project has `lockfile=false` in .npmrc
**Fix**: Use `pnpm install` instead of `pnpm install --frozen-lockfile`

### 5. Build-time env vars missing
**Symptom**: `KEY_VAULTS_SECRET is not set`
**Cause**: Next.js SSG needs env vars at build time
**Fix**: Add ARG/ENV placeholders in build stage

### 6. Node binary path
**Symptom**: `spawn /bin/node ENOENT`
**Cause**: Scripts hardcode `/bin/node` but `node:slim` has it at `/usr/local/bin/node`
**Fix**: Add `RUN ln -sf /usr/local/bin/node /bin/node`

### 7. ORM not found in Standalone mode
**Symptom**: `Cannot find module 'drizzle-orm'` at runtime
**Cause**: Next.js standalone doesn't include all node_modules
**Prevention**: Analysis phase detects standalone + ORM combination
**Fix**: Install ORM separately in /deps and copy to final image

### 8. Wrong build command for monorepo with custom CLI
**Symptom**: Build succeeds but output files missing (e.g., `assets-manifest.json` not found)
**Cause**: Using `yarn workspace @scope/pkg build` instead of detected custom CLI syntax
**Prevention**: Analysis phase Step 14 detects custom CLI
**Fix**: Use detected CLI syntax for all build commands

### 9. Git hash required but .git not in Docker context
**Symptom**: `Failed to open git repo` or `nodegit` errors
**Cause**: Build tool requires git commit hash for versioning
**Prevention**: Analysis phase Step 14 detects git hash dependency
**Fix**: Set `ENV GITHUB_SHA=docker-build` to bypass git requirement

### 10. CLI config files excluded by .dockerignore
**Symptom**: CLI initialization (e.g., `${CLI_NAME} init`) fails silently
**Cause**: `.prettierrc`, `.prettierignore`, or other config files excluded
**Prevention**: Analysis phase Step 14 detects config file dependencies
**Fix**: Remove config files from .dockerignore exclusions

### 11. Static assets not found at runtime
**Symptom**: `ENOENT: no such file or directory, open '/app/static/assets-manifest.json'`
**Cause**: Frontend builds to different path than backend expects
**Prevention**: Analysis phase Step 14 detects static asset path mapping
**Fix**: Copy frontend outputs to backend's expected path in Dockerfile

## Success Criteria

A successful Dockerfile must:

**Build Phase**:
1. Build without errors (`docker buildx build` exits 0)
2. Image size reasonable (< 2GB for most apps)
3. Follow production best practices (multi-stage, non-root, fixed versions)
4. Include all necessary supporting files (.dockerignore, docker-compose.yml, etc.)
5. Handle all workspace/monorepo requirements

**Runtime Phase** - CRITICAL:
6. Container starts successfully (no crashes)
7. **Database migrations execute successfully** (if migrations detected)
8. **Database tables created** (verify with psql)
9. **Application responds with valid HTTP codes** (200/302/401, not 500)
10. **No runtime errors in logs** (no "relation does not exist", etc.)

**DO NOT declare success if**:
- Build passes but runtime fails
- Migrations detected but tables missing
- App returns 500 errors
- Logs show database relation errors

## Post-Build Validation COMPREHENSIVE

After successful build, perform FULL validation:

```bash
# 1. Start services
docker-compose up -d
sleep 30 # Wait for startup

# 2. Check container status
docker-compose ps
# Expected: All containers UP and HEALTHY

# 3. Verify database migrations
if [ migrations_detected ]; then
 # List tables
 docker-compose exec postgres psql -U <user> -d <db> -c "\dt"
 # Expected: List of tables (users, sessions, etc.)
 # If "Did not find any relations" → FAIL

 # Count migrations
 MIGRATION_COUNT=$(docker-compose exec postgres psql -U <user> -d <db> -t -c "SELECT COUNT(*) FROM <migration_table>;")
 # Expected: Matches analysis count (e.g., 76)
fi

# 4. Test application health
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3210)
# Expected: 200, 302, or 401
# Unacceptable: 500, 502, 503

if [ "$HTTP_CODE" = "500" ]; then
 echo "FAILURE: App returning 500 error"
 docker-compose logs app
 exit 1
fi

# 5. Check for errors in logs
docker-compose logs app | grep -i "error" | tail -20
# Should NOT contain:
# - "relation does not exist"
# - "table not found"
# - "Cannot find module"

# 6. Check image size
docker images <image-name>

# 7. Cleanup (if needed)
docker-compose down
```

**Validation Checklist**:
- [ ] Image built successfully
- [ ] Container started without crashes
- [ ] Database connection established
- [ ] **Migrations executed (if applicable)**
- [ ] **Database tables exist (if applicable)**
- [ ] HTTP endpoint returns valid status
- [ ] No errors in application logs
- [ ] Health check passes
