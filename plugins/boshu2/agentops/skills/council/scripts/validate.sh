#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: council$' "$skill_dir/SKILL.md"
grep -Fq 'optional judgment strategy' "$skill_dir/SKILL.md"
grep -Fq 'does not mint a verdict of any version' "$skill_dir/SKILL.md"
test -f "$skill_dir/schemas/council-report.v1.schema.json"
test -x "$skill_dir/scripts/validate-output.sh"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo' \
  "$skill_dir/SKILL.md"; then
  echo 'council contract contains forbidden lifecycle authority' >&2
  exit 1
fi

echo 'council skill contract: PASS'
