#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: learn$' "$skill_dir/SKILL.md"
grep -Fq 'optional, off-path consumer' "$skill_dir/SKILL.md"
grep -Fq 'no-change' "$skill_dir/SKILL.md"
grep -Fq 'mine-learn.md' "$skill_dir/SKILL.md"
if grep -Eq 'verdict-only input|TTL.d|gets pruned rather than paraphrased' "$skill_dir/SKILL.md"; then
  echo 'learn retains retired source or blind-retention rules' >&2
  exit 1
fi
echo 'learn bounded memory operation: PASS'
