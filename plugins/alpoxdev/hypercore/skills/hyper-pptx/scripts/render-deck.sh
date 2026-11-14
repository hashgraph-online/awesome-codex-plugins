#!/usr/bin/env bash
# render-deck.sh — build a .pptx from a JSON deck spec and render it to images.
#
# Pipeline: spec.json -> layout.jq (geometry) -> pptx-package.jq (OOXML)
#           -> workbook.jq (chart data) -> .pptx (zip) -> preview.html
#           -> per-slide PNG (headless Chromium)
#
# Everything is deterministic: same spec, same bytes, no timestamps in the
# archive and no clock-dependent output. The script needs bash 3.2+, jq,
# zip/unzip, and one Chromium-family browser binary for the preview and the
# slide images.
set -uo pipefail

PP_USAGE='Usage: bash render-deck.sh --spec <deck.json> --out-dir <dir>
       [--name <slug>] [--formats pptx,html,png[,pdf]] [--scale <1-3>]
       [--browser <path>] [--budget-ms <ms>] [--no-check]
       bash render-deck.sh --list-browsers

Exit codes: 0 built and every check passed; 1 built but a layout check failed
(artifacts are written for inspection, not for delivery); 2 usage or spec
error; 3 blocked (no browser, no jq, or no runtime result).'

PP_HERE=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)
PP_RUNTIME=$PP_HERE/../assets/runtime
PP_PREVIEW=$PP_HERE/../assets/preview
PP_LAYOUT=$PP_RUNTIME/layout.jq
PP_PACKAGE=$PP_RUNTIME/pptx-package.jq
PP_WORKBOOK=$PP_RUNTIME/workbook.jq

pp_die() { # <code> <name> <message>
  jq -cn --arg code "$2" --arg message "$3" '{status: "error", code: $code, message: $message}'
  exit "$1"
}

pp_fail() { # <name> <message> — a check failure after artifacts were written
  PP_CHECKS=$(printf '%s' "$PP_CHECKS" | jq -c --arg code "$1" --arg message "$2" '. + [{code: $code, message: $message}]')
}

pp_candidates() {
  printf '%s\n' \
    "${HYPER_PPTX_BROWSER:-}" \
    "$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell" \
    "$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-x64/chrome-headless-shell" \
    "$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1207/chrome-headless-shell-mac-arm64/chrome-headless-shell" \
    "$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1206/chrome-headless-shell-mac-arm64/chrome-headless-shell" \
    "$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1205/chrome-headless-shell-mac-arm64/chrome-headless-shell" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"
}

pp_find_browser() {
  local c
  pp_candidates | while IFS= read -r c; do
    if [ -n "$c" ] && [ -f "$c" ] && [ -x "$c" ]; then printf '%s\n' "$c"; break; fi
  done
}

pp_abs() { # <path> — absolute without resolving symlinks
  case $1 in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$(pwd)" "$1" ;;
  esac
}

pp_url() { # <absolute path> — file URL with percent-encoding for space and friends
  local p=$1 out='' ch i=0
  while [ "$i" -lt "${#p}" ]; do
    ch=${p:$i:1}
    case $ch in
      [A-Za-z0-9/._~-]) out=$out$ch ;;
      ' ') out=$out%20 ;;
      *) out=$out$(printf '%%%02X' "'$ch") ;;
    esac
    i=$((i + 1))
  done
  printf 'file://%s\n' "$out"
}

pp_browser() { # <browser> <args...> — headless invocation, output on stdout
  local bin=$1
  shift
  "$bin" --headless --disable-gpu --no-sandbox --hide-scrollbars --disable-extensions \
    --disable-background-networking --disable-sync --no-first-run \
    --user-data-dir="$PP_TMP/profile" "$@" 2>"$PP_TMP/browser.log"
}

