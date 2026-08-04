#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: rpi$' "$skill_dir/SKILL.md"
grep -Fq 'Plan -> Implement -> fresh Validate -> report' "$skill_dir/SKILL.md"
grep -Fq 'dispatches each core phase at most once' "$skill_dir/SKILL.md"
grep -Fq 'creates no AgentOps packet' "$skill_dir/SKILL.md"
grep -Fq 'Plan is closed for that intent' "$skill_dir/SKILL.md"
grep -Fq 'spiral breaker' "$skill_dir/SKILL.md"
grep -Fq 'A rising artifact count over an unchanged subject is a stop' "$skill_dir/SKILL.md"
grep -Fq 'This is the default assistant response.' "$skill_dir/SKILL.md"
grep -Fq 'only when the caller requests machine-readable evidence' "$skill_dir/SKILL.md"
grep -Fq 'When no machine artifact was requested, do not create a hidden one.' "$skill_dir/SKILL.md"
if grep -Fq 'plan_packet_digest' "$skill_dir/SKILL.md"; then
  echo 'rpi contract references a model-authored plan packet digest' >&2
  exit 1
fi
echo 'rpi skill contract: PASS'
