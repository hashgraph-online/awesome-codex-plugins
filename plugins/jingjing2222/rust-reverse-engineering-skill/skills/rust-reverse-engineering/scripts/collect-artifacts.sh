#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: collect-artifacts.sh [OPTIONS] <binary-or-archive>

Create a Rust reverse-engineering artifact bundle for a native target.

Arguments:
  <binary-or-archive>      Path to ELF, Mach-O, PE/COFF, .so, .dylib, .dll, .a,
                           .rlib, or object file

Options:
  -o, --output DIR         Output directory (default: <basename>-reverse-output)
  --no-disasm              Skip disassembly output
  --no-ghidra              Skip Ghidra headless pseudocode export
  --macho-arch ARCH        Select a specific universal Mach-O slice before analysis
  --ghidra-max-functions N Limit Ghidra decompilation to N functions (default: all)
  --ghidra-timeout SEC     Ghidra per-function decompile timeout in seconds (default: 60)
  -h, --help               Show this help message

Output layout:
  <output>/
  ├── input/
  ├── triage/
  ├── symbols/
  ├── headers/
  ├── disassembly/
  ├── decompiled/
  └── reports/
EOF
  exit 0
}

pick_tool() {
  for tool in "$@"; do
    if command -v "$tool" >/dev/null 2>&1; then
      echo "$tool"
      return 0
    fi
  done
  return 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR=""
NO_DISASM=false
NO_GHIDRA=false
MACHO_ARCH=""
GHIDRA_MAX_FUNCTIONS=0
GHIDRA_TIMEOUT=60
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --no-disasm)
      NO_DISASM=true
      shift
      ;;
    --no-ghidra)
      NO_GHIDRA=true
      shift
      ;;
    --macho-arch)
      MACHO_ARCH="$2"
      shift 2
      ;;
    --ghidra-max-functions)
      GHIDRA_MAX_FUNCTIONS="$2"
      shift 2
      ;;
    --ghidra-timeout)
      GHIDRA_TIMEOUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    -*)
      echo "Error: Unknown option $1" >&2
      usage
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Error: No target specified." >&2
  usage
fi

if [[ ! -e "$TARGET" ]]; then
  echo "Error: target does not exist: $TARGET" >&2
  exit 2
fi

TARGET_NAME="$(basename "$TARGET")"
TARGET_STEM="${TARGET_NAME%.*}"
if [[ "$TARGET_STEM" == "$TARGET_NAME" ]]; then
  TARGET_STEM="${TARGET_NAME}"
fi

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="${TARGET_STEM}-reverse-output"
fi

mkdir -p \
  "$OUTPUT_DIR/input" \
  "$OUTPUT_DIR/triage" \
  "$OUTPUT_DIR/symbols" \
  "$OUTPUT_DIR/headers" \
  "$OUTPUT_DIR/disassembly" \
  "$OUTPUT_DIR/decompiled/ghidra" \
  "$OUTPUT_DIR/reports"

cp -p "$TARGET" "$OUTPUT_DIR/input/$TARGET_NAME"

# shellcheck source=/dev/null
source "$SCRIPT_DIR/macho-slice.sh"
macho_resolve_target "$TARGET" "$MACHO_ARCH" "$OUTPUT_DIR/input"
ANALYSIS_TARGET="$MACHO_ANALYSIS_TARGET"
macho_write_metadata "$OUTPUT_DIR/input/analysis-target.txt"

if [[ "$ANALYSIS_TARGET" != "$TARGET" ]]; then
  echo "INFO: selected Mach-O slice $MACHO_SELECTED_ARCH_TOKEN -> $ANALYSIS_TARGET"
fi

echo "=== Collecting triage output ==="
bash "$SCRIPT_DIR/triage.sh" "$ANALYSIS_TARGET" > "$OUTPUT_DIR/triage/summary.txt"

STRINGS_TOOL="$(pick_tool strings llvm-strings gstrings || true)"
NM_TOOL="$(pick_tool nm llvm-nm gnm || true)"
READELF_TOOL="$(pick_tool readelf llvm-readelf greadelf || true)"
OBJDUMP_TOOL="$(pick_tool llvm-objdump objdump gobjdump || true)"
OTOOL_TOOL="$(pick_tool otool || true)"

