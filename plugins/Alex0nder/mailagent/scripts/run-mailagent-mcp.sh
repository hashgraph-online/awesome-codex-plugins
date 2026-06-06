#!/usr/bin/env bash
# Codex plugin launcher — single entry for stdio MCP (same as Cursor path).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

: "${MAILAGENT_API_KEY:?Set MAILAGENT_API_KEY in env or examples/codex/plugin/.env}"
export MAILAGENT_API_URL="${MAILAGENT_API_URL:-https://api.webmailagent.com}"

exec npx -y -p @mailagent/mcp@0.2.5 mailagent-mcp
