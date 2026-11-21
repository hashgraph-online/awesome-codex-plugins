#!/usr/bin/env bash
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill="$(cd -- "$selftest_dir/../.." && pwd)/SKILL.md"

python3 - "$skill" <<'PY'
import pathlib
import sys

text = " ".join(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split())
rules = {
    "one judgment pass": "this audit is one judgment pass: do not rerun it",
    "no prewritten verdict": "Never write a `clean` verdict",
    "immutable receipt": "Keep the actual report immutable",
    "deterministic proof": "prove the fixes deterministically",
    "no confirmation review": "without a model confirmation review",
    "clean is not zero findings": "not zero raw findings",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"missing review-boundary rules: {', '.join(missing)}")
PY

printf 'owner intent audit boundary contract passed\n'
