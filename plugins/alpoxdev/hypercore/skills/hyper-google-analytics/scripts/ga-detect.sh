#!/usr/bin/env bash
# ga-detect.sh - list every Google Analytics 4 and Google Tag Manager signal a
# repository already contains, with the file and line that showed it.
#
# Usage: bash ga-detect.sh <repo-root>
#   <repo-root>  directory to scan (required)
#
# Output (stdout, one compact JSON object per line, sorted by path then line):
#   {"kind":"<kind>","path":"<relative path>","line":<number>,"value":"<evidence>"}
#   {"summary":{"files_scanned":<n>,"findings":<n>}}
#
# Kinds: measurement_id, gtm_id, gtag_snippet, gtm_snippet, framework_integration,
# consent_default, consent_update, send_page_view, debug_mode, csp_header,
# mp_endpoint, possible_api_secret.
#
# It reads files only. It skips node_modules, .git, .next, dist, and build, and it
# never reads a real .env file (only .env.example, .env.sample, .env.template).
# A value that looks like an API secret prints at most its first four characters.
# files_scanned counts every candidate file after the skip and env filters.
# Exit codes: 0 scan completed (even with no finding), 3 missing dependency (jq),
# 64 bad usage (no argument, extra arguments, or a non-directory).
# Requires bash 3.2+, POSIX find/grep/sed/sort, and jq 1.6+.
set -euo pipefail

if [ "$#" -eq 1 ]; then
  case $1 in
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
  esac
fi

if [ "$#" -eq 0 ]; then
  echo "usage: bash ga-detect.sh <repo-root>" >&2
  exit 64
fi
if [ "$#" -gt 1 ]; then
  echo "ga-detect: expected exactly one repository root" >&2
  exit 64
fi
ROOT_LABEL=$1
if [ ! -d "$ROOT_LABEL" ]; then
  echo "ga-detect: not a directory: $ROOT_LABEL" >&2
  exit 64
fi

command -v jq >/dev/null 2>&1 || { echo "ga-detect: jq is required" >&2; exit 3; }
ROOT=$(CDPATH='' cd -- "$ROOT_LABEL" && pwd)

HITS=$(mktemp "${TMPDIR:-/tmp}/ga-detect.XXXXXX")
CANDIDATES=$(mktemp "${TMPDIR:-/tmp}/ga-detect.XXXXXX")
SORTED=$(mktemp "${TMPDIR:-/tmp}/ga-detect.XXXXXX")
trap 'rm -f "$HITS" "$CANDIDATES" "$SORTED"' EXIT

TAB=$(printf '\t')

# add_hit <relative path> <line> <kind> <value>
add_hit() {
  local value
  value=$(printf '%s' "$4" | tr '\t\r' '  ')
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$value" >>"$HITS"
}

# emit <relative path> <absolute path> <kind> <extended regex> [i]
# Prints one hit per match of the regex on each line. Binary files are skipped.
emit() {
  local rel=$1 abs=$2 kind=$3 pattern=$4 mode=${5:-}
  local out line value
  if [ "$mode" = "i" ]; then
    out=$(grep -n -I -i -E -o -- "$pattern" "$abs" 2>/dev/null) || return 0
  else
    out=$(grep -n -I -E -o -- "$pattern" "$abs" 2>/dev/null) || return 0
  fi
  [ -n "$out" ] || return 0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    value=${line#*:}
    add_hit "$rel" "${line%%:*}" "$kind" "$value"
  done <<EOF
$out
EOF
}

# emit_secret <relative path> <absolute path>
# Prints only the masked value: four characters, or **** when shorter.
emit_secret() {
  local rel=$1 abs=$2
  local out line value
  out=$(grep -n -I -E -o -- '(api_secret|apiSecret)[[:space:]]*[=:][[:space:]]*["'\'']?[A-Za-z0-9_.~-]{4,}' "$abs" 2>/dev/null) || return 0
  [ -n "$out" ] || return 0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    value=${line#*:}
    value=${value##*[=:]}
    while [ "${value# }" != "$value" ]; do value=${value# }; done
    while [ "${value#\"}" != "$value" ]; do value=${value#\"}; done
    while [ "${value#\'}" != "$value" ]; do value=${value#\'}; done
    if [ "${#value}" -gt 4 ]; then
      value="${value:0:4}…"
    else
      value="****"
    fi
    add_hit "$rel" "${line%%:*}" possible_api_secret "$value"
  done <<EOF
$out
EOF
}

find "$ROOT" \( -name node_modules -o -name .git -o -name .next -o -name dist -o -name build \) -prune \
  -o -type f -print 2>/dev/null | LC_ALL=C sort >"$CANDIDATES"

FILES_SCANNED=0
while IFS= read -r abs; do
  [ -n "$abs" ] || continue
  base=${abs##*/}
  case $base in
    .env | .env.*)
      case $base in
        .env.example | .env.sample | .env.template) : ;;
        *) continue ;;
      esac
      ;;
  esac
  rel=${abs#"$ROOT"/}
  FILES_SCANNED=$((FILES_SCANNED + 1))

  emit "$rel" "$abs" measurement_id 'G-[A-Z0-9]{4,}'
  emit "$rel" "$abs" gtm_id 'GTM-[A-Z0-9]{4,}'
  emit "$rel" "$abs" gtag_snippet 'googletagmanager\.com/gtag/js'
  emit "$rel" "$abs" gtm_snippet 'googletagmanager\.com/(gtm\.js|ns\.html)'
  emit "$rel" "$abs" framework_integration '(@next/third-parties/google|<GoogleAnalytics|<GoogleTagManager|sendGAEvent|sendGTMEvent|vue-gtag|react-ga4|@nuxt/scripts|googlesitekit)'
  emit "$rel" "$abs" consent_default 'consent.{0,40}default'
  emit "$rel" "$abs" consent_update 'consent.{0,40}update'
  emit "$rel" "$abs" send_page_view 'send_page_view.{0,40}'
  emit "$rel" "$abs" debug_mode 'debug_mode.{0,40}'
  emit "$rel" "$abs" csp_header '(content-security-policy|script-src-elem[^;]{0,60}googletagmanager)' i
  emit "$rel" "$abs" mp_endpoint '[A-Za-z0-9.-]*google-analytics\.com/mp/collect'
  emit_secret "$rel" "$abs"
done <"$CANDIDATES"

LC_ALL=C sort -s -t "$TAB" -k1,1 -k2,2n "$HITS" >"$SORTED"

if [ -s "$SORTED" ]; then
  jq -R -c 'split("\t") | {kind: .[2], path: .[0], line: (.[1] | tonumber), value: .[3]}' "$SORTED"
fi

FINDINGS=$(wc -l <"$SORTED" | tr -d ' ')
jq -c -n --argjson files "$FILES_SCANNED" --argjson findings "$FINDINGS" \
  '{summary: {files_scanned: $files, findings: $findings}}'
