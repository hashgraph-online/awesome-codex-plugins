#!/usr/bin/env bash
# Render a hyper-diagram JSON spec into a static interactive HTML, a JPG, and an
# optional one-page vector PDF with one headless Chromium-family browser, and
# print the layout checks as one JSON report.
set -euo pipefail

RD_USAGE='Usage: bash render-diagram.sh --spec <name.diagram.json> --out-dir <dir>
       [--name <slug>] [--formats html,jpg[,pdf]] [--scale <1-4>] [--theme light|dark]
       [--browser <path>] [--budget-ms <ms>]
       bash render-diagram.sh --list-browsers

Exit codes: 0 rendered and every check passed; 1 rendered but a check failed
(files are written for inspection, not for delivery); 2 usage or spec error;
3 blocked (no browser, no layout engine, or no runtime result).'

RD_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
RD_RUNTIME="$RD_DIR/assets/runtime"
RD_ELK_VERSION=0.12.1
RD_ELK_SHA256=b1032b7cfd2a57c54c6f0e8369d7665e19a579954f7cd20a6dae28f1912ea0d7
RD_ELK_URL="https://cdn.jsdelivr.net/npm/elkjs@$RD_ELK_VERSION/lib/elk.bundled.js"
RD_TMP=''
rd_cleanup() { if [ -n "$RD_TMP" ] && [ -d "$RD_TMP" ]; then rm -rf "$RD_TMP"; fi; }
trap rd_cleanup EXIT

rd_die() { # <exit-code> <code> <message>
  jq -cn --arg code "$2" --arg message "$3" '{status: "error", code: $code, message: $message}'
  exit "$1"
}

rd_candidates() {
  local name dir
  if [ -n "${HYPER_DIAGRAM_BROWSER:-}" ]; then printf '%s\n' "$HYPER_DIAGRAM_BROWSER"; fi
  for name in chrome-headless-shell chromium chromium-browser; do command -v "$name" 2>/dev/null || true; done
  for dir in "$HOME/Library/Caches/ms-playwright" "$HOME/.cache/ms-playwright"; do
    [ -d "$dir" ] || continue
    find "$dir" -maxdepth 4 -type f -name 'chrome-headless-shell' -perm -u+x 2>/dev/null | sort -r
    find "$dir" -maxdepth 6 -type f \( -name 'Chromium' -o -name 'chrome' \) -perm -u+x -path '*chromium-*' 2>/dev/null | sort -r
  done
  printf '%s\n' "/Applications/Chromium.app/Contents/MacOS/Chromium"
  for name in google-chrome-stable google-chrome microsoft-edge brave-browser; do command -v "$name" 2>/dev/null || true; done
  printf '%s\n' "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
}
rd_find_browser() {
  local c
  while IFS= read -r c; do
    if [ -n "$c" ] && [ -f "$c" ] && [ -x "$c" ]; then printf '%s\n' "$c"; return 0; fi
  done <<EOF
$(rd_candidates)
EOF
  return 1
}

rd_sha256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }

# Prints the path of a verified ELK bundle, downloading it once into the cache.
rd_elk() {
  local cache="${XDG_CACHE_HOME:-$HOME/.cache}/hyper-diagram" file part
  file="$cache/elk-$RD_ELK_VERSION.js"
  if [ -n "${HYPER_DIAGRAM_ELK:-}" ]; then file=$HYPER_DIAGRAM_ELK; fi
  if [ -f "$file" ] && [ "$(rd_sha256 "$file")" = "$RD_ELK_SHA256" ]; then printf '%s\n' "$file"; return 0; fi
  [ -z "${HYPER_DIAGRAM_ELK:-}" ] || return 1
  command -v curl >/dev/null 2>&1 || return 1
  mkdir -p -- "$cache"
  part="$file.part.$$"
  if curl -fsSL --max-time 60 "$RD_ELK_URL" -o "$part" && [ "$(rd_sha256 "$part")" = "$RD_ELK_SHA256" ]; then
    mv -f -- "$part" "$file"; printf '%s\n' "$file"; return 0
  fi
  rm -f -- "$part"
  return 1
}

