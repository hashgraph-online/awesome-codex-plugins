#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: plan$' "$skill_dir/SKILL.md"
# test_no_model_authored_packet
grep -Fq "Prefer the caller's tracker, if any" "$skill_dir/SKILL.md"
grep -Fq 'Planning produces no AgentOps packet' "$skill_dir/SKILL.md"
! grep -Fq 'plan-packet.v1' "$skill_dir/SKILL.md"
echo 'plan skill contract: PASS'
