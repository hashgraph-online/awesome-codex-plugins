#!/bin/sh
# Installed contract checks. Python/schema/reference tests live in ../tests.
set -eu
skill_dir=$(CDPATH='' cd "$(dirname "$0")/.." && pwd)
grep -q '^name: validate$' "$skill_dir/SKILL.md"
grep -Fq 'PASS`, `FAIL`, or `NOT_PROVEN`' "$skill_dir/SKILL.md"
grep -Fq 'sole semantic author of `verdict.v2`' "$skill_dir/SKILL.md"
grep -Fq 'Only when the caller requests machine-readable evidence' "$skill_dir/SKILL.md"
grep -Fq 'nonempty implementation candidate' "$skill_dir/SKILL.md"
echo 'validate installed skill contract: PASS'
