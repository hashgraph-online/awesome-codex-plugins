#!/usr/bin/env bash
# gtm-detect.sh - list the web framework, the Google Tag Manager and Google tag
# installs, the dataLayer and consent code, and the CSP declarations a
# repository already carries, with the file and line that showed each one.
#
# Usage: bash gtm-detect.sh [--root <dir>]
#   --root  repository root to scan (default: current directory)
#
# Output (stdout, one JSON object):
#   {"root": "<the --root value as given>",
#    "frameworks": [{"framework": "next", "evidence": [{"file": "package.json", "signal": "\"next\":"}]}],
#    "signals": [{"kind": "gtm-id", "value": "GTM-XXXX", "file": "app/layout.tsx", "line": 12}],
#    "containerIds": ["GTM-XXXX"], "googleTagIds": ["G-XXXX"],
#    "findings": [{"severity": "warn", "code": "...", "detail": "..."}]}
#
# Signal kinds: gtm-id, gtm-loader, gtm-noscript, gtmjs-non-gtm-id, gtag-loader,
# gtag-config, google-tag-id,
# next-gtm-component, next-ga-component, nuxt-scripts-gtm, datalayer-init,
# datalayer-reset, consent-default, consent-update, csp, partytown.
#
# Finding codes: MULTIPLE_CONTAINER_IDS, MULTIPLE_GTM_LOADERS, LOADER_IN_SEVERAL_FILES,
# GTMJS_NON_GTM_ID, GTAG_CONFIG_WITH_GTM, GTM_AND_GTAG, DATALAYER_RESET,
# NO_CONSENT_DEFAULT_IN_CODE, NO_INSTALL.
# MULTIPLE_GTM_LOADERS is reported per file, because a multi-page site carrying one
# loader in a shared layout is the expected shape and LOADER_IN_SEVERAL_FILES is
# only an info note.
#
# It reads source and template files only, skips dependency, build, and VCS
# folders, and never reads .env files. Exit codes: 0 scanned (even with no
# install), 2 bad arguments, 3 missing dependency (jq).
# Requires bash 3.2+, POSIX find/grep/sed/sort, and jq 1.6+.
set -euo pipefail

ROOT="."
while [ "$#" -gt 0 ]; do
  case $1 in
    --root)
      [ "$#" -ge 2 ] || { echo "gtm-detect: --root needs a value" >&2; exit 2; }
      ROOT=$2
      shift 2
      ;;
    -h | --help)
      awk 'NR > 1 && /^#/ { print; next } NR > 1 { exit }' "$0"
      exit 0
      ;;
    *)
      echo "gtm-detect: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

command -v jq >/dev/null 2>&1 || { echo "gtm-detect: jq is required" >&2; exit 3; }
[ -d "$ROOT" ] || { echo "gtm-detect: not a directory: $ROOT" >&2; exit 2; }
ROOT_LABEL=$ROOT
ROOT=$(CDPATH='' cd -- "$ROOT" && pwd)

HITS=$(mktemp "${TMPDIR:-/tmp}/gtm-detect.XXXXXX")
FW=$(mktemp "${TMPDIR:-/tmp}/gtm-detect-fw.XXXXXX")
trap 'rm -f "$HITS" "$FW"' EXIT

# Source and template files, skipping dependency, build, and VCS folders.
list_sources() {
  find "$ROOT" \( -name node_modules -o -name .git -o -name .hyper -o -name .next \
    -o -name .nuxt -o -name .output -o -name .svelte-kit -o -name .astro -o -name dist \
    -o -name build -o -name out -o -name coverage -o -name vendor -o -name .turbo \
    -o -name .vercel -o -name .wrangler \) -prune -o -type f \
    \( -name '*.html' -o -name '*.htm' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \
    -o -name '*.jsx' -o -name '*.ts' -o -name '*.mts' -o -name '*.tsx' -o -name '*.vue' \
    -o -name '*.svelte' -o -name '*.astro' -o -name '*.php' -o -name '*.liquid' \
    -o -name '*.erb' -o -name '*.hbs' -o -name '*.njk' -o -name '*.ejs' -o -name '*.twig' \
    -o -name '*.json' -o -name '*.toml' -o -name '*.yaml' -o -name '*.yml' -o -name '_headers' \
    -o -name '*.conf' \) -print 2>/dev/null | LC_ALL=C sort
}

