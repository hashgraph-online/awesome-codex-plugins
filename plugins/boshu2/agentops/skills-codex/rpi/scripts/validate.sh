#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ADR-0017: RPI is no longer single-pass. Validate repeats inside the bounded
# repair phase, so this contract asserts the phase lock that survives (Plan and
# Implement once) plus positive canaries that each condition of the convergence
# law is present by name.
grep -q '^name: rpi$' "$skill_dir/SKILL.md"
grep -Fq 'Plan -> Implement -> fresh Validate -> bounded repair -> report' "$skill_dir/SKILL.md"
grep -Fq 'dependencies: [anti-ceremony, plan, implement, validate]' "$skill_dir/SKILL.md"
grep -Fq 'invokes the guard exactly once before Plan' "$skill_dir/SKILL.md"
grep -Fq '`STOP`, dispatch no core phase' "$skill_dir/SKILL.md"
grep -Fq 'dispatches Plan and Implement at most once' "$skill_dir/SKILL.md"
grep -Fq '## The convergence law' "$skill_dir/SKILL.md"
grep -Fq 'rounds_used < repair_rounds' "$skill_dir/SKILL.md"
grep -Fq "finding count alone is not useful progress" "$skill_dir/SKILL.md"
grep -Fq 'No finding id closed in an earlier round reopens.' "$skill_dir/SKILL.md"
grep -Fq 'unknown cause stops repair for causal examination' "$skill_dir/SKILL.md"
grep -Fq 'repair round N: k open findings' "$skill_dir/SKILL.md"
grep -Fq '## Waves' "$skill_dir/SKILL.md"
grep -Fq 'This prospective rule never waives a leg already' "$skill_dir/SKILL.md"
grep -Fq '## Cross-family validation' "$skill_dir/SKILL.md"
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
