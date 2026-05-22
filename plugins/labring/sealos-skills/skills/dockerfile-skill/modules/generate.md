# Module: Dockerfile Generation

## Purpose

Generate production-ready Dockerfile based on analysis results.

## Input

Project analysis from `analyze.md` module.

## Generation Rules

### Rule 1: Select Base Template

Based on `analysis.framework` and `analysis.package_manager`:

| Framework | Package Manager | Template |
|-----------|-----------------|----------|
| express / koa / nestjs | npm/yarn/pnpm | [templates/nodejs-express.dockerfile](../templates/nodejs-express.dockerfile) |
| nextjs | npm/yarn/pnpm | [templates/nodejs-nextjs.dockerfile](../templates/nodejs-nextjs.dockerfile) |
| nextjs | bun | [templates/nodejs-nextjs-bun.dockerfile](../templates/nodejs-nextjs-bun.dockerfile) |
| nuxt | any | [templates/nodejs-nuxt.dockerfile](../templates/nodejs-nuxt.dockerfile) |
| fastapi / flask | any | [templates/python-fastapi.dockerfile](../templates/python-fastapi.dockerfile) |
| django | any | [templates/python-django.dockerfile](../templates/python-django.dockerfile) |
| go (any) | any | [templates/golang.dockerfile](../templates/golang.dockerfile) |
| springboot | any | [templates/java-springboot.dockerfile](../templates/java-springboot.dockerfile) |

**Package Manager Detection**:
- `bun.lockb` → Bun
- `pnpm-lock.yaml` → pnpm
- `yarn.lock` → Yarn
- `package-lock.json` → npm

### Rule 2: Apply Best Practices

Every generated Dockerfile MUST include:

1. **Fixed version tags** (NEVER use `latest`)
  ```dockerfile
  # Good
  FROM node:20.11.1-slim

  # Bad
  FROM node:latest
  FROM node:lts
  ```

2. **Multi-stage build** (when applicable)
  ```dockerfile
  FROM node:20-slim AS deps
  FROM deps AS build
  FROM node:20-slim AS runtime
  ```

3. **Cache optimization**
  ```dockerfile
  # Copy dependency files first
  COPY package.json package-lock.json ./
  RUN npm ci

  # Then copy source
  COPY . .
  ```

4. **BuildKit cache mounts** (for package managers)
  ```dockerfile
  RUN --mount=type=cache,target=/root/.npm npm ci
  RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
  RUN --mount=type=cache,target=/go/pkg/mod go build
  ```

5. **Non-root user**
  ```dockerfile
  USER node     # Node.js
  USER appuser    # Python (create first)
  USER nobody    # Go (statically compiled)
  ```

6. **Minimal runtime image**
  - Node.js: `node:XX-slim` (not alpine, better compatibility)
  - Python: `python:3.XX-slim`
  - Go: `alpine` or `scratch`
  - Java: `eclipse-temurin:XX-jre-alpine`

7. **Clean package manager cache**
  ```dockerfile
  RUN apt-get update && apt-get install -y ... \
    && rm -rf /var/lib/apt/lists/*
  ```

8. **HEALTHCHECK** (without installing curl)
  ```dockerfile
  # Node.js
  HEALTHCHECK CMD node -e "require('http').get('http://127.0.0.1:3000/health')"

  # Python
  HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
  ```

### Rule 3: Handle System Dependencies

If `analysis.dependencies.system_libs` is not empty:

```dockerfile
# Build stage - install build tools
FROM node:20-slim AS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  make \
  g++ \
  && rm -rf /var/lib/apt/lists/*

# Runtime stage - minimal packages only
FROM node:20-slim AS runtime
# Only install runtime libs if needed (e.g., libvips for sharp)
```

### Rule 4: Handle External Services

If `analysis.dependencies.external_services` is not empty:

1. Generate `docker-compose.yml` with required services
2. Document required environment variables
3. Add health checks for dependent services

### Rule 5: Framework-Specific Handling

#### Next.js Special Rules

**Rule 1: Always Enable Standalone Output (Recommended)**

Standalone mode can reduce image size by 80-90% (e.g., from 3GB to 350MB).

