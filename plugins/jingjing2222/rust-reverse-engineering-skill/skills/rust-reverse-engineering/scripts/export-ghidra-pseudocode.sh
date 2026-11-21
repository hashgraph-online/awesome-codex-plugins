#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: export-ghidra-pseudocode.sh [OPTIONS] <binary> <output-dir>

Run Ghidra headless analysis and export decompiler pseudocode artifacts.

Arguments:
  <binary>                Native target to import into Ghidra
  <output-dir>            Destination directory, typically .../decompiled/ghidra

Options:
  --max-functions N       Limit exported functions (default: all)
  --timeout SECONDS       Per-function decompile timeout (default: 60)
  --macho-arch ARCH       Select a specific universal Mach-O slice before import
  --progress-interval N   Print progress heartbeat every N seconds (default: 30)
  -h, --help              Show this help message
EOF
  exit 0
}

pick_tool() {
  for tool in "$@"; do
    if command -v "$tool" >/dev/null 2>&1; then
      echo "$tool"
      return 0
    fi
  done
  return 1
}

MAX_FUNCTIONS=0
TIMEOUT_SECONDS=60
MACHO_ARCH=""
PROGRESS_INTERVAL_SECONDS=30
TARGET=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-functions)
      MAX_FUNCTIONS="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --macho-arch)
      MACHO_ARCH="$2"
      shift 2
      ;;
    --progress-interval)
      PROGRESS_INTERVAL_SECONDS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    -*)
      echo "Error: unknown option $1" >&2
      usage
      ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"
      elif [[ -z "$OUTPUT_DIR" ]]; then
        OUTPUT_DIR="$1"
      else
        echo "Error: unexpected argument $1" >&2
        usage
      fi
      shift
      ;;
  esac
done

if [[ -z "$TARGET" || -z "$OUTPUT_DIR" ]]; then
  echo "Error: target and output directory are required." >&2
  usage
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Error: target does not exist: $TARGET" >&2
  exit 2
fi

ANALYZE_HEADLESS="$(pick_tool analyzeHeadless || true)"
if [[ -z "$ANALYZE_HEADLESS" ]]; then
  echo "Error: analyzeHeadless not found in PATH." >&2
  exit 127
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GHIDRA_SCRIPT_DIR="$SCRIPT_DIR/ghidra"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/macho-slice.sh"

mkdir -p "$OUTPUT_DIR"

macho_resolve_target "$TARGET" "$MACHO_ARCH" "$OUTPUT_DIR/input"
ANALYSIS_TARGET="$MACHO_ANALYSIS_TARGET"
macho_write_metadata "$OUTPUT_DIR/analysis-target.txt"

if [[ "$ANALYSIS_TARGET" != "$TARGET" ]]; then
  echo "INFO: selected Mach-O slice $MACHO_SELECTED_ARCH_TOKEN -> $ANALYSIS_TARGET"
fi

PROJECT_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ghidra-rust-reverse.XXXXXX")"
PROJECT_NAME="rust_reverse_headless"
SCRIPT_LOG="$OUTPUT_DIR/script.log"
HEADLESS_LOG="$OUTPUT_DIR/headless.log"
STATUS_FILE="$OUTPUT_DIR/status.txt"
RUNNER_STATUS_FILE="$OUTPUT_DIR/runner-status.txt"
SUMMARY_FILE="$OUTPUT_DIR/summary.txt"
COMPLETE_MARKER="$OUTPUT_DIR/complete.marker"
FAILED_MARKER="$OUTPUT_DIR/failed.marker"
INTERRUPTED_MARKER="$OUTPUT_DIR/interrupted.marker"
ANALYZE_PID=""
RUNNER_PHASE="launching"

rm -f "$COMPLETE_MARKER" "$FAILED_MARKER" "$INTERRUPTED_MARKER"
cat > "$STATUS_FILE" <<EOF
STATE: launching
STARTED_AT: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
LAST_UPDATE_AT: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMPLETED_AT:
FUNCTIONS_PROCESSED: 0
PSEUDOCODE_FILES_WRITTEN: 0
DECOMPILATION_FAILURES: 0
DECOMPILATION_TIMEOUTS: 0
DECOMPILATION_CANCELLED: 0
LAST_FUNCTION_ENTRY:
LAST_FUNCTION_NAME:
LAST_ERROR:
EOF

