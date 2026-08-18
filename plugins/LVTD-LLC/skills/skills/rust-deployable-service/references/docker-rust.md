# Docker For Rust Services

Use multi-stage builds so the final image contains the runtime binary and only
the files it needs.

## Multi-Stage Shape

```dockerfile
FROM rust:1-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release --locked

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/target/release/my-service /usr/local/bin/my-service
CMD ["my-service"]
```

Adapt the base image, binary path, and copied assets to the project.

## SQLx Builds

For SQLx macros in Docker, prefer checked-in offline metadata:

```dockerfile
ENV SQLX_OFFLINE=true
COPY .sqlx ./.sqlx
RUN cargo build --release --locked
```

If the build intentionally connects to a database, make that explicit in CI and
avoid hiding network/database requirements inside the Dockerfile.

## Runtime Assets

Copy only assets the binary reads at runtime:

- `migrations/` if the app runs migrations at startup.
- Templates or static files for server-rendered apps.
- CA certificates for outbound HTTPS.
- Time zone or locale data if required.

## Checks

- Does the image build from a clean checkout?
- Does it start with missing required config and fail clearly?
- Does the health endpoint respond when dependencies are available?
- Is the binary compiled with the expected feature flags?
- Does the final image avoid build tools and source code unless needed?