1. **Check next.config.{js,mjs,ts}** for existing `output: 'standalone'`
2. **If not present, automatically add it**:
  ```javascript
  // next.config.mjs
  const nextConfig = {
   output: 'standalone', // Add this line
   // ... other config
  }
  ```

3. **Standalone Mode Dockerfile**:
  ```dockerfile
  # Only copy standalone output, no full node_modules needed
  COPY --from=builder /app/public ./public
  COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
  COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
  CMD ["node", "server.js"]
  ```

4. **Non-Standalone Mode** (not recommended, large image):
  ```dockerfile
  COPY --from=build /app/.next ./.next
  COPY --from=build /app/node_modules ./node_modules
  CMD ["npm", "start"]
  ```

**Rule 2: Detect SDK Initialization in API Routes**

Next.js statically analyzes all routes during build. If an API route has top-level SDK initialization:
```typescript
// app/api/mail/route.ts
const resend = new Resend(process.env.RESEND_API_KEY); // Executes at build time!
```

**Detection Method**:
```bash
# Scan for process.env usage in API routes
grep -r "process\.env\.\w\+" app/api/ --include="*.ts" --include="*.tsx"
```

**Fix**: Add placeholder environment variables in build stage
```dockerfile
# Build stage - add placeholders (only for passing static analysis)
ARG RESEND_API_KEY=re_placeholder_key
ARG NOTION_SECRET=placeholder_secret
ENV RESEND_API_KEY=${RESEND_API_KEY}
ENV NOTION_SECRET=${NOTION_SECRET}
# Actual values are injected at runtime via docker run -e or compose
```

**Common SDKs Requiring Placeholders**:
- Resend: `RESEND_API_KEY`
- Stripe: `STRIPE_SECRET_KEY`
- Notion: `NOTION_SECRET`, `NOTION_DB`
- Upstash: `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
- Supabase: `SUPABASE_URL`, `SUPABASE_KEY`

#### Database Migration Handling

**Entrypoint Templates**: When generating `docker-entrypoint.sh`, use the matching template from
`<SKILL_DIR>/templates/assets/` as the starting point instead of writing from scratch:

| ORM detected | Template |
|-------------|----------|
| Drizzle | `docker-entrypoint-drizzle.sh` |
| Prisma | `docker-entrypoint-prisma.sh` |
| TypeORM | `docker-entrypoint-typeorm.sh` |
| None (no migrations) | `docker-entrypoint-plain.sh` |

Replace `{{MIGRATION_DIR}}`, `{{ENTRY_FILE}}`, and `{{DATASOURCE_PATH}}` with actual project values.
You may add project-specific steps (e.g., seed data, cache warmup), but preserve the template's
`set -e`, echo markers, and `exec` for proper signal handling.

**Critical Pattern**: Next.js Standalone + ORM Dependencies

**Problem**: Next.js standalone output doesn't include all `node_modules`. If your app uses an ORM (Drizzle, Prisma, TypeORM), the ORM packages won't be available for migrations.

**Detection** (from analysis phase):
```yaml
migration_system:
 standalone_with_orm: true
 requires_separate_deps: true
 orm: "drizzle"
```

**Solution 1: Separate Dependencies Installation (Recommended)**

Pattern for Next.js Standalone + ORM:

```dockerfile
# Build stage
FROM node:20-slim AS build
WORKDIR /app

# ... build steps ...

# : Install ORM dependencies separately for migrations
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
  mkdir -p /deps && \
  cd /deps && \
  pnpm add pg drizzle-orm --ignore-scripts

# Continue with Next.js build
RUN npm run build

# Production stage
FROM node:20-slim AS production
WORKDIR /app

# Copy standalone output
COPY --from=build /app/.next/standalone ./

# : Copy ORM dependencies separately
COPY --from=build /deps/node_modules/pg ./node_modules/pg
COPY --from=build /deps/node_modules/drizzle-orm ./node_modules/drizzle-orm

# Copy migration files
COPY --from=build /app/packages/database/migrations ./packages/database/migrations

# Create startup script
COPY --chown=nextjs:nodejs docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
```

**Solution 2: Runtime Migration with Separate Deps**

For ORMs that support runtime migration:

```bash
# docker-entrypoint.sh
#!/bin/sh
set -e

echo "Running database migrations..."

# Use separately installed ORM packages
export NODE_PATH=/app/node_modules:/deps/node_modules

