#!/usr/bin/env bash
# Text contract for the charter skill: the load-bearing rules must still be stated.
# Reads only this payload's own files, so a deployed copy tests itself.
set -Eeuo pipefail

selftest_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd -- "$selftest_dir/../.." && pwd)"

python3 - "$skill_dir" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
norm = lambda name: " ".join((root / name).read_text(encoding="utf-8").split())
skill = norm("SKILL.md")
template = norm("references/template.md")
rules = {
    "a task is named by its charter file": "A task is named by its charter filename",
    "never invents a decision": "Never invent a decision, a fact or a requirement.",
    "checks are observable": "can be answered pass or fail by a real run or inspection",
    "reasoned preconditions only": "Before adding a precondition, check, section or approval step, name the failure",
    "owner names security checks and full suites": "enters a charter only if the",
    "an agent alone never releases": "an agent alone never releases a charter",
    "one kind of charter": "There is one kind of charter, not sizes.",
}
missing = [name for name, phrase in rules.items() if phrase not in skill]
for phrase in ("## Success checks", "## Proof", "status: draft", "Written only by `sno deliver-proof`"):
    if phrase not in template:
        missing.append(f"template lacks {phrase}")
if missing:
    raise SystemExit(f"missing charter rules: {', '.join(missing)}")
PY

printf 'charter rule contract passed\n'
