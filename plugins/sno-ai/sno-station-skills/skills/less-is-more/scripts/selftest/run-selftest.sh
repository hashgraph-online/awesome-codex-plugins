#!/usr/bin/env bash
# Text contract: the load-bearing rules must still be present in this skill's SKILL.md.
# Only files shipped inside this payload are read.
set -Eeuo pipefail

# Python must not write bytecode here: a generated __pycache__ would leave stray
# files inside the skill directory.
export PYTHONDONTWRITEBYTECODE=1

selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
source_skill="$skill_dir/SKILL.md"

[[ -f "$source_skill" ]] || { printf 'missing source skill: %s\n' "$source_skill" >&2; exit 1; }

python3 - "$source_skill" <<'PY'
import pathlib
import sys

text = " ".join(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split())
rules = {
    "cut runs after build": "After build, run cut on the code you just wrote before handing it over.",
    "checks and hashes are deletion targets": "By default, security checks, blocking preconditions, runtime assertions, and hashes are priority deletion targets, not protected categories.",
    "new security check needs approval": "By default, do not add a new security check on your own initiative.",
    "no replacement gate": "do not replace a deleted check with another gate, approval step, wrapper, or checklist.",
    "ladder stops at first rung": "Stop at the first rung that holds.",
    "requirements are never simplified": "Deliver all requested behavior; simplify the implementation, never the user's requirements.",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"missing less-is-more rules: {', '.join(missing)}")
PY

printf 'less-is-more text contract passed\n'
