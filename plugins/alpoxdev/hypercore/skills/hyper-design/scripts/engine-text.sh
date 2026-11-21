#!/usr/bin/env bash
# Text-family scan: apply each rule matcher to the raw source text.
set -euo pipefail

RS_ENGINE_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_ENGINE_DIR/rule-shared.sh"

# scan_text <file> <textfile> <root> <rule-ids> [engine] prints id, engine, line, excerpt per match.
scan_text() {
  local engine=${5:-text}
  rs_scan match "$engine" "$2" "${4:-}"
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
