#!/bin/sh
# Common functions for Yandex Metrika API skill
# POSIX sh compatible — no bashisms

set -e
umask 077

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="${YANDEX_METRIKA_PROJECT_ROOT:-$PWD}"
CONFIG_FILE="${YANDEX_METRIKA_CONFIG_FILE:-$PROJECT_ROOT/.codex/yandex-metrika.env}"
CACHE_DIR="${YANDEX_METRIKA_CACHE_DIR:-$PROJECT_ROOT/.codex/cache/yandex-metrika}"

METRIKA_API="https://api-metrika.yandex.net"

# Ensure tmp directory exists
METRIKA_TMPDIR="${TMPDIR:-/tmp}"
mkdir -p "$METRIKA_TMPDIR"

# --------------- Config ---------------

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        _config_mode=$(stat -f '%Lp' "$CONFIG_FILE" 2>/dev/null || stat -c '%a' "$CONFIG_FILE" 2>/dev/null || true)
        if [ "$_config_mode" != "600" ]; then
            echo "Error: Metrika config file must have mode 0600: $CONFIG_FILE" >&2
            exit 1
        fi
        # shellcheck disable=SC1090
        . "$CONFIG_FILE"
    fi

    if [ -z "$YANDEX_METRIKA_TOKEN" ]; then
        echo "Error: YANDEX_METRIKA_TOKEN not found." >&2
        echo "Set it in environment or in: $CONFIG_FILE" >&2
        echo "See: $SKILL_DIR/references/metrika/CONFIG.md" >&2
        exit 1
    fi
    case "$YANDEX_METRIKA_TOKEN" in
        *[!A-Za-z0-9._~-]*)
            echo "Error: YANDEX_METRIKA_TOKEN has invalid characters." >&2
            exit 1
            ;;
    esac

    mkdir -p "$CACHE_DIR"
    chmod 700 "$CACHE_DIR"
}

# --------------- Cache helpers ---------------

# cache_dir_for_counter <counter_id>
cache_dir_for_counter() {
    _cdc_dir="$CACHE_DIR/counter_$1"
    mkdir -p "$_cdc_dir/reports"
    echo "$_cdc_dir"
}

# cache_key <params_string> — deterministic hash via cksum
cache_key() {
    printf '%s' "$1" | cksum | awk '{print $1}'
}

# cache_get <file_path> — prints cached file if exists and not empty
# Returns 0 if cache hit, 1 if miss
cache_get() {
    if [ -f "$1" ] && [ -s "$1" ]; then
        cat "$1"
        return 0
    fi
    return 1
}

# cache_put <file_path> — reads stdin, writes to file
cache_put() {
    mkdir -p "$(dirname "$1")"
    cat > "$1"
}

# --------------- API helpers ---------------

# metrika_get <path> [extra_curl_args...]
# Makes authenticated GET request, returns body. Headers saved to temp file.
metrika_get() {
    _mg_path="$1"
    shift
    _mg_url="${METRIKA_API}${_mg_path}"
    _mg_headers="${METRIKA_TMPDIR}/metrika_headers_$$.txt"
    _mg_config="${METRIKA_TMPDIR}/metrika_curl_$$.conf"
    printf 'header = "Authorization: OAuth %s"\nheader = "Accept-Charset: utf-8"\n' "$YANDEX_METRIKA_TOKEN" > "$_mg_config"
    chmod 600 "$_mg_config"

    _mg_body=$(curl --config "$_mg_config" -s -G -D "$_mg_headers" \
        "$@" \
        "$_mg_url") || {
        rm -f "$_mg_headers" "$_mg_config"
        echo "Error: curl failed for $_mg_url" >&2
        return 1
    }

    # Check for 429
    _mg_status=$(head -1 "$_mg_headers" | grep -o '[0-9][0-9][0-9]' | head -1)
    if [ "$_mg_status" = "429" ]; then
        _mg_retry=$(grep -i 'Retry-After' "$_mg_headers" | sed 's/[^0-9]//g' | head -1)
        rm -f "$_mg_headers" "$_mg_config"
        # Only retry once (guard via env var)
        if [ -z "${_METRIKA_RETRY_DONE:-}" ] && [ -n "$_mg_retry" ] && [ "$_mg_retry" -le 60 ] 2>/dev/null; then
            _mg_jitter=$(awk 'BEGIN{srand(); printf "%d", rand()*3}')
            _mg_wait=$(( _mg_retry + _mg_jitter ))
            echo "Rate limited. Waiting ${_mg_wait}s (Retry-After: ${_mg_retry}s)..." >&2
            sleep "$_mg_wait"
            _METRIKA_RETRY_DONE=1 metrika_get "$_mg_path" "$@"
            return $?
        else
            echo "Error: Rate limit exceeded (429). Metrika quota: ~200 req/5min." >&2
            echo "Wait ~5 minutes and retry." >&2
            return 1
        fi
    fi

    # Check for HTTP errors
    if [ -n "$_mg_status" ] && [ "$_mg_status" -ge 400 ] 2>/dev/null; then
        rm -f "$_mg_headers" "$_mg_config"
        echo "Error: HTTP $_mg_status from $_mg_url" >&2
        echo "$_mg_body" >&2
        return 1
    fi

    rm -f "$_mg_headers" "$_mg_config"
    printf '%s' "$_mg_body"
}

