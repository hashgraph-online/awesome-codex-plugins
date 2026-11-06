#!/usr/bin/env bash
# End-to-end demo: Shopify product URL -> 9:16 promo video.
# Usage:  REVID_API_KEY=sk_… ./run.sh https://your-shop.com/products/x
set -euo pipefail

: "${REVID_API_KEY:?set REVID_API_KEY}"
URL="${1:-https://soundlabs.shop/products/aeropods-pro}"

HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="$(jq --arg url "$URL" '.source.url=$url' "$HERE/shopify-aeropods.json")"

echo "→ POST /render"
RESP=$(curl -fsS https://www.revid.ai/api/public/v3/render \
  -H "Content-Type: application/json" \
  -H "key: $REVID_API_KEY" \
  -d "$PAYLOAD")
echo "$RESP" | jq .

PID=$(echo "$RESP" | jq -r .pid)
[ "$PID" != "null" ] || { echo "render failed: $RESP"; exit 1; }

echo "→ polling pid=$PID"
while :; do
  STATUS=$(curl -fsSL "https://www.revid.ai/api/public/v3/status?pid=$PID" \
    -H "key: $REVID_API_KEY")
  S=$(echo "$STATUS" | jq -r .status)
  P=$(echo "$STATUS" | jq -r .progress)
  echo "  status=$S progress=$P"
  case "$S" in
    ready)  echo "$STATUS" | jq .; break ;;
    failed) echo "FAILED: $STATUS"; exit 1 ;;
  esac
  sleep 5
done
