#!/bin/sh
set -eu

main() {
  if ! command -v sendsets >/dev/null 2>&1; then
    printf '%s\n' 'sendsets is not on PATH; check ~/.local/bin/sendsets' >&2
    exit 1
  fi
  sendsets auth status --json
  sendsets doctor --json
}

main "$@"
