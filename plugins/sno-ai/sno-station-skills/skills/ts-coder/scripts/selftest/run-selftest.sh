#!/usr/bin/env bash
# Text contract for this skill only. Reads nothing outside this payload.
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill="$(cd -- "$selftest_dir/../.." && pwd)/SKILL.md"

python3 - "$skill" <<'PY'
import pathlib
import sys

text = " ".join(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split())
rules = {
    "no backward compatibility": "No legacy paths, compatibility wrappers, migration shims, dual-format support, or fallback behavior unless explicitly requested.",
    "no any escape hatch": "`unknown` + narrowing over `any`.",
    "no speculative work": "No unrequested options/flags/configurability",
    "deterministic decisions stay in code": "belong in code, never in a model call.",
    "no unrequested suite expansion": "Never expand to a package-wide or workspace-wide test suite without an explicit human request.",
    "no done over failing checks": "never report done with errors outstanding.",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"ts-coder: missing load-bearing rules: {', '.join(missing)}")
PY

printf 'ts-coder text contract passed\n'
