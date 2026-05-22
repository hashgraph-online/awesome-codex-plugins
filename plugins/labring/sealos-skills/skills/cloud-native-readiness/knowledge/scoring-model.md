# Deterministic Scoring Model

This document describes the code-level scoring algorithm implemented in
`dockerfile-service/scripts/score-model.js`. It provides instant (< 1 second)
readiness scoring by analyzing the local filesystem of a cloned repo.

## Architecture

The model has two layers:
1. **Signal Detection** — filesystem scanning for files, dependencies, patterns
2. **Scoring Algorithm** — maps signals to 6 dimension scores (0-2 each)

## Signal Detection

### Language Detection
Scans root AND up to 2 levels deep (monorepo support):

| File | Language |
|------|----------|
| `package.json` | Node.js (TypeScript/JavaScript) |
| `go.mod` | Go |
| `requirements.txt`, `pyproject.toml` | Python |
| `pom.xml`, `build.gradle` | Java |
| `Cargo.toml` | Rust |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.sln` | .NET/C# |

### Framework Detection (Node.js — scans ALL package.json in monorepo)
Collects dependencies from every `package.json` found up to 3 levels deep:

| Dependency | Framework |
|-----------|-----------|
| `next` | Next.js |
| `hono` | Hono |
| `express` | Express |
| `fastify` | Fastify |
| `@nestjs/core` | NestJS |
| `nuxt` | Nuxt |
| `astro` | Astro |

### HTTP Server Detection
The most critical signal — does this project listen on a port?

| Condition | HTTP Detected |
|-----------|--------------|
| Node.js + any web framework | Yes |
| Node.js + `start` script in package.json | Yes |
| Go (always web) | Yes |
| Python + FastAPI/Django/Flask | Yes |
| Java + Spring Boot | Yes |
| Rust + actix-web/axum/rocket | Yes |
| PHP (always served via web server) | Yes |
| Ruby + rails/sinatra/puma | Yes |

### State Externalization
Scans dependencies for database/cache libraries:

| Signal | Libraries |
|--------|-----------|
| PostgreSQL | `pg`, `@prisma/client`, `drizzle-orm`, `typeorm`, `sequelize`, `psycopg`, `pgx` |
| MySQL | `mysql2`, `mysql`, `pymysql`, `go-sql-driver/mysql` |
| MongoDB | `mongoose`, `mongodb`, `pymongo`, `mongo-driver` |
| Redis | `redis`, `ioredis`, `@upstash/redis`, `go-redis` |
| SQLite | `better-sqlite3`, `sqlite3` (penalty: reduces statelessness score) |
| S3 | `@aws-sdk/client-s3`, `minio` |

### Config Externalization
| Signal | Score Impact |
|--------|-------------|
| `.env.example` found (root or sub-dir) | +2 config |
| `.env` found but no `.env.example` | +1 config |
| `docker-compose` found | +1 config (implies env vars) |
| `@t3-oss/env-nextjs` or `envalid` | +2 config |

### Docker Artifacts (Bonus points, not dimension)
| Signal | Bonus |
|--------|-------|
| `Dockerfile` exists | +1 |
| `docker-compose.yml` exists | +1 |

## Scoring Algorithm

### Dimension Scores (0-2 each, max raw = 12)

```
statelessness:
  2 = external DB (postgres/mysql/mongo) without sqlite
  1 = external DB + sqlite (mixed), or redis/s3 only, or web service without detected DB
  0 = no external state or HTTP

config:
  2 = .env.example found OR env validation library
  1 = .env found or docker-compose exists
  0 = nothing detected

scalability:
  2 = Go/Rust (compiled binary) OR HTTP + Redis
  1 = any HTTP handler
  0 = no HTTP

startup:
  2 = Go/Rust OR Hono/Fastify (lightweight frameworks)
  1 = Next.js/Express/FastAPI/Django/Flask/Spring or has start script
  0 = nothing

observability:
  2 = Dockerfile has HEALTHCHECK
  1 = HTTP handler (produces request logs)
  0 = nothing

boundaries:
  2 = monorepo with apps/ dir, OR monorepo detected
  1 = single service with build pipeline or HTTP handler
  0 = nothing
```

### Bonus (capped at total 12)
- +1 if Dockerfile exists
- +1 if docker-compose exists

### Final Score
```
total = min(12, sum(dimensions) + bonus)

Excellent (10-12): Fully cloud-native ready
Good      (7-9):   Ready with minor adjustments
Fair      (4-6):   Needs some refactoring
Poor      (0-3):   Significant rework needed
```

## Accuracy (measured against 164 Sealos production templates)

All 164 templates are confirmed containerizable (ground truth = positive).

| Threshold | Accuracy |
|-----------|----------|
| Score >= 4 (Fair+) | ~95% (target: catch almost everything) |
| Score >= 7 (Good+) | ~75% (target: confident recommendation) |

Projects scoring below 4 are typically:
- Shell wrapper projects (language=Dockerfile or Shell)
- Unknown language repos (private or incomplete data)
- Clojure/Erlang (niche languages not in detection list)

These edge cases are handled by the AI deep assessment fallback.

## Usage

### CLI
```bash
node scripts/score-model.js /path/to/repo
```

### Programmatic
```javascript
import { scoreProject } from './scripts/score-model.js';

const result = scoreProject('/path/to/cloned/repo');
// result.score: 0-12
// result.verdict: "Excellent" | "Good" | "Fair" | "Poor"
// result.dimensions: { statelessness, config, scalability, startup, observability, boundaries }
// result.signals: { language, framework, has_http_server, external_db, ... }
```

### API
```bash
# Fast (code-only, < 5 seconds including git clone)
curl -X POST http://localhost:3000/assess \
  -H 'Content-Type: application/json' \
  -d '{"github_url": "https://github.com/lobehub/lobe-chat"}'

# Deep (AI-powered, 1-3 minutes, full markdown report)
curl -X POST http://localhost:3000/assess/deep \
  -H 'Content-Type: application/json' \
  -d '{"github_url": "https://github.com/lobehub/lobe-chat"}'
```
