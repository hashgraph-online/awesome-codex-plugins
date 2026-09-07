#!/usr/bin/env bash
# install-hooks.sh — wire the AgentOps policy dispatcher into Claude settings,
# from ANY install shape (epic age-4qw1: hooks ship by default).
#
# This copy lives INSIDE the cc-hooks skill package so every distribution path
# carries its own wiring:
#   - npx skills / skills.sh copy  -> ~/.claude/skills/cc-hooks/scripts/install-hooks.sh
#   - git clone / brew checkout    -> skills/cc-hooks/scripts/install-hooks.sh
#     (scripts/install-policy-dispatch.sh at the repo root delegates here)
#   - Claude Code PLUGIN installs need NO installer at all: the plugin bundles
#     hooks/hooks.json and Claude wires it automatically.
#
# Everything resolves relative to THIS script's skill dir, so it works from a
# copied skill directory with no repo present. Idempotent; backs up settings.
#
# Usage:
#   install-hooks.sh            # user settings (~/.claude/settings.json)
#   install-hooks.sh --project  # project settings (.claude/settings.json)
#   SETTINGS=/path/settings.json install-hooks.sh
set -euo pipefail
umask 022

# shellcheck disable=SC1007  # CDPATH= scopes an empty CDPATH to the cd, intentionally
script_dir="$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(dirname "$script_dir")"
src_dispatch="${skill_dir}/hooks/policy-dispatch.sh"
src_policies="${skill_dir}/policies/policies.json"
lint="${script_dir}/lint-policies.sh"
[[ -f "$src_dispatch" ]] || { echo "ERROR: dispatcher missing: ${src_dispatch}" >&2; exit 1; }
[[ -f "$src_policies" ]] || { echo "ERROR: registry missing: ${src_policies}" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq required" >&2; exit 1; }

# Never install a registry that fails its own contract.
bash "$lint" "$src_policies"

settings="${SETTINGS:-}"
if [[ -z "$settings" ]]; then
  case "${1:-}" in
    --project) settings=".claude/settings.json" ;;
    *)         settings="${HOME}/.claude/settings.json" ;;
  esac
fi

hooks_dir="${HOME}/.claude/hooks/aop"
mkdir -p "$hooks_dir"
install -m 0755 "$src_dispatch" "${hooks_dir}/policy-dispatch.sh"
install -m 0644 "$src_policies" "${hooks_dir}/policies.json"
dst="${hooks_dir}/policy-dispatch.sh"
echo "✓ installed ${dst} (+ policies.json beside it)"

mkdir -p "$(dirname "$settings")"
[[ -f "$settings" ]] || echo '{}' > "$settings"

if [[ -s "$settings" ]]; then
  backup="${settings}.bak.$(date +%Y%m%d%H%M%S)"
  cp -p "$settings" "$backup"
  echo "✓ backed up settings → ${backup}"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
jq --arg cmd "$dst" '
  .hooks //= {} |
  .hooks.PreToolUse //= [] |
  reduce ("Bash", "Edit|Write") as $m (.;
    if any(.hooks.PreToolUse[]?; .matcher == $m and any((.hooks // [])[]?; .command == $cmd))
    then .
    else .hooks.PreToolUse += [{
      "matcher": $m,
      "hooks": [ { "type": "command", "command": $cmd } ]
    }]
    end
  )
' "$settings" > "$tmp" && mv "$tmp" "$settings"
trap - EXIT

if grep -qF "$dst" "$settings"; then
  echo "✓ wired PreToolUse (Bash, Edit|Write) policy dispatcher into ${settings}"
else
  echo "ERROR: failed to wire dispatcher into ${settings}" >&2
  exit 1
fi

echo ""
echo "Policy dispatcher active for this Claude scope. SILENT on every clean call;"
echo "deny policies block with a one-line route to the correct tool; fires land one"
echo "hashed telemetry line in \${AGENTOPS_HOME:-~/.agents/ao}/guardrail-telemetry.jsonl."
echo "Waive once:  AOP_WAIVE=<policy-id> <your command>"
echo "Uninstall:   remove the two PreToolUse matchers for ${dst} from ${settings}, then rm -rf ${hooks_dir}"
