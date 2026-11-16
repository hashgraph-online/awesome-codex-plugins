#!/usr/bin/env bash
# Extract @lgpd: annotations from prisma/schema.prisma to seed data-map.md
# Usage: ./extract-prisma-annotations.sh prisma/schema.prisma > .lgpd/data-map-draft.md

set -euo pipefail

SCHEMA="${1:-prisma/schema.prisma}"

if [[ ! -f "$SCHEMA" ]]; then
  echo "Schema not found: $SCHEMA" >&2
  exit 1
fi

echo "# Data Map Draft — extracted from $SCHEMA"
echo
echo "**Generated**: $(date -Iseconds)"
echo

# Match `/// @lgpd:...` lines preceding a model/field
awk '
  /^\/\/\/[[:space:]]*@lgpd:/ { annot[NR]=$0 }
  /^model[[:space:]]/ {
    model=$2
    print "\n## Model: " model
    for (i=NR-5; i<NR; i++) if (i in annot) print "- " annot[i]
  }
  /^[[:space:]]+[a-zA-Z_]+[[:space:]]+[A-Z]/ {
    field=$1
    for (i=NR-2; i<NR; i++) if (i in annot) print "  - " field ": " annot[i]
  }
' "$SCHEMA"
