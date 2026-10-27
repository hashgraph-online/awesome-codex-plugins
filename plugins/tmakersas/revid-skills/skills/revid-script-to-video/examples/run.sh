#!/usr/bin/env bash
# Script text -> video.
# Usage:  REVID_API_KEY=… ./run.sh                # uses bundled example
#         REVID_API_KEY=… ./run.sh ./script.txt
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD_FILE="$HERE/honey-script.json"

if [ "${1:-}" ] && [ -f "$1" ]; then
  TXT=$(cat "$1")
  PAYLOAD=$(jq --arg t "$TXT" '.source.text=$t' "$PAYLOAD_FILE")
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
