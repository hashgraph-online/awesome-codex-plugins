# Monorepo Custom CLI Patterns

## Overview

Many large monorepo projects have custom CLI tools for building instead of standard `yarn workspace` commands.
Failing to detect and use these CLIs is a common cause of build failures.

**Key Principle**: NEVER assume `yarn workspace <pkg> build` works. Always detect the actual build system.

## Detection Checklist

### Step 1: Detect Known Monorepo Tools

```bash
# Check for well-known monorepo CLIs
KNOWN_CLIS=(
  "turbo"     # Turborepo
  "nx"        # Nx
  "lerna"     # Lerna
  "rush"      # Rush
)

for cli in "${KNOWN_CLIS[@]}"; do
  if [ -f "node_modules/.bin/$cli" ] || grep -q "\"$cli\"" package.json; then
    echo "Detected: $cli"
    CLI_TYPE="standard"
    CLI_NAME="$cli"
    break
  fi
done

# Check for turbo.json (Turborepo indicator)
[ -f "turbo.json" ] && CLI_NAME="turbo"

# Check for nx.json (Nx indicator)
[ -f "nx.json" ] && CLI_NAME="nx"

# Check for lerna.json (Lerna indicator)
[ -f "lerna.json" ] && CLI_NAME="lerna"
```

### Step 2: Detect Custom CLI

```bash
# If no standard CLI found, check for custom CLI in package.json scripts
# Look for scripts that define a single-word command
CUSTOM_CLI=$(jq -r '
  .scripts | to_entries[] |
  select(.key | test("^[a-z]+$")) |
  select(.value | test("^[a-z]+ |^r ")) |
  .key
' package.json 2>/dev/null | head -1)

# Check tools/ directory for CLI definitions
for dir in "tools/cli" "tools/scripts" "scripts/cli"; do
  if [ -d "$dir" ]; then
    CLI_ENTRY=$(find "$dir" -name "*.js" -o -name "*.ts" | head -1)
    [ -n "$CLI_ENTRY" ] && CLI_TYPE="custom"
  fi
done
```

### Step 3: Determine Build Syntax

Each CLI has different syntax. Detection must determine the correct pattern:

| CLI | Build Syntax | Filter Flag |
|-----|--------------|-------------|
| Turborepo | `yarn turbo run build --filter=<pkg>` | `--filter=` |
| Nx | `yarn nx build <project>` | positional |
| Lerna | `yarn lerna run build --scope=<pkg>` | `--scope=` |
| Rush | `rush build -t <pkg>` | `-t` |
| Custom | varies | detect from source |

```bash
# Determine syntax based on CLI type
case "$CLI_NAME" in
  turbo) BUILD_SYNTAX="yarn turbo run build --filter=\${PACKAGE}" ;;
  nx)    BUILD_SYNTAX="yarn nx build \${PROJECT}" ;;
  lerna) BUILD_SYNTAX="yarn lerna run build --scope=\${PACKAGE}" ;;
  rush)  BUILD_SYNTAX="rush build -t \${PACKAGE}" ;;
  *)
    # Custom CLI - analyze source for flag patterns
    if grep -rqE "\-p.*package|--package" tools/ 2>/dev/null; then
      BUILD_SYNTAX="yarn $CLI_NAME build -p \${PACKAGE}"
    elif grep -rqE "\-\-filter" tools/ 2>/dev/null; then
      BUILD_SYNTAX="yarn $CLI_NAME build --filter=\${PACKAGE}"
    else
      BUILD_SYNTAX="yarn $CLI_NAME build \${PACKAGE}"
    fi
    ;;
esac
```

## Common CLI Patterns

### Pattern 1: Turborepo

**Detection:**
```bash
[ -f "turbo.json" ] && echo "Turborepo detected"
```

**Correct Build:**
```dockerfile
RUN yarn turbo run build --filter=@scope/web
RUN yarn turbo run build --filter=@scope/server
```

### Pattern 2: Nx

**Detection:**
```bash
[ -f "nx.json" ] && echo "Nx detected"
```

**Correct Build:**
```dockerfile
RUN yarn nx build web
RUN yarn nx build server
```

### Pattern 3: Lerna

**Detection:**
```bash
[ -f "lerna.json" ] && echo "Lerna detected"
```

**Correct Build:**
```dockerfile
RUN yarn lerna run build --scope=@scope/web
```

### Pattern 4: Custom CLI

**Detection:**
```bash
# Custom CLI often defined in tools/ or has special script in package.json
if [ -d "tools/cli" ]; then
  echo "Custom CLI detected"
fi
```

**Analysis Required:**
1. Find CLI entry point
2. Analyze source for argument parsing
3. Determine correct syntax

**Example Build:**
```dockerfile
# Syntax varies by project - must be detected
RUN yarn ${CLI_NAME} build -p @scope/web
```

## Git Hash Dependency

Many build tools require git commit hash for versioning.

**Detection:**
```bash
# Common patterns for git hash usage
if grep -rqE "GITHUB_SHA|GIT_COMMIT|GIT_SHA|COMMIT_HASH|rev-parse|nodegit|simple-git" tools/ src/ scripts/ 2>/dev/null; then
  echo "Git hash required"
  # Find the specific env var name
  GIT_ENV=$(grep -rohE "(GITHUB_SHA|GIT_COMMIT|GIT_SHA|COMMIT_HASH)" tools/ src/ scripts/ 2>/dev/null | sort -u | head -1)
fi
```

