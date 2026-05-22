# Module: Project Analysis

## Purpose

Analyze a project to extract all information needed for Dockerfile generation.

## Execution Steps

### Pre-loaded Context (Optional)

When invoked from the `sealos-deploy` pipeline, Phase 1 analysis results may already
be available (loaded from `.sealos/analysis.json`).

**If analysis.json data is available**, skip overlapping steps and use pre-loaded values:

| Skip Step | Use pre-loaded value |
|-----------|---------------------|
| Step 1 (language/framework) | `language`, `framework` |
| Step 2 (package manager) | `package_manager` |
| Step 4 (port) | `port` |
| Step 5 (databases) | `databases` — only skip DB type detection; still detect S3, search engines, message queues |
| Step 7 (Docker config) | `has_dockerfile` — still check docker-compose.yml and .dockerignore |
| Step 8 (monorepo) | `complexity_tier` — if L1/L2, skip; if L3, still enumerate workspace packages |

**Always run** (Dockerfile-specific, not in analysis.json):
Steps 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17

**If no pre-loaded data** (standalone `/dockerfile`): run all 17 steps as normal.

### Step 1: Detect Language and Framework

Check for these files in order:

```
package.json    → Node.js (check for next/nuxt/express/koa/nest)
requirements.txt  → Python (check for django/flask/fastapi)
pyproject.toml   → Python (modern)
go.mod       → Go
pom.xml       → Java (Maven)
build.gradle    → Java (Gradle)
Cargo.toml     → Rust
composer.json    → PHP
Gemfile       → Ruby
```

For Node.js, additionally check:
- `next.config.*` → Next.js
- `nuxt.config.*` → Nuxt
- `nest-cli.json` → NestJS

### Step 2: Detect Package Manager

```
package-lock.json  → npm
yarn.lock      → yarn
pnpm-lock.yaml   → pnpm
bun.lockb      → bun
```

### Step 3: Extract Build and Run Commands

**Node.js**: Read `package.json` scripts:
```json
{
 "scripts": {
  "build": "...",    // Build command
  "start": "...",    // Production run command
  "dev": "..."      // Development (ignore)
 }
}
```

**Python**: Check for:
- `Makefile` with build targets
- `setup.py` / `pyproject.toml` entry points
- Common patterns: `uvicorn`, `gunicorn`, `python app.py`

**Go**: Standard `go build` → binary execution

### Step 4: Detect Port

Search patterns in source code:

```bash
# Node.js
grep -rE "listen\s*\(\s*[0-9]+" --include="*.js" --include="*.ts"
grep -rE "PORT.*[0-9]+" --include="*.js" --include="*.ts"

# Python
grep -rE "uvicorn.*port|flask.*port|run\(.*port" --include="*.py"

# Go
grep -rE "ListenAndServe.*:" --include="*.go"
```

Common defaults:
- Express/Koa/Nest: 3000
- Next.js: 3000
- FastAPI/Django: 8000
- Go: 8080
- Spring Boot: 8080

### Step 5: Detect External Services

**Purpose**: Auto-detect required external services for docker-compose generation.

**Detection Method**:

```bash
# ============================================
# Database Detection
# ============================================

# PostgreSQL
if grep -rqE "DATABASE_URL|POSTGRES_|postgres:|pg_|prisma|drizzle|typeorm" . 2>/dev/null; then
  DB_TYPE="postgres"

  # Check for vector extension requirement
  if grep -rqE "pgvector|vector.*embedding|createIndex.*vector" . 2>/dev/null; then
    DB_IMAGE="pgvector/pgvector:pg16"
  else
    DB_IMAGE="postgres:16-alpine"
  fi
fi

# MySQL
if grep -rqE "MYSQL_|mysql:|mysql2" . 2>/dev/null; then
  DB_TYPE="mysql"
  DB_IMAGE="mysql:8.0"
fi

# MongoDB
if grep -rqE "MONGODB_|mongodb:|mongoose" . 2>/dev/null; then
  DB_TYPE="mongodb"
  DB_IMAGE="mongo:7"
fi

# ============================================
# Cache/Queue Detection
# ============================================

# Redis
if grep -rqE "REDIS_|ioredis|redis:|bull|bullmq|@upstash/redis" . 2>/dev/null; then
  REDIS_REQUIRED=true
  REDIS_IMAGE="redis:7-alpine"
fi

# RabbitMQ
if grep -rqE "RABBITMQ_|amqp:|amqplib" . 2>/dev/null; then
  RABBITMQ_REQUIRED=true
  RABBITMQ_IMAGE="rabbitmq:3-management-alpine"
fi

# ============================================
# Object Storage Detection
# ============================================

# S3/MinIO
if grep -rqE "S3_|MINIO_|@aws-sdk/client-s3|aws-sdk.*S3" . 2>/dev/null; then
  S3_REQUIRED=true
  # Default to MinIO for self-hosted
  S3_IMAGE="minio/minio:latest"
fi

# ============================================
# Search Engine Detection
# ============================================

# Elasticsearch
if grep -rqE "ELASTIC_|elasticsearch|@elastic/elasticsearch" . 2>/dev/null; then
  SEARCH_TYPE="elasticsearch"
  SEARCH_IMAGE="elasticsearch:8.11.0"
fi

# Meilisearch
if grep -rqE "MEILI_|meilisearch" . 2>/dev/null; then
  SEARCH_TYPE="meilisearch"
  SEARCH_IMAGE="getmeili/meilisearch:v1.5"
fi

# ManticoreSearch
if grep -rqE "MANTICORE|manticoresearch|INDEXER_SEARCH_PROVIDER.*manticore" . 2>/dev/null; then
  SEARCH_TYPE="manticore"
  SEARCH_IMAGE="manticoresearch/manticore:latest"
fi
```

