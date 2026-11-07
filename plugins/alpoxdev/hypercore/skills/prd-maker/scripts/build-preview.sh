#!/usr/bin/env bash
# Build a self-contained preview.html for a PRD planning package.
# Requires bash 3.2+ and jq 1.6+.
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo 'Usage: bash build-preview.sh <package-dir> [preview.html]' >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${0}")" >/dev/null 2>&1 && pwd -P)
skill_dir=${script_dir%/*}

# Lexical path normalization equivalent to Node's path.resolve for one argument.
normalize_path() {
  printf '%s' "$1" | awk -F/ '
    {
      out = ""
      for (i = 1; i <= NF; i++) {
        part = $i
        if (part == "" || part == ".") continue
        if (part == "..") {
          if (out != "") sub(/\/[^\/]*$/, "", out)
          continue
        }
        out = out "/" part
      }
      if (out == "") out = "/"
      print out
    }'
}

resolve_path() {
  case $1 in
    /*) normalize_path "$1" ;;
    *) normalize_path "$(pwd -P)/$1" ;;
  esac
}

package_dir=$(resolve_path "$1")
if [ -n "${2:-}" ]; then
  output_path=$(resolve_path "$2")
else
  output_path=$(resolve_path "$package_dir/preview.html")
fi
template_path=$skill_dir/assets/preview.template.html

if [ ! -e "$template_path" ]; then
  echo "build-preview: missing template $template_path" >&2
  exit 1
fi

template=''
IFS= read -r -d '' template <"$template_path" || true

prd=''
feature_spec=''
user_flow=''
wireframe=''
diagram_md=''
sources=''
diagram_svg=''

[ -e "$package_dir/prd.md" ] && { IFS= read -r -d '' prd <"$package_dir/prd.md" || true; }
[ -e "$package_dir/feature-spec.md" ] && { IFS= read -r -d '' feature_spec <"$package_dir/feature-spec.md" || true; }
[ -e "$package_dir/user-flow.md" ] && { IFS= read -r -d '' user_flow <"$package_dir/user-flow.md" || true; }
[ -e "$package_dir/wireframe.md" ] && { IFS= read -r -d '' wireframe <"$package_dir/wireframe.md" || true; }
[ -e "$package_dir/diagram.md" ] && { IFS= read -r -d '' diagram_md <"$package_dir/diagram.md" || true; }
[ -e "$package_dir/sources.md" ] && { IFS= read -r -d '' sources <"$package_dir/sources.md" || true; }
[ -e "$package_dir/diagram.svg" ] && { IFS= read -r -d '' diagram_svg <"$package_dir/diagram.svg" || true; }

has_flow=false
[ -e "$package_dir/flow.json" ] && has_flow=true

slug=${package_dir##*/}

