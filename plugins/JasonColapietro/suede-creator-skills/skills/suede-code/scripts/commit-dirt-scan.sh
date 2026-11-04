#!/usr/bin/env bash
# commit-dirt-scan.sh — Commit Dirt Score, executed instead of eyeballed.
#
# Scans the added (`+`) lines of a diff for content that should never reach git
# history and prints one verdict line per category, then an overall rating.
#
# Usage:
#   scripts/commit-dirt-scan.sh                 # scans `git diff HEAD`
#   scripts/commit-dirt-scan.sh main...HEAD     # scans that range
#   git diff main...HEAD | scripts/commit-dirt-scan.sh -
#
# Read-only and advisory: it never stages, reverts, writes, or fails the caller's
# command. It always exits 0 — the verdict is reported, never enforced.

set -uo pipefail

if [ "${1:-}" = "-" ]; then
  DIFF=$(cat)
elif [ "$#" -gt 0 ]; then
  DIFF=$(git diff "$@" 2>/dev/null)
else
  DIFF=$(git diff HEAD 2>/dev/null)
fi

if [ -z "$DIFF" ]; then
  echo "COMMIT DIRT SCORE: no diff content to scan (empty range or not a git repo)."
  exit 0
fi

ADDED=$(printf '%s\n' "$DIFF" | grep -E '^\+' | grep -Ev '^\+\+\+')
PATHS=$(printf '%s\n' "$DIFF" | grep -E '^\+\+\+ b/' | sed 's|^+++ b/||')
DIRTY=0
SUSPECT=0

# $1 = label, $2 = pattern, $3 = corpus, $4 = severity when hit (dirty|suspicious)
check() {
  local label="$1" pattern="$2" corpus="$3" sev="$4" hit
  hit=$(printf '%s\n' "$corpus" | grep -Ein "$pattern" | head -3)
  if [ -n "$hit" ]; then
    printf '%-26s %s — %s\n' "$label" "$sev" "$(printf '%s' "$hit" | tr '\n' ';' | cut -c1-160)"
    [ "$sev" = "dirty" ] && DIRTY=1 || SUSPECT=1
  else
    printf '%-26s clean — none\n' "$label"
  fi
}

echo "COMMIT DIRT SCORE"
check "Secrets / credentials:" '(sk_[a-z0-9]|pk_live|ghp_|gho_|xox[baprs]-|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|(password|passwd|secret|api_?key|token)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{8,})' "$ADDED" suspicious
check "Debug artifacts:" '(console\.(log|debug)|[^a-z]debugger[^a-z]|binding\.pry|byebug|var_dump\(|pprint\(|TODO: ?remove|FIXME: ?before merge|HACK:)' "$ADDED" suspicious
check "Conflict markers:" '^\+(<{7}|={7}|>{7}|\|{7})' "$(printf '%s\n' "$DIFF" | grep -E '^\+')" dirty
check "Accidentally staged:" '(^|/)(node_modules|\.next|dist|build|__pycache__)/|\.(pyc|DS_Store|log|sqlite|db)$' "$PATHS" dirty
check "WIP breadcrumbs:" '(\[WIP\]|DO NOT MERGE|TEMP:|SKIP CI|lorem ipsum|[^a-z]asdf[^a-z])' "$ADDED" suspicious
check "Exposed internals:" '(https?://(localhost|127\.0\.0\.1|10\.[0-9]+\.|192\.168\.)|https?://[a-z0-9.-]*(staging|internal)[a-z0-9.-]*/|[a-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook)\.com)' "$ADDED" suspicious

# Oversized or binary blobs: binary markers in the diff, plus changed files >500 KB.
BIG=$(printf '%s\n' "$DIFF" | grep -E '^(Binary files|GIT binary patch)' | head -2)
while IFS= read -r p; do
  [ -f "$p" ] || continue
  sz=$(wc -c < "$p" 2>/dev/null | tr -d ' ')
  [ -n "$sz" ] && [ "$sz" -gt 512000 ] && BIG="$BIG${BIG:+; }$p (${sz}B)"
done <<< "$PATHS"
if [ -n "$BIG" ]; then
  printf '%-26s dirty — %s\n' "Oversized / binary:" "$(printf '%s' "$BIG" | tr '\n' ';' | cut -c1-160)"
  DIRTY=1
else
  printf '%-26s clean — none\n' "Oversized / binary:"
fi

if [ "$DIRTY" = 1 ]; then
  echo "Overall dirt rating:       DIRTY"
elif [ "$SUSPECT" = 1 ]; then
  echo "Overall dirt rating:       SUSPICIOUS"
else
  echo "Overall dirt rating:       CLEAN"
fi
echo "(Advisory. Confirm each hit against the diff before reporting it as a finding.)"
exit 0
