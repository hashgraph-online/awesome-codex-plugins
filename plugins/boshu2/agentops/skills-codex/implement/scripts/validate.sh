#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: implement" "grep -q '^name: implement' '$SKILL_DIR/SKILL.md'"
check "references/ directory exists" "[ -d '$SKILL_DIR/references' ]"
check "references/ has at least 2 files" "[ \$(ls '$SKILL_DIR/references/' | wc -l) -ge 2 ]"
check "SKILL.md mentions br for issue tracking" "grep -q 'br ' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions beads" "grep -qi 'beads' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions \$validate for closeout" "grep -q '[$]validate' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions Explore agent" "grep -qi 'explore' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions verification gate" "grep -qi 'verification\|verify' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions ratchet record" "grep -q 'ratchet record' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions GREEN mode" "grep -q 'GREEN' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions DONE/BLOCKED/PARTIAL markers" "grep -q 'DONE\|BLOCKED\|PARTIAL' '$SKILL_DIR/SKILL.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
