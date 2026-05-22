# Module: Cloud-Native Readiness Assessment

## Purpose

Evaluate a project against 6 cloud-native dimensions to produce a readiness score (0-12).

**Data source**: Patterns derived from 164 production-deployed Sealos Cloud templates.
See [knowledge/sealos-patterns.md](../knowledge/sealos-patterns.md) for the full dataset.

## Pre-Assessment: Fast-Track Rules

Before running the full 6-dimension assessment, check these fast-track rules derived
from 164 real-world containerized projects. If a fast-track matches, you can assign a
preliminary score and still verify with the full assessment.

### Instant Pass (Preliminary Score >= 10)
Apply if ANY of these match:
- **Go/Rust single binary** with HTTP listener (e.g., `net/http`, `actix-web`, `axum`)
- **Next.js** app with `output: "standalone"` in next.config
- **Python FastAPI/Flask/Django** with external PostgreSQL/MySQL
- **Project already has Dockerfile + docker-compose** with health checks
- **Published to container registry** (ghcr.io, Docker Hub, ECR)

### Likely Pass (Preliminary Score >= 7)
- TypeScript monorepo with `apps/` structure (Turborepo, pnpm workspaces, nx)
- Java Spring Boot application with external database
- PHP app with composer.json using official PHP-FPM base image pattern
- Any web service using PostgreSQL + Redis with env var config
- Python app with requirements.txt and Uvicorn/Gunicorn entry point

### Needs Full Assessment
- Projects with SQLite as primary database
- Desktop/Electron apps that also have a web component
- Projects with heavy local file processing or GPU requirements
- CLI tools that may or may not expose HTTP

### Likely Fail (Preliminary Score 0-3)
- Pure CLI tools with no HTTP server
- Desktop-only GUI applications (Electron without web API)
- Embedded systems or hardware-specific code
- Projects requiring persistent local state with no external DB

## Execution Steps

### Step 1: Identify Project Type

First, determine the basic project characteristics:

```
Check for:
- package.json → Node.js ecosystem
- requirements.txt / pyproject.toml → Python
- go.mod → Go
- pom.xml / build.gradle → Java
- Cargo.toml → Rust
- composer.json → PHP
- Gemfile → Ruby
```

For monorepos, identify all services/apps:
```
Check for:
- pnpm-workspace.yaml / turbo.json / nx.json → Monorepo
- apps/ or services/ directory → Multiple deployable units
- Each deployable unit should be assessed independently
```

**Output**:
```yaml
project:
  name: "{from package.json or directory name}"
  type: "monorepo | single-app"
  language: "typescript | python | go | java | rust | php | ruby"
  framework: "{detected framework}"
  deployable_units:
    - name: "api"
      path: "apps/api"
      type: "REST API"
    - name: "cms"
      path: "apps/cms"
      type: "Web application"
```

### Step 2: Assess Statelessness (0-2 points)

**What to check**:

```bash
# Check for in-memory session stores
grep -rE "express-session|cookie-session|session\(\)|MemoryStore" --include="*.ts" --include="*.js"

# Check for local file system writes (non-temp)
grep -rE "fs\.(write|append|mkdir)|writeFile|createWriteStream" --include="*.ts" --include="*.js" | grep -v "node_modules" | grep -v "/tmp"

# Check for in-memory caches without external backing
grep -rE "new Map\(\)|global\.\w+Cache|let cache =|const cache =" --include="*.ts" --include="*.js"

# Check for SQLite or local database files
grep -rE "sqlite|better-sqlite3|\.db\"|\.sqlite" --include="*.ts" --include="*.js"
find . -name "*.db" -o -name "*.sqlite" | head -5

# Check for local upload directories (non-cloud storage)
grep -rE "multer\.diskStorage|upload.*dest.*['\"]\./" --include="*.ts" --include="*.js"
```

**Scoring**:
- **2**: Fully stateless. State externalized to DB/Redis/S3. No local file dependency.
- **1**: Mostly stateless. Minor local state (temp files, build cache) but core state is external.
- **0**: Stateful. In-memory sessions, local file storage for user data, SQLite.

**Positive indicators** (state externalized):
- Uses PostgreSQL/MySQL/MongoDB for data → external DB
- Uses Redis/Memcached for sessions/cache → external cache
- Uses S3/R2/GCS for file storage → external storage
- Uses JWT or external auth (Better Auth, NextAuth) → stateless auth

**Negative indicators** (local state):
- `MemoryStore` for sessions
- `fs.writeFileSync` for user uploads
- SQLite as primary database
- In-process cron jobs with state

### Step 3: Assess Config Externalization (0-2 points)

**What to check**:

