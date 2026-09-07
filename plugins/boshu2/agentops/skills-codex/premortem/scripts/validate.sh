#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: premortem$' "$skill_dir/SKILL.md"
grep -Fq 'optional plan-challenge strategy' "$skill_dir/SKILL.md"
grep -Fq 'It is not part of the required RPI sequence' "$skill_dir/SKILL.md"
grep -Fq 'advisory findings' "$skill_dir/SKILL.md"
grep -q '^Feature: Premortem optionally challenges one frozen plan$' \
  "$skill_dir/references/premortem.feature"
test -f "$skill_dir/schemas/premortem-plan-review.v1.schema.json"
test -x "$skill_dir/scripts/validate-output.sh"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo|next[_ -]action' \
  "$skill_dir/SKILL.md"; then
  echo 'premortem contract contains forbidden lifecycle authority' >&2
  exit 1
fi

echo 'premortem skill contract: PASS'
