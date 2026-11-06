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
    "strict mode by default": "Start new Bash scripts with `set -Eeuo pipefail`",
    "no eval or string commands": "Never use `eval` or construct executable commands in strings.",
    "quote every expansion": "Quote every expansion unless intentional word splitting is proven and commented.",
    "never print secrets": "Never print secrets, tokens, credential-bearing URLs, raw environment dumps, or sensitive command lines.",
    "no backward compatibility": "No backward-compatibility aliases, dual paths, legacy flags, or fallbacks unless the user confirms an external published contract requires them.",
    "no success over failing checks": "never report success over a failing or skipped required check.",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"shellscript-coder: missing load-bearing rules: {', '.join(missing)}")
PY

printf 'shellscript-coder text contract passed\n'
