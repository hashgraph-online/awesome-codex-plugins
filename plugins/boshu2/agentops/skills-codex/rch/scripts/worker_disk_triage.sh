#!/usr/bin/env bash
# worker_disk_triage.sh — read-only mount-aware disk report for every worker.
#
# Never deletes anything. Suggests the next safe step (usually "hand off to sbh").
#
# Usage:
#   ./worker_disk_triage.sh                   # all workers
#   ./worker_disk_triage.sh css ts2           # specific workers by id
#   ./worker_disk_triage.sh --json            # machine-readable

set -euo pipefail

JSON_OUT=0
WORKERS=()
for arg in "$@"; do
  case "$arg" in
    --json) JSON_OUT=1 ;;
    -h|--help)
      sed -n '2,/^# Usage/p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) WORKERS+=("$arg") ;;
  esac
done

require() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 127; }; }
require rch
require jq
require ssh

# `rch --json workers list` shape: .data.workers[].{id, host, user, total_slots, priority, tags}
if [[ ${#WORKERS[@]} -eq 0 ]]; then
  mapfile -t WORKERS < <(rch --json workers list 2>/dev/null \
    | jq -r '.data.workers[]?.id')
fi

if [[ ${#WORKERS[@]} -eq 0 ]]; then
  echo "no workers configured" >&2
  exit 1
fi

# Resolve id → host using rch workers list
declare -A HOST_BY_ID
while IFS=$'\t' read -r id host; do
  HOST_BY_ID["$id"]="$host"
done < <(rch --json workers list 2>/dev/null \
  | jq -r '.data.workers[]? | [.id, .host] | @tsv')

probe_one() {
  local id="$1"
  local host="${HOST_BY_ID[$id]:-$id}"
  ssh -o ConnectTimeout=8 -o BatchMode=yes "ubuntu@$host" '
    set +e
    printf "%s\n" "--- df / and /tmp ---"
    df -h / /tmp 2>/dev/null
    printf "%s\n" "--- mem + pressure ---"
    free -h | awk "NR<=2"
    [ -r /proc/pressure/memory ] && cat /proc/pressure/memory
    [ -r /proc/pressure/io ]     && cat /proc/pressure/io
    printf "%s\n" "--- /tmp rch artifacts (top 10 by size) ---"
    du -sh /tmp/rch-* /tmp/rch_target_* 2>/dev/null | sort -h | tail -10
    printf "%s\n" "--- /data/projects target dirs (top 10 by size) ---"
    find /data/projects -maxdepth 3 -type d \( -name "target_rch_*" -o -name "target_*" -o -name "target-*" -o -name target \) -exec du -sh {} + 2>/dev/null | sort -h | tail -10
    printf "%s\n" "--- sbh status (if installed) ---"
    if command -v sbh >/dev/null 2>&1; then sbh status 2>/dev/null | head -20; else echo "sbh not installed"; fi
    printf "%s\n" "--- top processes by RSS ---"
    ps -eo pid,user,rss,cmd --sort=-rss --no-headers 2>/dev/null | head -10
  ' 2>&1
}

if (( JSON_OUT )); then
  echo "{"
  first=1
  for id in "${WORKERS[@]}"; do
    host="${HOST_BY_ID[$id]:-$id}"
    raw="$(probe_one "$id" 2>&1)"
    [[ $first -eq 0 ]] && echo ","
    first=0
    printf '  "%s": {"host": %s, "report": %s}' \
      "$id" "$(printf '%s' "$host" | jq -Rs .)" "$(printf '%s' "$raw" | jq -Rs .)"
  done
  echo
  echo "}"
  exit 0
fi

for id in "${WORKERS[@]}"; do
  host="${HOST_BY_ID[$id]:-$id}"
  echo
  echo "=========================================="
  echo "  Worker: $id  ($host)"
  echo "=========================================="
  probe_one "$id" || echo "[ssh failed]"
done

cat <<'EOF'

──────────────────────────────────────────────────────────────────────────
Next steps (NEVER delete anything yet):

  • If a /tmp/rch_target_* dir is large AND lsof is empty, it is safe:
        ssh ubuntu@<host> 'sudo lsof +D /tmp/rch_target_<name> 2>/dev/null | head'
        # If the lsof output is empty:
        ssh ubuntu@<host> 'rm -r -- /tmp/rch_target_<name>'   # require explicit user OK first

  • Prefer letting sbh handle it (if installed on the worker):
        ssh ubuntu@<host> 'sbh scan'
        ssh ubuntu@<host> 'sbh clean --apply'

  • Never delete /data/projects/<repo>/target_* without:
      1. confirming lsof is empty,
      2. confirming `rch --json queue | jq '.data.active_builds[].project_id'` does not reference that project.

  • If a worker has critical pressure that won't clear:
        rch workers drain <id> -y    # finish active builds, accept no new
        # ... investigate ...
        rch workers enable <id>
EOF
