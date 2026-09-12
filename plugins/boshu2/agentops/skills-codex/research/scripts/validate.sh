#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: research$' "$skill_dir/SKILL.md"
grep -q '^## Investigation$' "$skill_dir/SKILL.md"
grep -q '^## Repository tracing$' "$skill_dir/SKILL.md"
grep -q '^## Pattern evidence$' "$skill_dir/SKILL.md"
grep -Fq 'A quick answer needs no report file' "$skill_dir/SKILL.md"
grep -Fq 'Research selects no work' "$skill_dir/SKILL.md"
grep -Fq 'issues no semantic verdict' "$skill_dir/SKILL.md"
grep -Fq 'source_ledger' "$skill_dir/SKILL.md"
grep -Fq 'comparison' "$skill_dir/SKILL.md"
grep -Fq 'do not launch recursive synthesis passes' "$skill_dir/SKILL.md"
test -x "$skill_dir/scripts/codebase-recon/validate-output.sh"
test -x "$skill_dir/scripts/pattern-mining/validate-output.sh"
grep -Fq '"source_ledger"' "$skill_dir/schemas/findings.json"
grep -Fq '"comparison"' "$skill_dir/schemas/findings.json"
grep -q '^Feature: Research answers one bounded question$' \
  "$skill_dir/references/research.feature"
grep -Fq 'Scenario: Multiple caller-supplied reports are synthesized once' \
  "$skill_dir/references/research.feature"
grep -Fq 'agreement, contradiction, and unknown are reported separately' \
  "$skill_dir/references/research.feature"
python3 -m json.tool "$skill_dir/schemas/findings.json" >/dev/null

if rg -n 'ao lookup|ao land|auto-redo|Gate 1|\.agents/rpi/next-work|finding-compiler' \
  "$skill_dir/SKILL.md" "$skill_dir/references" "$skill_dir/schemas"; then
  echo 'research contract contains retired lifecycle behavior' >&2
  exit 1
fi

echo 'research skill contract: PASS'
