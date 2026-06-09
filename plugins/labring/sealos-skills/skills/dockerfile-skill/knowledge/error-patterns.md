# Error Pattern Knowledge Base

## Pattern Format

Each pattern includes:
- **regex**: Pattern to match in error output
- **category**: Error classification
- **fix**: Dockerfile modification to apply
- **confidence**: How reliably this fix works (high/medium/low)

---

## Category: File System

### ENOENT - File Not Found

```yaml
pattern: "ENOENT.*no such file or directory.*['\"](.+?)['\"]"
category: filesystem
confidence: high
extract: path from capture group 1
fix: |
 # Before the failing RUN command, add:
 RUN mkdir -p $(dirname {path}) && touch {path}
 # Or for JSON config:
 RUN mkdir -p $(dirname {path}) && echo '{}' > {path}
```

### ENOENT - Module Not Found

```yaml
pattern: "Cannot find module ['\"](.+?)['\"]"
category: filesystem
confidence: medium
extract: module name
fix: |
 # Check if it's a local file that wasn't copied
 # Add to COPY if needed:
 COPY {module_path} ./
```

### Directory Not Found

```yaml
pattern: "ENOTDIR|directory.*not found|No such file or directory: ['\"](.+?)['\"]"
category: filesystem
confidence: high
fix: |
 RUN mkdir -p {directory}
```

---

## Category: Environment Variables

### Required Env Not Set

```yaml
pattern: "`(.+?)` is not set|(.+?) environment variable is required|process\\.env\\.(.+?) is (not defined|undefined)"
category: environment
confidence: high
extract: variable name
fix: |
 # In build stage:
 ARG {VAR_NAME}=placeholder_for_build
 ENV {VAR_NAME}=${{VAR_NAME}}
```

### KeyError (Python)

```yaml
pattern: "KeyError: ['\"](.+?)['\"]"
category: environment
confidence: medium
extract: key name
fix: |
 # Check if it's an env var access
 ENV {KEY}=placeholder
```

---

## Category: Memory

### JavaScript Heap OOM

```yaml
pattern: "JavaScript heap out of memory|FATAL ERROR.*Allocation failed"
category: memory
confidence: high
fix: |
 ENV NODE_OPTIONS="--max-old-space-size=4096"
 # If already set to 4096, increase to 8192
```

### Process Killed (OOM Killer)

```yaml
pattern: "Killed|Exit code: 137|signal: SIGKILL"
category: memory
confidence: high
fix: |
 # For Node.js:
 ENV NODE_OPTIONS="--max-old-space-size=8192"
 # For general: suggest increasing Docker memory limit
```

---

## Category: Native Modules

### node-gyp Build Failed

```yaml
pattern: "gyp ERR!|node-gyp rebuild|Cannot find module.*node-gyp"
category: native_module
confidence: high
fix: |
 # Add to deps/build stage:
 RUN apt-get update && apt-get install -y --no-install-recommends \
   python3 \
   make \
   g++ \
   && rm -rf /var/lib/apt/lists/*
```

### GCC/G++ Missing

```yaml
pattern: "command 'gcc' failed|g\\+\\+: command not found|cc: not found"
category: native_module
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   build-essential \
   && rm -rf /var/lib/apt/lists/*
```

### Python distutils Missing

```yaml
pattern: "No module named 'distutils'|ModuleNotFoundError.*distutils"
category: native_module
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   python3 \
   python3-distutils \
   && rm -rf /var/lib/apt/lists/*
```

---

## Category: Package-Specific

### Sharp / libvips

```yaml
pattern: "sharp|vips|Something went wrong installing the \"sharp\" module"
category: package_specific
confidence: high
fix: |
 # In build stage:
 RUN apt-get update && apt-get install -y --no-install-recommends \
   libvips-dev \
   && rm -rf /var/lib/apt/lists/*
```

### Canvas / Cairo

```yaml
pattern: "canvas|cairo|pango|librsvg"
category: package_specific
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   libcairo2-dev \
   libpango1.0-dev \
   libjpeg-dev \
   libgif-dev \
   librsvg2-dev \
   && rm -rf /var/lib/apt/lists/*
```

### better-sqlite3

```yaml
pattern: "better-sqlite3|Could not locate the bindings file"
category: package_specific
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   python3 \
   make \
   g++ \
   && rm -rf /var/lib/apt/lists/*
```

