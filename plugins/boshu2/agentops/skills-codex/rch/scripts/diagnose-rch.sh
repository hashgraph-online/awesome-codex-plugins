#!/usr/bin/env bash
# RCH diagnostic script (CLI + hook protocol aware)
# Usage: ./diagnose-rch.sh

set -euo pipefail

if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  NC=''
fi

FAILURES=0
WARNINGS=0

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "${BLUE}i${NC} $1"; }

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
fi

json_jq() {
  local json="$1"
  local filter="$2"
  if [[ "$HAS_JQ" -eq 1 ]]; then
    printf '%s' "$json" | jq -r "$filter // empty" 2>/dev/null || true
  fi
}

extract_string() {
  local json="$1"
  local key="$2"
  printf '%s' "$json" | sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n1
}

extract_bool() {
  local json="$1"
  local key="$2"
  printf '%s' "$json" | sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\(true\|false\).*/\1/p" | head -n1
}

extract_int() {
  local json="$1"
  local key="$2"
  printf '%s' "$json" | sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p" | head -n1
}

if ! command -v rch >/dev/null 2>&1; then
  echo "rch binary not found in PATH"
  echo "Install or expose rch first, then re-run this script."
  exit 127
fi

echo "═══════════════════════════════════════"
echo "     RCH Diagnostic Report (Current)"
echo "═══════════════════════════════════════"
echo

# 1) quick health
echo "1. Quick Health (rch check)"
echo "───────────────────────────"
check_json="$(rch --json check 2>/dev/null || true)"
if [[ -z "$check_json" ]]; then
  fail "No JSON returned from 'rch --json check'"
else
  status=""
  if [[ "$HAS_JQ" -eq 1 ]]; then
    status="$(json_jq "$check_json" '.data.status')"
  fi
  if [[ -z "$status" ]]; then
    status="$(extract_string "$check_json" 'status')"
  fi

  if [[ "$status" == "ready" ]]; then
    pass "RCH status: ready"
  elif [[ "$status" == "degraded" ]]; then
    warn "RCH status: degraded"
  elif [[ -n "$status" ]]; then
    fail "RCH status: $status"
  else
    warn "Could not parse check status"
  fi
fi
echo

# 2) daemon status
echo "2. Daemon Status"
echo "────────────────"
daemon_json="$(rch --json daemon status 2>/dev/null || true)"
if [[ -z "$daemon_json" ]]; then
  fail "No response from 'rch --json daemon status'"
else
  running=""
  socket=""
  if [[ "$HAS_JQ" -eq 1 ]]; then
    running="$(json_jq "$daemon_json" '.data.running')"
    socket="$(json_jq "$daemon_json" '.data.socket_path')"
  fi
  if [[ -z "$running" ]]; then
    running="$(extract_bool "$daemon_json" 'running')"
  fi
  if [[ -z "$socket" ]]; then
    socket="$(extract_string "$daemon_json" 'socket_path')"
  fi

  if [[ "$running" == "true" ]]; then
    pass "Daemon running (${socket:-socket unknown})"
  elif [[ "$running" == "false" ]]; then
    fail "Daemon not running"
    info "Fix: rch daemon start"
  else
    warn "Could not determine daemon running state"
  fi
fi
echo

# 3) socket consistency
echo "3. Socket Consistency"
echo "─────────────────────"
config_socket_json="$(rch --json config get general.socket_path 2>/dev/null || true)"
config_socket=""
daemon_socket=""
if [[ -n "$config_socket_json" ]]; then
  if [[ "$HAS_JQ" -eq 1 ]]; then
    config_socket="$(json_jq "$config_socket_json" '.data.value')"
  fi
  if [[ -z "$config_socket" ]]; then
    config_socket="$(extract_string "$config_socket_json" 'value')"
  fi
fi

if [[ -n "$daemon_json" ]]; then
  if [[ "$HAS_JQ" -eq 1 ]]; then
    daemon_socket="$(json_jq "$daemon_json" '.data.socket_path')"
  fi
  if [[ -z "$daemon_socket" ]]; then
    daemon_socket="$(extract_string "$daemon_json" 'socket_path')"
  fi
fi

if [[ -n "$config_socket" && -n "$daemon_socket" ]]; then
  if [[ "$config_socket" == "$daemon_socket" ]]; then
    pass "Config socket matches daemon socket ($config_socket)"
  else
    fail "Socket mismatch: config=$config_socket daemon=$daemon_socket"
    info "Fix: align socket path then run 'rch daemon restart -y'"
  fi
else
  warn "Could not fully verify socket consistency"
fi
echo

