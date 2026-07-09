#!/usr/bin/env bash
# multi_agent_safety.sh — wrap an rch fleet/setup operation in a host-local lock
# so concurrent agents on the same host don't race destructively.
#
# Usage:
#   ./multi_agent_safety.sh rch fleet deploy --canary 25 --canary-wait 60 --verify
#   ./multi_agent_safety.sh rch workers setup --all
#   ./multi_agent_safety.sh rch workers deploy-binary --all
#   ./multi_agent_safety.sh rch update --fleet
#
# Behavior:
#   - Acquires an exclusive flock on $XDG_RUNTIME_DIR/rch/fleet_op.lock (or /tmp fallback)
#   - Holds the lock for the duration of the wrapped command
#   - Times out after 600s waiting; bails with a clear message if another agent holds it
#   - Logs the start/end + holder PID so concurrent agents can see who's blocking them
#
# This complements (does not replace) Agent Mail file_reservation_paths and
# build slots. For multi-machine coordination, use Agent Mail too.

set -euo pipefail

if [[ $# -eq 0 ]]; then
  sed -n '2,/^# This complements/p' "$0" | sed 's/^# \?//'; exit 0
fi

LOCK_DIR="${XDG_RUNTIME_DIR:-/tmp}/rch"
mkdir -p "$LOCK_DIR"
LOCK="$LOCK_DIR/fleet_op.lock"
LOG="$LOCK_DIR/fleet_op.log"

require() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 127; }; }
require flock

# Pre-check: who currently holds the lock?
current_holder() {
  if [[ -f "$LOCK" ]]; then
    local pid
    pid="$(fuser "$LOCK" 2>/dev/null | tr -d ' ' || true)"
    [[ -n "$pid" ]] && ps -p "$pid" -o user=,pid=,cmd= 2>/dev/null
  fi
}

HOLDER="$(current_holder || true)"
if [[ -n "$HOLDER" ]]; then
  printf '[multi_agent_safety] another agent holds %s:\n  %s\n' "$LOCK" "$HOLDER"
  printf '[multi_agent_safety] waiting up to 600s...\n'
fi

START_EPOCH=$(date +%s)
{
  flock --exclusive --timeout 600 9 || {
    echo "[multi_agent_safety] timed out waiting on lock $LOCK" >&2
    exit 75
  }
  printf '[%s] PID=%d started: %s\n' "$(date -Is)" "$$" "$*" >> "$LOG"
  printf '[multi_agent_safety] lock acquired; running: %s\n' "$*"
  EXIT=0
  "$@" || EXIT=$?
  printf '[%s] PID=%d done (exit=%d, %ds): %s\n' \
    "$(date -Is)" "$$" "$EXIT" "$(($(date +%s) - START_EPOCH))" "$*" >> "$LOG"
  exit "$EXIT"
} 9>>"$LOCK"
