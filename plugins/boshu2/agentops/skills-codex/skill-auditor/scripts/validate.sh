#!/usr/bin/env bash
# validate.sh — self-validation for skill-auditor
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

# Pass 1: run heal-skill on ourselves
bash "$REPO_ROOT/skills/heal-skill/scripts/heal.sh" --check "$SKILL_DIR"

# Required artifacts
for f in SKILL.md scripts/audit.sh references/skill-template.md references/audit-checks.md references/context-density-checks.md; do
  [[ -f "$SKILL_DIR/$f" ]] || { echo "validate.sh: missing $SKILL_DIR/$f" >&2; exit 1; }
done

# Churn budget
LINES="$(wc -l < "$SKILL_DIR/SKILL.md")"
if (( LINES > 250 )); then
  echo "validate.sh: SKILL.md is $LINES lines (>250 budget per finding f-2026-05-01-025)" >&2
  exit 1
fi

# audit.sh must contain all 8 NEW check function names
for fn in check_description_has_triggers check_constraints_frontloaded check_rationale_present check_verification_checkpoints check_output_spec_explicit check_quality_rubric check_references_modularization check_trigger_clarity; do
  grep -q "^${fn}()" "$SKILL_DIR/scripts/audit.sh" || {
    echo "validate.sh: scripts/audit.sh missing function $fn" >&2
    exit 1
  }
done

# audit.sh must include the advisory density report, without adding it to the
# Pass-2 verdict loop.
grep -q "^check_density_field()" "$SKILL_DIR/scripts/audit.sh" || {
  echo "validate.sh: scripts/audit.sh missing advisory density coverage function" >&2
  exit 1
}
for field in intent boundary evidence decision constraint next_action; do
  grep -q "$field" "$SKILL_DIR/scripts/audit.sh" || {
    echo "validate.sh: scripts/audit.sh missing density field $field" >&2
    exit 1
  }
done

# audit.sh must NOT contain the old check name (per pre-mortem F1)
if grep -q "check_description_multiline" "$SKILL_DIR/scripts/audit.sh"; then
  echo "validate.sh: audit.sh contains stale 'check_description_multiline' (must be 'check_description_has_triggers' per pre-mortem F1)" >&2
  exit 1
fi

# Make scripts executable
for s in scripts/audit.sh scripts/validate.sh; do
  [[ -x "$SKILL_DIR/$s" ]] || chmod +x "$SKILL_DIR/$s"
done

echo "validate.sh: skill-auditor PASS ($LINES lines, all 8 checks + density advisory present)"
