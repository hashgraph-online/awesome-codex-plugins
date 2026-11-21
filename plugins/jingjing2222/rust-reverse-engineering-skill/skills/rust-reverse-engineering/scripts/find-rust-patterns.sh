#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: find-rust-patterns.sh <artifact-dir-or-demangled-file> [OPTIONS]

Search Rust reverse-engineering artifacts for high-signal buckets.

Arguments:
  <artifact-dir-or-demangled-file>   Reverse output directory from collect-artifacts.sh
                                     or a demangled symbols file

Options:
  --runtime      Search runtime namespaces only
  --ffi          Search FFI and interop patterns only
  --async        Search async/runtime-dispatch patterns only
  --network      Search network-adjacent crates and imports only
  --panic        Search panic and unwind patterns only
  --all          Search all buckets (default)
  -h, --help     Show this help message
EOF
  exit 0
}

INPUT=""
SEARCH_RUNTIME=false
SEARCH_FFI=false
SEARCH_ASYNC=false
SEARCH_NETWORK=false
SEARCH_PANIC=false
SEARCH_ALL=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runtime) SEARCH_RUNTIME=true; SEARCH_ALL=false; shift ;;
    --ffi) SEARCH_FFI=true; SEARCH_ALL=false; shift ;;
    --async) SEARCH_ASYNC=true; SEARCH_ALL=false; shift ;;
    --network) SEARCH_NETWORK=true; SEARCH_ALL=false; shift ;;
    --panic) SEARCH_PANIC=true; SEARCH_ALL=false; shift ;;
    --all) SEARCH_ALL=true; shift ;;
    -h|--help) usage ;;
    -*) echo "Error: Unknown option $1" >&2; usage ;;
    *) INPUT="$1"; shift ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "Error: No artifact directory or symbols file specified." >&2
  usage
fi

DEMANGLED_FILE=""
STRINGS_FILE=""
IMPORTS_FILE=""

if [[ -d "$INPUT" ]]; then
  DEMANGLED_FILE="$INPUT/symbols/demangled.txt"
  STRINGS_FILE="$INPUT/triage/strings.txt"
  IMPORTS_FILE="$INPUT/symbols/imports.txt"
else
  DEMANGLED_FILE="$INPUT"
fi

if [[ ! -f "$DEMANGLED_FILE" ]]; then
  echo "Error: demangled symbols file not found: $DEMANGLED_FILE" >&2
  exit 1
fi

section() {
  echo
  echo "==== $1 ===="
  echo
}

run_file_grep() {
  local file="$1"
  local pattern="$2"
  if [[ -f "$file" ]]; then
    grep -Eni "$pattern" "$file" || true
  fi
}

if [[ "$SEARCH_ALL" == true || "$SEARCH_RUNTIME" == true ]]; then
  section "Runtime namespaces"
  run_file_grep "$DEMANGLED_FILE" '(^|[^A-Za-z0-9_])(core|alloc|std|hashbrown|panic_unwind|compiler_builtins)::'
fi

if [[ "$SEARCH_ALL" == true || "$SEARCH_FFI" == true ]]; then
  section "FFI and interop patterns"
  run_file_grep "$DEMANGLED_FILE" '(ffi|cxx|bindgen|JNI_OnLoad|Java_[A-Za-z0-9_]+|objc|swift_|com::apple|windows::Win32)'
  run_file_grep "$STRINGS_FILE" '(JNI_OnLoad|Java_[A-Za-z0-9_]+|objc_msgSend|dlopen|dlsym|CFBundle|LoadLibrary|GetProcAddress)'
  run_file_grep "$IMPORTS_FILE" '(objc|dlopen|dlsym|LoadLibrary|GetProcAddress|JNI)'
fi

if [[ "$SEARCH_ALL" == true || "$SEARCH_ASYNC" == true ]]; then
  section "Async and dispatcher patterns"
  run_file_grep "$DEMANGLED_FILE" '(tokio|futures|poll|core::task|wake_by_ref|RawWaker|async)'
  run_file_grep "$STRINGS_FILE" '(tokio|futures|poll|waker|async)'
fi

if [[ "$SEARCH_ALL" == true || "$SEARCH_NETWORK" == true ]]; then
  section "Network and IPC patterns"
  run_file_grep "$DEMANGLED_FILE" '(reqwest|hyper|tonic|prost|mio|socket2|rustls|openssl|native_tls|ureq|grpc|serde_json)'
  run_file_grep "$STRINGS_FILE" '(https?://|reqwest|hyper|grpc|protobuf|socket|tls|openssl)'
  run_file_grep "$IMPORTS_FILE" '(connect|send|recv|socket|SSL_|tls|CFNetwork|WinHTTP|libcurl)'
fi

if [[ "$SEARCH_ALL" == true || "$SEARCH_PANIC" == true ]]; then
  section "Panic and unwind patterns"
  run_file_grep "$DEMANGLED_FILE" '(panic|begin_unwind|core::panicking|backtrace|abort)'
  run_file_grep "$STRINGS_FILE" '(rust_begin_unwind|panic|backtrace|abort)'
fi

echo
echo "=== Search complete ==="