```bash
# Check for environment variable usage
grep -rE "process\.env\.|os\.environ|os\.Getenv|System\.getenv" --include="*.ts" --include="*.js" --include="*.py" --include="*.go" | wc -l

# Check for .env file patterns
ls -la .env* 2>/dev/null
ls -la */.env* 2>/dev/null

# Check for hardcoded connection strings
grep -rE "(localhost|127\.0\.0\.1):\d{4}" --include="*.ts" --include="*.js" | grep -v "node_modules" | grep -v ".env"

# Check for hardcoded secrets
grep -rE "password\s*[:=]\s*['\"][^'\"]+['\"]|secret\s*[:=]\s*['\"][^'\"]+['\"]" --include="*.ts" --include="*.js" | grep -v "node_modules" | grep -v ".env" | grep -v "placeholder"

# Check for config/env validation (good practice)
grep -rE "createEnv|envalid|env-var|joi.*env|zod.*env" --include="*.ts" --include="*.js"
```

**Scoring**:
- **2**: All config via env vars. `.env.example` exists. No hardcoded secrets. Config validation present.
- **1**: Mostly env var driven. Some hardcoded defaults but overridable. `.env.example` may be incomplete.
- **0**: Hardcoded configs, connection strings, or secrets in source code. No env var pattern.

**Positive indicators**:
- `.env.example` with documented variables
- `@t3-oss/env-nextjs` or `envalid` for validation
- All connection strings from env vars
- Docker-friendly config patterns (12-factor)

**Negative indicators**:
- Hardcoded `localhost:5432` without env var fallback
- Secrets committed in config files
- Config files that can't be overridden at runtime

### Step 4: Assess Horizontal Scalability (0-2 points)

**What to check**:

```bash
# Check for WebSocket with sticky sessions concern
grep -rE "WebSocket|socket\.io|ws\(" --include="*.ts" --include="*.js"

# Check for distributed-friendly patterns
grep -rE "Redis|BullMQ|bull|@upstash|amqp|kafka" --include="*.ts" --include="*.js"

# Check for file-based locks
grep -rE "lockfile|\.lock\"|flock|advisory.*lock" --include="*.ts" --include="*.js"

# Check for singleton patterns that break with multiple instances
grep -rE "global\.\w+\s*=|globalThis\.\w+\s*=" --include="*.ts" --include="*.js" | grep -v "prisma"

# Check for cron/scheduler (single-instance concern)
grep -rE "node-cron|cron\.schedule|setInterval.*\d{4,}" --include="*.ts" --include="*.js"

# Check for leader election or distributed lock patterns (good sign)
grep -rE "redlock|@upstash/lock|leader.*election" --include="*.ts" --include="*.js"
```

**Scoring**:
- **2**: Fully horizontally scalable. Stateless requests, external queue for background jobs, no file locks.
- **1**: Mostly scalable. May need sticky sessions for WebSocket, or has cron jobs that should be single-instance.
- **0**: Single-instance only. File-based locks, in-process schedulers with side effects, shared mutable state.

**Positive indicators**:
- REST/GraphQL API (naturally stateless)
- Redis-backed queues (BullMQ, etc.)
- Database-level locking (not file-level)
- No in-process cron with side effects

**Negative indicators**:
- `setInterval` for scheduled tasks without distributed lock
- File-based locking mechanisms
- In-memory pub/sub without Redis adapter

### Step 5: Assess Startup/Shutdown (0-2 points)

**What to check**:

```bash
# Check for graceful shutdown handling
grep -rE "SIGTERM|SIGINT|process\.on.*signal|graceful.*shutdown|beforeExit" --include="*.ts" --include="*.js"

# Check for health check endpoints
grep -rE "health|healthz|readyz|livez|ready|alive" --include="*.ts" --include="*.js" --include="*.py"

# Check for long initialization (e.g., loading large ML models)
grep -rE "loadModel|warmup|preload|initialize.*cache" --include="*.ts" --include="*.js"

# Check framework - some handle graceful shutdown automatically
grep -rE "hono|express|fastify|nestjs|next" package.json 2>/dev/null

# Check for connection draining
grep -rE "server\.close|drain|closeAllConnections" --include="*.ts" --include="*.js"
```

**Scoring**:
- **2**: Handles SIGTERM gracefully. Has health check endpoints. Fast startup (< 10s).
- **1**: Framework handles basic shutdown. No explicit health check but responds to HTTP quickly. Moderate startup.
- **0**: No signal handling. Long startup (loads large resources). Abrupt termination risks.

**Positive indicators**:
- Explicit `SIGTERM` handler
- `/health` or `/healthz` endpoint
- Frameworks like Hono/Fastify (lightweight, fast startup)
- Connection pooling with proper cleanup

**Negative indicators**:
- Loading large files at startup without lazy loading
- No graceful shutdown in custom server
- Long database migration at startup

### Step 6: Assess Observability (0-2 points)

