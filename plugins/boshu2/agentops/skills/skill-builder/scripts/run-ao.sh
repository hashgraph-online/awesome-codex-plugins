#!/usr/bin/env bash
# Thin source-aware launcher: development checks use the current Go subject.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
if [[ -n "${AO_SKILL_BUILDER_BIN:-}" ]]; then
  exec "$AO_SKILL_BUILDER_BIN" "$@"
fi
if [[ -f "$SOURCE_ROOT/cli/go.mod" ]]; then
  # go run collapses a child exit 2 to exit 1; execute a temporary build so the
  # compatibility entrypoints preserve the actual command status.
  build_dir="$(mktemp -d)"
  trap 'rm -rf "$build_dir"' EXIT
  # Build in the module without changing how caller-relative inputs resolve.
  (cd "$SOURCE_ROOT/cli" && go build -o "$build_dir/ao" ./cmd/ao)
  "$build_dir/ao" "$@"
  exit $?
fi
exec ao "$@"
