#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "name is product" "grep -q '^name: product' '$SKILL_DIR/SKILL.md'"
check "mentions PRODUCT.md" "grep -q 'PRODUCT.md' '$SKILL_DIR/SKILL.md'"
check "mentions personas" "grep -qi 'personas' '$SKILL_DIR/SKILL.md'"
check "mentions value propositions" "grep -qi 'value prop' '$SKILL_DIR/SKILL.md'"
check "mentions competitive landscape" "grep -qi 'competitive' '$SKILL_DIR/SKILL.md'"
check "mentions 10-star experience" "grep -qi '10-star experience' '$SKILL_DIR/SKILL.md'"
check "mentions PMF wedge" "grep -qi 'PMF Wedge' '$SKILL_DIR/SKILL.md'"
check "mentions product sense" "grep -qi 'Product Sense' '$SKILL_DIR/SKILL.md'"
check "mentions anti-personas" "grep -qi 'Anti-personas' '$SKILL_DIR/SKILL.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