# metrika_get_csv <path> <output_file> [extra_curl_args...]
# Downloads CSV report to file. Returns 0 on success.
metrika_get_csv() {
    _mgc_path="$1"
    _mgc_output="$2"
    shift 2
    _mgc_url="${METRIKA_API}${_mgc_path}"
    _mgc_headers="${METRIKA_TMPDIR}/metrika_headers_$$.txt"
    _mgc_config="${METRIKA_TMPDIR}/metrika_curl_$$.conf"
    printf 'header = "Authorization: OAuth %s"\nheader = "Accept-Charset: utf-8"\n' "$YANDEX_METRIKA_TOKEN" > "$_mgc_config"
    chmod 600 "$_mgc_config"

    curl --config "$_mgc_config" -s -G -D "$_mgc_headers" \
        -o "$_mgc_output" \
        "$@" \
        "$_mgc_url" || {
        rm -f "$_mgc_headers" "$_mgc_config"
        echo "Error: curl failed for $_mgc_url" >&2
        return 1
    }

    _mgc_status=$(head -1 "$_mgc_headers" | grep -o '[0-9][0-9][0-9]' | head -1)
    if [ "$_mgc_status" = "429" ]; then
        _mgc_retry=$(grep -i 'Retry-After' "$_mgc_headers" | sed 's/[^0-9]//g' | head -1)
        rm -f "$_mgc_headers" "$_mgc_config"
        if [ -z "${_METRIKA_RETRY_DONE:-}" ] && [ -n "$_mgc_retry" ] && [ "$_mgc_retry" -le 60 ] 2>/dev/null; then
            _mgc_jitter=$(awk 'BEGIN{srand(); printf "%d", rand()*3}')
            _mgc_wait=$(( _mgc_retry + _mgc_jitter ))
            echo "Rate limited. Waiting ${_mgc_wait}s..." >&2
            sleep "$_mgc_wait"
            _METRIKA_RETRY_DONE=1 metrika_get_csv "$_mgc_path" "$_mgc_output" "$@"
            return $?
        else
            echo "Error: Rate limit exceeded (429). Wait ~5 minutes." >&2
            return 1
        fi
    fi

    if [ -n "$_mgc_status" ] && [ "$_mgc_status" -ge 400 ] 2>/dev/null; then
        rm -f "$_mgc_headers" "$_mgc_config"
        echo "Error: HTTP $_mgc_status" >&2
        cat "$_mgc_output" >&2
        return 1
    fi

    rm -f "$_mgc_headers" "$_mgc_config"
    return 0
}

# metrika_mgmt_get <path> [extra_curl_args...]
# Management API with simple backoff (2/4/8s) for 429.
metrika_mgmt_get() {
    _mmg_path="$1"
    shift
    _mmg_attempt=0
    _mmg_max=3
    _mmg_delay=2

    while [ "$_mmg_attempt" -lt "$_mmg_max" ]; do
        _mmg_result=$(metrika_get "$_mmg_path" "$@") && {
            printf '%s' "$_mmg_result"
            return 0
        }
        _mmg_attempt=$(( _mmg_attempt + 1 ))
        if [ "$_mmg_attempt" -lt "$_mmg_max" ]; then
            echo "Management API retry ${_mmg_attempt}/${_mmg_max}, waiting ${_mmg_delay}s..." >&2
            sleep "$_mmg_delay"
            _mmg_delay=$(( _mmg_delay * 2 ))
        fi
    done
    return 1
}

# --------------- Filter/param builders ---------------

