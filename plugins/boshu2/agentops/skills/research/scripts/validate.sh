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
# Claimed-state audit, folded in from the retired Reality Check skill.
grep -q '^## Claimed-state audit$' "$skill_dir/SKILL.md"
grep -Fq 'compare an' "$skill_dir/SKILL.md"
grep -Fq 'expected state with observable evidence' "$skill_dir/SKILL.md"
grep -Fq 'live entry point' "$skill_dir/SKILL.md"
grep -Fq 'production path' "$skill_dir/SKILL.md"
grep -Fq 'carries no overall PASS, FAIL, verdict or' "$skill_dir/SKILL.md"
grep -Fq 'references/advice-or-acceptance.md' "$skill_dir/SKILL.md"
grep -Fq '../validate/SKILL.md' "$skill_dir/SKILL.md"
grep -Fq 'goal snapshots and requested' "$skill_dir/SKILL.md"
grep -Fq '](references/goals.md)' "$skill_dir/SKILL.md"
grep -Fq '](references/status.md)' "$skill_dir/SKILL.md"
test -f "$skill_dir/references/goals.md"
test -f "$skill_dir/references/status.md"
test -f "$skill_dir/schemas/reality-check-report.v1.schema.json"
test -x "$skill_dir/scripts/claim-audit/validate-output.sh"
python3 -m json.tool "$skill_dir/schemas/reality-check-report.v1.schema.json" >/dev/null
grep -Fq 'Scenario: A claimed state gets a per-item ledger without a verdict' \
  "$skill_dir/references/research.feature"
grep -Fq '"source_ledger"' "$skill_dir/schemas/findings.json"
grep -Fq '"comparison"' "$skill_dir/schemas/findings.json"
grep -q '^Feature: Research answers one bounded question$' \
  "$skill_dir/references/research.feature"
python3 -m json.tool "$skill_dir/schemas/findings.json" >/dev/null

# grep exits 1 for no match; any other status means the scan did not run.
retired_rc=0
grep -rEn 'ao lookup|ao land|auto-redo|Gate 1|\.agents/rpi/next-work|finding-compiler' \
  "$skill_dir/SKILL.md" "$skill_dir/references" "$skill_dir/schemas" || retired_rc=$?
if [[ "$retired_rc" -eq 0 ]]; then
  echo 'research contract contains retired lifecycle behavior' >&2
  exit 1
elif [[ "$retired_rc" -ne 1 ]]; then
  echo 'research contract: retired-lifecycle scan failed to run' >&2
  exit 2
fi

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo|next[_ -]action' \
  "$skill_dir/SKILL.md"; then
  echo 'research contract contains forbidden lifecycle authority' >&2
  exit 1
fi

echo 'research skill contract: PASS'
