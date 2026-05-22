# Docker Best Practices

## Base Image Selection

### Version Pinning

```dockerfile
# GOOD - Fixed patch version
FROM node:20.11.1-slim
FROM python:3.11.7-slim
FROM golang:1.21.6-alpine

# BAD - Floating tags
FROM node:latest
FROM node:lts
FROM node:20          # Minor version can change
FROM python:3         # Major version only
```

### Image Variants

| Variant | Size | Use Case |
|---------|------|----------|
| `alpine` | Smallest | Go static binaries, simple apps |
| `slim` | Small | Node.js, Python (recommended) |
| `bookworm/bullseye` | Medium | Need full toolchain |
| Default (no suffix) | Large | Avoid in production |

### Recommended Base Images

```dockerfile
# Node.js
FROM node:20.11.1-slim

# Python
FROM python:3.11.7-slim

# Go
FROM golang:1.21.6-alpine AS builder
FROM alpine:3.19 AS runtime
# Or for scratch:
FROM scratch

# Java
FROM eclipse-temurin:21-jre-alpine

# Ruby
FROM ruby:3.2-slim
```

---

## Multi-Stage Build Pattern

### Standard 3-Stage Pattern

```dockerfile
# Stage 1: Dependencies
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build
FROM deps AS build
COPY . .
RUN npm run build

# Stage 3: Runtime
FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

### Why Multi-Stage?

1. **Smaller images**: Build tools don't end up in production
2. **Better caching**: Dependencies layer changes less often
3. **Security**: Less attack surface

---

## Layer Optimization

### Order by Change Frequency

```dockerfile
# GOOD - Least changing first
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# BAD - Source files invalidate cache for dependencies
COPY . .
RUN npm ci && npm run build
```

### Combine RUN Commands

```dockerfile
# GOOD - Single layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        make \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# BAD - Multiple layers
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y make
RUN apt-get install -y g++
```

---

## Cache Mounts (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1.4

# npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# yarn
RUN --mount=type=cache,target=/root/.yarn \
    yarn install --frozen-lockfile

# pnpm
RUN --mount=type=cache,target=/pnpm/store \
    pnpm install --frozen-lockfile

# pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# go
RUN --mount=type=cache,target=/go/pkg/mod \
    go build -o main .
```

---

## Security

### Non-Root User

```dockerfile
# Node.js (built-in user)
USER node

# Python (create user)
RUN useradd -m -u 1000 appuser
USER appuser

# Go/Alpine
RUN adduser -D -u 1000 appuser
USER appuser

# Or use nobody
USER nobody
```

### File Permissions

```dockerfile
# Set ownership before switching user
COPY --chown=node:node . .
USER node

# Or change after copy
COPY . .
RUN chown -R node:node /app
USER node
```

### Don't Include Secrets

```dockerfile
# BAD - Secret in image layer
ENV API_KEY=sk-xxxxx
COPY .env .

# GOOD - Runtime injection
# Use docker run -e or docker-compose environment
```

---

## .dockerignore

### Must Ignore

```
.git
.env
.env.*
node_modules
__pycache__
*.pyc
.venv
vendor
dist
build
.next
coverage
*.log
```

### Should Ignore

```
.vscode
.idea
*.md
docs
tests
*.test.js
*.spec.ts
Makefile
docker-compose*.yml
Dockerfile*
```

---

## Health Check

### Without curl (Recommended)

```dockerfile
# Node.js
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Python
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
```

### With curl (If available)

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
```

---

## Environment Variables

### Build-time vs Runtime

```dockerfile
# Build-time only (not in final image)
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-slim

# Runtime (persists in image)
ENV NODE_ENV=production
ENV PORT=3000

# Build-time passed to runtime
ARG VERSION
ENV APP_VERSION=$VERSION
```

### Default Values

```dockerfile
# With default
ENV PORT=3000
ENV NODE_ENV=production

# Without default (must be provided at runtime)
# Just document in comments or separate file
```

---

## Signals and Graceful Shutdown

### Exec Form (Recommended)

```dockerfile
# GOOD - PID 1, receives signals
CMD ["node", "server.js"]
ENTRYPOINT ["python", "app.py"]

