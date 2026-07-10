#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: extract_sitemap_paths.sh <sitemap.xml>" >&2
  exit 2
fi

SITEMAP_XML="$1"

python3 - "$SITEMAP_XML" <<'PY'
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

src = Path(sys.argv[1])
data = src.read_text(encoding="utf-8", errors="replace")
root = ET.fromstring(data)

paths = set()
for loc in root.iter():
    if loc.tag.endswith("loc") and loc.text:
        u = loc.text.strip()
        p = urllib.parse.urlparse(u)
        path = p.path or ""
        if not path:
            continue
        # Normalize: ensure leading slash, drop trailing slash except root.
        if not path.startswith("/"):
            path = "/" + path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        paths.add(path)

for p in sorted(paths):
    print(p)
PY

