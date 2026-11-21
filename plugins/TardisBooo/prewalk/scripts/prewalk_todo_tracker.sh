#!/usr/bin/env bash
# prewalk · codex host — PostToolUse on update_plan|todo (plan snapshots).
# Root resolution mirrors prewalk_pause.sh: PLUGIN_ROOT first, else ../.
set -euo pipefail

ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

exec python3 "$ROOT/hooks/todo_tracker.py"
