#!/usr/bin/env bash
# validator.sh — POSIX wrapper for the vault-sync Phase 1 validator.
#
# Usage:
#   bash validator.sh [VAULT_DIR]
#   VAULT_DIR=/path/to/vault bash validator.sh
#
# Behavior:
#   - Resolves VAULT_DIR from arg 1 or env.
#   - Ensures `node` is available.
#   - Auto-installs deps on first run (pnpm install --silent) if node_modules missing.
#   - Execs validator.mjs; propagates exit code.
#
# Exit codes (mirror validator.mjs):
#   0 — vault valid (or skipped: no vault)
#   1 — validation errors
#   2 — infrastructure error (missing node / pnpm, missing validator.mjs)
#
# Output: JSON report on stdout (machine-readable).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR_MJS="${SCRIPT_DIR}/validator.mjs"

# ── Resolve vault dir ──────────────────────────────────────────────────────
if [[ $# -ge 1 && -n "${1:-}" && "${1:-}" != --* ]]; then
  export VAULT_DIR="$1"
  shift
fi
: "${VAULT_DIR:=$PWD}"

# ── Dependency checks ──────────────────────────────────────────────────────
if ! command -v node >/dev/null 2>&1; then
  echo '{"status":"infra-error","reason":"node not found in PATH"}' >&2
  exit 2
fi

if [[ ! -f "$VALIDATOR_MJS" ]]; then
  echo "{\"status\":\"infra-error\",\"reason\":\"validator.mjs not found at $VALIDATOR_MJS\"}" >&2
  exit 2
fi

# ── Self-bootstrap node_modules on first run ───────────────────────────────
if [[ ! -d "$SCRIPT_DIR/node_modules" ]]; then
  if ! command -v pnpm >/dev/null 2>&1; then
    echo '{"status":"infra-error","reason":"pnpm not found; cannot bootstrap dependencies"}' >&2
    exit 2
  fi
  (cd "$SCRIPT_DIR" && pnpm install --silent) >&2
fi

# ── Execute validator ──────────────────────────────────────────────────────
export VAULT_DIR
exec node "$VALIDATOR_MJS" "$@"
