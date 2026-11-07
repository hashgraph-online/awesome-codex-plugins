#!/usr/bin/env bash
# Render diagram.data.json into a card-and-connector SVG planning map.
# Requires bash 3.2+ and jq 1.6+.
set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo 'Usage: bash render-planning-map.sh <diagram.data.json> <diagram.svg>' >&2
  exit 1
fi

input_path=$1
output_path=$2

raw=''
if [ -e "$input_path" ]; then
  IFS= read -r -d '' raw <"$input_path" || true
else
  echo "render-planning-map: cannot read $input_path" >&2
  exit 1
fi

data=''
if [ -n "$raw" ]; then
  data=$(printf '%s' "$raw" | jq -cs 'if length == 1 then .[0] else error("expected a single JSON value") end' 2>/dev/null) || data=''
fi
if [ -z "$data" ]; then
  echo "render-planning-map: invalid JSON in $input_path" >&2
  exit 1
fi

svg=$(jq -rnj --argjson data "$data" --arg input "$input_path" '
  def truthy: . as $v | ($v != null and $v != false and $v != "" and $v != 0);
  def jsstr:
    if type == "object" then "[object Object]"
    elif . == null then "null"
    elif type == "boolean" then (if . then "true" else "false" end)
    elif type == "number" then tostring
    elif type == "array" then (map(jsstr) | join(","))
    else . end;
  def wtext: if . == null or . == false or . == "" or . == 0 then "" else jsstr end;
  def esc: jsstr | gsub("&"; "&amp;") | gsub("<"; "&lt;") | gsub(">"; "&gt;") | gsub("\""; "&quot;");
  def wrap($max):
    (wtext | [splits("\\s+")] | map(select(length > 0))) as $words
    | reduce $words[] as $w ({lines: [], line: ""};
        (if .line == "" then $w else .line + " " + $w end) as $cand
        | if (.line != "" and ($cand | length) > $max)
          then {lines: (.lines + [.line]), line: $w}
          else {lines: .lines, line: $cand} end)
    | ((.lines + (if .line != "" then [.line] else [] end))[0:2]);
  def textlines($lines; $x; $y; $size; $weight; $fill):
    [ $lines | to_entries[] | . as $e
      | "<text x=\"\($x)\" y=\"\($y + $e.key * ($size + 5))\" font-size=\"\($size)\" font-weight=\"\($weight)\" fill=\"\($fill)\">\($e.value | esc)</text>" ]
    | join("\n");
  def card($x; $y; $w; $h; $title; $subtitle; $accent):
    ($title | wrap(26)) as $tl
    | ($subtitle | wrap(42)) as $sl
    | "\n  <g filter=\"url(#shadow)\">\n"
      + "    <rect x=\"\($x)\" y=\"\($y)\" width=\"\($w)\" height=\"\($h)\" rx=\"10\" fill=\"#fff\" stroke=\"#ececf1\"/>\n"
      + "    <rect x=\"\($x + 18)\" y=\"\($y + 18)\" width=\"8\" height=\"8\" rx=\"2\" fill=\"\($accent)\"/>\n"
      + "    \(textlines($tl; $x + 34; $y + 27; 16; 700; "#24242b"))\n"
      + "    \(textlines($sl; $x + 22; $y + 56; 11; 400; "#737380"))\n"
      + "  </g>";
  def connector($x1; $y1; $x2; $y2):
    ([80, ($x2 - $x1) * 0.45] | max) as $d
    | "<path d=\"M \($x1) \($y1) C \($x1 + $d) \($y1), \($x2 - $d) \($y2), \($x2) \($y2)\" fill=\"none\" stroke=\"#cfd0d7\" stroke-width=\"2\"/>";
  def basename: split("/") | map(select(length > 0)) | if length == 0 then "" else .[length - 1] end;

  $data as $d
  | (if ($d | type) == "object" and ($d | has("branches")) and (($d.branches) | type) == "array"
     then $d.branches else [] end) as $branches
  | ($branches | length) as $n
  | ([760, (160 + $n * 180)] | max) as $height
  | (($height - ($n - 1) * 180) / 2) as $top
  | (($d | if type == "object" and has("title") then .title else null end)
     | if truthy then . else ($input | basename) end) as $title
  | (($d | if type == "object" and has("subtitle") then .subtitle else null end)
     | if truthy then . else "Planning package map" end) as $subtitle
  | ["#ff5b6e", "#f59e0b", "#8b5cf6", "#06b6d4", "#22c55e", "#64748b"] as $palette
  | "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    + "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1400\" height=\"\($height)\" viewBox=\"0 0 1400 \($height)\">\n"
    + "  <defs>\n"
    + "    <pattern id=\"dots\" width=\"18\" height=\"18\" patternUnits=\"userSpaceOnUse\">\n"
    + "      <circle cx=\"1\" cy=\"1\" r=\"1\" fill=\"#e7e7ec\"/>\n"
    + "    </pattern>\n"
    + "    <filter id=\"shadow\" x=\"-20%\" y=\"-20%\" width=\"140%\" height=\"150%\">\n"
    + "      <feDropShadow dx=\"0\" dy=\"8\" stdDeviation=\"10\" flood-color=\"#111827\" flood-opacity=\"0.10\"/>\n"
    + "    </filter>\n"
    + "  </defs>\n"
    + "  <rect width=\"100%\" height=\"100%\" fill=\"#fafafa\"/>\n"
    + "  <rect width=\"100%\" height=\"100%\" fill=\"url(#dots)\" opacity=\"0.75\"/>\n"
    + "  <text x=\"40\" y=\"52\" font-size=\"18\" font-weight=\"700\" fill=\"#2a2a31\">\($subtitle | esc)</text>\n"
    + ([range(0; $n) | . as $i
        | "  " + connector(380; ($height / 2 + 38); 560; ($top + $i * 180 + 43)) + "\n"] | join(""))
    + card(130; ($height / 2); 250; 76; $title; "Central product idea"; "#ff5b6e")
    + ([range(0; $n) | . as $i
        | $branches[$i] as $b
        | ($top + $i * 180) as $y
        | $palette[$i % 6] as $accent
        | (($b | if type == "object" and has("label") then .label else null end)) as $label
        | (($b | if type == "object" and has("summary") then .summary else null end)) as $summary
        | ((if ($b | type) == "object" and ($b | has("children")) and (($b.children) | type) == "array"
            then $b.children else [] end)[0:4]) as $kids
        | ($kids | length) as $kn
        | ($y + 43 - (($kn - 1) * 68) / 2 - 27) as $child_top
        | card(560; $y; 285; 86; $label; $summary; $accent)
          + ([range(0; $kn) | . as $j
              | ($child_top + $j * 68) as $cy
              | "  " + connector(845; ($y + 43); 980; ($cy + 27)) + "\n"
                + card(980; $cy; 235; 54; $kids[$j]; ""; $accent)] | join(""))
      ] | join(""))
    + "</svg>\n"'; printf x)
svg=${svg%x}

if ! { printf '%s' "$svg" >"$output_path"; } 2>/dev/null; then
  echo "render-planning-map: cannot write $output_path" >&2
  exit 1
fi
printf 'Rendered %s\n' "$output_path"