**Solution:**
```dockerfile
# Set environment variable to bypass git requirement
# Use the detected env var name, or default to GITHUB_SHA
ENV ${GIT_ENV:-GITHUB_SHA}=docker-build
```

## Configuration File Dependencies

Custom CLIs often depend on configuration files.

**Common Required Files:**
- `.prettierrc` / `.prettierignore` - Code formatting
- `.eslintrc.*` / `oxlint.json` - Linting
- `tsconfig.json` - TypeScript config
- `.editorconfig` - Editor settings

**Detection:**
```bash
CONFIG_DEPS=()

# Check what the CLI/build system references
for config in ".prettierrc" ".prettierignore" ".eslintrc.js" "oxlint.json" "tsconfig.json"; do
  if [ -f "$config" ] && grep -rqE "${config#.}" tools/ scripts/ 2>/dev/null; then
    CONFIG_DEPS+=("$config")
  fi
done
```

**Fix .dockerignore:**
```
# Comment out any config files that CLI needs:
# .prettierrc
# .prettierignore
# tsconfig.json
```

## postinstall Script Handling

Many monorepos run initialization in postinstall.

**Detection:**
```bash
POSTINSTALL=$(jq -r '.scripts.postinstall // ""' package.json)
if [ -n "$POSTINSTALL" ]; then
  echo "postinstall script: $POSTINSTALL"
fi
```

**Options:**

1. **Keep postinstall** (recommended):
```dockerfile
RUN yarn install --immutable --inline-builds
# postinstall runs automatically
```

2. **Skip postinstall, run manually**:
```dockerfile
RUN yarn install --immutable --ignore-scripts
RUN yarn ${CLI_NAME} init  # or equivalent
```

## Native Module (Rust/NAPI-RS) Builds

**Detection:**
```bash
# Check for Rust project
HAS_RUST=false
if [ -f "Cargo.toml" ] || ls packages/*/Cargo.toml 2>/dev/null; then
  HAS_RUST=true
fi

# Check for NAPI-RS
if grep -qE "@napi-rs|napi-derive" package.json Cargo.toml 2>/dev/null; then
  HAS_NAPI_RS=true
fi
```

**Build Pattern:**
```dockerfile
# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/usr/local/cargo/bin:$PATH"

# Install NAPI-RS build dependencies
RUN apt-get update && apt-get install -y clang llvm

# Build with correct target (auto-detect architecture)
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
      rustup target add aarch64-unknown-linux-gnu && \
      yarn workspace @scope/native build --target aarch64-unknown-linux-gnu; \
    else \
      rustup target add x86_64-unknown-linux-gnu && \
      yarn workspace @scope/native build --target x86_64-unknown-linux-gnu; \
    fi
```

## Static Assets Path Detection

Backend servers often expect frontend builds at specific paths.

**Detection:**
```bash
# Search for static path references in backend code
STATIC_PATH=""
if grep -rqE "static|public" packages/backend/ src/server/ 2>/dev/null; then
  STATIC_PATH=$(grep -rohE "(static|public)" packages/backend/ src/server/ 2>/dev/null | head -1)
fi

# Find frontend output directories
FRONTEND_OUTPUTS=$(find packages apps -name "dist" -type d 2>/dev/null)
```

**Solution:**
```dockerfile
# Copy frontend builds to where backend expects
# Paths detected from analysis
COPY --from=builder /app/${FRONTEND_OUTPUT} ./${BACKEND_EXPECTS}
```

## Analysis Output Format

When analyzing a monorepo, produce this structured output:

```yaml
custom_cli:
  detected: true | false
  name: "${CLI_NAME}"                # Detected CLI name
  type: "standard | custom"          # Known tool or custom
  entry: "${CLI_ENTRY}"              # Path to CLI (if custom)

  build_syntax: "${BUILD_SYNTAX}"    # Complete build command template
  packages_to_build:
    - name: "@scope/web"
      command: "yarn ${CLI_NAME} build ..."
      output: "packages/web/dist"

  dependencies:
    git_hash:
      required: true | false
      env_var: "${GIT_ENV}"          # e.g., GITHUB_SHA
      fallback: "docker-build"

    config_files: []                 # Files NOT to exclude in .dockerignore

    postinstall:
      script: "${POSTINSTALL}"
      recommendation: "keep | skip_and_run_manually"

  native_modules:
    rust: true | false
    packages: []
    multi_arch: true | false

  static_assets:
    backend_expects: "${STATIC_PATH}"
    frontend_outputs: []
```

## Troubleshooting

### "command not found: ${CLI_NAME}"

**Cause:** CLI not installed or PATH not set.

**Fix:**
```dockerfile
# Ensure dependencies installed first
RUN yarn install --immutable
# CLI available via yarn
RUN yarn ${CLI_NAME} build ...
```

### "Unknown Syntax Error" / "Invalid argument"

**Cause:** Wrong CLI syntax.

**Fix:** Verify syntax by checking CLI help or source code.

### "Failed to open git repo"

**Cause:** Build requires git hash but .git not in Docker context.

**Fix:**
```dockerfile
ENV ${GIT_ENV}=docker-build
```

### "assets-manifest.json not found" or similar static file errors

**Cause:** Frontend output not copied to correct location.

**Fix:**
1. Verify frontend builds successfully
2. Check where backend expects static files
3. Add correct COPY command in Dockerfile
