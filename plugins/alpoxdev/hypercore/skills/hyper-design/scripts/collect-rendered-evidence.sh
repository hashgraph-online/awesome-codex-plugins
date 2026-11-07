#!/usr/bin/env bash
# Validate a browser-evidence handoff document and emit only the observations it proves.
set -euo pipefail

CE_USAGE='Usage: bash collect-rendered-evidence.sh --input <capture.json> [--json]'

ce_prog() {
  cat <<'CE_JQ'
def is_record: type == "object";
def is_positive: (type == "number") and (. > 0);
def rect_shape: is_record and (. as $r | ["x", "y", "width", "height"] | all(.[]; ($r[.] | type) == "number"));
def computed_shape: is_record and (all(.[]; type == "string"));
def has_any_evidence:
  ((.rect | rect_shape) or ((.overflowX | type) == "boolean") or ((.focusVisible | type) == "boolean")
   or ((.reducedMotion | type) == "boolean") or (.computed | computed_shape));
def date_ok:
  if type != "string" then false
  elif (test("^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\\.[0-9]+)?)?(Z|[+-][0-9]{2}:[0-9]{2})?)?$") | not) then false
  else (capture("^(?<y>[0-9]{4})-(?<m>[0-9]{2})-(?<d>[0-9]{2})")) as $p
    | (($p.m | tonumber) >= 1 and ($p.m | tonumber) <= 12 and ($p.d | tonumber) >= 1 and ($p.d | tonumber) <= 31)
  end;
def states: ["default", "hover", "focus", "active", "disabled", "loading", "empty", "error"];
def observation_errors($label):
  if is_record | not then ["\($label) must be an object."]
  else
    [ (if ((.locator | type) == "string") and ((.locator | gsub("^[\\s]+|[\\s]+$"; "")) != "")
         then empty else "\($label).locator must be non-empty." end),
      (if has_any_evidence then empty
         else "\($label) needs a rect, overflowX, focusVisible, reducedMotion, or string computed value." end) ]
  end;
def capture_errors($label):
  if is_record | not then ["\($label) must be an object."]
  else
    [ (if ((.viewport | is_record) and (.viewport.width | is_positive) and (.viewport.height | is_positive))
         then empty else "\($label).viewport requires positive width and height." end),
      (if (.state as $s | (states | index($s)) != null) then empty else "\($label).state is invalid." end),
      (if (.capturedAt | date_ok) then empty else "\($label).capturedAt must be an ISO date-time." end),
      (if ((.observations | type) == "array") and ((.observations | length) > 0)
         then empty else "\($label).observations must be non-empty." end) ]
    + (if (.observations | type) == "array" then
         [ range(0; (.observations | length)) as $j
           | "\($label).observations[\($j)]" as $ol
           | (.observations[$j] | observation_errors($ol)) ] | add // []
       else [] end)
  end;
def validate:
  if is_record | not then {errors: ["Evidence handoff must be an object."], observations: []}
  else
    {errors: ([ (if .version != 1 then "version must equal 1." else empty end),
                (if ((.surface | type) == "string") and ((.surface | gsub("^[\\s]+|[\\s]+$"; "")) != "")
                   then empty else "surface must be a non-empty string." end),
                (if ((.captures | type) == "array") and ((.captures | length) > 0)
                   then empty else "captures must be a non-empty array." end) ]
              + (if (.captures | type) == "array" then
                   [ range(0; (.captures | length)) as $i
                     | "captures[\($i)]" as $label
                     | (.captures[$i] | capture_errors($label)) ] | add // []
                 else [] end)),
     observations: (if (.captures | type) == "array" then
       [ .captures[] as $c | select(($c | is_record) and (($c.observations | type) == "array")) |
         $c.observations[] | select(type == "object") |
         {viewport: $c.viewport, state: $c.state, locator: .locator}
         + (if has("rect") then {rect: .rect} else {} end)
         + (if has("overflowX") then {overflowX: .overflowX} else {} end)
         + (if has("focusVisible") then {focusVisible: .focusVisible} else {} end)
         + (if has("reducedMotion") then {reducedMotion: .reducedMotion} else {} end)
         + (if has("computed") then {computed: .computed} else {} end) ]
     else [] end)}
  end;
validate
CE_JQ
}

ce_main() {
  local input='' json=0 help=0 abs result ok bad_type
  while [ $# -gt 0 ]; do
    case "$1" in
      --input) shift; input=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --help|-h) help=1; shift; break ;;
      *) printf '%s\n' "$(jq -cn --arg error "Unknown argument: $1" '{ok: false, error: $error}')" >&2; exit 2 ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$CE_USAGE"
    return 0
  fi
  [ -n "$input" ] || { printf '%s\n' '{"ok":false,"error":"--input requires a path"}' >&2; exit 2; }
  abs=$(cd -- "$(dirname -- "$input")" 2>/dev/null && pwd -P)/$(basename -- "$input")
  if [ ! -f "$input" ] || [ ! -r "$input" ]; then
    printf '%s\n' "$(jq -cn --arg error "Invalid evidence JSON: ENOENT: no such file or directory, open '$abs'" '{ok: false, error: $error}')" >&2
    exit 2
  fi
  if ! jq . "$input" > /dev/null 2>&1; then
    printf '%s\n' "$(jq -cn --arg error 'Invalid evidence JSON: malformed JSON document' '{ok: false, error: $error}')" >&2
    exit 2
  fi
  bad_type=$(jq -r '
    if type == "object" then
      (if (.captures != null) and ((.captures | type) != "array") then "captures.entries is not a function" else "" end),
      (if (.captures | type) == "array" then
         [ .captures[] | select(type == "object") | .observations
           | select(. != null and (type != "array")) ] | if length > 0 then "observations.entries is not a function" else "" end
       else "" end)
    else "" end' "$input" 2>/dev/null | LC_ALL=C grep -v '^$' | head -n 1 || true)
  if [ -n "$bad_type" ]; then
    printf '%s\n' "$(jq -cn --arg error "$bad_type" '{ok: false, error: $error}')" >&2
    exit 2
  fi
  result=$(jq -c "$(ce_prog)" "$input")
  errors=$(printf '%s' "$result" | jq -c '.errors')
  observations=$(printf '%s' "$result" | jq -c '.observations')
  ok=false
  if [ "$(printf '%s' "$errors" | jq 'length')" = 0 ]; then ok=true; fi
  if [ "$json" = 1 ]; then
    jq -n --argjson ok "$ok" --argjson errors "$errors" --argjson observations "$observations" \
      '{ok: $ok, errors: $errors, observations: $observations}'
  elif [ "$ok" = true ]; then
    printf 'Validated %s rendered observations.\n' "$(printf '%s' "$observations" | jq 'length')"
  else
    printf '%s' "$errors" | jq -r '.[]'
  fi
  [ "$ok" = true ]
}

ce_main "$@"
