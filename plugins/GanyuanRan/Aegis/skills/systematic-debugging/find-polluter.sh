#!/usr/bin/env bash
# Linear scan of test invocations for unwanted files/state.
# Usage: bash ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: bash ./find-polluter.sh '.git' 'src/*.test.ts'
# Patterns use find -path: * also matches directory separators.
# Exit: 0 = no pollution observed; 1 = polluter found; 2 = inconclusive.

set -e

if [ $# -ne 2 ]; then
  echo "Usage: bash $0 <file_to_check> <test_pattern>"
  echo "Example: bash $0 '.git' 'src/*.test.ts'"
  exit 2
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"
case "$TEST_PATTERN" in
  /*) echo "Use a test pattern relative to the current directory"; exit 2 ;;
  ./*) ;;
  *) TEST_PATTERN="./$TEST_PATTERN" ;;
esac

if [ -e "$POLLUTION_CHECK" ] || [ -L "$POLLUTION_CHECK" ]; then
  echo "Inconclusive: pollution already exists: $POLLUTION_CHECK (preserved)"
  exit 2
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "Inconclusive: npm is unavailable"
  exit 2
fi

echo "🔍 Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo ""

# Keep paths intact and check discovery itself before claiming evidence.
TEST_LIST=$(mktemp) || exit 2
trap 'rm -f -- "$TEST_LIST"' EXIT
if ! find . -type f -path "$TEST_PATTERN" -print0 > "$TEST_LIST"; then
  echo "Inconclusive: test discovery failed"
  exit 2
fi
TEST_FILES=()
while IFS= read -r -d '' TEST_FILE; do
  TEST_FILES+=("$TEST_FILE")
done < "$TEST_LIST"
TOTAL=${#TEST_FILES[@]}

echo "Found $TOTAL test files"
echo ""
if [ "$TOTAL" -eq 0 ]; then
  echo "Inconclusive: no tests matched"
  exit 2
fi

COUNT=0
FAILED=0
for TEST_FILE in "${TEST_FILES[@]}"; do
  COUNT=$((COUNT + 1))

  if [ -e "$POLLUTION_CHECK" ] || [ -L "$POLLUTION_CHECK" ]; then
    echo "Inconclusive: pollution appeared between invocations (preserved)"
    exit 2
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  # Run the test
  STATUS=0
  npm test -- "$TEST_FILE" > /dev/null 2>&1 || STATUS=$?

  # Check if pollution appeared
  if [ -e "$POLLUTION_CHECK" ] || [ -L "$POLLUTION_CHECK" ]; then
    echo ""
    echo "FOUND POLLUTER! (invocation exit $STATUS)"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "Pollution details:"
    ls -ld -- "$POLLUTION_CHECK" || true
    echo ""
    echo "To investigate:"
    printf '  npm test -- %q\n' "$TEST_FILE"
    printf '  cat -- %q\n' "$TEST_FILE"
    exit 1
  fi
  if [ "$STATUS" -ne 0 ]; then
    FAILED=$((FAILED + 1))
    echo "Invocation returned $STATUS without observed pollution: $TEST_FILE"
  fi
done

echo ""
if [ "$FAILED" -gt 0 ]; then
  echo "Inconclusive: $FAILED of $TOTAL invocations failed; inspect runner output"
  exit 2
fi
echo "No new pollution observed in $COUNT test invocations"
exit 0
