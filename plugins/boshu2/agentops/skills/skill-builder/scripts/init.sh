#!/usr/bin/env bash
# Compatibility initialization only; Go owns source creation and receipts.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ $# -ge 2 ]] || { echo 'usage: init.sh --scratch|--template|--external <slug> [--like <slug>|--from <path>] [--report <external-path>]' >&2; exit 2; }
case "$1" in --scratch) mode=from-scratch;; --template) mode=from-template;; --external) mode=absorb-external;; *) exit 2;; esac
shift
exec bash "$SCRIPT_DIR/build.sh" "$mode" "$@" --init-only
