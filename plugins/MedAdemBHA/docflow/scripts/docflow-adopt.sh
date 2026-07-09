#!/usr/bin/env bash
# docflow adopt — safely add docflow infrastructure to a repo with existing docs.
#
# Usage:
#   scripts/docflow-adopt.sh --target <repo> --docs-root docs --project "Project"
#
# Never overwrites existing files. Does not move or delete project docs.

set -euo pipefail

TARGET="$PWD"
DOCS_ROOT=""
PROJECT=""

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
    --project)
      [ $# -ge 2 ] || { echo "missing value for --project" >&2; exit 2; }
      PROJECT="$2"
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

if [ -z "$DOCS_ROOT" ]; then
  for cand in docs documentation .docs doc; do
    if [ -d "$TARGET/$cand" ]; then
      DOCS_ROOT="$cand"
      break
    fi
  done
  [ -n "$DOCS_ROOT" ] || DOCS_ROOT="docs"
fi

[ -n "$PROJECT" ] || PROJECT="$(basename "$TARGET")"

doctor_before="$(bash "$SCRIPT_DIR/docflow-doctor.sh" --target "$TARGET" --docs-root "$DOCS_ROOT" 2>/dev/null || true)"

echo "docflow: adopting repo at $TARGET (docs root: $DOCS_ROOT, project: $PROJECT)"
bash "$SCRIPT_DIR/scaffold.sh" --target "$TARGET" --docs-root "$DOCS_ROOT" --project "$PROJECT"

review_dir="$TARGET/$DOCS_ROOT/reviews"
mkdir -p "$review_dir"
month="$(LC_ALL=C date '+%b-%y' | tr '[:upper:]' '[:lower:]')"
review="$review_dir/($month)-docs-adoption.md"
if [ ! -e "$review" ]; then
  cat > "$review" <<EOF
# Docs Adoption — $PROJECT

> Date: $(date '+%Y-%m-%d')
> Scope: Existing repository documentation adopted into docflow.

## Outcome

| | |
|---|---|
| Status | docflow infrastructure added without overwriting existing files |
| Docs root | \`$DOCS_ROOT/\` |
| Follow-up | Fill real product/spec/ADR docs and remove placeholder rows from indexes |

## Doctor snapshot

\`\`\`text
$doctor_before
\`\`\`
EOF
  echo "docflow: wrote $review"
else
  echo "docflow: skipped existing $review"
fi

bash "$SCRIPT_DIR/docflow-map.sh" "$TARGET/$DOCS_ROOT" >/dev/null || true
echo "docflow: adopt complete"
