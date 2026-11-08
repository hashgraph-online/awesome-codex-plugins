#!/usr/bin/env bash
# stack-detect.sh - Print every supported stack present in the current directory.
# Prints one of: node, rust, python. Exits 1 when none is supported.

set -euo pipefail

found=0

if [ -e package.json ]; then
  echo "node"
  found=1
fi
if [ -e Cargo.toml ]; then
  echo "rust"
  found=1
fi
for manifest in pyproject.toml requirements.txt setup.py Pipfile poetry.lock; do
  if [ -e "$manifest" ]; then
    echo "python"
    found=1
    break
  fi
done

if [ "$found" -eq 0 ]; then
  echo "Error: No supported stack detected (node/rust/python)" >&2
  exit 1
fi
