#!/usr/bin/env bash
set -euo pipefail

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo was not found on PATH" >&2
  exit 127
fi

if [ ! -f Cargo.toml ]; then
  echo "run this script from a Rust crate or workspace root containing Cargo.toml" >&2
  exit 2
fi

cargo fmt --all --check

if [ "${RUST_API_TEST_HARNESS_SKIP_CLIPPY:-0}" != "1" ]; then
  cargo clippy --all-targets --all-features -- -D warnings
fi

cargo test --all-features
