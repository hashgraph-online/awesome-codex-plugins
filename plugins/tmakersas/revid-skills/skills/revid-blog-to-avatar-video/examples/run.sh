#!/usr/bin/env bash
# Blog post URL + avatar image -> talking-head video.
# Usage:  REVID_API_KEY=… ./run.sh <blog-url> <avatar-image-url>
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

BLOG="${1:?blog url required}"
AVATAR="${2:?avatar image url required}"

HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="$(jq --arg u "$BLOG" --arg a "$AVATAR" \
  '.source.url=$u | .avatar.url=$a' \
  "$HERE/blog-to-avatar.json")"

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
