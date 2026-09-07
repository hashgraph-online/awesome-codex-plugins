#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <reality-check-report.json>" >&2
  exit 2
fi

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
  and (if has("coverage") then
        (.coverage
          | type == "array"
          and all(.[];
            ((keys - ["goal","disposition","evidence"]) | length == 0)
            and (.goal | text)
            and (.disposition == "confirmed" or .disposition == "gap" or .disposition == "unverifiable")
            and (.evidence | (. == null) or (type == "array" and all(.[]; text)))))
      else true end)
' "$1" >/dev/null || {
  echo "invalid reality-check-report.v1 artifact: $1" >&2
  exit 1
}

echo "valid reality-check-report.v1: $1"
