#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: rpi$' "$skill_dir/SKILL.md"
grep -Fq 'Plan -> Implement -> fresh Validate -> report' "$skill_dir/SKILL.md"
grep -Fq 'dispatches each core phase at most once' "$skill_dir/SKILL.md"
grep -Fq 'creates no AgentOps packet' "$skill_dir/SKILL.md"
! grep -Fq 'plan_packet_digest' "$skill_dir/SKILL.md"
echo 'rpi skill contract: PASS'
