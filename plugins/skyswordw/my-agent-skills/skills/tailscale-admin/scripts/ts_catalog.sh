#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CATALOG="$SCRIPT_DIR/../references/operations.tsv"

TAG_FILTER=""
METHOD_FILTER=""
SEARCH_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG_FILTER="${2:-}"
      shift 2
      ;;
    --method)
      METHOD_FILTER="${2:-}"
      shift 2
      ;;
    --search)
      SEARCH_FILTER="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: ts_catalog.sh [--tag TAG] [--method METHOD] [--search TEXT]

Examples:
  ts_catalog.sh --tag Devices
  ts_catalog.sh --method GET --search device
USAGE
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

awk -F '\t' \
  -v tag="$TAG_FILTER" \
  -v method="$METHOD_FILTER" \
  -v search="$SEARCH_FILTER" '
    BEGIN {
      if (method != "") {
        method = toupper(method)
      }
      print "operationId\tmethod\tpath\ttags\tsummary"
    }
    NR == 1 { next }
    {
      hay = tolower($1 " " $3 " " $4 " " $5)
      if (tag != "" && index($4, tag) == 0) next
      if (method != "" && toupper($2) != method) next
      if (search != "" && index(hay, tolower(search)) == 0) next
      print $0
    }
  ' "$CATALOG" | column -t -s $'\t'
