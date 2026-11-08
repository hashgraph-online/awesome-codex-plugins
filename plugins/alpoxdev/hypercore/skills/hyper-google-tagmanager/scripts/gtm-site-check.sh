#!/usr/bin/env bash
# gtm-site-check.sh - read one page's served HTML and report which Google Tag
# Manager containers and Google tags it loads, where, in what order relative to
# consent defaults and the dataLayer, and (optionally) whether each container's
# gtm.js is served.
#
# Usage: bash gtm-site-check.sh (--url <url> | --html-file <file>) [--check-loader]
#   --url           fetch the page with curl (follows redirects, 20 s timeout)
#   --html-file     read saved HTML instead of fetching (no network)
#   --check-loader  also request https://www.googletagmanager.com/gtm.js?id=<ID>
#                   for each container ID and record the HTTP status and bytes
#
# Output (stdout, one JSON object):
#   {"source": "<url or file as given>", "httpStatus": 200|null, "bytes": N,
#    "containers": [{"id": "GTM-XXXX", "loaderCount": 1, "noscript": true,
#                    "loaderInHead": true, "loaderStatus": 200|null, "loaderBytes": N|null,
#                    "loaderResourceVersion": "44"|null, "loaderEmpty": false|null}],
#    "googleTagIds": ["G-XXXX"],
#    "order": {"dataLayerInit": N|null, "consentDefault": N|null, "firstGtmLoader": N|null},
#    "findings": [{"severity": "warn", "code": "...", "detail": "..."}]}
# Order values are byte offsets of the first match in the HTML, or null.
#
# Served HTML shows only what the server sends: a framework that injects the
# loader after hydration, or a tag GTM itself adds, is absent here and needs a
# rendered-browser check. Exit codes: 0 checked (even with findings), 2 bad
# arguments, 3 missing dependency (jq, curl), 4 the page could not be fetched.
# Requires bash 3.2+, curl, grep, and jq 1.6+.
set -euo pipefail

URL="" HTML_FILE="" CHECK_LOADER=0
while [ "$#" -gt 0 ]; do
  case $1 in
    --url)
      [ "$#" -ge 2 ] || { echo "gtm-site-check: --url needs a value" >&2; exit 2; }
      URL=$2; shift 2 ;;
    --html-file)
      [ "$#" -ge 2 ] || { echo "gtm-site-check: --html-file needs a value" >&2; exit 2; }
      HTML_FILE=$2; shift 2 ;;
    --check-loader) CHECK_LOADER=1; shift ;;
    -h | --help) awk 'NR > 1 && /^#/ { print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "gtm-site-check: unknown argument: $1" >&2; exit 2 ;;
  esac
done

command -v jq >/dev/null 2>&1 || { echo "gtm-site-check: jq is required" >&2; exit 3; }
if [ -n "$URL" ] && [ -n "$HTML_FILE" ]; then echo "gtm-site-check: use --url or --html-file, not both" >&2; exit 2; fi
if [ -z "$URL" ] && [ -z "$HTML_FILE" ]; then echo "gtm-site-check: --url or --html-file is required" >&2; exit 2; fi
if [ -n "$URL" ]; then
  case $URL in http://* | https://*) : ;; *) echo "gtm-site-check: --url must start with http:// or https://" >&2; exit 2 ;; esac
fi
if [ -n "$URL" ] || [ "$CHECK_LOADER" -eq 1 ]; then
  command -v curl >/dev/null 2>&1 || { echo "gtm-site-check: curl is required" >&2; exit 3; }
fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/gtm-site-check.XXXXXX")
trap 'rm -rf "$WORK"' EXIT
PAGE=$WORK/page.html
STATUS=null SOURCE=$URL

if [ -n "$HTML_FILE" ]; then
  [ -f "$HTML_FILE" ] || { echo "gtm-site-check: not a file: $HTML_FILE" >&2; exit 2; }
  cp "$HTML_FILE" "$PAGE"
  SOURCE=$HTML_FILE
