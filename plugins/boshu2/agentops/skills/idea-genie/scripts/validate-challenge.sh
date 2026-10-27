#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <idea-challenge.json>" >&2
  exit 2
fi

jq -e '
  def text: type == "string" and length > 0;
  def only($allowed): type == "object" and ((keys - $allowed) | length == 0);
  def optional_text($field): if has($field) then (.[$field] | text) else true end;
  only(["schema_version","door_class","sealed_generation","perspectives","cross_reviews","disagreements","refutations","handoff"])
  and .schema_version == "idea-challenge.v1"
  and .door_class == "one-way"
  and .sealed_generation == true
  and (.perspectives
    | type == "array" and length >= 2
    and all(.[];
      only(["id","context_id","model_identity","proposal"])
      and (.id | text)
      and (.context_id | text)
      and (.proposal | text)
      and optional_text("model_identity"))
    and ((map(.id) | unique | length) == length)
    and ((map(.context_id) | unique | length) == length))
  and ((.perspectives | map(.id)) as $ids
    | .cross_reviews
    | type == "array" and length > 0
    and all(.[];
      only(["reviewer","subject","dimensions"])
      and (.reviewer | text)
      and (.subject | text)
      and (.reviewer != .subject)
      and (.reviewer as $reviewer | $ids | index($reviewer)) != null
      and (.subject as $subject | $ids | index($subject)) != null
      and (.dimensions
        | only(["evidence","reversibility","system_fit","failure_modes","cost"])
        and length > 0
        and all(.[]; text)))
    and (($ids - map(.subject)) | length == 0))
  and (.disagreements | type == "array" and length > 0 and all(.[]; text))
  and (.refutations
    | type == "array" and length > 0
    and all(.[];
      only(["claim","attempt","result"])
      and (.claim | text)
      and (.attempt | text)
      and (.result | text)))
  and (if has("handoff") then
      .handoff
      | only(["owner","artifact_dir","route"])
      and .owner == "plan"
      and (.artifact_dir | text)
      and optional_text("route")
    else true end)
' "$1" >/dev/null || {
  echo "invalid idea-challenge.v1 artifact: $1" >&2
  exit 1
}

echo "valid idea-challenge.v1: $1"
