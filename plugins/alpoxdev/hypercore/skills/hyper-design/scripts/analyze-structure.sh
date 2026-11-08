#!/usr/bin/env bash
# Count repeated page-structure signals in supported source files and emit stable JSON.
set -euo pipefail

RS_STRUCT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_STRUCT_DIR/rule-shared.sh"

STRUCT_USAGE='Usage: bash analyze-structure.sh --target <file-or-directory> --json'

struct_fail() {
  printf '%s\n' "$(jq -cn --arg error "$1" '{error: $error, version: 2}')" >&2
  exit 2
}

# struct_files <absolute-target> prints supported markup files, skipping ignored directories.
struct_files() {
  local abs_target=$1 path
  if [ -f "$abs_target" ]; then
    printf '%s\n' "$abs_target"
    return 0
  fi
  find "$abs_target" \( -name .git -o -name node_modules -o -name dist -o -name build -o -name coverage \
    -o -name .next -o -name .nuxt -o -name .svelte-kit \) -prune -o -type f -print 2>/dev/null |
    while IFS= read -r path; do
      if rs_is_markup_ext "$(rs_extname "$path")"; then printf '%s\n' "$path"; fi
    done |
    LC_ALL=C sort
}

struct_count_table() {
  cat <<'COUNTS'
sections	<section\b	gi
cards	\bcard\b	gi
eyebrows	\b(?:eyebrow|kicker)\b	gi
numberedSectionLabels	\b(?:section-number|step-number)\b|>\s*0[1-9]\s*<	gi
iconTiles	\bicon-tile\b	gi
gridsOfThree	\b(?:grid-cols-3|repeat\(\s*3\s*,)	gi
headings	<h[1-6]\b	gi
ctas	\b(?:cta|call-to-action)\b	gi
navs	<nav\b	gi
footers	<footer\b	gi
COUNTS
}

struct_main() {
  local target='' help=0 abs_target root file rel counts table rows file_json
  while [ $# -gt 0 ]; do
    case "$1" in
      --target) shift; target=${1-}; if [ $# -gt 0 ]; then shift; fi ;;
      --json) shift ;;
      --help|-h) help=1; break ;;
      *) struct_fail "Unknown argument: $1" ;;
    esac
  done
  if [ "$help" = 1 ]; then
    printf '%s\n' "$STRUCT_USAGE"
    return 0
  fi
  [ -n "$target" ] || struct_fail '--target requires a path'
  abs_target=$(rs_resolve "$target")
  [ -e "$abs_target" ] || struct_fail "ENOENT: no such file or directory, stat '$abs_target'"
  if [ -f "$abs_target" ]; then
    ext=$(rs_extname "$abs_target")
    if ! rs_is_markup_ext "$ext"; then
      [ -n "$ext" ] || ext='(none)'
      struct_fail "Unsupported file type: $ext"
    fi
  elif [ ! -d "$abs_target" ]; then
    struct_fail 'Target must be a file or directory'
  fi
  table=$(mktemp "${TMPDIR:-/tmp}/slop-counts.XXXXXX")
  struct_count_table > "$table"
  rows=$(mktemp "${TMPDIR:-/tmp}/slop-rows.XXXXXX")
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    counts=$(rs_scan_table count text "$file" < "$table")
    if [ -d "$abs_target" ]; then
      root=$abs_target
    else
      root=$(dirname -- "$abs_target")
    fi
    rel=${file#"$root"/}
    [ -n "$rel" ] || rel=$file
    jq -cn --arg file "$rel" --argjson counts "$(printf '%s\n' "$counts" | jq -Rn '
      reduce inputs as $line ({};
        ($line | split("\t")) as $parts | .[$parts[0]] = ($parts[1] | tonumber))')" \
      '{file: $file, sections: $counts.sections, cards: $counts.cards, eyebrows: $counts.eyebrows,
        numberedSectionLabels: $counts.numberedSectionLabels, iconTiles: $counts.iconTiles,
        gridsOfThree: $counts.gridsOfThree, headings: $counts.headings, ctas: $counts.ctas,
        navs: $counts.navs, footers: $counts.footers}' >> "$rows"
  done < <(struct_files "$abs_target")
  file_json=$(jq -s '.' < "$rows")
  rm -f -- "$table" "$rows"
  jq -n --arg target "$target" --argjson files "$file_json" \
    '{target: $target, version: 2, files: $files,
      limitations: ["Counts are structural source signals only; they do not determine whether a layout is generic, inappropriate, or safe to change."]}'
}

struct_main "$@"
