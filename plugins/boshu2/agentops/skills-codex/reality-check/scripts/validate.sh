#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: reality-check$' "$skill_dir/SKILL.md"
grep -Fq 'Compare an expected state with observable evidence' "$skill_dir/SKILL.md"
grep -q '^## Goal measurement$' "$skill_dir/SKILL.md"
grep -q '^## Native status$' "$skill_dir/SKILL.md"
grep -Fq 'without selecting work' "$skill_dir/SKILL.md"
grep -Fq 'issues semantic PASS' "$skill_dir/SKILL.md"
grep -Fq 'goal snapshots and requested report/spec writes' "$skill_dir/SKILL.md"
test -f "$skill_dir/schemas/reality-check-report.v1.schema.json"
test -x "$skill_dir/scripts/validate-output.sh"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo|next[_ -]action' \
  "$skill_dir/SKILL.md"; then
  echo 'reality-check contract contains forbidden lifecycle authority' >&2
  exit 1
fi

echo 'reality-check skill contract: PASS'
