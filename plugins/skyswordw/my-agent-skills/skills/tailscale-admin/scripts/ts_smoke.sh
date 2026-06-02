#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPT_DIR/ts_catalog.sh" --search device --method GET >/dev/null
bash "$SCRIPT_DIR/ts_call.sh" listTailnetDevices \
  --params-json '{"tailnet":"-"}' \
  --dry-run >/dev/null
bash "$SCRIPT_DIR/ts_api.sh" rename-device device-id demo-name --dry-run >/dev/null

echo "OK: tailscale-admin project skill smoke checks passed"
