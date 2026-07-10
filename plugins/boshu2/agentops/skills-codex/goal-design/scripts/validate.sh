#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
PASS=0
FAIL=0

check() {
  local name="$1" cmd="$2"
  if bash -c "$cmd"; then
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $name"
    FAIL=$((FAIL + 1))
  fi
}

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "frontmatter name" "grep -q '^name: goal-design' '$SKILL_DIR/SKILL.md'"
check "helper documented" "grep -q 'scripts/goal-design-packet.py new' '$SKILL_DIR/SKILL.md'"
check "checker documented" "grep -q 'check-goal-design-packet.sh' '$SKILL_DIR/SKILL.md'"
check "independent validation required" "grep -qi 'independent validation' '$SKILL_DIR/SKILL.md'"
check "helper tests exist" "[ -f '$REPO_ROOT/tests/scripts/goal-design-packet.bats' ]"

echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
