#!/usr/bin/env bash
# docflow repair — safe maintenance for an existing docflow repo.
#
# Usage:
#   scripts/docflow-repair.sh --target <repo> [--docs-root docs]
#
# Regenerates INDEX.md, installs missing helper scripts, and reports links/placeholders.

set -euo pipefail

TARGET="$PWD"
DOCS_ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ $# -ge 2 ] || { echo "missing value for --target" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --docs-root)
      [ $# -ge 2 ] || { echo "missing value for --docs-root" >&2; exit 2; }
      DOCS_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
[ -d "$TARGET" ] || { echo "target not found: $TARGET" >&2; exit 2; }

json_val() {
  key="$1"
  cfg="$2"
  grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$cfg" 2>/dev/null \
    | head -1 | sed -E "s/.*:[[:space:]]*\"([^\"]*)\".*/\1/"
}

if [ -z "$DOCS_ROOT" ] && [ -f "$TARGET/docflow.json" ]; then
  DOCS_ROOT="$(json_val docsRoot "$TARGET/docflow.json")"
fi
if [ -z "$DOCS_ROOT" ]; then
  for cand in docs documentation .docs doc; do
    if [ -d "$TARGET/$cand" ]; then
      DOCS_ROOT="$cand"
      break
    fi
  done
fi
[ -n "$DOCS_ROOT" ] || DOCS_ROOT="docs"

DR="$TARGET/$DOCS_ROOT"
echo "docflow: repairing $TARGET (docs root: $DOCS_ROOT)"
if [ ! -d "$DR" ]; then
  echo "docflow: no docs root found at $DR"
  exit 0
fi

mkdir -p "$TARGET/scripts"
for helper in check-links.sh docflow-check.sh docflow-map.sh docflow-validate.sh; do
  src="$SCRIPT_DIR/$helper"
  out="$TARGET/scripts/$helper"
  [ -f "$src" ] || continue
  if [ ! -e "$out" ]; then
    cp "$src" "$out"
    chmod +x "$out"
    echo "docflow: installed $out"
  fi
done

bash "$SCRIPT_DIR/docflow-map.sh" "$DR"

echo
echo "Link check"
if ! bash "$SCRIPT_DIR/check-links.sh" "$DR"; then
  echo "docflow: broken links found"
else
  echo "docflow: links ok"
fi

echo
echo "Placeholders"
placeholder_files="$(grep -RIlE '<(PROJECT|YYYY-MM-DD|Month YEAR|topic|item|description|title|name|scope|owner|status|hash|feature|module)>' "$DR" 2>/dev/null | grep -vE '/references/|/NAMING\.md$' || true)"
if [ -n "$placeholder_files" ]; then
  printf '%s\n' "$placeholder_files" | sed "s#^$TARGET/##" | head -40
else
  echo "none"
fi

echo "docflow: repair complete"
