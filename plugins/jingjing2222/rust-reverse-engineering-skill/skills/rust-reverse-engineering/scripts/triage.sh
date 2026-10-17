#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: triage.sh [OPTIONS] <binary-or-archive>

Options:
  --macho-arch ARCH   Select a specific universal Mach-O slice before triage
  -h, --help          Show this help message
EOF
}

TARGET=""
MACHO_ARCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --macho-arch)
      MACHO_ARCH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Error: unknown option $1" >&2
      usage
      exit 2
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  usage
  exit 2
fi

if [[ ! -e "$TARGET" ]]; then
  echo "ERROR: target does not exist: $TARGET"
  exit 2
fi

pick_tool() {
  for tool in "$@"; do
    if command -v "$tool" >/dev/null 2>&1; then
      echo "$tool"
      return 0
    fi
  done
  return 1
}

FILE_TOOL="$(pick_tool file || true)"
STRINGS_TOOL="$(pick_tool strings llvm-strings gstrings || true)"
READELF_TOOL="$(pick_tool readelf llvm-readelf greadelf || true)"
NM_TOOL="$(pick_tool nm llvm-nm gnm || true)"
OBJDUMP_TOOL="$(pick_tool objdump llvm-objdump gobjdump || true)"
RUSTFILT_TOOL="$(pick_tool rustfilt || true)"
OTOOL_TOOL="$(pick_tool otool || true)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/macho-slice.sh"

if [[ -z "$FILE_TOOL" || -z "$STRINGS_TOOL" || -z "$NM_TOOL" ]]; then
  echo "ERROR: missing one of required tools: file, strings, nm/llvm-nm"
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

macho_resolve_target "$TARGET" "$MACHO_ARCH" "$TMPDIR/macho"
ANALYSIS_TARGET="$MACHO_ANALYSIS_TARGET"

FILE_OUT="$("$FILE_TOOL" "$ANALYSIS_TARGET" 2>/dev/null || true)"
FORMAT="unknown"
ARCH="unknown"

case "$FILE_OUT" in
  *ELF*) FORMAT="ELF" ;;
  *Mach-O*) FORMAT="Mach-O" ;;
  *PE32*|*MS\ Windows*|*PE32+*) FORMAT="PE/COFF" ;;
  *current\ ar\ archive*) FORMAT="archive" ;;
  *archive\ random\ library*) FORMAT="archive" ;;
esac

case "$FILE_OUT" in
  *x86-64*|*x86_64*) ARCH="x86-64" ;;
  *aarch64*|*ARM64*|*arm64*) ARCH="aarch64" ;;
  *ARM*) ARCH="arm" ;;
  *80386*|*Intel\ 80386*) ARCH="x86" ;;
  *RISC-V*) ARCH="riscv" ;;
esac

STRIPPED="unknown"
if [[ "$FILE_OUT" == *"not stripped"* ]]; then
  STRIPPED="no"
elif [[ "$FILE_OUT" == *"stripped"* ]]; then
  STRIPPED="yes"
fi

DEBUG_INFO="none"
if [[ "$FORMAT" == "ELF" && -n "$READELF_TOOL" ]]; then
  if "$READELF_TOOL" -S "$ANALYSIS_TARGET" 2>/dev/null | grep -Eq '\.(z?debug_info|z?debug_line|z?debug_str|z?debug_abbrev)\b'; then
    DEBUG_INFO="DWARF"
  fi
elif [[ "$FORMAT" == "Mach-O" && -n "$OTOOL_TOOL" ]]; then
  if "$OTOOL_TOOL" -l "$ANALYSIS_TARGET" 2>/dev/null | grep -Eq '__DWARF|__debug_'; then
    DEBUG_INFO="DWARF/dSYM-hint"
  fi
elif [[ "$FORMAT" == "PE/COFF" ]]; then
  if "$STRINGS_TOOL" -a "$ANALYSIS_TARGET" 2>/dev/null | grep -Eiq '\.pdb($|\\)'; then
    DEBUG_INFO="PDB-hint"
  fi
fi

RAW_SYMBOLS="$TMPDIR/raw-symbols.txt"
RAW_STRINGS="$TMPDIR/raw-strings.txt"
DEMANGLED="$TMPDIR/demangled.txt"

"$NM_TOOL" -an "$ANALYSIS_TARGET" >"$RAW_SYMBOLS" 2>/dev/null || true
"$STRINGS_TOOL" -a "$ANALYSIS_TARGET" >"$RAW_STRINGS" 2>/dev/null || true

if [[ -n "$RUSTFILT_TOOL" ]]; then
  "$RUSTFILT_TOOL" <"$RAW_SYMBOLS" >"$DEMANGLED" 2>/dev/null || cp "$RAW_SYMBOLS" "$DEMANGLED"