**What to check**:

```bash
# Check for structured logging
grep -rE "pino|winston|bunyan|structured.*log|JSON\.stringify.*log" --include="*.ts" --include="*.js"

# Check for console.log (not ideal but functional)
grep -rE "console\.(log|error|warn)" --include="*.ts" --include="*.js" | wc -l

# Check for metrics/monitoring
grep -rE "prometheus|prom-client|datadog|newrelic|opentelemetry|@sentry" --include="*.ts" --include="*.js"

# Check for request tracing
grep -rE "trace-id|x-request-id|correlation-id|opentelemetry" --include="*.ts" --include="*.js"

# Check for error tracking
grep -rE "sentry|bugsnag|rollbar|errorHandler" --include="*.ts" --include="*.js"
```

**Scoring**:
- **2**: Structured logging (JSON). Metrics endpoint. Error tracking. Request tracing.
- **1**: Has logging (even console.log to stdout). Some error handling. No metrics.
- **0**: No logging. Silent failures. No observability infrastructure.

**Positive indicators**:
- Structured JSON logging → works with log aggregators
- Sentry/error tracking → crash reporting
- Prometheus metrics → monitoring
- Logs to stdout/stderr → container-friendly

**Negative indicators**:
- Logging to local files only (not stdout)
- No error handling middleware
- Silent `catch {}` blocks

### Step 7: Assess Service Boundaries (0-2 points)

**What to check**:

```bash
# Check if it's a monorepo with clear service separation
ls apps/ services/ 2>/dev/null

# Check for clear API boundaries
grep -rE "app\.(get|post|put|delete|use)" --include="*.ts" --include="*.js" | head -5
grep -rE "router\.(get|post|put|delete)" --include="*.ts" --include="*.js" | head -5

# Check for tightly coupled components
# (e.g., frontend and backend in same process)
grep -rE "next.*custom.*server|express.*next\(" --include="*.ts" --include="*.js"

# Check for shared database access pattern
grep -rE "prisma|drizzle|typeorm|sequelize" --include="*.ts" --include="*.js" |
  cut -d: -f1 | sort -u

# For monorepos: check if services can deploy independently
ls apps/*/package.json 2>/dev/null
```

**Scoring**:
- **2**: Clear service boundaries. Each service has its own entry point, dependencies, and can deploy independently.
- **1**: Logical separation exists (routes, modules) but deployed as single unit. Monorepo with shared DB is fine.
- **0**: Tightly coupled monolith. No clear service boundaries. Everything in one process with cross-cutting concerns.

**Positive indicators**:
- Monorepo with `apps/` directory and independent package.json per app
- API and frontend are separate deployable units
- Clear route/controller structure
- REST/GraphQL API with well-defined endpoints

**Negative indicators**:
- Single `index.js` with everything
- Frontend rendering and API in same server without separation
- Circular dependencies between modules

### Step 8: Calculate Total Score and Produce Report

Sum all dimension scores (0-12) and determine rating:

```
12-10: ★★★★★ Excellent — Fully cloud-native ready
 9-7:  ★★★★  Good     — Ready with minor adjustments
 6-4:  ★★★   Fair     — Needs some refactoring
 3-0:  ★★    Poor     — Significant rework needed
```

**For monorepos**: Assess each deployable unit separately, then provide an overall score.

### Output Format

```yaml
assessment:
  project_name: "{name}"
  project_type: "monorepo | single-app"
  overall_score: {0-12}
  rating: "Excellent | Good | Fair | Poor"
  verdict: "Ready | Ready with caveats | Needs work | Not recommended"

  dimensions:
    statelessness:
      score: {0-2}
      findings:
        - "{specific finding}"
      evidence:
        positive: ["{what's good}"]
        negative: ["{what's concerning}"]

    config_externalization:
      score: {0-2}
      findings:
        - "{specific finding}"
      evidence:
        positive: []
        negative: []

    horizontal_scalability:
      score: {0-2}
      findings: []
      evidence:
        positive: []
        negative: []

    startup_shutdown:
      score: {0-2}
      findings: []
      evidence:
        positive: []
        negative: []

    observability:
      score: {0-2}
      findings: []
      evidence:
        positive: []
        negative: []

    service_boundaries:
      score: {0-2}
      findings: []
      evidence:
        positive: []
        negative: []

  # Per-unit assessment for monorepos
  units:
    - name: "api"
      path: "apps/api"
      score: {0-12}
      notes: "{specific notes}"
    - name: "cms"
      path: "apps/cms"
      score: {0-12}
      notes: "{specific notes}"

  strengths:
    - "{summary of what's already good}"

  concerns:
    - "{issues that need attention}"

  blockers:
    - "{critical issues, if any}"

  recommendations:
    - "{actionable next steps}"
```
