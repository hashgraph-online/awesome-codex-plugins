#!/usr/bin/env bash
# Portable PreToolUse command guard for Claude Code, Codex, and AGY.
#
# The hook is intentionally silent and fail-open unless it sees an actual
# Agent Mail / NTM command head or `tmux send-keys`. On the first match for a
# runtime session, it asks the agent to load the owning skill contract and
# exits 2 so the command can be reconsidered. The next attempt is allowed.
set -uo pipefail

[[ "${AGENTOPS_HOOKS_DISABLED:-0}" == "1" ]] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

input="$(cat)" || exit 0
cmd="$(
  printf '%s' "$input" |
    jq -er '
      (
        .tool_input.command
        // .tool_input.cmd
        // .tool_input.command_line
        // .command
        // ""
      ) | strings
    ' 2>/dev/null
)" || exit 0
[[ -n "$cmd" ]] || exit 0

sid="$(
  printf '%s' "$input" |
    jq -r '
      (
        .session_id
        // .thread_id
        // .conversation_id
        // .project_id
        // ""
      ) | tostring
    ' 2>/dev/null
)" || sid=""

# Remove quoted spans and heredoc bodies before examining shell command heads.
# This avoids firing on issue bodies, commit messages, or prose that merely
# mentions a coordination command.
stripped="$(
  printf '%s' "$cmd" |
    perl -0777 -pe "
      s/'[^']*'//g;
      s/\"[^\"]*\"//g;
      s/<<-?\s*([A-Za-z_][A-Za-z0-9_]*).*?^\s*\1\b//gms;
    " 2>/dev/null
)" || exit 0

is_coord=0
printf '%s' "$stripped" | awk '
  BEGIN { RS="[;&\n]|\\|\\|?"; FS="[ \t]+" }
  {
    i=1
    while (i<=NF && ($i=="" || $i ~ /^[A-Za-z_][A-Za-z0-9_]*=/)) i++
    head=$i
    sub(/^.*\//, "", head)
    if (head=="am" || head=="ntm") found=1
    if (head=="tmux" && $(i+1)=="send-keys") found=1
  }
  END { exit (found ? 0 : 1) }
' && is_coord=1
[[ "$is_coord" -eq 1 ]] || exit 0

if [[ -n "$sid" ]]; then
  sentinel_dir="${TMPDIR:-/tmp}/agentops-coordguard"
  safe_sid="$(printf '%s' "$sid" | tr -c 'A-Za-z0-9_.-' '_')"
  sentinel="$sentinel_dir/$safe_sid"
  [[ -f "$sentinel" ]] && exit 0
  mkdir -p "$sentinel_dir" 2>/dev/null || true
  : >"$sentinel" 2>/dev/null || true
fi

cat >&2 <<'MSG'
AgentOps coordination guard: load the `agent-mail` or `ntm` skill contract
before hand-writing coordination commands. Re-run the command after loading
the skill; this guard fires at most once for a runtime session.
MSG
exit 2