### bcrypt

```yaml
pattern: "bcrypt.*error|node_modules/bcrypt"
category: package_specific
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   python3 \
   make \
   g++ \
   && rm -rf /var/lib/apt/lists/*
```

---

## Category: Permission

### EACCES Permission Denied

```yaml
pattern: "EACCES.*permission denied|PermissionError.*Errno 13"
category: permission
confidence: medium
fix: |
 # Before USER directive:
 RUN chown -R node:node /app
 # Or adjust the path in question
```

### npm/yarn EACCES

```yaml
pattern: "npm ERR! EACCES|yarn.*EACCES"
category: permission
confidence: high
fix: |
 # Ensure cache directory is writable:
 RUN mkdir -p /home/node/.npm && chown -R node:node /home/node
 USER node
```

---

## Category: Network

### Network Timeout

```yaml
pattern: "ETIMEDOUT|network timeout|request.*timed out"
category: network
confidence: medium
fix: |
 # For npm:
 RUN npm ci --network-timeout 600000
 # For yarn:
 RUN yarn install --network-timeout 600000
```

### Host Resolution Failed

```yaml
pattern: "ENOTFOUND|getaddrinfo.*failed|Could not resolve host"
category: network
confidence: low
fix: |
 # Usually a transient issue, retry may help
 # Or add DNS configuration if persistent
```

---

## Category: Shell Syntax

### Shell Syntax Error

```yaml
pattern: "/bin/sh.*syntax error|unexpected (EOF|token)"
category: shell
confidence: high
fix: |
 # Review RUN commands for:
 # - Unescaped special characters ($, ", ', `)
 # - Unclosed quotes
 # - Complex command substitution
 # Use heredoc for multi-line:
 RUN <<EOF
 command1
 command2
 EOF
```

### Escape Character Issues

```yaml
pattern: "command not found:|unexpected.*\\$"
category: shell
confidence: medium
fix: |
 # Check for proper escaping:
 # $VAR → \$VAR (if literal)
 # Or use single quotes
```

---

## Category: Lockfile

### Lockfile Mismatch

```yaml
pattern: "npm ci.*This command requires an existing lockfile|Your lock file needs to be updated"
category: lockfile
confidence: high
fix: |
 # Change from npm ci to npm install:
 RUN npm install
 # Or for pnpm:
 RUN pnpm install # Instead of --frozen-lockfile
```

### Missing Lockfile

```yaml
pattern: "npm ci.*ENOENT.*package-lock.json|pnpm.*ERR_PNPM_NO_LOCKFILE"
category: lockfile
confidence: high
fix: |
 # Fallback to non-frozen install:
 RUN npm install
 # Or:
 RUN pnpm install
```

### Lockfile Disabled in Config

```yaml
pattern: "lockfile is set to false|Cannot generate.*lockfile.*because lockfile is set to false"
category: lockfile
confidence: high
fix: |
 # Project has lockfile=false in .npmrc
 # Do NOT use --frozen-lockfile
 RUN pnpm install --ignore-scripts
 # Instead of:
 # RUN pnpm install --frozen-lockfile
```

---

## Category: Build Tool Configuration

### ESLint Parse Errors (Config Missing)

```yaml
pattern: "Parsing error: The keyword '(import|export|const|let|class)' is reserved|✖ \\d+ problems \\(\\d+ errors"
category: build_config
confidence: high
cause: |
  Build script includes lint/eslint step, but ESLint config files
  (.eslintrc.js, eslint.config.js, etc.) are excluded from Docker context.
  ESLint falls back to default parser which doesn't support ES6+ syntax.
prevention: |
  Should be caught in analysis phase Step 16 (Build Command Dependency Validation).
  Analysis auto-detects commands with missing config files and generates
  a resolved build command that skips them.
fix: |
  # Identify the prebuild script that runs lint:
  # e.g., "prebuild": "tsx scripts/prebuild.mts && npm run lint"

  # Replace with direct script execution, skipping lint:
  # Before (fails):
  RUN npm run prebuild && npm run build

  # After (works):
  RUN npx tsx scripts/prebuild.mts && npx next build --webpack

  # Add comment explaining the change:
  # NOTE: Running prebuild script directly (skipping lint)
  # Lint requires .eslintrc.js which is excluded in .dockerignore
  # Run lint in CI/CD pipeline instead
