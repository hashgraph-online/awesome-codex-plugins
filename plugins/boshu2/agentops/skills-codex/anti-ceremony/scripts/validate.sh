#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
bash "$REPO_ROOT/skills/skill-builder/scripts/heal.sh" --check --strict "$SKILL_DIR"
grep -Fq 'Perform the guard exactly once in memory.' "$SKILL_DIR/SKILL.md"
grep -Fq 'decision: CONTINUE | STOP' "$SKILL_DIR/SKILL.md"
grep -Fq 'Run this mode only when the caller explicitly requests it.' "$SKILL_DIR/SKILL.md"
echo 'anti-ceremony skill contract: PASS'
