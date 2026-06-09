# syntax=docker/dockerfile:1.4

# ============================================
# Stage 1: Build
# ============================================
FROM rust:1.75-slim AS builder

WORKDIR /app

# Install build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a dummy project to cache dependencies
RUN cargo new --bin app
WORKDIR /app/app

# Copy dependency manifests only
COPY Cargo.toml Cargo.lock ./

# Build dependencies only (cached unless Cargo.toml/Cargo.lock change)
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/app/target \
    cargo build --release && rm -rf src

# Copy real source code
COPY src ./src

# Build the actual application
# Touch main.rs to invalidate the dummy binary but keep dependency cache
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/app/target \
    touch src/main.rs && \
    cargo build --release && \
    cp target/release/app /usr/local/bin/app

# ============================================
# Stage 2: Runtime
# ============================================
FROM debian:bookworm-slim AS runtime

WORKDIR /app

# Install runtime dependencies (TLS + timezone)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PORT=8080

# Copy binary from builder
COPY --from=builder /usr/local/bin/app .

# Create non-root user
RUN useradd -r -u 1001 -s /bin/false appuser
USER 1001

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/health || exit 1

# Start application
CMD ["./app"]

# ============================================
# Alternative: Alpine + musl static build
# Smaller image (~30MB) but requires musl target
# ============================================
# FROM rust:1.75-alpine AS builder
#
# RUN apk add --no-cache musl-dev pkgconfig openssl-dev
# WORKDIR /app
# COPY Cargo.toml Cargo.lock ./
# RUN cargo new --bin app && cd app && cp ../Cargo.toml ../Cargo.lock . && cargo build --release && rm -rf src
# COPY src app/src
# RUN cd app && touch src/main.rs && cargo build --release
#
# FROM alpine:3.19
# RUN apk --no-cache add ca-certificates
# COPY --from=builder /app/app/target/release/app /usr/local/bin/app
# USER 1000
# EXPOSE 8080
# CMD ["app"]
