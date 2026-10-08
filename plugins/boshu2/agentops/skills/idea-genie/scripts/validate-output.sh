#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <idea-portfolio.json>" >&2
  exit 2
fi

jq -e '
  def text: type == "string" and length > 0;
  .schema_version == "idea-portfolio.v1"
  and (.status == "candidates" or .status == "no-new-work")
  and (.observations
    | type == "array" and length > 0
    and all(.[]; (.claim | text) and (.evidence | text)))
  and (.assumptions | type == "array" and all(.[]; text))
  and (.candidates | type == "array")
  and (.termination | type == "object")
  and (.termination.novel_candidates_last_pass == 0)
  and (
    if .status == "candidates" then
      .termination.reason == "novelty-saturated"
      and (.candidates
        | length > 0
        and all(.[];
          (.id | text)
          and (.evidence | type == "array" and length > 0 and all(.[]; text))
          and (.overlaps | type == "array" and all(.[]; text))
          and (.scenario | type == "object")
          and (.scenario.given | text)
          and (.scenario.when | text)
          and (.scenario.then | text)))
    else
      .termination.reason == "all-overlap-or-unsupported"
      and (.candidates | length == 0)
    end
  )
' "$1" >/dev/null || {
  echo "invalid idea-portfolio.v1 artifact: $1" >&2
  exit 1
}

echo "valid idea-portfolio.v1: $1"
