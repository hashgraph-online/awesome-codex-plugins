#!/usr/bin/env bash
# validate.sh — structural check for the cass skill.
#
# CI should prove the skill artifact is valid, not require an operator's local
# cass index. Set AGENTOPS_VALIDATE_LIVE_TOOLS=1 to run the live cass smoke.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
SPEC_JSON="$SKILL_DIR/skill.spec.json"

fail=0
err() { printf 'FAIL: %s\n' "$1" >&2; fail=1; }
ok() { printf 'ok:   %s\n' "$1"; }

[ -f "$SKILL_MD" ] || { err "SKILL.md missing"; exit 1; }
head -n1 "$SKILL_MD" | grep -qx -- '---' || err "frontmatter must open with ---"
grep -q '^name: cass$' "$SKILL_MD" || err "name must be cass"
grep -q '^description:' "$SKILL_MD" || err "description missing"
grep -q '^skill_api_version:' "$SKILL_MD" || err "skill_api_version missing"
grep -q 'cass search' "$SKILL_MD" || err "cass search workflow missing"
grep -q 'cass status' "$SKILL_MD" || err "cass status workflow missing"
grep -q 'Incremental refresh can become authoritative' "$SKILL_MD" || err "authoritative fallback guidance missing"
grep -q '124 is NOT zero hits' "$SKILL_MD" || err "bounded concurrent-search guidance missing"
grep -q 'not evidence that source sessions were lost' "$SKILL_MD" || err "source-preservation boundary missing"
grep -q '^## Authoritative Fallback and Concurrent Read Latency$' \
  "$SKILL_DIR/references/OBSERVABILITY.md" || err "observability fallback detail missing"

if [ -f "$SPEC_JSON" ]; then
  python3 -m json.tool "$SPEC_JSON" >/dev/null || err "skill.spec.json is not valid JSON"
  ok "skill.spec.json valid JSON"
else
  ok "skill.spec.json sidecar absent"
fi

if [ "${AGENTOPS_VALIDATE_LIVE_TOOLS:-0}" = "1" ]; then
  command -v cass >/dev/null 2>&1 || err "cass is not installed or not in PATH"
  command -v jq >/dev/null 2>&1 || err "jq is not installed or not in PATH"
  if command -v cass >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    status="$(cass status --robot-format json 2>/dev/null)" || err "cass status failed"
    printf '%s' "$status" | jq -e . >/dev/null 2>&1 || err "cass status returned invalid JSON"
    cass search "*" --json --limit 1 --fields minimal >/dev/null 2>&1 || err "basic cass search failed"
    cass search "*" --json --aggregate agent --limit 1 --fields minimal >/dev/null 2>&1 || err "cass aggregation search failed"
  fi
else
  ok "live cass smoke skipped (set AGENTOPS_VALIDATE_LIVE_TOOLS=1 to enable)"
fi

if [ "$fail" -eq 0 ]; then
  printf '\nPASS: cass skill artifact is valid.\n'
  exit 0
fi

printf '\nFAILED: cass skill artifact validation failed.\n' >&2
exit 1
