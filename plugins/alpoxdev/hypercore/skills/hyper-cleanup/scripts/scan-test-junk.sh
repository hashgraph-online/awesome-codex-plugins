#!/usr/bin/env bash
# Scan an explicit set of test files for the junk classes this package's test rule lists.
#
# Prints `<path>:<line>:<CODE>: <detail>` per finding, or one JSON object with --json.
# Read-only: it never writes a target file and never runs a test. A finding is a
# candidate, never an automatic cut: the proof each class needs is in the test rule.
set -euo pipefail

SJ_USAGE='Usage: bash scan-test-junk.sh <path> [path ...] [--json]
       bash scan-test-junk.sh --self-test
       bash scan-test-junk.sh --help

<path>      a test file, or a directory searched for *.test.*, *.spec.*, *_test.*,
            test_*.py, *_spec.rb, and *Test.java. The scan never widens past the
            paths it is given.

--json      print one JSON object instead of finding lines.
--self-test build a throwaway fixture set, prove every junk class is reported and a
            clean fixture stays silent, then print {"ok":true,...}.

Codes: FOCUSED_TEST, SKIPPED_TEST, FIXED_SLEEP, SELF_COMPARISON, WEAK_ASSERTION,
SOURCE_TEXT_GREP.

Exit codes: 0 scan completed (with or without findings); 2 usage, path, or tool failure.'

SJ_JSON=0
SJ_SELF=0
SJ_TMP=''
SJ_PATHS=()
SJ_AWK_FILE=''

sj_cleanup() {
  if [ -n "$SJ_TMP" ] && [ -d "$SJ_TMP" ]; then rm -rf "$SJ_TMP"; fi
}
trap sj_cleanup EXIT

sj_ue() { # <code> <message> [exit]
  printf '{"ok":false,"code":"%s","message":"%s"}\n' "$1" "$2" >&2
  exit "${3:-2}"
}

sj_workdir() {
  if [ -z "$SJ_TMP" ]; then
    SJ_TMP=$(mktemp -d "${TMPDIR:-/tmp}/scan-test-junk.XXXXXX") || sj_ue TMP_FAILED "cannot create a temporary directory"
    SJ_AWK_FILE=$SJ_TMP/scan.awk
    sj_awk_program >"$SJ_AWK_FILE"
  fi
}

