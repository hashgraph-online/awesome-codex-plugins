#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <pattern-mining.json>" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "pattern-mining validator requires jq, which is not on PATH" >&2
  exit 2
fi

jq -e '
  def text: type == "string" and length > 0;
  . as $result
  | .schema_version == "pattern-mining.v1"
  and (.outcome == "promote" or .outcome == "hypothesis")
  and (.exemplars
    | type == "array" and length > 0 and all(.[]; text)
    and ((unique | length) == length))
  and (.invariants | type == "array" and all(.[]; text))
  and (.variations | type == "array" and all(.[]; text))
  and (.incidental | type == "array" and all(.[]; text))
  and (.holdout | type == "object")
  and (.holdout.source | type == "string")
  and (.holdout.result == "pass" or .holdout.result == "fail" or .holdout.result == "inconclusive" or .holdout.result == "not-run")
  and (.back_application == "pass" or .back_application == "fail" or .back_application == "not-run")
  and (
    if .outcome == "promote" then
      (.exemplars | length >= 3)
      and (.invariants | length > 0)
      and (.holdout.source | text)
      and (($result.exemplars | index($result.holdout.source)) == null)
      and .holdout.result == "pass"
      and .back_application == "pass"
      and .route == "operationalize"
    else
      ((.exemplars | length) < 3 or .holdout.result != "pass" or .back_application != "pass")
      and .route == "no-action"
    end
  )
' "$1" >/dev/null || {
  echo "invalid pattern-mining.v1 artifact: $1" >&2
  exit 1
}

echo "valid pattern-mining.v1: $1"
