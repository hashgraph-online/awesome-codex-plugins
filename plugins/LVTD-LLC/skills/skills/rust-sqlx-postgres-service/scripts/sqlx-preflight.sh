#!/usr/bin/env bash
set -euo pipefail

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo is required" >&2
  exit 127
fi

if [ ! -f Cargo.toml ]; then
  echo "run this script from a Rust project root containing Cargo.toml" >&2
  exit 2
fi

echo "==> cargo fmt"
cargo fmt --all --check

if command -v sqlx >/dev/null 2>&1 && [ -d migrations ]; then
  if [ -d .sqlx ] || [ -n "${DATABASE_URL:-}" ]; then
    echo "==> cargo sqlx prepare --check"
    cargo sqlx prepare --check --workspace
  else
    echo "==> skipping cargo sqlx prepare --check; .sqlx/ and DATABASE_URL are not available"
  fi

  if [ -n "${DATABASE_URL:-}" ]; then
    echo "==> sqlx migrate info"
    sqlx migrate info

    if [ "${RUST_SQLX_PREFLIGHT_RUN_MIGRATIONS:-0}" = "1" ]; then
      echo "==> sqlx migrate run"
      sqlx migrate run
    else
      echo "==> skipping sqlx migrate run; set RUST_SQLX_PREFLIGHT_RUN_MIGRATIONS=1 to apply migrations"
    fi
  else
    echo "==> skipping sqlx migrate info; DATABASE_URL is not set"
  fi
else
  echo "==> skipping sqlx CLI checks; sqlx command or migrations/ directory not found"
fi

echo "==> cargo test"
cargo test --all-features
