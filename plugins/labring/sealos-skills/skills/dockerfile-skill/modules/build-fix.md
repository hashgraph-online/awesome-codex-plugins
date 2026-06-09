# Module: Build Validation & Fix

## Purpose

Execute docker buildx build (targeting linux/amd64), capture errors, and automatically fix Dockerfile issues through iterative refinement.

## Execution Flow

```
┌─────────────────────┐
│ docker buildx build │
└──────────┬──────────┘
      │
  ┌──────┴──────┐
  │       │
 SUCCESS    FAILURE
  │       │
  ▼       ▼
 OUTPUT   ┌─────────────┐
 FINAL   │ Parse Error │
 FILES   └──────┬──────┘
          │
          ▼
       ┌─────────────┐
       │ Match Pattern│
       └──────┬──────┘
          │
          ▼
       ┌─────────────┐
       │ Apply Fix  │
       └──────┬──────┘
          │
          ▼
       ┌─────────────┐
       │ iteration++ │
       │ < max?   │
       └──────┬──────┘
          │
      ┌───────┴───────┐
      │        │
     YES       NO
      │        │
      ▼        ▼
    RETRY     OUTPUT BEST
            + WARN USER
```

## Build Command

```bash
docker buildx build --platform linux/amd64 --load -t test-build:latest . 2>&1
```

**Important**: Capture both stdout and stderr for error analysis.

## Error Pattern Matching

See [knowledge/error-patterns.md](../knowledge/error-patterns.md) for the full pattern database.

### Priority 1: File/Directory Not Found

**Pattern**:
```
ENOENT: no such file or directory, open '...'
Error: Cannot find module '...'
FileNotFoundError: [Errno 2] No such file or directory: '...'
```

**Fix Actions**:
1. Extract the missing path from error message
2. If it's a config file (*.json, *.yaml, *.toml):
  ```dockerfile
  RUN mkdir -p /app/data && echo '{}' > /app/data/config.json
  ```
3. If it's a directory:
  ```dockerfile
  RUN mkdir -p /app/missing-dir
  ```

### Priority 2: Environment Variable Missing

**Pattern**:
```
`XXX` is not set
Error: XXX environment variable is required
KeyError: 'XXX'
```

**Fix Actions**:
1. Extract variable name
2. Add to build stage with placeholder:
  ```dockerfile
  ARG XXX=placeholder_for_build
  ENV XXX=$XXX
  ```

### Priority 3: Out of Memory

**Pattern**:
```
Killed
Exit code: 137
JavaScript heap out of memory
FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed
```

**Fix Actions**:
1. Add memory options:
  ```dockerfile
  ENV NODE_OPTIONS="--max-old-space-size=4096"
  ```
2. If still failing, increase to 8192

### Priority 4: Native Module Build Failed

**Pattern**:
```
gyp ERR!
node-gyp rebuild
error: command 'gcc' failed
ModuleNotFoundError: No module named 'distutils'
```