# First ATX level-1 heading of prd.md; the pattern tolerates the JS \s+ newline skip.
title_raw=''
if [ -n "$prd" ]; then
  title_raw=$(printf '%s' "$prd" | awk '
    { lines[NR] = $0 }
    END {
      text = ""
      for (i = 1; i <= NR; i++) text = text lines[i] "\n"
      total = length(text)
      pos = 1
      while (pos <= total) {
        if (substr(text, pos, 1) == "#") {
          p = pos + 1
          while (p <= total) {
            ch = substr(text, p, 1)
            if (ch == " " || ch == "\t" || ch == "\n" || ch == "\r" || ch == "\v" || ch == "\f") p++
            else break
          }
          if (p <= total) {
            q = p
            while (q <= total) {
              ch = substr(text, q, 1)
              if (ch == "\n" || ch == "\r") break
              q++
            }
            print substr(text, p, q - p)
            exit
          } else if (total - pos >= 2) {
            print substr(text, total, 1)
            exit
          }
        }
        nl = index(substr(text, pos), "\n")
        if (nl == 0) break
        pos = pos + nl
      }
    }')
fi

if [ -n "$title_raw" ]; then
  title=$(printf '%s\n' "$title_raw" | awk '{
    t = tolower($0)
    if (match(t, /[[:space:]]+prd$/)) print substr($0, 1, RSTART - 1)
    else print $0
  }')
else
  title=$slug
fi

# Count "- [ ]" task lines across every document.
open_questions=0
for doc_text in "$prd" "$feature_spec" "$user_flow" "$wireframe" "$diagram_md" "$sources"; do
  [ -n "$doc_text" ] || continue
  n=$(printf '%s' "$doc_text" | awk 'substr($0, 1, 5) == "- [ ]" { c++ } END { print c + 0 }')
  open_questions=$((open_questions + n))
done

generated_at=$(jq -rn '
  now as $t
  | ($t | floor) as $s
  | (($t - $s) * 1000 | floor) as $ms
  | ($s | todateiso8601 | sub("Z$"; "")) + "."
    + (if $ms < 10 then "00" elif $ms < 100 then "0" else "" end)
    + ($ms | tostring) + "Z"')

documents_json=$(jq -cn \
  --arg id1 prd --arg label1 'PRD' --arg path1 prd.md --arg content1 "$prd" \
  --arg id2 featureSpec --arg label2 '기능명세서' --arg path2 feature-spec.md --arg content2 "$feature_spec" \
  --arg id3 userFlow --arg label3 '유저플로우' --arg path3 user-flow.md --arg content3 "$user_flow" \
  --arg id4 wireframe --arg label4 '와이어프레임' --arg path4 wireframe.md --arg content4 "$wireframe" \
  --arg id5 diagram --arg label5 '기획 맵' --arg path5 diagram.md --arg content5 "$diagram_md" \
  --arg id6 sources --arg label6 '출처 로그' --arg path6 sources.md --arg content6 "$sources" \
  '[
    {id: $id1, label: $label1, path: $path1, content: $content1},
    {id: $id2, label: $label2, path: $path2, content: $content2},
    {id: $id3, label: $label3, path: $path3, content: $content3},
    {id: $id4, label: $label4, path: $path4, content: $content4},
    {id: $id5, label: $label5, path: $path5, content: $content5},
    {id: $id6, label: $label6, path: $path6, content: $content6}
  ]')

safe_json=$(jq -cn \
  --arg title "$title" \
  --arg slug "$slug" \
  --arg generatedAt "$generated_at" \
  --argjson hasFlow "$has_flow" \
  --argjson openQuestionCount "$open_questions" \
  --arg diagramSvg "$diagram_svg" \
  --argjson documents "$documents_json" \
  '{title: $title, slug: $slug, generatedAt: $generatedAt, hasFlow: $hasFlow, openQuestionCount: $openQuestionCount, diagramSvg: $diagramSvg, documents: $documents}')

# JSON.stringify keeps U+007F raw while jq escapes it as \u007f.
safe_json=$(printf '%s' "$safe_json" | awk '
  {
    s = $0; out = ""; n = length(s); i = 1
    while (i <= n) {
      c = substr(s, i, 1)
      if (c == "\\") {
        nxt = substr(s, i + 1, 1)
        if (i + 5 <= n && nxt == "u" && substr(s, i + 1, 5) == "u007f") {
          out = out sprintf("%c", 127); i += 6
        } else if (nxt != "") {
          out = out c nxt; i += 2
        } else {
          out = out c; i += 1
        }
      } else {
        out = out c; i += 1
      }
    }
    printf "%s", out
  }')

# The template uses "<" inside the embedded JSON; escape it so </script> cannot close early.
safe_json=${safe_json//</\\u003c}

ESCAPED=''
escape_html_attr() {
  local value=$1
  value=${value//&/&amp;}
  value=${value//</&lt;}
  value=${value//>/&gt;}
  value=${value//\"/&quot;}
  ESCAPED=$value
}

# String.prototype.replace treats $&, $`, $', $$ in the replacement specially.
JS_OUT=''
js_expand_replacement() {
  local repl=$1 matched=$2 prefix=$3 suffix=$4
  local out='' i=0 n=${#repl} c
  while [ "$i" -lt "$n" ]; do
    c=${repl:$i:1}
    if [ "$c" = '$' ] && [ $((i + 1)) -lt "$n" ]; then
      case ${repl:$((i + 1)):1} in
        '$') out=$out'$'; i=$((i + 2)); continue ;;
        '&') out=$out$matched; i=$((i + 2)); continue ;;
        '`') out=$out$prefix; i=$((i + 2)); continue ;;
        "'") out=$out$suffix; i=$((i + 2)); continue ;;
      esac
    fi
    out=$out$c
    i=$((i + 1))
  done
  JS_OUT=$out
}

js_replace_all() {
  local hay=$1 needle=$2 repl=$3
  local out='' rest=$hay consumed='' pre post prefix suffix
  while [ "${rest#*"$needle"}" != "$rest" ]; do
    pre=${rest%%"$needle"*}
    post=${rest#*"$needle"}
    prefix=$consumed$pre
    suffix=$post
    js_expand_replacement "$repl" "$needle" "$prefix" "$suffix"
    out=$out$prefix$JS_OUT
    consumed=$prefix$needle
    rest=$post
  done
  JS_OUT=$out$rest
}

escape_html_attr "$title"
js_replace_all "$template" '{{TITLE}}' "$ESCAPED"
html=$JS_OUT
case $html in
  *'{{PACKAGE_JSON}}'*)
    prefix=${html%%'{{PACKAGE_JSON}}'*}
    suffix=${html#*'{{PACKAGE_JSON}}'}
    js_expand_replacement "$safe_json" '{{PACKAGE_JSON}}' "$prefix" "$suffix"
    html=$prefix$JS_OUT$suffix
    ;;
esac

if ! { printf '%s' "$html" >"$output_path"; } 2>/dev/null; then
  echo "build-preview: cannot write $output_path" >&2
  exit 1
fi
printf 'Built %s\n' "$output_path"