rd_abs() { local d b; d=$(dirname -- "$1"); b=$(basename -- "$1"); (CDPATH='' cd -- "$d" && printf '%s/%s\n' "$(pwd)" "$b"); }
rd_url() { printf 'file://%s' "$1" | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/#/%23/g' -e 's/?/%3F/g'; }
rd_unescape() { sed -e 's/&quot;/"/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' -e "s/&#39;/'/g" -e 's/&amp;/\&/g'; }
rd_magic() { local got; got=$(od -An -tx1 -N4 -- "$1" 2>/dev/null | tr -d ' \n'); case "$got" in "$2"*) return 0 ;; *) return 1 ;; esac; }
rd_browser() {
  local b=$1; shift
  "$b" --headless --disable-gpu --no-first-run --no-default-browser-check --hide-scrollbars \
    --allow-file-access-from-files --user-data-dir="$RD_TMP/profile" "$@" 2>>"$RD_TMP/browser.log"
}

rd_page() { # <spec-json-file> <elk-path|''> -> page on stdout
  local spec=$1 elk=$2 f
  printf '<!doctype html>\n<html lang="ko" data-theme="light">\n<head>\n<meta charset="utf-8">\n'
  printf '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>diagram</title>\n<style id="hd-theme">\n'
  cat "$RD_RUNTIME/theme.css"
  printf '</style>\n</head>\n<body>\n'
  cat <<'HTML'
<figure id="hd-canvas" role="group" aria-labelledby="hd-title" aria-describedby="hd-desc">
  <header class="hd-head"><span class="hd-dot" aria-hidden="true"></span><h1 id="hd-title"></h1><span class="hd-badge" id="hd-badge"></span></header>
  <p id="hd-subtitle"></p>
  <div class="hd-board">
    <svg id="hd-svg" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="hd-title" aria-describedby="hd-desc"></svg>
    <ul class="hd-legend" id="hd-legend"></ul>
  </div>
  <figcaption id="hd-desc"></figcaption>
</figure>
HTML
  printf '<script type="application/json" id="hd-spec">'
  jq -c . "$spec" | sed -e 's#</#<\\/#g' -e 's#<!--#<\\!--#g'
  printf '</script>\n<script data-hd-viewer>\n'
  cat "$RD_RUNTIME/viewer.js"
  printf '</script>\n'
  if [ -n "$elk" ]; then printf '<script data-hd-runtime src="%s"></script>\n' "$(rd_url "$elk")"; fi
  for f in draw.js graph.js sequence.js tree.js timeline.js run.js; do
    printf '<script data-hd-runtime src="%s"></script>\n' "$(rd_url "$RD_RUNTIME/$f")"
  done
  printf '<script data-hd-runtime>HD.run();</script>\n</body>\n</html>\n'
}