sj_awk_program() {
  cat <<'AWK'
function sq(s) {
  sub(/^[ \t]+/, "", s)
  sub(/[ \t]+$/, "", s)
  gsub(/[ \t]+/, "", s)
  return s
}
function emit(code, detail) {
  if (index(" " seen " ", " " code " ") > 0) return
  seen = seen " " code
  printf "%d\t%s\t%s\n", NR, code, detail
}
# compare_pair <left> <right> <detail>
function compare_pair(left, right, detail) {
  left = sq(left)
  right = sq(right)
  if (left != "" && left == right) emit("SELF_COMPARISON", detail)
}
# part(s, start) — s from the absolute character start to the end.
function part(s, start) {
  return substr(s, start, length(s) - start + 1)
}
# balanced(s, open) — content between the paren at index open and its partner.
function balanced(s, open,   i, depth, ch, out) {
  depth = 0
  out = ""
  i = open
  while (i <= length(s)) {
    ch = substr(s, i, 1)
    if (ch == "(") {
      depth++
      if (depth > 1) out = out ch
    } else if (ch == ")") {
      depth--
      if (depth == 0) return out
      out = out ch
    } else {
      out = out ch
    }
    i++
  }
  return ""
}
function check_expect(line,   at, left, rest, open) {
  at = index(line, "expect(")
  if (at == 0) return
  left = balanced(line, at + 6)
  rest = substr(line, at + 8 + length(left), length(line))
  open = index(rest, "(")
  if (rest !~ /^\.to[A-Za-z]*\(/ || open == 0) return
  compare_pair(left, balanced(rest, open), "the assertion compares a value with itself")
}
function check_equal(line,   at, open, inner, cut) {
  at = index(line, "assertEqual")
  if (at == 0) at = index(line, "assertEquals")
  if (at == 0) at = index(line, "assert_eq!")
  if (at == 0) return
  open = index(substr(line, at), "(")
  if (open == 0) return
  inner = balanced(line, at + open - 1)
  cut = index(inner, ",")
  if (cut == 0) return
  compare_pair(substr(inner, 1, cut - 1), substr(inner, cut + 1), "the assertion compares a value with itself")
}
function check_python_assert(line,   frag, cut) {
  if (!match(line, /^[ \t]*assert[ \t]+.*==.*$/)) return
  frag = line
  sub(/^[ \t]*assert[ \t]+/, "", frag)
  cut = index(frag, "==")
  compare_pair(substr(frag, 1, cut - 1), part(frag, cut + 2), "the assertion compares a value with itself")
}
function check_weak(line) {
  if (line ~ /toBeGreaterThan\([ \t]*0[ \t]*\)/) {
    emit("WEAK_ASSERTION", "the assertion proves only that the collection is not empty")
  } else if (line ~ /(length|size|count)[ \t]*\.(toBeGreaterThan|toBeTruthy|toBeDefined)/) {
    emit("WEAK_ASSERTION", "the assertion proves only that the collection is not empty")
  } else if (line ~ /(assertGreater|assertTrue|assert)\([^)]*len\(/) {
    emit("WEAK_ASSERTION", "the assertion proves only the length, not the content")
  } else if (line ~ /^[ \t]*assert[ \t]+len\(/) {
    emit("WEAK_ASSERTION", "the assertion proves only the length, not the content")
  } else if (line ~ /(assertEq|assertEquals)\([^)]*\.len\(\)/) {
    emit("WEAK_ASSERTION", "the assertion proves only the length, not the content")
  } else if (line ~ /\.length\).*\.to(Be|Equal)\([0-9]+\)/) {
    emit("WEAK_ASSERTION", "the assertion proves only the length, not the content")
  }
}
function check_source_grep(line) {
  if (line ~ /readFileSync\(/ || line ~ /readFile\(/ || line ~ /read_text\(/ ||
      line ~ /readFileSync\([^)]*\.(py|js|mjs|cjs|ts|tsx|go|rs|rb)/) {
    emit("SOURCE_TEXT_GREP", "the test reads source text instead of exercising behavior")
  } else if (line ~ /(execSync|exec|system|subprocess\.run)\([^)]*(grep|Get-Content)/) {
    emit("SOURCE_TEXT_GREP", "the test greps source text instead of exercising behavior")
  }
}
{
  seen = ""
  check_focused = index($0, ".only(") > 0 || $0 ~ /(^|[^A-Za-z0-9_])f(it|describe|test)\(/ ||
    $0 ~ /focus[ \t]*:[ \t]*true/ || $0 ~ /@pytest\.mark\.focus/
  if (check_focused) emit("FOCUSED_TEST", "a focused test narrows the run to one case")
  check_skipped = index($0, ".skip(") > 0 || $0 ~ /(^|[^A-Za-z0-9_])x(it|describe|test)\(/ ||
    $0 ~ /@pytest\.mark\.skip/ || $0 ~ /@unittest\.skip/ ||
    $0 ~ /(^|[^A-Za-z0-9_.])t\.Skip\(/ || $0 ~ /#\[ignore\]/ || $0 ~ /\.todo\(/
  if (check_skipped) emit("SKIPPED_TEST", "a skipped test hides the case instead of proving it")
  check_sleep = $0 ~ /(^|[^A-Za-z0-9_.])(sleep|usleep)\([ \t]*[0-9]/ ||
    $0 ~ /waitForTimeout\(/ || $0 ~ /(Thread|time)\.sleep\(/ ||
    ($0 ~ /setTimeout\(/ && $0 ~ /,[ \t]*[0-9]+[ \t]*\)/)
  if (check_sleep) emit("FIXED_SLEEP", "a fixed delay stands in for waiting on the real condition")
  check_expect($0)
  check_equal($0)
  check_python_assert($0)
  check_weak($0)
  check_source_grep($0)
}
AWK
}

# sj_scan <file> — prints "<line>\t<CODE>\t<detail>" per finding.
sj_scan() {
  awk -f "$SJ_AWK_FILE" "$1"
}

# sj_is_test_name <basename>
sj_is_test_name() {
  case $1 in
    *.test.* | *.spec.* | *_test.* | test_*.py | *_spec.rb | *Test.java) return 0 ;;
  esac
  return 1
}

# sj_collect <path> — appends matching files to <work>/files.
sj_collect() {
  local path=$1 work=$SJ_TMP
  if [ -f "$path" ]; then
    printf '%s\n' "$path" >>"$work/files"
    return 0
  fi
  if [ -d "$path" ]; then
    if ! find "$path" -type f \( -name '*.test.*' -o -name '*.spec.*' -o -name '*_test.*' \
      -o -name 'test_*.py' -o -name '*_spec.rb' -o -name '*Test.java' \) >"$work/found" 2>/dev/null; then
      sj_ue FIND_FAILED "cannot read directory: $path"
    fi
    while IFS= read -r entry; do
      [ -n "$entry" ] || continue
      printf '%s\n' "$entry" >>"$work/files"
    done <"$work/found"
    return 0
  fi
  sj_ue PATH_MISSING "no such file or directory: $path"
}

# sj_run <work> — scans every collected test file; writes findings.tsv and summary.
sj_run() {
  local work=$1 file base line code detail count=0 files=0
  : >"$work/findings.tsv"
  LC_ALL=C sort -u "$work/files" >"$work/sorted"
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    base=${file##*/}
    sj_is_test_name "$base" || continue
    files=$((files + 1))
    if ! sj_scan "$file" >"$work/one.tsv"; then
      sj_ue SCAN_FAILED "cannot read file: $file"
    fi
    while IFS="$(printf '\t')" read -r line code detail; do
      [ -n "$line" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$file" "$line" "$code" "$detail" >>"$work/findings.tsv"
      count=$((count + 1))
    done <"$work/one.tsv"
  done <"$work/sorted"
  printf '%s\t%s\n' "$count" "$files" >"$work/summary"
}

sj_emit_text() { # <work>
  local work=$1 file line code detail count files
  if [ -s "$work/findings.tsv" ]; then
    LC_ALL=C sort -t "$(printf '\t')" -k1,1 -k2,2n "$work/findings.tsv" >"$work/sorted-findings"
    while IFS="$(printf '\t')" read -r file line code detail; do
      printf '%s:%s:%s: %s\n' "$file" "$line" "$code" "$detail"
    done <"$work/sorted-findings"
  fi
  count=$(cut -f1 "$work/summary")
  files=$(cut -f2 "$work/summary")
  if [ "$count" -eq 0 ]; then
    printf 'summary: no findings in %s file(s)\n' "$files"
  else
    printf 'summary: %s finding(s) in %s file(s)\n' "$count" "$files"
  fi
}

sj_emit_json() { # <work>
  local work=$1
  if [ -s "$work/findings.tsv" ]; then
    jq -Rn --argjson files "$(cut -f2 "$work/summary")" '
      [inputs | split("\t") | {file: .[0], line: (.[1] | tonumber), code: .[2], detail: .[3]}] as $f
      | {ok: true, files: $files, total: ($f | length), findings: $f,
         counts: ($f | group_by(.code) | map({key: .[0].code, value: length}) | from_entries)}
    ' <"$work/findings.tsv"
  else
    jq -cn --argjson files "$(cut -f2 "$work/summary")" \
      '{ok: true, files: $files, total: 0, findings: [], counts: {}}'
  fi
}

sj_self_test() {
  local work=$1 failures=0 expected
  mkdir -p "$work/fixtures/nested"
  cat >"$work/fixtures/junk.test.ts" <<'FIXTURE'
import { test } from 'node:test'
test.only('adds', () => {
  expect(total).toBe(total)
  expect(items.length).toBeGreaterThan(0)
  setTimeout(() => {}, 500)
})
test.skip('subtracts', () => {})
FIXTURE
  cat >"$work/fixtures/nested/source_grep_test.py" <<'FIXTURE'
from pathlib import Path


def test_source_text():
    text = Path('src/app.py').read_text()
    assert 'def run' in text
    assert len(text) > 0
    assert 1 == 1
FIXTURE
  cat >"$work/fixtures/clean.test.ts" <<'FIXTURE'
import { test } from 'node:test'
test('adds two numbers', () => {
  expect(add(1, 2)).toBe(3)
  expect(add(-1, 1)).toBe(0)
})
FIXTURE
  : >"$work/files"
  printf '%s\n' "$work/fixtures/junk.test.ts" "$work/fixtures/nested/source_grep_test.py" \
    "$work/fixtures/clean.test.ts" >"$work/files"
  sj_run "$work"
  cut -f3 "$work/findings.tsv" | LC_ALL=C sort -u >"$work/codes"
  expected=$(printf '%s\n' FIXED_SLEEP FOCUSED_TEST SELF_COMPARISON SKIPPED_TEST SOURCE_TEXT_GREP WEAK_ASSERTION)
  if ! cmp -s <(printf '%s\n' "$expected") "$work/codes"; then
    printf 'self-test: the reported code set does not match the six classes\n' >&2
    failures=$((failures + 1))
  fi
  if grep -Fq "$work/fixtures/clean.test.ts" "$work/findings.tsv"; then
    printf 'self-test: the clean fixture produced a finding\n' >&2
    failures=$((failures + 1))
  fi
  if [ "$failures" -ne 0 ]; then
    printf '{"ok":false,"classes":3,"fixtures":3,"failures":%s}\n' "$failures"
    return 1
  fi
  printf '{"ok":true,"classes":6,"fixtures":3,"findings":%s,"clean_fixture_findings":0}\n' \
    "$(wc -l <"$work/findings.tsv" | tr -d ' ')"
}

while [ "$#" -gt 0 ]; do
  case $1 in
    --help | -h)
      printf '%s\n' "$SJ_USAGE"
      exit 0
      ;;
    --json) SJ_JSON=1 ;;
    --self-test) SJ_SELF=1 ;;
    --*)
      printf '{"ok":false,"code":"BAD_ARGUMENT","message":"unknown argument: %s"}\n' "$1" >&2
      exit 2
      ;;
    *) SJ_PATHS+=("$1") ;;
  esac
  shift
done

sj_workdir
work=$SJ_TMP
if [ "$SJ_SELF" -eq 1 ]; then
  sj_self_test "$work"
  exit $?
fi

if [ "${#SJ_PATHS[@]}" -eq 0 ]; then
  sj_ue NO_PATHS "name at least one file or directory; a scan never widens past the paths it was given"
fi

: >"$work/files"
for path in "${SJ_PATHS[@]}"; do
  sj_collect "$path"
done
if [ ! -s "$work/files" ]; then
  if [ "$SJ_JSON" -eq 1 ]; then
    printf '{"ok":true,"files":0,"total":0,"findings":[],"counts":{},"message":"no test files matched the given paths"}\n'
  else
    printf 'summary: no test files matched the given paths\n'
  fi
  exit 0
fi

sj_run "$work"
if [ "$SJ_JSON" -eq 1 ]; then
  sj_emit_json "$work"
else
  sj_emit_text "$work"
fi