# 4) workers
echo "4. Worker Fleet"
echo "───────────────"
workers_json="$(rch --json workers list 2>/dev/null || true)"
worker_count=""
if [[ -n "$workers_json" ]]; then
  if [[ "$HAS_JQ" -eq 1 ]]; then
    worker_count="$(json_jq "$workers_json" '.data.count')"
  fi
  if [[ -z "$worker_count" ]]; then
    worker_count="$(extract_int "$workers_json" 'count')"
  fi
fi

if [[ -z "$worker_count" ]]; then
  warn "Could not parse configured worker count"
  worker_count=0
fi

if [[ "$worker_count" -gt 0 ]]; then
  pass "Configured workers: $worker_count"
  probe_json="$(rch --json workers probe --all 2>/dev/null || true)"
  if [[ -z "$probe_json" ]]; then
    fail "No response from 'rch --json workers probe --all'"
  else
    ok_count=0
    bad_count=0
    if [[ "$HAS_JQ" -eq 1 ]]; then
      ok_count="$(printf '%s' "$probe_json" | jq -r '[.data[] | select(.status == "ok")] | length' 2>/dev/null || echo 0)"
      bad_count="$(printf '%s' "$probe_json" | jq -r '[.data[] | select(.status != "ok")] | length' 2>/dev/null || echo 0)"
    else
      ok_count="$(printf '%s' "$probe_json" | grep -c '"status"[[:space:]]*:[[:space:]]*"ok"' || true)"
      bad_count="$(printf '%s' "$probe_json" | grep -Ec '"status"[[:space:]]*:[[:space:]]*"(fail|error|timeout|unreachable|down)"' || true)"
    fi

    if [[ "$ok_count" -eq "$worker_count" ]]; then
      pass "All workers probe successfully"
    elif [[ "$ok_count" -gt 0 ]]; then
      warn "Partial worker health: ${ok_count}/${worker_count} reachable"
    else
      fail "No workers are currently reachable"
    fi

    if [[ "$bad_count" -gt 0 ]]; then
      warn "Workers with non-ok probe status: $bad_count"
    fi
  fi
else
  fail "No workers configured"
  info "Fix: rch workers discover --add --yes && rch workers setup --all"
fi
echo

# 5) hook install
echo "5. Hook Installation"
echo "────────────────────"
hook_json="$(rch --json hook status 2>/dev/null || true)"
if [[ -z "$hook_json" ]]; then
  warn "Could not retrieve hook status"
else
  claude_status=""
  if [[ "$HAS_JQ" -eq 1 ]]; then
    claude_status="$(printf '%s' "$hook_json" | jq -r '.data.agents[]? | select(.agent == "ClaudeCode") | .status' 2>/dev/null | head -n1)"
  fi
  if [[ -z "$claude_status" ]]; then
    if printf '%s' "$hook_json" | grep -q '"agent"[[:space:]]*:[[:space:]]*"ClaudeCode"' && \
       printf '%s' "$hook_json" | grep -q '"status"[[:space:]]*:[[:space:]]*"Installed"'; then
      claude_status="Installed"
    fi
  fi

  if [[ "$claude_status" == "Installed" ]]; then
    pass "Claude Code hook is installed"
  else
    fail "Claude Code hook is not installed"
    info "Fix: rch hook install"
  fi
fi
echo

# 6) protocol rewrite test
echo "6. Hook Protocol Rewrite Test"
echo "─────────────────────────────"
hook_input='{"tool_name":"Bash","tool_input":{"command":"cargo build --release"}}'
hook_output="$(printf '%s\n' "$hook_input" | rch 2>/dev/null || true)"

if [[ -z "$hook_output" ]]; then
  warn "Hook returned empty stdout (allow unchanged/local)"
elif printf '%s' "$hook_output" | grep -q '"updatedInput"' && \
     printf '%s' "$hook_output" | grep -q 'rch exec --'; then
  pass "Hook returns allow-with-modified-command (rch exec delegation)"
elif printf '%s' "$hook_output" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
  warn "Hook returned deny decision; inspect policy/logs"
else
  warn "Hook returned unexpected protocol payload"
fi
echo

echo "═══════════════════════════════════════"
echo "Summary: ${FAILURES} failure(s), ${WARNINGS} warning(s)"
echo "═══════════════════════════════════════"

if [[ "$FAILURES" -gt 0 ]]; then
  echo
  echo "Suggested next commands:"
  echo "  rch doctor"
  echo "  rch config doctor"
  echo "  rch diagnose \"cargo build --release\""
  echo "  rch daemon logs -n 200"
  exit 1
fi

exit 0
