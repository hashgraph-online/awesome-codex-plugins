#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "name is beads" "grep -q '^name: beads' '$SKILL_DIR/SKILL.md'"
check "mentions br CLI" "grep -q 'br' '$SKILL_DIR/SKILL.md'"
check "mentions issue tracking" "grep -qi 'issue track' '$SKILL_DIR/SKILL.md'"
check "mentions dependency-aware" "grep -qi 'dependency' '$SKILL_DIR/SKILL.md'"
check "mentions git-backed" "grep -qi 'git' '$SKILL_DIR/SKILL.md'"
check "documents live br queries as source of truth" "grep -q 'Treat live \`br\` reads as authoritative' '$SKILL_DIR/SKILL.md'"
check "documents explicit br sync refresh" "grep -q 'br sync --flush-only' '$SKILL_DIR/SKILL.md'"
check "documents parent-child reconciliation" "grep -q 'reconcile the open parent' '$SKILL_DIR/SKILL.md'"
check "documents broad parent handling" "grep -q 'broad umbrella issue' '$SKILL_DIR/SKILL.md'"
check "documents tracker push after sync" "grep -q 'git push.*tracker remote' '$SKILL_DIR/SKILL.md'"
check "workflow doc covers authoritative reads" "grep -q '^## Authoritative State Reads' '$SKILL_DIR/references/WORKFLOWS.md'"
check "workflow doc covers tracker mutation follow-through" "grep -q '^## Tracker Mutation Follow-Through' '$SKILL_DIR/references/WORKFLOWS.md'"
check "workflow doc covers parent-child reconciliation" "grep -q '^## Parent/Child Reconciliation' '$SKILL_DIR/references/WORKFLOWS.md'"
check "workflow doc covers queue normalization" "grep -q '^## Queue and Backlog Reconciliation' '$SKILL_DIR/references/WORKFLOWS.md'"
check "anti-pattern doc forbids jsonl as canonical state" "grep -q 'Canonical Tracker' '$SKILL_DIR/references/ANTI_PATTERNS.md'"
check "br reference requires explicit sync" "grep -q 'br sync --flush-only' '$SKILL_DIR/references/BR_REFERENCE.md'"
check "cli reference no longer claims automatic jsonl sync" "! grep -q 'JSONL auto-sync is automatic' '$SKILL_DIR/references/CLI_REFERENCE.md'"
check "cli reference avoids stale migrate inspect json command" "! grep -q 'bd migrate --inspect --json' '$SKILL_DIR/references/CLI_REFERENCE.md'"
check "cli reference documents machine-readable version probe" "grep -q 'bd upgrade status --json' '$SKILL_DIR/references/CLI_REFERENCE.md'"
check "patterns doc uses parent-child semantics for broad-parent decomposition" "grep -q -- '--parent pl-vnu.5' '$SKILL_DIR/references/PATTERNS.md' && ! grep -q 'discovered-from:pl-vnu.5' '$SKILL_DIR/references/PATTERNS.md'"
check "dependencies doc remains the planning contract" "grep -q 'parent-child.*planned task breakdown' '$SKILL_DIR/references/DEPENDENCIES.md'"
check "troubleshooting doc covers missing dolt remote" "grep -q '^## \`bd dolt push\` Fails Because No Remote Is Configured' '$SKILL_DIR/references/TROUBLESHOOTING.md'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
