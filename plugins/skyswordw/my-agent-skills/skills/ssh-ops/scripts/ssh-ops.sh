#!/usr/bin/env bash
set -euo pipefail

MAX_LINES="${SSH_OPS_MAX_LINES:-120}"
DRY_RUN=0
PRINT_REMOTE_SCRIPT=0
SSH_OPTS=(
  -o BatchMode=yes
  -o ConnectTimeout=8
  -o ServerAliveInterval=30
  -o ServerAliveCountMax=3
)

[[ "$MAX_LINES" =~ ^[0-9]+$ ]] || {
  printf 'error: SSH_OPS_MAX_LINES must be a positive integer\n' >&2
  exit 2
}
[[ "$MAX_LINES" -gt 0 ]] || {
  printf 'error: SSH_OPS_MAX_LINES must be a positive integer\n' >&2
  exit 2
}

usage() {
  cat <<'EOF'
Usage:
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] help
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] health <alias>
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] run <alias> -- <command...>
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] batch <alias> <local-script>
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] logs <alias> journal <unit>
  scripts/ssh-ops.sh [--dry-run] [--print-remote-script] logs <alias> docker <container>

Environment:
  SSH_OPS_MAX_LINES  Raw output excerpt lines for run/logs. Default: 120.
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 2
}

shell_quote() {
  local value="$1"
  printf "'%s'" "${value//\'/\'\\\'\'}"
}

ssh_shape() {
  local alias="$1"
  local part
  printf 'ssh'
  for part in "${SSH_OPTS[@]}"; do
    printf ' %s' "$part"
  done
  printf ' %s ' "$alias"
  shell_quote "bash -s"
  printf '\n'
}

print_or_exec_remote() {
  local alias="$1"
  local script="$2"

  if (( PRINT_REMOTE_SCRIPT )); then
    ssh_shape "$alias"
    printf 'DRY_RUN_REMOTE_BASE=/tmp/ssh-ops/\n'
    printf 'DRY_RUN_RAW_LOG=/tmp/ssh-ops/<timestamp>/raw.log\n'
    printf '%s\n' '--- remote script ---'
    printf '%s\n' "$script"
    return 0
  fi

  if (( DRY_RUN )); then
    ssh_shape "$alias"
    printf 'DRY_RUN_REMOTE_BASE=/tmp/ssh-ops/\n'
    printf 'DRY_RUN_RAW_LOG=/tmp/ssh-ops/<timestamp>/raw.log\n'
    return 0
  fi

  ssh "${SSH_OPTS[@]}" "$alias" 'bash -s' <<<"$script"
}

remote_wrapper() {
  local label="$1"
  local body="$2"
  local excerpt_lines="$3"

  cat <<EOF
set -euo pipefail
base_dir="/tmp/ssh-ops"
mkdir -p "\$base_dir"
timestamp="\$(date -u +%Y%m%dT%H%M%SZ)"
run_dir="\$base_dir/\${timestamp}-${label}"
mkdir -p "\$run_dir"
raw_log="\$run_dir/raw.log"
status=0
{
${body}
} >"\$raw_log" 2>&1 || status=\$?
printf 'RUN_DIR=%s\n' "\$run_dir"
printf 'RAW_LOG=%s\n' "\$raw_log"
printf 'EXIT_STATUS=%s\n' "\$status"
printf '%s\n' '--- raw excerpt ---'
tail -n ${excerpt_lines} "\$raw_log" || true
exit "\$status"
EOF
}

remote_health_script() {
  cat <<'EOF'
set -euo pipefail
base_dir="/tmp/ssh-ops"
mkdir -p "$base_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
run_dir="$base_dir/${timestamp}-health"
mkdir -p "$run_dir"
raw_log="$run_dir/raw.log"
{
  printf '== hostname ==\n'
  hostname
  printf '\n== uptime ==\n'
  uptime
  printf '\n== df -hT ==\n'
  df -hT
  printf '\n== free -h ==\n'
  free -h 2>/dev/null || true
  printf '\n== lscpu ==\n'
  lscpu 2>/dev/null | head -n 40 || true
  printf '\n== docker ps ==\n'
  if command -v docker >/dev/null 2>&1; then
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1 | head -n 40 || true
  else
    printf 'docker not installed\n'
  fi
  printf '\n== nvidia-smi ==\n'
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi || true
  else
    printf 'nvidia-smi not installed\n'
  fi
} >"$raw_log" 2>&1 || true
printf 'HEALTH_SUMMARY\n'
printf 'HOSTNAME=%s\n' "$(hostname)"
printf 'UPTIME=%s\n' "$(uptime | sed 's/^[[:space:]]*//')"
printf 'RAW_LOG=%s\n' "$raw_log"
EOF
}

