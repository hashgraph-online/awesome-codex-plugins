#!/usr/bin/env bash
# deploy-check.sh - Full pre-deploy proof: quality checks plus the build phase.
# Usage: deploy-check.sh [--parallel|--sequential]
# Environment: PRE_DEPLOY_MODE=parallel|sequential (default: parallel)
# Exit codes: 0 all executed checks passed, 1 a check failed, 2 no check executed, 64 usage error

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
LINT_CHECK="$SCRIPT_DIR/lint-check.sh"
BUILD_RUN="$SCRIPT_DIR/build-run.sh"
STACK_DETECT="$SCRIPT_DIR/stack-detect.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pre-deploy-check.XXXXXX")"
STOP_NEW_WORK=0
REQUESTED_SIGNAL=""

CHILD_PIDS=()
CHILD_LOGS=()
CHILD_COUNT=0

cleanup() {
  if [ -n "$TMP_ROOT" ] && [ -d "$TMP_ROOT" ]; then
    rm -rf "$TMP_ROOT"
  fi
}

# Invoked from the trap handlers below, which shellcheck cannot see.
# shellcheck disable=SC2329
on_signal() {
  signal_name="$1"
  if [ -z "$REQUESTED_SIGNAL" ]; then
    REQUESTED_SIGNAL="$signal_name"
  fi
  STOP_NEW_WORK=1
  # Bash starts asynchronous children with SIGINT ignored, so a forwarded INT
  # never reaches them; TERM does, and it terminates children whether they trap
  # it or take the default action. The parent still re-raises the original
  # signal after reaping its children.
  forward_signal="$signal_name"
  if [ "$forward_signal" = "INT" ]; then
    forward_signal="TERM"
  fi
  index=0
  while [ "$index" -lt "$CHILD_COUNT" ]; do
    kill -s "$forward_signal" "${CHILD_PIDS[$index]}" 2>/dev/null || true
    index=$((index + 1))
  done
}

trap cleanup EXIT
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

# Start a child with stdout and stderr merged into one log, preserving their order.
# Returns 1 without spawning once a signal has arrived.
spawn_child() {
  if [ "$STOP_NEW_WORK" -eq 1 ]; then
    return 1
  fi
  child_log="$TMP_ROOT/child-$CHILD_COUNT.log"
  : > "$child_log"
  bash "$1" > "$child_log" 2>&1 &
  CHILD_PIDS[CHILD_COUNT]=$!
  CHILD_LOGS[CHILD_COUNT]="$child_log"
  CHILD_COUNT=$((CHILD_COUNT + 1))
  return 0
}

# Wait for one spawned child; sets CHILD_STATUS.
collect_child() {
  child_status=0
  wait "${CHILD_PIDS[$1]}" || child_status=$?
  CHILD_STATUS=$child_status
}

coverage() {
  awk '
    /^PRE_DEPLOY_SUMMARY executed=[0-9][0-9]* skipped=[0-9][0-9]*$/ {
      rest = $0
      sub(/^PRE_DEPLOY_SUMMARY executed=/, "", rest)
      split(rest, parts, " skipped=")
      executed += parts[1]
      skipped += parts[2]
    }
    END { printf "%d %d\n", executed + 0, skipped + 0 }
  ' "$1" "$2"
}

main() {
  mode="${PRE_DEPLOY_MODE-parallel}"
  argument="${1:-}"
  case "$argument" in
    --sequential)
      mode=sequential
      ;;
    --parallel | "")
      ;;
    -h | --help)
      echo "Usage: deploy-check.sh [--parallel|--sequential]"
      echo "Environment: PRE_DEPLOY_MODE=parallel|sequential (default: parallel)"
      echo "Exit codes: 0 all executed checks passed, 1 a check failed, 2 no check executed, 64 usage error"
      return 0
      ;;
    *)
      echo "Error: unknown argument: $argument" >&2
      return 64
      ;;
  esac
  if [ "$mode" != "parallel" ] && [ "$mode" != "sequential" ]; then
    echo "Error: PRE_DEPLOY_MODE must be parallel or sequential" >&2
    return 64
  fi
  echo "=========================================="
  echo "  Pre-Deploy Verification"
  echo "=========================================="
  if [ ! -e "$LINT_CHECK" ]; then
    echo "Error: lint-check.sh not found or not executable" >&2
    return 1
  fi
  if [ ! -e "$BUILD_RUN" ]; then
    echo "Error: build-run.sh not found or not executable" >&2
    return 1
  fi
  if [ ! -e "$STACK_DETECT" ]; then
    echo "Error: stack-detect.sh not found or not executable" >&2
    return 1
  fi
  lint_code=0
  build_code=0
  if [ "$mode" = "sequential" ]; then
    printf '\n[1/2] Running quality checks...\n'
    spawn_child "$LINT_CHECK" || return 1
    collect_child 0
    lint_code="$CHILD_STATUS"
    cat "${CHILD_LOGS[0]}"
    if [ "$lint_code" -ne 0 ]; then
      return 1
    fi
    if [ "$STOP_NEW_WORK" -eq 1 ]; then
      return 1
    fi
    printf '\n[2/2] Running build phase...\n'
    spawn_child "$BUILD_RUN" || return 1
    collect_child 1
    build_code="$CHILD_STATUS"
    cat "${CHILD_LOGS[1]}"
    if [ "$build_code" -ne 0 ]; then
      return 1
    fi
  else
    printf '\n[1+2/2] Running quality checks and build concurrently...\n'
    spawn_child "$LINT_CHECK" || return 1
    spawn_child "$BUILD_RUN" || return 1
    collect_child 0
    lint_code="$CHILD_STATUS"
    collect_child 1
    build_code="$CHILD_STATUS"
    printf '\n--- Quality checks ---\n'
    cat "${CHILD_LOGS[0]}"
    printf '\n--- Build phase ---\n'
    cat "${CHILD_LOGS[1]}"
    if [ "$lint_code" -ne 0 ] || [ "$build_code" -ne 0 ]; then
      return 1
    fi
  fi
  summary="$(coverage "${CHILD_LOGS[0]}" "${CHILD_LOGS[1]}")"
  executed="${summary%% *}"
  skipped="${summary##* }"
  printf '\nPRE_DEPLOY_SUMMARY executed=%s skipped=%s\n' "$executed" "$skipped"
  if [ "$executed" -eq 0 ]; then
    echo "=========================================="
    echo "  ✗ No check executed - readiness is NOT proven"
    echo "=========================================="
    echo "Nothing was configured or installed to verify. A skipped check is not a pass."
    return 2
  fi
  printf '\n==========================================\n  ✓ All executed checks passed\n==========================================\n'
  if [ "$skipped" -gt 0 ]; then
    echo "Note: $skipped check(s) skipped and not counted as passed."
  fi
  return 0
}

main_status=0
main "${1:-}" || main_status=$?

if [ -n "$REQUESTED_SIGNAL" ]; then
  trap - EXIT INT TERM
  index=0
  while [ "$index" -lt "$CHILD_COUNT" ]; do
    wait "${CHILD_PIDS[$index]}" 2>/dev/null || true
    index=$((index + 1))
  done
  cleanup
  kill -s "$REQUESTED_SIGNAL" $$
fi
exit "$main_status"