rel() { printf '%s' "${1#"$ROOT"/}"; }

# grep_kind <kind> <extended-regex> [value-regex]
# Records one hit per matching line; with a value regex, one hit per match.
grep_kind() {
  local kind=$1 re=$2 vre=${3:-} f n line v
  while IFS= read -r f; do
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      n=${line%%:*}
      line=${line#*:}
      if [ -n "$vre" ]; then
        while IFS= read -r v; do
          [ -n "$v" ] && printf '%s\t%s\t%s\t%s\n' "$kind" "$v" "$(rel "$f")" "$n" >>"$HITS"
        done < <(printf '%s\n' "$line" | grep -oE "$vre" || true)
      else
        printf '%s\t%s\t%s\t%s\n' "$kind" "" "$(rel "$f")" "$n" >>"$HITS"
      fi
    done < <(grep -nE "$re" "$f" 2>/dev/null || true)
  done < <(list_sources)
}

grep_kind gtm-id 'GTM-[A-Z0-9]{4,10}' 'GTM-[A-Z0-9]{4,10}'
grep_kind gtm-loader 'googletagmanager\.com/gtm\.js'
grep_kind gtm-noscript 'googletagmanager\.com/ns\.html'
grep_kind gtmjs-non-gtm-id 'gtm\.js\?id=(G|AW|DC)-[A-Z0-9]{4,12}' '(G|AW|DC)-[A-Z0-9]{4,12}'
grep_kind gtag-config "gtag\\([[:space:]]*['\"]config['\"]"
grep_kind gtag-loader 'googletagmanager\.com/gtag/js'
grep_kind google-tag-id "(gtag\\(['\"]config['\"], *['\"]|[?&]id=|gaId=['\"{]*|measurementId['\"]?[:=] *['\"])(G|AW|DC|GT)-[A-Z0-9]{4,12}" '(G|AW|DC|GT)-[A-Z0-9]{4,12}'
grep_kind next-gtm-component '<GoogleTagManager[[:space:]>]'
grep_kind next-ga-component '<GoogleAnalytics[[:space:]>]'
grep_kind nuxt-scripts-gtm 'useScriptGoogleTagManager|googleTagManager[[:space:]]*:'
grep_kind datalayer-init 'dataLayer[[:space:]]*=[[:space:]]*(window\.)?dataLayer[[:space:]]*\|\|'
grep_kind datalayer-reset '(window\.)?dataLayer[[:space:]]*=[[:space:]]*\['
grep_kind consent-default "['\"]consent['\"],[[:space:]]*['\"]default['\"]|setDefaultConsentState"
grep_kind consent-update "['\"]consent['\"],[[:space:]]*['\"]update['\"]|updateConsentState"
grep_kind csp 'Content-Security-Policy|contentSecurityPolicy'
grep_kind partytown '@builder\.io/partytown|@qwik\.dev/partytown|@astrojs/partytown|type=["'"'"']text/partytown'

# Frameworks from manifests and layout files.
fw() { printf '%s\t%s\t%s\n' "$1" "$(rel "$2")" "$3" >>"$FW"; }
while IFS= read -r f; do
  for pair in 'next:"next"' 'nuxt:"nuxt"' 'sveltekit:"@sveltejs/kit"' 'astro:"astro"' \
    'tanstack-start:"@tanstack/react-start"' 'tanstack-start:"@tanstack/solid-start"' \
    'remix:"@remix-run/react"' 'react-router:"@react-router/dev"' 'gatsby:"gatsby"' \
    'vite:"vite"' 'angular:"@angular/core"' 'vue:"vue"' 'react:"react"'; do
    name=${pair%%:*}
    token=${pair#*:}
    if grep -qF "$token:" "$f" 2>/dev/null; then fw "$name" "$f" "$token:"; fi
  done
done < <(find "$ROOT" \( -name node_modules -o -name .git -o -name .hyper \) -prune -o -type f -name package.json -print 2>/dev/null | LC_ALL=C sort)
while IFS= read -r f; do
  case $f in
    */wp-config.php | */wp-config-sample.php) fw wordpress "$f" "wp-config" ;;
    */layout/theme.liquid) fw shopify-theme "$f" "layout/theme.liquid" ;;
    */index.html) fw static-html "$f" "index.html" ;;
  esac
