#!/usr/bin/env bash
# Vibe Pre-Scan: Fast static detection for 7 failure patterns
# Usage: prescan.sh <target>
#   target: recent | all | <directory> | <file>

set -euo pipefail

TARGET="${1:-recent}"

# Validate TARGET to prevent argument injection
if [[ "$TARGET" =~ ^- ]]; then
    echo "Error: TARGET cannot start with a dash (prevents argument injection)" >&2
    exit 1
fi
if [[ "$TARGET" != "recent" && "$TARGET" != "all" && ! -e "$TARGET" ]]; then
    echo "Error: TARGET '$TARGET' does not exist" >&2
    exit 1
fi

# File filtering (exclude generated code, build artifacts, test fixtures)
filter_files() {
  grep -v '__pycache__\|\.venv\|venv/\|node_modules\|\.git/\|test_fixtures\|/fixtures/\|\.eggs\|egg-info\|/dist/\|/build/\|\.tox\|\.mypy_cache\|\.pytest_cache' \
  | grep -v '\.gen\.go$\|zz_generated\|_generated\.go$\|\.pb\.go$\|mock_.*\.go$\|/generated/\|/gen/\|deepcopy'
}

# Resolve target to file lists (Python, Go, Bash)
case "$TARGET" in
  recent)
    PY_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep '\.py$' | filter_files || true)
    GO_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep '\.go$' | filter_files || true)
    SH_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep '\.sh$' | filter_files || true)
    MODE="Recent"
    ;;
  all)
    PY_FILES=$(find . -name "*.py" -type f 2>/dev/null | filter_files | grep -v 'test_' || true)
    GO_FILES=$(find . -name "*.go" -type f 2>/dev/null | filter_files | grep -v '_test\.go$' || true)
    SH_FILES=$(find . -name "*.sh" -type f 2>/dev/null | filter_files || true)
    MODE="All"
    ;;
  *)
    if [ -d "$TARGET" ]; then
      PY_FILES=$(find "$TARGET" -name "*.py" -type f 2>/dev/null | filter_files || true)
      GO_FILES=$(find "$TARGET" -name "*.go" -type f 2>/dev/null | filter_files || true)
      SH_FILES=$(find "$TARGET" -name "*.sh" -type f 2>/dev/null | filter_files || true)
      MODE="Dir"
    elif [ -f "$TARGET" ]; then
      case "$TARGET" in
        *.py) PY_FILES="$TARGET"; GO_FILES=""; SH_FILES="" ;;
        *.go) GO_FILES="$TARGET"; PY_FILES=""; SH_FILES="" ;;
        *.sh) SH_FILES="$TARGET"; PY_FILES=""; GO_FILES="" ;;
        *) PY_FILES="$TARGET"; GO_FILES=""; SH_FILES="" ;;
      esac
      MODE="File"
    else
      echo "ERROR: Target not found: $TARGET" >&2
      exit 1
    fi
    ;;
esac

# Combine for backwards compatibility
FILES="$PY_FILES"
[ -n "$GO_FILES" ] && FILES=$(printf "%s\n%s" "$FILES" "$GO_FILES")
[ -n "$SH_FILES" ] && FILES=$(printf "%s\n%s" "$FILES" "$SH_FILES")

# Count files (handle empty strings properly)
count_lines() {
  local input="$1"
  [ -z "$input" ] && echo 0 && return
  echo "$input" | wc -l | tr -d ' '
}
PY_COUNT=$(count_lines "$PY_FILES")
GO_COUNT=$(count_lines "$GO_FILES")
SH_COUNT=$(count_lines "$SH_FILES")
FILE_COUNT=$((PY_COUNT + GO_COUNT + SH_COUNT))
if [ "$FILE_COUNT" -eq 0 ]; then
  echo "No files found for target: $TARGET"
  exit 0
fi