# For Drizzle
if [ -f "/app/packages/database/migrations" ]; then
 node -e "require('drizzle-orm/node-postgres').migrate(...)"
fi

# For Prisma
if [ -f "/app/prisma/schema.prisma" ]; then
 npx prisma migrate deploy
fi

echo "Starting application..."
exec node server.js
```

**Solution 3: SQL File Direct Execution (Fallback)**

If ORM approach fails, execute SQL files directly:

```dockerfile
# Copy SQL migration files
COPY --from=build /app/packages/database/migrations/*.sql ./migrations/

# In entrypoint or compose healthcheck
# for file in /app/migrations/*.sql; do
#  psql $DATABASE_URL < $file
# done
```

**ORM-Specific Patterns**:

```yaml
# Drizzle
dependencies:
 - pg
 - drizzle-orm
migration_command: "node -r drizzle-orm/node-postgres ..."

# Prisma
dependencies:
 - prisma
 - @prisma/client
migration_command: "npx prisma migrate deploy"

# TypeORM
dependencies:
 - typeorm
 - pg
migration_command: "npx typeorm migration:run"
```

#### Build Optimization Handling

**Problem**: Build scripts often include CI tasks (lint, type-check) that consume excessive memory in Docker.

**Detection** (from analysis phase):
```yaml
build_complexity:
 heavy_operations: ["lint", "type-check", "sitemap"]
 memory_risk: "high"
 optimized_build: "npx tsx scripts/prebuild.mts && npx next build"
```

**Solution: Skip Non-Essential Build Steps**

```dockerfile
# Build stage
FROM node:20-slim AS build

# Increase memory limit based on complexity
ENV NODE_OPTIONS="--max-old-space-size=8192"

# Don't run full build script with CI tasks
# RUN npm run build # This includes lint, type-check, etc.

# Run only essential build steps
RUN npx tsx scripts/prebuild.mts && \
  npx cross-env NODE_OPTIONS=--max-old-space-size=8192 npx next build --webpack

# Skip optional build artifacts
# - Sitemap generation (not needed in Docker)
# - Type checking (should be in CI)
# - Linting (should be in CI)
```

**Memory Optimization Strategy**:

```yaml
Workspace Package Count:
 0-10 packages: NODE_OPTIONS=--max-old-space-size=4096
 11-20 packages: NODE_OPTIONS=--max-old-space-size=6144
 21+ packages: NODE_OPTIONS=--max-old-space-size=8192

Heavy Operations to Skip:
 - lint/eslint: Run in CI, not in Docker build
 - type-check: Run in CI, not in Docker build
 - test: Run in CI, not in Docker build
 - sitemap: Usually not needed in containerized deployment
 - docs generation: Not needed for runtime
```

**Comment in Generated Dockerfile**:
```dockerfile
# NOTE: Build script optimized for Docker
# - Skipped: lint, type-check (should be done in CI/CD pipeline)
# - Skipped: sitemap generation (not required for containerized deployment)
# - Memory limit increased to 8192MB due to large workspace (39+ packages)
# - Only running essential build steps: prebuild + next build
```

#### Build Command Resolution (from Analysis Step 16)

**Purpose**: Use the auto-resolved build command that skips commands with unavailable config files.

**Input** (from analysis phase `build_command_resolution`):
```yaml
build_command_resolution:
  docker_build_command: "npx tsx scripts/prebuild.mts && npx cross-env NODE_OPTIONS=--max-old-space-size=8192 npx next build --webpack"
  skipped_commands:
    - command: "npm run lint"
      reason: "Config file .eslintrc.js excluded in .dockerignore"
```

**Generation Rules**:

1. **Always use `docker_build_command` from analysis** - never use raw `npm run prebuild` or `npm run build`:
   ```dockerfile
   # Use the resolved command directly
   RUN ${analysis.build_command_resolution.docker_build_command}
   ```

2. **Add comments for skipped commands** - document what was skipped and why:
   ```dockerfile
   # Build the application
   # Auto-resolved build command (commands with unavailable configs skipped)
   # - Skipped: npm run lint (Config file .eslintrc.js excluded in .dockerignore)
   RUN npx tsx scripts/prebuild.mts && \
       npx cross-env NODE_OPTIONS=--max-old-space-size=8192 npx next build --webpack
   ```

3. **Always prefix CLI tools with `npx`** - ensures tools are found in Docker:
   ```dockerfile
   # Correct: use npx prefix
   RUN npx tsx scripts/prebuild.mts && npx next build

   # Incorrect: may fail if not in PATH
   RUN tsx scripts/prebuild.mts && next build
   ```

**Why This Matters**:
- Build scripts often chain multiple commands: `prebuild && lint && build`
- Some commands (lint, type-check) require config files that may be in `.dockerignore`
- Instead of modifying `.dockerignore`, we skip commands that would fail
- This is detected in analysis phase Step 16 and resolved automatically

**No User Interaction Required**:
- Analysis phase determines which commands to skip based on config file availability
- Generation phase simply uses the pre-resolved `docker_build_command`
- Comments document what was skipped for transparency

#### Custom CLI Build Rules (L3 Monorepo)

**CRITICAL**: Many monorepos use custom CLI tools. Using standard `yarn workspace` commands causes silent failures.

**Detection** (from analysis phase Step 14):
```yaml
custom_cli:
  detected: true
  name: "${CLI_NAME}"           # Detected CLI name (e.g., turbo, nx, custom name)
  build_syntax: "${BUILD_CMD}"  # Detected build command syntax
```

**Build Command Generation**:

1. **If custom CLI detected**, use the detected CLI syntax from analysis:
   ```dockerfile
   # Use the exact build_syntax from analysis.custom_cli
   RUN ${analysis.custom_cli.build_syntax}
   ```

   Common CLI patterns (for reference):
   ```dockerfile
   # Turborepo pattern: turbo run <task> --filter=<package>
   RUN yarn turbo run build --filter=@scope/web

   # Nx pattern: nx <task> <project>
   RUN yarn nx build web

   # Lerna pattern: lerna run <task> --scope=<package>
   RUN yarn lerna run build --scope=@scope/web

   # Custom CLI pattern (varies by project)
   RUN yarn ${CLI_NAME} build -p @scope/package
   ```

2. **If git hash required** (`analysis.custom_cli.git_hash_required == true`), set bypass:
   ```dockerfile
   # Set BEFORE build commands
   ENV ${analysis.custom_cli.git_hash_env}=docker-build
   # Common: ENV GITHUB_SHA=docker-build
   ```

3. **If config files required**, ensure NOT in .dockerignore:
   ```dockerfile
   # Copy config files detected as CLI dependencies
   # Files from: analysis.custom_cli.config_files
   COPY ${config_file} ./
   ```

4. **Map static assets** based on analysis:
   ```dockerfile
   # Copy frontend builds to where backend expects
   # Source: analysis.custom_cli.static_assets.frontend_outputs
   # Dest: analysis.custom_cli.static_assets.backend_expects
   COPY --from=builder /app/${frontend_output} ./${backend_expects}
   ```

**Detection Logic** (what analyze.md Step 14 provides):
```yaml
# Analysis output example:
custom_cli:
  detected: true
  name: "turbo"
  entry: "node_modules/.bin/turbo"
  build_syntax: "yarn turbo run build --filter=@scope/web"

  dependencies:
    git_hash_required: false
    config_files: []

  static_assets:
    backend_expects: "public"
    frontend_outputs:
      - src: "apps/web/dist"
        dest: "public"
```

**WRONG patterns to avoid**:
```dockerfile
# WRONG: Using standard workspace command when custom CLI exists
RUN yarn workspace @scope/web build  # May fail or produce wrong output

# WRONG: Assuming build output locations without checking
COPY --from=builder /app/.next ./  # May not exist for custom build system
```

**Key Principle**: ALWAYS use the build command from `analysis.custom_cli.build_syntax`. Never assume standard patterns work.

#### Rust/Native Module Build Stage

**When `analysis.native_modules.rust_required == true`**:

```dockerfile
# Separate native-builder stage
FROM builder AS native-builder

WORKDIR /app

# Install Rust toolchain
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

# Install build dependencies for NAPI-RS
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    llvm \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set clang for tree-sitter compatibility
ENV CC="clang -D_BSD_SOURCE" \
    TARGET_CC="clang -D_BSD_SOURCE"

# Build for correct architecture
ARG TARGETARCH
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    if [ "$TARGETARCH" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then \
        rustup target add aarch64-unknown-linux-gnu && \
        yarn workspace @pkg/native build --target aarch64-unknown-linux-gnu; \
    else \
        rustup target add x86_64-unknown-linux-gnu && \
        yarn workspace @pkg/native build --target x86_64-unknown-linux-gnu; \
    fi
```

#### Monorepo Special Rules (L3)

1. For Turborepo:
  ```dockerfile
  RUN npx turbo prune --scope=<target-app> --docker
  ```

2. For pnpm workspace:
  ```dockerfile
  # Copy workspace configuration
  COPY package.json pnpm-workspace.yaml .npmrc ./

  # Copy all workspace package.json files
  COPY packages ./packages
  COPY patches ./patches
  COPY e2e/package.json ./e2e/
  COPY apps/desktop/src/main/package.json ./apps/desktop/src/main/

  # Install - check if lockfile is disabled
  # If lockfile=false in .npmrc:
  RUN pnpm install --ignore-scripts
  # Otherwise:
  RUN pnpm install --frozen-lockfile --ignore-scripts
  ```

3. For pnpm workspace with `lockfile=false`:
  ```dockerfile
  # IMPORTANT: Do NOT use --frozen-lockfile
  # Check .npmrc for lockfile=false
  RUN pnpm install --ignore-scripts
  ```

4. Handle custom entry points:
  ```dockerfile
  # If project has custom startServer.js or similar
  COPY --from=builder /app/scripts/serverLauncher/startServer.js ./startServer.js
  COPY --from=builder /app/scripts/_shared ./scripts/_shared

  # Handle database migrations
  COPY --from=builder /app/scripts/migrateServerDB/docker.cjs ./docker.cjs
  COPY --from=builder /app/packages/database/migrations ./migrations
  ```

5. Handle build-time environment variables:
  ```dockerfile
  # For Next.js apps that require env vars at build time
  # Use ARG for build-time only (more secure than ENV)
  ARG KEY_VAULTS_SECRET_PLACEHOLDER="build-placeholder-key-32chars"
  ARG DATABASE_URL_PLACEHOLDER="postgres://placeholder:placeholder@localhost:5432/placeholder"

  ENV KEY_VAULTS_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
  ENV DATABASE_URL=${DATABASE_URL_PLACEHOLDER}
  ENV AUTH_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
  ENV DATABASE_DRIVER=""
  ```

6. Handle Node.js path compatibility:
  ```dockerfile
  # Some scripts hardcode /bin/node but node:slim has it in /usr/local/bin
  RUN ln -sf /usr/local/bin/node /bin/node
  ```

## Output Files

### 1. Dockerfile

Generated based on template + rules above.

### 2. .dockerignore

**IMPORTANT**: For workspace/monorepo projects, .dockerignore must be carefully crafted to:
1. Exclude unnecessary files for smaller context
2. BUT include all workspace package.json files
3. BUT include patches directory
4. BUT include required build scripts

**Smart .dockerignore Generation Rules**:

1. Check `analysis.workspace.required_copy_files` - these MUST NOT be excluded
2. Check `analysis.required_files` - these MUST NOT be excluded
3. Use negation patterns (`!`) to re-include specific files

```
# VCS
.git
.gitignore
.gitattributes

# Dependencies (will be installed in container)
node_modules
**/node_modules
.pnpm-store

