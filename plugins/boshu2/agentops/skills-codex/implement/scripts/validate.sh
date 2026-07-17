#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: implement$' "$skill_dir/SKILL.md"
# test_runtime_derives_subject
grep -Fq 'exactly one bounded experiment' "$skill_dir/SKILL.md"
grep -Fq 'runtime derive actual changed paths' "$skill_dir/SKILL.md"
! grep -Fq 'candidate-packet.v1' "$skill_dir/SKILL.md"
echo 'implement skill contract: PASS'
