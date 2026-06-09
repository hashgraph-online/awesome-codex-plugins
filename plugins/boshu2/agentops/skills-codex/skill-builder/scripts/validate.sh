#!/usr/bin/env bash
# validate.sh — self-validation for skill-builder
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

# Run heal-skill structural check on ourselves by exit code.
bash "$REPO_ROOT/skills/heal-skill/scripts/heal.sh" --check --strict "$SKILL_DIR"

# Verify required artifacts exist
for f in SKILL.md scripts/build.sh scripts/init.sh references/skill-template.md schemas/build-report.json; do
  [[ -f "$SKILL_DIR/$f" ]] || { echo "validate.sh: missing $SKILL_DIR/$f" >&2; exit 1; }
done

# Verify scale-factory lessons stay encoded.
for phrase in \
  "heal-skill --check --strict" \
  "One skill directory = one writer" \
  "git status" \
  "Clean-room includes names" \
  "Workflow tool"; do
  grep -q "$phrase" "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references/agentops-skill-factory.md" || {
    echo "validate.sh: missing scale-factory lesson: $phrase" >&2
    exit 1
  }
done

# Verify SKILL.md is within churn budget
LINES="$(wc -l < "$SKILL_DIR/SKILL.md")"
if (( LINES > 250 )); then
  echo "validate.sh: SKILL.md is $LINES lines (>250 budget per finding f-2026-05-01-025)" >&2
  exit 1
fi

# Verify build.sh and init.sh are executable
for s in scripts/build.sh scripts/init.sh; do
  [[ -x "$SKILL_DIR/$s" ]] || chmod +x "$SKILL_DIR/$s"
done

echo "validate.sh: skill-builder PASS ($LINES lines, all artifacts present)"
