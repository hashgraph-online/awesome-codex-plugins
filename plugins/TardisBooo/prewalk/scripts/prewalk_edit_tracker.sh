#!/usr/bin/env bash
# prewalk · codex host — PostToolUse on edit tools (planner edit budget).
# Root resolution mirrors prewalk_pause.sh: PLUGIN_ROOT first, else ../.
set -euo pipefail

ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

exec python3 "$ROOT/hooks/edit_tracker.py"