if [[ -n "$STRINGS_TOOL" ]]; then
  "$STRINGS_TOOL" -a "$ANALYSIS_TARGET" > "$OUTPUT_DIR/triage/strings.txt" 2>/dev/null || true
  grep -Eim 200 'rust_begin_unwind|panic|core::|alloc::|std::|tokio|serde|reqwest|hyper|mio|tracing|clap|prost|tonic|openssl|ring|jni|ffi|objc' \
    "$OUTPUT_DIR/triage/strings.txt" > "$OUTPUT_DIR/triage/interesting-strings.txt" || true
fi

if [[ -n "$NM_TOOL" ]]; then
  "$NM_TOOL" -an "$ANALYSIS_TARGET" > "$OUTPUT_DIR/symbols/raw.txt" 2>/dev/null || true
  "$NM_TOOL" -g "$ANALYSIS_TARGET" > "$OUTPUT_DIR/symbols/exports.txt" 2>/dev/null || true
fi

bash "$SCRIPT_DIR/demangle-symbols.sh" "$ANALYSIS_TARGET" > "$OUTPUT_DIR/symbols/demangled.txt" 2>/dev/null || true

grep -Eo '([A-Za-z_][A-Za-z0-9_]*::){1,}' "$OUTPUT_DIR/symbols/demangled.txt" 2>/dev/null \
  | sed 's/::$//' \
  | cut -d: -f1 \
  | sort | uniq -c | sort -nr > "$OUTPUT_DIR/symbols/namespaces.txt" || true

FORMAT="$(sed -n 's/^FORMAT: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"

case "$FORMAT" in
  ELF)
    if [[ -n "$READELF_TOOL" ]]; then
      "$READELF_TOOL" -h "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/readelf-header.txt" 2>/dev/null || true
      "$READELF_TOOL" -S "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/readelf-sections.txt" 2>/dev/null || true
      "$READELF_TOOL" -Ws "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/readelf-symbols.txt" 2>/dev/null || true
      grep ' UND ' "$OUTPUT_DIR/headers/readelf-symbols.txt" > "$OUTPUT_DIR/symbols/imports.txt" || true
    fi
    ;;
  Mach-O)
    if [[ -n "$OTOOL_TOOL" ]]; then
      "$OTOOL_TOOL" -hv "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/otool-header.txt" 2>/dev/null || true
      "$OTOOL_TOOL" -l "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/otool-load-commands.txt" 2>/dev/null || true
      "$OTOOL_TOOL" -L "$ANALYSIS_TARGET" > "$OUTPUT_DIR/symbols/imports.txt" 2>/dev/null || true
    fi
    ;;
  PE/COFF)
    if [[ -n "$OBJDUMP_TOOL" ]]; then
      "$OBJDUMP_TOOL" -p "$ANALYSIS_TARGET" > "$OUTPUT_DIR/headers/objdump-pe.txt" 2>/dev/null || true
      grep 'DLL Name:' "$OUTPUT_DIR/headers/objdump-pe.txt" > "$OUTPUT_DIR/symbols/imports.txt" || true
    fi
    ;;
esac

if [[ "$NO_DISASM" == false ]]; then
  echo "=== Collecting disassembly ==="
  case "$FORMAT" in
    Mach-O)
      if [[ -n "$OTOOL_TOOL" ]]; then
        "$OTOOL_TOOL" -tvV "$ANALYSIS_TARGET" > "$OUTPUT_DIR/disassembly/disassembly.txt" 2>/dev/null || true
      fi
      ;;
    *)
      if [[ -n "$OBJDUMP_TOOL" ]]; then
        if [[ "$OBJDUMP_TOOL" == "llvm-objdump" ]]; then
          "$OBJDUMP_TOOL" --demangle -d "$ANALYSIS_TARGET" > "$OUTPUT_DIR/disassembly/disassembly.txt" 2>/dev/null || true
        else
          "$OBJDUMP_TOOL" -d "$ANALYSIS_TARGET" > "$OUTPUT_DIR/disassembly/disassembly.txt" 2>/dev/null || true
        fi
      fi
      ;;
  esac
fi

