#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: reality-check$' "$skill_dir/SKILL.md"
grep -Fq 'Compare an explicit claim with observable evidence' "$skill_dir/SKILL.md"
grep -Fq 'mint a verdict or' "$skill_dir/SKILL.md"
test -f "$skill_dir/schemas/reality-check-report.v1.schema.json"
test -x "$skill_dir/scripts/validate-output.sh"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo|next[_ -]action' \
  "$skill_dir/SKILL.md"; then
  echo 'reality-check contract contains forbidden lifecycle authority' >&2
  exit 1
fi

echo 'reality-check skill contract: PASS'
