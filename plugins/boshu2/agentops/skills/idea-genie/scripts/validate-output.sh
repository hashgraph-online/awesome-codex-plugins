#!/usr/bin/env bash
set -euo pipefail

# Pass a file path, or - to read an inline packet from stdin.
# Exit 0 valid, 1 invalid, 2 usage or jq missing (not checked).
usage() {
  echo "usage: $0 <idea-portfolio.json | ->" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage
if [[ "$1" == "-" ]]; then
  src=/dev/stdin
  label=stdin
elif [[ -f "$1" ]]; then
  src="$1"
  label="$1"
else
  usage
fi

command -v jq >/dev/null 2>&1 || {
  echo "jq not found: $label was not validated" >&2
  exit 2
}

jq -e '
  def text: type == "string" and length > 0;
  def only($allowed): type == "object" and ((keys - $allowed) | length == 0);
  . as $portfolio
  | only(["schema_version","status","observations","assumptions","candidates","dropped"])
  and .schema_version == "idea-portfolio.v1"
  and (.status == "candidates" or .status == "no-new-work")
  and (.observations
    | type == "array" and length > 0
    and all(.[]; only(["claim","evidence"]) and (.claim | text) and (.evidence | text)))
  and (.assumptions | type == "array" and all(.[]; text))
  and (.candidates
    | type == "array"
    and all(.[];
      only(["id","idea","evidence","overlaps","status_quo","scenario"])
      and (.id | text)
      and (.idea | text)
      and (.evidence
        | type == "array" and length > 0
        and all(.[]; . as $cited | ($portfolio.observations | any(.evidence == $cited))))
      and (.overlaps | type == "array" and all(.[]; text))
      and (.status_quo | text)
      and (.scenario | only(["given","when","then"]))
      and (.scenario.given | text)
      and (.scenario.when | text)
      and (.scenario.then | text))
    and ((map(.id) | unique | length) == length))
  and (if has("dropped") then
      .dropped | type == "array" and all(.[]; only(["idea","reason"]) and (.idea | text) and (.reason | text))
    else true end)
  and (
    if .status == "candidates" then
      (.candidates | length > 0)
    else
      (.candidates | length == 0)
      and (.dropped | type == "array" and length > 0)
    end
  )
' "$src" >/dev/null || {
  echo "invalid idea-portfolio.v1 artifact: $label" >&2
  exit 1
}

echo "valid idea-portfolio.v1: $label"