else
  cp "$RAW_SYMBOLS" "$DEMANGLED"
fi

rust_score=0
evidence=()

if grep -Eq '(^|[^A-Za-z0-9])_R[A-Za-z0-9_]+' "$RAW_SYMBOLS"; then
  rust_score=$((rust_score + 2))
  evidence+=("v0-mangled-symbols")
fi

if grep -Eq '_ZN[^ ]*17h[0-9a-f]{16}E' "$RAW_SYMBOLS"; then
  rust_score=$((rust_score + 2))
  evidence+=("legacy-mangled-symbols")
fi

if grep -Eq '(^|[^A-Za-z0-9])(core|alloc|std)::' "$DEMANGLED"; then
  rust_score=$((rust_score + 2))
  evidence+=("demangled-runtime-namespaces")
fi

if grep -Eiq 'rust_begin_unwind|panic_fmt|core::panicking|alloc::|std::|\.rustc' "$RAW_STRINGS"; then
  rust_score=$((rust_score + 1))
  evidence+=("rust-runtime-strings")
fi

RUST_CONFIDENCE="low"
if [[ "$rust_score" -ge 4 ]]; then
  RUST_CONFIDENCE="high"
elif [[ "$rust_score" -ge 2 ]]; then
  RUST_CONFIDENCE="medium"
fi

EXPORTED_COUNT="$("$NM_TOOL" -g "$ANALYSIS_TARGET" 2>/dev/null | wc -l | tr -d ' ' || echo 0)"
IMPORTED_COUNT=0
if [[ "$FORMAT" == "ELF" && -n "$READELF_TOOL" ]]; then
  IMPORTED_COUNT="$("$READELF_TOOL" -Ws "$ANALYSIS_TARGET" 2>/dev/null | grep -c ' UND ' || true)"
elif [[ "$FORMAT" == "Mach-O" && -n "$OTOOL_TOOL" ]]; then
  IMPORTED_COUNT="$("$OTOOL_TOOL" -L "$ANALYSIS_TARGET" 2>/dev/null | tail -n +2 | wc -l | tr -d ' ' || echo 0)"
elif [[ "$FORMAT" == "PE/COFF" && -n "$OBJDUMP_TOOL" ]]; then
  IMPORTED_COUNT="$("$OBJDUMP_TOOL" -p "$ANALYSIS_TARGET" 2>/dev/null | grep -c 'DLL Name:' || true)"
fi

TOP_NAMESPACES="$TMPDIR/namespaces.txt"
grep -Eo '([A-Za-z_][A-Za-z0-9_]*::){1,}' "$DEMANGLED" 2>/dev/null \
  | sed 's/::$//' \
  | cut -d: -f1 \
  | grep -Ev '^(core|alloc|std|panic_unwind|unwind|compiler_builtins|hashbrown|test)$' \
  | sort | uniq -c | sort -nr | head -10 >"$TOP_NAMESPACES" || true

echo "ORIGINAL_TARGET: $TARGET"
echo "ANALYSIS_TARGET: $ANALYSIS_TARGET"
echo "MACHO_UNIVERSAL: $MACHO_IS_UNIVERSAL"
if [[ "$MACHO_IS_UNIVERSAL" == "yes" ]]; then
  echo "MACHO_ARCHES: $MACHO_ARCH_LIST"
  echo "MACHO_SELECTED_ARCH: $MACHO_SELECTED_ARCH"
  echo "MACHO_SELECTED_ARCH_TOKEN: $MACHO_SELECTED_ARCH_TOKEN"
fi
echo "TARGET: $ANALYSIS_TARGET"
echo "FILE: $FILE_OUT"
echo "FORMAT: $FORMAT"
echo "ARCH: $ARCH"
echo "STRIPPED: $STRIPPED"
echo "DEBUG_INFO: $DEBUG_INFO"
echo "RUST_CONFIDENCE: $RUST_CONFIDENCE"
if [[ ${#evidence[@]} -gt 0 ]]; then
  echo "RUST_EVIDENCE: $(IFS=, ; echo "${evidence[*]}")"
else
  echo "RUST_EVIDENCE: none"
fi
echo "EXPORTED_SYMBOLS: $EXPORTED_COUNT"
echo "IMPORTED_SYMBOL_HINTS: $IMPORTED_COUNT"

echo
echo "=== candidate namespaces ==="
if [[ -s "$TOP_NAMESPACES" ]]; then
  cat "$TOP_NAMESPACES"
else
  echo "(none recovered)"
fi

echo
echo "=== interesting strings ==="
grep -Eim 20 'rust_begin_unwind|panic|core::|alloc::|std::|tokio|serde|reqwest|hyper|mio|tracing|clap|prost|tonic|openssl|ring' "$RAW_STRINGS" || true
