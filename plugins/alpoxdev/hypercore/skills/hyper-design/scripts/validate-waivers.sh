#!/usr/bin/env bash
# Validate an optional .ai-slop-remover.json waiver document against the rule registry.
set -euo pipefail

VW_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$VW_DIR/rule-registry.sh"

VW_USAGE='Usage: bash validate-waivers.sh --input <.ai-slop-remover.json> [--json]'

vw_prog() {
  cat <<'VW_JQ'
# V8 accepts every day of month 1-31 and rolls overflow over, so the check mirrors that.
def valid_date:
  if type != "string" then false
  elif (test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$") | not) then false
  else (capture("^(?<y>[0-9]{4})-(?<m>[0-9]{2})-(?<d>[0-9]{2})$")) as $p
    | ($p.y | tonumber) as $y | ($p.m | tonumber) as $m | ($p.d | tonumber) as $d
    | ($m >= 1 and $m <= 12 and $d >= 1 and $d <= 31)
  end;
def has_text: if type == "string" then (gsub("^[\\s]+|[\\s]+$"; "") != "") else false end;
def allowed_keys: ["ruleId", "value", "file", "reason", "source", "reviewAfter"];
def known_rule($id; $ids): if ($id | type) != "string" then false else ($ids | index("," + $id + ",")) != null end;
def waiver_errors($l; $w; $ids; $sources):
  if ($w | type) != "object" then "\($l) must be an object."
  else
    (if known_rule($w.ruleId; $ids) then empty else "\($l).ruleId must name a known rule." end),
    (if ($w.reason | has_text) then empty else "\($l).reason must be non-empty." end),
    (if ($w.source | type) == "string" and (($sources | index($w.source)) != null)
       then empty else "\($l).source is invalid." end),
    (($w.value | has_text) as $hasValue | ($w.file | has_text) as $hasFile
      | if ($hasValue == $hasFile) then "\($l) requires exactly one of value or file." else empty end),
    (if (($w.file | type) == "string") and ($w.file != "") and
        (($w.file == "*") or (($w.file | index("**")) != null))
       then "\($l).file must be a narrow file path, not a broad glob." else empty end),
    (if ($w | has("reviewAfter")) and (($w.reviewAfter | valid_date) | not)
       then "\($l).reviewAfter must be an absolute valid YYYY-MM-DD date." else empty end),
    ($w | keys_unsorted[]) as $key
      | if (allowed_keys | index($key)) == null then "\($l).\($key) is not allowed." else empty end
  end;
def validate($ids; $sources):
  if type != "object" then ["Waiver document must be an object."]
  else
    ([ (if .version != 1 then "version must equal 1." else empty end),
       (if (.waivers | type) != "array" then "waivers must be an array." else empty end) ]
     + (if (.waivers | type) == "array" then
          [ .waivers | to_entries[] | "waivers[\(.key)]" as $l | waiver_errors($l; .value; $ids; $sources) ]
        else [] end))
  end;
validate($ids; ["user-confirmed", "documented-brand", "fixture", "generated-output"])
VW_JQ
}

vw_main() {
  local input='' json=0 help=0 ids errors ok
  while [ $# -gt 0 ]; do
    case "$1" in
      --input) shift; input=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift; break ;;
      *) printf '%s\n' "$(jq -cn --arg error "Unknown argument: $1" '{ok: false, error: $error}')" >&2; exit 2 ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$VW_USAGE"
    return 0
  fi
  [ -n "$input" ] || { printf '%s\n' '{"ok":false,"error":"--input requires a path"}' >&2; exit 2; }
  local abs ftypes
  abs=$(cd -- "$(dirname -- "$input")" 2>/dev/null && pwd -P)/$(basename -- "$input")
  if [ ! -f "$input" ] || [ ! -r "$input" ]; then
    printf '%s\n' "$(jq -cn --arg error "Invalid waiver JSON: ENOENT: no such file or directory, open '$abs'" '{ok: false, error: $error}')" >&2
    exit 2
  fi
  if ! jq . "$input" > /dev/null 2>&1; then
    printf '%s\n' "$(jq -cn --arg error 'Invalid waiver JSON: malformed JSON document' '{ok: false, error: $error}')" >&2
    exit 2
  fi
  ftypes=$(jq -r 'if type == "object" then (.waivers | type) else "null" end' "$input")
  if [ "$ftypes" != "null" ] && [ "$ftypes" != "array" ]; then
    printf '%s\n' '{"ok":false,"error":"waivers.entries is not a function"}' >&2
    exit 2
  fi
  ids=","
  while IFS= read -r id; do ids="$ids$id,"; done < <(rule_registry_rows | cut -f1)
  errors=$(jq -c --arg ids "$ids" "$(vw_prog)" "$input")
  ok=false
  if [ "$(printf '%s' "$errors" | jq 'length')" = 0 ]; then ok=true; fi
  if [ "$json" = 1 ]; then
    jq -n --argjson ok "$ok" --argjson errors "$errors" '{ok: $ok, errors: $errors}'
  elif [ "$ok" = true ]; then
    printf 'Waiver document is valid.\n'
  else
    printf '%s' "$errors" | jq -r '.[]'
  fi
  [ "$ok" = true ]
}

vw_main "$@"