# Pixel size of a local picture, so the layout can keep its aspect ratio without
# the spec having to repeat what the file already says. PNG carries a fixed IHDR
# header; JPEG needs a scan for a start-of-frame marker. Anything else is
# reported as unknown and the caller falls back to the spec's own aspect.
pp_image_size() { # <file> — prints "<w> <h>" or nothing
  local f=$1 b hdr w h
  case $(printf '%s' "${f##*.}" | tr 'A-Z' 'a-z') in
    png)
      hdr=$(od -An -tu1 -j16 -N8 "$f" 2>/dev/null | tr -s ' ')
      set -- $hdr
      if [ $# -ge 8 ]; then
        w=$(( ($1 * 16777216) + ($2 * 65536) + ($3 * 256) + $4 ))
        h=$(( ($5 * 16777216) + ($6 * 65536) + ($7 * 256) + $8 ))
        printf '%s %s\n' "$w" "$h"
      fi
      ;;
    jpg|jpeg)
      # Walk the marker chain: each segment is FFxx followed by a 2-byte length.
      local off=2 marker seglen
      while [ "$off" -lt 2000000 ]; do
        marker=$(od -An -tx1 -j"$off" -N2 "$f" 2>/dev/null | tr -d ' \n')
        [ "$marker" = "ffd8" ] && { off=$((off + 2)); continue; }
        case $marker in
          ff*) : ;;
          *) break ;;
        esac
        case $marker in
          ffc0|ffc1|ffc2|ffc3|ffc5|ffc6|ffc7|ffc9|ffca|ffcb|ffcd|ffce|ffcf)
            # od may break one byte per line, so the pair is joined before awk.
            h=$(od -An -tu1 -j$((off + 5)) -N2 "$f" 2>/dev/null | tr -s ' \n' ' ' \
              | awk '{print $1 * 256 + $2}')
            w=$(od -An -tu1 -j$((off + 7)) -N2 "$f" 2>/dev/null | tr -s ' \n' ' ' \
              | awk '{print $1 * 256 + $2}')
            if [ -n "$w" ] && [ -n "$h" ] && [ "$w" -gt 0 ] && [ "$h" -gt 0 ]; then
              printf '%s %s\n' "$w" "$h"
            fi
            return 0
            ;;
          ffd9|ffda) break ;;
        esac
        seglen=$(od -An -tu1 -j$((off + 2)) -N2 "$f" 2>/dev/null | tr -s ' \n' ' ' \
          | awk '{print $1 * 256 + $2}')
        case $seglen in ''|*[!0-9]*) break ;; esac
        [ "$seglen" -lt 2 ] && break
        off=$((off + 2 + seglen))
      done
      ;;
  esac
}

# Every relationship target must resolve to a part in the package.
pp_check_relationships() { # <stage dir>
  local stage=$1 rel base tgt tpath
  cd "$stage" || return 0
  find . -name '*.rels' | while IFS= read -r rel; do
    base=$(dirname -- "$(dirname -- "$rel")")
    grep -o 'Target="[^"]*"' "$rel" | sed -e 's/^Target="//' -e 's/"$//' | while IFS= read -r tgt; do
      case $tgt in http*) continue ;; esac
      tpath=$base/$tgt
      if [ ! -f "$tpath" ]; then
        printf '%s -> %s\n' "$rel" "$tgt"
      fi
    done
  done
}