```

### TypeScript Config Missing

```yaml
pattern: "Cannot find.*tsconfig.json|TS18003.*tsconfig.json"
category: build_config
confidence: high
fix: |
  # If type-check is in build script but tsconfig.json excluded:
  # Skip type-check command, run essential build steps only

  # Or ensure tsconfig.json is NOT in .dockerignore
```

### Stylelint Config Missing

```yaml
pattern: "Error: No configuration provided for|Could not find.*stylelintrc"
category: build_config
confidence: high
fix: |
  # Skip stylelint command or ensure config file is available
  # Same pattern as ESLint - run essential build steps only
```

---

## Category: Workspace / Monorepo

### Workspace Package Not Found

```yaml
pattern: "ENOENT.*workspace.*package.json|pnpm.*ERR_PNPM_NO_IMPORTER"
category: workspace
confidence: high
fix: |
 # Ensure all workspace package.json files are copied
 COPY packages ./packages
 COPY e2e/package.json ./e2e/
 COPY apps/desktop/src/main/package.json ./apps/desktop/src/main/
```

### Patches Directory Missing

```yaml
pattern: "ENOENT.*patches/|Could not apply patch"
category: workspace
confidence: high
fix: |
 # pnpm patches require patches directory
 COPY patches ./patches
```

### .dockerignore Excludes Required Files

```yaml
pattern: "COPY failed.*not found|failed to calculate checksum.*not found"
category: workspace
confidence: high
fix: |
 # Check .dockerignore - likely excluding required workspace files
 # Use specific exclusions instead of directory-level:
 # Bad: e2e
 # Good: e2e/*
 #    !e2e/package.json
```

---

## Category: Node.js Path / Runtime

### Node Binary Not Found

```yaml
pattern: "spawn /bin/node ENOENT|spawn node ENOENT|/bin/node.*not found"
category: runtime_path
confidence: high
fix: |
 # node:slim images have node at /usr/local/bin/node, not /bin/node
 # Some scripts hardcode /bin/node
 RUN ln -sf /usr/local/bin/node /bin/node
```

### Proxychains Not Found

```yaml
pattern: "/bin/proxychains.*not found|proxychains.*ENOENT"
category: runtime_deps
confidence: high
fix: |
 RUN apt-get update && apt-get install -y --no-install-recommends \
   proxychains4 \
   && rm -rf /var/lib/apt/lists/*
```

---

## Category: Build-Time Environment

### Build-Time Env Required (Next.js SSG)

```yaml
pattern: "`(.+?)` is not set.*build|Failed to collect page data.*(.+?) is not set"
category: build_env
confidence: high
extract: variable name from capture group
fix: |
 # Next.js SSG/ISR requires env vars at build time
 # Add placeholder values for build stage:
 ARG {VAR_NAME}_PLACEHOLDER="build-placeholder-value"
 ENV {VAR_NAME}=${{{VAR_NAME}_PLACEHOLDER}}
```

### Next.js API Route SDK Initialization (Resend, Stripe, etc.)

```yaml
pattern: "Missing API key.*Pass it to the constructor|error:.*API key|Failed to collect page data for /api/"
category: build_env
confidence: high
description: |
 Next.js statically analyzes API routes during build time and attempts to load modules,
 even if the code only runs at runtime. If an SDK is initialized at module top-level
 (e.g., `const resend = new Resend(process.env.KEY)`), the build will fail due to
 missing API key.
fix: |
 # Add placeholder values in build stage (these won't be used at runtime)
 ARG RESEND_API_KEY=re_placeholder_key
 ARG STRIPE_SECRET_KEY=sk_placeholder_key
 ARG NOTION_SECRET=placeholder_notion_secret
 # ... add corresponding variables based on error message

 ENV RESEND_API_KEY=${RESEND_API_KEY}
 ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
 ENV NOTION_SECRET=${NOTION_SECRET}
detection: |
 # Scan app/api/**/route.ts to detect required env vars:
 grep -r "new.*process\.env\." app/api/
 grep -r "process\.env\.\w\+" app/api/ | grep -v "process.env.NODE_ENV"
