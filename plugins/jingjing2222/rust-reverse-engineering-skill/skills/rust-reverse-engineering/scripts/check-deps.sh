#!/usr/bin/env bash
set -euo pipefail

has() {
  command -v "$1" >/dev/null 2>&1
}

check_any() {
  local label="$1"
  shift
  local found=""
  for tool in "$@"; do
    if has "$tool"; then
      found="$tool"
      break
    fi
  done

  if [[ -n "$found" ]]; then
    echo "OK:${label}:${found}"
  else
    echo "INSTALL_REQUIRED:${label}:$*"
  fi
}

check_optional_any() {
  local label="$1"
  shift
  local found=""
  for tool in "$@"; do
    if has "$tool"; then
      found="$tool"
      break
    fi
  done

  if [[ -n "$found" ]]; then
    echo "OK_OPTIONAL:${label}:${found}"
  else
    echo "INSTALL_OPTIONAL:${label}:$*"
  fi
}

check_any file file
check_any strings strings llvm-strings gstrings
check_any headers readelf llvm-readelf greadelf otool
check_any nm nm llvm-nm gnm
check_any disassembler objdump llvm-objdump gobjdump otool

check_optional_any rustfilt rustfilt
check_optional_any debugger gdb lldb
check_optional_any ghidra ghidraRun analyzeHeadless ghidra
check_optional_any ida idat64 ida64 ida
check_optional_any binaryninja binaryninja

missing_required=0
while IFS= read -r line; do
  [[ "$line" == INSTALL_REQUIRED:* ]] && missing_required=1
done < <(
  check_any file file
  check_any strings strings llvm-strings gstrings
  check_any headers readelf llvm-readelf greadelf otool
  check_any nm nm llvm-nm gnm
  check_any disassembler objdump llvm-objdump gobjdump otool
)

if [[ "$missing_required" -eq 1 ]]; then
  exit 1
fi
