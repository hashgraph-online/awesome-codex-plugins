#!/usr/bin/env bash
# Text contract for e2e-red-triage. Reads only files shipped in this payload.
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill_root="${1:-$(cd -- "$selftest_dir/../.." && pwd)}"

python3 - "$skill_root" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
text = " ".join((root / "SKILL.md").read_text(encoding="utf-8").split())

rules = {
    "manual only, one named caller": "NEVER auto-load from context",
    "split the collapsed result": "what are the two halves of this",
    "instrument before touching the product": "The first commit after this kind of red does not touch product behaviour.",
    "calibrate every new check": "Feed every new check a known-wrong input and watch it go red.",
    "close only with a durable check": "coming back with nothing durable is not",
    "stuck is not a pass": "a run that produced no verdict at all is not a pass and not a skip",
}

missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    print(f"SKILL.md: missing rules: {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(1)
PY

printf 'e2e-red-triage text contract passed\n'
