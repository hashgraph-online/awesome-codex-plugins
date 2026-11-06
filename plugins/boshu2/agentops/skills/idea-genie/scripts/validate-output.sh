#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <idea-portfolio.json>" >&2
  exit 2
fi

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
' "$1" >/dev/null || {
  echo "invalid idea-portfolio.v1 artifact: $1" >&2
  exit 1
}

echo "valid idea-portfolio.v1: $1"