# A slide's motion is the one place where a wrong id does not fail loudly: the
# file still opens, PowerPoint just offers to repair it. Three things are checked
# per slide: one timing tree, unique time-node ids, and animation targets that
# name a shape which actually exists on that slide.
pp_check_motion() { # <stage dir>
  local stage=$1 f
  for f in "$stage"/ppt/slides/slide*.xml; do
    [ -f "$f" ] || continue
    local n=${f##*/slide}; n=${n%.xml}
    local trees
    trees=$(grep -o '<p:timing' "$f" | wc -l | tr -d ' ')
    if [ "$trees" -gt 1 ]; then
      printf 'slide %s: %s timing trees, PowerPoint keeps only one\n' "$n" "$trees"
      continue
    fi
    [ "$trees" -eq 1 ] || continue
    local dup
    dup=$(grep -o '<p:cTn id="[0-9]*"' "$f" | sed -e 's/.*id="//' -e 's/"$//' | sort | uniq -d | head -n 1)
    [ -z "$dup" ] || printf 'slide %s: time node id %s repeats\n' "$n" "$dup"
    local ids spid
    ids=$(grep -o '<p:cNvPr id="[0-9]*"' "$f" | sed -e 's/.*id="//' -e 's/"$//' | sort -u)
    for spid in $(grep -o '<p:spTgt spid="[0-9]*"' "$f" | sed -e 's/.*spid="//' -e 's/"$//' | sort -u); do
      printf '%s\n' "$ids" | grep -qx -- "$spid" \
        || printf 'slide %s: animation targets shape %s, which is not on the slide\n' "$n" "$spid"
    done
  done
}

# The preview needs the picture's pixel size and a URL it can load, and the
# package needs the file itself. One pass over the spec fills in both: every
# image entry gets an absolute path and a measured aspect ratio.
pp_image_slots() { # <spec> — one JSON object per image entry, in a stable order
  jq -c '
    [ .slides | to_entries[] | .key as $si | .value
      | ([ (select(.image != null and .image.path != null) | {slide: $si, key: "image", idx: 0}) ]
         + ((.images // []) | to_entries | map({slide: $si, key: "images", idx: .key})))
    ] | add // []' "$1"
}

pp_prepare_images() { # <spec> <out path>
  local spec=$1 out=$2 total i path size w h aspect slot
  jq '.' "$spec" > "$out"
  total=$(pp_image_slots "$out" | jq 'length')
  [ "$total" -gt 0 ] || return 0
  i=0
  while [ "$i" -lt "$total" ]; do
    slot=$(pp_image_slots "$out" | jq -c --argjson i "$i" '.[$i]')
    path=$(jq -r --argjson s "$slot" '
      if $s.key == "image" then .slides[$s.slide].image.path
      else .slides[$s.slide].images[$s.idx].path end' "$out")
    case $path in
      ''|null) pp_die 2 IMAGE_MISSING \
        "an image entry on slide $(jq -r --argjson s "$slot" '($s.slide + 1)' "$out") has no path" ;;
      http://*|https://*) pp_die 2 IMAGE_REMOTE "image paths must be local files: $path" ;;
    esac
    # Alternative text is the only description of a picture for a reader who
    # cannot see it, so a delivery without it is a defect, not a style choice.
    alt=$(jq -r --argjson s "$slot" '
      if $s.key == "image" then (.slides[$s.slide].image.alt // "")
      else ((.slides[$s.slide].images[$s.idx].alt) // "") end' "$out")
    [ -n "$alt" ] || pp_fail IMAGE_NO_ALT \
      "an image on slide $(jq -r --argjson s "$slot" '($s.slide + 1)' "$out") has no alt text: $path"
    # A relative path is read against the spec's own folder, so a deck and its
    # pictures can move together and a spec written in a subfolder still works.
    case $path in
      /*) : ;;
      *) path="$(cd "$(dirname -- "$spec")" && pwd)/$path" ;;
    esac
    [ -f "$path" ] || pp_die 2 IMAGE_MISSING "image file not found: $path"
    case $(printf '%s' "${path##*.}" | tr 'A-Z' 'a-z') in
      png|jpg|jpeg|gif) : ;;
      *) pp_die 2 IMAGE_TYPE "use a png, jpg, or gif image: $path" ;;
    esac
    size=$(pp_image_size "$path")
    if [ -z "$size" ]; then
      pp_die 2 IMAGE_UNREADABLE "cannot read the pixel size of: $path (use a png or jpeg)"
    fi
    w=${size% *}; h=${size#* }
    if [ "$w" -le 0 ] || [ "$h" -le 0 ]; then
      pp_die 2 IMAGE_UNREADABLE "image has no pixels: $path"
    fi
    if [ "$w" -lt 320 ] || [ "$h" -lt 180 ]; then
      pp_fail IMAGE_SMALL "image is under 320x180 and will look soft on a slide: $path ($w x $h)"
    fi
    case $(awk -v w="$w" -v h="$h" 'BEGIN { printf "%.2f", w / h }') in
      0.0*|0.1*) pp_fail IMAGE_EXTREME "image aspect ratio is under 1:5 and will crop badly: $path ($w x $h)" ;;
    esac
    aspect=$(awk -v w="$w" -v h="$h" 'BEGIN { printf "%.6f", w / h }')
    # jq cannot update through a constructed path expression, so the slot is
    # addressed with setpath on the real array index.
    jq --argjson s "$slot" --arg p "$path" --argjson a "$aspect" '
      if $s.key == "image"
      then .slides[$s.slide].image |= (. + {path: $p, aspect: $a})
      else .slides[$s.slide].images[$s.idx] |= (. + {path: $p, aspect: $a})
      end' "$out" > "$out.tmp" && mv "$out.tmp" "$out"
    i=$((i + 1))
  done
  return 0
}

pp_main() {
  local spec='' out_dir='' name='' formats='pptx,html,png' scale=1 browser='' budget=30000 check=1
  while [ $# -gt 0 ]; do
    case $1 in
      --spec|--input) spec=${2-}; shift 2 || shift ;;
      --out-dir) out_dir=${2-}; shift 2 || shift ;;
      --name) name=${2-}; shift 2 || shift ;;
      --formats) formats=${2-}; shift 2 || shift ;;
      --scale) scale=${2-}; shift 2 || shift ;;
      --browser) browser=${2-}; shift 2 || shift ;;
      --budget-ms) budget=${2-}; shift 2 || shift ;;
      --no-check) check=0; shift ;;
      --list-browsers)
        pp_candidates | while IFS= read -r c; do
          if [ -n "$c" ] && [ -f "$c" ] && [ -x "$c" ]; then printf '%s\n' "$c"; fi
        done
        exit 0 ;;
      -h|--help) printf '%s\n' "$PP_USAGE"; exit 0 ;;
      *) printf 'unknown argument: %s\n%s\n' "$1" "$PP_USAGE" >&2; exit 2 ;;
    esac
  done
  [ -n "$spec" ] && [ -n "$out_dir" ] || { printf '%s\n' "$PP_USAGE" >&2; exit 2; }

  command -v jq >/dev/null 2>&1 || pp_die 3 JQ_MISSING "jq is required; install it with 'brew install jq'"
  [ -f "$spec" ] || pp_die 2 SPEC_MISSING "spec file not found: $spec"
  jq -e 'type == "object" and (.slides | type) == "array" and (.slides | length) > 0' "$spec" >/dev/null 2>&1 \
    || pp_die 2 SPEC_INVALID "spec must be a JSON object with a non-empty \"slides\" array"
  case $scale in 1|2|3) ;; *) pp_die 2 BAD_SCALE "--scale must be 1, 2, or 3" ;; esac
  case $budget in ''|*[!0-9]*) pp_die 2 BAD_BUDGET "--budget-ms must be a positive integer" ;; esac

  local want_pptx=0 want_html=0 want_png=0 want_pdf=0 f
  for f in $(printf '%s' "$formats" | tr ',' ' '); do
    case $f in
      pptx) want_pptx=1 ;;
      html) want_html=1 ;;
      png|jpg|jpeg) want_png=1 ;;
      pdf) want_pdf=1 ;;
      *) pp_die 2 BAD_FORMAT "unknown format '$f'; use pptx, html, png, pdf" ;;
    esac
  done
  [ $((want_pptx + want_html + want_png + want_pdf)) -gt 0 ] || pp_die 2 BAD_FORMAT "--formats is empty"

  if [ -z "$name" ]; then
    name=$(basename -- "$spec"); name=${name%.json}; name=${name%.deck}
  fi
  case $name in ''|*/*|.*) pp_die 2 BAD_NAME "--name must be a plain file stem" ;; esac

  local need_browser=0
  [ "$want_png" -eq 1 ] || [ "$want_pdf" -eq 1 ] || [ "$check" -eq 1 ] && need_browser=1
  if [ "$need_browser" -eq 1 ] && [ -z "$browser" ]; then
    browser=$(pp_find_browser)
    if [ -z "$browser" ]; then
      pp_die 3 BROWSER_MISSING "no Chromium-family browser found; run 'npx playwright install chromium-headless-shell' or pass --browser <path> / HYPER_PPTX_BROWSER"
    fi
  fi
  if [ -n "$browser" ]; then
    [ -f "$browser" ] && [ -x "$browser" ] || pp_die 3 BROWSER_MISSING "browser is not an executable file: $browser"
  fi

  command -v zip >/dev/null 2>&1 || pp_die 3 ZIP_MISSING "zip is required to write the .pptx package"

  PP_TMP=$(mktemp -d "${TMPDIR:-/tmp}/hyper-pptx.XXXXXX") || pp_die 3 TMP_FAILED "cannot create a temporary directory"
  trap 'rm -rf "$PP_TMP"' EXIT
  mkdir -p "$PP_TMP/profile"

  local out_abs resolved pkg enriched
  out_abs=$(pp_abs "$out_dir")
  mkdir -p -- "$out_abs" || pp_die 2 OUT_DIR_FAILED "cannot create output directory: $out_dir"
  resolved=$PP_TMP/resolved.json
  pkg=$PP_TMP/pkg.json
  enriched=$PP_TMP/spec.json
  PP_CHECKS='[]'

  pp_prepare_images "$spec" "$enriched"

  if ! jq -f "$PP_LAYOUT" "$enriched" > "$resolved" 2>"$PP_TMP/layout.err"; then
    # jq prefixes its own diagnostic; the message that matters starts at the code.
    local why
    why=$(head -n 1 "$PP_TMP/layout.err" \
      | sed -e 's/^jq: error ([^)]*): //' -e 's/^jq: error: //')
    pp_die 2 SPEC_INVALID "$why"
  fi

  # Chart data must be well formed before a chart part is written; a NaN or a
  # ragged series would produce a part PowerPoint refuses to open.
  local nslides i bad
  nslides=$(jq '.slides | length' "$resolved")
  i=0
  while [ "$i" -lt "$nslides" ]; do
    bad=$(jq -r --argjson i "$i" '
      .slides[$i]
      | if .chart == null then ""
        else
          (.chart.categories | length) as $nc
          | ([ .chart.series[] | (.values | length) ] | unique) as $lens
          | if ($nc == 0) then "chart on slide \($i + 1) has no categories"
            elif ([.chart.series[] | select((.values | length) != $nc)] | length) > 0
              then "chart on slide \($i + 1): every series must have one value per category (\($nc))"
            elif ([.chart.series[] | .values[] | select((type != "number") or (. != .))] | length) > 0
              then "chart on slide \($i + 1): values must be numbers (NaN and strings are not accepted)"
            elif (.chart.type == "pie" or .chart.type == "doughnut")
                 and ([.chart.series[0].values[] | select(. < 0)] | length) > 0
              then "chart on slide \($i + 1): a pie or doughnut cannot draw a negative value"
            elif (.chart.type == "pie" or .chart.type == "doughnut")
                 and ((.chart.series[0].values | add) <= 0)
              then "chart on slide \($i + 1): a pie or doughnut needs a positive total"
            elif (.chart.type == "combo") and ((.chart.series | length) < 2)
              then "chart on slide \($i + 1): a combo needs at least two series (bars and a line)"
            else ""
            end
        end' "$resolved")
    [ -z "$bad" ] || pp_die 2 CHART_INVALID "$bad"
    i=$((i + 1))
  done

  if ! jq -f "$PP_PACKAGE" "$resolved" > "$pkg" 2>"$PP_TMP/package.err"; then
    pp_die 2 SPEC_INVALID "package build failed: $(head -n 1 "$PP_TMP/package.err")"
  fi

  # Write the OOXML parts, then zip them with a fixed timestamp so the same
  # spec always produces the same file bytes.
  local stage=$PP_TMP/stage
  mkdir -p "$stage"
  local pptx_out=''
  jq -r '.parts[] | @base64' "$pkg" | while IFS= read -r row; do
    [ -n "$row" ] || continue
    printf '%s' "$row" | base64 -d > "$PP_TMP/part.json"
    local path xml
    path=$(jq -r '.path' "$PP_TMP/part.json")
    xml=$(jq -r '.xml' "$PP_TMP/part.json")
    mkdir -p "$stage/$(dirname -- "$path")"
    printf '%s' "$xml" > "$stage/$path"
  done

  # Pictures are stored as package parts; the XML only names the relationship.
  local media_rows
  media_rows=$(jq -r '.media[]? | @base64' "$pkg")
  if [ -n "$media_rows" ]; then
    while IFS= read -r row; do
      [ -n "$row" ] || continue
      printf '%s' "$row" | base64 -d > "$PP_TMP/media.json"
      local mname mpath mdest
      mname=$(jq -r '.name' "$PP_TMP/media.json")
      mpath=$(jq -r '.path' "$PP_TMP/media.json")
      mdest="$stage/ppt/media/$mname"
      mkdir -p "$stage/ppt/media"
      cp -- "$mpath" "$mdest"
    done <<< "$media_rows"
  fi

  # One workbook per chart, built beside the deck so "Edit Data" works.
  local wb_rows has_wb=0
  wb_rows=$(jq -c '.workbooks[]?' "$pkg")
  if [ -n "$wb_rows" ]; then
    has_wb=1
    mkdir -p "$stage/ppt/embeddings"
    while IFS= read -r wb; do
      [ -n "$wb" ] || continue
      local widx
      widx=$(printf '%s' "$wb" | jq -r '.index')
      printf '%s' "$wb" | jq -f "$PP_WORKBOOK" > "$PP_TMP/wb.json" \
        || pp_die 2 CHART_INVALID "cannot build the workbook for chart $widx"
      local wstage=$PP_TMP/wb$widx
      mkdir -p "$wstage"
      jq -r '.parts[] | @base64' "$PP_TMP/wb.json" | while IFS= read -r prow; do
        [ -n "$prow" ] || continue
        printf '%s' "$prow" | base64 -d > "$PP_TMP/wbpart.json"
        local wpath wxml
        wpath=$(jq -r '.path' "$PP_TMP/wbpart.json")
        wxml=$(jq -r '.xml' "$PP_TMP/wbpart.json")
        mkdir -p "$wstage/$(dirname -- "$wpath")"
        printf '%s' "$wxml" > "$wstage/$wpath"
      done
      ( cd "$wstage" && find . -exec touch -t 198001010000 {} + \
        && zip -X -q -r "$stage/ppt/embeddings/Microsoft_Excel_Worksheet$widx.xlsx" . ) \
        || pp_die 3 ZIP_FAILED "cannot write the chart workbook"
    done <<< "$wb_rows"
  fi

  jq -r '.presentation' "$pkg" > "$stage/ppt/presentation.xml"
  mkdir -p "$stage/ppt/_rels" "$stage/_rels"
  jq -r '.presentationRels' "$pkg" > "$stage/ppt/_rels/presentation.xml.rels"
  jq -r '.contentTypes' "$pkg" > "$stage/[Content_Types].xml"
  jq -r '.rootRels' "$pkg" > "$stage/_rels/.rels"

  if [ "$want_pptx" -eq 1 ]; then
    pptx_out="$out_abs/$name.pptx"
    rm -f -- "$pptx_out"
    ( cd "$stage" && find . -exec touch -t 198001010000 {} + && zip -X -q -r "$pptx_out" . ) \
      || pp_die 3 ZIP_FAILED "cannot write the .pptx package"
  fi

  # Preview HTML: the resolved deck plus the viewer, self-contained.
  local html_out='' page=$PP_TMP/preview.html
  {
    printf '<!doctype html>\n<html lang="%s"><head><meta charset="utf-8">\n' "$(jq -r '.lang // "ko"' "$resolved")"
    printf '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    printf '<title>%s</title>\n<style>\n' "$(jq -r '.title // "deck"' "$resolved" | sed -e 's/</\&lt;/g' -e 's/>/\&gt;/g')"
    cat "$PP_PREVIEW/viewer.css"
    printf '</style></head><body>\n<div id="pp-root"></div>\n'
    printf '<script type="application/json" id="pp-deck">'
    jq -c . "$resolved" | sed -e 's#</#<\\/#g' -e 's#<!--#<\\!--#g'
    printf '</script>\n<script>\n'
    cat "$PP_PREVIEW/viewer.js"
    printf '</script>\n</body></html>\n'
  } > "$page"

  if [ "$want_html" -eq 1 ]; then
    html_out="$out_abs/$name.html"
    cp -- "$page" "$html_out"
  fi

  local pages images='[]' i=0 n
  n=$(jq '.slides | length' "$resolved")
  local report='{}'

  if [ -n "$browser" ]; then
    # One bake of the whole deck gives the layout report; per-slide images come
    # from the same page with ?capture=<index>.
    if ! pp_browser "$browser" --virtual-time-budget="$budget" --dump-dom "$(pp_url "$page")" > "$PP_TMP/baked.html"; then
      pp_die 3 BAKE_FAILED "browser exited with an error: $(tail -n 2 "$PP_TMP/browser.log" 2>/dev/null | tr '\n' ' ')"
    fi
    report=$(grep -o 'data-pp-result="[^"]*"' "$PP_TMP/baked.html" | head -n 1 \
      | sed -e 's/^data-pp-result="//' -e 's/"$//' \
      | sed -e 's/&quot;/"/g' -e 's/&amp;/\&/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' -e "s/&#39;/'/g" || true)
    if [ -z "$report" ] || ! printf '%s' "$report" | jq -e . >/dev/null 2>&1; then
      pp_die 3 RUNTIME_NO_RESULT "the viewer left no layout report; raise --budget-ms or check the browser log"
    fi

    if [ "$want_png" -eq 1 ]; then
      local w h png
      w=$(printf '%s' "$report" | jq -r '.size.w')
      h=$(printf '%s' "$report" | jq -r '.size.h')
      while [ "$i" -lt "$n" ]; do
        png="$out_abs/${name}-$((i + 1)).png"
        rm -f -- "$png"
        pp_browser "$browser" --window-size="$w,$h" --force-device-scale-factor="$scale" \
          --virtual-time-budget="$budget" --screenshot="$png" "$(pp_url "$page")?capture=$i" >/dev/null || true
        if [ -s "$png" ]; then
          images=$(printf '%s' "$images" | jq -c --arg p "$png" --argjson i "$i" '. + [{index: $i, path: $p}]')
        else
          pp_fail PNG_FAILED "browser wrote no image for slide $((i + 1))"
        fi
        i=$((i + 1))
      done
    fi

    if [ "$want_pdf" -eq 1 ]; then
      local pdf="$out_abs/$name.pdf"
      rm -f -- "$pdf"
      pp_browser "$browser" --no-pdf-header-footer --print-to-pdf="$pdf" \
        --virtual-time-budget="$budget" "$(pp_url "$page")" >/dev/null || true
      [ -s "$pdf" ] || pp_fail PDF_FAILED "browser wrote no PDF"
    fi

    if [ "$check" -eq 1 ]; then
      printf '%s' "$report" | jq -r '
        .slides[] | . as $s |
        ($s.overflow[]? | "OVERFLOW slide \($s.index + 1) shape \(.shape): needs \(.needH|floor)px in \(.availH|floor)px — \(.text)"),
        ($s.outside[]? | "OUTSIDE slide \($s.index + 1) shape \(.shape): box crosses the slide edge — \(.text)"),
        ($s.overlap[]? | "OVERLAP slide \($s.index + 1) shapes \(.a) and \(.b): \(.ratio) of the smaller box covered — \(.textA) / \(.textB)")
      ' > "$PP_TMP/findings" 2>/dev/null
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        case $line in
          OVERFLOW*) pp_fail LAYOUT_OVERFLOW "$line" ;;
          OUTSIDE*) pp_fail LAYOUT_OUTSIDE "$line" ;;
          OVERLAP*) pp_fail LAYOUT_OVERLAP "$line" ;;
        esac
      done < "$PP_TMP/findings"

      # A slide whose content covers less than a third of the canvas reads as
      # unfinished. The layout engine centres and enlarges to avoid this; the
      # check is what keeps a regression from shipping silently. A cover, a
      # section opener, a hero and a pull quote are meant to be mostly empty, so
      # they are exempt by kind rather than by a lower threshold.
      printf '%s' "$report" | jq -r '
        .slides[] | .kind as $k
        | select(["title", "section", "hero", "quote"] | index($k) | not)
        | select(.coverage < 0.34)
        | "SPARSE slide \(.index + 1) (\(.kind)): content covers \(.coverage * 100 | floor)% of the slide"' \
        > "$PP_TMP/sparse" 2>/dev/null
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        pp_fail LAYOUT_SPARSE "$line"
      done < "$PP_TMP/sparse"
    fi
  fi

  # Structural self-checks on the package: every part is well-formed XML and
  # every relationship target exists.
  if command -v xmllint >/dev/null 2>&1 && [ "$want_pptx" -eq 1 ]; then
    local badxml
    badxml=$(find "$stage" \( -name '*.xml' -o -name '*.rels' \) -print0 \
      | xargs -0 -n1 xmllint --noout 2>&1 | head -n 1)
    [ -z "$badxml" ] || pp_fail XML_INVALID "$badxml"
  fi
  local missing
  pp_check_relationships "$stage" > "$PP_TMP/rel-missing" 2>/dev/null
  missing=$(head -n 1 "$PP_TMP/rel-missing")
  [ -z "$missing" ] || pp_fail RELATIONSHIP_BROKEN "$missing"

  if [ "$want_pptx" -eq 1 ]; then
    local motion_line
    pp_check_motion "$stage" > "$PP_TMP/motion-bad" 2>/dev/null
    while IFS= read -r motion_line; do
      [ -n "$motion_line" ] || continue
      pp_fail MOTION_INVALID "$motion_line"
    done < "$PP_TMP/motion-bad"
  fi

  local checks_ok
  checks_ok=$(printf '%s' "$PP_CHECKS" | jq 'length == 0')
  local summary
  summary=$(jq -cn \
    --arg status "$(if [ "$checks_ok" = "true" ]; then printf pass; else printf fail; fi)" \
    --argjson slides "$n" \
    --argjson checks "$PP_CHECKS" \
    --argjson images "$images" \
    --argjson report "$report" \
    --arg pptx "$pptx_out" --arg html "$html_out" \
    '{status: $status, slides: $slides, checks: $checks, images: $images,
      layout: { slides: ($report.slides // []) },
      pptx: (if $pptx == "" then null else $pptx end),
      html: (if $html == "" then null else $html end)}')
  printf '%s\n' "$summary"
  [ "$checks_ok" = "true" ] || exit 1
  exit 0
}

pp_main "$@"
