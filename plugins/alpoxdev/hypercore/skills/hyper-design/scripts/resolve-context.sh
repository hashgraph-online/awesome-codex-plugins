#!/usr/bin/env bash
# Read only explicit local context declarations that the detector may treat as evidence.
set -euo pipefail

RS_CONTEXT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_CONTEXT_DIR/rule-shared.sh"

# is_below <path> <root> reports whether path is inside root.
is_below() {
  case "$1" in
    "$2"/*) return 0 ;;
  esac
  return 1
}

# resolve_context <target> prints brand/pricing/state/motion flags as 1/0 tab-separated fields.
# It reads DESIGN.md and PRODUCT.md from the target ancestors up to the working directory, then any
# direct stylesheet context, exactly like the module it replaces.
resolve_context() {
  local target=$1 abs_target cwd scope current work brand pricing state motion
  local first=1 path
  [ -e "$target" ] || return 1
  cwd=$(pwd -P)
  if [ -d "$target" ]; then
    abs_target=$(cd -- "$target" && pwd -P)
    scope=$abs_target
  else
    abs_target=$(cd -- "$(dirname -- "$target")" && pwd -P)/$(basename -- "$target")
    scope=$(dirname -- "$abs_target")
  fi
  work=$(mktemp "${TMPDIR:-/tmp}/slop-context.XXXXXX")
  add_input() {
    if [ "$first" = 1 ]; then
      first=0
    else
      printf '\n' >> "$work"
    fi
    if [ -n "$1" ] && [ -f "$1" ]; then
      cat -- "$1" >> "$work"
    fi
  }
  current=$scope
  while [ "$current" = "$cwd" ] || is_below "$current" "$cwd"; do
    add_input "$current/DESIGN.md"
    add_input "$current/PRODUCT.md"
    [ "$current" = "$cwd" ] && break
    current=$(dirname -- "$current")
  done
  if [ -d "$target" ]; then
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      if rs_is_style_ext "$(rs_extname "$path")"; then add_input "$path"; fi
    done < <(find "$target" -maxdepth 1 -type f -print 2>/dev/null | LC_ALL=C sort)
  elif rs_is_style_ext "$(rs_extname "$target")"; then
    add_input "$target"
  fi
  tr '[:upper:]' '[:lower:]' < "$work" > "$work.lower"
  rm -f -- "$work"
  brand=$(printf '%s\t%s\t%s\n' \
    'brandGradient' '(?:approved|brand|keep|required)[\s\S]{0,140}(?:purple|violet)[\s\S]{0,140}(?:blue|gradient)|(?:purple|violet)[\s\S]{0,140}(?:blue|gradient)[\s\S]{0,140}(?:approved|brand|keep|required)' '' |
    rs_scan_table bool text "$work.lower" | LC_ALL=C awk -F '\t' '$1 == "brandGradient" { print $2 }')
  pricing=$(printf '%s\t%s\t%s\n' \
    'pricingComparison' '\b(?:pricing|comparison|plan|tier)\b' '' |
    rs_scan_table bool text "$work.lower" | LC_ALL=C awk -F '\t' '$1 == "pricingComparison" { print $2 }')
  state=$(printf '%s\t%s\t%s\n' \
    'realState' '\b(?:recording|live|sync|unread|online)\b' '' |
    rs_scan_table bool text "$work.lower" | LC_ALL=C awk -F '\t' '$1 == "realState" { print $2 }')
  motion=$(printf '%s\t%s\t%s\n' \
    'reducedMotion' 'prefers-reduced-motion|motion-reduce:' '' |
    rs_scan_table bool text "$work.lower" | LC_ALL=C awk -F '\t' '$1 == "reducedMotion" { print $2 }')
  rm -f -- "$work.lower"
  printf '%s\t%s\t%s\t%s\n' "$brand" "$pricing" "$state" "$motion"
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
