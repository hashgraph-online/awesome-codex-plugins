#!/usr/bin/env bash
export PYTHONDONTWRITEBYTECODE=1
set -euo pipefail

selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
validator="$skill_dir/scripts/validate-report.py"
fixtures="$selftest_dir/fixtures"

[[ -f "$validator" ]] || { echo "missing validator: $validator" >&2; exit 1; }

temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
for disposition in PROCEED REFRAME SIMPLIFY REPLACE SPLIT TEST-FIRST STOP; do
  report="$temporary/$disposition.md"
  python3 - "$fixtures/valid-report.md" "$report" "$disposition" <<'PY'
import json
import pathlib
import re
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
destination = pathlib.Path(sys.argv[2])
disposition = sys.argv[3]
fence = chr(96) * 3
match = re.search(rf"{fence}json\s*\n(.*?)\n{fence}", source, re.DOTALL)
if not match:
    raise SystemExit("valid fixture lacks JSON handoff")
handoff = json.loads(match.group(1))
handoff["selected_direction"]["disposition"] = disposition
handoff["selected_direction"]["split_outcomes"] = (
    ["Independently buildable outcome one", "Independently buildable outcome two"]
    if disposition == "SPLIT"
    else []
)
replacement = fence + "json\n" + json.dumps(handoff, separators=(",", ":")) + "\n" + fence
report = source[:match.start()] + replacement + source[match.end():]
destination.write_text(
    report.replace("**Disposition:** REFRAME", f"**Disposition:** {disposition}", 1),
    encoding="utf-8",
)
PY
  python3 "$validator" "$report"
done

python3 - "$fixtures/scenarios" <<'PY'
import pathlib
import sys

directory = pathlib.Path(sys.argv[1])
expectations = {
    "raw-idea-reframe.md": "REFRAME",
    "inherited-constraint-test-first.md": "TEST-FIRST",
    "sound-design-proceed.md": "PROCEED",
}
sections = (
    "## Research Receipt",
    "## True Outcome",
    "## Constraint and Assumption Analysis",
    "## Premise Ledger",
    "## Alternatives",
    "## Primary Recommendation",
    "## Falsifiers",
    "## PRD Handoff",
)
for name, disposition in expectations.items():
    report = (directory / name).read_text(encoding="utf-8")
    for section in sections:
        if section not in report:
            raise SystemExit(f"{name}: missing {section}")
    if f"**Disposition:** {disposition}" not in report:
        raise SystemExit(f"{name}: expected {disposition}")
    if "```json" not in report:
        raise SystemExit(f"{name}: missing embedded JSON handoff")
    owner_section = report.split("## Owner Decisions", 1)[1].split("## PRD Handoff", 1)[0]
    if "?" in owner_section:
        raise SystemExit(f"{name}: owner decision is phrased as a question")

raw_idea = (directory / "raw-idea-reframe.md").read_text(encoding="utf-8")
if "eliminate the need" not in raw_idea.lower() or "reuse incumbent capability" not in raw_idea.lower():
    raise SystemExit("raw idea: alternatives are not materially distinct")
if "fixed candidate count" in "\n".join(path.read_text(encoding="utf-8") for path in directory.glob("*.md")).lower():
    raise SystemExit("scenarios must not force novelty or a fixed candidate count")
PY

for report in "$fixtures/scenarios"/*.md; do
  python3 "$validator" "$report"
done

echo "scenario static contract passed; no model judgment assessed"
