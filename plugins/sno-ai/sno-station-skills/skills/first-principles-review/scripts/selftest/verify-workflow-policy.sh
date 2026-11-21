#!/usr/bin/env bash
set -Eeuo pipefail

selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
source_skill="$skill_dir/SKILL.md"

[[ -f "$source_skill" ]] || { printf 'missing source skill: %s\n' "$source_skill" >&2; exit 1; }

python3 - "$source_skill" <<'PY'
import pathlib
import sys

text = " ".join(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split())
rules = {
    "accepted input classes": "product idea, design, PRD, or architecture",
    "source-as-evidence boundary": "Source code is evidence about the incumbent, not the main",
    "missing-input recovery": "locate the canonical artifact, repair access within authority",
    "bounded research stop": "cannot change a premise state, the disposition, or the next",
    "deterministic report path": "reports/<input-stem>-first-principles-review.md",
    "preserve existing report": "Use a distinct report filename when the default already exists.",
    "settled-decision protection": "A settled owner decision stays settled unless a specific new fact",
    "single-handoff SPLIT rule": "independently buildable outcomes inside the single handoff object.",
    "post-report one-question interaction": "If a genuine owner decision survives research, ask one decision at a time in chat.",
    "one pass": "this review is one pass (a project may choose otherwise): do not rerun it to confirm",
    "reviewer record": "The report is the record of the review.",
    "no confirmation rerun": "do not turn its output into a new",
    "deterministic fix proof": "proves fixes deterministically",
}
missing = [name for name, phrase in rules.items() if phrase not in text]
if missing:
    raise SystemExit(f"missing operating-policy rules: {', '.join(missing)}")
PY

printf 'workflow policy static contract passed; no model judgment assessed\n'
