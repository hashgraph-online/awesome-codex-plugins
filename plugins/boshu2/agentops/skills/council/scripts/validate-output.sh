#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <council-report.json>" >&2
  exit 2
fi

jq -e '
  def text: type == "string" and length > 0;
  ((keys - ["schema_version","question","subject_digest","judges","synthesis","diversity_unsatisfied"]) | length == 0)
  and .schema_version == "council-report.v1"
  and (.question | text)
  and (.subject_digest | type == "string" and test("^[a-f0-9]{64}$"))
  and (if has("diversity_unsatisfied") then (.diversity_unsatisfied | type == "boolean") else true end)
  and (.judges
    | type == "array" and length >= 2
    and all(.[];
      ((keys - ["context_id","methodology","model_identity","judgment","evidence","omissions"]) | length == 0)
      and (.context_id | text)
      and (.methodology | text)
      and (.judgment | text)
      and (if has("model_identity") then (.model_identity | text) else true end)
      and (.evidence | type == "array" and length > 0 and all(.[]; text))
      and (if has("omissions") then (.omissions | type == "array" and all(.[]; text)) else true end)))
  and ((.judges | map(.context_id) | unique | length) == (.judges | length))
  and (.synthesis | type == "object")
  and ((.synthesis | keys - ["consensus","divergence","minority","unresolved","caller_challenge"]) | length == 0)
  and (.synthesis | has("consensus") and has("divergence") and has("minority") and has("unresolved"))
  and (.synthesis.consensus
    | type == "array"
    and all(.[];
      ((keys - ["claim","methodologies"]) | length == 0)
      and (.claim | text)
      and (.methodologies | type == "array" and length > 0 and all(.[]; text))))
  and (.synthesis.divergence
    | type == "array"
    and all(.[];
      ((keys - ["point","positions"]) | length == 0)
      and (.point | text)
      and (.positions | type == "array" and length > 0 and all(.[]; text))))
  and (.synthesis.minority | type == "array" and all(.[]; text))
  and (.synthesis.unresolved | type == "array" and all(.[]; text))
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
' "$1" >/dev/null || {
  echo "invalid council-report.v1 artifact: $1" >&2
  exit 1
}

echo "valid council-report.v1: $1"
