#!/usr/bin/env bash
# pm-detect.sh - Detect the Node package manager from lock files.
# Output: bun | pnpm | yarn | npm. Exits 1 when no package.json is present.

set -euo pipefail

if [ -e bun.lock ] || [ -e bun.lockb ]; then
  echo "bun"
elif [ -e pnpm-lock.yaml ]; then
  echo "pnpm"
elif [ -e yarn.lock ]; then
  echo "yarn"
elif [ -e package-lock.json ]; then
  echo "npm"
elif [ -e package.json ]; then
  echo "Warning: No lock file found, defaulting to npm" >&2
  echo "npm"
else
  echo "Error: No package.json found" >&2
  exit 1
fi