else
  if ! STATUS=$(curl -sSL --max-time 20 -A 'Mozilla/5.0 (compatible; gtm-site-check)' \
    -o "$PAGE" -w '%{http_code}' "$URL" 2>"$WORK/curl.err"); then
    echo "gtm-site-check: fetch failed: $(head -n 1 "$WORK/curl.err")" >&2
    exit 4
  fi
fi

# offset <regex>: byte offset of the first match, or null.
offset() {
  local o
  o=$(LC_ALL=C grep -boE "$1" "$PAGE" 2>/dev/null | head -n 1 | cut -d: -f1 || true)
  if [ -n "$o" ]; then printf '%s' "$o"; else printf 'null'; fi
}

HEAD_END=$(offset '</head>')
IDS=$(LC_ALL=C grep -oE 'GTM-[A-Z0-9]{4,10}' "$PAGE" | LC_ALL=C sort -u || true)
: >"$WORK/containers.tsv"
for id in $IDS; do
  # A loader is a gtm.js URL carrying the ID, or the classic snippet whose
  # IIFE receives the ID as its last argument: ...,'dataLayer','GTM-XXXX');
  loaders=$({ LC_ALL=C grep -oE "gtm\\.js\\?id=$id|['\"]$id['\"] *\\)" "$PAGE" || true; } | wc -l | tr -d ' ')
  first=$(offset "gtm\\.js\\?id=$id|['\"]$id['\"] *\\)")
  noscript=false
  LC_ALL=C grep -qE "googletagmanager\\.com/ns\\.html\\?id=$id" "$PAGE" && noscript=true
  in_head=false
  if [ "$first" != null ] && [ "$HEAD_END" != null ] && [ "$first" -lt "$HEAD_END" ]; then in_head=true; fi
  lstatus=null lbytes=null lversion=null lempty=null
  if [ "$CHECK_LOADER" -eq 1 ]; then
    out=$(curl -sS --max-time 20 -o "$WORK/gtm-$id.js" -w '%{http_code}' \
      "https://www.googletagmanager.com/gtm.js?id=$id" 2>/dev/null || printf '000')
    lstatus=$out
    lbytes=$(wc -c <"$WORK/gtm-$id.js" 2>/dev/null | tr -d ' ' || printf 0)
    # gtm.js answers 200 even for an ID that does not exist; the resource
    # block then has version "1" and empty macros and tags arrays.
    flat=$(tr -d '\n' <"$WORK/gtm-$id.js" 2>/dev/null || true)
    v=$(printf '%s' "$flat" | grep -oE '"resource": *\{ *"version":"[0-9]+"' | head -n 1 | grep -oE '[0-9]+' || true)
    [ -n "$v" ] && lversion=$v
    if printf '%s' "$flat" | grep -qE '"resource": *\{ *"version":"[0-9]+" *, *"macros":\[ *\] *, *"tags":\[ *\]'; then
      lempty=true
    elif [ -n "$v" ]; then
      lempty=false
    fi
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$loaders" "$noscript" "$in_head" "$lstatus" "$lbytes" "$lversion" "$lempty" >>"$WORK/containers.tsv"
done
GTAG_IDS=$(LC_ALL=C grep -oE "googletagmanager\\.com/gtag/js\\?id=(G|AW|DC|GT)-[A-Z0-9]{4,12}|['\"]config['\"], *['\"](G|AW|DC|GT)-[A-Z0-9]{4,12}" "$PAGE" \
  | grep -oE '(G|AW|DC|GT)-[A-Z0-9]{4,12}' | LC_ALL=C sort -u || true)
GTM_LOADER_COUNT=$({ LC_ALL=C grep -oE 'googletagmanager\.com/gtm\.js' "$PAGE" || true; } | wc -l | tr -d ' ')
NON_GTM_ON_GTMJS=$(LC_ALL=C grep -oE 'gtm\.js\?id=(G|AW|DC)-[A-Z0-9]{4,12}' "$PAGE" | grep -oE '(G|AW|DC)-[A-Z0-9]{4,12}' | LC_ALL=C sort -u || true)
DL_INIT=$(offset 'dataLayer *= *(window\.)?dataLayer *\|\|')
CONSENT=$(offset "['\"]consent['\"], *['\"]default['\"]")
FIRST_LOADER=$(offset 'googletagmanager\.com/gtm\.js')
BYTES=$(wc -c <"$PAGE" | tr -d ' ')

