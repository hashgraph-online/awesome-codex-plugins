# syntax=docker/dockerfile:1.4

# ============================================
# Stage 1: Dependencies
# ============================================
FROM node:20.11.1-slim AS deps

WORKDIR /app

# Install system dependencies for native modules (if needed)
# {{SYSTEM_DEPS}}

# Copy package files
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# ============================================
# Stage 2: Build
# ============================================
FROM deps AS build

WORKDIR /app

# Copy source code
COPY . .

# Set build-time environment variables
ARG NUXT_PUBLIC_API_BASE=http://localhost:3000
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE

# Build Nuxt application
RUN npm run build

# ============================================
# Stage 3: Runtime
# ============================================
FROM node:20.11.1-slim AS runtime

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0
ENV NITRO_PORT=3000
ENV NITRO_HOST=0.0.0.0

# Copy built application (.output directory from Nuxt 3)
COPY --from=build /app/.output ./.output

# Use non-root user
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:3000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start Nuxt server
CMD ["node", ".output/server/index.mjs"]
