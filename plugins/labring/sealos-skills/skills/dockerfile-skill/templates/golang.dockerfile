# syntax=docker/dockerfile:1.4

# ============================================
# Stage 1: Build
# ============================================
FROM golang:1.21.6-alpine AS build

WORKDIR /app

# Install git for private modules (if needed)
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies with cache mount
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Copy source code
COPY . .

# Build static binary
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o main .

# ============================================
# Stage 2: Runtime
# ============================================
FROM alpine:3.19 AS runtime

WORKDIR /app

# Install CA certificates for HTTPS
RUN apk --no-cache add ca-certificates tzdata

# Set environment variables
ENV PORT=8080
ENV GIN_MODE=release

# Copy binary from build stage
COPY --from=build /app/main .

# Copy static/config files if needed
# COPY --from=build /app/config ./config
# COPY --from=build /app/templates ./templates

# Create non-root user
RUN adduser -D -u 1000 appuser
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/health || exit 1

# Start application
CMD ["./main"]

# ============================================
# Alternative: Scratch image (smallest possible)
# Use only for fully static binaries
# ============================================
# FROM scratch AS runtime-scratch
#
# WORKDIR /app
#
# COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# COPY --from=build /app/main .
#
# USER 1000:1000
#
# EXPOSE 8080
#
# CMD ["./main"]
