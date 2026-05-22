# syntax=docker/dockerfile:1
#
# Next.js + Bun Dockerfile Template
#
# Features:
# - Multi-stage build for minimal image size
# - Bun for fast dependency installation and build
# - Node.js slim runtime (Bun runtime is larger)
# - Standalone output support (recommended)
# - Non-root user for security
#
# Usage:
# - Ensure next.config has `output: 'standalone'`
# - Replace {BUN_VERSION} with specific version (e.g., 1.1.42)
# - Replace {NODE_VERSION} with specific version (e.g., 20.18.1)
# - Add build-time env var placeholders as needed (see comments)

# ============================================
# Stage 1: Dependencies
# ============================================
FROM oven/bun:{BUN_VERSION}-slim AS deps

WORKDIR /app

# Copy dependency files
COPY package.json bun.lockb ./

# Install dependencies
# Note: --frozen-lockfile ensures reproducible builds
RUN bun install --frozen-lockfile

# ============================================
# Stage 2: Build
# ============================================
FROM oven/bun:{BUN_VERSION}-slim AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# ============================================
# Build-time Environment Variables
# ============================================
# Next.js statically analyzes API routes during build.
# If your code initializes SDKs at module top-level, add placeholders here.
# These are NOT used at runtime - actual values come from docker run -e
#
# Common examples (uncomment as needed):
# ARG RESEND_API_KEY=re_placeholder_key
# ARG STRIPE_SECRET_KEY=sk_placeholder_key
# ARG NOTION_SECRET=placeholder_notion_secret
# ARG NOTION_DB=placeholder_notion_db
# ARG UPSTASH_REDIS_REST_URL=https://placeholder.upstash.io
# ARG UPSTASH_REDIS_REST_TOKEN=placeholder_token
# ARG DATABASE_URL=postgres://placeholder:placeholder@localhost:5432/placeholder
#
# ENV RESEND_API_KEY=${RESEND_API_KEY}
# ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
# ENV NOTION_SECRET=${NOTION_SECRET}
# ENV NOTION_DB=${NOTION_DB}
# ENV UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL}
# ENV UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN}
# ENV DATABASE_URL=${DATABASE_URL}

# Build the application
RUN bun run build

# ============================================
# Stage 3: Production Runtime
# ============================================
# Using Node.js slim for runtime (smaller than Bun runtime image)
FROM node:{NODE_VERSION}-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone build output (much smaller than full node_modules)
# Requires `output: 'standalone'` in next.config
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check without installing curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:3000', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "server.js"]