file_mtime_epoch() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "0"
    return 0
  fi
  if stat -f %m "$path" >/dev/null 2>&1; then
    stat -f %m "$path" 2>/dev/null || echo "0"
  else
    stat -c %Y "$path" 2>/dev/null || echo "0"
  fi
}

write_runner_status() {
  local status_state processed written failed timeouts cancelled last_name last_error
  local heartbeat_at heartbeat_epoch process_alive log_bytes log_mtime phase

  status_state="$(sed -n 's/^STATE: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  processed="$(sed -n 's/^FUNCTIONS_PROCESSED: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  written="$(sed -n 's/^PSEUDOCODE_FILES_WRITTEN: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  failed="$(sed -n 's/^DECOMPILATION_FAILURES: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  timeouts="$(sed -n 's/^DECOMPILATION_TIMEOUTS: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  cancelled="$(sed -n 's/^DECOMPILATION_CANCELLED: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  last_name="$(sed -n 's/^LAST_FUNCTION_NAME: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  last_error="$(sed -n 's/^LAST_ERROR: //p' "$STATUS_FILE" 2>/dev/null | head -1)"

  if [[ -n "$ANALYZE_PID" ]] && kill -0 "$ANALYZE_PID" >/dev/null 2>&1; then
    process_alive="yes"
  else
    process_alive="no"
  fi

  phase="$RUNNER_PHASE"
  if [[ "$status_state" == "completed" ]]; then
    phase="completed"
  elif [[ "$status_state" == "failed" ]]; then
    phase="failed"
  elif [[ "$status_state" == "interrupted" ]]; then
    phase="interrupted"
  elif [[ "$status_state" == "running" || "${processed:-0}" != "0" || "${written:-0}" != "0" ]]; then
    phase="decompiling"
  fi

  heartbeat_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  heartbeat_epoch="$(date +%s)"
  if [[ -f "$HEADLESS_LOG" ]]; then
    log_bytes="$(wc -c < "$HEADLESS_LOG" 2>/dev/null | tr -d ' ' || echo 0)"
  else
    log_bytes="0"
  fi
  log_mtime="$(file_mtime_epoch "$HEADLESS_LOG")"

  cat > "$RUNNER_STATUS_FILE" <<EOF
RUNNER_HEARTBEAT_AT: $heartbeat_at
RUNNER_HEARTBEAT_EPOCH: $heartbeat_epoch
RUNNER_PID: $$
ANALYZE_PID: ${ANALYZE_PID:-}
PROCESS_ALIVE: $process_alive
RUNNER_PHASE: $phase
HEARTBEAT_TIMEOUT_SECONDS: $((PROGRESS_INTERVAL_SECONDS * 3))
HEADLESS_LOG_BYTES: ${log_bytes:-0}
HEADLESS_LOG_MTIME_EPOCH: ${log_mtime:-0}
STATUS_STATE: ${status_state:-}
FUNCTIONS_PROCESSED: ${processed:-0}
PSEUDOCODE_FILES_WRITTEN: ${written:-0}
DECOMPILATION_FAILURES: ${failed:-0}
DECOMPILATION_TIMEOUTS: ${timeouts:-0}
DECOMPILATION_CANCELLED: ${cancelled:-0}
LAST_FUNCTION_NAME: ${last_name:-}
LAST_ERROR: ${last_error:-}
EOF
}

write_runner_status

mark_interrupted() {
  if [[ -n "$ANALYZE_PID" ]]; then
    kill -TERM "$ANALYZE_PID" >/dev/null 2>&1 || true
  fi
  RUNNER_PHASE="interrupted"
  cat > "$STATUS_FILE" <<EOF
STATE: interrupted
STARTED_AT: $(sed -n 's/^STARTED_AT: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_UPDATE_AT: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMPLETED_AT:
FUNCTIONS_PROCESSED: $(sed -n 's/^FUNCTIONS_PROCESSED: //p' "$STATUS_FILE" 2>/dev/null | head -1)
PSEUDOCODE_FILES_WRITTEN: $(sed -n 's/^PSEUDOCODE_FILES_WRITTEN: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_FAILURES: $(sed -n 's/^DECOMPILATION_FAILURES: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_TIMEOUTS: $(sed -n 's/^DECOMPILATION_TIMEOUTS: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_CANCELLED: $(sed -n 's/^DECOMPILATION_CANCELLED: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_FUNCTION_ENTRY: $(sed -n 's/^LAST_FUNCTION_ENTRY: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_FUNCTION_NAME: $(sed -n 's/^LAST_FUNCTION_NAME: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_ERROR: interrupted by shell signal
EOF
  : > "$INTERRUPTED_MARKER"
  write_runner_status
}

cleanup() {
  rm -rf "$PROJECT_ROOT"
}
trap cleanup EXIT
trap 'mark_interrupted; exit 130' INT TERM

summarize_headless_warnings() {
  local warnings_file="$OUTPUT_DIR/warning-summary.txt"
  local raw_matches="$OUTPUT_DIR/.constructor-warnings.tsv"
  local total_pcode_errors
  local constructor_warnings
  local top_function
  local top_function_count
  local top_address
  local top_address_count

  if [[ ! -f "$HEADLESS_LOG" ]]; then
    return 0
  fi

  total_pcode_errors="$(grep -c 'pcode error' "$HEADLESS_LOG" 2>/dev/null || true)"
  constructor_warnings="$(grep -c 'Unable to resolve constructor' "$HEADLESS_LOG" 2>/dev/null || true)"

  grep 'Unable to resolve constructor' "$HEADLESS_LOG" 2>/dev/null \
    | sed -E 's/.*Decompiling ([^,]+), pcode error at ([^:]+):.*/\1\t\2/' > "$raw_matches" || true

  top_function=""
  top_function_count="0"
  top_address=""
  top_address_count="0"

  if [[ -s "$raw_matches" ]]; then
    top_function="$(awk -F'\t' '{count[$1]++} END {for (k in count) print count[k] "\t" k}' "$raw_matches" | sort -nr | head -1 | awk '{print $2}')"
    top_function_count="$(awk -F'\t' -v func="$top_function" '$1 == func {count++} END {print count+0}' "$raw_matches")"
    top_address="$(awk -F'\t' -v func="$top_function" '$1 == func {count[$2]++} END {for (k in count) print count[k] "\t" k}' "$raw_matches" | sort -nr | head -1 | awk '{print $2}')"
    top_address_count="$(awk -F'\t' -v func="$top_function" -v addr="$top_address" '$1 == func && $2 == addr {count++} END {print count+0}' "$raw_matches")"
  fi

  {
    echo "TOTAL_PCODE_ERRORS: ${total_pcode_errors:-0}"
    echo "CONSTRUCTOR_RESOLVE_WARNINGS: ${constructor_warnings:-0}"
    echo "TOP_CONSTRUCTOR_WARNING_FUNCTION: ${top_function:-}"
    echo "TOP_CONSTRUCTOR_WARNING_FUNCTION_COUNT: ${top_function_count:-0}"
    echo "TOP_CONSTRUCTOR_WARNING_ADDRESS: ${top_address:-}"
    echo "TOP_CONSTRUCTOR_WARNING_ADDRESS_COUNT: ${top_address_count:-0}"
    echo
    echo "TOP_CONSTRUCTOR_WARNING_FUNCTIONS:"
    if [[ -s "$raw_matches" ]]; then
      awk -F'\t' '{count[$1]++} END {for (k in count) print count[k] "\t" k}' "$raw_matches" \
        | sort -nr \
        | head -20 \
        | awk '{printf "FUNCTION: %s\tCOUNT: %s\n", $2, $1}'
      if [[ -n "$top_function" ]]; then
        echo
        echo "TOP_CONSTRUCTOR_WARNING_ADDRESSES_FOR_${top_function}:"
        awk -F'\t' -v func="$top_function" '$1 == func {count[$2]++} END {for (k in count) print count[k] "\t" k}' "$raw_matches" \
          | sort -nr \
          | head -20 \
          | awk '{printf "ADDRESS: %s\tCOUNT: %s\n", $2, $1}'
      fi
    else
      echo "(none)"
    fi
  } > "$warnings_file"

  rm -f "$raw_matches"
}

print_progress() {
  local state processed written failed timeouts cancelled last_name last_error
  state="$(sed -n 's/^STATE: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  processed="$(sed -n 's/^FUNCTIONS_PROCESSED: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  written="$(sed -n 's/^PSEUDOCODE_FILES_WRITTEN: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  failed="$(sed -n 's/^DECOMPILATION_FAILURES: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  timeouts="$(sed -n 's/^DECOMPILATION_TIMEOUTS: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  cancelled="$(sed -n 's/^DECOMPILATION_CANCELLED: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  last_name="$(sed -n 's/^LAST_FUNCTION_NAME: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
  last_error="$(sed -n 's/^LAST_ERROR: //p' "$STATUS_FILE" 2>/dev/null | head -1)"

  echo "PROGRESS: state=${state:-unknown} processed=${processed:-0} written=${written:-0} failures=${failed:-0} timeouts=${timeouts:-0} cancelled=${cancelled:-0} last_function=${last_name:-} last_error=${last_error:-}"
}

echo "INFO: launching Ghidra headless export"

set +e
"$ANALYZE_HEADLESS" \
  "$PROJECT_ROOT" \
  "$PROJECT_NAME" \
  -import "$ANALYSIS_TARGET" \
  -overwrite \
  -scriptPath "$GHIDRA_SCRIPT_DIR" \
  -postScript ExportRustPseudocode.java "$OUTPUT_DIR" "$MAX_FUNCTIONS" "$TIMEOUT_SECONDS" \
  -scriptlog "$SCRIPT_LOG" \
  -log "$HEADLESS_LOG" \
  -analysisTimeoutPerFile 1800 \
  -deleteProject &
ANALYZE_PID=$!
RUNNER_PHASE="analyzing"
write_runner_status

while kill -0 "$ANALYZE_PID" >/dev/null 2>&1; do
  sleep "$PROGRESS_INTERVAL_SECONDS"
  if kill -0 "$ANALYZE_PID" >/dev/null 2>&1; then
    write_runner_status
    print_progress
  fi
done

wait "$ANALYZE_PID"
rc=$?
set -e

summarize_headless_warnings

if [[ "$rc" -ne 0 ]]; then
  RUNNER_PHASE="failed"
  if [[ ! -f "$FAILED_MARKER" && ! -f "$INTERRUPTED_MARKER" ]]; then
    cat > "$STATUS_FILE" <<EOF
STATE: failed
STARTED_AT: $(sed -n 's/^STARTED_AT: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_UPDATE_AT: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMPLETED_AT:
FUNCTIONS_PROCESSED: $(sed -n 's/^FUNCTIONS_PROCESSED: //p' "$STATUS_FILE" 2>/dev/null | head -1)
PSEUDOCODE_FILES_WRITTEN: $(sed -n 's/^PSEUDOCODE_FILES_WRITTEN: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_FAILURES: $(sed -n 's/^DECOMPILATION_FAILURES: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_TIMEOUTS: $(sed -n 's/^DECOMPILATION_TIMEOUTS: //p' "$STATUS_FILE" 2>/dev/null | head -1)
DECOMPILATION_CANCELLED: $(sed -n 's/^DECOMPILATION_CANCELLED: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_FUNCTION_ENTRY: $(sed -n 's/^LAST_FUNCTION_ENTRY: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_FUNCTION_NAME: $(sed -n 's/^LAST_FUNCTION_NAME: //p' "$STATUS_FILE" 2>/dev/null | head -1)
LAST_ERROR: analyzeHeadless exited with status $rc
EOF
    : > "$FAILED_MARKER"
  fi
  write_runner_status
  exit "$rc"
fi

if [[ -f "$COMPLETE_MARKER" && -f "$SUMMARY_FILE" ]]; then
  RUNNER_PHASE="completed"
  write_runner_status
  print_progress
  echo "INFO: Ghidra export completed successfully"
  exit 0
fi

state="$(sed -n 's/^STATE: //p' "$STATUS_FILE" 2>/dev/null | head -1)"
if [[ -z "$state" ]]; then
  state="failed"
fi

RUNNER_PHASE="$state"
write_runner_status
print_progress
echo "Error: Ghidra export exited without a completion marker (state: $state)." >&2
if [[ -f "$STATUS_FILE" ]]; then
  echo "Inspect: $STATUS_FILE" >&2
fi
if [[ -f "$SUMMARY_FILE" ]]; then
  echo "Partial summary: $SUMMARY_FILE" >&2
fi
exit 1
