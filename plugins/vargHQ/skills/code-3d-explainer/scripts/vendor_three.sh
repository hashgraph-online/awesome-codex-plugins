#!/usr/bin/env bash
# vendor_three.sh: serve three.js from the project instead of the CDN, so renders work offline and never
# stall on a slow jsDelivr fetch (we lost a render to a DNS outage: the page waited for three.js forever).
#
#   bash scripts/vendor_three.sh <project-dir> [version]      # default: the version pinned in index.html
#
# Copies build/three.module.js + build/three.core.js and examples/jsm/{postprocessing,shaders} (~2.6 MB)
# into <project>/vendor/three/ (from the npm registry via `bun add`), then rewrites the import map in
# <project>/index.html to ./vendor/three/. Undo: restore the two jsDelivr lines in the import map.
set -euo pipefail
proj="${1:?usage: vendor_three.sh <project-dir> [version]}"; html="$proj/index.html"
ver="${2:-$(grep -o 'three@[0-9.]*' "$html" | head -1 | cut -d@ -f2)}"; [ -n "$ver" ] || { echo "no three@<version> in $html; pass a version" >&2; exit 1; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
( cd "$tmp" && echo '{}' > package.json && bun add "three@$ver" >/dev/null 2>&1 )
src="$tmp/node_modules/three"; dst="$proj/vendor/three"
mkdir -p "$dst/build" "$dst/examples/jsm"
cp "$src/build/three.module.js" "$src/build/three.core.js" "$dst/build/"
cp -R "$src/examples/jsm/postprocessing" "$src/examples/jsm/shaders" "$dst/examples/jsm/"
cp "$src/LICENSE" "$dst/LICENSE"
perl -0pi -e 's#"three": "[^"]*"#"three": "./vendor/three/build/three.module.js"#; s#"three/addons/": "[^"]*"#"three/addons/": "./vendor/three/examples/jsm/"#' "$html"
echo "three@$ver vendored to $dst ($(du -sh "$dst" | cut -f1)); import map in $html now points to ./vendor/three/"
