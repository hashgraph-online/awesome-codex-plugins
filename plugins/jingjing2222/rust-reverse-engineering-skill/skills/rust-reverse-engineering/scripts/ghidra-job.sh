#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ghidra-job.sh start [OPTIONS] <binary> <output-dir>
  ghidra-job.sh status <output-dir>
  ghidra-job.sh wait [--poll SECONDS] <output-dir>
  ghidra-job.sh stop <output-dir>

Manage detached Ghidra headless pseudocode export jobs.

Commands:
  start                 Launch export-ghidra-pseudocode.sh under nohup
  status                Print current job and export state
  wait                  Poll until the export reaches a terminal state
  stop                  Stop a detached export job

Start options:
  --max-functions N     Limit exported functions (default: all)
  --timeout SECONDS     Per-function decompile timeout (default: 60)

Wait options:
  --poll SECONDS        Poll interval in seconds (default: 15)
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

status_value() {
  local file="$1"
  local key="$2"
  if [[ -f "$file" ]]; then
    sed -n "s/^${key}: //p" "$file" | head -1
  fi
}

current_epoch() {
  date +%s
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

print_status() {
  local output_dir="$1"
  local pid_file="$output_dir/job.pid"
  local pgid_file="$output_dir/job.pgid"
  local status_file="$output_dir/status.txt"
  local runner_status_file="$output_dir/runner-status.txt"
  local pid=""
  local pgid=""
  local process_alive="no"
  local state="unknown"
  local runner_heartbeat_epoch=""
  local runner_heartbeat_timeout=""
  local runner_heartbeat_age=""
  local runner_heartbeat_stale="unknown"
  local liveness_hint="unknown"
  local now_epoch=""

  if [[ -f "$pid_file" ]]; then
    pid="$(tr -d '[:space:]' < "$pid_file")"
    if is_pid_alive "$pid"; then
      process_alive="yes"
    fi
  fi

  if [[ -f "$pgid_file" ]]; then
    pgid="$(tr -d '[:space:]' < "$pgid_file")"
  fi

  if [[ -f "$output_dir/complete.marker" ]]; then
    state="completed"
  elif [[ -f "$output_dir/failed.marker" ]]; then
    state="failed"
  elif [[ -f "$output_dir/interrupted.marker" ]]; then
    state="interrupted"
  elif [[ -f "$status_file" ]]; then
    state="$(status_value "$status_file" "STATE")"
  fi

  runner_heartbeat_epoch="$(status_value "$runner_status_file" "RUNNER_HEARTBEAT_EPOCH")"
  runner_heartbeat_timeout="$(status_value "$runner_status_file" "HEARTBEAT_TIMEOUT_SECONDS")"
  if [[ -n "$runner_heartbeat_epoch" && -n "$runner_heartbeat_timeout" ]]; then
    now_epoch="$(current_epoch)"
    runner_heartbeat_age="$((now_epoch - runner_heartbeat_epoch))"
    if (( runner_heartbeat_age > runner_heartbeat_timeout )); then
      runner_heartbeat_stale="yes"
    else
      runner_heartbeat_stale="no"
    fi
  fi

  if [[ "$state" == "completed" || "$state" == "failed" || "$state" == "interrupted" ]]; then
    liveness_hint="terminal"
  elif [[ "$process_alive" == "yes" && "$runner_heartbeat_stale" == "no" ]]; then
    liveness_hint="running"
  elif [[ "$process_alive" == "no" && "$runner_heartbeat_stale" == "yes" ]]; then
    liveness_hint="stopped"
  elif [[ "$process_alive" == "yes" && "$runner_heartbeat_stale" == "yes" ]]; then
    liveness_hint="stale-heartbeat-check-runner"
  fi

  cat <<EOF
OUTPUT_DIR: $output_dir
PID: ${pid:-}
PGID: ${pgid:-}
PROCESS_ALIVE: $process_alive
STATE: ${state:-unknown}
STARTED_AT: $(status_value "$status_file" "STARTED_AT")
LAST_UPDATE_AT: $(status_value "$status_file" "LAST_UPDATE_AT")
COMPLETED_AT: $(status_value "$status_file" "COMPLETED_AT")
FUNCTIONS_PROCESSED: $(status_value "$status_file" "FUNCTIONS_PROCESSED")
PSEUDOCODE_FILES_WRITTEN: $(status_value "$status_file" "PSEUDOCODE_FILES_WRITTEN")
DECOMPILATION_FAILURES: $(status_value "$status_file" "DECOMPILATION_FAILURES")
DECOMPILATION_TIMEOUTS: $(status_value "$status_file" "DECOMPILATION_TIMEOUTS")
DECOMPILATION_CANCELLED: $(status_value "$status_file" "DECOMPILATION_CANCELLED")
LAST_FUNCTION_ENTRY: $(status_value "$status_file" "LAST_FUNCTION_ENTRY")
LAST_FUNCTION_NAME: $(status_value "$status_file" "LAST_FUNCTION_NAME")
LAST_ERROR: $(status_value "$status_file" "LAST_ERROR")
STATUS_FILE: $status_file
RUNNER_STATUS_FILE: $runner_status_file
RUNNER_HEARTBEAT_AT: $(status_value "$runner_status_file" "RUNNER_HEARTBEAT_AT")
RUNNER_HEARTBEAT_EPOCH: ${runner_heartbeat_epoch:-}
RUNNER_HEARTBEAT_AGE_SECONDS: ${runner_heartbeat_age:-}
RUNNER_HEARTBEAT_STALE: ${runner_heartbeat_stale:-unknown}
RUNNER_PHASE: $(status_value "$runner_status_file" "RUNNER_PHASE")
RUNNER_PROCESS_ALIVE: $(status_value "$runner_status_file" "PROCESS_ALIVE")
HEARTBEAT_TIMEOUT_SECONDS: $(status_value "$runner_status_file" "HEARTBEAT_TIMEOUT_SECONDS")
LIVENESS_HINT: ${liveness_hint}
HEADLESS_LOG_BYTES: $(status_value "$runner_status_file" "HEADLESS_LOG_BYTES")
HEADLESS_LOG_MTIME_EPOCH: $(status_value "$runner_status_file" "HEADLESS_LOG_MTIME_EPOCH")
LAUNCHER_LOG: $output_dir/launcher.log
HEADLESS_LOG: $output_dir/headless.log
SCRIPT_LOG: $output_dir/script.log
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORT_SCRIPT="$SCRIPT_DIR/export-ghidra-pseudocode.sh"

if [[ $# -lt 1 ]]; then
  usage
fi

COMMAND="$1"
shift

case "$COMMAND" in
  start)
    MAX_FUNCTIONS=0
    TIMEOUT_SECONDS=60
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

    mkdir -p "$OUTPUT_DIR"

    if [[ -f "$OUTPUT_DIR/job.pid" ]]; then
      existing_pid="$(tr -d '[:space:]' < "$OUTPUT_DIR/job.pid")"
      if is_pid_alive "$existing_pid"; then
        echo "Error: export job is already running for $OUTPUT_DIR (pid: $existing_pid)." >&2
        exit 1
      fi
    fi

    LAUNCHER_LOG="$OUTPUT_DIR/launcher.log"
    COMMAND_FILE="$OUTPUT_DIR/job-command.txt"
    STARTED_FILE="$OUTPUT_DIR/job-started-at.txt"
    : > "$LAUNCHER_LOG"

    {
      printf 'bash %q --max-functions %q --timeout %q %q %q\n' \
        "$EXPORT_SCRIPT" "$MAX_FUNCTIONS" "$TIMEOUT_SECONDS" "$TARGET" "$OUTPUT_DIR"
    } > "$COMMAND_FILE"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$STARTED_FILE"

    nohup bash "$EXPORT_SCRIPT" \
      --max-functions "$MAX_FUNCTIONS" \
      --timeout "$TIMEOUT_SECONDS" \
      "$TARGET" \
      "$OUTPUT_DIR" >> "$LAUNCHER_LOG" 2>&1 < /dev/null &

    pid="$!"
    pgid="$(ps -o pgid= -p "$pid" | tr -d '[:space:]' || true)"
    printf '%s\n' "$pid" > "$OUTPUT_DIR/job.pid"
    printf '%s\n' "$pgid" > "$OUTPUT_DIR/job.pgid"

    cat <<EOF
STARTED: yes
OUTPUT_DIR: $OUTPUT_DIR
PID: $pid
PGID: $pgid
STATUS_FILE: $OUTPUT_DIR/status.txt
LAUNCHER_LOG: $LAUNCHER_LOG
EOF
    ;;

  status)
    if [[ $# -ne 1 ]]; then
      echo "Error: status requires <output-dir>." >&2
      usage
    fi
    print_status "$1"
    ;;

  wait)
    POLL_SECONDS=15
    OUTPUT_DIR=""

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --poll)
          POLL_SECONDS="$2"
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
          if [[ -z "$OUTPUT_DIR" ]]; then
            OUTPUT_DIR="$1"
          else
            echo "Error: unexpected argument $1" >&2
            usage
          fi
          shift
          ;;
      esac
    done

    if [[ -z "$OUTPUT_DIR" ]]; then
      echo "Error: wait requires <output-dir>." >&2
      usage
    fi

    while true; do
      current_state="$(status_value "$OUTPUT_DIR/status.txt" "STATE")"
      if [[ -f "$OUTPUT_DIR/complete.marker" || "$current_state" == "completed" ]]; then
        print_status "$OUTPUT_DIR"
        exit 0
      fi
      if [[ -f "$OUTPUT_DIR/failed.marker" || "$current_state" == "failed" ]]; then
        print_status "$OUTPUT_DIR"
        exit 1
      fi
      if [[ -f "$OUTPUT_DIR/interrupted.marker" || "$current_state" == "interrupted" ]]; then
        print_status "$OUTPUT_DIR"
        exit 1
      fi

      current_pid=""
      if [[ -f "$OUTPUT_DIR/job.pid" ]]; then
        current_pid="$(tr -d '[:space:]' < "$OUTPUT_DIR/job.pid")"
      fi

      if [[ -n "$current_pid" ]] && ! is_pid_alive "$current_pid"; then
        echo "Error: detached export process is no longer running, but no terminal marker was written." >&2
        print_status "$OUTPUT_DIR"
        exit 1
      fi

      sleep "$POLL_SECONDS"
    done
    ;;

  stop)
    if [[ $# -ne 1 ]]; then
      echo "Error: stop requires <output-dir>." >&2
      usage
    fi

    OUTPUT_DIR="$1"
    if [[ ! -f "$OUTPUT_DIR/job.pid" ]]; then
      echo "Error: no job.pid found under $OUTPUT_DIR." >&2
      exit 1
    fi

    pid="$(tr -d '[:space:]' < "$OUTPUT_DIR/job.pid")"
    pgid=""
    if [[ -f "$OUTPUT_DIR/job.pgid" ]]; then
      pgid="$(tr -d '[:space:]' < "$OUTPUT_DIR/job.pgid")"
    fi

    pkill -TERM -P "$pid" >/dev/null 2>&1 || true
    kill -TERM "$pid" >/dev/null 2>&1 || true

    echo "STOP_SIGNAL_SENT: yes"
    echo "OUTPUT_DIR: $OUTPUT_DIR"
    echo "PID: $pid"
    echo "PGID: $pgid"
    ;;

  *)
    echo "Error: unknown command $COMMAND" >&2
    usage
    ;;
esac
