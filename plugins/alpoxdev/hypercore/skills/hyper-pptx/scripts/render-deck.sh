#!/usr/bin/env bash
# render-deck.sh — build a .pptx from a JSON deck spec and render it to images.
#
# Pipeline: spec.json -> layout.jq (geometry) -> pptx-package.jq (OOXML)
#           -> .pptx (zip) -> preview.html -> per-slide PNG (headless Chromium)
#
# Everything is deterministic: same spec, same bytes, no timestamps in the
# archive. The script needs bash 3.2+, jq, zip/unzip, and one Chromium-family
# browser binary for the preview and the slide images.
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
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)" \
    "$(command -v google-chrome 2>/dev/null || true)"
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

# Every relationship target must resolve to a part in the package. bash 3.2
# cannot parse a case statement inside a command substitution, so this runs as
# its own function writing to stdout.
pp_check_relationships() { # <stage dir>
  local stage=$1 rel base tgt tpath
  cd "$stage" || return 0
  find . -name '*.rels' | while IFS= read -r rel; do
    base=$(dirname -- "$(dirname -- "$rel")")
    grep -o 'Target="[^"]*"' "$rel" | sed -e 's/^Target="//' -e 's/"$//' | while IFS= read -r tgt; do
      if [ "${tgt#http}" != "$tgt" ]; then
        continue
      fi
      if [ "${tgt#../}" != "$tgt" ]; then
        tpath=$base/$tgt
      else
        tpath=$base/$tgt
      fi
      if [ ! -f "$tpath" ]; then
        printf '%s -> %s\n' "$rel" "$tgt"
      fi
    done
  done
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

  local out_abs resolved pkg
  out_abs=$(pp_abs "$out_dir")
  mkdir -p -- "$out_abs" || pp_die 2 OUT_DIR_FAILED "cannot create output directory: $out_dir"
  resolved=$PP_TMP/resolved.json
  pkg=$PP_TMP/pkg.json

  if ! jq -f "$PP_LAYOUT" "$spec" > "$resolved" 2>"$PP_TMP/layout.err"; then
    pp_die 2 SPEC_INVALID "layout failed: $(head -n 1 "$PP_TMP/layout.err")"
  fi
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
      local mslot mext mpath mdest
      mslot=$(jq -r '.slot' "$PP_TMP/media.json")
      mext=$(jq -r '.ext' "$PP_TMP/media.json")
      mpath=$(jq -r '.path' "$PP_TMP/media.json")
      mdest="$stage/ppt/media/image$((mslot + 1)).$mext"
      mkdir -p "$stage/ppt/media"
      case $mpath in
        http://*|https://*) pp_die 2 IMAGE_REMOTE "image paths must be local files: $mpath" ;;
      esac
      mpath=$(pp_abs "$mpath")
      if [ ! -f "$mpath" ]; then
        pp_die 2 IMAGE_MISSING "image file not found: $mpath"
      fi
      case $mext in png|jpg|jpeg|gif) ;; *) pp_die 2 IMAGE_TYPE "use a png, jpg, or gif image: $mpath" ;; esac
      cp -- "$mpath" "$mdest"
    done <<< "$media_rows"
  fi
  jq -r '.presentation' "$pkg" > "$stage/ppt/presentation.xml"
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
  PP_CHECKS='[]'
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
        ($s.outside[]? | "OUTSIDE slide \($s.index + 1) shape \(.shape): box crosses the slide edge — \(.text)")
      ' > "$PP_TMP/findings" 2>/dev/null
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        pp_fail LAYOUT_OVERFLOW "$line"
      done < "$PP_TMP/findings"
    fi
  fi

  # Structural self-checks on the package: every part is well-formed XML and
  # every relationship target exists.
  if command -v xmllint >/dev/null 2>&1 && [ "$want_pptx" -eq 1 ]; then
    local bad
    bad=$(find "$stage" \( -name '*.xml' -o -name '*.rels' \) -print0 \
      | xargs -0 -n1 xmllint --noout 2>&1 | head -n 1)
    [ -z "$bad" ] || pp_fail XML_INVALID "$bad"
  fi
  local missing
  pp_check_relationships "$stage" > "$PP_TMP/rel-missing" 2>/dev/null
  missing=$(head -n 1 "$PP_TMP/rel-missing")
  [ -z "$missing" ] || pp_fail RELATIONSHIP_BROKEN "$missing"

  local checks_ok
  checks_ok=$(printf '%s' "$PP_CHECKS" | jq 'length == 0')
  local summary
  summary=$(jq -cn \
    --arg status "$(if [ "$checks_ok" = "true" ]; then printf pass; else printf fail; fi)" \
    --argjson slides "$n" \
    --argjson checks "$PP_CHECKS" \
    --argjson images "$images" \
    --arg pptx "$pptx_out" --arg html "$html_out" \
    '{status: $status, slides: $slides, checks: $checks, images: $images,
      pptx: (if $pptx == "" then null else $pptx end),
      html: (if $html == "" then null else $html end)}')
  printf '%s\n' "$summary"
  [ "$checks_ok" = "true" ] || exit 1
  exit 0
}

pp_main "$@"
