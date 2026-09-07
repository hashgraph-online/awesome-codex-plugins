#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: postmortem$' "$skill_dir/SKILL.md"
grep -Fq 'retrospective causal analysis' "$skill_dir/SKILL.md"
grep -Fq 'does not re-run acceptance validation' "$skill_dir/SKILL.md"
grep -Fq 'counterfactual' "$skill_dir/SKILL.md"
grep -Fq 'Empty or inconclusive analysis is valid' "$skill_dir/SKILL.md"
grep -q '^Feature: Postmortem tests retrospective causal claims$' "$skill_dir/references/postmortem.feature"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)' "$skill_dir/SKILL.md"; then
  echo 'postmortem contract contains forbidden delivery or tracker execution' >&2
  exit 1
fi

echo 'postmortem skill contract: PASS'
