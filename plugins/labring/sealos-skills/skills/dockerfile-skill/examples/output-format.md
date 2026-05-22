# Output Format Examples

## Successful Build Output

```
## Dockerfile Generation Complete

### Project Analysis
- **Language**: Node.js (TypeScript)
- **Framework**: Next.js 14
- **Package Manager**: pnpm
- **Complexity**: L2 (Medium)
- **Detected Port**: 3000

### Generated Files

#### Dockerfile
```dockerfile
# syntax=docker/dockerfile:1.4
FROM node:20.11.1-slim AS deps
...
```

#### .dockerignore
```
.git
node_modules
.next
...
```

#### docker-compose.yml
```yaml
services:
  app:
    build: .
    ports:
      - "3000:3000"
...
```

### Build Results
Build successful!

**Image**: `your-app:latest`
**Size**: ~245MB

### Quick Start

```bash
# Build
docker buildx build --platform linux/amd64 --load -t your-app:latest .

# Run
docker run -d -p 3000:3000 your-app:latest

# With docker-compose
docker-compose up -d
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `PORT` | No | 3000 | Server port |
```

---

## Build with Fixes Output

```
## Dockerfile Generation Complete

### Project Analysis
- **Language**: Node.js (TypeScript)
- **Framework**: Next.js 14
- **Package Manager**: npm
- **Complexity**: L3 (High)
- **Detected Port**: 3000

### Build Iterations

#### Iteration 1: Failed
**Error**: `ENOENT: no such file or directory, open '/app/config/config.json'`
**Fix Applied**: Added `RUN mkdir -p /app/config && echo '{}' > /app/config/config.json`

#### Iteration 2: Failed
**Error**: `Error: DATABASE_URL environment variable is required`
**Fix Applied**: Added `ARG DATABASE_URL=postgres://placeholder` and `ENV DATABASE_URL=$DATABASE_URL`

#### Iteration 3: Success

### Generated Files
[files output...]

### Build Results
Build successful after 3 iterations

### Fixes Applied
1. Created missing config directory and placeholder config.json
2. Added DATABASE_URL build-time placeholder for SSG compatibility

### Notes
- The DATABASE_URL placeholder is used only during build
- Provide actual DATABASE_URL at runtime via environment variable
```

---

## Build Failed Output

```
## Dockerfile Generation - Manual Review Required

### Project Analysis
- **Language**: Node.js
- **Framework**: Custom
- **Complexity**: L3 (High)

### Build Iterations

#### Iteration 1-5: Failed
**Final Error**:
```
Error: Cannot find module '@company/internal-package'
```

### Attempted Fixes
1. Added node-gyp build dependencies
2. Increased NODE_OPTIONS memory
3. Added missing directories

### Manual Steps Required

The build failed due to a private npm package that requires authentication.

**To fix**:
1. Add `.npmrc` with registry authentication:
  ```
  //npm.pkg.github.com/:_authToken=${NPM_TOKEN}
  @company:registry=https://npm.pkg.github.com
  ```

2. Update Dockerfile to use build secrets:
  ```dockerfile
  RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
  ```

3. Build with:
  ```bash
  docker buildx build --platform linux/amd64 --load --secret id=npmrc,src=.npmrc -t app .
  ```

### Partial Output
The best working version of Dockerfile has been saved. It may work with the above modifications.
```

---

## Analysis-Only Output (for debugging)

```
## Project Analysis Results

### Detection Summary
| Property | Value |
|----------|-------|
| Language | Node.js |
| Runtime Version | 20.x |
| Framework | Next.js 14.1.0 |
| Package Manager | pnpm |
| Has TypeScript | Yes |
| Has Build Step | Yes |
| Output Mode | standalone |

### Dependency Analysis

#### NPM Packages with Native Dependencies
- `sharp` → requires `libvips-dev`
- `bcrypt` → requires `python3 make g++`

#### External Services Detected
- PostgreSQL (from `@prisma/client`)
- Redis (from `ioredis`)

### Environment Variables

#### Build-time Required
| Variable | Source | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | `schema.prisma` | Prisma client generation |
| `NEXT_PUBLIC_API_URL` | `next.config.js` | Public API endpoint |

#### Runtime Required
| Variable | Source | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | `lib/db.ts` | Database connection |
| `REDIS_URL` | `lib/cache.ts` | Cache connection |
| `JWT_SECRET` | `lib/auth.ts` | Authentication |

### Complexity Assessment
**Level**: L3 (High)

**Reasons**:
- SSG with database access during build
- Multiple native dependencies
- External service dependencies
- Environment variable requirements during build

### Recommended Approach
1. Use multi-stage build with deps → build → runtime
2. Install `libvips-dev` and build tools in deps stage
3. Provide placeholder DATABASE_URL for build
4. Generate Prisma client before build step
```
