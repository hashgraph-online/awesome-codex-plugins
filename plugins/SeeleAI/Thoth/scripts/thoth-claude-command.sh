#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export THOTH_CLAUDE_PLUGIN_ROOT="${PLUGIN_ROOT}"

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${PLUGIN_ROOT}:${PYTHONPATH}"
else
  export PYTHONPATH="${PLUGIN_ROOT}"
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi

"${PYTHON_BIN}" "${PLUGIN_ROOT}/thoth/surface/bridges/claude.py" "$@"
