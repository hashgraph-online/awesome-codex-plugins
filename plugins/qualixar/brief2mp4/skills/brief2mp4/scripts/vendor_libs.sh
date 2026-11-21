#!/usr/bin/env bash
# vendor_libs.sh: copy pinned GSAP, three.js and web fonts into a project's vendor/ folder, so a
# render never touches the network (same pixels every run, works offline).
#
#   vendor_libs.sh PROJECT_DIR                         # GSAP only
#   vendor_libs.sh PROJECT_DIR --three                 # GSAP + three.js
#   vendor_libs.sh PROJECT_DIR --fonts inter,space-grotesk
#
# Writes PROJECT_DIR/vendor/gsap.min.js, vendor/three.module.js (with --three) and
# vendor/fonts/<family>-<weight>.woff2 plus vendor/fonts/fonts.css (with --fonts; weights 400 and 700,
# latin subset). Load them with <script src="vendor/gsap.min.js">, an import map pointing "three" at
# ./vendor/three.module.js, and <link rel="stylesheet" href="vendor/fonts/fonts.css">.
# Needs npm (it ships with Node.js). Safe to run again.
set -euo pipefail

GSAP_VERSION="3.15.0"
THREE_VERSION="0.170.0"
FONT_VERSION="5.3.0"

DIR="${1:-}"; [[ -n "$DIR" ]] || { echo "usage: vendor_libs.sh PROJECT_DIR [--three] [--fonts a,b]" >&2; exit 2; }
shift
THREE=0 FONTS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --three) THREE=1; shift ;;
    --fonts) [[ -n "${2:-}" ]] || { echo "vendor_libs.sh: --fonts needs a list, e.g. inter,space-grotesk" >&2; exit 2; }; FONTS="$2"; shift 2 ;;
    *) echo "vendor_libs.sh: unknown option $1" >&2; exit 2 ;;
  esac
done
command -v npm >/dev/null 2>&1 || { echo "vendor_libs.sh: npm not found; install Node.js 22+" >&2; exit 1; }

mkdir -p "$DIR/vendor"
VENDOR="$(cd "$DIR/vendor" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fetch() {  # fetch <package@version> -> prints the unpacked package folder
  local tgz
  tgz="$(cd "$WORK" && npm pack "$1" --silent 2>/dev/null | tail -1)"
  mkdir -p "$WORK/${tgz%.tgz}"
  tar xzf "$WORK/$tgz" -C "$WORK/${tgz%.tgz}"
  echo "$WORK/${tgz%.tgz}/package"
}

pkg="$(fetch "gsap@$GSAP_VERSION")"
cp "$pkg/dist/gsap.min.js" "$VENDOR/gsap.min.js"
echo "vendor: gsap $GSAP_VERSION -> vendor/gsap.min.js"

if [[ "$THREE" == 1 ]]; then
  pkg="$(fetch "three@$THREE_VERSION")"
  cp "$pkg/build/three.module.js" "$VENDOR/three.module.js"
  echo "vendor: three $THREE_VERSION -> vendor/three.module.js"
fi

if [[ -n "$FONTS" ]]; then
  mkdir -p "$VENDOR/fonts"
  : > "$VENDOR/fonts/fonts.css"
  for fam in ${FONTS//,/ }; do
    pkg="$(fetch "@fontsource/$fam@$FONT_VERSION")"
    name="$(sed -n 's/.*"family": *"\([^"]*\)".*/\1/p' "$pkg/metadata.json" 2>/dev/null | head -1)"
    [[ -f "$pkg/LICENSE" ]] && cp "$pkg/LICENSE" "$VENDOR/fonts/LICENSE-$fam.txt"   # fonts are OFL: ship the licence
    [[ -n "$name" ]] || name="$fam"
    for w in 400 700; do
      src="$pkg/files/$fam-latin-$w-normal.woff2"
      if [[ -f "$src" ]]; then
        cp "$src" "$VENDOR/fonts/$fam-$w.woff2"
        printf '@font-face{font-family:"%s";font-weight:%s;font-style:normal;font-display:block;src:url("%s-%s.woff2") format("woff2")}\n' \
          "$name" "$w" "$fam" "$w" >> "$VENDOR/fonts/fonts.css"
      fi
    done
    echo "vendor: font $name ($fam) -> vendor/fonts/"
  done
fi
