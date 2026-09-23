#!/usr/bin/env bash
# Opt-in Codex PreToolUse adapter for the documented canonical Bash event.
# Codex shell/exec_command calls arrive as tool_name=Bash, tool_input.command.
# Read/read_file and MCP tools are not mapped here. The sibling guard owns the
# policy, waivers, line counting and hashed telemetry; only denial advice differs.
# Source: https://learn.chatgpt.com/docs/hooks (Codex CLI 0.154.0 contract).
# No preamble: this installed hook must fail open, independent of the checkout.
set -uo pipefail

[ "${AGENTOPS_HOOKS_DISABLED:-}" = "1" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0
# CDPATH= clears a caller's directory-search setting for this one cd.
# shellcheck disable=SC1007
hook_dir="$( (CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) 2>/dev/null)" || exit 0
core="${hook_dir}/read-budget-guard.sh"
[ -r "$core" ] || exit 0
input="$(cat 2>/dev/null)" || exit 0
printf '%s' "$input" | jq -e '
  type == "object" and .hook_event_name == "PreToolUse" and
  .tool_name == "Bash" and (.tool_input.command | type == "string")
' >/dev/null 2>&1 || exit 0

# Capture only diagnostics, never relay stdout. Unexpected guard errors remain
# fail-open; only the shared guard's explicit denial preserves exit 2.
diagnostic="$(printf '%s' "$input" | bash "$core" 2>&1 >/dev/null)"
decision=$?
[ "$decision" -eq 2 ] || exit 0
while IFS= read -r line; do
  line="${line//agentops:bulk-reader/bulk-reader}"
  case "$line" in
    '→ Read a slice:'*)
      printf '%s\n' "→ Read a bounded shell slice: sed -n 'START,ENDp' <file>, within AOP_READ_BUDGET_LINES (default 350)." >&2 ;;
    '    Agent tool:'*)
      printf '%s\n' '    Codex: delegate the question and file path to the installed bulk-reader role; request path:line bullets only.' >&2 ;;
    '    Workflow:'*|'    These names require the AgentOps plugin.'*) ;;
    *) printf '%s\n' "${line//offset+limit \/ sed -n/sed -n}" >&2 ;;
  esac
done <<< "$diagnostic"
exit 2
