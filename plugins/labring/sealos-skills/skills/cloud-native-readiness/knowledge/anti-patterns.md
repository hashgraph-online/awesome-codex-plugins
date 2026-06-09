# Cloud-Native Anti-Patterns

Common patterns that indicate a project is NOT ready for containerization.

## Critical Anti-Patterns (Blockers)

### 1. Local File Storage for User Data
```
Problem: User uploads saved to ./uploads/ or ./data/
Impact: Data lost on container restart, can't scale horizontally
Fix: Migrate to S3/R2/GCS for file storage
```

### 2. SQLite as Primary Database
```
Problem: SQLite file stored on local filesystem
Impact: Can't share between containers, data lost on restart without volume
Fix: Migrate to PostgreSQL/MySQL with external connection
```

### 3. Hardcoded Secrets in Source
```
Problem: API keys, passwords, tokens committed to git
Impact: Security risk, can't rotate without code change
Fix: Move all secrets to environment variables
```

### 4. Hardcoded localhost References
```
Problem: Code references localhost:5432, 127.0.0.1:6379
Impact: Won't work in container network
Fix: Use env vars for all service URLs (DATABASE_URL, REDIS_URL)
```

### 5. Process-Dependent State
```
Problem: Global variables storing user sessions, request counts
Impact: State lost on restart, inconsistent across instances
Fix: Externalize to Redis or database
```

## Warning Anti-Patterns (Concerns)

### 6. In-Memory Session Store
```
Problem: express-session with default MemoryStore
Impact: Sessions lost on restart, can't load-balance across instances
Fix: Use Redis session store (connect-redis)
```

### 7. Cron Jobs Without Distributed Lock
```
Problem: node-cron or setInterval for scheduled tasks
Impact: Multiple instances = multiple executions
Fix: Use distributed scheduler (BullMQ, database-backed, leader election)
```

### 8. WebSocket Without Redis Adapter
```
Problem: Socket.IO or ws without pub/sub backing
Impact: Clients on different instances can't communicate
Fix: Add Redis adapter for Socket.IO, or use external pub/sub
```

### 9. Large Startup Payload
```
Problem: Loading large ML models, data files, or indexes at startup
Impact: Slow container startup, fails K8s readiness probes
Fix: Lazy loading, separate model-serving service, readiness probe with delay
```

### 10. No Graceful Shutdown
```
Problem: No SIGTERM handler, abrupt process exit
Impact: In-flight requests dropped, database connections leaked
Fix: Add signal handler, drain connections, close DB pool
```

### 11. Logging to Files
```
Problem: Winston/Bunyan configured to write to ./logs/app.log
Impact: Logs lost on container restart, fills up container filesystem
Fix: Log to stdout/stderr, use container log driver for aggregation
```

### 12. Build-Time Secrets Required
```
Problem: Next.js SSG pages need DATABASE_URL at build time
Impact: Secrets must be available during docker build (leaks into layers)
Fix: Use ARG with placeholder values for build, real values at runtime
```

## Informational Anti-Patterns (Notes)

### 13. Monolith Without Clear Boundaries
```
Problem: Single process handles API, background jobs, WebSocket, cron
Impact: Can't scale components independently
Note: Works in containers but limits K8s benefits
Suggestion: Consider splitting into services over time
```

### 14. Shared Database Without Scoping
```
Problem: Multiple services access same tables directly
Impact: Schema changes require coordinated deployment
Note: Common and acceptable for many projects
Suggestion: Define clear table ownership per service
```

### 15. Missing Health Checks
```
Problem: No /health or /healthz endpoint
Impact: K8s can't determine if container is healthy
Fix: Add simple health endpoint that checks DB connectivity
```

## Detection Cheat Sheet

| Anti-Pattern | Search Pattern |
|-------------|---------------|
| Local file storage | `fs.write`, `multer.diskStorage`, `./uploads` |
| SQLite | `sqlite`, `better-sqlite3`, `*.db` |
| Hardcoded secrets | `password = "`, `apiKey: "sk-` |
| Hardcoded localhost | `localhost:`, `127.0.0.1:` (outside .env) |
| Memory sessions | `MemoryStore`, `express-session` without store |
| Cron without lock | `node-cron`, `setInterval` > 60s |
| WebSocket no adapter | `socket.io` without `@socket.io/redis-adapter` |
| File logging | `winston.*File`, `createWriteStream.*log` |
| No SIGTERM | absence of `SIGTERM` in codebase |
| No health check | absence of `/health` or `/healthz` route |
