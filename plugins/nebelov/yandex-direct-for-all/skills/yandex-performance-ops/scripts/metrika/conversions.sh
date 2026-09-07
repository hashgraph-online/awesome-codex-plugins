#!/bin/sh
# Goal conversion report
# Usage: conversions.sh --counter <ID> --date1 YYYY-MM-DD [--date2 ...] [--group day|week|month]
#        [--goals 123,456] [--all-goals] [--device ...] [--source ...] [--attribution ...]
#        [--limit N] [--csv path] [--no-cache]
#
# By default shows only conversion_goals from cache/counter_<id>/config.json.
# Use --all-goals to show all goals, or --goals to specify goal IDs manually.

set -e
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config
parse_common_params "$@"
require_counter
require_dates

GOALS=""
ALL_GOALS=""

# Re-parse for goals-specific params (parse_common_params already consumed "$@",
# but it passes unknown args through, so we re-scan the original args)
_prev=""
for _arg in "$@"; do
    if [ "$_prev" = "--goals" ]; then
        GOALS="$_arg"
        _prev=""
        continue
    fi
    case "$_arg" in
        --goals)     _prev="--goals" ;;
        --all-goals) ALL_GOALS="1" ;;
        *)           _prev="" ;;
    esac
done

ATTRIBUTION="${ATTRIBUTION:-lastsign}"
COUNTER_DIR=$(cache_dir_for_counter "$COUNTER")
CONFIG_JSON="$COUNTER_DIR/config.json"

# Determine goal IDs
if [ -n "$GOALS" ]; then
    # Manual override
    GOAL_IDS="$GOALS"
elif [ -n "$ALL_GOALS" ]; then
    # All goals from cache
    if [ -f "$COUNTER_DIR/goals.tsv" ]; then
        GOAL_IDS=$(cut -f1 "$COUNTER_DIR/goals.tsv" | tr '\n' ',' | sed 's/,$//')
    else
        echo "Error: No cached goals. Run: goals.sh --counter $COUNTER" >&2
        exit 1
    fi
else
    # Default: conversion goals from config
    if [ -f "$CONFIG_JSON" ] && grep -q "conversion_goals" "$CONFIG_JSON" 2>/dev/null; then
        GOAL_IDS=$(grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]*' "$CONFIG_JSON" | sed 's/.*:[[:space:]]*//' | tr '\n' ',' | sed 's/,$//')
    else
        echo "Error: No conversion goals configured for counter $COUNTER." >&2
        echo "Run goals.sh --counter $COUNTER to see available goals," >&2
        echo "then save conversion goals to $CONFIG_JSON." >&2
        echo "Or use --all-goals or --goals <ids>." >&2
        exit 1
    fi
fi

# Build metrics string with goal IDs
# For each goal: visits, conversionRate, reaches
_metrics=""
_IFS="$IFS"
IFS=","
for _gid in $GOAL_IDS; do
    _gid=$(echo "$_gid" | tr -d ' ')
    [ -z "$_gid" ] && continue
    if [ -n "$_metrics" ]; then
        _metrics="${_metrics},"
    fi
    _metrics="${_metrics}ym:s:goal${_gid}visits,ym:s:goal${_gid}reaches,ym:s:goal${_gid}conversionRate"
done
IFS="$_IFS"

if [ -z "$_metrics" ]; then
    echo "Error: No valid goal IDs found." >&2
    exit 1
fi

DIMENSIONS="ym:s:${ATTRIBUTION}TrafficSource"

# Cache key
_params_str="conv_${COUNTER}_${DATE1}_${DATE2}_${GROUP}_${GOAL_IDS}_${DEVICE}_${SOURCE}_${ATTRIBUTION}"
_hash=$(cache_key "$_params_str")
CACHE_FILE="$COUNTER_DIR/reports/conversions_${DATE1}_${DATE2}_${_hash}.csv"

# Skip cache if date2 is today (data still accumulating)
if date_is_today "$DATE2"; then
    NO_CACHE="1"
fi

# Check cache
if [ -z "$NO_CACHE" ] && [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ]; then
    echo "Conversions for counter $COUNTER ($DATE1 — $DATE2), goals: $GOAL_IDS"
    print_csv_head "$CACHE_FILE" 30
    [ -n "$CSV_OUT" ] && cp "$CACHE_FILE" "$CSV_OUT" && echo "Copied to: $CSV_OUT"
    exit 0
fi

# Build API path
if [ -n "$GROUP" ]; then
    API_PATH="/stat/v1/data/bytime.csv"
else
    API_PATH="/stat/v1/data.csv"
fi

echo "Fetching conversions for counter $COUNTER, goals: $GOAL_IDS..." >&2

TMPFILE="${METRIKA_TMPDIR}/metrika_conv_$$.csv"
trap 'rm -f "$TMPFILE"' EXIT

metrika_get_csv "$API_PATH" "$TMPFILE" \
    --data-urlencode "ids=$COUNTER" \
    --data-urlencode "date1=$DATE1" \
    --data-urlencode "date2=$DATE2" \
    --data-urlencode "metrics=$_metrics" \
    --data-urlencode "dimensions=$DIMENSIONS" \
    --data-urlencode "accuracy=1" \
    --data-urlencode "filters=$FILTERS" \
    ${GROUP:+--data-urlencode "group=$GROUP"} \
    ${LIMIT:+--data-urlencode "limit=$LIMIT"}

cp "$TMPFILE" "$CACHE_FILE"

echo "Conversions for counter $COUNTER ($DATE1 — $DATE2), goals: $GOAL_IDS"
print_csv_head "$CACHE_FILE" 30

if [ -n "$CSV_OUT" ]; then
    cp "$CACHE_FILE" "$CSV_OUT"
    echo "Exported to: $CSV_OUT"
fi
