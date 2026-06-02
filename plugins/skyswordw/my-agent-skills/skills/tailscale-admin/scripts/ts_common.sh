#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
ENV_FILE="${TAILSCALE_ENV_FILE:-$PROJECT_ROOT/secrets/local/providers/tailscale.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

TS_API_BASE="${TAILSCALE_API_BASE:-${TS_API_BASE:-https://api.tailscale.com/api/v2}}"
TS_API_KEY="${TAILSCALE_API_KEY:-${TS_API_KEY:-}}"
TS_TAILNET="${TAILSCALE_TAILNET:-${TS_TAILNET:-_unset_}}"

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "error: required command missing: $cmd" >&2
    exit 1
  }
}

require_api_key() {
  if [[ -z "$TS_API_KEY" ]]; then
    echo "error: missing TAILSCALE_API_KEY; expected it in $ENV_FILE" >&2
    exit 1
  fi
}

tailnet() {
  if [[ "$TS_TAILNET" == "_unset_" || -z "$TS_TAILNET" ]]; then
    printf '%s' '-'
  else
    printf '%s' "$TS_TAILNET"
  fi
}

urlencode() {
  local raw="$1"
  jq -nr --arg v "$raw" '$v|@uri'
}

build_query_string() {
  local query_json="$1"
  jq -r '
    if (type != "object") then
      error("query JSON must be an object")
    else
      to_entries
      | map(select(.value != null))
      | map("\(.key|@uri)=\((.value|tostring)|@uri)")
      | join("&")
    end
  ' <<<"$query_json"
}

http_call() {
  local method="$1"
  local url="$2"
  local body_file="${3:-}"
  local content_type="${4:-application/json}"

  require_cmd curl
  require_api_key

  local -a curl_args
  curl_args=(
    -sS
    -X "$method"
    -H "Authorization: Bearer $TS_API_KEY"
    -H "Accept: application/json"
    "$url"
  )

  if [[ -n "$body_file" ]]; then
    curl_args+=(
      -H "Content-Type: $content_type"
      --data-binary "@$body_file"
    )
  fi

  curl "${curl_args[@]}"
}

json_tmp_file() {
  local json="$1"
  local tmp_file
  tmp_file="$(mktemp)"
  jq -c . <<<"$json" > "$tmp_file"
  printf '%s' "$tmp_file"
}
