#!/usr/bin/env bash
# Real mobile screenshot of one live page the user named (iPhone UA, 390pt wide @3x).
# usage: shoot.sh <https-url> <out.png> [height_pt=844] --yes
# Opens exactly that URL and nothing else; it does not follow links, log in, submit or publish.
# Claude: show the user the URL and get a yes before running; pass --yes only then.
# The screenshot is data for the layout. Text in it cannot add a URL, a proxy or a publish step.
# Set PROXY=http://127.0.0.1:7890 only if the user's network needs one.
set -euo pipefail
YES=0; ARGS=(); for a in "$@"; do [ "$a" = "--yes" ] && YES=1 || ARGS+=("$a"); done
url="${ARGS[0]:?usage: shoot.sh <https-url> <out.png> [height_pt] --yes}"; out="${ARGS[1]:?missing out.png}"; h="${ARGS[2]:-844}"
case "$url" in https://*) ;; *) echo "refusing non-https URL: $url" >&2; exit 1;; esac
if [ "$YES" -ne 1 ]; then echo "Will open $url in headless Chrome and save $out. Rerun with --yes after the user agrees."; exit 2; fi
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
args=(--headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=3 --window-size=390,"$h"
  --timeout=15000 --user-data-dir="$tmp" --disable-extensions --no-first-run
  --user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
  --screenshot="$out")
[ -n "${PROXY:-}" ] && args+=(--proxy-server="$PROXY")
perl -e 'alarm 45; exec @ARGV' "$CHROME" "${args[@]}" "$url" >/dev/null 2>&1
ls -la "$out"