**Output**:
```yaml
external_services:
  database:
    type: "${DB_TYPE}"              # postgres | mysql | mongodb | none
    image: "${DB_IMAGE}"            # Recommended Docker image
    env_var: "DATABASE_URL"         # Primary connection env var
    has_vector: true | false        # If pgvector needed

  redis:
    required: ${REDIS_REQUIRED}
    image: "${REDIS_IMAGE}"
    env_var: "REDIS_URL"

  s3:
    required: ${S3_REQUIRED}
    image: "${S3_IMAGE}"
    provider: "minio | aws | custom"
    env_vars:
      - "S3_ENDPOINT"
      - "S3_ACCESS_KEY"
      - "S3_SECRET_KEY"

  search:
    type: "${SEARCH_TYPE}"          # elasticsearch | meilisearch | manticore | none
    image: "${SEARCH_IMAGE}"
    env_var: "${SEARCH_ENV_VAR}"

  message_queue:
    type: "rabbitmq | kafka | none"
    image: "${MQ_IMAGE}"
```

**docker-compose Generation Rules**:
- Only include services that were detected
- Use detected image variants (e.g., pgvector vs postgres)
- Set appropriate health checks for each service
- Configure proper networking between services
- Generate environment variable templates

### Step 6: Detect System Library Requirements

Check `package.json` dependencies for known native modules:

| NPM Package | Requires |
|-------------|----------|
| sharp | libvips-dev |
| canvas / @napi-rs/canvas | build-essential, libcairo2-dev, libpango1.0-dev |
| better-sqlite3 | python3, make, g++ |
| bcrypt | python3, make, g++ |
| node-gyp (any) | python3, make, g++ |

Check `requirements.txt` for Python:

| Pip Package | Requires |
|-------------|----------|
| psycopg2 | libpq-dev |
| Pillow | libjpeg-dev, libpng-dev |
| cryptography | libssl-dev, libffi-dev |
| lxml | libxml2-dev, libxslt-dev |

### Step 7: Check for Existing Docker Configuration

Look for:
- `Dockerfile` / `Dockerfile.*`
- `docker-compose.yml` / `docker-compose.yaml`
- `.dockerignore`

If found, extract key decisions for reference (DO NOT blindly copy).

### Step 8: Detect Workspace/Monorepo Configuration

**For pnpm workspaces**:
```bash
# Check for pnpm-workspace.yaml
if [ -f "pnpm-workspace.yaml" ]; then
 # Parse workspace packages
 grep -E "^\s*-\s+" pnpm-workspace.yaml
fi

# Check for patches directory (pnpm patch feature)
if [ -d "patches" ]; then
 PATCHES_DIR="patches"
fi
```

**For npm/yarn workspaces**:
```bash
# Check package.json workspaces field
grep -A 20 '"workspaces"' package.json
```

**For Turborepo**:
```bash
# Check for turbo.json
if [ -f "turbo.json" ]; then
 MONOREPO_TYPE="turborepo"
fi
```

**Output for workspace analysis**:
```yaml
workspace:
 enabled: true
 type: "pnpm"          # pnpm | npm | yarn | turborepo | nx
 config_file: "pnpm-workspace.yaml"
 packages:
  - "packages/**"
  - "apps/desktop/src/main"
  - "e2e"
 patches_dir: "patches"     # pnpm patched dependencies
 required_files:         # Files that MUST be copied for workspace to work
  - "pnpm-workspace.yaml"
  - "patches/**"
  - "packages/*/package.json"
  - "apps/desktop/src/main/package.json"
  - "e2e/package.json"
```

### Step 9: Detect Package Manager Configuration

**Check .npmrc / .yarnrc.yml**:
```bash
# Check for lockfile=false (common in some projects)
if grep -q "lockfile=false" .npmrc 2>/dev/null; then
 LOCKFILE_DISABLED=true
fi

# Check for other important settings
grep -E "^(resolution-mode|public-hoist-pattern|shamefully-hoist)" .npmrc
```

**Output**:
```yaml
package_manager_config:
 lockfile_disabled: true     # If lockfile=false in .npmrc
 config_file: ".npmrc"
 special_settings:
  - "lockfile=false"
  - "resolution-mode=highest"
```

### Step 10: Detect Build-Time Environment Variables

**Scan for build-time required env vars**:
```bash
# Check for env validation in config files
grep -rE "process\.env\.\w+" src/ --include="*.ts" --include="*.js" | \
 grep -E "(throw|required|must be set)" | \
 grep -oE "process\.env\.\w+" | sort -u

# Check for @t3-oss/env-nextjs or similar
grep -rE "createEnv|z\.string\(\)" src/env* 2>/dev/null
```

**Common build-time required vars for Next.js**:
- `KEY_VAULTS_SECRET` - Database encryption
- `DATABASE_URL` - For static page generation with DB access
- `AUTH_SECRET` - Authentication

