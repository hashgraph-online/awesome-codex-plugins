---
name: rust-deployable-service
description: Use when preparing, containerizing, configuring, testing, or reviewing Rust services for deployment, especially Docker multi-stage builds, runtime configuration, environment overrides, secrets, health checks, SQLx offline builds, release profiles, image-size reduction, or production startup validation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Deployable Service
  category: Rust
  tags: rust,deployment,docker,configuration,sqlx
---

# Rust Deployable Service

Use this skill when a Rust service needs to move from local development to a
repeatable container or cloud deployment. Keep runtime configuration explicit,
builds reproducible, and health checks boring.

## Core Workflow

1. Inspect `Cargo.toml`, workspace layout, `Dockerfile`, `.dockerignore`,
   config files, migrations, `.sqlx/`, CI, and deployment docs.
2. Identify the binary entrypoint and runtime dependencies: database, Redis,
   external APIs, TLS roots, static files, templates, migrations, and config.
3. Separate build-time and runtime configuration. Never bake production secrets
   into images.
4. Use hierarchical config with environment overrides for deployment-specific
   values.
5. Use a multi-stage Docker build and copy only the runtime binary and needed
   assets into the final image.
6. Account for SQLx query checking. Use `SQLX_OFFLINE=true` with checked-in
   `.sqlx/` metadata or provide a build-time database intentionally.
7. Add health and readiness checks that match real dependencies.
8. Run the bundled Docker preflight or the repository's equivalent CI command.

## Configuration Rules

Read `references/configuration.md` when adding config files, environment
variables, or secret handling.

- Keep local defaults convenient and production defaults conservative.
- Validate config at startup before binding the server when possible.
- Store secrets in environment variables or the deployment secret manager.
- Avoid reading environment variables deep inside handlers or repositories.

## Docker Rules

Read `references/docker-rust.md` before changing Docker builds.

- Use dependency caching deliberately; avoid invalidating the whole build on
  every source edit when practical.
- Use `--locked` for release builds if the repo commits `Cargo.lock`.
- Include CA certificates when outbound HTTPS is required.
- Copy migrations, templates, and static assets only if the binary needs them at
  runtime.
- Run as a non-root user when the deployment platform supports it.

## Verification

Run from the Rust project root when Docker is part of the delivery path:

```bash
path/to/rust-deployable-service/scripts/docker-preflight.sh
```

The script builds an image. It only runs a smoke command when
`RUST_DEPLOY_SMOKE_COMMAND` is set, because services often need environment and
infrastructure to start successfully.

## Reference Files

- `references/configuration.md`: typed config loading, overrides, validation,
  and secrets.
- `references/docker-rust.md`: multi-stage builds, SQLx offline builds, runtime
  assets, and image checks.
