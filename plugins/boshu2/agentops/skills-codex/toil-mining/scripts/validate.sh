#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: toil-mining$' "$skill_dir/SKILL.md"
grep -Fq 'caller-supplied Codex JSONL' "$skill_dir/SKILL.md"
grep -Fq 'recent_human.py --since' "$skill_dir/SKILL.md"
grep -Fq 'retrieval/report-only' "$skill_dir/SKILL.md"

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s "$skill_dir/tests" -p 'test_*.py'

echo 'toil-mining skill contract: PASS'