**Output**:
```yaml
build_time_env:
 required:
  - name: KEY_VAULTS_SECRET
   source: "src/libs/server-config/db.ts"
   placeholder: "build-placeholder-32chars"
  - name: DATABASE_URL
   source: "src/libs/server-config/db.ts"
   placeholder: "postgres://placeholder:placeholder@localhost:5432/placeholder"
 optional:
  - name: NEXT_PUBLIC_API_URL
   default: "http://localhost:3000"
```

### Step 11: Detect Custom Scripts and Entry Points

**Check for docker-specific scripts**:
```bash
# Look for docker-specific build scripts
grep -E '"build:docker"|"start:docker"|"docker"' package.json

# Check for custom server entry points
ls -la scripts/serverLauncher/*.js 2>/dev/null
ls -la scripts/*/startServer.js 2>/dev/null
```

**Output**:
```yaml
custom_scripts:
 build: "npm run build:docker"      # Prefer docker-specific if exists
 start: "node startServer.js"
 entry_point: "scripts/serverLauncher/startServer.js"
 migrations: "scripts/migrateServerDB/docker.cjs"
```

### Step 12: Detect Database Migration System

**Purpose**: Critical to detect migrations BEFORE Dockerfile generation to prevent runtime failures.

**Detection Checklist**:
```bash
# 1. Check for migration directories
MIGRATION_DIRS=(
 "packages/database/migrations"
 "prisma/migrations"
 "drizzle"
 "migrations"
 "db/migrations"
 "database/migrations"
)

for dir in "${MIGRATION_DIRS[@]}"; do
 if [ -d "$dir" ]; then
  MIGRATION_DIR="$dir"
  MIGRATION_COUNT=$(find "$dir" -name "*.sql" -o -name "*.ts" -o -name "*.js" | wc -l)
  break
 fi
done

# 2. Detect ORM type
if [ -f "prisma/schema.prisma" ]; then
 ORM="prisma"
 MIGRATION_CMD="npx prisma migrate deploy"
elif [ -f "drizzle.config.ts" ]; then
 ORM="drizzle"
 MIGRATION_CMD="npx drizzle-kit migrate"
elif grep -q "typeorm" package.json; then
 ORM="typeorm"
 MIGRATION_CMD="npx typeorm migration:run"
else
 ORM="unknown"
fi

# 3. Check if migrations run at build time or runtime
if grep -q "build-migrate" package.json; then
 MIGRATION_TIME="build"
elif grep -q "MIGRATION_DB" .env.example 2>/dev/null; then
 MIGRATION_TIME="runtime"
 MIGRATION_ENV_VAR="MIGRATION_DB=1"
else
 MIGRATION_TIME="none" # CRITICAL WARNING
fi

# 4. Check for Next.js Standalone mode + ORM combination
if grep -q "output.*standalone" next.config.* 2>/dev/null && [ "$ORM" != "unknown" ]; then
 # CRITICAL: Standalone mode doesn't include all node_modules
 # ORM dependencies must be installed separately
 STANDALONE_WITH_ORM=true
fi
```

**Output**:
```yaml
migration_system:
 detected: true
 orm: "drizzle"            # prisma | drizzle | typeorm | unknown
 migration_dir: "packages/database/migrations"
 migration_count: 76
 migration_files:
  - "0000_init.sql"
  - "0049_better_auth.sql"
  - "...76 files total"

 execution_timing: "runtime"      # build | runtime | none
 execution_command: "npx drizzle-kit migrate"
 execution_env_var: "MIGRATION_DB=1"

 # Critical pattern detection
 standalone_with_orm: true
 requires_separate_deps: true     # If true, must install ORM separately

 warnings:
  - "Next.js standalone mode + ORM detected - ORM must be installed separately"
  - "76 migration files found - ensure they run before first request"
  - "No automatic migration detected - must add runtime migration"
```

**Warning Conditions**:
- `migration_count > 0` AND `migration_time == "none"` → **CRITICAL: Migrations will never run**
- `standalone_with_orm == true` AND `requires_separate_deps == false` → **Migrations will fail silently**
- `orm == "unknown"` AND `migration_count > 0` → **Cannot determine migration method**

### Step 13: Analyze Build Script Complexity

**Purpose**: Detect memory-intensive or unnecessary build steps to prevent OOM failures.

**Detection Method**:
```bash
# 1. Parse build script from package.json
BUILD_SCRIPT=$(jq -r '.scripts.build' package.json)

# 2. Check for heavy operations
HEAVY_OPS=()

if echo "$BUILD_SCRIPT" | grep -qE "lint|eslint"; then
 HEAVY_OPS+=("lint")
fi

if echo "$BUILD_SCRIPT" | grep -qE "type-check|tsc.*--noEmit"; then
 HEAVY_OPS+=("type-check")
fi

if echo "$BUILD_SCRIPT" | grep -qE "test|jest|vitest"; then
 HEAVY_OPS+=("test")
fi

if echo "$BUILD_SCRIPT" | grep -qE "sitemap|buildSitemap"; then
 HEAVY_OPS+=("sitemap")
fi

# 3. Check workspace package count (memory multiplier)
if [ -f "pnpm-workspace.yaml" ]; then
 WORKSPACE_COUNT=$(grep -E "^\s*-\s+" pnpm-workspace.yaml | wc -l)
 if [ "$WORKSPACE_COUNT" -gt 20 ]; then
  MEMORY_RISK="high"
 elif [ "$WORKSPACE_COUNT" -gt 10 ]; then
  MEMORY_RISK="medium"
 fi
fi
```

