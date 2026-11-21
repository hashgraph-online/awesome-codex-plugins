#!/usr/bin/env bash
set -u -o pipefail


export PYTHONDONTWRITEBYTECODE=1
selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
fixtures="$selftest_dir/fixtures"
source_skill="$skill_dir/SKILL.md"
codex_metadata="$skill_dir/agents/openai.yaml"
validator="$skill_dir/scripts/validate-report.py"
extractor="$skill_dir/scripts/extract-prd-handoff.py"
failures=0

fail() { echo "FAIL: $*" >&2; failures=$((failures + 1)); }
require_file() { [[ -f "$1" ]] || fail "missing required file: $1"; }

expect_success() {
  local label="$1"
  shift
  if ! "$@"; then
    fail "$label should succeed"
  fi
}

expect_failure() {
  local label="$1"
  shift
  if "$@"; then
    fail "$label should be rejected"
  fi
}

require_file "$source_skill"
require_file "$codex_metadata"
require_file "$validator"
require_file "$extractor"

if [[ -f "$source_skill" ]]; then
  grep -Fq "MANUAL-ONLY" "$source_skill" || fail "skill description must say MANUAL-ONLY"
  if grep -Eiq "placeholder|todo:.*implement|coming soon" "$source_skill"; then
    fail "skill source still contains a placeholder"
  fi
fi
if [[ -f "$codex_metadata" ]]; then
  grep -Eq 'allow_implicit_invocation:[[:space:]]*false' "$codex_metadata" || \
    fail "Codex metadata must disable implicit invocation"
fi

if [[ -f "$validator" && -f "$extractor" ]]; then
  temporary="$(mktemp -d)"
  trap 'rm -rf "$temporary"' EXIT
  expect_success "conforming report" python3 "$validator" "$fixtures/valid-report.md"

  python3 - "$fixtures/valid-report.md" "$temporary" <<'PY'
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
output = pathlib.Path(sys.argv[2])

def write(name, text):
    (output / name).write_text(text, encoding="utf-8")

write("missing-section.md", source.replace("## Falsifiers\n\n", ""))
write("unknown-disposition.md", source.replace("REFRAME", "APPROVE"))
write("empty-research.md", source.replace('"research_receipt":[{', '"research_receipt":[] , "discarded": [{'))
write("unresolved-recommendation.md", source.replace('"recommendation":"Use priority-based delivery before building a queue."', '"recommendation":""'))
write("malformed-json.md", source.replace('{"true_problem"', '{"true_problem":,'))
write("question-in-report.md", source.replace("high priority.\n\n## PRD Handoff", "high priority?\n\n## PRD Handoff"))
write("accept-url-with-query.txt", source.replace("high priority.\n\n## PRD Handoff", "high priority. See https://example.com/doc?page=2 for detail.\n\n## PRD Handoff"))
write("zero-handoff.md", source.replace('{"true_problem"', '{}\n<!-- discarded {"true_problem"'))
write("zero-work.md", source.replace("| `fixtures/target-prd.md:1-12` | The proposal assumes a queue and a universal ten-second target. | verified |", "No research was performed.").replace("| Ten seconds is required for every event | unproven | inversion | falsified for low-priority events |", "No premises were challenged."))
write("empty-premises.md", source.replace('"premises":[{', '"premises":[],"discarded":[{', 1))
write("split-empty-outcomes.md", source.replace('"disposition":"REFRAME"', '"disposition":"SPLIT"', 1))
write("split-one-outcome.md", source.replace('"disposition":"REFRAME"', '"disposition":"SPLIT"', 1).replace('"split_outcomes":[]', '"split_outcomes":["Only one outcome"]', 1))
write("non-split-outcomes.md", source.replace('"split_outcomes":[]', '"split_outcomes":["Unexpected split outcome"]', 1))
write("multiple-handoff.md", source + "\n```json\n{}\n```\n")
PY
  expect_success "URL with query string" python3 "$validator" "$temporary/accept-url-with-query.txt"
  for report in "$temporary"/*.md; do
    expect_failure "$(basename "$report")" python3 "$validator" "$report"
  done
  expect_success "scenario reports" bash "$selftest_dir/run-scenarios.sh"

  extracted="$temporary/extracted.json"
  if python3 "$extractor" "$fixtures/valid-report.md" >"$extracted"; then
    if ! python3 - "$fixtures/expected-handoff.json" "$extracted" <<'PY'
import json
import pathlib
import sys

expected = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
observed = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
if observed != expected:
    raise SystemExit("extracted JSON differs from the embedded handoff")
PY
    then
      fail "extractor must emit exactly the embedded handoff JSON"
    fi
  else
    fail "extractor should accept the conforming report"
  fi
  expect_failure "extractor malformed JSON" python3 "$extractor" "$temporary/malformed-json.md"
  expect_failure "extractor multiple handoff blocks" python3 "$extractor" "$temporary/multiple-handoff.md"
fi

for verifier in verify-workflow-policy.sh verify-manual-only.sh run-extractor-test.sh; do
  if ! output="$(bash "$selftest_dir/$verifier" 2>&1)"; then
    printf '%s\n' "$output" >&2
    fail "$verifier failed"
  fi
done

if (( failures > 0 )); then
  echo "self-test failed with $failures failure(s)" >&2
  exit 1
fi
echo "self-test passed"
