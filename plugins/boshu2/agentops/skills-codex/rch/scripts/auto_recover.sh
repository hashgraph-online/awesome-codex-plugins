#!/usr/bin/env bash
# auto_recover.sh — heuristic, safe-by-default recovery loop for unhealthy rch fleets.
#
# Usage:
#   ./auto_recover.sh             # dry-run: print what would happen
#   ./auto_recover.sh --apply     # actually take action (still safe; no rm -rf)
#
# What it does, in order:
#   1. Probes daemon health → if dead and 'rchd' is in PATH, starts it
#   2. Probes hook install on every detected agent → installs if missing
#   3. Probes every worker → classifies failures (key missing, host down,
#      auth, telemetry stale, version drift, disk pressure)
#   4. For each classifiable failure, applies the safe recovery
#      (disable+drain unreachable workers, redeploy binary on version drift,
#      hand off to sbh skill on disk pressure, etc.)
#   5. Re-runs probes, prints a summary
#
# What it deliberately will NOT do without explicit user authorization:
#   - rm anything (target dirs, sockets, key files, daemon state, telemetry db)
#   - kill -9 any process
#   - chown /data/projects on a worker
#   - run sbh clean (just suggests the command)
#
# Adheres to AGENTS.md "no destructive defaults" rule.

set -euo pipefail

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { sed -n '2,/^# Adheres/p' "$0" | sed 's/^# \?//'; exit 0; }

color() { [[ -t 1 ]] && printf '\033[%sm%s\033[0m' "$1" "$2" || printf '%s' "$2"; }
say()   { printf '%s %s\n' "$(color '1;34' '[plan]')" "$*"; }
ok()    { printf '%s %s\n' "$(color '1;32' '[ok]  ')" "$*"; }
warn()  { printf '%s %s\n' "$(color '1;33' '[warn]')" "$*" >&2; }
err()   { printf '%s %s\n' "$(color '1;31' '[fail]')" "$*" >&2; }

run() {
  if (( APPLY )); then
    "$@"
  else
    printf '       $ %s\n' "$*"
  fi
}

require() { command -v "$1" >/dev/null 2>&1 || { err "missing command: $1"; exit 127; }; }
require rch
require jq

# ──────────────────────────────────────────────────────────────────────────────
# Phase 1: Daemon
# ──────────────────────────────────────────────────────────────────────────────
say "Phase 1: daemon health"
DAEMON_JSON="$(timeout 5 rch --json daemon status 2>/dev/null || true)"
DAEMON_RUNNING="$(printf '%s' "$DAEMON_JSON" | jq -r '.data.running // false' 2>/dev/null || echo false)"

if [[ "$DAEMON_RUNNING" != "true" ]]; then
  if command -v rchd >/dev/null 2>&1; then
    say "daemon not responding — running 'rch daemon start'"
    run rch daemon start || true
    sleep 2
  else
    err "rchd binary missing from PATH; install rch first"
    exit 1
  fi
else
  ok "daemon responsive"
fi

# Socket consistency
CFG_SOCK="$(timeout 5 rch --json config get general.socket_path 2>/dev/null | jq -r '.data.value // ""')"
DMN_SOCK="$(printf '%s' "$DAEMON_JSON" | jq -r '.data.socket_path // ""')"
if [[ -n "$CFG_SOCK" && -n "$DMN_SOCK" && "$CFG_SOCK" != "$DMN_SOCK" ]]; then
  warn "socket mismatch: config=$CFG_SOCK daemon=$DMN_SOCK — restarting daemon"
  run rch daemon restart -y || true
fi

# ──────────────────────────────────────────────────────────────────────────────
# Phase 2: Hook installation per agent
# ──────────────────────────────────────────────────────────────────────────────
# `rch --json agents status` returns:
#   .data.agents[].{kind, name, hook_status, can_install_hook, ...}
# `kind` is PascalCase ("ClaudeCode"); install-hook expects kebab-case
# ("claude-code"). Convert by injecting hyphens before each upper-case run.
pascal_to_kebab() {
  printf '%s\n' "$1" | sed -E 's/([a-z0-9])([A-Z])/\1-\2/g; s/([A-Z]+)([A-Z][a-z])/\1-\2/g' \
    | tr '[:upper:]' '[:lower:]'
}

say "Phase 2: hook installation per agent"
AGENT_JSON="$(timeout 10 rch --json agents status 2>/dev/null || true)"
if [[ -n "$AGENT_JSON" ]]; then
  while IFS=$'\t' read -r kind name hook_status can_install; do
    [[ -z "$kind" ]] && continue
    [[ "$hook_status" == "Installed" ]] && continue
    if [[ "$can_install" != "true" ]]; then
      warn "$name ($kind): hook missing but agent reports can_install_hook=false — skipping"
      continue
    fi
    agent_arg="$(pascal_to_kebab "$kind")"
    warn "$name ($kind): hook is '$hook_status' — installing as '$agent_arg'"
    run rch agents install-hook "$agent_arg" || true
  done < <(printf '%s' "$AGENT_JSON" \
            | jq -r '.data.agents[]? | [.kind, .name, .hook_status, (.can_install_hook|tostring)] | @tsv')
else
  warn "could not query agents; skipping hook check"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Phase 3: Worker probe + classification