**Output**:
```yaml
build_complexity:
 build_script: "npm run prebuild && next build"
 heavy_operations:
  - name: "lint"
   location: "prebuild"
   essential: false
   memory_usage: "2-4GB"
   recommendation: "Skip in Docker build (run in CI)"
  - name: "type-check"
   location: "prebuild"
   essential: false
   memory_usage: "4-8GB"
   recommendation: "Skip in Docker build (run in CI)"
  - name: "sitemap"
   location: "build"
   essential: false
   memory_usage: "500MB"
   recommendation: "Skip in Docker (not needed for container)"

 workspace_package_count: 39
 memory_risk: "high"          # low | medium | high

 recommendations:
  optimized_build: "npx tsx scripts/prebuild.mts && npx next build --webpack"
  memory_limit: "NODE_OPTIONS=--max-old-space-size=8192"
  rationale: "Skip lint/type-check/sitemap to reduce memory from 12GB+ to 4GB"
```

### Step 14: Detect Custom CLI Tools

**Purpose**: Many monorepos use custom CLI tools instead of standard workspace commands.
Using the wrong build command is a common cause of failure.

**Why This Matters**:
- Standard `yarn workspace @pkg build` may not work
- Custom CLI may require specific flags/syntax
- Build outputs may go to non-standard locations
- CLI may depend on git hash, config files, or initialization scripts

**Detection Method**:

```bash
# Step 1: Detect well-known monorepo CLIs
KNOWN_CLIS=("turbo" "nx" "lerna" "rush")
for cli in "${KNOWN_CLIS[@]}"; do
  if [ -f "node_modules/.bin/$cli" ] || grep -q "\"$cli\"" package.json; then
    CLI_NAME="$cli"
    CLI_TYPE="standard"
    break
  fi
done

# Step 2: Detect custom CLI in root package.json scripts
# Look for scripts that invoke a single command (potential CLI)
CUSTOM_CLI=$(jq -r '.scripts | to_entries[] | select(.key | test("^[a-z]+$")) | select(.value | test("^[a-z]+ ")) | .key' package.json 2>/dev/null | head -1)
if [ -n "$CUSTOM_CLI" ] && [ "$CLI_TYPE" != "standard" ]; then
  CLI_NAME="$CUSTOM_CLI"
  CLI_TYPE="custom"
fi

# Step 3: Check for CLI definition in tools/ or scripts/
for dir in "tools/cli" "tools/scripts" "scripts/cli"; do
  if [ -d "$dir" ]; then
    CLI_ENTRY=$(find "$dir" -name "*.js" -o -name "*.ts" | head -1)
    if [ -n "$CLI_ENTRY" ]; then
      CLI_TYPE="custom"
      break
    fi
  fi
done

# Step 4: Analyze how packages are built
# Check if individual packages use CLI internally
for pkg_json in packages/*/package.json apps/*/package.json; do
  if [ -f "$pkg_json" ]; then
    BUILD_CMD=$(jq -r '.scripts.build // ""' "$pkg_json")
    if [ -n "$BUILD_CMD" ] && ! echo "$BUILD_CMD" | grep -qE "^(tsc|webpack|next|vite|esbuild)"; then
      # Non-standard build command, might use custom CLI
      CUSTOM_BUILD_DETECTED=true
    fi
  fi
done

# Step 5: Determine build syntax by examining usage patterns
if [ "$CLI_TYPE" = "standard" ]; then
  case "$CLI_NAME" in
    turbo) BUILD_SYNTAX="yarn turbo run build --filter=\${PACKAGE}" ;;
    nx)    BUILD_SYNTAX="yarn nx build \${PROJECT}" ;;
    lerna) BUILD_SYNTAX="yarn lerna run build --scope=\${PACKAGE}" ;;
    rush)  BUILD_SYNTAX="rush build -t \${PACKAGE}" ;;
  esac
elif [ "$CLI_TYPE" = "custom" ]; then
  # Analyze CLI source or README to determine syntax
  # Common patterns: -p for package, --filter, positional argument
  if grep -rqE "\-p.*package|--package" tools/ 2>/dev/null; then
    BUILD_SYNTAX="yarn $CLI_NAME build -p \${PACKAGE}"
  else
    BUILD_SYNTAX="yarn $CLI_NAME build \${PACKAGE}"
  fi
fi
```

**Git Hash Dependency Detection**:
```bash
# Check if build requires git hash
GIT_HASH_REQUIRED=false
GIT_HASH_ENV=""

# Common patterns for git hash usage
if grep -rqE "GITHUB_SHA|GIT_COMMIT|GIT_SHA|COMMIT_HASH" tools/ src/ scripts/ 2>/dev/null; then
  GIT_HASH_REQUIRED=true
  GIT_HASH_ENV=$(grep -rohE "(GITHUB_SHA|GIT_COMMIT|GIT_SHA|COMMIT_HASH)" tools/ src/ scripts/ 2>/dev/null | sort -u | head -1)
fi

# Check for nodegit, simple-git, or git command usage
if grep -rqE "nodegit|simple-git|Repository.*open|git.*rev-parse" tools/ src/ 2>/dev/null; then
  GIT_HASH_REQUIRED=true
  [ -z "$GIT_HASH_ENV" ] && GIT_HASH_ENV="GITHUB_SHA"
fi
```

