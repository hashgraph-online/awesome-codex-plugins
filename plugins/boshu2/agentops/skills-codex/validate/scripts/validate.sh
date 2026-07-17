#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="$(cd "$skill_dir/../.." && pwd)"

grep -q '^name: validate$' "$skill_dir/SKILL.md"
grep -Fq 'PASS`, `FAIL`, or `NOT_PROVEN`' "$skill_dir/SKILL.md"
grep -Fq 'sole' "$skill_dir/SKILL.md"
grep -Fq 'verdict writer' "$skill_dir/SKILL.md"

python3 "$skill_dir/scripts/validate.py" --help >/dev/null
python3 - "$repo_root" <<'PY'
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(sys.argv[1])
names = (
    "subject-manifest.v1.schema.json",
    "verdict.v2.schema.json",
)
for name in names:
    Draft202012Validator.check_schema(json.loads((root / "schemas" / name).read_text(encoding="utf-8")))
PY

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$skill_dir/scripts" -p 'test_validate.py'
echo 'validate skill contract: PASS'
