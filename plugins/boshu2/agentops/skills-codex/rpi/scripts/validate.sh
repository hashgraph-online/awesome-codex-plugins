#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ADR-0017's lean amendment removes the native phase lock while preserving
# exact fresh judgment and real bounds. The pure adapter is checked separately.
grep -q '^name: rpi$' "$skill_dir/SKILL.md"
grep -Fq 'dependencies: [plan, implement, validate]' "$skill_dir/SKILL.md"
grep -Fq 'Own the authorized outcome through finish.' "$skill_dir/SKILL.md"
grep -Fq 'ordinary known' "$skill_dir/SKILL.md"
grep -Fq 'Acceptance changes need caller authority.' "$skill_dir/SKILL.md"
grep -Fq 'at most one bounded' "$skill_dir/SKILL.md"
grep -Fq 'reviewers remain required.' "$skill_dir/SKILL.md"
grep -Fq 'author-distinct' "$skill_dir/SKILL.md"
grep -Fq 'no fixed ten-minute cap' "$skill_dir/SKILL.md"
grep -Fq 'empty' "$skill_dir/SKILL.md"
grep -Fq 'When no machine' "$skill_dir/SKILL.md"
if grep -Eq 'Plan is closed for that intent|dependencies:.*anti-ceremony|plan_packet_digest' "$skill_dir/SKILL.md"; then
  echo 'rpi retains a retired phase lock, mandatory specialist or planning packet' >&2
  exit 1
fi
for ref in boundaries bounded-adapter outer-goal; do
  test -s "$skill_dir/references/$ref.md"
done
echo 'rpi lean skill contract: PASS'
