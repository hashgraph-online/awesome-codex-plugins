#!/usr/bin/env bash
# Markup-family scan: reuse the text scanner with the markup engine label.
set -euo pipefail

RS_ENGINE_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_ENGINE_DIR/engine-text.sh"

# scan_markup <file> <textfile> <root> <rule-ids> prints matching markup-engine rules.
scan_markup() {
  scan_text "$1" "$2" "$3" "${4:-}" markup
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
