#!/usr/bin/env bash
# prewalk · codex host — spawn_agent lifecycle (route check, executor
# binding, completion) plus SubagentStop. Root resolution mirrors
# prewalk_pause.sh: PLUGIN_ROOT first, else ../.
set -euo pipefail

ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

exec python3 "$ROOT/hooks/executor_router.py"