# BAD - Shell wrapper, signals not forwarded
CMD node server.js
```

### With Init System

```dockerfile
# For complex apps needing init
FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.js"]
```

---

## Common Anti-Patterns

### DON'T: Use ADD for URLs

```dockerfile
# BAD
ADD https://example.com/file.tar.gz /app/

# GOOD
RUN curl -L https://example.com/file.tar.gz | tar xz -C /app/
```

### DON'T: Run apt-get upgrade

```dockerfile
# BAD - Unpredictable results
RUN apt-get update && apt-get upgrade -y

# GOOD - Only install what you need
RUN apt-get update && apt-get install -y --no-install-recommends specific-package
```

### DON'T: Store data in container

```dockerfile
# BAD - Data lost on container restart
RUN mkdir /data

# GOOD - Use volumes
VOLUME ["/data"]
```

### DON'T: Hardcode paths that should be configurable

```dockerfile
# BAD
WORKDIR /home/user/myapp

# GOOD
WORKDIR /app
```

---

## Workspace / Monorepo Best Practices

### pnpm Workspace Pattern

```dockerfile
# Stage 1: Dependencies
FROM node:20-slim AS deps
WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@10.20.0 --activate

# Copy workspace configuration files
COPY package.json pnpm-workspace.yaml .npmrc ./

# Copy ALL workspace package.json files for proper resolution
COPY packages ./packages
COPY patches ./patches
COPY e2e/package.json ./e2e/
COPY apps/desktop/src/main/package.json ./apps/desktop/src/main/

# Install dependencies
# IMPORTANT: Check .npmrc for lockfile=false
# If lockfile=false, do NOT use --frozen-lockfile
RUN pnpm install --ignore-scripts
```

### Smart .dockerignore for Workspaces

```dockerfile
# DON'T: Exclude entire directories
e2e               # This excludes e2e/package.json too!
apps/desktop

# DO: Exclude contents but keep package.json
e2e/*
!e2e/package.json

apps/desktop/node_modules
apps/desktop/dist
apps/desktop/out
# This keeps apps/desktop/src/main/package.json
```

### Build-Time Environment Variables

For Next.js and similar frameworks that need env vars during static generation:

```dockerfile
# Build stage
FROM base AS build

# Use ARG for build-time placeholders (more secure, not in final image)
ARG KEY_VAULTS_SECRET_PLACEHOLDER="build-placeholder-32chars"
ARG DATABASE_URL_PLACEHOLDER="postgres://placeholder:placeholder@localhost:5432/placeholder"

# Set as ENV for the build process
ENV KEY_VAULTS_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
ENV DATABASE_URL=${DATABASE_URL_PLACEHOLDER}
ENV AUTH_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
ENV DATABASE_DRIVER=""

# Build will now succeed even though these are placeholders
RUN npm run build
```

### Custom Server Entry Points

For apps with custom server launchers:

```dockerfile
# Runtime stage
FROM node:20-slim AS production

# IMPORTANT: Create symlink for scripts that expect /bin/node
RUN ln -sf /usr/local/bin/node /bin/node

# Copy custom entry point
COPY --from=build /app/scripts/serverLauncher/startServer.js ./startServer.js
COPY --from=build /app/scripts/_shared ./scripts/_shared

# If using database migrations
COPY --from=build /app/scripts/migrateServerDB/docker.cjs ./docker.cjs
COPY --from=build /app/scripts/migrateServerDB/errorHint.js ./errorHint.js
COPY --from=build /app/packages/database/migrations ./migrations

# Use custom entry point instead of server.js
CMD ["node", "startServer.js"]
```

### Files You Must NOT Exclude

When creating .dockerignore for complex projects:

```
# These MUST be available during build:
# ✓ .npmrc (package manager config)
# ✓ pnpm-workspace.yaml
# ✓ patches/** (pnpm patched deps)
# ✓ All workspace package.json files
# ✓ Build scripts (prebuild.mts, etc.)
# ✓ Server launcher scripts
# ✓ Migration scripts and files
```

---

## Database/External Service Patterns

### PostgreSQL with pgvector

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16    # Not just postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
```

### Wait for Dependencies

```dockerfile
# In app container, wait for DB to be ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "fetch('http://localhost:3000/api/health')"
```

```yaml
# docker-compose.yml
services:
  app:
    depends_on:
      db:
        condition: service_healthy
```
