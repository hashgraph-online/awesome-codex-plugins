# syntax=docker/dockerfile:1.4

# ============================================
# Next.js Production Dockerfile
# Supports: standalone mode, workspace/monorepo, custom entry points
# ============================================

# ============================================
# Stage 1: Base - Common setup
# ============================================
FROM node:{{NODE_VERSION}}-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    {{SYSTEM_DEPS}} \
    && rm -rf /var/lib/apt/lists/*

# Enable corepack for pnpm (if using pnpm)
# {{PNPM_SETUP}}
# RUN corepack enable && corepack prepare pnpm@{{PNPM_VERSION}} --activate

# ============================================
# Stage 2: Dependencies
# ============================================
FROM base AS deps

WORKDIR /app

# Copy package manager files
COPY package.json {{PACKAGE_MANAGER_FILES}} ./

# For workspace/monorepo: Copy all workspace package.json files
# {{WORKSPACE_COPY}}
# COPY packages ./packages
# COPY patches ./patches
# COPY e2e/package.json ./e2e/
# COPY apps/desktop/src/main/package.json ./apps/desktop/src/main/

# Install dependencies
# If lockfile=false in .npmrc, do NOT use --frozen-lockfile
RUN --mount=type=cache,target=/root/.npm \
    {{INSTALL_COMMAND}}

# ============================================
# Stage 3: Build
# ============================================
FROM base AS build

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
# For workspace: also copy package directories with their node_modules
# {{WORKSPACE_DEPS_COPY}}
# COPY --from=deps /app/packages ./packages

# Copy source code
COPY . .

# Set build environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS="--max-old-space-size=8192"

# Build-time environment variables (placeholders for SSG/ISR)
# These are replaced at runtime with actual values
# {{BUILD_TIME_ENV}}
# ARG KEY_VAULTS_SECRET_PLACEHOLDER="build-placeholder-32chars"
# ARG DATABASE_URL_PLACEHOLDER="postgres://placeholder:placeholder@localhost:5432/placeholder"
# ENV KEY_VAULTS_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
# ENV DATABASE_URL=${DATABASE_URL_PLACEHOLDER}
# ENV AUTH_SECRET=${KEY_VAULTS_SECRET_PLACEHOLDER}
# ENV DATABASE_DRIVER=""

# Build the application
RUN {{BUILD_COMMAND}}

# ============================================
# Stage 4: Production Runtime
# ============================================
FROM node:{{NODE_VERSION}}-slim AS production

# Build arguments for labels
ARG SHA

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    {{RUNTIME_DEPS}} \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/local/bin/node /bin/node

# Create non-root user
RUN groupadd --gid 1001 nodejs \
    && useradd --uid 1001 --gid nodejs --shell /bin/bash --create-home nextjs

WORKDIR /app

# ============================================
# Option A: Standalone mode (recommended)
# Requires: output: 'standalone' in next.config.js
# ============================================
COPY --from=build --chown=nextjs:nodejs /app/public ./public
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static

# ============================================
# Option B: Custom entry point (for complex apps)
# ============================================
# {{CUSTOM_ENTRY_POINT}}
# COPY --from=build --chown=nextjs:nodejs /app/scripts/serverLauncher/startServer.js ./startServer.js
# COPY --from=build --chown=nextjs:nodejs /app/scripts/_shared ./scripts/_shared

# ============================================
# Option C: Database migrations (if needed)
# ============================================
# {{MIGRATIONS}}
# COPY --from=build --chown=nextjs:nodejs /app/scripts/migrateServerDB/docker.cjs ./docker.cjs
# COPY --from=build --chown=nextjs:nodejs /app/scripts/migrateServerDB/errorHint.js ./errorHint.js
# COPY --from=build --chown=nextjs:nodejs /app/packages/database/migrations ./migrations

# Set production environment
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT={{PORT}}
ENV NEXT_TELEMETRY_DISABLED=1

# Labels
LABEL org.opencontainers.image.title="{{APP_NAME}}"
LABEL org.opencontainers.image.source="{{REPO_URL}}"
LABEL org.opencontainers.image.revision="${SHA}"

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE {{PORT}}

# Health check (adjust path as needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "fetch('http://localhost:{{PORT}}/api/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

# Start the application
# Option A: Standard Next.js standalone
CMD ["node", "server.js"]

# Option B: Custom entry point
# CMD ["node", "startServer.js"]

# ============================================
# Template Variables Reference
# ============================================
# {{NODE_VERSION}}         - e.g., "20.11.1" or "24"
# {{PNPM_VERSION}}         - e.g., "10.20.0"
# {{PACKAGE_MANAGER_FILES}} - e.g., "pnpm-workspace.yaml .npmrc"
# {{INSTALL_COMMAND}}      - e.g., "pnpm install --ignore-scripts"
# {{BUILD_COMMAND}}        - e.g., "npm run build:docker"
# {{PORT}}                 - e.g., "3210"
# {{APP_NAME}}             - e.g., "LobeChat"
# {{REPO_URL}}             - e.g., "https://github.com/lobehub/lobe-chat"
# {{SYSTEM_DEPS}}          - e.g., "proxychains4"
# {{RUNTIME_DEPS}}         - e.g., "proxychains4"
# {{WORKSPACE_COPY}}       - Workspace package.json COPY commands
# {{WORKSPACE_DEPS_COPY}}  - Workspace with node_modules COPY commands
# {{BUILD_TIME_ENV}}       - ARG/ENV for build-time variables
# {{CUSTOM_ENTRY_POINT}}   - Custom server entry point COPY commands
# {{MIGRATIONS}}           - Database migration file COPY commands
