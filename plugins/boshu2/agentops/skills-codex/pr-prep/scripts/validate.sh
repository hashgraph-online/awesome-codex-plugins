#!/bin/bash
# Validate pr-prep skill
set -euo pipefail

# Determine SKILL_DIR relative to this script (works in plugins or ~/.claude)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ERRORS=0
CHECKS=0

check() {
    local desc="$1"
    local cmd="$2"
    local expected="$3"

    CHECKS=$((CHECKS + 1))
    if eval "$cmd" 2>/dev/null | grep -qi "$expected"; then
        echo "✓ $desc"
    else
        echo "✗ $desc"
        echo "  Command: $cmd"
        echo "  Expected to find: $expected"
        ERRORS=$((ERRORS + 1))
    fi
}

check_pattern() {
    local desc="$1"
    local file="$2"
    local pattern="$3"

    CHECKS=$((CHECKS + 1))
    if grep -qiE "$pattern" "$file" 2>/dev/null; then
        echo "✓ $desc"
    else
        echo "✗ $desc (pattern '$pattern' not found in $file)"
        ERRORS=$((ERRORS + 1))
    fi
}

check_exists() {
    local desc="$1"
    local path="$2"

    CHECKS=$((CHECKS + 1))
    if [ -e "$path" ]; then
        echo "✓ $desc"
    else
        echo "✗ $desc ($path not found)"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "=== PR Prep Skill Validation ==="
echo ""


# Verify git is available
check "git binary exists" "which git" "git"

# Verify current tracker skill surfaces exist (`beads` and `beads-workflow`
# were merged into beads-br, ag-ez7y6).
check_exists "beads-br skill exists" "$SKILL_DIR/../beads-br/SKILL.md"
check_exists "beads-br conversion prompts exist" "$SKILL_DIR/../beads-br/references/PROMPTS.md"

# Verify pr-prep workflow patterns in SKILL.md
check_pattern "SKILL.md has git archaeology" "$SKILL_DIR/SKILL.md" "git|[Aa]rchaeology"
check_pattern "SKILL.md has test validation" "$SKILL_DIR/SKILL.md" "[Tt]est.*[Vv]alid|[Vv]alidat.*[Tt]est"
check_pattern "SKILL.md has PR body generation" "$SKILL_DIR/SKILL.md" "PR.*[Bb]ody|[Bb]ody.*PR"
check_pattern "SKILL.md has user review gate" "$SKILL_DIR/SKILL.md" "[Rr]eview.*[Gg]ate|MANDATORY.*[Rr]eview"

echo ""
echo "=== Results ==="
echo "Checks: $CHECKS"
echo "Errors: $ERRORS"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "FAIL: PR-prep skill validation failed"
    exit 1
else
    echo ""
    echo "PASS: PR-prep skill validation passed"
    exit 0
fi
