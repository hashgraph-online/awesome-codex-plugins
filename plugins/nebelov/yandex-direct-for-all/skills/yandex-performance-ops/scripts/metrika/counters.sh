#!/bin/sh
# List Yandex Metrika counters with cache + TSV index
# Usage: counters.sh [--no-cache] [--search <text>]

set -e
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

SEARCH=""
NO_CACHE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --no-cache) NO_CACHE="1"; shift ;;
        --search)   SEARCH="$2"; shift 2 ;;
        *)          shift ;;
    esac
done

CACHE_JSON="$CACHE_DIR/counters.json"
CACHE_TSV="$CACHE_DIR/counters.tsv"

# Try cache first
if [ -z "$NO_CACHE" ] && [ -f "$CACHE_TSV" ] && [ -s "$CACHE_TSV" ]; then
    if [ -n "$SEARCH" ]; then
        echo "ID	Name	Site"
        grep -i "$SEARCH" "$CACHE_TSV" || echo "(no matches for '$SEARCH')"
    else
        echo "ID	Name	Site"
        cat "$CACHE_TSV"
    fi
    echo ""
    echo "(cached: $CACHE_TSV)"
    exit 0
fi

# Fetch from API
echo "Fetching counters from API..." >&2

TMPFILE="${METRIKA_TMPDIR}/metrika_counters_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

metrika_mgmt_get "/management/v1/counters" \
    --data-urlencode "per_page=1000" \
    > "$TMPFILE"

# Save raw JSON to cache
mkdir -p "$CACHE_DIR"
cp "$TMPFILE" "$CACHE_JSON"

# Generate TSV index: id<TAB>name<TAB>site
# Parse flat JSON array — each counter has "id", "name", "site" fields
# We extract them line by line using grep/sed, sanitize tabs/newlines
{
    # Extract id/name/site blocks from the counters array
    tr '{}' '\n' < "$TMPFILE" | while IFS= read -r _line; do
        _id=$(echo "$_line" | grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
        _name=$(echo "$_line" | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' | tr '	\n' '  ')
        _site=$(echo "$_line" | grep -o '"site"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' | tr '	\n' '  ')

        if [ -n "$_id" ]; then
            printf '%s\t%s\t%s\n' "$_id" "$_name" "$_site"
        fi
    done
} > "$CACHE_TSV"

# Output
echo "ID	Name	Site"
if [ -n "$SEARCH" ]; then
    grep -i "$SEARCH" "$CACHE_TSV" || echo "(no matches for '$SEARCH')"
else
    print_csv_head "$CACHE_TSV" 30
fi
echo ""
echo "Total counters: $(wc -l < "$CACHE_TSV" | tr -d ' ')"
echo "Cached: $CACHE_TSV (use grep/rg to search)"
