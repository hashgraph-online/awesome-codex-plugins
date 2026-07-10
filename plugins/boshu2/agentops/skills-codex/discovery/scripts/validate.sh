#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: discovery" "grep -q '^name: discovery' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions brainstorm phase" "grep -qi 'brainstorm' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions research phase" "grep -qi 'research' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions plan phase" "grep -qi 'plan' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions pre-mortem gate" "grep -qi 'pre-mortem' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions fanout approval packet" "grep -q 'PerspectivePlan' '$SKILL_DIR/SKILL.md' && grep -q 'SynthesisPacket' '$SKILL_DIR/SKILL.md' && grep -q 'ApprovalEdge' '$SKILL_DIR/SKILL.md'"
check "DAG gates judgment WARN explicitly" "grep -q 'judgment WARN is surfaced' '$SKILL_DIR/references/dag.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
