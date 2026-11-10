#!/usr/bin/env bash
# Prove one test can catch a regression: mutate one literal string, run the test
# command, restore the file, and confirm the restore from the hash.
#
# The restore is not conditional on the test outcome. A failing test, a missing
# command, or an interrupted run still restores from the backup, and the restored
# bytes are compared against the original SHA-256 before this script exits.
set -euo pipefail

MP_USAGE='Usage: bash mutation-proof.sh --file <path> --find <text> --replace <text> \
         --test <command> [--json]
       bash mutation-proof.sh --self-test
       bash mutation-proof.sh --help

--file      the source file to mutate. Exactly one file per run: one mutation,
            one test command, one verdict.
--find      literal text that must occur exactly once in the file. It is matched
            with literal comparison, never as a regular expression.
--replace   literal text that replaces the first occurrence of --find.
--test      the test command to run once with the mutation in place. It runs
            through sh -c in the current directory, so it sees the real project.
--json      print one JSON object instead of the report lines.
--self-test prove the three paths on throwaway fixtures: a mutation the test
            catches, a mutation the test misses, and a test command that fails on
            its own ; every path must restore the file byte-identically.

Verdicts: caught (the test command failed with the mutation in place) and survived
(the test command passed, so the case is not covered). The file is restored before
the verdict is reported.

Exit codes: 0 proof completed (either verdict); 2 usage, target, or backup failure;
3 restore could not be verified, with the backup path printed for recovery.'

MP_JSON=0
MP_SELF=0
MP_FILE=''
MP_FIND=''
MP_REPLACE=''
MP_TEST=''
MP_TMP=''
MP_BACKUP=''
MP_ORIGINAL_SHA=''
MP_RESTORED=0

mp_cleanup() {
  if [ -n "$MP_TMP" ] && [ -d "$MP_TMP" ]; then rm -rf "$MP_TMP"; fi
}
mp_on_exit() {
  # A run that dies before restoring must not leave the mutation in place.
  if [ "$MP_RESTORED" -eq 0 ] && [ -n "$MP_BACKUP" ] && [ -f "$MP_BACKUP" ] && [ -n "$MP_FILE" ]; then
    cp "$MP_BACKUP" "$MP_FILE" 2>/dev/null || true
    printf 'mutation-proof: the file was restored from %s during exit cleanup\n' "$MP_BACKUP" >&2
  fi
  mp_cleanup
}
trap mp_on_exit EXIT

mp_ue() { # <code> <message> [exit]
  printf '{"ok":false,"code":"%s","message":"%s"}\n' "$1" "$2" >&2
  exit "${3:-2}"
}

mp_workdir() {
  if [ -z "$MP_TMP" ]; then
    MP_TMP=$(mktemp -d "${TMPDIR:-/tmp}/mutation-proof.XXXXXX") || mp_ue TMP_FAILED "cannot create a temporary directory"
  fi
  printf '%s\n' "$MP_TMP"
}

mp_sha() { shasum -a 256 "$1" | awk '{print $1}'; }

# mp_count <file> <text> — number of literal occurrences, using awk index walks.
mp_count() {
  MP_NEEDLE=$2 awk '
    BEGIN { needle = ENVIRON["MP_NEEDLE"] }
    {
      line = $0
      while ((i = index(line, needle)) > 0) {
        n++
        line = substr(line, i + length(needle))
      }
    }
    END { printf "%d\n", n + 0 }
  ' "$1"
}

# mp_mutate <file> <find> <replace> — replace the first literal occurrence in place.
mp_mutate() {
  MP_FIND_TEXT=$2 MP_REPLACE_TEXT=$3 awk '
    BEGIN { find = ENVIRON["MP_FIND_TEXT"]; repl = ENVIRON["MP_REPLACE_TEXT"]; done = 0 }
    {
      if (!done && (i = index($0, find)) > 0) {
        $0 = substr($0, 1, i - 1) repl substr($0, i + length(find))
        done = 1
      }
      print
    }
  ' "$1" >"$1.mutation-proof.new" || return 1
  mv "$1.mutation-proof.new" "$1"
}

# mp_restore <file> <backup> — restore and verify the hash; never skipped.
mp_restore() {
  local file=$1 backup=$2 sha
  cp "$backup" "$file" || return 1
  sha=$(mp_sha "$file")
  if [ "$sha" != "$MP_ORIGINAL_SHA" ]; then
    printf 'mutation-proof: restore mismatch: expected %s, got %s\n' "$MP_ORIGINAL_SHA" "$sha" >&2
    return 1
  fi
  MP_RESTORED=1
  return 0
}

