# Cloud-Native Readiness Scoring Criteria

## Dimension 1: Statelessness (0-2)

### Score 2 — Fully Stateless
- All persistent data stored in external database (PostgreSQL, MySQL, MongoDB)
- Session management via external store (Redis, DB) or stateless tokens (JWT)
- File uploads go to cloud storage (S3, R2, GCS) not local filesystem
- No in-memory caches that can't be lost (or cache is external like Redis)
- Application can be killed and restarted with zero data loss

### Score 1 — Mostly Stateless
- Core data is external, but some local state exists:
  - Temporary file processing (acceptable if using `/tmp`)
  - In-memory cache for performance (acceptable if cache miss just hits DB)
  - Local uploads that get moved to cloud storage eventually
- Losing an instance causes minor degradation, not data loss

### Score 0 — Stateful
- SQLite or embedded database as primary store
- User uploads saved to local filesystem permanently
- In-memory session store (`MemoryStore`)
- Application state lives in process memory
- Killing instance = data loss

---

## Dimension 2: Config Externalization (0-2)

### Score 2 — Fully Externalized
- All environment-specific values from env vars
- `.env.example` documents all required variables
- Config validation at startup (e.g., `envalid`, `@t3-oss/env-nextjs`)
- No secrets in source code
- Same image works in dev/staging/prod with different env vars

### Score 1 — Partially Externalized
- Most config via env vars, some hardcoded defaults
- `.env.example` exists but may be incomplete
- Some config files that could be overridden but aren't env-driven
- No secrets committed, but config isn't fully documented

### Score 0 — Hardcoded
- Connection strings hardcoded in source
- Secrets committed to repo
- Config files with environment-specific values checked in
- No env var pattern

---

## Dimension 3: Horizontal Scalability (0-2)

### Score 2 — Fully Scalable
- Stateless HTTP handlers (REST/GraphQL)
- Background jobs via external queue (BullMQ, RabbitMQ, SQS)
- Database handles concurrency (proper transactions, no file locks)
- No singleton patterns that break with N instances
- WebSocket with Redis adapter (if applicable)

### Score 1 — Mostly Scalable
- Core request handling is stateless
- Some single-instance concerns:
  - Cron jobs without distributed lock
  - WebSocket without sticky session support
  - In-memory rate limiting
- Running 2+ instances mostly works, with minor issues

### Score 0 — Single Instance Only
- File-based locking
- In-process scheduler with side effects
- Shared mutable state across requests
- Can only run one instance

---

## Dimension 4: Startup/Shutdown (0-2)

### Score 2 — Production Ready
- Explicit SIGTERM/SIGINT handling
- Graceful connection draining
- Health check endpoint (`/health`, `/healthz`, `/readyz`)
- Fast startup (< 10 seconds)
- Proper cleanup of resources on shutdown

### Score 1 — Framework Defaults
- Framework handles basic lifecycle (Express, Next.js, Hono)
- No explicit signal handling but doesn't crash on SIGTERM
- No dedicated health endpoint but root responds quickly
- Moderate startup time (10-30 seconds)

### Score 0 — Unmanaged
- No signal handling
- Long startup (> 30 seconds, loading large models/data)
- Abrupt termination loses in-flight requests
- No way to check if service is ready

---

## Dimension 5: Observability (0-2)

### Score 2 — Well Instrumented
- Structured logging (JSON to stdout/stderr)
- Error tracking (Sentry, Bugsnag)
- Metrics endpoint (Prometheus, custom)
- Request tracing (correlation IDs, OpenTelemetry)
- Centralized log-friendly output

### Score 1 — Basic Logging
- Console.log to stdout (works with container log drivers)
- Some error handling middleware
- No structured format but parseable
- No metrics or tracing

### Score 0 — Blind
- No logging or logs to local files only
- Silent error swallowing
- No way to diagnose issues in production
- No error reporting

---

## Dimension 6: Service Boundaries (0-2)

### Score 2 — Well Bounded
- Clear separation: each service has own entry point and package.json
- Independent deployment possible
- Well-defined API contracts (REST routes, GraphQL schema)
- Monorepo with apps/ directory pattern
- Database per service or clearly scoped queries

### Score 1 — Logical Separation
- Routes/modules are organized but deploy as one unit
- Shared database with clear ownership
- Could be split into services with moderate effort
- Has clear API layer even if monolithic

### Score 0 — Tightly Coupled
- Everything in one file or deeply intertwined
- No clear API boundaries
- Frontend and backend inseparable
- Circular dependencies between modules

---

## Technology-Specific Bonuses (Informational, not scored)

These don't affect the score but are noted in the report:

### Naturally Cloud-Native Frameworks
- **Hono** — Edge-first, stateless by design
- **Fastify** — Fast startup, graceful shutdown built-in
- **Next.js** — Standalone output mode = container-ready
- **Go net/http** — Single binary, fast startup, graceful shutdown
- **FastAPI** — ASGI, stateless, Uvicorn handles signals

### Requires Extra Attention
- **Express** — No built-in graceful shutdown (needs manual SIGTERM)
- **Django** — ORM connection management in containers
- **Spring Boot** — JVM startup time, memory tuning needed
- **Rails** — Asset pipeline, Puma worker configuration
