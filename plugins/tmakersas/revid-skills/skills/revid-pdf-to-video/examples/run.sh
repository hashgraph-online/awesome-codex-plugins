#!/usr/bin/env bash
# PDF URL -> summary video.
# Usage:  REVID_API_KEY=… ./run.sh <pdf-url>
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

URL="${1:?pdf url required}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD=$(jq --arg u "$URL" '.source.url=$u' "$HERE/whitepaper.json")

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
