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

# Collect `/// @lgpd:...` annotations (standalone blocks and trailing field
# comments), then flush them onto the next model/field line. A buffer avoids
# leaking a preceding annotation onto an unrelated field.
# The trailing-comment locator ignores `///` sequences inside quoted strings
# (e.g. @default("file:///private")), including escaped quotes.
awk '
  function annot(s,   i, c, n, inq, esc, dq, bs, t) {
    dq = sprintf("%c", 34)
    bs = sprintf("%c", 92)
    n = length(s)
    inq = 0
    esc = 0
    for (i = 1; i <= n; i++) {
      c = substr(s, i, 1)
      if (inq) {
        if (esc) { esc = 0; continue }
        if (c == bs) { esc = 1; continue }
        if (c == dq) { inq = 0 }
        continue
      }
      if (c == dq) { inq = 1; continue }
      if (c == "/" && substr(s, i, 3) == "///") {
        t = substr(s, i)
        if (substr(t, 4) ~ /^[[:space:]]*@lgpd:/) return t
        return ""
      }
    }
    return ""
  }
  function flush(field,   j) {
    if (field == "") return
    for (j = 1; j <= np; j++) print "  - " field ": " pending[j]
    if (inline != "") print "  - " field ": " inline
    np = 0
    inline = ""
  }
  {
    line = $0
    sub(/^[[:space:]]*/, "", line)
    if (substr(line, 1, 3) == "///" && substr(line, 4) ~ /^[[:space:]]*@lgpd:/) {
      pending[++np] = line
      next
    }
    if (line ~ /^model[[:space:]]/) {
      model = $2
      print ""
      print "## Model: " model
      for (j = 1; j <= np; j++) print "- " pending[j]
      np = 0
      next
    }
    if ($0 ~ /^[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]+[A-Z]/) {
      inline = annot($0)
      flush($1)
      next
    }
    if (substr(line, 1, 2) == "//") { next }
    if (line == "") { next }
    np = 0
    inline = ""
  }
' "$SCHEMA"
