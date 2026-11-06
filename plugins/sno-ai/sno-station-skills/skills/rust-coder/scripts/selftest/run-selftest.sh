#!/usr/bin/env bash
# Text contract for this skill only. Reads nothing outside this payload.
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd -- "$selftest_dir/../.." && pwd)"

python3 - "$skill_dir" <<'PY'
import pathlib
import sys

skill_dir = pathlib.Path(sys.argv[1])
text = " ".join((skill_dir / "SKILL.md").read_text(encoding="utf-8").split())
rules = {
    "no nested codex process": "Do not launch another Codex process.",
    "standards are read first": "Read [references/standards.md](references/standards.md) completely before editing.",
    "hard cut by default": "Default to a hard cut; preserve compatibility only when an explicitly confirmed published contract requires it.",
    "no compiler appeasement": "abstractions merely to satisfy the compiler.",
    "changed lines trace to the request": "every changed line must trace to the request.",
    "bounded correction rounds": "Stop after three failed correction rounds and report the blocker",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if not (skill_dir / "references" / "standards.md").is_file():
    missing.append("references/standards.md is shipped")
if missing:
    raise SystemExit(f"rust-coder: missing load-bearing rules: {', '.join(missing)}")
PY

printf 'rust-coder text contract passed\n'
