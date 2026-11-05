#!/usr/bin/env bash
# Default separated evidence report; --legacy preserves the accepted v1 contract.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
args=()
legacy=0
for arg in "$@"; do
  if [[ "$arg" == --legacy ]]; then legacy=1; else args+=("$arg"); fi
done
if [[ "$legacy" -eq 1 ]]; then
  exec bash "$SCRIPT_DIR/audit-legacy.sh" "${args[@]}"
fi
# Resolve paths before the source-aware launcher changes its working directory.
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[$i]}" in
    --profile) i=$((i+1)) ;;
    --repo) i=$((i+1)); [[ "${args[$i]:-}" = /* ]] || args[$i]="$PWD/${args[$i]:-}" ;;
    --json) i=$((i+1)); [[ "${args[$i]:-}" = /* ]] || args[$i]="$PWD/${args[$i]:-}" ;;
    --*) ;;
    *) [[ "${args[$i]}" = /* ]] || args[$i]="$PWD/${args[$i]}" ;;
  esac
done
exec bash "$SCRIPT_DIR/run-ao.sh" skills audit --repo "$REPO_ROOT" "${args[@]}"
