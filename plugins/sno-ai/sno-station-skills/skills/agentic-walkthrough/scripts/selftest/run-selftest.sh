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
    "take the program seat": "BE the executor, then make the executor prove itself.",
    "check the consumer side of the last hop": "Check the reader's path, not the writer's",
    "report a number a no-op could not produce": "Finish with a number a no-op could not have produced, plus the line where each action happens.",
    "zero is a broken path, not a result": "Zero is a failure of the walk, not a result.",
    "an unnamed line is not proof": "If you cannot name the line, that action is not proven to run.",
    "prove the instrument can answer otherwise": "Prove your check could have produced the other answer",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"agentic-walkthrough: missing load-bearing rules: {', '.join(missing)}")
PY

printf 'agentic-walkthrough text contract passed\n'
