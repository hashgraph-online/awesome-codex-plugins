#!/usr/bin/env bash
# recover.sh — autonomous cass recovery, no user prompt required
#
# Decision tree:
#   1) If healthy: exit 0
#   2) If stale-but-usable: refresh in background, exit 0
#   3) If broken: doctor --fix, then verify
#   4) If still broken after fix: print actionable diagnostic and exit 1
#
# Used by: PreToolUse hooks before cass search; cron pre-flight; agent loops.
#
# Safe by default. Never touches source session files.

set -uo pipefail
# NOT -e: a non-zero exit from cass/jq is informational, not fatal — we want
# to fall through to the next recovery step rather than abort silently.

# Unique log files so concurrent agents don't clobber each other.
REFRESH_LOG=$(mktemp /tmp/cass-refresh.XXXXXX) || { echo "BROKEN: could not create refresh log" >&2; exit 2; }
REBUILD_LOG=$(mktemp /tmp/cass-rebuild.XXXXXX) || { echo "BROKEN: could not create rebuild log" >&2; exit 2; }

# Wall-clock caps. cass index has been observed to hang (see issue #196 and
# the limit-0 freeze); without these the script itself becomes the symptom.
STATUS_TIMEOUT="${CASS_STATUS_TIMEOUT:-15}"          # status / doctor / diag
REBUILD_TIMEOUT="${CASS_REBUILD_TIMEOUT:-900}"       # 15 min — covers ~1M-msg corpora

# Run cass binary check up front; if missing, fail loudly with a useful message.
if ! command -v cass >/dev/null 2>&1; then
  echo "BROKEN: cass binary not on PATH" >&2
  exit 2
fi
if ! command -v timeout >/dev/null 2>&1; then
  echo "BROKEN: GNU 'timeout' not on PATH (install coreutils; on macOS: brew install coreutils + use gtimeout)" >&2
  exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "BROKEN: 'jq' not on PATH" >&2
  exit 2
fi

cass_state() {
  # Always emits 5 tab-separated values, even when cass times out or returns garbage.
  local out
  out=$(timeout "$STATUS_TIMEOUT" cass status --json 2>/dev/null) || out=""
  if [ -z "$out" ]; then
    printf 'false\tfalse\t0\t0\t\n'
    return
  fi
  printf '%s' "$out" \
    | jq -r '[
        (.index.fresh // false),
        (.database.exists // false),
        (.index.documents // 0),
        (.database.messages // 0),
        (.recommended_action // "")
      ] | @tsv' 2>/dev/null \
    || printf 'false\tfalse\t0\t0\t\n'
}

# Read state once. Use || true so an empty stream doesn't trip downstream.
state_line=$(cass_state)
IFS=$'\t' read -r FRESH DB_EXISTS DOCS MSGS REC <<< "$state_line" || true
FRESH=${FRESH:-false}
DB_EXISTS=${DB_EXISTS:-false}
DOCS=${DOCS:-0}
MSGS=${MSGS:-0}

case "$FRESH:$DB_EXISTS" in
  true:*)
    echo "READY: index fresh" >&2
    exit 0
    ;;
  false:true)
    if [ "$DOCS" != "0" ] && [ "$MSGS" != "0" ]; then
      echo "STALE_BUT_USABLE: refreshing in background (log: $REFRESH_LOG, hint: ${REC:-none})" >&2
      # Detached refresh that can't hang forever. Use setsid when available
      # (Linux/util-linux); on macOS without coreutils-setsid the inner
      # subshell + nohup-equivalent (`</dev/null` + `&` + parent exit) still
      # orphans the child to init and survives our exit.
      if command -v setsid >/dev/null 2>&1; then
        ( setsid timeout "$REBUILD_TIMEOUT" cass index --json >"$REFRESH_LOG" 2>&1 </dev/null & ) 2>/dev/null
      else
        ( trap '' HUP; timeout "$REBUILD_TIMEOUT" cass index --json >"$REFRESH_LOG" 2>&1 </dev/null & ) 2>/dev/null
      fi
      exit 0
    fi
    ;;
esac

# Got here = broken or empty index with non-empty DB
echo "RECOVERING: doctor --fix --json" >&2
# Doctor exits 0 even when checks fail — never abort on its exit code.
# Cap wall time to avoid hanging on a degraded DB.
doctor_json=$(timeout "$REBUILD_TIMEOUT" cass doctor --fix --json 2>/dev/null || true)
if [ -n "$doctor_json" ]; then
  printf '%s' "$doctor_json" \
    | jq -c '{healthy, status, fixed: .auto_fix_actions, issues_found, issues_fixed,
              failures: [.checks[]? | select(.status=="fail") | .name]}' >&2 \
    || echo '{"warning":"doctor output not parseable as JSON"}' >&2
else
  echo '{"warning":"doctor produced no output"}' >&2
fi

# Verify
state_line=$(cass_state)
IFS=$'\t' read -r FRESH DB_EXISTS DOCS MSGS REC <<< "$state_line" || true

if [ "${DB_EXISTS:-false}" = "true" ] && [ "${DOCS:-0}" != "0" ]; then
  echo "RECOVERED: doctor succeeded" >&2
  exit 0
fi

# Last resort: full force rebuild (workaround for OPEN issue #196).
# `timeout` here is critical — `cass index --full` has been observed to hang
# indefinitely under contention. Treat exit 124 (timeout) as a definite failure.
echo "ESCALATING: cass index --full --force-rebuild --json (log: $REBUILD_LOG, cap: ${REBUILD_TIMEOUT}s)" >&2
timeout "$REBUILD_TIMEOUT" cass index --full --force-rebuild --json >"$REBUILD_LOG" 2>&1
rebuild_rc=$?
case "$rebuild_rc" in
  124) echo "  ! rebuild hit ${REBUILD_TIMEOUT}s timeout (likely issue #196)" >&2 ;;
  0)   : ;;
  *)   echo "  ! rebuild exited $rebuild_rc (data may still be partially committed)" >&2 ;;
esac

# Even on exit 0 the JSON may report success:false (the last_indexed_at race
# documented in coding_agent_session_search-zz8ni). Always verify by re-reading state.
state_line=$(cass_state)
IFS=$'\t' read -r FRESH DB_EXISTS DOCS MSGS REC <<< "$state_line" || true
if [ "${DB_EXISTS:-false}" = "true" ] && [ "${DOCS:-0}" != "0" ]; then
  echo "RECOVERED: index is queryable (fresh marker may still be stale; that's harmless)" >&2
  exit 0
fi

# Genuinely stuck — surface for human (compact JSON only, not the verbose log spam)
echo "BROKEN: cass cannot self-recover" >&2
echo "Diagnostic (cass diag --json):" >&2
timeout "$STATUS_TIMEOUT" cass diag --json 2>/dev/null | jq -c '{paths, database, index, version}' >&2 || true
echo "Last index attempt log: $REBUILD_LOG (tail):" >&2
tail -n 5 "$REBUILD_LOG" 2>/dev/null >&2 || true
exit 1
