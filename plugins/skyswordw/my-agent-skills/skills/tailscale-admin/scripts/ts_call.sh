#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ts_common.sh
source "$SCRIPT_DIR/ts_common.sh"
CATALOG="$SCRIPT_DIR/../references/operations.tsv"

usage() {
  cat <<'USAGE'
Usage:
  ts_call.sh <operationId> [flags]

Flags:
  --params-json JSON    JSON object for path params, e.g. '{"tailnet":"-"}'
  --query-json JSON     JSON object for query params
  --body-json JSON      Inline JSON request body
  --body-file FILE      JSON body file path
  --jq FILTER           jq filter to apply to response
  --raw                 print raw response
  --dry-run             print resolved request and exit
  --yes                 required for POST/PUT/PATCH/DELETE
  -h, --help            show help
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

OP_ID="$1"
shift

PARAMS_JSON="{}"
QUERY_JSON="{}"
BODY_JSON=""
BODY_FILE=""
JQ_FILTER=""
RAW=0
DRY_RUN=0
CONFIRM_WRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --params-json)
      PARAMS_JSON="${2:-}"
      shift 2
      ;;
    --query-json)
      QUERY_JSON="${2:-}"
      shift 2
      ;;
    --body-json)
      BODY_JSON="${2:-}"
      shift 2
      ;;
    --body-file)
      BODY_FILE="${2:-}"
      shift 2
      ;;
    --jq)
      JQ_FILTER="${2:-}"
      shift 2
      ;;
    --raw)
      RAW=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --yes)
      CONFIRM_WRITE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

require_cmd jq

jq -e 'type=="object"' <<<"$PARAMS_JSON" >/dev/null
jq -e 'type=="object"' <<<"$QUERY_JSON" >/dev/null

op_line="$(awk -F '\t' -v op="$OP_ID" 'NR > 1 && $1 == op { print; exit }' "$CATALOG")"
if [[ -z "$op_line" ]]; then
  echo "error: operationId not found: $OP_ID" >&2
  echo "hint: run $SCRIPT_DIR/ts_catalog.sh --search '$OP_ID'" >&2
  exit 1
fi

IFS=$'\t' read -r _ method path_tpl _tags _summary <<<"$op_line"
resolved_path="$path_tpl"

while [[ "$resolved_path" =~ \{([^}]+)\} ]]; do
  param_name="${BASH_REMATCH[1]}"
  value="$(jq -r --arg k "$param_name" '.[$k] // empty' <<<"$PARAMS_JSON")"
  if [[ -z "$value" ]]; then
    echo "error: missing required path param '$param_name' for $OP_ID" >&2
    exit 1
  fi
  encoded="$(urlencode "$value")"
  resolved_path="${resolved_path//\{$param_name\}/$encoded}"
done

if [[ -n "$BODY_JSON" && -n "$BODY_FILE" ]]; then
  echo "error: use either --body-json or --body-file, not both" >&2
  exit 1
fi

tmp_body=""
if [[ -n "$BODY_JSON" ]]; then
  tmp_body="$(json_tmp_file "$BODY_JSON")"
  BODY_FILE="$tmp_body"
fi

trap '[[ -n "${tmp_body:-}" && -f "$tmp_body" ]] && rm -f "$tmp_body"' EXIT

qs="$(build_query_string "$QUERY_JSON")"
url="$TS_API_BASE$resolved_path"
if [[ -n "$qs" ]]; then
  url="$url?$qs"
fi

if [[ "$DRY_RUN" -eq 0 && "$method" != "GET" && "$CONFIRM_WRITE" -ne 1 ]]; then
  echo "error: $OP_ID uses $method and may mutate state; re-run with --yes after validating with --dry-run" >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "method=$method"
  echo "url=$url"
  if [[ -n "$BODY_FILE" ]]; then
    echo "body_file=$BODY_FILE"
    if [[ -n "$BODY_JSON" ]]; then
      jq . "$BODY_FILE"
    fi
  else
    echo "body_file=<none>"
  fi
  exit 0
fi

resp="$(http_call "$method" "$url" "$BODY_FILE")"

if [[ "$RAW" -eq 1 ]]; then
  printf '%s\n' "$resp"
  exit 0
fi

if [[ -n "$JQ_FILTER" ]]; then
  jq -r "$JQ_FILTER" <<<"$resp"
else
  jq . <<<"$resp"
fi
