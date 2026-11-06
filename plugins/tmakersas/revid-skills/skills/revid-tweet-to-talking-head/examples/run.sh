#!/usr/bin/env bash
# Tweet text + avatar -> talking-head video.
# Usage:  REVID_API_KEY=… ./run.sh ./tweet.txt <avatar-image-url>
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

TXT_FILE="${1:?path to tweet text required}"
AVATAR="${2:?avatar image url required}"

HERE="$(cd "$(dirname "$0")" && pwd)"
TXT=$(cat "$TXT_FILE")
PAYLOAD=$(jq --arg t "$TXT" --arg a "$AVATAR" \
  '.source.text=$t | .avatar.url=$a' \
  "$HERE/thread-text.json")

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
