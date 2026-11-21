#!/usr/bin/env bash
set -euo pipefail
# Static package/contract checks only; no report or causal claim is evaluated.

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: postmortem$' "$skill_dir/SKILL.md"
grep -Fq 'retrospective causal analysis' "$skill_dir/SKILL.md"
grep -Fq 'does not re-run acceptance validation' "$skill_dir/SKILL.md"
grep -Fq 'counterfactual' "$skill_dir/SKILL.md"
grep -Fq 'Empty or inconclusive analysis is valid' "$skill_dir/SKILL.md"

forbidden='ao (pawl|land)|git (commit|push)|(bd|br) (close|update|create)'
# Seeded case: the guard must catch this repository's live tracker (BD), not only br.
grep -Eiq "$forbidden" <<<'bd close age-1' || { echo 'tracker guard misses bd' >&2; exit 1; }
if grep -Eiq "$forbidden" "$skill_dir/SKILL.md"; then
  echo 'postmortem contract contains forbidden delivery or tracker execution' >&2
  exit 1
fi

echo 'postmortem static package contract: PASS (report truth not checked)'
