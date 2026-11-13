#!/usr/bin/env bash
# inspect-deck.sh — read an existing .pptx and report what is inside it.
#
# Answers the questions you have before editing someone else's deck: how many
# slides, what each slide says, which shapes carry that text and where they sit,
# which parts of a shape leave the canvas, and which fonts the deck asks for.
#
# Needs bash 3.2+, jq, unzip, and the xmllint/awk pair from the base system.
set -uo pipefail

IN_USAGE='Usage: bash inspect-deck.sh --file <deck.pptx> [--outline] [--json]
       [--slide <n>] [--check]

--outline  print slide-by-slide text only (what a reader sees)
--json     print the full report as JSON
--slide N  restrict --outline/--json to slide N (1-based)
--check    exit 1 when a structural problem was found (see report.problems)

Exit codes: 0 report produced; 1 report produced with problems (--check);
2 usage or file error.'

in_die() { # <code> <message>
  jq -cn --arg code "$1" --arg message "$2" '{status: "error", code: $code, message: $message}'
  exit 2
}

# Extract one slide's shapes as JSON. DrawingML from every writer puts each
# element on its own line once formatted, so a line-oriented scanner is enough
# and avoids a full XML library dependency.
in_slide_shapes() { # <slide xml>
  xmllint --format "$1" 2>/dev/null | awk '
    function esc(s) {
      gsub(/&lt;/, "\001", s); gsub(/&gt;/, "\002", s)
      gsub(/&quot;/, "\003", s); gsub(/&apos;/, "\004", s)
      gsub(/&amp;/, "&", s)
      gsub(/\001/, "<", s); gsub(/\002/, ">", s)
      gsub(/\003/, "\"", s); gsub(/\004/, "\047", s)
      gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s)
      gsub(/\t/, "\\t", s); gsub(/\r/, "", s); gsub(/\n/, "\\n", s)
      return s
    }
    BEGIN { inblock = 0; depth = 0; first = 1 }
    /<p:sp>/ { inblock = 1; name = ""; x = ""; y = ""; cx = ""; cy = ""; txt = ""; box = 0; placeholder = ""; next }
    /<p:pic>/ { inblock = 1; name = ""; x = ""; y = ""; cx = ""; cy = ""; txt = ""; box = 2; placeholder = ""; next }
    /<p:graphicFrame>/ { inblock = 1; name = ""; x = ""; y = ""; cx = ""; cy = ""; txt = ""; box = 3; placeholder = ""; next }
    inblock && /<p:cNvPr/ {
      if (match($0, /name="[^"]*"/)) { name = substr($0, RSTART + 6, RLENGTH - 7) }
      next
    }
    inblock && /<p:ph/ {
      if (match($0, /type="[^"]*"/)) { placeholder = substr($0, RSTART + 6, RLENGTH - 7) }
      else placeholder = "body"
      next
    }
    inblock && /<a:off / {
      if (match($0, /x="-?[0-9]+"/)) { x = substr($0, RSTART + 3, RLENGTH - 4) }
      if (match($0, /y="-?[0-9]+"/)) { y = substr($0, RSTART + 3, RLENGTH - 4) }
      next
    }
    inblock && /<a:ext / {
      if (match($0, /cx="[0-9]+"/)) { cx = substr($0, RSTART + 4, RLENGTH - 5) }
      if (match($0, /cy="[0-9]+"/)) { cy = substr($0, RSTART + 4, RLENGTH - 5) }
      next
    }
    inblock && /<a:t>/ {
      line = $0
      gsub(/^[ \t]*<a:t>/, "", line); gsub(/<\/a:t>[ \t]*$/, "", line)
      if (length(txt) > 0) txt = txt "\n" line; else txt = line
      next
    }
    inblock && /<\/p:sp>|<\/p:pic>|<\/p:graphicFrame>/ {
      inblock = 0
      type = (box == 2) ? "picture" : ((box == 3) ? "frame" : (placeholder != "" ? "placeholder" : "text"))
      printf "%s{\"name\":\"%s\",\"type\":\"%s\",\"x\":%s,\"y\":%s,\"cx\":%s,\"cy\":%s,\"text\":\"%s\"}\n", \
        (first ? "" : ",\n"), esc(name), type, \
        (x == "" ? "null" : x), (y == "" ? "null" : y), (cx == "" ? "null" : cx), (cy == "" ? "null" : cy), esc(txt)
      first = 0
      next
    }
  ' | { printf '['; cat; printf ']'; }
}

in_slide_text() { # <slide xml> — paragraphs in reading order, one per line
  xmllint --format "$1" 2>/dev/null | awk '
    /<a:p>/ { p = "" }
    /<a:t>/ {
      line = $0
      gsub(/^[ \t]*<a:t>/, "", line); gsub(/<\/a:t>[ \t]*$/, "", line)
      p = p line
    }
    /<\/a:p>/ { if (p != "") print p }
  '
}

in_notes_text() { # <notes xml> — only the body placeholder, not the slide image
  [ -f "$1" ] || return 0
  xmllint --format "$1" 2>/dev/null | awk '
    /ph type="body"/ { body = 1 }
    /<\/p:sp>/ { body = 0 }
    body && /<a:t>/ {
      line = $0
      gsub(/^[ \t]*<a:t>/, "", line); gsub(/<\/a:t>[ \t]*$/, "", line)
      if (line != "") print line
    }
  '
}

# A graphicFrame table: column count, row count, and the text of every cell.
in_table() { # <slide xml>
  xmllint --format "$1" 2>/dev/null | awk '
    function esc(s) {
      gsub(/&amp;/, "&", s); gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s)
      gsub(/\t/, "\\t", s); gsub(/\n/, "\\n", s)
      return s
    }
    /<a:tbl>/ { intbl = 1; row = -1; cells = 0; out = ""; next }
    /<\/a:tbl>/ { intbl = 0; print "[" out "]"; next }
    intbl && /<a:tr / {
      row++
      cells = 0
      if (row > 0) out = out ","
      out = out "["
      next
    }
    intbl && /<a:tc>/ { cell = ""; next }
    intbl && /<a:t>/ {
      line = $0
      gsub(/^[ \t]*<a:t>/, "", line); gsub(/<\/a:t>[ \t]*$/, "", line)
      cell = cell line
      next
    }
    intbl && /<\/a:tc>/ {
      if (cells > 0) out = out ","
      out = out "\"" esc(cell) "\""
      cells++
      next
    }
    intbl && /<\/a:tr>/ { out = out "]" ; next }
  ' | head -n 1
}

