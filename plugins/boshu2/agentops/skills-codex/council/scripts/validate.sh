#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: council" "grep -q '^name: council' '$SKILL_DIR/SKILL.md'"
check "schemas/ directory exists" "[ -d '$SKILL_DIR/schemas' ]"
check "verdict.json exists" "[ -f '$SKILL_DIR/schemas/verdict.json' ]"
check "verdict.json is valid JSON" "python3 -m json.tool '$SKILL_DIR/schemas/verdict.json' >/dev/null 2>&1"
check "verdict.json has verdict field" "grep -q '\"verdict\"' '$SKILL_DIR/schemas/verdict.json'"
check "verdict.json has confidence field" "grep -q '\"confidence\"' '$SKILL_DIR/schemas/verdict.json'"
check "verdict.json has key_insight field" "grep -q '\"key_insight\"' '$SKILL_DIR/schemas/verdict.json'"
check "verdict.json has findings field" "grep -q '\"findings\"' '$SKILL_DIR/schemas/verdict.json'"
check "verdict.json has recommendation field" "grep -q '\"recommendation\"' '$SKILL_DIR/schemas/verdict.json'"
check "verdict.json has additionalProperties:false at root" "python3 -c \"import json,sys; d=json.load(open('$SKILL_DIR/schemas/verdict.json')); sys.exit(0 if d.get('additionalProperties') == False else 1)\""
check "verdict.json has additionalProperties:false in findings items" "python3 -c \"import json,sys; d=json.load(open('$SKILL_DIR/schemas/verdict.json')); sys.exit(0 if d['properties']['findings']['items'].get('additionalProperties') == False else 1)\""
check "references/ has at least 5 files" "[ \$(ls '$SKILL_DIR/references/' | wc -l) -ge 5 ]"
check "SKILL.md mentions default mode" "grep -q 'default' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions --deep mode" "grep -q '\-\-deep' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions --mixed mode" "grep -q '\-\-mixed' '$SKILL_DIR/SKILL.md'"
check "Output directory pattern documented" "grep -q '\.agents/council/' '$SKILL_DIR/SKILL.md'"
check "leadership-quartet preset documented in personas" "grep -q 'leadership-quartet' '$SKILL_DIR/references/personas.md'"
check "leadership-quartet preset documented in presets index" "grep -q 'leadership-quartet' '$SKILL_DIR/references/presets.md'"
check "leadership-quartet Codex skill surface documented" "grep -q 'leadership-quartet' '$SKILL_DIR/SKILL.md'"
check "leadership-quartet maps four perspectives" "grep -q 'product-manager, cto, chief-engineer, staff-engineer' '$SKILL_DIR/references/personas.md'"
check "leadership-quartet has read budgets" "grep -q 'read_budget:' '$SKILL_DIR/references/personas.md'"
check "leadership-quartet has verdict formats" "grep -q 'verdict_format:' '$SKILL_DIR/references/personas.md'"
check "leadership-quartet mixed mode documents 8 judges" "grep -q '8 total judges' '$SKILL_DIR/references/personas.md'"
check "mocked --mixed artifact smoke reads default and leadership-quartet outputs" "bash '$SKILL_DIR/scripts/validate-mixed-artifacts.sh'"
# Behavioral contracts: verify key features remain documented
check "SKILL.md documents the --adversarial verdict intensifier" "grep -q '\-\-adversarial' '$SKILL_DIR/SKILL.md'"
check "SKILL.md documents the three-mode taxonomy" "grep -q 'mode=debate' '$SKILL_DIR/SKILL.md' && grep -q 'mode=brainstorm' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions --quick depth alias" "grep -q '\-\-quick' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions verdict field" "grep -q 'verdict' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions PASS/WARN/FAIL" "grep -q 'PASS.*WARN.*FAIL\|PASS | WARN | FAIL' '$SKILL_DIR/SKILL.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
