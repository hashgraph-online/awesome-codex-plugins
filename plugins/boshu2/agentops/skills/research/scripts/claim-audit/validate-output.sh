#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <reality-check-report.json>" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "reality-check-report validator requires jq, which is not on PATH" >&2
  exit 2
fi

# coverage is the per-item ledger: at least one row, and every confirmed or gap
# row cites evidence. An unverifiable row may name what would settle it.
jq -e '
  def text: type == "string" and length > 0;
  ((keys - ["schema_version","claim","findings","coverage"]) | length == 0)
  and .schema_version == "reality-check-report.v1"
  and (.claim | text)
  and (.findings
    | type == "array" and length > 0
    and all(.[];
      ((keys - ["category","statement","evidence"]) | length == 0)
      and (.category == "confirmed" or .category == "gap"
        or .category == "incomplete-evidence" or .category == "changed-assumption")
      and (.statement | text)
      and (.evidence | type == "array" and length > 0 and all(.[]; text))))
  and (.coverage
    | type == "array" and length > 0
    and all(.[];
      . as $row
      | ((keys - ["goal","disposition","evidence"]) | length == 0)
      and ($row.goal | text)
      and ($row.disposition == "confirmed" or $row.disposition == "gap" or $row.disposition == "unverifiable")
      and (if $row.disposition == "unverifiable"
           then ((has("evidence") | not) or ($row.evidence | type == "array" and all(.[]; text)))
           else ($row.evidence | type == "array" and length > 0 and all(.[]; text)) end)))
' "$1" >/dev/null || {
  echo "invalid reality-check-report.v1 artifact: $1" >&2
  exit 1
}

echo "valid reality-check-report.v1: $1"
