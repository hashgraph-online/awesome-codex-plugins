#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: plan$' "$skill_dir/SKILL.md"
# test_no_model_authored_packet
grep -Fq "Prefer the caller's tracker, if any" "$skill_dir/SKILL.md"
grep -Fq 'Planning produces no AgentOps packet' "$skill_dir/SKILL.md"
if grep -Fq 'plan-packet.v1' "$skill_dir/SKILL.md"; then
  echo 'plan contract references a model-authored plan packet' >&2
  exit 1
fi
echo 'plan skill contract: PASS'
