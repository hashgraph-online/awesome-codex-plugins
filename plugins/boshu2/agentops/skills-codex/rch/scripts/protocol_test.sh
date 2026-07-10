#!/usr/bin/env bash
# protocol_test.sh — directly probe the rch hook protocol with synthetic inputs.
#
# Confirms what the hook will do for a given command without actually building.
# Useful when:
#   - hook seems installed but commands run locally
#   - you want to know whether a compound command (cd ... && cargo ...) will be wrapped
#   - you want to see the exact JSON the hook returns
#
# Usage:
#   ./protocol_test.sh                                   # default tests
#   ./protocol_test.sh "cargo build --release"           # one custom command
#   ./protocol_test.sh "cd /data/projects/x && cargo check"

set -euo pipefail

require() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 127; }; }
require rch
require jq

# Use mktemp so concurrent runs don't collide and we clean up on exit/interrupt.
STDERR_TMP="$(mktemp -t rch_proto_stderr.XXXXXX)"
trap 'rm -f "$STDERR_TMP"' EXIT INT TERM

run_one() {
  local cmd="$1"
  local input
  input=$(jq -nc --arg c "$cmd" '{tool_name:"Bash", tool_input:{command:$c}}')
  printf '\n--- INPUT ---\n%s\n' "$input"
  printf '\n--- STDOUT (the hook decision) ---\n'
  local out
  out=$(printf '%s\n' "$input" | RCH_LOG_LEVEL=info rch 2>"$STDERR_TMP")
  if [[ -z "$out" ]]; then
    printf '(empty)  → ALLOW UNCHANGED (hook did not intercept)\n'
  else
    printf '%s\n' "$out" | jq . 2>/dev/null || printf '%s\n' "$out"
    if grep -q '"updatedInput"' <<<"$out"; then
      printf '\n  → hook will REWRITE to: %s\n' \
        "$(jq -r '.hookSpecificOutput.updatedInput.command' <<<"$out")"
    elif grep -q '"deny"' <<<"$out"; then
      printf '\n  → hook will DENY\n'
    fi
  fi
  printf '\n--- STDERR (diagnostics) ---\n'
  cat "$STDERR_TMP" || true
  : > "$STDERR_TMP"   # truncate for next run
  printf '\n=================================================================\n'
}

if [[ $# -gt 0 ]]; then
  for cmd in "$@"; do
    run_one "$cmd"
  done
  exit 0
fi

# Default battery
COMMANDS=(
  "cargo check"
  "cargo build --release"
  "cargo test --workspace"
  "cargo nextest run"
  "bun test"
  "bun typecheck"
  "ls -la"                               # should NOT be intercepted
  "cargo install ripgrep"                # should NOT be intercepted (mutating)
  "cd /data/projects/x && cargo check"   # compound: should preserve cd
)

for cmd in "${COMMANDS[@]}"; do
  run_one "$cmd"
done

cat <<'EOF'

──────────────────────────────────────────────────────────────────────────
Interpretation:
  • Empty stdout    → hook does nothing (command runs as-is, locally)
  • permissionDecision=allow + updatedInput → hook will rewrite to `rch exec -- ...`
  • permissionDecision=deny → policy or config blocks the command

If a compilation command (cargo build, cargo test, etc.) returns empty stdout:
  - Check 'rch hook status' to confirm the hook is installed for the right agent
  - Check '[general] enabled = true' in ~/.config/rch/config.toml
  - Check '[general] force_local' isn't true
  - Run 'rch diagnose "<command>"' to see classifier output
EOF