```

### Database URL Required at Build Time

```yaml
pattern: "DATABASE_URL.*is not set|You are try to use database.*DATABASE_URL"
category: build_env
confidence: high
fix: |
 # Some pages need DB access during build for static generation
 ARG DATABASE_URL_PLACEHOLDER="postgres://placeholder:placeholder@localhost:5432/placeholder"
 ENV DATABASE_URL=${DATABASE_URL_PLACEHOLDER}
 ENV DATABASE_DRIVER=""
```

### Auth Secret Required at Build Time

```yaml
pattern: "AUTH_SECRET.*is not set|KEY_VAULTS_SECRET.*is not set"
category: build_env
confidence: high
fix: |
 ARG KEY_VAULTS_SECRET_PLACEHOLDER="build-placeholder-key-vaults-secret-32chars"
 ENV KEY_VAULTS_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
 ENV AUTH_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
```

---

## Category: Script/Entry Point

### Build Script Missing

```yaml
pattern: "Cannot find module.*prebuild|ERR_MODULE_NOT_FOUND.*scripts/"
category: script_missing
confidence: high
fix: |
 # Build script excluded by .dockerignore
 # Remove from .dockerignore or ensure COPY includes it
 # Check if script path is in .dockerignore exclusions
```

### Server Entry Point Not Found

```yaml
pattern: "Cannot find module.*startServer|Cannot find module.*server.js"
category: script_missing
confidence: high
fix: |
 # Copy server entry point in production stage
 COPY --from=builder /app/scripts/serverLauncher/startServer.js ./startServer.js
 COPY --from=builder /app/scripts/_shared ./scripts/_shared
```

---

## Category: Database Migration

### Relation/Table Does Not Exist (Runtime)

```yaml
pattern: "relation \"(.+?)\" does not exist|Table '(.+?)' doesn't exist|no such table: (.+)"
category: migration_failed
confidence: high
phase: runtime
extract: table name
fix: |
 # CRITICAL: This is a RUNTIME error, indicating migrations never ran
 # This should have been detected in analysis phase!

 # Fix 1: Check if migration system was detected
 # - Re-run analysis phase with migration detection
 # - Verify migration_system.detected == true

 # Fix 2: For Next.js Standalone + ORM
 # Add separate ORM dependency installation:
 RUN mkdir -p /deps && \
   cd /deps && \
   pnpm add pg drizzle-orm

 COPY --from=build /deps/node_modules/drizzle-orm ./node_modules/drizzle-orm
 COPY --from=build /deps/node_modules/pg ./node_modules/pg

 # Fix 3: Verify entrypoint runs migrations
 # docker-entrypoint.sh should have:
 export MIGRATION_DB=1
 # Or explicitly run migration command

 # Fix 4: Fallback - Execute SQL files directly
 # for file in migrations/*.sql; do
 #  psql $DATABASE_URL < $file
 # done
prevention: |
 This error should be caught in ANALYSIS phase by:
 - Detecting migration directory (Step 12)
 - Detecting ORM type
 - Detecting standalone mode
 - Warning if standalone + ORM without separate deps
```

### Drizzle/Prisma Module Not Found (Runtime)

```yaml
pattern: "Cannot find module 'drizzle-orm'|Cannot find module '@prisma/client'|Cannot find module 'typeorm'"
category: migration_deps_missing
confidence: high
phase: runtime
extract: module name
fix: |
 # CRITICAL: ORM not available in standalone mode

 # Next.js standalone mode doesn't include all node_modules
 # Must install ORM dependencies separately

 # In build stage:
 RUN mkdir -p /deps && \
   cd /deps && \
   pnpm add {module_name} pg

 # In production stage:
 COPY --from=build /deps/node_modules/{module_name} ./node_modules/{module_name}
 COPY --from=build /deps/node_modules/pg ./node_modules/pg
prevention: |
 Detect in analysis phase Step 12:
 - migration_system.standalone_with_orm == true
 - migration_system.requires_separate_deps == true
 Then automatically use separate deps pattern
```

### Migration Directory Not Found

```yaml
pattern: "ENOENT.*migrations|Migration directory not found|no such file or directory.*migrations"
category: migration_files_missing
confidence: high
phase: build_or_runtime
fix: |
 # Migration files not copied to image

 # Add to Dockerfile production stage:
 COPY --from=build /app/packages/database/migrations ./packages/database/migrations

 # Or wherever migrations are located:
 COPY --from=build /app/prisma/migrations ./prisma/migrations
 COPY --from=build /app/drizzle ./drizzle
