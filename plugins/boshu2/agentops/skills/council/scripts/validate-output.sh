#!/usr/bin/env bash
# Validate a council-report.v1 artifact. Pass a file path, or - to read an
# inline report from stdin. Exit 0 valid, 1 invalid, 2 usage.
set -euo pipefail

usage() {
  echo "usage: $0 <council-report.json | ->" >&2
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

jq -e '
  def text: type == "string" and length > 0;
  def non_verdict: text and (ascii_downcase | test("^\\s*(pass|fail|not_proven)\\s*$") | not);
  def text_list: type == "array" and all(.[]; text);
  def text_set: text_list and length > 0 and (unique | length) == length;
  (.judges | map(.methodology)) as $methods
  | (.judges | map(.model_identity // empty)) as $models
  | ((keys - ["schema_version","question","subject_digest","recommendation","judges","synthesis","diversity_unsatisfied"]) | length == 0)
  and .schema_version == "council-report.v1"
  and (.question | text)
  and (.subject_digest | type == "string" and test("^[a-f0-9]{64}$"))
  and (if has("recommendation") then (.recommendation | non_verdict) else true end)
  and (if has("diversity_unsatisfied") then (.diversity_unsatisfied | type == "boolean" or text_list) else true end)
  and (.judges
    | type == "array" and length >= 2
    and all(.[];
      ((keys - ["context_id","methodology","model_identity","judgment","evidence","omissions"]) | length == 0)
      and (.context_id | text)
      and (.methodology | text)
      and (.judgment | non_verdict)
      and (if has("model_identity") then (.model_identity | text) else true end)
      and (.evidence | type == "array" and length > 0 and all(.[]; text))
      and (if has("omissions") then (.omissions | text_list) else true end)))
  and ((.judges | map(.context_id) | unique | length) == (.judges | length))
  and (.synthesis | type == "object")
  and ((.synthesis | keys - ["consensus","divergence","minority","unresolved","notes","caller_challenge"]) | length == 0)
  and (.synthesis | has("consensus") and has("divergence") and has("minority") and has("unresolved"))
  and (.synthesis.consensus
    | type == "array"
    and all(.[];
      ((keys - ["claim","methodologies","models","weighs_as_one"]) | length == 0)
      and (.claim | text)
      and (.methodologies | text_set and all(.[]; . as $m | $methods | any(. == $m)))
      and (if has("models") then (.models | text_set and all(.[]; . as $m | $models | any(. == $m))) else true end)
      and (if has("weighs_as_one") then (.weighs_as_one | type == "boolean") else true end)
      and (if (.methodologies | length) < 2 or (has("models") and (.models | length) < 2)
           then .weighs_as_one == true else true end)))
  and (.synthesis.divergence
    | type == "array"
    and all(.[];
      ((keys - ["point","positions"]) | length == 0)
      and (.point | text)
      and (.positions | type == "array" and length > 0 and all(.[]; text))))
  and (.synthesis.minority | text_list)
  and (.synthesis.unresolved | text_list)
  and (if (.synthesis | has("notes")) then (.synthesis.notes | text_list) else true end)
  and (if (.synthesis | has("caller_challenge")) then (.synthesis.caller_challenge
    | type == "array"
    and all(.[];
      ((keys - ["caller_stated","judges_recommend","judge_count","reasoning","context_possibly_missing","cost_if_wrong","disagreement_kind"]) | length == 0)
      and (.caller_stated | text)
      and (.judges_recommend | text)
      and (.reasoning | text)
      and (.context_possibly_missing | text)
      and (.cost_if_wrong | text)
      and (if has("judge_count") then (.judge_count | type == "number" and . >= 2 and . == (. | floor)) else true end)
      and (if has("disagreement_kind") then (.disagreement_kind as $k | ["preference","security","feasibility"] | index($k) != null) else true end)))
    else true end)
' "$src" >/dev/null || {
  echo "invalid council-report.v1 artifact: $label" >&2
  exit 1
}

echo "valid council-report.v1: $label"
