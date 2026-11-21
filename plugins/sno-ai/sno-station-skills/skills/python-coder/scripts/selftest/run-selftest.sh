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
    "honor the declared runtime": "Never emit syntax, stdlib APIs, or typing features newer than the target.",
    "no backward compatibility": "No legacy paths, compatibility wrappers, migration shims, dual-format support, or fallback behavior unless explicitly requested.",
    "no speculative work": "no speculative abstractions or configurability, no error handling for scenarios that cannot happen.",
    "deterministic decisions stay in code": "belong in code, never in a model call.",
    "claims trace to a command run": "every claim must trace to a command actually run this session",
    "no done over failing checks": "never report done with errors outstanding.",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"python-coder: missing load-bearing rules: {', '.join(missing)}")
PY

printf 'python-coder text contract passed\n'