**Configuration File Dependencies**:
```bash
# Detect which config files the CLI/build system depends on
CONFIG_DEPS=()

# Check for prettier dependency
if grep -rqE "prettier|\.prettierrc" tools/ scripts/ 2>/dev/null; then
  [ -f ".prettierrc" ] && CONFIG_DEPS+=(".prettierrc")
  [ -f ".prettierignore" ] && CONFIG_DEPS+=(".prettierignore")
fi

# Check for eslint/oxlint dependency
if grep -rqE "eslint|oxlint" tools/ scripts/ 2>/dev/null; then
  [ -f ".eslintrc.js" ] && CONFIG_DEPS+=(".eslintrc.js")
  [ -f "oxlint.json" ] && CONFIG_DEPS+=("oxlint.json")
fi

# Check for tsconfig dependency (almost always needed)
if grep -rqE "tsconfig|typescript" tools/ scripts/ 2>/dev/null; then
  [ -f "tsconfig.json" ] && CONFIG_DEPS+=("tsconfig.json")
fi

# Check postinstall script for init commands
POSTINSTALL=$(jq -r '.scripts.postinstall // ""' package.json)
if [ -n "$POSTINSTALL" ]; then
  POSTINSTALL_RUNS_INIT=true
fi
```

**Static Assets Path Detection**:
```bash
# Detect where backend expects static files
BACKEND_STATIC_PATH=""
FRONTEND_OUTPUTS=()

# Search for static path references in backend code
STATIC_REFS=$(grep -rohE "(static|public|dist|assets).*manifest|readHtmlAssets|webAssets" packages/backend/ src/server/ 2>/dev/null)
if [ -n "$STATIC_REFS" ]; then
  BACKEND_STATIC_PATH=$(echo "$STATIC_REFS" | grep -oE "(static|public)" | head -1)
fi

# Detect frontend build output directories
for frontend_dir in packages/frontend/*/dist apps/*/dist packages/*/.next; do
  if [ -d "$frontend_dir" ] 2>/dev/null || grep -q "output.*dist" "$(dirname $frontend_dir)/package.json" 2>/dev/null; then
    FRONTEND_OUTPUTS+=("$frontend_dir")
  fi
done
```

**Output**:
```yaml
custom_cli:
  detected: true
  name: "${CLI_NAME}"                    # Detected CLI name
  type: "${CLI_TYPE}"                    # standard | custom
  entry: "${CLI_ENTRY}"                  # Path to CLI entry point (if custom)

  build_syntax: "${BUILD_SYNTAX}"        # Complete build command template
  # The ${PACKAGE} placeholder should be replaced with actual package names

  packages_to_build:                     # Detected packages that need building
    - name: "@scope/web"
      build_cmd: "yarn ${CLI_NAME} build -p @scope/web"
      output_dir: "packages/web/dist"
    - name: "@scope/server"
      build_cmd: "yarn ${CLI_NAME} build -p @scope/server"
      output_dir: "packages/server/dist"

  dependencies:
    git_hash_required: ${GIT_HASH_REQUIRED}
    git_hash_env: "${GIT_HASH_ENV}"      # e.g., GITHUB_SHA, GIT_COMMIT
    git_hash_fallback: "docker-build"

    config_files: ${CONFIG_DEPS}         # Files that must NOT be in .dockerignore
    # e.g., [".prettierrc", ".prettierignore", "tsconfig.json"]

    postinstall_runs_init: ${POSTINSTALL_RUNS_INIT}

  static_assets:
    backend_expects: "${BACKEND_STATIC_PATH}"  # e.g., "static", "public"
    frontend_outputs: ${FRONTEND_OUTPUTS}       # Source paths to copy from
    # Generation phase will create COPY commands to map outputs to expected paths
```

**Warning Conditions**:
- `custom_cli.detected == true` AND analysis uses `yarn workspace` → **CRITICAL: Wrong build command**
- `git_hash_required == true` AND git_hash_env not set in Dockerfile → **Build will fail**
- `config_files` items found in `.dockerignore` → **CLI init will fail**
- `frontend_outputs` != `backend_expects` → **Runtime ENOENT errors**

**Key Principle**:
The goal is to DETECT the patterns, not hardcode specific project names. The detection should work for ANY monorepo by analyzing:
1. What CLI is being used (by checking scripts, dependencies, and file structure)
2. What syntax that CLI requires (by analyzing CLI source or documentation)
3. What dependencies the build system has (git hash, config files, etc.)
4. Where outputs are generated and expected (static asset mapping)

### Step 15: Detect Rust/Native Module Requirements

**Purpose**: Some projects include Rust native modules that require special build setup.

