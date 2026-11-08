#!/usr/bin/env bash
# CSS-family scan: reuse the text scanner with the css engine label.
set -euo pipefail

RS_ENGINE_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_ENGINE_DIR/engine-text.sh"

# scan_css <file> <textfile> <root> <rule-ids> prints matching css-engine rules.
scan_css() {
  scan_text "$1" "$2" "$3" "${4:-}" css
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
