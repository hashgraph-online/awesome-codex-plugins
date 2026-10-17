#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "usage: $0 <idea-challenge.json>" >&2
  exit 2
fi

jq -e '
  def text: type == "string" and length > 0;
  . as $packet
  | ((keys - ["schema_version","door_class","sealed_generation","perspectives","cross_reviews","disagreements","refutations","handoff","requires_ntm"]) | length == 0)
  and .schema_version == "idea-challenge.v1"
  and (.door_class == "one-way" or .door_class == "two-way")
  and (.sealed_generation | type == "boolean")
  and (.perspectives | type == "array")
  and (.cross_reviews | type == "array")
  and (.disagreements | type == "array" and all(.[]; text))
  and (.refutations | type == "array")
  and (.handoff | type == "object")
  and ((.handoff | keys - ["owner","artifact_dir","route"]) | length == 0)
  and .handoff.owner == "plan"
  and (.handoff.artifact_dir | text)
  and (
    if .door_class == "one-way" then
      .sealed_generation == true
      and (.perspectives
        | length >= 2
        and all(.[]; (.id | text) and (.context_id | text)))
      and ((.perspectives | map(.id) | unique | length) == (.perspectives | length))
      and ((.perspectives | map(.context_id) | unique | length) == (.perspectives | length))
      and ((.perspectives | map(.id)) as $ids
        | (.cross_reviews
          | length > 0
          and all(.[];
            .reviewer as $reviewer
            | .subject as $subject
            | ($reviewer | text)
            and ($subject | text)
            and ($reviewer != $subject)
            and (($ids | index($reviewer)) != null)
            and (($ids | index($subject)) != null)
            and (.dimensions
              | type == "object" and length > 0 and all(.[]; text)))))
      and ($packet.disagreements | length > 0)
      and ($packet.refutations
        | length > 0
        and all(.[]; (.claim | text) and (.attempt | text) and (.result | text)))
      and ($packet | has("requires_ntm") | not)
    else
      .sealed_generation == false
      and (.perspectives | length == 0)
      and (.cross_reviews | length == 0)
      and (.disagreements | length == 0)
      and (.refutations | length == 0)
      and .requires_ntm == false
      and .handoff.route == "single-fresh-context"
    end
  )
' "$1" >/dev/null || {
  echo "invalid idea-challenge.v1 artifact: $1" >&2
  exit 1
}

echo "valid idea-challenge.v1: $1"