mp_report() { # <verdict> <test-exit> <test-output-file>
  local verdict=$1 code=$2 out=$3
  if [ "$MP_JSON" -eq 1 ]; then
    jq -cn \
      --arg file "$MP_FILE" --arg find "$MP_FIND" --arg replace "$MP_REPLACE" \
      --arg command "$MP_TEST" --arg verdict "$verdict" \
      --arg original "$MP_ORIGINAL_SHA" --arg restored "$(mp_sha "$MP_FILE")" \
      --argjson exit_code "$code" --rawfile output "$out" \
      '{ok: true, file: $file,
        mutation: {find: $find, replace: $replace},
        test: {command: $command, exit_code: $exit_code, output: ($output | split("\n") | map(select(length > 0)))},
        verdict: $verdict, restored: true,
        original_sha256: $original, restored_sha256: $restored}'
    return 0
  fi
  printf 'file: %s\n' "$MP_FILE"
  printf 'mutation: %s -> %s\n' "$MP_FIND" "$MP_REPLACE"
  printf 'test: %s (exit %s)\n' "$MP_TEST" "$code"
  if [ -s "$out" ]; then
    printf 'output: %s\n' "$(tr '\n' ' ' <"$out" | cut -c1-400)"
  fi
  case $verdict in
    caught) printf 'verdict: caught — the test failed with the mutation in place\n' ;;
    survived) printf 'verdict: survived — the test passed with the mutation in place\n' ;;
  esac
  printf 'restore: byte-identical, sha256 %s\n' "$MP_ORIGINAL_SHA"
}

# mp_prove <file> <find> <replace> <command> — one mutation, one verdict, one restore.
mp_prove() {
  local file=$1 find=$2 replace=$3 command=$4 work out code verdict count
  [ -f "$file" ] || mp_ue FILE_MISSING "no such file: $file"
  [ -n "$find" ] || mp_ue FIND_EMPTY "the find text is empty"
  count=$(mp_count "$file" "$find")
  if [ "$count" -eq 0 ]; then
    mp_ue FIND_ABSENT "the find text does not occur in $file"
  fi
  if [ "$count" -gt 1 ]; then
    mp_ue FIND_AMBIGUOUS "the find text occurs $count times in $file; narrow it to one occurrence"
  fi

  work=$(mp_workdir)
  out=$work/test-output.txt
  MP_BACKUP=$work/backup
  MP_ORIGINAL_SHA=$(mp_sha "$file")
  cp "$file" "$MP_BACKUP" || mp_ue BACKUP_FAILED "cannot copy $file to $MP_BACKUP"
  MP_RESTORED=0

  mp_mutate "$file" "$find" "$replace" || {
    mp_restore "$file" "$MP_BACKUP" || mp_ue RESTORE_FAILED "cannot restore $file; the backup is at $MP_BACKUP" 3
    mp_ue MUTATION_FAILED "cannot write the mutation into $file"
  }
  if [ "$(mp_sha "$file")" = "$MP_ORIGINAL_SHA" ]; then
    mp_restore "$file" "$MP_BACKUP" || mp_ue RESTORE_FAILED "cannot restore $file; the backup is at $MP_BACKUP" 3
    mp_ue MUTATION_NO_CHANGE "the replacement left $file unchanged, so the proof would be vacuous"
  fi

  code=0
  sh -c "$command" >"$out" 2>&1 || code=$?

  if ! mp_restore "$file" "$MP_BACKUP"; then
    printf '{"ok":false,"code":"RESTORE_FAILED","message":"restore mismatch","backup":"%s"}\n' "$MP_BACKUP" >&2
    exit 3
  fi

  if [ "$code" -eq 0 ]; then verdict=survived; else verdict=caught; fi
  mp_report "$verdict" "$code" "$out"
}

# mp_self_case <work> <name> <dir> <file> <find> <replace> <command>
# Runs one proof inside a subshell and writes its JSON report to <work>/<name>.json.
mp_self_case() {
  local work=$1 name=$2 dir=$3 file=$4 find=$5 replace=$6 command=$7 rc=0
  (cd "$dir" && MP_JSON=1 mp_prove "$file" "$find" "$replace" "$command") \
    >"$work/$name.json" 2>"$work/$name.err" || rc=$?
  return "$rc"
}