echo "Pre-Scan Target: $TARGET"
echo "Mode: $MODE | Files: $FILE_COUNT (py:$PY_COUNT go:$GO_COUNT sh:$SH_COUNT)"
echo ""

# Initialize counters
P1_COUNT=0
P2_COUNT=0
P4_COUNT=0
P5_COUNT=0
P8_COUNT=0
P9_COUNT=0
P12_COUNT=0

# P1: Phantom Modifications (CRITICAL)
# Committed lines not in current file
echo "[P1] Phantom Modifications"
if [ "$TARGET" = "recent" ]; then
  for file in $FILES; do
    [ -f "$file" ] || continue
    while IFS= read -r line; do
      clean=$(echo "$line" | sed 's/^+//' | xargs)
      if [ ${#clean} -gt 10 ] && ! grep -qF "$clean" "$file" 2>/dev/null; then
        echo "  - $file: Committed line missing: \"${clean:0:50}...\""
        P1_COUNT=$((P1_COUNT + 1))
      fi
    done < <(git show HEAD -- "$file" 2>/dev/null | grep '^+[^+]' || true)
  done
fi
echo "  $P1_COUNT findings"

# P2: Hardcoded Secrets (CRITICAL)
# Uses path-based filtering to exclude test directories
echo ""
echo "[P2] Hardcoded Secrets"
for file in $FILES; do
  [ -f "$file" ] || continue
  # Skip test directories
  case "$file" in
    */test/*|*/tests/*|*_test.*|*/example/*|*/examples/*|*.example.*) continue ;;
  esac
  while IFS= read -r match; do
    line_num=$(echo "$match" | cut -d: -f1)
    echo "  - $file:$line_num: Possible hardcoded secret"
    P2_COUNT=$((P2_COUNT + 1))
  done < <(grep -n -E "(password|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]" "$file" 2>/dev/null | head -5 || true)
done
echo "  $P2_COUNT findings"

# P4: Invisible Undone (HIGH)
# Detects: unfinished work markers, commented-out code
echo ""
echo "[P4] Invisible Undone"
for file in $FILES; do
  [ -f "$file" ] || continue
  # TODO/FIXME markers
  while IFS= read -r match; do
    line_num=$(echo "$match" | cut -d: -f1)
    echo "  - $file:$line_num: TODO marker"
    P4_COUNT=$((P4_COUNT + 1))
  done < <(grep -n "TODO\|FIXME\|XXX\|HACK" "$file" 2>/dev/null | head -3 || true)
  # Commented code
  while IFS= read -r match; do
    line_num=$(echo "$match" | cut -d: -f1)
    echo "  - $file:$line_num: Commented code"
    P4_COUNT=$((P4_COUNT + 1))
  done < <(grep -n "^\s*#\s*\(def \|class \|if \|for \)" "$file" 2>/dev/null | head -2 || true)
done
echo "  $P4_COUNT findings"

# P5: Eldritch Horror (HIGH)
# Complexity CC > 15 or function > 50 lines
echo ""
echo "[P5] Eldritch Horror"

# Python: radon for cyclomatic complexity
if [ -n "$PY_FILES" ]; then
  if command -v radon &>/dev/null; then
    for file in $PY_FILES; do
      [ -f "$file" ] || continue
      while IFS= read -r line; do
        cc=$(echo "$line" | grep -oE '\([0-9]+\)' | tr -d '()')
        if [ -n "$cc" ] && [ "$cc" -gt 15 ]; then
          func=$(echo "$line" | awk '{print $3}')
          echo "  - $file: $func CC=$cc (py)"
          P5_COUNT=$((P5_COUNT + 1))
        fi
      done < <(radon cc "$file" -s -n E 2>/dev/null | grep -E "^\s*[EF]\s+[0-9]+" || true)
    done
  else
    echo "  WARNING: radon not installed (Python CC skipped)"
  fi
fi

# Go: gocyclo for cyclomatic complexity
if [ -n "$GO_FILES" ]; then
  if command -v gocyclo &>/dev/null; then
    for file in $GO_FILES; do
      [ -f "$file" ] || continue
      while IFS= read -r line; do
        # gocyclo output: "15 pkg funcName file.go:42:1"
        cc=$(echo "$line" | awk '{print $1}')
        func=$(echo "$line" | awk '{print $3}')
        loc=$(echo "$line" | awk '{print $4}')
        if [ -n "$cc" ] && [ "$cc" -gt 15 ]; then
          echo "  - $loc: $func CC=$cc (go)"
          P5_COUNT=$((P5_COUNT + 1))
        fi
      done < <(gocyclo -over 15 "$file" 2>/dev/null || true)
    done
  else
    echo "  WARNING: gocyclo not installed (Go CC skipped)"
  fi
fi

# Python: Function length > 50 lines
for file in $PY_FILES; do
  [ -f "$file" ] || continue
  python3 -c '
import ast, sys
fname = sys.argv[1]
try:
    with open(fname) as f: tree = ast.parse(f.read())
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and hasattr(n, "end_lineno"):
            lines = n.end_lineno - n.lineno + 1
            if lines > 50: print(f"  - {fname}:{n.lineno}: {n.name}() is {lines} lines (py)")
except: pass
' "$file" 2>/dev/null || true
done

# Go: Function length > 50 lines (simple heuristic)
# Limitation: This awk-based parser only detects `func ` at line start and `}` alone on a line.
# Multi-line signatures, nested braces, or unusual formatting may cause false positives/negatives.
# For production Go codebases, consider using gocyclo or go/ast for accurate metrics.
for file in $GO_FILES; do
  [ -f "$file" ] || continue
  awk '
    /^func / { fname=$0; start=NR; in_func=1 }
    in_func && /^}$/ {
      lines = NR - start + 1
      if (lines > 50) {
        # Extract function name
        match(fname, /func[[:space:]]+(\([^)]+\)[[:space:]]+)?([a-zA-Z_][a-zA-Z0-9_]*)/, arr)
        print "  - '"$file"':" start ": " arr[2] "() is " lines " lines (go)"
      }
      in_func=0
    }
  ' "$file" 2>/dev/null || true
done
echo "  $P5_COUNT findings"

# P8: Cargo Cult Error Handling (HIGH)
# Empty except, pass-only handlers, bare except
echo ""
echo "[P8] Cargo Cult Error Handling"

# Python: except:pass, bare except
for file in $PY_FILES; do
  [ -f "$file" ] || continue
  python3 -c '
import ast, sys
fname = sys.argv[1]
try:
    with open(fname) as f: tree = ast.parse(f.read())
    for n in ast.walk(tree):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                if len(h.body) == 1 and isinstance(h.body[0], ast.Pass):
                    print(f"  - {fname}:{h.lineno}: except: pass (swallowed) (py)")
                if h.type is None:
                    print(f"  - {fname}:{h.lineno}: bare except (catches SystemExit) (py)")
except: pass
' "$file" 2>/dev/null || true
done

# Bash: shellcheck for error handling issues
if [ -n "$SH_FILES" ]; then
  if command -v shellcheck &>/dev/null; then
    for file in $SH_FILES; do
      [ -f "$file" ] || continue
      # SC2181: Check exit code directly, not via $?
      # SC2086: Double quote to prevent globbing/splitting
      # SC2046: Quote to prevent word splitting
      # SC2155: Declare and assign separately to avoid masking return values
      while IFS= read -r line; do
        echo "  - $line (sh)"
        P8_COUNT=$((P8_COUNT + 1))
      done < <(shellcheck -f gcc -S warning "$file" 2>/dev/null | head -5 || true)
    done
  else
    echo "  WARNING: shellcheck not installed (Bash checks skipped)"
  fi
fi
echo "  $P8_COUNT findings"

# P9: Documentation Phantom (MEDIUM)
# Docstrings claiming behavior not implemented (Python only)
echo ""
echo "[P9] Documentation Phantom"
for file in $PY_FILES; do
  [ -f "$file" ] || continue
  python3 -c '
import ast, re, sys
fname = sys.argv[1]
try:
    with open(fname) as f: src = f.read()
    tree = ast.parse(src)
    PATTERNS = [
        (r"\bvalidates?\b", ["raise", "ValueError", "return False"]),
        (r"\bensures?\b", ["assert", "raise"]),
        (r"\bencrypts?\b", ["crypto", "cipher"]),
        (r"\bauthenticat", ["token", "password"]),
        (r"\bsanitiz", ["escape", "strip"])
    ]
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
                doc = str(n.body[0].value.value).lower()
                fsrc = (ast.get_source_segment(src, n) or "").lower()
                for pat, impl in PATTERNS:
                    if re.search(pat, doc) and not any(i in fsrc for i in impl):
                        print(f"  - {fname}:{n.lineno}: {n.name}() docstring mismatch")
                        break
except: pass
' "$file" 2>/dev/null || true
done
echo "  $P9_COUNT findings"

# P12: Zombie Code (MEDIUM)
# Unused functions, unreachable code after return (Python only)
echo ""
echo "[P12] Zombie Code"
for file in $PY_FILES; do
  [ -f "$file" ] || continue
  python3 -c '
import ast, sys
fname = sys.argv[1]
try:
    with open(fname) as f: src = f.read()
    tree = ast.parse(src)
    defined, called = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            defined.add(n.name)
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name): called.add(n.func.id)
            elif isinstance(n.func, ast.Attribute): called.add(n.func.attr)
    for fn in (defined - called):
        if fn not in ("main", "setup", "teardown") and not fn.startswith("test_"):
            print(f"  - {fname}: {fn}() may be unused")
    # Unreachable code
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for i, s in enumerate(n.body[:-1]):
                if isinstance(s, (ast.Return, ast.Raise)) and n.body[i+1:]:
                    nxt = n.body[i+1]
                    if not (isinstance(nxt, ast.Expr) and isinstance(getattr(nxt, "value", None), ast.Constant)):
                        print(f"  - {fname}:{nxt.lineno}: Unreachable after return/raise")
except: pass
' "$file" 2>/dev/null || true
done
echo "  $P12_COUNT findings"

# Summary
echo ""
echo "=============================================="
echo "Pre-Scan Results:"
CRITICAL=$((P1_COUNT + P2_COUNT))
HIGH=$((P4_COUNT + P5_COUNT + P8_COUNT))
MEDIUM=$((P9_COUNT + P12_COUNT))
TOTAL=$((CRITICAL + HIGH + MEDIUM))

echo "[P1] Phantom Modifications: $P1_COUNT findings"
echo "[P2] Hardcoded Secrets: $P2_COUNT findings"
echo "[P4] Invisible Undone: $P4_COUNT findings"
echo "[P5] Eldritch Horror: $P5_COUNT findings"
echo "[P8] Cargo Cult Error Handling: $P8_COUNT findings"
echo "[P9] Documentation Phantom: $P9_COUNT findings"
echo "[P12] Zombie Code: $P12_COUNT findings"
echo "----------------------------------------------"
echo "Summary: $TOTAL findings ($CRITICAL CRITICAL, $HIGH HIGH, $MEDIUM MEDIUM)"
echo ""

[ "$CRITICAL" -gt 0 ] && echo "CRITICAL: Fix P1, P2 immediately"
[ "$HIGH" -gt 0 ] && echo "HIGH: Review P4, P5, P8"
[ "$MEDIUM" -gt 0 ] && echo "MEDIUM: Consider P9, P12"
[ "$TOTAL" -eq 0 ] && echo "All clear - no violations"
echo "=============================================="

# Exit code based on findings
[ "$CRITICAL" -gt 0 ] && exit 2
[ "$HIGH" -gt 0 ] && exit 3
exit 0
