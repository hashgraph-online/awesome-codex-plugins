#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

bash "$REPO_ROOT/skills/skill-builder/scripts/heal.sh" --check --strict "$SKILL_DIR"

if rg -n 'scope\.lock|AO_SCOPE_LOCK|PreToolUse|ao scope|freeze|unfreeze|git (commit|push)|ao land' \
  "$SKILL_DIR/SKILL.md"; then
  echo "scope validate: mutable scope authority remains" >&2
  exit 1
fi

echo "scope validate: PASS"