done < <(find "$ROOT" \( -name node_modules -o -name .git -o -name .hyper -o -name dist -o -name build \) -prune -o -type f \
  \( -name wp-config.php -o -name wp-config-sample.php -o -path '*/layout/theme.liquid' -o -name index.html \) -print 2>/dev/null | LC_ALL=C sort)

jq -n --arg root "$ROOT_LABEL" --rawfile hits "$HITS" --rawfile fw "$FW" '
  def rows($t): $t | split("\n") | map(select(length > 0) | split("\t"));
  def sig: rows($hits) | map({kind: .[0], value: .[1], file: .[2], line: (.[3] | tonumber)})
    | unique_by([.kind, .file, .line, .value]) | sort_by(.file, .line, .kind, .value)
    | map(if .value == "" then del(.value) else . end);
  def frameworks: rows($fw) | map({framework: .[0], file: .[1], signal: .[2]})
    | group_by(.framework)
    | map({framework: .[0].framework, evidence: (map({file, signal}) | unique)});
  sig as $s
  | ([$s[] | select(.kind == "gtm-id") | .value] | unique) as $gtm
  | ([$s[] | select(.kind == "google-tag-id") | .value] | unique) as $gt
  | ([$s[] | select(.kind == "gtm-loader")] | length) as $loader
  | ([$s[] | select(.kind == "gtm-loader")] | group_by(.file) | map(select(length > 1))) as $loaderPerFile
  | ([$s[] | select(.kind == "next-gtm-component" or .kind == "nuxt-scripts-gtm")] | length) as $component
  | ([$s[] | select(.kind == "gtag-config")] | length) as $gtagConfig
  | ([$s[] | select(.kind == "gtag-loader" or .kind == "next-ga-component")] | length) as $gtag
  | {root: $root,
     frameworks: frameworks,
     signals: $s,
     containerIds: $gtm,
     googleTagIds: $gt,
     findings: ([
       (if ($gtm | length) > 1 then {severity: "warn", code: "MULTIPLE_CONTAINER_IDS",
          detail: "more than one GTM container ID is referenced: \($gtm | join(", "))"} else empty end),
       ($loaderPerFile[]
        | {severity: "warn", code: "MULTIPLE_GTM_LOADERS",
           detail: "\(.[0].file) loads the gtm.js loader \(length) times; one loader per container per page is the rule, so a second loader in the same file is a duplicate"}),
       (if $loader > 1 and ($loaderPerFile | length) == 0 then {severity: "info", code: "LOADER_IN_SEVERAL_FILES",
          detail: "the gtm.js loader appears in \($loader) files; that is expected for a multi-page site with a shared layout, so confirm each page carries one loader rather than treating the count as a finding"} else empty end),
       ($s[] | select(.kind == "gtmjs-non-gtm-id")
        | {severity: "error", code: "GTMJS_NON_GTM_ID",
           detail: "\(.file):\(.line) loads \(.value) through the gtm.js path; Google calls a non-GTM ID on gtm.js unsupported, use gtag/js for a G-/AW-/DC- ID or a GTM- container ID on gtm.js"}),
       (if ($loader + $component) > 0 and $gtagConfig > 0 then {severity: "warn", code: "GTAG_CONFIG_WITH_GTM",
          detail: "page code calls gtag(\"config\") next to GTM; the command is deprecated, gtm.js no longer waits for it, and it now surfaces as a gtag.config event that wildcard custom event triggers match"} else empty end),
       (if ($loader + $component) > 0 and $gtag > 0 then {severity: "warn", code: "GTM_AND_GTAG",
          detail: "GTM and a direct Google tag are both installed; a measurement ID configured in both sends duplicate hits"} else empty end),
       (if ([$s[] | select(.kind == "datalayer-reset")] | length) > 0 then {severity: "warn", code: "DATALAYER_RESET",
          detail: "dataLayer is assigned a new array; after GTM loads this breaks its dataLayer listener"} else empty end),
       (if ($loader + $component) > 0 and ([$s[] | select(.kind == "consent-default")] | length) == 0 then {severity: "info", code: "NO_CONSENT_DEFAULT_IN_CODE",
          detail: "no consent default in page code; confirm a Consent Initialization tag or CMP template sets it in the container"} else empty end),
       (if ($loader + $component + $gtag) == 0 then {severity: "info", code: "NO_INSTALL",
          detail: "no GTM or Google tag install was found"} else empty end)
     ])}'