jq -n --arg source "$SOURCE" --argjson status "$STATUS" --argjson bytes "$BYTES" \
  --rawfile c "$WORK/containers.tsv" --arg gtag "$GTAG_IDS" --arg nongtm "$NON_GTM_ON_GTMJS" \
  --argjson dl "$DL_INIT" --argjson consent "$CONSENT" --argjson loader "$FIRST_LOADER" \
  --argjson loaderCount "$GTM_LOADER_COUNT" '
  ($c | split("\n") | map(select(length > 0) | split("\t")
    | {id: .[0], loaderCount: (.[1] | tonumber), noscript: (.[2] == "true"),
       loaderInHead: (.[3] == "true"),
       loaderStatus: (if .[4] == "null" then null else (.[4] | tonumber) end),
       loaderBytes: (if .[5] == "null" then null else (.[5] | tonumber) end),
       loaderResourceVersion: (if .[6] == "null" then null else .[6] end),
       loaderEmpty: (if .[7] == "null" then null else (.[7] == "true") end)})) as $containers
  | ($gtag | split("\n") | map(select(length > 0))) as $gt
  | ($nongtm | split("\n") | map(select(length > 0))) as $ng
  | {source: $source, httpStatus: $status, bytes: $bytes,
     containers: $containers, googleTagIds: $gt,
     order: {dataLayerInit: $dl, consentDefault: $consent, firstGtmLoader: $loader},
     findings: ([
       (if ($containers | length) == 0 then {severity: "info", code: "NO_CONTAINER_IN_HTML",
          detail: "no GTM container ID in the served HTML; check the rendered page if the framework injects it on the client"} else empty end),
       (if ($containers | length) > 1 then {severity: "warn", code: "MULTIPLE_CONTAINERS",
          detail: "the page references \($containers | length) containers: \([$containers[].id] | join(", "))"} else empty end),
       (if $loaderCount > ($containers | length) and ($containers | length) > 0 then {severity: "warn", code: "DUPLICATE_LOADER",
          detail: "gtm.js is referenced \($loaderCount) times for \($containers | length) container(s)"} else empty end),
       ($containers[] | select(.loaderCount > 0 and (.loaderInHead | not))
        | {severity: "warn", code: "LOADER_NOT_IN_HEAD", detail: "\(.id) loader is not inside <head>"}),
       ($ng[] | {severity: "error", code: "GTMJS_NON_GTM_ID",
          detail: "\(.) is loaded through the gtm.js path; Google calls a non-GTM ID on gtm.js unsupported, load it with gtag/js or use the GTM- container ID"}),
       ($containers[] | select(.loaderCount == 0)
        | {severity: "info", code: "ID_WITHOUT_LOADER", detail: "\(.id) appears in the HTML but no gtm.js loader does; a script loads it at run time, so confirm it in a rendered browser"}),
       ($containers[] | select(.loaderStatus != null and .loaderStatus != 200)
        | {severity: "error", code: "LOADER_NOT_SERVED", detail: "gtm.js?id=\(.id) answered HTTP \(.loaderStatus)"}),
       ($containers[] | select(.loaderEmpty == true)
        | {severity: "error", code: "LOADER_EMPTY_CONTAINER", detail: "gtm.js?id=\(.id) returned an empty container (resource version \(.loaderResourceVersion), no tags or variables); the ID is wrong or nothing was published"}),
       (if ($gt | length) > 0 and ($containers | length) > 0 then {severity: "warn", code: "GTM_AND_GTAG",
          detail: "the page loads GTM and a direct Google tag (\($gt | join(", "))); one measurement ID configured in both double-counts"} else empty end),
       (if $consent != null and $loader != null and $consent > $loader then {severity: "warn", code: "CONSENT_AFTER_LOADER",
          detail: "the consent default appears after the gtm.js loader; put the default command above the container snippet so it runs before any measurement command"} else empty end)
     ])}'
