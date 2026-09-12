#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: memory$' "$skill_dir/SKILL.md"
grep -Fq 'dependencies: []' "$skill_dir/SKILL.md"
for ref in recall mine-learn curate; do
  test -s "$skill_dir/references/$ref.md"
  grep -Fq "references/$ref.md" "$skill_dir/SKILL.md"
done
grep -Fq 'applicability, action, support, limits and invalidation' "$skill_dir/SKILL.md"
grep -Fq 'public or already-cleared trial inputs only' "$skill_dir/SKILL.md"
grep -Fq 'No blind TTL' "$skill_dir/SKILL.md"
grep -Fq 'Only later' "$skill_dir/SKILL.md"
grep -Fq 'no Git objects or imports before exact' "$skill_dir/references/mine-learn.md"
if grep -Fq 'ao provenance read-source' "$skill_dir/SKILL.md"; then
  echo 'read-source belongs to ao session, not provenance' >&2
  exit 1
fi
echo 'memory operation routing and boundaries: PASS'
