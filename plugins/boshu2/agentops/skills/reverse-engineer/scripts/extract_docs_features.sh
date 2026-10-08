#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: extract_docs_features.sh <paths.txt> <docs_features_prefix>" >&2
  exit 2
fi

PATHS_TXT="$1"
PREFIX_RAW="$2"

# Normalize prefix: "docs/features/" -> "/docs/features"
PREFIX="/${PREFIX_RAW#/}"
PREFIX="${PREFIX%/}"

python3 - "$PATHS_TXT" "$PREFIX" <<'PY'
import sys
from pathlib import Path

paths_txt = Path(sys.argv[1])
prefix = sys.argv[2]

out = set()
for line in paths_txt.read_text(encoding="utf-8", errors="replace").splitlines():
    p = line.strip()
    if not p:
        continue
    if not p.startswith("/"):
        p = "/" + p
    if p.startswith(prefix + "/") or p == prefix:
        # Keep the path *under* docs/features as a slug, without leading slash.
        slug = p.lstrip("/")
        out.add(slug)

for s in sorted(out):
    print(s)
PY