```

### bun/bunx Not Found in Migration Script

```yaml
pattern: "sh: 1: bun: not found|sh: 1: bunx: not found|bun: command not found"
category: migration_runtime
confidence: high
phase: runtime
context: "Often in build-migrate-db or migration scripts"
fix: |
 # Project uses bun for migrations but image only has node

 # Option 1: Don't run migrations at build time
 # Remove build-time migration from Dockerfile
 # Run migrations at container startup instead

 # Option 2: Install bun in image
 RUN curl -fsSL https://bun.sh/install | bash
 ENV PATH="/root/.bun/bin:$PATH"

 # Option 3: Convert migration script to use node
 # Replace 'bun run db:migrate' with 'npx drizzle-kit migrate'
prevention: |
 In analysis phase, detect if migration scripts use bun
 Recommend runtime migration instead of build-time
```

---

## Category: Build Memory Optimization

### Build Script Contains Lint/Type-Check

```yaml
pattern: "Linting|Type-checking|Running type check|eslint|tsc --noEmit"
category: build_optimization
confidence: medium
phase: build
detection: |
 # During analysis, check package.json build script:
 BUILD_SCRIPT=$(jq -r '.scripts.build' package.json)
 if echo "$BUILD_SCRIPT" | grep -qE "lint|type-check"; then
  # Heavy operations detected
 fi
fix: |
 # These are CI tasks, not essential for Docker image
 # Skip them in Docker build to save memory and time

 # Instead of:
 RUN npm run build # Includes lint, type-check, tests

 # Use:
 RUN npx next build # Only build the app

 # Or if custom prebuild needed:
 RUN npx tsx scripts/prebuild.mts && npx next build

 # Comment in Dockerfile:
 # NOTE: Skipping lint/type-check in Docker build
 # These should be run in CI/CD pipeline
prevention: |
 In analysis phase Step 13:
 - Parse build script for heavy operations
 - Recommend optimized build command
 - Set appropriate memory limit
```

### Sitemap Generation Fails or Slows Build

```yaml
pattern: "buildSitemapIndex|sitemap.*failed|Cannot find module.*sitemap"
category: build_optimization
confidence: high
phase: build
fix: |
 # Sitemap generation often not needed in Docker deployment
 # Skip it to reduce build time and complexity

 # Remove from build script or add flag to skip:
 ENV SKIP_SITEMAP=1

 # Or modify package.json script to check env var
prevention: |
 In analysis phase Step 13:
 - Detect sitemap generation in build script
 - Recommend skipping for Docker builds
```

---

## Category: Custom CLI / Monorepo Build

### Wrong Build Command for Custom CLI

```yaml
pattern: "ENOENT.*assets-manifest\\.json|build output not found|Missing static files"
category: custom_cli
confidence: high
phase: runtime
context: "Build succeeded but outputs missing - likely wrong build command"
fix: |
  # CRITICAL: Monorepo may use custom CLI instead of yarn workspace
  # Detection: Check package.json scripts for custom CLI usage

  # Wrong (standard workspace):
  # RUN yarn workspace @scope/web build

  # Correct (use detected CLI syntax from analysis):
  # Turborepo: yarn turbo run build --filter=@scope/web
  # Nx:        yarn nx build web
  # Lerna:     yarn lerna run build --scope=@scope/web
  # Custom:    yarn ${CLI_NAME} build -p @scope/web
prevention: |
  In analysis phase Step 14:
  - Detect custom CLI in package.json scripts
  - Use correct CLI syntax for all build commands
  - Never assume `yarn workspace <pkg> build` works
```

### Git Hash Required

```yaml
pattern: "Failed to open git repo|nodegit.*ENOENT|Repository.*not found|git.*rev-parse.*failed"
category: custom_cli
confidence: high
phase: build
fix: |
  # Build tools may require git hash for versioning
  # In Docker, .git is not available

  # Set environment variable to bypass git requirement
  ENV GITHUB_SHA=docker-build

  # Or use build arg for custom value:
  ARG GIT_COMMIT=docker-build
  ENV GITHUB_SHA=${GIT_COMMIT}
