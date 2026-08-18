#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"
MCP_SEARCH="$SKILL_DIR/scripts/mcp-search.py"

[[ -s "$SKILL" ]]
grep -q '^name: ms$' "$SKILL"
# Canonical source carries full metadata; the generated Codex package uses slim
# frontmatter but mirrors this validator and the runnable body. Effects must be
# declared HONESTLY: ms spawns an MCP search server, writes feedback/outcome rows
# to a live DB, and rebuilds the index. An empty effects list is a known
# falsehood. Anchor the assertion to the YAML frontmatter block (between the
# first two --- fences) so a token that merely appears in the prose body can
# never satisfy the effects contract, and require the exact declared value.
if grep -q '^metadata:' "$SKILL"; then
  frontmatter="$(awk '/^---[[:space:]]*$/{fences++; next} fences==1{print}' "$SKILL")"
  expected_effects='  effects: [spawn_search_server, write_feedback_outcomes, rebuild_search_index]'
  if printf '%s\n' "$frontmatter" | grep -qxF "$expected_effects"; then
    :
  else
    echo "ms frontmatter effects must be exactly: [spawn_search_server, write_feedback_outcomes, rebuild_search_index]" >&2
    echo "(ms spawns a search server and writes feedback/outcome/index state; an empty or partial list is a known falsehood)" >&2
    exit 1
  fi
fi
grep -Fq 'Keep `ms` retrieval-only for production skill work.' "$SKILL"
grep -Fq '**Authority boundary:** `skills/**` is canonical source' "$SKILL"
grep -Fq '**Outcome timing:** Record `ms outcome` only after the caller has independent evidence' "$SKILL"
grep -Fq 'A zero-result `ms search` CLI response is not evidence' "$SKILL"
grep -Fq 'python3 skills/ms/scripts/mcp-search.py "<query>"' "$SKILL"
if grep -Eiq 'pawl|AUTO-REDO|ONE-HELPER|circuit breaker|canonical factory|promotes a skill' "$SKILL"; then
  echo 'ms contract contains retired factory/lifecycle vocabulary' >&2
  exit 1
fi
[[ -s "$MCP_SEARCH" ]]
python3 "$MCP_SEARCH" --help >/dev/null

echo "ms retrieval contract: PASS"
