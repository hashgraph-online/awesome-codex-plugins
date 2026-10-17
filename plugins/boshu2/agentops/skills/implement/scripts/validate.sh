#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: implement$' "$skill_dir/SKILL.md"
# test_runtime_derives_subject
grep -Fq 'ordinary known defects directly.' "$skill_dir/SKILL.md"
grep -Fq 'runtime derive actual changed paths' "$skill_dir/SKILL.md"
if grep -Fq 'candidate-packet.v1' "$skill_dir/SKILL.md"; then
  echo 'implement contract references a model-authored candidate packet' >&2
  exit 1
fi
echo 'implement skill contract: PASS'
