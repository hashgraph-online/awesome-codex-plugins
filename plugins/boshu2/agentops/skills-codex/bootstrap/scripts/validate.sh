#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: bootstrap" "grep -q '^name: bootstrap' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions GOALS.md" "grep -q 'GOALS\\.md' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions PRODUCT.md" "grep -q 'PRODUCT\\.md' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions PROGRAM/AUTODEV" "grep -Eq 'PROGRAM\\.md|AUTODEV\\.md' '$SKILL_DIR/SKILL.md'"
check "SKILL.md delegates core seed to quick-start" "grep -q 'ao quick-start' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions progressive/gap-filling behavior" "grep -qiE 'progressive|fills? gaps|idempotent' '$SKILL_DIR/SKILL.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
