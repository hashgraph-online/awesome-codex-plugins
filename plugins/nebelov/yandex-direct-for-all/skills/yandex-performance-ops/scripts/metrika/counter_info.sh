#!/bin/sh
# Get counter metadata (name, site, create_time) with permanent cache
# Usage: counter_info.sh --counter <ID> [--no-cache]
# Also stores/reads conversion_goals in config.json

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
    exit 1
fi

COUNTER_DIR=$(cache_dir_for_counter "$COUNTER")
CACHE_JSON="$COUNTER_DIR/info.json"
CONFIG_JSON="$COUNTER_DIR/config.json"

# Try cache first (permanent — counter metadata rarely changes)
if [ -z "$NO_CACHE" ] && [ -f "$CACHE_JSON" ] && [ -s "$CACHE_JSON" ]; then
    _info=$(cat "$CACHE_JSON")
else
    echo "Fetching counter $COUNTER info..." >&2

    TMPFILE="${METRIKA_TMPDIR}/metrika_info_$$.json"
    trap 'rm -f "$TMPFILE"' EXIT

    metrika_mgmt_get "/management/v1/counter/$COUNTER" > "$TMPFILE"

    cp "$TMPFILE" "$CACHE_JSON"
    _info=$(cat "$TMPFILE")
fi

# Extract fields
_name=$(json_extract_field "$_info" "name")
_site=$(json_extract_field "$_info" "site2" || true)
[ -z "$_site" ] && _site=$(json_extract_field "$_info" "site" || true)
_create=$(json_extract_field "$_info" "create_time" || true)
_owner=$(json_extract_field "$_info" "owner_login" || true)
_code_status=$(json_extract_field "$_info" "code_status" || true)

echo "Counter: $COUNTER"
echo "Name: $_name"
echo "Site: $_site"
echo "Created: $_create"
echo "Owner: $_owner"
echo "Code status: $_code_status"

# Show config if exists
if [ -f "$CONFIG_JSON" ]; then
    echo ""
    echo "--- Saved config ---"
    _attr=$(json_extract_field "$(cat "$CONFIG_JSON")" "attribution")
    [ -n "$_attr" ] && echo "Attribution: $_attr"

    # Show conversion goals
    if grep -q "conversion_goals" "$CONFIG_JSON" 2>/dev/null; then
        echo "Conversion goals:"
        grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]*' "$CONFIG_JSON" | sed 's/.*:[[:space:]]*/  - /'
    fi
fi

echo ""
echo "(cached: $CACHE_JSON)"
if [ -f "$CONFIG_JSON" ]; then echo "(config: $CONFIG_JSON)"; fi