# Chart parts: type, categories, and each series' name and values.
in_chart() { # <chart xml>
  [ -f "$1" ] || return 0
  xmllint --format "$1" 2>/dev/null | awk '
    function esc(s) {
      gsub(/&amp;/, "&", s); gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s)
      gsub(/\t/, "\\t", s); gsub(/\n/, "\\n", s)
      return s
    }
    /<c:(barChart|lineChart|pieChart|doughnutChart|areaChart|scatterChart)>/ {
      tag = $0; sub(/^[ \t]*<c:/, "", tag); sub(/>.*$/, "", tag)
      sub(/Chart$/, "", tag); chartType = tag
    }
    /<c:ser>/ { inSer = 1; sname = ""; vals = ""; nvals = 0; cats = ""; nc = 0; next }
    /<\/c:ser>/ {
      inSer = 0
      if (nser > 0) series = series ","
      series = series "{\"name\":\"" esc(sname) "\",\"values\":[" vals "]}"
      nser++
      next
    }
    inSer && /<c:tx>/ { inTx = 1; next }
    inSer && /<\/c:tx>/ { inTx = 0; next }
    inSer && /<c:cat>/ { inCat = 1; next }
    inSer && /<\/c:cat>/ { inCat = 0; next }
    inSer && /<c:val>/ { inVal = 1; next }
    inSer && /<\/c:val>/ { inVal = 0; next }
    inTx && /<c:v>/ {
      v = $0; gsub(/^[ \t]*<c:v>/, "", v); gsub(/<\/c:v>[ \t]*$/, "", v)
      if (sname == "") sname = v
      next
    }
    inCat && /<c:v>/ {
      v = $0; gsub(/^[ \t]*<c:v>/, "", v); gsub(/<\/c:v>[ \t]*$/, "", v)
      if (nc > 0) cats = cats ","
      cats = cats "\"" esc(v) "\""
      nc++
      next
    }
    inVal && /<c:pt |<c:pt>/ { next }
    inVal && /<c:v>/ {
      v = $0; gsub(/^[ \t]*<c:v>/, "", v); gsub(/<\/c:v>[ \t]*$/, "", v)
      if (v !~ /^-?[0-9.]+$/) next
      if (nvals > 0) vals = vals ","
      vals = vals v
      nvals++
      next
    }
    END {
      if (nser > 0 || chartType != "")
        printf "{\"type\":\"%s\",\"categories\":[%s],\"series\":[%s]}\n", chartType, cats, series
    }
  ' | head -n 1
}