build_run_body() {
  local command_line
  if [[ $# -eq 1 ]]; then
    command_line="$1"
  else
    local quoted
    local arg
    command_line=""
    for arg in "$@"; do
      printf -v quoted '%q' "$arg"
      if [[ -n "$command_line" ]]; then
        command_line+=" "
      fi
      command_line+="$quoted"
    done
  fi
  printf 'bash -lc %s\n' "$(shell_quote "$command_line")"
}

cmd_health() {
  [[ $# -eq 1 ]] || die "health requires <alias>"
  print_or_exec_remote "$1" "$(remote_health_script)"
}

cmd_run() {
  [[ $# -ge 2 ]] || die "run requires <alias> -- <command...>"
  local alias="$1"
  shift
  [[ "${1:-}" == "--" ]] || die "run requires -- before command"
  shift
  [[ $# -ge 1 ]] || die "run requires a command after --"
  print_or_exec_remote "$alias" "$(remote_wrapper run "$(build_run_body "$@")" "$MAX_LINES")"
}

cmd_batch() {
  [[ $# -eq 2 ]] || die "batch requires <alias> <local-script>"
  local alias="$1"
  local local_script="$2"
  [[ -f "$local_script" ]] || die "local script not found: $local_script"
  command -v base64 >/dev/null 2>&1 || die "base64 is required for batch"

  if (( DRY_RUN )); then
    ssh_shape "$alias"
    printf 'DRY_RUN_REMOTE_BASE=/tmp/ssh-ops/\n'
    printf 'DRY_RUN_RAW_LOG=/tmp/ssh-ops/<timestamp>/raw.log\n'
    printf 'DRY_RUN_LOCAL_SCRIPT=%s\n' "$local_script"
    if (( PRINT_REMOTE_SCRIPT )); then
      printf '%s\n' '--- remote script wrapper ---'
      remote_wrapper batch 'bash "$payload"' "$MAX_LINES"
    fi
    return 0
  fi

  if (( PRINT_REMOTE_SCRIPT )); then
    ssh_shape "$alias"
    printf 'DRY_RUN_REMOTE_BASE=/tmp/ssh-ops/\n'
    printf 'DRY_RUN_RAW_LOG=/tmp/ssh-ops/<timestamp>/raw.log\n'
    printf 'DRY_RUN_LOCAL_SCRIPT=%s\n' "$local_script"
    printf '%s\n' '--- remote script wrapper ---'
    remote_wrapper batch 'bash "$payload"' "$MAX_LINES"
    return 0
  fi

  local payload_b64
  payload_b64="$(base64 <"$local_script" | tr -d '\n')"
  print_or_exec_remote "$alias" "$(remote_wrapper batch "payload=\"\$run_dir/payload.sh\"
printf %s $(shell_quote "$payload_b64") | base64 -d >\"\$payload\"
chmod +x \"\$payload\"
bash \"\$payload\"" "$MAX_LINES")"
}

cmd_logs() {
  [[ $# -eq 3 ]] || die "logs requires <alias> journal <unit> or <alias> docker <container>"
  local alias="$1"
  local mode="$2"
  local target="$3"
  local body

  case "$mode" in
    journal)
      body="journalctl --since -10min --no-pager -n 120 -u $(shell_quote "$target")"
      ;;
    docker)
      body="docker logs --since=10m --tail=120 $(shell_quote "$target")"
      ;;
    *)
      die "logs mode must be journal or docker"
      ;;
  esac

  print_or_exec_remote "$alias" "$(remote_wrapper "logs-${mode}" "$body" "$MAX_LINES")"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --print-remote-script)
      PRINT_REMOTE_SCRIPT=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

cmd="${1:-help}"
shift || true

case "$cmd" in
  help) usage ;;
  health) cmd_health "$@" ;;
  run) cmd_run "$@" ;;
  batch) cmd_batch "$@" ;;
  logs) cmd_logs "$@" ;;
  *) die "unknown command: $cmd" ;;
esac