**Detection Method**:
```bash
# 1. Check for Cargo files
if [ -f "Cargo.toml" ] || ls packages/*/Cargo.toml 2>/dev/null; then
  HAS_RUST=true
fi

# 2. Check for napi-rs dependencies
if grep -qE "@napi-rs|napi-derive" package.json Cargo.toml 2>/dev/null; then
  HAS_NAPI_RS=true
fi

# 3. Detect native package location
NATIVE_PACKAGES=$(find packages -name "Cargo.toml" -exec dirname {} \;)
```

**Output**:
```yaml
native_modules:
  rust_required: true
  napi_rs: true
  packages:
    - path: "packages/backend/native"
      name: "@scope/native"
      build_command: "yarn workspace @scope/native build"
      targets:
        - "x86_64-unknown-linux-gnu"
        - "aarch64-unknown-linux-gnu"

  build_dependencies:
    - clang
    - llvm
    - pkg-config
    - libssl-dev
```

### Step 16: Validate Build Command Dependencies

**Purpose**: Detect build commands that will fail due to missing config files in Docker context, and automatically determine the resolved build command.

**Core Principle**:
If a config file is in `.dockerignore`, the user intentionally excluded it. Respect that decision by skipping commands that depend on it.

**Detection Method**:
```bash
# Command → Required config files mapping
declare -A CMD_CONFIG_DEPS=(
  ["lint"]=".eslintrc.js .eslintrc.json .eslintrc.cjs eslint.config.js eslint.config.mjs"
  ["eslint"]=".eslintrc.js .eslintrc.json .eslintrc.cjs eslint.config.js eslint.config.mjs"
  ["type-check"]="tsconfig.json"
  ["tsc --noEmit"]="tsconfig.json"
  ["stylelint"]=".stylelintrc .stylelintrc.js .stylelintrc.json .stylelintrc.cjs"
  ["prettier --check"]=".prettierrc .prettierrc.js .prettierrc.json .prettierrc.cjs"
  ["jest"]="jest.config.js jest.config.ts jest.config.mjs"
  ["vitest"]="vitest.config.ts vitest.config.js vitest.config.mts"
)

# Parse build-related scripts
PREBUILD=$(jq -r '.scripts.prebuild // ""' package.json)
BUILD=$(jq -r '.scripts.build // ""' package.json)

# Split script by && or ; into individual commands
# For each command:
#   1. Check if it matches any key in CMD_CONFIG_DEPS
#   2. If yes, find which config file it needs
#   3. Check if config file exists in project
#   4. Check if config file is excluded in .dockerignore
#   5. Determine action: keep or skip

resolve_command() {
  local script="$1"
  local resolved=""

  # Split by &&
  IFS='&&' read -ra COMMANDS <<< "$script"

  for cmd in "${COMMANDS[@]}"; do
    cmd=$(echo "$cmd" | xargs)  # trim whitespace
    should_skip=false
    skip_reason=""

    for pattern in "${!CMD_CONFIG_DEPS[@]}"; do
      if echo "$cmd" | grep -q "$pattern"; then
        config_files="${CMD_CONFIG_DEPS[$pattern]}"

        # Check if any required config exists
        config_found=""
        for cfg in $config_files; do
          if [ -f "$cfg" ]; then
            config_found="$cfg"
            break
          fi
        done

        if [ -z "$config_found" ]; then
          # Config file doesn't exist
          should_skip=true
          skip_reason="Config file not found"
        elif [ -f ".dockerignore" ] && grep -qE "^${config_found}$|^${config_found%.*}\." .dockerignore; then
          # Config file excluded in .dockerignore
          should_skip=true
          skip_reason="Config file excluded in .dockerignore"
        fi
        break
      fi
    done

    if [ "$should_skip" = false ]; then
      if [ -n "$resolved" ]; then
        resolved="$resolved && $cmd"
      else
        resolved="$cmd"
      fi
    fi
  done

  echo "$resolved"
}
```

**Decision Logic**:
```
For each command in build script:
    │
    ├── Command needs config file?
    │   │
    │   ├── NO → Keep command
    │   │
    │   └── YES → Config file exists?
    │             │
    │             ├── NO → Skip command (config doesn't exist)
    │             │
    │             └── YES → Config in .dockerignore?
    │                       │
    │                       ├── YES → Skip command (user excluded it)
    │                       │
    │                       └── NO → Keep command
```

**Output**:
```yaml
build_command_resolution:
  original_prebuild: "tsx scripts/prebuild.mts && npm run lint"
  original_build: "cross-env NODE_OPTIONS=... next build"

  commands:
    - cmd: "tsx scripts/prebuild.mts"
      requires_config: "scripts/prebuild.mts"
      config_status: "available"
      action: "keep"

    - cmd: "npm run lint"
      requires_config: ".eslintrc.js"
      config_status: "excluded_in_dockerignore"
      action: "skip"
      skip_reason: "Config file .eslintrc.js excluded in .dockerignore"

  # Final resolved command for Dockerfile
  resolved_prebuild: "tsx scripts/prebuild.mts"
  resolved_build: "next build --webpack"

  # Full docker build command
  docker_build_command: "npx tsx scripts/prebuild.mts && npx cross-env NODE_OPTIONS=--max-old-space-size=8192 npx next build --webpack"

  skipped_commands:
    - command: "npm run lint"
      reason: "Config file .eslintrc.js excluded in .dockerignore"
```