GHIDRA_STATUS="not-run"
if [[ "$NO_GHIDRA" == false ]]; then
  if command -v analyzeHeadless >/dev/null 2>&1; then
    echo "=== Exporting Ghidra pseudocode ==="
    if bash "$SCRIPT_DIR/export-ghidra-pseudocode.sh" \
      --max-functions "$GHIDRA_MAX_FUNCTIONS" \
      --timeout "$GHIDRA_TIMEOUT" \
      --macho-arch "$MACHO_ARCH" \
      "$TARGET" \
      "$OUTPUT_DIR/decompiled/ghidra"; then
      GHIDRA_STATUS="ok"
    else
      GHIDRA_STATE="$(sed -n 's/^STATE: //p' "$OUTPUT_DIR/decompiled/ghidra/status.txt" 2>/dev/null | head -1)"
      case "$GHIDRA_STATE" in
        interrupted)
          GHIDRA_STATUS="interrupted"
          ;;
        running|launching)
          GHIDRA_STATUS="partial"
          ;;
        failed)
          GHIDRA_STATUS="failed"
          ;;
        *)
          if [[ -s "$OUTPUT_DIR/decompiled/ghidra/functions.tsv" ]]; then
            GHIDRA_STATUS="partial"
          else
            GHIDRA_STATUS="failed"
          fi
          ;;
      esac
    fi
  else
    GHIDRA_STATUS="missing"
  fi
else
  GHIDRA_STATUS="skipped"
fi

bash "$SCRIPT_DIR/find-rust-patterns.sh" "$OUTPUT_DIR" > "$OUTPUT_DIR/reports/pattern-hits.txt" 2>/dev/null || true

TARGET_LINE="$(sed -n 's/^TARGET: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
ORIGINAL_TARGET_LINE="$(sed -n 's/^ORIGINAL_TARGET: //p' "$OUTPUT_DIR/input/analysis-target.txt" | head -1)"
ANALYSIS_TARGET_LINE="$(sed -n 's/^ANALYSIS_TARGET: //p' "$OUTPUT_DIR/input/analysis-target.txt" | head -1)"
MACHO_UNIVERSAL_LINE="$(sed -n 's/^MACHO_UNIVERSAL: //p' "$OUTPUT_DIR/input/analysis-target.txt" | head -1)"
MACHO_ARCHES_LINE="$(sed -n 's/^MACHO_ARCHES: //p' "$OUTPUT_DIR/input/analysis-target.txt" | head -1)"
MACHO_SELECTED_ARCH_LINE="$(sed -n 's/^MACHO_SELECTED_ARCH: //p' "$OUTPUT_DIR/input/analysis-target.txt" | head -1)"
ARCH_LINE="$(sed -n 's/^ARCH: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
STRIPPED_LINE="$(sed -n 's/^STRIPPED: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
DEBUG_LINE="$(sed -n 's/^DEBUG_INFO: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
RUST_LINE="$(sed -n 's/^RUST_CONFIDENCE: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
EVIDENCE_LINE="$(sed -n 's/^RUST_EVIDENCE: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
EXPORTS_LINE="$(sed -n 's/^EXPORTED_SYMBOLS: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
IMPORTS_LINE="$(sed -n 's/^IMPORTED_SYMBOL_HINTS: //p' "$OUTPUT_DIR/triage/summary.txt" | head -1)"
GHIDRA_STATE_LINE="$(sed -n 's/^STATE: //p' "$OUTPUT_DIR/decompiled/ghidra/status.txt" 2>/dev/null | head -1)"
GHIDRA_RUNNER_HEARTBEAT_LINE="$(sed -n 's/^RUNNER_HEARTBEAT_AT: //p' "$OUTPUT_DIR/decompiled/ghidra/runner-status.txt" 2>/dev/null | head -1)"
GHIDRA_RUNNER_PHASE_LINE="$(sed -n 's/^RUNNER_PHASE: //p' "$OUTPUT_DIR/decompiled/ghidra/runner-status.txt" 2>/dev/null | head -1)"
GHIDRA_WRITTEN_LINE="$(sed -n 's/^PSEUDOCODE_FILES_WRITTEN: //p' "$OUTPUT_DIR/decompiled/ghidra/summary.txt" 2>/dev/null | head -1)"
GHIDRA_PROCESSED_LINE="$(sed -n 's/^FUNCTIONS_PROCESSED: //p' "$OUTPUT_DIR/decompiled/ghidra/summary.txt" 2>/dev/null | head -1)"
GHIDRA_LAST_ERROR_LINE="$(sed -n 's/^LAST_ERROR: //p' "$OUTPUT_DIR/decompiled/ghidra/summary.txt" 2>/dev/null | head -1)"
GHIDRA_CONSTRUCTOR_WARNINGS_LINE="$(sed -n 's/^CONSTRUCTOR_RESOLVE_WARNINGS: //p' "$OUTPUT_DIR/decompiled/ghidra/warning-summary.txt" 2>/dev/null | head -1)"
GHIDRA_TOP_WARNING_FUNCTION_LINE="$(sed -n 's/^TOP_CONSTRUCTOR_WARNING_FUNCTION: //p' "$OUTPUT_DIR/decompiled/ghidra/warning-summary.txt" 2>/dev/null | head -1)"
GHIDRA_TOP_WARNING_FUNCTION_COUNT_LINE="$(sed -n 's/^TOP_CONSTRUCTOR_WARNING_FUNCTION_COUNT: //p' "$OUTPUT_DIR/decompiled/ghidra/warning-summary.txt" 2>/dev/null | head -1)"