in_main() {
  local file='' mode='report' only='' check=0
  while [ $# -gt 0 ]; do
    case $1 in
      --file) file=${2-}; shift 2 || shift ;;
      --outline) mode='outline'; shift ;;
      --json) mode='json'; shift ;;
      --slide) only=${2-}; shift 2 || shift ;;
      --check) check=1; shift ;;
      -h|--help) printf '%s\n' "$IN_USAGE"; exit 0 ;;
      *) printf 'unknown argument: %s\n%s\n' "$1" "$IN_USAGE" >&2; exit 2 ;;
    esac
  done
  [ -n "$file" ] || { printf '%s\n' "$IN_USAGE" >&2; exit 2; }
  command -v jq >/dev/null 2>&1 || in_die JQ_MISSING 'jq is required'
  command -v unzip >/dev/null 2>&1 || in_die UNZIP_MISSING 'unzip is required'
  [ -f "$file" ] || in_die FILE_MISSING "not a file: $file"
  unzip -l "$file" >/dev/null 2>&1 || in_die NOT_A_PPTX "not a readable zip package: $file"

  local tmp
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/hyper-pptx-inspect.XXXXXX") || in_die TMP_FAILED 'cannot create a temporary directory'
  trap 'rm -rf "$tmp"' EXIT
  unzip -o -q "$file" -d "$tmp" || in_die NOT_A_PPTX "cannot unpack: $file"
  [ -f "$tmp/ppt/presentation.xml" ] || in_die NOT_A_PPTX "package has no ppt/presentation.xml: $file"

  local size cx cy
  cx=$(xmllint --xpath "string(//*[local-name()='sldSz']/@cx)" "$tmp/ppt/presentation.xml" 2>/dev/null)
  cy=$(xmllint --xpath "string(//*[local-name()='sldSz']/@cy)" "$tmp/ppt/presentation.xml" 2>/dev/null)
  case $cx in ''|*[!0-9]*) cx=12192000 ;; esac
  case $cy in ''|*[!0-9]*) cy=6858000 ;; esac

  local fonts
  fonts=$(grep -oh 'typeface="[^"]*"' "$tmp/ppt/theme/"*.xml 2>/dev/null \
    | sed -e 's/typeface="//' -e 's/"$//' | grep -v '^+m' | grep -v '^$' | sort -u | jq -R . | jq -sc . )

  local slides='[]' idx=0 f entry notes shapes problems slide_json
  problems='[]'
  for f in $(ls "$tmp/ppt/slides" 2>/dev/null | grep -E '^slide[0-9]+\.xml$' | sort -t e -k3 -n); do
    idx=$((idx + 1))
    [ -n "$only" ] && [ "$only" != "$idx" ] && continue
    local base=${f%.xml}
    shapes=$(in_slide_shapes "$tmp/ppt/slides/$f" 2>/dev/null || printf '[]')
    notes=$(in_notes_text "$tmp/ppt/notesSlides/notesSlide${base#slide}.xml" | jq -Rs .)
    local table_json='null' chart_json='null' rels chartPart
    table_json=$(in_table "$tmp/ppt/slides/$f" 2>/dev/null || true)
    case $table_json in ''|null) table_json='null' ;; [[:space:]]*) table_json='null' ;; esac
    rels="$tmp/ppt/slides/_rels/$f.rels"
    if [ -f "$rels" ]; then
      chartPart=$(grep -o 'Target="[^"]*chart[^"]*"' "$rels" | head -n 1 \
        | sed -e 's/^Target="//' -e 's/"$//' -e 's#^\.\./#ppt/#')
      if [ -n "$chartPart" ] && [ -f "$tmp/$chartPart" ]; then
        chart_json=$(in_chart "$tmp/$chartPart" 2>/dev/null || true)
        case $chart_json in ''|null) chart_json='null' ;; [[:space:]]*) chart_json='null' ;; esac
      fi
    fi
    entry=$(jq -cn \
      --argjson index "$idx" \
      --argjson shapes "$shapes" \
      --argjson notes "$notes" \
      --argjson table "$table_json" \
      --argjson chart "$chart_json" \
      --argjson cx "$cx" --argjson cy "$cy" \
      '{index: $index, shapes: $shapes, notes: $notes,
        table: $table, chart: $chart,
        outside: [ $shapes[] | select(.x != null and (.x < 0 or .y < 0 or (.x + (.cx // 0)) > $cx or (.y + (.cy // 0)) > $cy))
                   | {name, x, y, cx, cy} ]}')
    slides=$(printf '%s' "$slides" | jq -c --argjson e "$entry" '. + [$e]')
    if printf '%s' "$entry" | jq -e '.outside | length > 0' >/dev/null; then
      problems=$(printf '%s' "$problems" | jq -c --arg m "slide $idx: a shape leaves the slide canvas" '. + [$m]')
    fi
  done

  local report
  report=$(jq -cn --argjson slides "$slides" --argjson fonts "$fonts" \
    --argjson cx "$cx" --argjson cy "$cy" \
    --arg file "$file" \
    '{file: $file, status: "ok", size: {w: $cx, h: $cy},
      slideCount: ($slides | length), fonts: $fonts, slides: $slides,
      problems: []}' | jq -c --argjson p "$problems" '.problems = $p')

  case $mode in
    outline)
      printf '%s' "$report" | jq -r '.slides[] | "── slide \(.index) ──",
        ([.shapes[] | select(.text != "") | .text] | join(" ⏎ ")),
        (if .chart then "[chart] " + .chart.type + " " + ([.chart.series[] | .name + ": " + (.values | map(tostring) | join("/"))] | join(", ")) else empty end),
        (if .notes != "" then "[notes] " + (.notes | gsub("\n"; " ")) else empty end)'
      ;;
    json) printf '%s\n' "$report" ;;
    report)
      printf '%s' "$report" | jq -r '
        "\(.file)\n\(.slideCount) slides · \(.size.w | . / 914400 * 10 | round / 10) × \(.size.h | . / 914400 * 10 | round / 10) in"
        + (if (.fonts | length) > 0 then "\nfonts: " + (.fonts | join(", ")) else "" end)'
      printf '%s' "$report" | jq -r '.slides[] |
        "── slide \(.index)  (\(.shapes | length) shapes)\(if (.outside | length) > 0 then "  ⚠ " + ((.outside|length)|tostring) + " outside" else "" end)",
        ([.shapes[] | select(.text != "") | "   · " + (.text | gsub("\n"; " ⏎ ") | .[0:110])] | join("\n")),
        (if .table then "   [table] " + ((.table | length) | tostring) + " rows × " + (((.table[0] | length) // 0) | tostring) + " cols" else empty end),
        (if .chart then "   [chart] " + (.chart.type | sub("Chart$"; "")) + " · " + ((.chart.series | length) | tostring) + " series · " + ((.chart.categories | length) | tostring) + " categories" else empty end),
        (if .notes != "" then "   [notes] " + (.notes | gsub("\n"; " ") | .[0:110]) else empty end)'
      ;;
  esac

  if [ "$check" -eq 1 ]; then
    printf '%s' "$report" | jq -e '(.problems | length) == 0' >/dev/null || exit 1
  fi
  exit 0
}

in_main "$@"
