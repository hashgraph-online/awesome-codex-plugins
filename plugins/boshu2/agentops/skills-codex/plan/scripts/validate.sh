#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "SKILL.md has name: plan" "grep -q '^name: plan' '$SKILL_DIR/SKILL.md'"
check "references/ directory exists" "[ -d '$SKILL_DIR/references' ]"
check "references/ has at least 2 files" "[ \$(ls '$SKILL_DIR/references/' | wc -l) -ge 2 ]"
check "SKILL.md mentions .agents/plans/ output path" "grep -q '\.agents/plans/' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions compiled planning rules" "grep -q '\.agents/planning-rules' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions finding registry fallback" "grep -q 'registry.jsonl' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions active findings" "grep -qi 'active findings' '$SKILL_DIR/SKILL.md'"
check "SKILL.md requires applied finding IDs in plan context" "grep -q 'Applied findings:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions waves" "grep -qi 'wave' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions dependencies" "grep -qi 'dependencies\|depend' '$SKILL_DIR/SKILL.md'"
check "SKILL.md requires Codex companion scope" "grep -q 'Generated Artifact Companion Scope' '$SKILL_DIR/SKILL.md' && grep -q 'refresh-codex-artifacts.sh --scope worktree' '$SKILL_DIR/SKILL.md'"
check "SKILL.md requires full touched-file inventory" "grep -q 'list every touched file' '$SKILL_DIR/SKILL.md' && grep -q 'tests, docs, schemas, fixtures' '$SKILL_DIR/SKILL.md' && grep -q 'parity manifests, hash markers' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions br for issue tracking" "grep -q 'br ' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions task tracking" "grep -qi 'task\|tracking\|br ' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions conformance checks" "grep -qi 'conformance' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions --auto flag" "grep -q '\-\-auto' '$SKILL_DIR/SKILL.md'"
check "SKILL.md mentions Explore agent" "grep -qi 'explore' '$SKILL_DIR/SKILL.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
