# Real-World Containerizable Project Patterns

Data derived from analysis of 164 Sealos Cloud templates — all production-deployed containerized applications.

## Key Finding

**ALL 164 projects in the Sealos template marketplace are successfully containerized and running in production.**
This dataset provides ground truth for what "containerizable" looks like in practice.

## Language Distribution (150 analyzed)

| Language | Count | % | Dockerfile in Repo |
|----------|-------|---|-------------------|
| TypeScript | 53 | 35% | 47% have Dockerfile |
| Go | 23 | 15% | 61% have Dockerfile |
| Python | 18 | 12% | 67% have Dockerfile |
| Shell | 9 | 6% | 44% (wrapper projects) |
| JavaScript | 7 | 5% | 43% |
| PHP | 7 | 5% | 14% (use official images) |
| Java | 5 | 3% | 40% |
| Rust | 4 | 3% | 100% |
| Vue | 3 | 2% | 67% |
| C#/.NET | 2 | 1% | 0% (use pre-built images) |
| Others | 19 | 13% | varies |

**Insight**: TypeScript + Go + Python + Rust = 65% of all containerizable projects.
Go and Rust have the highest Dockerfile presence (single binary advantage).

## Docker Artifact Presence

- **50% of repos have a Dockerfile** in the repository root
- **35% have docker-compose.yml** alongside
- **25% have both** Dockerfile + docker-compose
- **41% have neither** — Sealos builds from pre-built images or generates config

**Insight**: Having NO Dockerfile doesn't mean "not containerizable". Many mature projects
publish pre-built images to registries (ghcr.io, Docker Hub), and Sealos references those directly.

## Project Categories

| Category | Count | Most Common Languages |
|----------|-------|-----------------------|
| tool | 91 | TypeScript, Go, PHP |
| ai | 34 | TypeScript, Python |
| backend | 16 | Go, TypeScript, Java |
| low-code | 13 | TypeScript |
| database | 13 | TypeScript, Go, Java |
| dev-ops | 8 | Go, Shell |
| game | 7 | Shell, Java |
| monitor | 6 | TypeScript, Go |
| blog | 4 | Java, TypeScript |
| storage | 3 | Go, Rust |

## Common Dockerfile Patterns (from 30 deep-analyzed repos)

### Multi-Stage Builds
- **88% use multi-stage builds** (2-5 stages)
- Average: 2.5 stages
- Pattern: `deps → build → runtime`
- Go/Rust projects: `build → scratch/alpine` (minimal final image)
- Node.js projects: `deps → build → node:slim` or `→ nginx`

### Base Image Choices
| Runtime | Base Image | Used By |
|---------|-----------|---------|
| Node.js | `node:20-alpine`, `node:22-slim` | TypeScript/JavaScript apps |
| Go | `alpine:latest`, `scratch` | Go binaries |
| Python | `python:3.x-slim` | Python apps |
| Java | `eclipse-temurin:21-jre` | Spring Boot apps |
| Rust | `debian:slim`, `alpine` | Rust binaries |
| Static | `nginx:stable-alpine` | Vue/React SPAs |

### Security Practices
- **35% use non-root USER** (e.g., `USER node`, `USER nextjs`, `USER 1000`)
- **18% have HEALTHCHECK** instruction
- Most use fixed image versions (not `:latest`)

### Entry Point Patterns
| Pattern | Example | Used By |
|---------|---------|---------|
| Direct binary | `CMD ["./app"]` | Go, Rust |
| Node start | `CMD ["npm", "start"]` or `CMD ["pnpm", "start"]` | Node.js |
| Entrypoint script | `ENTRYPOINT ["./docker-entrypoint.sh"]` | Complex apps (migrations + start) |
| Custom server | `CMD ["node", "server.js"]` | Next.js standalone |
| Nginx | `CMD ["nginx", "-g", "daemon off;"]` | Static SPAs |

## What Makes ALL These Projects Containerizable

### Universal Characteristics (found in 100% of templates)

1. **Web Service**: Every project exposes HTTP/HTTPS (API, dashboard, or web UI)
2. **External State**: Data stored in PostgreSQL, MySQL, MongoDB, Redis — never embedded-only
3. **Config via Environment**: All use env vars for connection strings, API keys, secrets
4. **Clear Entry Point**: Single binary, `npm start`, or well-defined startup command
5. **Single Responsibility**: Each container runs one process/service

### Common External Dependencies

| Dependency | Frequency | Typical Env Var |
|-----------|-----------|-----------------|
| PostgreSQL | Very High | `DATABASE_URL` |
| Redis | High | `REDIS_URL` |
| MySQL | Medium | `DATABASE_URL`, `MYSQL_*` |
| S3/MinIO | Medium | `S3_ENDPOINT`, `S3_ACCESS_KEY` |
| MongoDB | Medium | `MONGODB_URI` |
| OpenAI API | High (AI category) | `OPENAI_API_KEY` |

### Monorepo Patterns (common in TypeScript projects)

Many of the largest projects (Dify, AFFiNE, n8n, Plane, Twenty) are monorepos:
- Use Turborepo, pnpm workspaces, or nx
- Build specific app targets for Docker
- Often have separate Dockerfiles per service (api, web, worker)
- Use `--filter` or workspace commands in Dockerfile

## Fast-Track Assessment Rules

Based on this data, these characteristics almost guarantee containerization readiness:

### Instant Pass (Score >= 10)
- Go or Rust single-binary web server
- Next.js/Nuxt app with `output: standalone`
- Python FastAPI/Flask with PostgreSQL
- Any project that already has Dockerfile + docker-compose

### Likely Pass (Score >= 7)
- TypeScript monorepo with apps/ structure
- Java Spring Boot application
- PHP app with composer (use official PHP-FPM image)
- Any project using PostgreSQL/MySQL + Redis

### Needs Investigation (Score 4-6)
- Projects with SQLite as primary DB (might need volume mount)
- Desktop/Electron apps with web component
- Projects with heavy local file processing

### Likely Fail (Score 0-3)
- Pure CLI tools with no web server
- Desktop-only applications
- Projects requiring GPU without web API
- Embedded systems code

## Sealos Template Structure Reference

Each Sealos template defines:
```yaml
spec:
  gitRepo: "https://github.com/org/repo"    # Source code
  defaults:
    app_name: "xxx-${{ random(8) }}"          # Random instance name
    app_host: "xxx-${{ random(8) }}"          # Random hostname
  inputs:                                      # User-configurable params
    OPENAI_API_KEY:                            # Most common: API keys
      type: string
      required: true
    admin_password:                            # Second: admin credentials
      type: string
```

**Key patterns in inputs (most common)**:
1. `OPENAI_API_KEY` (9 templates) — AI service API key
2. `admin_password` (5) — Admin credentials
3. `api_key` (3) — Generic API key
4. `root_password` (3) — Database root password
5. `BASE_URL` (2) — Service URL configuration

This tells us: containerizable apps externalize their secrets and API configurations.