**Fix Actions**:
1. Add build tools to deps stage:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*
  ```

### Priority 5: Package-Specific Errors

**Pattern**: `sharp`, `vips`, `canvas` related errors

**Fix Actions**:
```dockerfile
# For sharp
RUN apt-get update && apt-get install -y --no-install-recommends \
  libvips-dev \
  && rm -rf /var/lib/apt/lists/*

# For canvas
RUN apt-get update && apt-get install -y --no-install-recommends \
  libcairo2-dev \
  libpango1.0-dev \
  libjpeg-dev \
  libgif-dev \
  librsvg2-dev \
  && rm -rf /var/lib/apt/lists/*
```

### Priority 6: Permission Denied

**Pattern**:
```
EACCES: permission denied
PermissionError: [Errno 13]
```

**Fix Actions**:
1. Check if file operations happen before USER switch
2. Add ownership change:
  ```dockerfile
  RUN chown -R node:node /app
  USER node
  ```

### Priority 7: Network/Download Errors

**Pattern**:
```
ETIMEDOUT
ECONNREFUSED
npm ERR! network
Could not resolve host
```

**Fix Actions**:
1. Add retry logic or timeout increase:
  ```dockerfile
  RUN npm ci --network-timeout 600000
  ```
2. Consider adding mirror/proxy if consistently failing

### Priority 8: Shell Syntax Error

**Pattern**:
```
/bin/sh: syntax error
unexpected EOF
```

**Fix Actions**:
1. Check for unescaped special characters
2. Avoid complex shell substitutions in RUN
3. Use heredoc syntax for multi-line scripts:
  ```dockerfile
  RUN <<EOF
  set -e
  echo "line 1"
  echo "line 2"
  EOF
  ```

## Iteration Control

```python
max_iterations = {
  "L1": 1,
  "L2": 3,
  "L3": 5
}

for i in range(max_iterations[complexity]):
  result = docker_build()
  if result.success:
    return SUCCESS

  errors = parse_errors(result.stderr)
  if not errors:
    # Unknown error, cannot auto-fix
    return FAIL_WITH_LOG

  for error in errors:
    fix = match_pattern(error)
    if fix:
      apply_fix(dockerfile, fix)
      break # One fix per iteration
  else:
    # No matching pattern found
    return FAIL_WITH_LOG

return PARTIAL_SUCCESS # Max iterations reached
```

## Post-Build Validation

After successful build, perform comprehensive validation:

### Step 1: Container Startup Validation

```bash
# Start container with docker-compose
docker-compose up -d

# Wait for startup (adjust based on app)
sleep 30

# Check container status
docker-compose ps
```

### Step 2: Database Migration Validation

If `migration_system.detected == true` from analysis:

```bash
# Verify database tables exist
docker-compose exec postgres psql -U <user> -d <db> -c "\dt"

# Expected output: List of tables (users, sessions, messages, etc.)
# If "Did not find any relations" → MIGRATIONS FAILED

# Check migration status table
docker-compose exec postgres psql -U <user> -d <db> -c "SELECT * FROM drizzle_migrations LIMIT 5;"

# Verify migration count
MIGRATION_COUNT=$(docker-compose exec postgres psql -U <user> -d <db> -t -c "SELECT COUNT(*) FROM drizzle_migrations;")
EXPECTED_COUNT=76 # From analysis phase

if [ "$MIGRATION_COUNT" -ne "$EXPECTED_COUNT" ]; then
 echo "CRITICAL: Only $MIGRATION_COUNT of $EXPECTED_COUNT migrations ran"
fi
```

### Step 3: Application Health Validation

```bash
# Test HTTP response
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3210)

# Acceptable codes: 200 (OK), 302 (Redirect to login), 401 (Auth required)
# Unacceptable: 500 (Internal error), 502 (Bad gateway)

if [ "$HTTP_CODE" = "500" ]; then
 echo "CRITICAL: Application returning 500 error"
 docker-compose logs app
fi

# Test specific API endpoint
curl -v http://localhost:3210/api/health
```

### Step 4: Log Analysis

```bash
# Check for common error patterns
docker-compose logs app | grep -E "error|Error|ERROR|failed|Failed|FAILED" | tail -20

# Check for migration-related errors
docker-compose logs app | grep -E "migration|migrate|schema|relation.*does not exist"

# Check for database connection
docker-compose logs app | grep -E "database|postgres|connection"
```

### Validation Checklist

Before declaring success:

**Build Phase**:
- [ ] Image builds successfully (`docker buildx build` exits 0)
- [ ] Image size reasonable (< 2GB for most apps)

**Startup Phase**:
- [ ] Container starts without crash
- [ ] All ports accessible
- [ ] Database connection successful

**Migration Phase** - CRITICAL:
- [ ] Database tables exist (verify with `\dt`)
- [ ] Migration count matches expected (e.g., 76/76)
- [ ] Migration status table populated
- [ ] No "relation does not exist" errors

**Runtime Phase** :
- [ ] App returns 200/302/401, not 500
- [ ] Health check endpoint works
- [ ] Core API endpoint accessible
- [ ] No runtime errors in logs

**Failure Conditions** → Don't declare success if:
- Database tables missing
- App returns 500 errors
- Logs show "relation does not exist"
- Migration count mismatch
- Container crashes on startup

## Output on Success

```
## Build Results

Build successful!
Container started successfully!
Database migrations completed (76/76)
Application health check passed

### Generated Files
- Dockerfile
- .dockerignore
- docker-compose.yml
- .env.docker.local (auto-generated with test secrets)
- docker-entrypoint.sh
- DOCKER.md (deployment guide)

### Validation Results
- Image size: ~1.4GB
- Container status: UP (healthy)
- Database tables: 23 tables created
- HTTP response: 302 (redirecting to /signin)
- Migrations: 76/76 completed

### Quick Start
cd /path/to/project
docker-compose up -d

# Access application
open http://localhost:3210

### Build Command
docker buildx build --platform linux/amd64 --load -t your-app:latest .

### Run Command
docker run -d -p 3000:3000 your-app:latest

### Next Steps
1. Application is ready to use
2. Set real API keys in .env.docker.local for production
3. Review DOCKER.md for production deployment guide
```

## Output on Failure

```
## Build Results

Build completed with issues after 3 iterations.

### Last Error
[error message]

### Attempted Fixes
1. Added missing directory /app/data
2. Injected environment variable XXX
3. Added memory limit increase

### Manual Steps Required
- Review the error above
- The generated Dockerfile may need manual adjustment for: [specific issue]

### Partial Output
The best version of Dockerfile is saved. It may work with additional configuration.
```

## Artifact Output

After completing all build iterations AND all runtime validation steps (Phase 3 + Phase 4),
write two artifact files to the `docker-build/` directory.

### Phase 3: Build Result

**File**: `docker-build/build-result.json`

**Instructions**:
1. Write this file after the build loop completes (whether success or failure)
2. Create the `docker-build/` directory if it does not exist: `Bash: mkdir -p docker-build`
3. `outcome`: `"success"` | `"partial_success"` (max iterations reached but last Dockerfile saved) | `"failed"`
4. `iterations`: one entry per docker build execution, with `status`, `error_category`,
   `error_excerpt` (first 200 chars of error), `fix_applied`, `duration_seconds`
5. `fixes_applied`: only include iterations where a fix was applied
6. `errors_not_matched`: include the raw error text for any error where no pattern from
   `knowledge/error-patterns.md` matched — these are candidates for new patterns
7. `build.image_size_mb`: capture from `docker images` output after successful build

**Schema**:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 timestamp>",
  "phase": "build",
  "outcome": "success",
  "iterations": [
    {
      "iteration": 1,
      "status": "failed",
      "error_category": "env_var_missing",
      "error_excerpt": "KEY_VAULTS_SECRET is not set",
      "fix_applied": "Added ARG KEY_VAULTS_SECRET=build-placeholder with ENV",
      "duration_seconds": 47
    },
    {
      "iteration": 2,
      "status": "success",
      "error_category": null,
      "error_excerpt": null,
      "fix_applied": null,
      "duration_seconds": 184
    }
  ],
  "total_iterations": 2,
  "max_iterations_allowed": 5,
  "complexity_level": "L3",
  "build": {
    "command": "docker buildx build --platform linux/amd64 --load -t test-build:latest .",
    "image_name": "test-build:latest",
    "image_size_mb": 1420,
    "image_size_human": "1.42GB",
    "exit_code": 0
  },
  "fixes_applied": [
    {
      "iteration": 1,
      "pattern_matched": "env_var_missing",
      "error": "KEY_VAULTS_SECRET is not set",
      "fix": "Added ARG/ENV placeholder for KEY_VAULTS_SECRET in build stage"
    }
  ],
  "errors_not_matched": []
}
```

### Phase 4: Validation Result

**File**: `docker-build/validation-result.json`

**Instructions**:
1. Write this file after ALL validation steps (Steps 1–4 of Post-Build Validation) complete
2. If build failed entirely, still write this file with `outcome: "skipped"` and all checklist items false
3. `migration.applicable`: set to `false` if `analysis.migration_system.detected == false`
4. `http_health.acceptable`: true if HTTP code is 200, 302, or 401; false if 500, 502, 503
5. `checklist`: each boolean maps directly to a checkbox in the Validation Checklist above
6. `summary`: one sentence describing the overall outcome

**Schema**:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 timestamp>",
  "phase": "validation",
  "outcome": "success",
  "container_startup": {
    "status": "healthy",
    "compose_command": "docker-compose up -d",
    "wait_seconds": 30,
    "all_containers_up": true,
    "crash_detected": false
  },
  "migration": {
    "applicable": true,
    "orm": "drizzle",
    "expected_count": 76,
    "actual_count": 76,
    "tables_exist": true,
    "tables_verified": ["users", "sessions", "messages", "agents"],
    "status": "success",
    "verification_command": "docker-compose exec postgres psql -U app -d app -c \"\\dt\""
  },
  "http_health": {
    "url": "http://localhost:3210",
    "http_code": 302,
    "acceptable": true,
    "notes": "302 redirect to /signin — expected for unauthenticated request"
  },
  "log_analysis": {
    "error_count": 0,
    "migration_errors": [],
    "critical_errors": [],
    "warnings": []
  },
  "checklist": {
    "image_built": true,
    "container_started": true,
    "database_connected": true,
    "migrations_executed": true,
    "tables_created": true,
    "http_valid_response": true,
    "no_runtime_errors": true,
    "healthcheck_passed": true
  },
  "summary": "All validation checks passed. App is fully operational."
}
```

If the build failed entirely (Phase 3 outcome = `"failed"`), write this file with:
```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 timestamp>",
  "phase": "validation",
  "outcome": "skipped",
  "reason": "Build failed — validation cannot proceed without a working image",
  "checklist": {
    "image_built": false,
    "container_started": false,
    "database_connected": false,
    "migrations_executed": false,
    "tables_created": false,
    "http_valid_response": false,
    "no_runtime_errors": false,
    "healthcheck_passed": false
  },
  "summary": "Validation skipped because the Docker image failed to build."
}
```