{
  echo "## Rust reverse output"
  echo
  echo "- **Target**: \`${ORIGINAL_TARGET_LINE:-$TARGET_LINE}\`"
  if [[ -n "$ANALYSIS_TARGET_LINE" && "$ANALYSIS_TARGET_LINE" != "${ORIGINAL_TARGET_LINE:-$TARGET_LINE}" ]]; then
    echo "- **Analysis target**: \`${ANALYSIS_TARGET_LINE}\`"
  fi
  if [[ "$MACHO_UNIVERSAL_LINE" == "yes" ]]; then
    echo "- **Mach-O slices**: \`${MACHO_ARCHES_LINE:-unknown}\`"
    echo "- **Selected slice**: \`${MACHO_SELECTED_ARCH_LINE:-unknown}\`"
  fi
  echo "- **Format / arch**: \`${FORMAT:-unknown} ${ARCH_LINE:-unknown}\`"
  echo "- **Stripped**: \`${STRIPPED_LINE:-unknown}\`"
  echo "- **Debug info**: \`${DEBUG_LINE:-unknown}\`"
  echo "- **Rust confidence**: \`${RUST_LINE:-unknown}\`"
  echo "- **Rust evidence**: \`${EVIDENCE_LINE:-none}\`"
  echo "- **Export count**: \`${EXPORTS_LINE:-0}\`"
  echo "- **Import hint count**: \`${IMPORTS_LINE:-0}\`"
  echo "- **Ghidra pseudocode export**: \`${GHIDRA_STATUS}\`"
  if [[ -n "$GHIDRA_STATE_LINE" ]]; then
    echo "- **Ghidra export state**: \`${GHIDRA_STATE_LINE}\`"
  fi
  if [[ -n "$GHIDRA_RUNNER_PHASE_LINE" ]]; then
    echo "- **Ghidra runner phase**: \`${GHIDRA_RUNNER_PHASE_LINE}\`"
  fi
  if [[ -n "$GHIDRA_RUNNER_HEARTBEAT_LINE" ]]; then
    echo "- **Ghidra runner heartbeat**: \`${GHIDRA_RUNNER_HEARTBEAT_LINE}\`"
  fi
  if [[ -n "$GHIDRA_PROCESSED_LINE" ]]; then
    echo "- **Ghidra functions processed**: \`${GHIDRA_PROCESSED_LINE}\`"
  fi
  if [[ -n "$GHIDRA_WRITTEN_LINE" ]]; then
    echo "- **Ghidra pseudocode files**: \`${GHIDRA_WRITTEN_LINE}\`"
  fi
  if [[ -n "$GHIDRA_LAST_ERROR_LINE" ]]; then
    echo "- **Ghidra last error**: \`${GHIDRA_LAST_ERROR_LINE}\`"
  fi
  if [[ -n "$GHIDRA_CONSTRUCTOR_WARNINGS_LINE" ]]; then
    echo "- **Ghidra constructor warnings**: \`${GHIDRA_CONSTRUCTOR_WARNINGS_LINE}\`"
  fi
  if [[ -n "$GHIDRA_TOP_WARNING_FUNCTION_LINE" ]]; then
    echo "- **Top constructor-warning function**: \`${GHIDRA_TOP_WARNING_FUNCTION_LINE}\` (\`${GHIDRA_TOP_WARNING_FUNCTION_COUNT_LINE:-0}\`)"
  fi
  echo
  echo "## Generated artifacts"
  echo
  echo "- \`input/analysis-target.txt\`"
  echo "- \`triage/summary.txt\`"
  echo "- \`triage/strings.txt\`"
  echo "- \`triage/interesting-strings.txt\`"
  echo "- \`symbols/raw.txt\`"
  echo "- \`symbols/demangled.txt\`"
  echo "- \`symbols/namespaces.txt\`"
  echo "- \`symbols/imports.txt\`"
  echo "- \`symbols/exports.txt\`"
  echo "- \`reports/pattern-hits.txt\`"
  if [[ "$NO_DISASM" == false ]]; then
    echo "- \`disassembly/disassembly.txt\`"
  fi
  if [[ "$GHIDRA_STATUS" == "ok" ]]; then
    echo "- \`decompiled/ghidra/analysis-target.txt\`"
    echo "- \`decompiled/ghidra/runner-status.txt\`"
    echo "- \`decompiled/ghidra/status.txt\`"
    echo "- \`decompiled/ghidra/summary.txt\`"
    echo "- \`decompiled/ghidra/complete.marker\`"
    echo "- \`decompiled/ghidra/warning-summary.txt\`"
    echo "- \`decompiled/ghidra/functions.tsv\`"
    echo "- \`decompiled/ghidra/decompile-errors.tsv\`"
    echo "- \`decompiled/ghidra/functions/*.c\`"
  elif [[ "$GHIDRA_STATUS" == "partial" || "$GHIDRA_STATUS" == "interrupted" ]]; then
    echo "- Ghidra export produced partial output; inspect \`decompiled/ghidra/runner-status.txt\`, \`decompiled/ghidra/status.txt\`, \`decompiled/ghidra/functions.tsv\`, and \`decompiled/ghidra/decompile-errors.tsv\`"
  elif [[ "$GHIDRA_STATUS" == "missing" ]]; then
    echo "- Ghidra headless not available; \`decompiled/ghidra/\` was left empty"
  elif [[ "$GHIDRA_STATUS" == "failed" ]]; then
    echo "- Ghidra headless export failed; inspect \`decompiled/ghidra/runner-status.txt\`, \`decompiled/ghidra/status.txt\`, \`decompiled/ghidra/headless.log\`, and \`decompiled/ghidra/script.log\`"
  fi
  echo
  echo "## Candidate namespaces"
  echo
  if [[ -s "$OUTPUT_DIR/symbols/namespaces.txt" ]]; then
    head -10 "$OUTPUT_DIR/symbols/namespaces.txt" | sed 's/^/- /'
  else
    echo "- none recovered"
  fi
  echo
  echo "## Next artifact-driven moves"
  echo
  echo "- Review \`reports/pattern-hits.txt\` to separate runtime, panic, async, FFI, and network-adjacent clusters."
  if [[ "$GHIDRA_STATUS" == "ok" ]]; then
    echo "- Start from \`decompiled/ghidra/functions.tsv\` and the \`decompiled/ghidra/functions/*.c\` pseudocode files, then validate only the high-signal flows in Ghidra."
  elif [[ "$GHIDRA_STATUS" == "partial" || "$GHIDRA_STATUS" == "interrupted" ]]; then
    echo "- Resume or rerun the Ghidra export and do not treat the decompiler bundle as final until \`decompiled/ghidra/status.txt\` says \`STATE: completed\`."
  else
    echo "- Pivot from \`symbols/demangled.txt\` into Ghidra, IDA, or Binary Ninja and rename only the high-signal buckets first."
  fi
  echo "- Use \`symbols/imports.txt\` and \`triage/interesting-strings.txt\` to choose the first subsystem path for static or dynamic analysis."
} > "$OUTPUT_DIR/reports/summary.md"

echo
echo "OUTPUT_DIR: $OUTPUT_DIR"
echo "REPORT: $OUTPUT_DIR/reports/summary.md"
