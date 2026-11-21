#!/usr/bin/env bash
# Product description -> AI ad video.
# Usage:  REVID_API_KEY=… ./run.sh           # uses bundled example
#         REVID_API_KEY=… ./run.sh ./desc.txt
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD_FILE="$HERE/aeropods-ad.json"

if [ "${1:-}" ] && [ -f "$1" ]; then
  DESC=$(cat "$1")
  PAYLOAD=$(jq --arg p "$DESC" '.source.prompt=$p' "$PAYLOAD_FILE")
else
  PAYLOAD=$(cat "$PAYLOAD_FILE")
fi

PID=$(curl -fsS https://www.revid.ai/api/public/v3/render \
  -H "Content-Type: application/json" -H "key: $REVID_API_KEY" \
  -d "$PAYLOAD" | jq -r .pid)
echo "pid=$PID"

while :; do
  R=$(curl -fsSL "https://www.revid.ai/api/public/v3/status?pid=$PID" -H "key: $REVID_API_KEY")
  S=$(echo "$R" | jq -r .status); echo "  status=$S progress=$(echo "$R" | jq -r .progress)"
  [ "$S" = "ready" ] && { echo "$R" | jq .; break; }
  [ "$S" = "failed" ] && { echo "FAILED: $R"; exit 1; }
  sleep 5
done
