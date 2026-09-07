#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: doc" "grep -q '^name: doc' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions documentation generation" "grep -qi 'generate.*doc\|documentation' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions code-map" "grep -qi 'code-map\|code map' '$SKILL_DIR/SKILL.md'"
check "SKILL.md front-loads constraints" "grep -q '^## Constraints' '$SKILL_DIR/SKILL.md'"
check "SKILL.md declares output specification" "grep -q '^## Output Specification' '$SKILL_DIR/SKILL.md'"
check "output specification declares validation and handoff" "grep -qi 'validation command' '$SKILL_DIR/SKILL.md' && grep -qi 'downstream handoff' '$SKILL_DIR/SKILL.md'"
check "SKILL.md declares quality checklist" "grep -q '^## Quality Checklist' '$SKILL_DIR/SKILL.md'"
check "OSS scaffold is missing-only by default" "grep -Eqi 'OSS scaffold.*missing.*only by default' '$SKILL_DIR/SKILL.md'"
check "OSS existing-doc writes require explicit user confirmation" "grep -Eqi 'OSS.*existing doc.*explicit user confirmation' '$SKILL_DIR/SKILL.md'"
check "OSS output avoids broad create-or-update claim" "! grep -Eqi 'OSS mode (creates?|writes?) or updates?' '$SKILL_DIR/SKILL.md'"
check "OSS reference preserves explicit confirmation boundary" "grep -Eqi 'refresh.*explicit user confirmation' '$SKILL_DIR/references/oss-pack.md'"
check "OSS executable spec covers confirmed refresh" "grep -Eqi 'explicit user confirmation before updating or overwriting' '$SKILL_DIR/references/oss-docs.feature'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