**Key Rules**:
1. **Respect .dockerignore**: If user excluded a config file, skip commands that need it
2. **No user interaction**: Automatically determine which commands to skip
3. **Document skipped commands**: Record what was skipped and why for Dockerfile comments
4. **Prefix with npx**: Use `npx` for CLI tools to ensure they're found in Docker

### Step 17: Determine Complexity Level

**L1 (Simple)**:
- Single language
- No build step OR simple build (just `npm install`)
- No external service dependencies
- No workspace
- No migrations
- Examples: Express API, simple Python script

**L2 (Medium)**:
- Has build step (Next.js, TypeScript compilation, etc.)
- Has external services (Database, Redis)
- May have environment variable requirements at build time
- Simple migration system
- Examples: Next.js app, Django with PostgreSQL

**L3 (Complex)**:
- Monorepo structure (pnpm-workspace, turborepo, nx)
- Multi-language (Python backend + Node frontend)
- Complex build pipeline
- Many external dependencies
- Has build-time env var requirements
- Custom entry points / server launchers
- Complex migration system (76+ migrations, ORM dependencies)
- Examples: Large monorepo projects, enterprise applications

## Output Format

```yaml
analysis:
 language: "typescript"
 framework: "nextjs"
 framework_version: "16.x"
 package_manager: "pnpm"
 package_manager_version: "10.20.0"

 # Package manager configuration
 package_manager_config:
  lockfile_disabled: true      # lockfile=false in .npmrc
  config_file: ".npmrc"
  install_command: "pnpm install"  # NOT --frozen-lockfile if lockfile disabled

 # Workspace / Monorepo configuration
 workspace:
  enabled: true
  type: "pnpm"
  config_file: "pnpm-workspace.yaml"
  packages:
   - "packages/**"
   - "apps/desktop/src/main"
   - "e2e"
  patches_dir: "patches"
  required_copy_files:       # Files MUST be copied for workspace
   - path: "pnpm-workspace.yaml"
    dest: "./"
   - path: "patches"
    dest: "./patches"
   - path: "packages"
    dest: "./packages"
   - path: "e2e/package.json"
    dest: "./e2e/"
   - path: "apps/desktop/src/main/package.json"
    dest: "./apps/desktop/src/main/"

 # Build configuration
 build:
  command: "npm run build:docker"  # Prefer docker-specific script
  fallback_command: "npm run build"
  output_dir: ".next"
  standalone_mode: true       # output: 'standalone' in next.config
  env_required:           # Build-time required env vars
   - name: KEY_VAULTS_SECRET
    placeholder: "build-placeholder-32chars"
   - name: DATABASE_URL
    placeholder: "postgres://placeholder:placeholder@localhost:5432/placeholder"
   - name: AUTH_SECRET
    placeholder: "build-placeholder-auth-secret"

 # Runtime configuration
 run:
  command: "node startServer.js"
  entry_point: "scripts/serverLauncher/startServer.js"
  port: 3210
  env_required:
   - DATABASE_URL
   - KEY_VAULTS_SECRET
   - AUTH_SECRET

 # External dependencies
 dependencies:
  external_services:
   - type: postgres
    env_var: DATABASE_URL
    recommended_image: "pgvector/pgvector:pg16"
   - type: redis
    env_var: REDIS_URL
    optional: true
   - type: s3
    env_var: S3_ENDPOINT
    optional: true
  system_libs:
   - name: sharp
    packages: ["libvips-dev"]
   - name: "@napi-rs/canvas"
    packages: ["build-essential", "libcairo2-dev", "libpango1.0-dev"]

 # Files that must NOT be excluded from docker build context
 required_files:
  - ".npmrc"            # Package manager config
  - "pnpm-workspace.yaml"
  - "patches/**"
  - "scripts/prebuild.mts"
  - "scripts/serverLauncher/**"
  - "scripts/migrateServerDB/**"
  - "scripts/_shared/**"
  - "packages/database/migrations/**"

 # Existing docker configuration analysis
 existing_docker:
  has_dockerfile: false
  has_compose: false
  key_decisions: []

 # Database migration system
 migration_system:
  detected: true
  orm: "drizzle"
  migration_dir: "packages/database/migrations"
  migration_count: 76
  execution_timing: "runtime"
  execution_env_var: "MIGRATION_DB=1"
  standalone_with_orm: true
  requires_separate_deps: true
  warnings:
   - "Next.js standalone mode + Drizzle ORM - must install drizzle-orm separately"
   - "76 migration files - ensure runtime execution before first request"

 # Build complexity analysis
 build_complexity:
  build_script: "npm run prebuild && next build"
  heavy_operations:
   - name: "lint"
    essential: false
    recommendation: "Skip in Docker (run in CI)"
   - name: "type-check"
    essential: false
    recommendation: "Skip in Docker (run in CI)"
  workspace_package_count: 39
  memory_risk: "high"
  optimized_build: "npx tsx scripts/prebuild.mts && npx next build --webpack"
  memory_limit: "NODE_OPTIONS=--max-old-space-size=8192"

 # Build command resolution (from Step 16)
 build_command_resolution:
  original_prebuild: "tsx scripts/prebuild.mts && npm run lint"
  original_build: "cross-env NODE_OPTIONS=... next build"
  resolved_prebuild: "tsx scripts/prebuild.mts"
  resolved_build: "next build --webpack"
  docker_build_command: "npx tsx scripts/prebuild.mts && npx cross-env NODE_OPTIONS=--max-old-space-size=8192 npx next build --webpack"
  skipped_commands:
   - command: "npm run lint"
     reason: "Config file .eslintrc.js excluded in .dockerignore"

 # Complexity assessment
 complexity: "L3"
 max_iterations: 5

 # Warnings / Notes
 warnings:
  - "Project uses lockfile=false - cannot use --frozen-lockfile"
  - "Workspace packages must be copied individually for Docker cache optimization"
  - "Build requires placeholder env vars for Next.js static generation"
  - "CRITICAL: Migration system detected - must handle ORM dependencies separately"
  - "Build script includes heavy operations - optimize to prevent OOM"
```