# Build outputs (will be regenerated)
.next
out
dist
build
coverage
*.tsbuildinfo

# Local environment
.env
.env.local
.env.*.local
# Keep example files for reference
!.env.example
!.env.docker.example

# IDE
.vscode
.idea
*.swp
*.swo

# Documentation (not needed for runtime)
docs
*.md
!README.md

# Tests (for workspace, keep package.json only)
# IMPORTANT: Use e2e/* not e2e to allow !e2e/package.json
e2e/*
!e2e/package.json
tests
**/*.test.ts
**/*.test.tsx
**/*.spec.ts
**/*.spec.tsx

# Desktop app (keep package.json for workspace)
apps/desktop/node_modules
apps/desktop/dist
apps/desktop/out
# Note: Do NOT exclude apps/desktop entirely if it's a workspace package

# CI/CD
.github
.gitlab
.circleci

# Docker files (avoid recursion)
Dockerfile*
docker-compose*.yml
!docker-compose/

# Misc
.DS_Store
Thumbs.db
*.log
npm-debug.log*
.pnpm-debug.log*

# Cache
.cache
.turbo
.eslintcache
.stylelintcache

# Source maps (optional, may want for debugging)
# *.map

# Scripts not needed for runtime
# IMPORTANT: Do NOT exclude scripts needed for build/start
# scripts/prebuild.mts  # Needed for build
# scripts/serverLauncher # Needed for start
scripts/cdnWorkflow
scripts/changelogWorkflow
scripts/docsWorkflow
scripts/i18nWorkflow
scripts/mdxWorkflow
scripts/readmeWorkflow
```

**Validation Checklist for .dockerignore**:

- [ ] All workspace package.json files are NOT excluded
- [ ] patches/ directory is NOT excluded (if pnpm patches used)
- [ ] .npmrc is NOT excluded (needed for pnpm config)
- [ ] Build scripts are NOT excluded (prebuild.mts, etc.)
- [ ] Server launcher scripts are NOT excluded
- [ ] Migration scripts are NOT excluded

### 3. docker-compose.yml (if external services)

**Auto-Detection Rules** (from analysis phase Step 5):

Based on `analysis.dependencies.external_services`, generate appropriate service blocks:

```yaml
# Service detection patterns:
postgres:
  detection: "DATABASE_URL|POSTGRES_|prisma|drizzle|typeorm"
  check_for_vector: "pgvector|vector.*embedding"  # Use pgvector if detected

redis:
  detection: "REDIS_|ioredis|redis|bull|bullmq"

s3/minio:
  detection: "S3_|MINIO_|AWS_S3|@aws-sdk/client-s3"

search_engines:
  elasticsearch: "ELASTIC_|elasticsearch|@elastic"
  meilisearch: "MEILI_|meilisearch"
  manticore: "MANTICORE|manticoresearch"
```

**Template Generation**:

```yaml
services:
  # Main application
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME}-server
    restart: unless-stopped
    ports:
      - "${APP_PORT:-3000}:${APP_PORT:-3000}"
    environment:
      # Auto-generated based on detected services
      - DATABASE_URL=postgres://${DB_USER:-app}:${DB_PASS:-app}@postgres:5432/${DB_NAME:-app}
      - REDIS_URL=redis://redis:6379
      # ... other env vars from analysis
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${APP_PORT}/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    networks:
      - app-network

  # PostgreSQL (if detected)
  # Use pgvector/pgvector:pg16 if vector search detected
  # Use postgres:16-alpine otherwise
  postgres:
    image: ${POSTGRES_IMAGE}  # pgvector/pgvector:pg16 or postgres:16-alpine
    container_name: ${PROJECT_NAME}-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER:-app}
      - POSTGRES_PASSWORD=${DB_PASS:-app}
      - POSTGRES_DB=${DB_NAME:-app}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-app} -d ${DB_NAME:-app}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - app-network

  # Redis (if detected)
  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME}-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # MinIO (if S3 detected and MINIO preferred)
  minio:
    image: minio/minio:latest
    container_name: ${PROJECT_NAME}-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER:-minioadmin}
      - MINIO_ROOT_PASSWORD=${MINIO_PASS:-minioadmin}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

  # ManticoreSearch (if detected)
  manticore:
    image: manticoresearch/manticore:latest
    container_name: ${PROJECT_NAME}-manticore
    restart: unless-stopped
    volumes:
      - manticore-data:/var/lib/manticore
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9308"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  pgdata:
    driver: local
  redis-data:
    driver: local
  minio-data:
    driver: local
  manticore-data:
    driver: local
```

**Generation Logic**:

1. Start with base template (app service only)
2. For each detected service in `analysis.dependencies.external_services`:
   - Add the corresponding service block
   - Add to app's `depends_on` with health check condition
   - Add corresponding volume
   - Add environment variables to app service
3. Only include services that were detected
4. Use appropriate image variants (e.g., pgvector vs postgres)

### 4. Environment Documentation

Output a summary of required environment variables:

```
## Required Environment Variables

### Build Time
(none required)

### Runtime
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string (optional)
- PORT: Server port (default: 3000)
```

## Validation Checklist

Before proceeding to build phase, verify:

- [ ] Base image version is fixed (not `latest`)
- [ ] Multi-stage build is used (if build step exists)
- [ ] Non-root user is configured
- [ ] EXPOSE matches detected port
- [ ] CMD/ENTRYPOINT is correct
- [ ] .dockerignore excludes sensitive files

**Programmatic validation** (if Node.js available):
```bash
node "<SKILL_DIR>/scripts/validate-dockerfile.mjs" "$WORK_DIR/Dockerfile" --port=<port> --json
```
This checks: no `:latest` tags, non-root USER, multi-stage build, COPY order, port match, no -dev packages in runtime, CMD exists, .dockerignore exists.
Fix any reported errors before proceeding to build.

## Artifact Output

After writing all Docker configuration files to disk, write two additional artifacts:

### 1. Generate Report

**File**: `docker-build/generate-report.json`

**Instructions**:
1. Write immediately after all Docker files are created
2. Create the `docker-build/` directory if it does not exist: `Bash: mkdir -p docker-build`
3. Use the Write tool with path `docker-build/generate-report.json`
4. `files_generated`: list every file written in this phase with its path and a one-line description
5. `template_used`: the filename from `templates/` that was selected in Rule 1
6. `key_decisions`: for each significant choice made (standalone mode, separate ORM deps, pgvector image,
   memory limit, skipped build steps), write one entry with `decision` (short identifier) and
   `rationale` (one sentence explaining why, based on what was detected in analysis)
7. `env_vars.build_time`: list env vars added as ARG/ENV placeholders
8. `env_vars.runtime_required`: list env vars the app needs at runtime (from `analysis.run.env_required`)
9. `validation_checklist`: set each boolean based on whether the generated Dockerfile satisfies it

**Schema**:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 timestamp>",
  "phase": "generate",
  "files_generated": [
    { "path": "Dockerfile", "size_bytes": 3240, "description": "Multi-stage production Dockerfile" },
    { "path": ".dockerignore", "size_bytes": 892, "description": "Build context exclusions" },
    { "path": "docker-compose.yml", "size_bytes": 2100, "description": "Compose file with postgres, redis" },
    { "path": ".env.docker.local", "size_bytes": 580, "description": "Auto-generated test secrets" },
    { "path": "docker-entrypoint.sh", "size_bytes": 620, "description": "Startup script with migration handling" },
    { "path": "docker-build/deploy.md", "size_bytes": 1800, "description": "Deployment guide with env vars and run commands" }
  ],
  "template_used": "nodejs-nextjs.dockerfile",
  "key_decisions": [
    { "decision": "standalone_mode", "rationale": "output: standalone detected in next.config.mjs — reduces image size ~80%" },
    { "decision": "separate_orm_deps", "rationale": "Standalone mode + Drizzle ORM requires drizzle-orm installed in /deps" },
    { "decision": "skip_lint_type_check", "rationale": "High memory risk with 39 workspace packages — CI tasks skipped in Docker build" },
    { "decision": "pgvector_image", "rationale": "pgvector extension usage detected — using pgvector/pgvector:pg16 instead of postgres:16-alpine" },
    { "decision": "node_options_8192", "rationale": "39 workspace packages — memory limit set to 8192MB" }
  ],
  "base_image": "node:20.11.1-slim",
  "build_stages": ["deps", "build", "production"],
  "exposed_port": 3210,
  "non_root_user": "nextjs",
  "env_vars": {
    "build_time": [
      { "name": "KEY_VAULTS_SECRET", "type": "placeholder", "placeholder": "build-placeholder-32chars" },
      { "name": "DATABASE_URL", "type": "placeholder", "placeholder": "postgres://placeholder:placeholder@localhost:5432/placeholder" }
    ],
    "runtime_required": ["DATABASE_URL", "KEY_VAULTS_SECRET", "AUTH_SECRET"],
    "runtime_optional": [
      { "name": "PORT", "default": "3210" },
      { "name": "REDIS_URL", "default": null, "optional": true }
    ]
  },
  "compose_services": ["app", "postgres"],
  "validation_checklist": {
    "fixed_base_image_version": true,
    "multi_stage_build": true,
    "non_root_user": true,
    "expose_matches_detected_port": true,
    "healthcheck_present": true,
    "dockerignore_excludes_sensitive": true
  }
}
```

### 2. Deployment Guide

**File**: `docker-build/deploy.md`

Write this file using the Write tool. Use the following template, replacing all `[BRACKETED]` placeholders
with actual values from the analysis and generation results. Do not leave any brackets in the output file.

**Template**:

````markdown
# Deployment Guide

Generated by the Dockerfile skill on [TIMESTAMP].

---

## Required Environment Variables

These must be set for the application to start. The app will fail without them.

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@localhost:5432/myapp` |
| `KEY_VAULTS_SECRET` | 32+ character encryption key | `your-32-char-secret-key-here` |
| `AUTH_SECRET` | Authentication secret | `your-auth-secret` |

> These values were detected from: [SOURCE FILES, e.g., src/libs/server-config/db.ts]

---

## Optional Environment Variables

These have defaults but can be customized.

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3210` | Port the application listens on |
| `NODE_ENV` | `production` | Node environment |

---

## How to Run

### With Docker Compose (Recommended)

```bash
# 1. Copy and edit the environment file
cp .env.docker.local .env.docker.local.real
# Edit .env.docker.local.real with your real values

# 2. Start all services
docker-compose --env-file .env.docker.local.real up -d

# 3. Check status
docker-compose ps
```

### With Docker Run (App Only)

```bash
docker run -d \
  --name [PROJECT_NAME] \
  -p [PORT]:[PORT] \
  -e DATABASE_URL="postgres://user:pass@your-db-host:5432/myapp" \
  -e KEY_VAULTS_SECRET="your-32-char-secret-key-here-xxxxx" \
  -e AUTH_SECRET="your-auth-secret" \
  [IMAGE_NAME]:latest
```

### Build the Image

```bash
docker buildx build --platform linux/amd64 --load -t [IMAGE_NAME]:latest .
```

---

## Exposed Ports

| Port | Protocol | Description |
|------|----------|-------------|
| `[PORT]` | HTTP | Main application |

---

## Health Check

The Dockerfile includes an automatic health check. To verify manually:

```bash
# Check container health status
docker inspect [PROJECT_NAME] --format='{{.State.Health.Status}}'

# Test HTTP endpoint directly
curl -s -o /dev/null -w "%{http_code}" http://localhost:[PORT]
# Expected: 200, 302, or 401
```

---

## Database Migrations

[CONDITIONAL SECTION — only include if migration_system.detected == true]

Migrations run automatically on startup via `docker-entrypoint.sh`.

- **ORM**: [ORM_NAME]
- **Migration count**: [MIGRATION_COUNT] files
- **Migration directory**: [MIGRATION_DIR]
- **Execution timing**: runtime (before app starts)

To verify migrations ran successfully:

```bash
docker-compose exec postgres psql -U [DB_USER] -d [DB_NAME] -c "\dt"
# Expected: list of tables including users, sessions, etc.
```

[END CONDITIONAL — omit this entire section if no migration system detected]

---

## Services (docker-compose)

[CONDITIONAL SECTION — only include if docker-compose.yml was generated]

| Service | Image | Purpose |
|---------|-------|---------|
| `app` | Built from Dockerfile | Main application |
| `postgres` | `pgvector/pgvector:pg16` | Database |

[END CONDITIONAL — omit this entire section if no compose file generated]

---

## Troubleshooting

### App returns 500 error
```bash
docker-compose logs app | tail -50
```
Check for database connection errors or missing environment variables.

### Migrations did not run
```bash
docker-compose exec postgres psql -U [DB_USER] -d [DB_NAME] -c "\dt"
```
If no tables exist, check the entrypoint script logs:
```bash
docker-compose logs app | grep -i "migrat"
```

### Container exits immediately
```bash
docker-compose logs app
```
Usually indicates a missing required environment variable.
````

**Template rules**:
- "Required" vs "Optional" env vars are pulled from `analysis.run.env_required` vs `analysis.run.env_optional`
- The Database Migrations section is **conditional** on `migration_system.detected == true` — omit entirely if false
- The Services table is **conditional** on `external_services` having at least one detected service — omit entirely if no compose file was generated
- All bracketed values `[LIKE_THIS]` must be filled by the agent from analysis results — do not use literal brackets in the output file
- The env var table rows are illustrative — use the actual detected variables for the project
