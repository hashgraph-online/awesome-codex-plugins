#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"
MCP_SEARCH="$SKILL_DIR/scripts/mcp-search.py"

[[ -s "$SKILL" ]]
grep -q '^name: ms$' "$SKILL"
# Canonical source carries full metadata; the generated Codex package uses slim
# frontmatter but mirrors this validator and the runnable body.
if grep -q '^metadata:' "$SKILL"; then
  grep -q '^  effects: \[\]$' "$SKILL"
fi
grep -Fq 'Keep `ms` retrieval-only for production skill work.' "$SKILL"
grep -Fq '**Authority boundary:** `skills/**` is canonical source' "$SKILL"
grep -Fq '**Outcome timing:** Record `ms outcome` only after the caller has independent evidence' "$SKILL"
grep -Fq 'A zero-result `ms search` CLI response is not evidence' "$SKILL"
grep -Fq 'python3 skills/ms/scripts/mcp-search.py "<query>"' "$SKILL"
! grep -Eiq 'pawl|AUTO-REDO|ONE-HELPER|circuit breaker|canonical factory|promotes a skill' "$SKILL"
[[ -s "$MCP_SEARCH" ]]
python3 "$MCP_SEARCH" --help >/dev/null

echo "ms retrieval contract: PASS"