## Artifact Output

After completing all 17 analysis steps and displaying the analysis summary in conversation,
write the structured artifact to disk:

**File**: `docker-build/analysis.json`

**Instructions**:
1. Create the `docker-build/` directory if it does not exist: `Bash: mkdir -p docker-build`
2. Write the JSON file using the Write tool with path `docker-build/analysis.json`
3. Populate all fields from the analysis results gathered in Steps 1–17
4. Set `generated_at` to current ISO-8601 timestamp
5. Set `detection_steps_completed` to 17 (or the actual count if any steps were skipped)

**Schema**:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 timestamp>",
  "phase": "analysis",
  "project": {
    "language": "typescript",
    "framework": "nextjs",
    "framework_version": "14.x",
    "package_manager": "pnpm",
    "package_manager_version": "10.20.0"
  },
  "package_manager_config": {
    "lockfile_disabled": false,
    "config_file": ".npmrc",
    "install_command": "pnpm install --frozen-lockfile"
  },
  "workspace": {
    "enabled": true,
    "type": "pnpm",
    "config_file": "pnpm-workspace.yaml",
    "packages": ["packages/**", "apps/**"],
    "patches_dir": "patches",
    "package_count": 39
  },
  "build": {
    "command": "npm run build",
    "resolved_command": "npx tsx scripts/prebuild.mts && npx next build --webpack",
    "output_dir": ".next",
    "standalone_mode": true,
    "env_required": [
      { "name": "KEY_VAULTS_SECRET", "placeholder": "build-placeholder-32chars" }
    ]
  },
  "run": {
    "command": "node server.js",
    "entry_point": "scripts/serverLauncher/startServer.js",
    "port": 3210,
    "env_required": ["DATABASE_URL", "KEY_VAULTS_SECRET", "AUTH_SECRET"]
  },
  "external_services": {
    "database": {
      "type": "postgres",
      "image": "pgvector/pgvector:pg16",
      "env_var": "DATABASE_URL",
      "has_vector": true
    },
    "redis": { "required": false },
    "s3": { "required": false },
    "search": { "type": "none" },
    "message_queue": { "type": "none" }
  },
  "system_libs": [
    { "npm_package": "sharp", "apt_packages": ["libvips-dev"] }
  ],
  "migration_system": {
    "detected": true,
    "orm": "drizzle",
    "migration_dir": "packages/database/migrations",
    "migration_count": 76,
    "execution_timing": "runtime",
    "execution_command": "npx drizzle-kit migrate",
    "execution_env_var": "MIGRATION_DB=1",
    "standalone_with_orm": true,
    "requires_separate_deps": true,
    "warnings": [
      "Next.js standalone mode + Drizzle ORM - must install drizzle-orm separately",
      "76 migration files - ensure runtime execution before first request"
    ]
  },
  "build_complexity": {
    "original_build_script": "npm run prebuild && next build",
    "heavy_operations": [
      { "name": "lint", "essential": false, "recommendation": "Skip in Docker" },
      { "name": "type-check", "essential": false, "recommendation": "Skip in Docker" }
    ],
    "workspace_package_count": 39,
    "memory_risk": "high",
    "docker_build_command": "npx tsx scripts/prebuild.mts && npx next build --webpack",
    "memory_limit": "NODE_OPTIONS=--max-old-space-size=8192",
    "skipped_commands": [
      { "command": "npm run lint", "reason": "Config file .eslintrc.js excluded in .dockerignore" }
    ]
  },
  "custom_cli": { "detected": false },
  "native_modules": { "rust_required": false },
  "complexity": "L3",
  "max_iterations": 5,
  "existing_docker": {
    "has_dockerfile": false,
    "has_compose": false,
    "has_dockerignore": false
  },
  "warnings": [
    "CRITICAL: Migration system detected - must handle ORM dependencies separately"
  ],
  "detection_steps_completed": 17
}
```

The top-level keys are: `schema_version`, `generated_at`, `phase`, `project`, `package_manager_config`,
`workspace`, `build`, `run`, `external_services`, `system_libs`, `migration_system`,
`build_complexity`, `custom_cli`, `native_modules`, `complexity`, `max_iterations`,
`existing_docker`, `warnings`, `detection_steps_completed`.

Populate each key from the corresponding analysis step results. Use actual detected values — the JSON
example above is illustrative (based on a Next.js monorepo) and your output must reflect the actual project.

**Note**: This file is written to `docker-build/` to keep artifacts separate from the generated
Docker files (Dockerfile, .dockerignore, etc.) which remain at the project root.