# build_filters <base_filter> [device] [source] [attribution]
# Combines filters with AND
build_filters() {
    _bf_result="${1:-ym:s:isRobot=='No'}"
    _bf_device="$2"
    _bf_source="$3"
    _bf_attr="${4:-lastsign}"

    if [ -n "$_bf_device" ] && [ "$_bf_device" != "all" ]; then
        case "$_bf_device" in
            desktop) _bf_result="${_bf_result} AND ym:s:deviceCategory=='desktop'" ;;
            mobile)  _bf_result="${_bf_result} AND ym:s:deviceCategory=='mobile'" ;;
            tablet)  _bf_result="${_bf_result} AND ym:s:deviceCategory=='tablet'" ;;
        esac
    fi

    if [ -n "$_bf_source" ] && [ "$_bf_source" != "all" ]; then
        case "$_bf_source" in
            organic)  _bf_result="${_bf_result} AND ym:s:${_bf_attr}TrafficSource=='organic'" ;;
            ad)       _bf_result="${_bf_result} AND ym:s:${_bf_attr}TrafficSource=='ad'" ;;
            referral) _bf_result="${_bf_result} AND ym:s:${_bf_attr}TrafficSource=='referral'" ;;
            direct)   _bf_result="${_bf_result} AND ym:s:${_bf_attr}TrafficSource=='direct'" ;;
            social)   _bf_result="${_bf_result} AND ym:s:${_bf_attr}TrafficSource=='social'" ;;
        esac
    fi

    echo "$_bf_result"
}

# --------------- Output helpers ---------------

# print_csv_head <file> [n_lines]
# Prints first N lines of CSV (default 30) with line numbers
print_csv_head() {
    _pch_file="$1"
    _pch_n="${2:-30}"
    if [ -f "$_pch_file" ]; then
        head -n "$_pch_n" "$_pch_file"
        _pch_total=$(wc -l < "$_pch_file" | tr -d ' ')
        if [ "$_pch_total" -gt "$_pch_n" ]; then
            echo "... ($(( _pch_total - _pch_n )) more rows, full data in: $_pch_file)"
        fi
    fi
}

# --------------- JSON minimal helpers (management API only) ---------------

# json_extract_field <json_string> <field_name>
# Extracts value of a simple key:value pair (not nested)
json_extract_field() {
    echo "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//'
}

# json_extract_number <json_string> <field_name>
json_extract_number() {
    echo "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*[0-9]*" | head -1 | sed 's/.*:[[:space:]]*//'
}

# --------------- Date helpers ---------------

# date_is_today <YYYY-MM-DD> — returns 0 if date equals today
date_is_today() {
    [ "$1" = "$(date +%Y-%m-%d)" ]
}

# --------------- Common param parsing ---------------

# parse_common_params "$@"
# Sets variables: COUNTER, DATE1, DATE2, GROUP, DEVICE, SOURCE, ATTRIBUTION, FILTERS, LIMIT, CSV_OUT, NO_CACHE
parse_common_params() {
    COUNTER=""
    DATE1=""
    DATE2=""
    GROUP=""
    DEVICE=""
    SOURCE=""
    ATTRIBUTION="lastsign"
    FILTERS=""
    LIMIT=""
    CSV_OUT=""
    NO_CACHE=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --counter)     COUNTER="$2"; shift 2 ;;
            --date1)       DATE1="$2"; shift 2 ;;
            --date2)       DATE2="$2"; shift 2 ;;
            --group)       GROUP="$2"; shift 2 ;;
            --device)      DEVICE="$2"; shift 2 ;;
            --source)      SOURCE="$2"; shift 2 ;;
            --attribution) ATTRIBUTION="$2"; shift 2 ;;
            --filters)     FILTERS="$2"; shift 2 ;;
            --limit)       LIMIT="$2"; shift 2 ;;
            --csv)         CSV_OUT="$2"; shift 2 ;;
            --no-cache)    NO_CACHE="1"; shift ;;
            *)             shift ;;
        esac
    done

    # Default date2 to today
    if [ -z "$DATE2" ]; then
        DATE2=$(date +%Y-%m-%d)
    fi

    # Build combined filters
    FILTERS=$(build_filters "${FILTERS:-ym:s:isRobot=='No'}" "$DEVICE" "$SOURCE" "$ATTRIBUTION")
}

# require_counter — exits if COUNTER not set
require_counter() {
    if [ -z "$COUNTER" ]; then
        echo "Error: --counter <ID> is required." >&2
        exit 1
    fi
}

# require_dates — exits if DATE1 not set
require_dates() {
    if [ -z "$DATE1" ]; then
        echo "Error: --date1 YYYY-MM-DD is required." >&2
        exit 1
    fi
}