prevention: |
  In analysis phase Step 14:
  - grep for "GITHUB_SHA|Repository|rev-parse" in build tools
  - Automatically add ENV GITHUB_SHA if detected
```

### CLI Init/Config File Missing

```yaml
pattern: "init.*failed|prettier.*not found|Cannot read config file|eslint.*not found|tsconfig.*not found"
category: custom_cli
confidence: medium
phase: build
fix: |
  # Custom CLI may depend on config files excluded by .dockerignore

  # Common required config files (check .dockerignore):
  # - .prettierrc / .prettierignore (code formatting)
  # - .eslintrc.* / oxlint.json (linting)
  # - tsconfig.json (TypeScript)
  # - .editorconfig (editor settings)

  # Fix: Comment out exclusions in .dockerignore
  # Example:
  # .prettierignore  <- Comment this out
  # .prettierrc      <- Comment this out
prevention: |
  In analysis phase Step 14:
  - Detect which config files CLI depends on
  - Ensure they are NOT in .dockerignore
```

### Static Assets Path Mismatch

```yaml
pattern: "ENOENT.*static.*manifest|webAssets.*not found|Cannot find static directory"
category: custom_cli
confidence: high
phase: runtime
fix: |
  # Backend code hardcodes expected static asset paths
  # Must copy frontend outputs to correct locations

  # Example (paths detected from analysis):
  COPY --from=builder /app/${FRONTEND_OUTPUT} ./${BACKEND_EXPECTS}
  # e.g., COPY --from=builder /app/packages/web/dist ./static

  # Detection: Search backend code for static path references
  # grep -rE "projectRoot.*static|assets-manifest|webAssets" packages/backend/ src/server/
prevention: |
  In analysis phase Step 14:
  - Detect backend's expected static paths
  - Map frontend output paths to expected locations
  - Generate correct COPY commands in Dockerfile
```

---

## Category: Rust/Native Module Build

### Rust Toolchain Missing

```yaml
pattern: "cargo.*not found|rustc.*not found|error: no default toolchain configured"
category: native_module
confidence: high
phase: build
fix: |
  # Install Rust toolchain in build stage
  ENV RUSTUP_HOME=/usr/local/rustup \
      CARGO_HOME=/usr/local/cargo \
      PATH=/usr/local/cargo/bin:$PATH

  RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
```

### Wrong Rust Target

```yaml
pattern: "error: linking with.*failed|unknown target triple|can't find crate"
category: native_module
confidence: high
phase: build
fix: |
  # Must use correct target for container architecture
  ARG TARGETARCH

  RUN if [ "$TARGETARCH" = "arm64" ]; then \
          rustup target add aarch64-unknown-linux-gnu && \
          yarn workspace @pkg/native build --target aarch64-unknown-linux-gnu; \
      else \
          rustup target add x86_64-unknown-linux-gnu && \
          yarn workspace @pkg/native build --target x86_64-unknown-linux-gnu; \
      fi
```

### NAPI-RS Build Dependencies Missing

```yaml
pattern: "napi.*build failed|tree-sitter.*error|clang.*not found"
category: native_module
confidence: high
phase: build
fix: |
  # NAPI-RS and tree-sitter require clang
  RUN apt-get update && apt-get install -y --no-install-recommends \
      clang \
      llvm \
      pkg-config \
      libssl-dev \
      && rm -rf /var/lib/apt/lists/*

  # Set clang for compatibility
  ENV CC="clang -D_BSD_SOURCE" \
      TARGET_CC="clang -D_BSD_SOURCE"
```

---

## Unknown Error Fallback

If no pattern matches:

1. Log the full error message
2. Check if error contains a file path → might be COPY issue or .dockerignore issue
3. Check if error contains package name → might be dependency issue
4. Check if error mentions env var → might need build-time placeholder
5. Check if error mentions workspace → might be missing workspace files
6. Return to user with error for manual review

### Debugging Checklist

When build fails with unknown error:

1. **File not found**: Check .dockerignore, ensure file is not excluded
2. **Module not found**: Check if it's a workspace package that wasn't copied
3. **Env var not set**: Add ARG/ENV placeholder for build time
4. **Permission denied**: Check USER directive placement
5. **Command not found**: Check if binary exists in the image (node path, proxychains, etc.)