# ──────────────────────────────────────────────────────────────────────────────
say "Phase 3: worker probes"
PROBE_JSON="$(timeout 60 rch --json workers probe --all 2>/dev/null || true)"
if [[ -z "$PROBE_JSON" ]]; then
  err "could not probe workers; daemon may still be starting — try again in 10s"
  exit 0
fi

# `rch --json workers probe --all` returns:
#   .data is a flat array of {id, host, status, latency_ms?, error?}
# status is one of: "ok", "unhealthy", "error", "connection_failed".
mapfile -t ROWS < <(
  printf '%s' "$PROBE_JSON" \
    | jq -r '.data[]? | [.id, .host, .status, (.error // "")] | @tsv'
)

if [[ ${#ROWS[@]} -eq 0 ]]; then
  warn "no workers configured (probe returned empty array)"
  say "  rch workers discover --probe --add --yes && rch workers setup --all"
  exit 0
fi

UNHEALTHY=()
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r id host status reason <<<"$row"
  if [[ "$status" == "ok" ]]; then
    ok "$id ($host)"
    continue
  fi
  UNHEALTHY+=("$id|$host|$reason")
done

if [[ ${#UNHEALTHY[@]} -eq 0 ]]; then
  ok "all ${#ROWS[@]} worker(s) healthy"
  exit 0
fi

say "Phase 4: classify ${#UNHEALTHY[@]} unhealthy worker(s)"
for entry in "${UNHEALTHY[@]}"; do
  IFS='|' read -r id host reason <<<"$entry"
  printf '\n  worker=%s host=%s\n  reason=%s\n' "$id" "$host" "$reason"

  case "$reason" in
    *"Permission denied"*"publickey"*|*"identity_file"*|*"no such identity"*)
      warn "$id: SSH auth/key failure"
      # Find the identity_file for this worker by walking workers.toml.
      # Strategy: track the current [[workers]] block; remember when we
      # see id="<target>"; print identity_file when matched. Handles id
      # appearing either before or after identity_file within a block.
      KEY_PATH="$(awk -v target="$id" '
        function strval(s) { sub(/^[^"]*"/, "", s); sub(/".*$/, "", s); return s }
        /^[[:space:]]*\[\[workers\]\]/ { id_seen=""; ifile=""; matched=0; next }
        /^[[:space:]]*id[[:space:]]*=/ { id_seen=strval($0); if (id_seen==target) matched=1 }
        /^[[:space:]]*identity_file[[:space:]]*=/ { ifile=strval($0) }
        matched && ifile != "" { print ifile; exit }
      ' ~/.config/rch/workers.toml 2>/dev/null)"
      KEY_RESOLVED="${KEY_PATH/#~/$HOME}"
      if [[ -z "$KEY_PATH" ]]; then
        warn "could not find identity_file for '$id' in ~/.config/rch/workers.toml"
        say "manual check:  rch --json workers list | jq '.data.workers[] | select(.id==\"$id\")'"
      elif [[ -n "$KEY_RESOLVED" && ! -r "$KEY_RESOLVED" ]]; then
        warn "configured key '$KEY_RESOLVED' is not readable on this host"
        say "search for an alternate copy:  find ~/.ssh /etc/ssh /root/.ssh 2>/dev/null -name '$(basename "$KEY_RESOLVED")*'"
        say "or check ssh-agent:           ssh-add -l"
        say "or disable temporarily:       rch workers disable $id --reason 'missing key' --drain -y"
        say "full recovery playbook:       references/SSH_KEY_RECOVERY.md"
      else
        say "key looks present; check authorized_keys on $host:"
        say "  ssh -i '$KEY_RESOLVED' -v ubuntu@$host true"
      fi
      ;;
    *"Connection refused"*|*"Connection timed out"*|*"No route to host"*|*"timed out"*)
      warn "$id: TCP unreachable"
      run rch workers disable "$id" --reason "host unreachable: $reason" --drain -y || true
      ;;
    *"self-test failed"*|*"binary version"*|*"outdated"*)
      warn "$id: looks like binary/version drift"
      # rch workers deploy-binary doesn't have --verify; use rch fleet deploy with --worker.
      run rch fleet deploy --worker "$id" --verify || true
      ;;
    *"disk pressure"*|*"no space left"*|*"telemetry"*"stale"*|*"RCH-E21"*)
      warn "$id: disk/telemetry pressure — handing off to sbh"
      say "ssh ubuntu@$host 'df -h / /tmp; free -h; sbh status 2>/dev/null'"
      say "if sbh available:  ssh ubuntu@$host 'sbh scan && sbh clean --apply'"
      ;;
    *"toolchain"*|*"rustup"*|*"cargo: command not found"*)
      warn "$id: toolchain missing on remote"
      run rch workers sync-toolchain "$id" || true
      ;;
    *"host key verification"*)
      warn "$id: host-key mismatch — needs explicit human authorization to refresh known_hosts"
      ;;
    *)
      warn "$id: no automated rule matched. Investigate manually:"
      say "  ssh -v ubuntu@$host echo OK"
      say "  rch workers probe $id --json | jq"
      ;;
  esac
done

# ──────────────────────────────────────────────────────────────────────────────
# Phase 5: Re-verify
# ──────────────────────────────────────────────────────────────────────────────
echo
say "Phase 5: re-verify"
run rch check
echo
ok "done."
if (( ! APPLY )); then
  warn "this was a DRY RUN — re-run with --apply to execute the suggested actions"
fi
