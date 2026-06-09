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

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# ============================================
# Stage 2: Build (if needed)
# ============================================
FROM deps AS build

# Install all dependencies including devDependencies
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# ============================================
# Stage 3: Runtime
# ============================================
FROM node:20.11.1-slim AS runtime

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000

# Copy production dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy built application from build stage
COPY --from=build /app/dist ./dist
# Or if no build step:
# COPY . .

# Copy package.json for npm start
COPY package.json ./

# Use non-root user
USER node

# Expose port
EXPOSE 3000

# Health check without curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start application
CMD ["node", "dist/index.js"]
