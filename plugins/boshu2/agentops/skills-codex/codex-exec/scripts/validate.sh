#!/usr/bin/env bash
# validate.sh — self-check for the codex-exec skill.
# Verifies: frontmatter completeness, exact line-start Triggers marker, the
# required section spine + ordering, and the Form-A line budget (<=250).
# Exit 0 on PASS, 1 on any FAIL. Run: bash scripts/validate.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"
PASS=0; FAIL=0

check() { # name, test-expr
  if bash -c "$2" >/dev/null 2>&1; then
    echo "PASS: $1"; PASS=$((PASS + 1))
  else
    echo "FAIL: $1"; FAIL=$((FAIL + 1))
  fi
}

# --- existence + frontmatter ---
check "SKILL.md exists" "[ -f '$SKILL' ]"
check "starts with YAML frontmatter" "head -1 '$SKILL' | grep -q '^---$'"
check "frontmatter closes" "[ \$(grep -c '^---$' '$SKILL') -ge 2 ]"
check "has name: field" "grep -qE '^name: codex-exec$' '$SKILL'"
check "has description: field" "grep -qE '^description:' '$SKILL'"
check "has skill_api_version: 1" "grep -qE '^skill_api_version: 1$' '$SKILL'"
check "has metadata.tier" "grep -qE '^  tier:' '$SKILL'"
check "has output_contract" "grep -qE '^output_contract:' '$SKILL'"

# --- triggers (FAIL-severity per AUTHORING-STANDARD §0/§8.2) ---
check "line-start Triggers: marker present" "grep -qE '^[[:space:]]*Triggers:' '$SKILL'"
check "description carries a Triggers clause" "awk '/^description:/{f=1} /^[A-Za-z_]/&&!/^description:/{if(f)exit} f' '$SKILL' | grep -q 'Triggers:'"

# --- section spine (required order per §5) ---
check "has Critical Constraints section" "grep -qE '^## .*Critical Constraints' '$SKILL'"
check "has Why This Exists section" "grep -qE '^## Why This Exists' '$SKILL'"
check "has Quick Start section" "grep -qE '^## Quick Start' '$SKILL'"
check "has Workflow/Methodology section" "grep -qE '^## Workflow' '$SKILL'"
check "has Output Specification section" "grep -qE '^## Output Specification' '$SKILL'"
check "has Quality Rubric section" "grep -qE '^## Quality Rubric' '$SKILL'"
check "has Troubleshooting section" "grep -qE '^## Troubleshooting' '$SKILL'"
check "has See Also section" "grep -qE '^## See Also' '$SKILL'"

# spine ordering: Critical Constraints must precede Why This Exists
cc=$(grep -nE '^## .*Critical Constraints' "$SKILL" | head -1 | cut -d: -f1)
wy=$(grep -nE '^## Why This Exists' "$SKILL" | head -1 | cut -d: -f1)
check "Critical Constraints precedes Why This Exists" "[ -n '$cc' ] && [ -n '$wy' ] && [ '$cc' -lt '$wy' ]"

# --- line budget (Form A hard ceiling 250) ---
LINES=$(wc -l < "$SKILL" | tr -d ' ')
check "Form-A line budget (<=250, is $LINES)" "[ '$LINES' -le 250 ]"

echo ""
echo "Results: $PASS passed, $FAIL failed (SKILL.md = $LINES lines)"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
