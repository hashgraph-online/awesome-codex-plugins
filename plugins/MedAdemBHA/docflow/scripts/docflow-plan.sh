#!/usr/bin/env bash
# docflow plan generator — turn real repo signal into a roadmap DRAFT.
# Signal: TODO/FIXME/HACK markers (backlog candidates) + recent git churn
# (where work is happening). Output is a draft the dev sorts into horizons.
#
# Usage: docflow-plan.sh [--target .] [--docs-root docs] [--days 30] [--stdout] [--force]

set -euo pipefail

TARGET="$PWD"; DOCS_ROOT="docs"; DAYS=30; TO_STDOUT=0; FORCE=0
require_value() {
  opt="$1"
  value="${2-}"
  case "$value" in
    ''|--*)
      echo "missing value for $opt" >&2
      exit 1
      ;;
  esac
}
while [ $# -gt 0 ]; do
  case "$1" in
    --target)    require_value "$1" "${2-}"; TARGET="$2";    shift 2 ;;
    --docs-root) require_value "$1" "${2-}"; DOCS_ROOT="$2"; shift 2 ;;
    --days)      require_value "$1" "${2-}"; DAYS="$2";      shift 2 ;;
    --stdout)    TO_STDOUT=1;    shift ;;
    --force)     FORCE=1;        shift ;;
    -h|--help)   grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done
cd "$TARGET"
MON="$(date +%b | tr '[:upper:]' '[:lower:]')-$(date +%y)"
SCAN="${SCAN_DIR:-.}"
EXCL='node_modules|\.git|dist|build|vendor|\.next|coverage'

markers() {
  grep -rnoE '(TODO|FIXME|HACK|XXX)[: ].{0,90}' "$SCAN" 2>/dev/null \
    | grep -vE "$EXCL" | head -40
}

churn() {
  command -v git >/dev/null && git rev-parse --git-dir >/dev/null 2>&1 || return 0
  git log --since="$DAYS days ago" --name-only --pretty=format: 2>/dev/null \
    | grep -vE "^$|$EXCL" | sed -E 's#^([^/]+/[^/]+)/.*#\1#' \
    | LC_ALL=C sort | uniq -c | sort -rn | head -12
}

emit() {
cat <<EOF
<!-- docflow plan (auto-draft, $MON). From TODO/FIXME + git churn — sort into critical/now/next/later. -->
# Roadmap candidates — $MON

> Auto-generated draft. Triage each line into \`plans/upcoming/{critical,now,next,later}.md\`, then delete this file.

## Backlog candidates (code markers)

| Marker | Location | Note |
|--------|----------|------|
$(markers | sed -E "s#^([^:]+):([0-9]+):[[:space:]]*(TODO|FIXME|HACK|XXX)[: ]*(.*)#| \3 | \`\1:\2\` | \4 |#")

## Where work is happening (last $DAYS days)

| Area | Commits touching it |
|------|---------------------|
$(churn | awk '{print "| `"$2"` | "$1" |"}')

## Suggested triage
- FIXME/HACK in hot areas (top of churn) → likely **critical** or **now**.
- TODO in cold areas → **later**, or delete if stale.
EOF
}

if [ "$TO_STDOUT" = 1 ]; then emit; exit 0; fi
OUT="$TARGET/$DOCS_ROOT/plans/upcoming/($MON)-candidates.md"
mkdir -p "$(dirname "$OUT")"
if [ -e "$OUT" ] && [ "$FORCE" != 1 ]; then
  echo "exists, not overwriting: $OUT (use --force to replace)" >&2
  exit 0
fi
emit > "$OUT"
echo "docflow: wrote $OUT  (triage into horizons, then delete)"
