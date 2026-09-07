#!/bin/sh
# List goals for a Yandex Metrika counter with cache + TSV index
# Usage: goals.sh --counter <ID> [--no-cache]

set -e
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config

COUNTER=""
NO_CACHE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --counter)  COUNTER="$2"; shift 2 ;;
        --no-cache) NO_CACHE="1"; shift ;;
        *)          shift ;;
    esac
done

if [ -z "$COUNTER" ]; then
    echo "Error: --counter <ID> is required." >&2
    echo "Usage: goals.sh --counter <ID> [--no-cache]" >&2
    exit 1
fi

COUNTER_DIR=$(cache_dir_for_counter "$COUNTER")
CACHE_JSON="$COUNTER_DIR/goals.json"
CACHE_TSV="$COUNTER_DIR/goals.tsv"

# Try cache first
if [ -z "$NO_CACHE" ] && [ -f "$CACHE_TSV" ] && [ -s "$CACHE_TSV" ]; then
    echo "Goals for counter $COUNTER:"
    echo "ID	Name	Type"
    cat "$CACHE_TSV"
    echo ""
    echo "(cached: $CACHE_TSV)"
    exit 0
fi

# Fetch from API
echo "Fetching goals for counter $COUNTER..." >&2

TMPFILE="${METRIKA_TMPDIR}/metrika_goals_$$.json"
trap 'rm -f "$TMPFILE"' EXIT

metrika_mgmt_get "/management/v1/counter/$COUNTER/goals" > "$TMPFILE"

# Save raw JSON
cp "$TMPFILE" "$CACHE_JSON"

# Generate TSV index: id<TAB>name<TAB>type
{
    tr '{}' '\n' < "$TMPFILE" | while IFS= read -r _line; do
        _id=$(echo "$_line" | grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
        _name=$(echo "$_line" | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//' | tr '	\n' '  ')
        _type=$(echo "$_line" | grep -o '"type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//')

        if [ -n "$_id" ] && [ -n "$_name" ]; then
            printf '%s\t%s\t%s\n' "$_id" "$_name" "$_type"
        fi
    done
} > "$CACHE_TSV"

# Output
echo "Goals for counter $COUNTER:"
echo "ID	Name	Type"
cat "$CACHE_TSV"
echo ""
_total=$(wc -l < "$CACHE_TSV" | tr -d ' ')
echo "Total goals: $_total"
echo "Cached: $CACHE_TSV"
