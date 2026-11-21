#!/usr/bin/env bash
# Text contract for e2e-environment-preflight. Reads only files shipped in this payload.
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill_root="${1:-$(cd -- "$selftest_dir/../.." && pwd)}"

python3 - "$skill_root" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
text = " ".join((root / "SKILL.md").read_text(encoding="utf-8").split())

rules = {
    "manual only, named callers": "NEVER auto-load from context",
    "amber is red": "No row starts while any check is red. Amber is red.",
    "checks never repair": "Checks; never repairs.",
    "credential proved by a real call": "only a real call that returned a real response passes",
    "every check calibrated red once": "A check nobody has watched go red is not a check.",
    "environment red owes a check": "no such check exists, it is written before the journey closes",
}

missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    print(f"SKILL.md: missing rules: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(1)
PY

printf 'e2e-environment-preflight text contract passed\n'
