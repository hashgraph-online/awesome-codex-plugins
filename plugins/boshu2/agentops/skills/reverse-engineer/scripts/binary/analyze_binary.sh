#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: analyze_binary.sh <binary_path> <out_dir>" >&2
  exit 2
fi

BIN="$1"
OUT="$2"
mkdir -p "$OUT"

if [[ ! -f "$BIN" ]]; then
  echo "error: binary not found: $BIN" >&2
  exit 2
fi

{
  echo "# Binary Analysis (Best-Effort)"
  echo
  echo "- Target: \`$BIN\`"
  echo "- Generated: $(date +%F)"
  echo
  echo "## file(1)"
  echo
  if command -v file >/dev/null 2>&1; then
    file "$BIN" || true
  else
    echo "_file not available_"
  fi
  echo
  echo "## Linked Libraries (best-effort)"
  echo
  if command -v otool >/dev/null 2>&1; then
    otool -L "$BIN" 2>/dev/null || true
  elif command -v ldd >/dev/null 2>&1; then
    ldd "$BIN" 2>/dev/null || true
  else
    echo "_otool/ldd not available_"
  fi
  echo
  echo "## Language Heuristics (best-effort)"
  echo
  if command -v strings >/dev/null 2>&1; then
    # Cache strings output to a temp file for multiple scans
    _STRINGS_FILE=$(mktemp)
    trap 'rm -f "$_STRINGS_FILE"' EXIT
    strings -a "$BIN" 2>/dev/null >"$_STRINGS_FILE"

    # Helper: search strings file with rg falling back to grep -E
    _str_match() {
      local pattern="$1"
      if command -v rg >/dev/null 2>&1; then
        rg -m 1 "$pattern" "$_STRINGS_FILE" 2>/dev/null
      else
        grep -E -m 1 "$pattern" "$_STRINGS_FILE" 2>/dev/null
      fi
    }

    # --- Go detection (broad markers for stripped binaries) ---
    GO_DETECTED=false
    GO_MARKER=""
    # Original markers (unstripped binaries)
    if _str_match 'runtime\.morestack|go\.buildid|Go build ID|type\.\*runtime\.' >/dev/null 2>&1; then
      GO_DETECTED=true; GO_MARKER="Go runtime markers"
    # Broader markers for stripped binaries (version strings, GOROOT, module paths)
    elif _str_match 'go1\.[0-9]|GOROOT|github\.com/|golang\.org/' >/dev/null 2>&1; then
      GO_DETECTED=true; GO_MARKER="Go version/module strings"
    fi

    # --- Python detection ---
    PYTHON_DETECTED=false
    if _str_match '__pycache__|\.pyc|Py_Initialize|libpython|python[0-9]\.[0-9]' >/dev/null 2>&1; then
      PYTHON_DETECTED=true
    fi

    # --- Report language ---
    if $GO_DETECTED && $PYTHON_DETECTED; then
      echo "- Likely language/runtime: Go + Python (Go binary embedding Python code)"
      echo "  - Go detection: $GO_MARKER"
    elif $GO_DETECTED; then
      echo "- Likely language/runtime: Go (heuristic: $GO_MARKER)"
    elif $PYTHON_DETECTED; then
      echo "- Likely language/runtime: Python (heuristic: Python runtime markers in strings)"
    else
      echo "- Likely language/runtime: unknown (no Go or Python markers found)"
    fi

    # --- Go details (version, module, packages) ---
    if $GO_DETECTED; then
      echo
      echo "### Go Details"
      echo
      # Go version string (e.g. "go1.23.4") — match lines that ARE the version
      _go_ver=$({
        if command -v rg >/dev/null 2>&1; then
          rg -m 1 -o '^go1\.[0-9]+\.[0-9]+$' "$_STRINGS_FILE" 2>/dev/null
        else
          grep -E -m 1 '^go1\.[0-9]+\.[0-9]+$' "$_STRINGS_FILE" 2>/dev/null
        fi
      } || true)
      if [[ -n "$_go_ver" ]]; then
        echo "- Go version: \`$_go_ver\`"
      else
        echo "- Go version: _not found (stripped)_"
      fi
      # Module path — prefer github.com/gitlab.com/golang.org paths first
      _go_mod=$({
        if command -v rg >/dev/null 2>&1; then
          rg -m 1 -o '^(github|gitlab|bitbucket)\.com/[^\s]+' "$_STRINGS_FILE" 2>/dev/null \
          || rg -m 1 -o '^golang\.org/[^\s]+' "$_STRINGS_FILE" 2>/dev/null \
          || rg -m 1 -o '^[a-z][a-z0-9.-]+\.[a-z]{2,}/[^\s]+' "$_STRINGS_FILE" 2>/dev/null
        else
          grep -E -m 1 -o '^(github|gitlab|bitbucket)\.com/[^ ]+' "$_STRINGS_FILE" 2>/dev/null \
          || grep -E -m 1 -o '^golang\.org/[^ ]+' "$_STRINGS_FILE" 2>/dev/null \
          || grep -E -m 1 -o '^[a-z][a-z0-9.-]+\.[a-z]{2,}/[^ ]+' "$_STRINGS_FILE" 2>/dev/null
        fi
      } || true)
      if [[ -n "$_go_mod" ]]; then
        echo "- Module path: \`$_go_mod\`"
      else
        echo "- Module path: _not found_"
      fi
      # Internal package count (unique Go module-style paths)
      _go_pkgs=$({
        if command -v rg >/dev/null 2>&1; then
          rg -o '^(github|gitlab|bitbucket)\.com/[^\s]+|^golang\.org/[^\s]+' "$_STRINGS_FILE" 2>/dev/null
        else
          grep -E -o '^(github|gitlab|bitbucket)\.com/[^ ]+|^golang\.org/[^ ]+' "$_STRINGS_FILE" 2>/dev/null
        fi
      } | sort -u | wc -l || echo 0)
      echo "- Internal packages (approx): ${_go_pkgs##* }"
    fi
  else
    echo "- strings not available; cannot run heuristics"
  fi
  echo
  echo "## Embedded Archive Signatures (ZIP, best-effort)"
  echo
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$BIN" <<'PY'
import sys
from pathlib import Path

p = Path(sys.argv[1])
data = p.read_bytes()

sig = b"PK\x03\x04"
hits = []
start = 0
while True:
    i = data.find(sig, start)
    if i < 0:
        break
    hits.append(i)
    start = i + 1

print(f"- ZIP local header occurrences: {len(hits)}")
for i in hits[:10]:
    print(f"  - offset: {i}")
if len(hits) > 10:
    print("  - ...")
PY
  else
    echo "_python3 not available_"
  fi
} >"$OUT/binary-analysis.md"

# Raw strings (kept under tmp out dir; do not copy into output_dir by default).
if command -v strings >/dev/null 2>&1; then
  strings -a "$BIN" 2>/dev/null | head -2000 >"$OUT/strings.head.txt" || true
  if command -v rg >/dev/null 2>&1; then
    strings -a "$BIN" 2>/dev/null | rg -n -S 'mcp|prompt|system|tool|openai|anthropic|claude' >"$OUT/strings.ai-hits.txt" 2>/dev/null || true
  else
    strings -a "$BIN" 2>/dev/null | grep -E -in 'mcp|prompt|system|tool|openai|anthropic|claude' >"$OUT/strings.ai-hits.txt" 2>/dev/null || true
  fi
fi

# Optional disassembly snippet (bounded). Keep under tmp out dir; do not paste into reports by default.
if command -v otool >/dev/null 2>&1; then
  otool -tvV "$BIN" 2>/dev/null | head -500 >"$OUT/disassembly.head.txt" || true
elif command -v objdump >/dev/null 2>&1; then
  objdump -d "$BIN" 2>/dev/null | head -500 >"$OUT/disassembly.head.txt" || true
fi
