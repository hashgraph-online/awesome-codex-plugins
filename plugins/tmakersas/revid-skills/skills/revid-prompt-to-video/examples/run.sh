#!/usr/bin/env bash
# Idea prompt -> video.
# Usage:  REVID_API_KEY=… ./run.sh "Your one-line idea"
set -euo pipefail
: "${REVID_API_KEY:?set REVID_API_KEY}"

PROMPT="${1:-Why honey never spoils.}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD=$(jq --arg p "$PROMPT" '.source.prompt=$p' "$HERE/honey-prompt.json")

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