mp_self_test() {
  local work failures=0
  work=$(mp_workdir)
  mkdir -p "$work/fixtures"

  cat >"$work/fixtures/calc" <<'FIXTURE'
#!/usr/bin/env bash
add() { echo $(( $1 + $2 )); }
add "$1" "$2"
FIXTURE
  cat >"$work/fixtures/calc-check" <<'FIXTURE'
#!/usr/bin/env bash
result=$(bash calc 2 3)
[ "$result" = "5" ] || { echo "expected 5, got $result"; exit 1; }
FIXTURE
  cat >"$work/fixtures/notes" <<'FIXTURE'
#!/usr/bin/env bash
# helper: prints a fixed banner
echo "banner"
FIXTURE
  cp "$work/fixtures/calc" "$work/calc.orig"
  cp "$work/fixtures/notes" "$work/notes.orig"

  # 1. A mutation the test catches, restored byte-identically.
  # shellcheck disable=SC2016  # the fixture text is literal, never expanded here
  if ! mp_self_case "$work" caught "$work/fixtures" calc '+ $2' '- $2' 'bash calc-check'; then
    printf 'self-test: the caught case failed to complete: %s\n' "$(cat "$work/caught.err" 2>/dev/null)" >&2
    failures=$((failures + 1))
  elif ! jq -e '.verdict == "caught" and .restored == true' "$work/caught.json" >/dev/null 2>&1; then
    printf 'self-test: the caught case did not report caught: %s\n' "$(cat "$work/caught.json" 2>/dev/null)" >&2
    failures=$((failures + 1))
  fi
  if ! cmp -s "$work/fixtures/calc" "$work/calc.orig"; then
    printf 'self-test: the caught case did not restore the file byte-identically\n' >&2
    failures=$((failures + 1))
  fi

  # 2. A mutation the test misses: survived, still restored byte-identically.
  if ! mp_self_case "$work" survived "$work/fixtures" notes 'fixed banner' 'banner text' 'bash -n notes'; then
    printf 'self-test: the survived case failed to complete: %s\n' "$(cat "$work/survived.err" 2>/dev/null)" >&2
    failures=$((failures + 1))
  elif ! jq -e '.verdict == "survived" and .restored == true' "$work/survived.json" >/dev/null 2>&1; then
    printf 'self-test: the survived case did not report survived: %s\n' "$(cat "$work/survived.json" 2>/dev/null)" >&2
    failures=$((failures + 1))
  fi
  if ! cmp -s "$work/fixtures/notes" "$work/notes.orig"; then
    printf 'self-test: the survived case did not restore the file byte-identically\n' >&2
    failures=$((failures + 1))
  fi

  # 3. A test command that fails on its own still restores byte-identically.
  # shellcheck disable=SC2016  # the fixture text is literal, never expanded here
  if ! mp_self_case "$work" failing "$work/fixtures" calc '+ $2' '* $2' 'exit 7'; then
    printf 'self-test: the failing-command case failed to complete: %s\n' "$(cat "$work/failing.err" 2>/dev/null)" >&2
    failures=$((failures + 1))
  elif ! jq -e '.test.exit_code == 7 and .restored == true' "$work/failing.json" >/dev/null 2>&1; then
    printf 'self-test: the failing-command case did not keep the exit code and a verified restore: %s\n' "$(cat "$work/failing.json" 2>/dev/null)" >&2
    failures=$((failures + 1))
  fi
  if ! cmp -s "$work/fixtures/calc" "$work/calc.orig"; then
    printf 'self-test: the failing-command case did not restore the file byte-identically\n' >&2
    failures=$((failures + 1))
  fi

  # 4. An ambiguous target is rejected before anything is written.
  printf 'x\nx\n' >"$work/fixtures/dup.txt"
  if mp_self_case "$work" ambiguous "$work/fixtures" dup.txt 'x' 'y' 'true'; then
    printf 'self-test: an ambiguous target was accepted\n' >&2
    failures=$((failures + 1))
  fi
  if [ "$(mp_sha "$work/fixtures/dup.txt")" != "$(printf 'x\nx\n' | shasum -a 256 | awk '{print $1}')" ]; then
    printf 'self-test: a rejected run still touched the file\n' >&2
    failures=$((failures + 1))
  fi

  if [ "$failures" -ne 0 ]; then
    printf '{"ok":false,"cases":4,"failures":%s}\n' "$failures"
    return 1
  fi
  printf '{"ok":true,"cases":4,"caught":true,"survived":true,"failing_command_restored":true,"ambiguous_rejected":true,"byte_identical_restore":true}\n'
}

while [ "$#" -gt 0 ]; do
  case $1 in
    --help | -h)
      printf '%s\n' "$MP_USAGE"
      exit 0
      ;;
    --json) MP_JSON=1 ;;
    --self-test) MP_SELF=1 ;;
    --file | --find | --replace | --test)
      if [ "$#" -lt 2 ]; then
        mp_ue BAD_ARGUMENT "$1 needs a value"
      fi
      case $1 in
        --file) MP_FILE=$2 ;;
        --find) MP_FIND=$2 ;;
        --replace) MP_REPLACE=$2 ;;
        --test) MP_TEST=$2 ;;
      esac
      shift
      ;;
    *)
      printf '{"ok":false,"code":"BAD_ARGUMENT","message":"unknown argument: %s"}\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$MP_SELF" -eq 1 ]; then
  mp_self_test
  exit $?
fi

[ -n "$MP_FILE" ] || mp_ue MISSING_FILE "pass --file <path>"
[ -n "$MP_FIND" ] || mp_ue MISSING_FIND "pass --find <text>"
[ -n "$MP_TEST" ] || mp_ue MISSING_TEST "pass --test <command>"

mp_prove "$MP_FILE" "$MP_FIND" "$MP_REPLACE" "$MP_TEST"