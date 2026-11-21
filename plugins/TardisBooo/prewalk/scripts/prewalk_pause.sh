#!/usr/bin/env bash
# prewalk · codex host — Stop event (checkpoint detection + v4 state machine).
#
# Codex launches plugin hooks with cwd set to the plugin root and exposes
# PLUGIN_ROOT; when running straight from a checkout neither is guaranteed,
# so fall back to the wrapper's own location (scripts/ → plugin root).
set -euo pipefail

ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

exec python3 "$ROOT/hooks/pause_detect.py"
