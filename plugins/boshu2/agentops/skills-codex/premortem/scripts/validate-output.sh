#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <premortem-plan-review.json>" >&2
  exit 2
fi

python3 - "$1" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    value = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"premortem plan review: unreadable JSON: {exc}", file=sys.stderr)
    raise SystemExit(1)

required = {
    "schema_version", "intent_digest", "author_context_id",
    "judge_context_id", "findings", "checked", "not_checked",
}
if set(value) != required:
    print("premortem plan review: unexpected or missing fields", file=sys.stderr)
    raise SystemExit(1)
if value["schema_version"] != "premortem-plan-review.v1":
    raise SystemExit("premortem plan review: wrong schema_version")
if not re.fullmatch(r"[a-f0-9]{64}", value["intent_digest"]):
    raise SystemExit("premortem plan review: invalid intent digest")
author = value["author_context_id"]
judge = value["judge_context_id"]
if not isinstance(author, str) or not author or not isinstance(judge, str) or not judge or author == judge:
    raise SystemExit("premortem plan review: author and judge identities must be nonempty and distinct")
for field in ("checked", "not_checked"):
    if not isinstance(value[field], list) or not all(isinstance(item, str) for item in value[field]):
        raise SystemExit(f"premortem plan review: {field} must be a string array")
if not isinstance(value["findings"], list):
    raise SystemExit("premortem plan review: findings must be an array")
for finding in value["findings"]:
    if not isinstance(finding, dict) or set(finding) != {"id", "statement", "evidence"}:
        raise SystemExit("premortem plan review: malformed finding")
    if not all(isinstance(finding[key], str) and finding[key] for key in ("id", "statement")):
        raise SystemExit("premortem plan review: finding id and statement are required")
    evidence = finding["evidence"]
    if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item for item in evidence):
        raise SystemExit("premortem plan review: each finding needs evidence")
print("premortem plan review: valid")
PY