rd_main() {
  local spec='' out_dir='' name='' formats='html,jpg' scale=2 browser='' budget=30000 theme=''
  command -v jq >/dev/null 2>&1 || { printf 'render-diagram.sh needs jq\n' >&2; exit 2; }
  while [ $# -gt 0 ]; do
    case "$1" in
      --spec|--input) spec=${2-}; shift 2 || shift ;;
      --out-dir) out_dir=${2-}; shift 2 || shift ;;
      --name) name=${2-}; shift 2 || shift ;;
      --formats) formats=${2-}; shift 2 || shift ;;
      --scale) scale=${2-}; shift 2 || shift ;;
      --theme) theme=${2-}; shift 2 || shift ;;
      --browser) browser=${2-}; shift 2 || shift ;;
      --budget-ms) budget=${2-}; shift 2 || shift ;;
      --list-browsers)
        rd_candidates | while IFS= read -r c; do if [ -n "$c" ] && [ -f "$c" ] && [ -x "$c" ]; then printf '%s\n' "$c"; fi; done
        exit 0 ;;
      -h|--help) printf '%s\n' "$RD_USAGE"; exit 0 ;;
      *) printf 'unknown argument: %s\n%s\n' "$1" "$RD_USAGE" >&2; exit 2 ;;
    esac
  done
  [ -n "$spec" ] && [ -n "$out_dir" ] || { printf '%s\n' "$RD_USAGE" >&2; exit 2; }
  [ -f "$spec" ] || rd_die 2 SPEC_MISSING "spec file not found: $spec"
  jq -e 'type == "object" and (.type | type) == "string"' "$spec" >/dev/null 2>&1 \
    || rd_die 2 SPEC_INVALID "spec must be a JSON object with a string \"type\""
  case "$scale" in 1|2|3|4) ;; *) rd_die 2 BAD_SCALE "--scale must be 1, 2, 3, or 4" ;; esac
  case "$budget" in ''|*[!0-9]*) rd_die 2 BAD_BUDGET "--budget-ms must be a positive integer" ;; esac
  case "$theme" in ''|light|dark) ;; *) rd_die 2 BAD_THEME "--theme must be light or dark" ;; esac
  local want_html=0 want_jpg=0 want_pdf=0 f
  for f in $(printf '%s' "$formats" | tr ',' ' '); do
    case "$f" in html) want_html=1 ;; jpg|jpeg) want_jpg=1 ;; pdf) want_pdf=1 ;;
      *) rd_die 2 BAD_FORMAT "unknown format '$f'; use html, jpg, pdf" ;; esac
  done
  [ $((want_html + want_jpg + want_pdf)) -gt 0 ] || rd_die 2 BAD_FORMAT "--formats is empty"
  if [ -z "$name" ]; then name=$(basename -- "$spec"); name=${name%.json}; name=${name%.diagram}; fi
  case "$name" in ''|*/*|.*) rd_die 2 BAD_NAME "--name must be a plain file stem" ;; esac

  if [ -z "$browser" ]; then
    browser=$(rd_find_browser) || rd_die 3 BROWSER_MISSING "no Chromium-family browser found; install one (for example 'npx playwright install chromium-headless-shell') or pass --browser <path> / HYPER_DIAGRAM_BROWSER"
  fi
  [ -f "$browser" ] && [ -x "$browser" ] || rd_die 3 BROWSER_MISSING "browser is not an executable file: $browser"

  local type elk=''
  type=$(jq -r .type "$spec")
  case "$type" in
    architecture|dataflow|flowchart|state|class|erd)
      elk=$(rd_elk) || rd_die 3 ELK_UNAVAILABLE "cannot obtain elkjs $RD_ELK_VERSION with sha256 $RD_ELK_SHA256 from $RD_ELK_URL; download it once with network access or set HYPER_DIAGRAM_ELK to a verified copy" ;;
  esac

  mkdir -p -- "$out_dir"
  RD_TMP=$(mktemp -d "${TMPDIR:-/tmp}/hyper-diagram.XXXXXX")
  local out_abs page result spec_in="$RD_TMP/spec.json"
  out_abs=$(rd_abs "$out_dir")
  if [ -n "$theme" ]; then jq --arg t "$theme" '.theme = $t' "$spec" > "$spec_in"; else cp -- "$spec" "$spec_in"; fi
  page="$RD_TMP/page.html"
  rd_page "$spec_in" "$elk" > "$page"

  # 1. bake: run the runtime and serialize the rendered DOM
  if ! rd_browser "$browser" --virtual-time-budget="$budget" --dump-dom "$(rd_url "$page")" > "$RD_TMP/static.html"; then
    rd_die 3 BAKE_FAILED "browser exited with an error while rendering: $(tail -n 3 "$RD_TMP/browser.log" 2>/dev/null | tr '\n' ' ')"
  fi
  result=$(grep -o 'data-hd-result="[^"]*"' "$RD_TMP/static.html" | head -n 1 | sed -e 's/^data-hd-result="//' -e 's/"$//' | rd_unescape || true)
  if [ -z "$result" ] || ! printf '%s' "$result" | jq -e . >/dev/null 2>&1; then
    rd_die 3 RUNTIME_NO_RESULT "the runtime left no result; raise --budget-ms or check the browser log"
  fi
  if grep '<script' "$RD_TMP/static.html" | grep -qv 'data-hd-viewer'; then
    result=$(printf '%s' "$result" | jq -c '.errors += [{code: "SCRIPT_LEFT", message: "the baked HTML still contains a runtime <script>"}]')
  fi
  local W H html_out='' jpg_out='' pdf_out='' pages='null' extra='[]' url
  W=$(printf '%s' "$result" | jq -r '.canvas.width // 0')
  H=$(printf '%s' "$result" | jq -r '.canvas.height // 0')
  [ "$W" -gt 0 ] && [ "$H" -gt 0 ] || rd_die 3 CANVAS_EMPTY "#hd-canvas has no size after rendering"
  url="$(rd_url "$RD_TMP/static.html")?capture=1"

  if [ "$want_html" -eq 1 ]; then html_out="$out_abs/$name.html"; cp -- "$RD_TMP/static.html" "$html_out"; fi
  if [ "$want_jpg" -eq 1 ]; then
    jpg_out="$out_abs/$name.jpg"; rm -f -- "$jpg_out"
    rd_browser "$browser" --window-size="$W,$H" --force-device-scale-factor="$scale" --screenshot="$jpg_out" "$url" >/dev/null || true
    if [ ! -s "$jpg_out" ] || ! rd_magic "$jpg_out" ffd8ff; then
      extra=$(printf '%s' "$extra" | jq -c '. + [{code: "JPG_FAILED", message: "the browser wrote no JPEG"}]'); jpg_out=''
    fi
  fi
  if [ "$want_pdf" -eq 1 ]; then
    pdf_out="$out_abs/$name.pdf"; rm -f -- "$pdf_out"
    rd_browser "$browser" --no-pdf-header-footer --print-to-pdf="$pdf_out" "$url" >/dev/null || true
    if [ ! -s "$pdf_out" ] || ! rd_magic "$pdf_out" 25504446; then
      extra=$(printf '%s' "$extra" | jq -c '. + [{code: "PDF_FAILED", message: "the browser wrote no PDF"}]'); pdf_out=''
    else
      pages=$( (LC_ALL=C grep -a -o '/Count [0-9][0-9]*' "$pdf_out" || true) | awk '{ if ($2 > m) m = $2 } END { print m + 0 }')
      if [ "$pages" -ne 1 ]; then
        extra=$(printf '%s' "$extra" | jq -c --arg p "$pages" '. + [{code: "PDF_MULTIPAGE", message: ("the PDF has " + $p + " pages")}]')
      fi
    fi
  fi

  printf '%s' "$result" | jq -c --arg browser "$browser" --arg html "$html_out" --arg jpg "$jpg_out" --arg pdf "$pdf_out" \
    --argjson pages "$pages" --argjson extra "$extra" --argjson scale "$scale" '
    .errors += $extra
    | {status: (if (.errors | length) == 0 then "pass" else "fail" end), type, canvas, scale: $scale, counts,
       outputs: {html: (if $html == "" then null else $html end), jpg: (if $jpg == "" then null else $jpg end), pdf: (if $pdf == "" then null else $pdf end)},
       pdfPages: $pages, errors, warnings, browser: $browser}' > "$RD_TMP/report.json"
  cat "$RD_TMP/report.json"
  if jq -e '.status == "pass"' "$RD_TMP/report.json" >/dev/null; then exit 0; fi
  exit 1
}

rd_main "$@"
