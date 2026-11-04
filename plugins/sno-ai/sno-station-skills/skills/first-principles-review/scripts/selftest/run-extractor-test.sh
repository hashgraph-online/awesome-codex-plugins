#!/usr/bin/env bash
export PYTHONDONTWRITEBYTECODE=1
set -Eeuo pipefail

selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
fixtures="$selftest_dir/fixtures"
extractor="$skill_dir/scripts/extract-prd-handoff.py"
valid_report="$fixtures/valid-report.md"
expected_handoff="$fixtures/expected-handoff.json"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT

expect_rejection() {
  local label="$1"
  shift
  if "$@"; then
    printf 'FAIL: %s was accepted\n' "$label" >&2
    exit 1
  fi
  printf 'PASS: %s rejected\n' "$label"
}

for required in "$extractor" "$valid_report" "$expected_handoff"; do
  [[ -f "$required" ]] || { printf 'missing required file: %s\n' "$required" >&2; exit 1; }
done

observed_handoff="$temporary/observed-handoff.json"
python3 "$extractor" "$valid_report" >"$observed_handoff"
python3 - "$expected_handoff" "$observed_handoff" <<'PY'
import json
import pathlib
import sys

expected = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
observed = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
if observed != expected:
    raise SystemExit("extracted handoff differs from expected-handoff.json")
PY
printf 'PASS: valid-report extraction exactly matches expected handoff data\n'

malformed="$temporary/malformed-handoff.md"
multiple="$temporary/multiple-handoff.md"
python3 - "$valid_report" "$malformed" "$multiple" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
pathlib.Path(sys.argv[2]).write_text(
    source.replace('{"true_problem"', '{"true_problem":', 1),
    encoding="utf-8",
)
pathlib.Path(sys.argv[3]).write_text(
    source + '\n```json\n{}\n```\n',
    encoding="utf-8",
)
PY
expect_rejection "malformed handoff block" python3 "$extractor" "$malformed"
expect_rejection "multiple handoff blocks" python3 "$extractor" "$multiple"

printf 'run-extractor-test passed\n'
