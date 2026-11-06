#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <binary-or-archive> [grep-regex]"
  exit 2
fi

TARGET="$1"
FILTER="${2:-}"

pick_tool() {
  for tool in "$@"; do
    if command -v "$tool" >/dev/null 2>&1; then
      echo "$tool"
      return 0
    fi
  done
  return 1
}

NM_TOOL="$(pick_tool nm llvm-nm gnm || true)"
RUSTFILT_TOOL="$(pick_tool rustfilt || true)"

if [[ -z "$NM_TOOL" ]]; then
  echo "ERROR: nm, llvm-nm, or gnm is required"
  exit 1
fi

if [[ ! -e "$TARGET" ]]; then
  echo "ERROR: target does not exist: $TARGET"
  exit 2
fi

if [[ -n "$RUSTFILT_TOOL" ]]; then
  if [[ -n "$FILTER" ]]; then
    "$NM_TOOL" -an "$TARGET" 2>/dev/null | "$RUSTFILT_TOOL" | grep -Ei "$FILTER" || true
  else
    "$NM_TOOL" -an "$TARGET" 2>/dev/null | "$RUSTFILT_TOOL"
  fi
else
  echo "WARN: rustfilt not found; emitting raw symbols" >&2
  if [[ -n "$FILTER" ]]; then
    "$NM_TOOL" -an "$TARGET" 2>/dev/null | grep -Ei "$FILTER" || true
  else
    "$NM_TOOL" -an "$TARGET" 2>/dev/null
  fi
fi
