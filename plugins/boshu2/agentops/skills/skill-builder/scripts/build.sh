#!/usr/bin/env bash
# Compatibility entrypoint; mutation and receipts belong to ao's Go owner.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SKILL_BUILDER_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
[[ $# -ge 2 ]] || { echo 'usage: build.sh from-scratch|from-template|absorb-external <slug> [--like <slug>|--from <path>] [--report <external-path>]' >&2; exit 2; }
mode="$1"; slug="$2"; shift 2
case "$mode" in from-scratch|from-template|absorb-external) ;; *) echo "unknown mode: $mode" >&2; exit 2;; esac
args=(skills build "$mode" "$slug" --repo "$REPO_ROOT")
while [[ $# -gt 0 ]]; do
 case "$1" in
 --like|--from) [[ $# -ge 2 ]] || exit 2; args+=(--source "$2"); shift 2;;
 --report) [[ $# -ge 2 ]] || exit 2; args+=(--report "$2"); shift 2;;
 --init-only) args+=(--init-only); shift;;
 *) echo "unknown argument: $1" >&2; exit 2;;
 esac
done
exec bash "$SCRIPT_DIR/run-ao.sh" "${args[@]}"
