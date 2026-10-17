#!/bin/sh
# Traffic distribution by source
# Usage: traffic_summary.sh --counter <ID> --date1 YYYY-MM-DD [--date2 ...] [--group day|week|month]
#        [--device desktop|mobile|tablet] [--source organic|ad|referral|direct]
#        [--attribution lastsign|last|first] [--limit N] [--csv path] [--no-cache]

set -e
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/common.sh"
load_config
parse_common_params "$@"
require_counter
require_dates

ATTRIBUTION="${ATTRIBUTION:-lastsign}"

METRICS="ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds"
DIMENSIONS="ym:s:${ATTRIBUTION}TrafficSource"

# Cache key
_params_str="traffic_${COUNTER}_${DATE1}_${DATE2}_${GROUP}_${DEVICE}_${SOURCE}_${ATTRIBUTION}_${LIMIT}"
_hash=$(cache_key "$_params_str")
COUNTER_DIR=$(cache_dir_for_counter "$COUNTER")
CACHE_FILE="$COUNTER_DIR/reports/traffic_${DATE1}_${DATE2}_${_hash}.csv"

# Skip cache if date2 is today (data still accumulating)
if date_is_today "$DATE2"; then
    NO_CACHE="1"
fi

# Check cache
if [ -z "$NO_CACHE" ] && [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ]; then
    echo "Traffic summary for counter $COUNTER ($DATE1 — $DATE2):"
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

# Fetch
echo "Fetching traffic summary for counter $COUNTER ($DATE1 — $DATE2)..." >&2

TMPFILE="${METRIKA_TMPDIR}/metrika_traffic_$$.csv"
trap 'rm -f "$TMPFILE"' EXIT

metrika_get_csv "$API_PATH" "$TMPFILE" \
    --data-urlencode "ids=$COUNTER" \
    --data-urlencode "date1=$DATE1" \
    --data-urlencode "date2=$DATE2" \
    --data-urlencode "metrics=$METRICS" \
    --data-urlencode "dimensions=$DIMENSIONS" \
    --data-urlencode "accuracy=1" \
    --data-urlencode "filters=$FILTERS" \
    ${GROUP:+--data-urlencode "group=$GROUP"} \
    ${LIMIT:+--data-urlencode "limit=$LIMIT"}

# Cache result
cp "$TMPFILE" "$CACHE_FILE"

# Output
echo "Traffic summary for counter $COUNTER ($DATE1 — $DATE2):"
print_csv_head "$CACHE_FILE" 30

if [ -n "$CSV_OUT" ]; then
    cp "$CACHE_FILE" "$CSV_OUT"
    echo "Exported to: $CSV_OUT"
fi
