#!/usr/bin/env bash
# Validate a browser-evidence handoff document, compute rendered layout measurements,
# and emit only the observations and findings the document proves.
set -euo pipefail

CE_USAGE='Usage: bash collect-rendered-evidence.sh --input <capture.json> [--json] [--measurements]'

ce_prog() {
  cat <<'CE_JQ'
def is_record: type == "object";
def is_positive: (type == "number") and (. > 0);
def rect_shape: is_record and (. as $r | ["x", "y", "width", "height"] | all(.[]; ($r[.] | type) == "number"));
def computed_shape: is_record and (all(.[]; type == "string"));
def hexdigit: (. as $c | "0123456789abcdef" | index($c));
def hexpair: (.[0:1] | hexdigit) * 16 + (.[1:2] | hexdigit);
def hexnibble: (.[0:1] | hexdigit) * 17;
def hex_rgb:
  if type != "string" then null
  else (ascii_downcase) as $h
    | if ($h | test("^#[0-9a-f]{6}$")) then
        [ ($h[1:3] | hexpair), ($h[3:5] | hexpair), ($h[5:7] | hexpair) ]
      elif ($h | test("^#[0-9a-f]{3}$")) then
        [ ($h[1:2] | hexnibble), ($h[2:3] | hexnibble), ($h[3:4] | hexnibble) ]
      else null end
  end;
def lin: ((. / 255) as $c | if $c <= 0.03928 then $c / 12.92 else pow(($c + 0.055) / 1.055; 2.4) end);
def luminance: (.[0] | lin) * 0.2126 + (.[1] | lin) * 0.7152 + (.[2] | lin) * 0.0722;
def ratio_of($a; $b):
  ([($a | luminance), ($b | luminance)] | (max + 0.05) / (min + 0.05));
def round4: ((. * 10000) | round / 10000);
def measured_contrast:
  (if (is_record | not) then false
   elif ((.computed | is_record) | not) then false
   else
     (((.computed.foreground // .computed.color) | hex_rgb) != null)
     and (((.computed.background // .computed.backgroundColor) | hex_rgb) != null)
   end);
def has_measurement:
  measured_contrast
  or ((.measuredFontSize | type) == "number")
  or ((.fontSizePx | type) == "number")
  or ((.contrastPairs | type) == "array")
  or ((.textRect | rect_shape))
  or ((.overflowX | type) == "number")
  or ((.gapAbovePx | type) == "number");
def has_any_evidence:
  ((.rect | rect_shape) or ((.overflowX | type) == "boolean") or ((.overflowX | type) == "number")
   or ((.focusVisible | type) == "boolean") or ((.measuredFontSize | type) == "number")
   or ((.fontSizePx | type) == "number") or ((.gapAbovePx | type) == "number")
   or ((.contrastPairs | type) == "array") or ((.textRect | rect_shape))
   or ((.reducedMotion | type) == "boolean") or (.computed | computed_shape));
def date_ok:
  if type != "string" then false
  elif (test("^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\\.[0-9]+)?)?(Z|[+-][0-9]{2}:[0-9]{2})?)?$") | not) then false
  else (capture("^(?<y>[0-9]{4})-(?<m>[0-9]{2})-(?<d>[0-9]{2})")) as $p
    | (($p.m | tonumber) >= 1 and ($p.m | tonumber) <= 12 and ($p.d | tonumber) >= 1 and ($p.d | tonumber) <= 31)
  end;
def iso_epoch:
  if type != "string" then null
  else
    ([capture("^(?<y>[0-9]{4})-(?<m>[0-9]{2})-(?<d>[0-9]{2})(?:T(?<hh>[0-9]{2}):(?<mi>[0-9]{2})(?::(?<ss>[0-9]{2}))?(?:\\.[0-9]+)?(?<tz>Z|[+-][0-9]{2}:[0-9]{2})?)?$")] | first) as $p
    | if $p == null then null
      else
        (($p.y + "-" + $p.m + "-" + $p.d + "T" + ($p.hh // "00") + ":" + ($p.mi // "00") + ":" + ($p.ss // "00") + "Z")
         | try fromdateiso8601 catch null) as $base
        | if $base == null then null
          else ($p.tz // "Z") as $tz
            | if $tz == "Z" then $base
              else (if ($tz[0:1] == "-") then -1 else 1 end) as $sign
                | (($tz[1:3] | tonumber) * 3600 + ($tz[4:6] | tonumber) * 60) as $off
                | ($base - ($sign * $off))
              end
          end
      end
  end;
def file_extension: gsub("^[\\s]+|[\\s]+$"; "") | ascii_downcase | (capture("(?<e>\\.[a-z0-9]+)$") // {e: ""}) | .e;
def extension_signature:
  if . == ".png" then "png" elif (. == ".jpg" or . == ".jpeg") then "jpeg" else null end;
def hygiene_errors($label):
  if is_record | not then []
  else
    . as $c
    | [ (if ($c | has("frameKind")) then
           (if $c.frameKind == "page" then empty
            elif $c.frameKind == "window" then "\($label).frameKind is window; a capture must be a page frame."
            else "\($label).frameKind must be page or window." end)
         else empty end),
        (if ($c | has("fileSignature")) then
           (if (($c.fileSignature | type) != "string") or ((["png", "jpeg", "jpg"] | index($c.fileSignature)) == null) then
              "\($label).fileSignature must be png or jpeg."
            elif (($c.file | type) != "string") or (($c.file | gsub("^[\\s]+|[\\s]+$"; "")) == "") then
              "\($label).fileSignature requires \($label).file to name the capture file."
            else ($c.file | file_extension) as $ext
              | ($ext | extension_signature) as $want
              | if $want == null then "\($label).file must end in .png, .jpg, or .jpeg."
                elif ($want == "jpeg" and ($c.fileSignature == "jpeg" or $c.fileSignature == "jpg")) or $want == $c.fileSignature then empty
                else "\($label).fileSignature \($c.fileSignature) does not match file extension \($ext)." end
            end)
         else empty end),
        (if ($c | has("dimensions")) then
           (if (($c.dimensions | is_record) and ($c.dimensions.width | is_positive) and ($c.dimensions.height | is_positive)) then
              (if (($c.viewport | is_record) and ($c.viewport.width | is_positive) and ($c.viewport.height | is_positive)) then
                 (if $c.dimensions.width == $c.viewport.width and $c.dimensions.height == $c.viewport.height then empty
                  else "\($label).dimensions \($c.dimensions.width)x\($c.dimensions.height) do not match viewport \($c.viewport.width)x\($c.viewport.height)." end)
               else empty end)
            else "\($label).dimensions requires positive width and height." end)
         else empty end),
        (if ($c | has("sourceMtime")) then
           ($c.sourceMtime
            | if type == "string" then (if date_ok then [.] else null end)
              elif type == "array" and length > 0 and ([.[] | date_ok] | all) then .
              else null end) as $times
           | if $times == null then "\($label).sourceMtime must be an ISO date-time or a non-empty array of them."
             elif ($c.capturedAt | date_ok) | not then empty
             else ($times | map({t: ., e: iso_epoch}) | map(select(.e != null))) as $dated
               | ($c.capturedAt | iso_epoch) as $captured
               | if ($dated | length) == 0 or $captured == null then empty
                 else ($dated | max_by(.e)) as $newest
                   | if $captured < $newest.e then
                       "\($label) is stale: capturedAt \($c.capturedAt) is earlier than sourceMtime \($newest.t)."
                     else empty end
                 end
             end
         else empty end) ]
  end;
def states: ["default", "hover", "focus", "active", "disabled", "loading", "empty", "error"];
def observation_errors($label):
  if is_record | not then ["\($label) must be an object."]
  else
    [ (if ((.locator | type) == "string") and ((.locator | gsub("^[\\s]+|[\\s]+$"; "")) != "")
         then empty else "\($label).locator must be non-empty." end),
      (if has_any_evidence then empty
         else "\($label) needs a rect, textRect, overflowX, focusVisible, reducedMotion, measuredFontSize, gapAbovePx, contrastPairs, or string computed value." end) ]
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
    + (. | hygiene_errors($label))
    + (if (.observations | type) == "array" then
         [ range(0; (.observations | length)) as $j
           | "\($label).observations[\($j)]" as $ol
           | (.observations[$j] | observation_errors($ol)) ] | add // []
       else [] end)
  end;
def contrast_finding($cap; $o; $fg; $bg; $label):
  (($fg | hex_rgb) as $a | ($bg | hex_rgb) as $b
   | if $a == null or $b == null then empty
     else (ratio_of($a; $b)) as $r
       | {type: "contrast",
          locator: ($label // $o.locator),
          viewport: $cap.viewport,
          state: $cap.state,
          foreground: $fg,
          background: $bg,
          threshold: 4.5,
          ratio: ($r | round4),
          failure: ($r < 4.5)}
     end);
def pair_overlap_px($a; $b):
  if (($a | rect_shape) and ($b | rect_shape)) then
    ([([$a.x, $b.x] | max), ([($a.x + $a.width), ($b.x + $b.width)] | min)] | (.[1] - .[0])) as $w
    | ([([$a.y, $b.y] | max), ([($a.y + $a.height), ($b.y + $b.height)] | min)] | (.[1] - .[0])) as $h
    | if $w <= 0 or $h <= 0 then 0 elif $w < $h then $w else $h end
  else 0 end;
def capture_overlap_findings($cap):
  [$cap.observations[]? | select(type == "object") | select((.textRect | rect_shape))
      | {locator: .locator, textRect: .textRect}] as $boxes
  | [range(0; $boxes | length) as $i | range(($i + 1); $boxes | length)
      | [$boxes[$i], $boxes[.]]] | .[]
  | (pair_overlap_px(.[0].textRect; .[1].textRect)) as $px
  | select($px > 4)
  | {type: "overlap", locator: (.[1].locator // .[0].locator), otherLocator: .[0].locator,
     viewport: $cap.viewport, state: $cap.state,
     threshold: 4, overlapPx: ($px | round4), failure: true};
def observation_findings($cap):
  . as $o
  | if ($o | is_record) | not then []
  else
    [ (if ($o | measured_contrast) then
         contrast_finding($cap; $o; ($o.computed.foreground // $o.computed.color); ($o.computed.background // $o.computed.backgroundColor); $o.locator)
       else empty end),
      (if (($o.contrastPairs | type) == "array") then
         $o.contrastPairs[]
         | select(type == "object")
         | contrast_finding($cap; $o; .foreground; .background; (.label // $o.locator))
       else empty end),
      (if (((($o.overflowX | type) == "number") and ($o.overflowX > 2))) then
         {type: "overflow", locator: $o.locator, viewport: $cap.viewport, state: $cap.state,
          threshold: 2, overflowPx: ($o.overflowX | round4),
          width: $cap.viewport.width, failure: true}
       else empty end) ]
  end;
def report_findings:
  if (.captures | type) == "array" then
    {per: ([ .captures[] as $c | select(($c | is_record) and (($c.observations | type) == "array")) |
      $c.observations[] | select(type == "object") | observation_findings($c) ] | flatten),
     over: ([ .captures[] as $c | select(($c | is_record) and (($c.observations | type) == "array")) |
      capture_overlap_findings($c) ] | flatten)}
    | (.per + .over)
  else [] end;
def measurement_summary:
  (if (.captures | type) == "array" then
     [ .captures[] | select(is_record) | (.observations // [])[] | select(is_record) | select(has_measurement) ] | length
   else 0 end) as $n
  | if $n == 0 then
      {status: "not_run",
       reason: "No contrast, size, overlap, or overflow measurement fields were present."}
    else {status: "measured", reason: "", counted: $n} end;
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
         + (if has("textRect") then {textRect: .textRect} else {} end)
         + (if has("role") then {role: .role} else {} end)
         + (if has("fontSizePx") then {fontSizePx: .fontSizePx} else {} end)
         + (if has("measuredFontSize") then {measuredFontSize: .measuredFontSize} else {} end)
         + (if has("gapAbovePx") then {gapAbovePx: .gapAbovePx} else {} end)
         + (if has("overflowX") then {overflowX: .overflowX} else {} end)
         + (if has("focusVisible") then {focusVisible: .focusVisible} else {} end)
         + (if has("reducedMotion") then {reducedMotion: .reducedMotion} else {} end)
         + (if has("contrastPairs") then {contrastPairs: .contrastPairs} else {} end)
         + (if has("computed") then {computed: .computed} else {} end) ]
     else [] end)}
  end;
{validation: validate, findings: report_findings, measurements: measurement_summary}
CE_JQ
}

ce_main() {
  local input='' json=0 measure=0 help=0 abs result ok errors observations findings measurements
  local measurements_status failing
  while [ $# -gt 0 ]; do
    case "$1" in
      --input) shift; input=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --json) json=1; shift ;;
      --measurements|--measure) measure=1; shift ;;
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
  local bad_type
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
  errors=$(printf '%s' "$result" | jq -c '.validation.errors')
  observations=$(printf '%s' "$result" | jq -c '.validation.observations')
  findings=$(printf '%s' "$result" | jq -c '.findings')
  measurements=$(printf '%s' "$result" | jq -c '.measurements')
  measurements_status=$(printf '%s' "$measurements" | jq -r '.status')
  failing=$(printf '%s' "$findings" | jq '[.[] | select(.failure == true)] | length')
  ok=false
  if [ "$(printf '%s' "$errors" | jq 'length')" = 0 ] && [ "$failing" = 0 ]; then ok=true; fi
  if [ "$json" = 1 ]; then
    if [ "$measure" = 1 ] || [ "$measurements_status" = measured ]; then
      jq -n --argjson ok "$ok" --argjson errors "$errors" --argjson observations "$observations" \
        --argjson findings "$findings" --argjson measurements "$measurements" \
        '{ok: $ok, errors: $errors, observations: $observations, findings: $findings, measurements: $measurements}'
    else
      jq -n --argjson ok "$ok" --argjson errors "$errors" --argjson observations "$observations" \
        '{ok: $ok, errors: $errors, observations: $observations}'
    fi
  elif [ "$ok" != true ]; then
    printf '%s' "$errors" | jq -r '.[]'
    printf '%s' "$findings" | jq -r '.[] | select(.failure == true) | "\(.type) at \(.locator): measured \(.ratio // .overlapPx // .overflowPx), threshold \(.threshold)"'
  else
    printf 'Validated %s rendered observations.\n' "$(printf '%s' "$observations" | jq 'length')"
    if [ "$measurements_status" = not_run ]; then
      printf 'Measurements: not_run. %s\n' "$(printf '%s' "$measurements" | jq -r '.reason')"
    else
      printf 'Measurements: %s finding(s), %s failing.\n' \
        "$(printf '%s' "$findings" | jq 'length')" "$failing"
      printf '%s' "$findings" | jq -r '.[] | select(.failure == true) | "\(.type) at \(.locator): measured \(.ratio // .overlapPx // .overflowPx), threshold \(.threshold)"'
    fi
  fi
  [ "$ok" = true ]
}

ce_main "$@"
