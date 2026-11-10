#!/usr/bin/env bash
# Read-only memo fingerprint and format check for the hyper-handoff skill.
#
# The memo contract fixes the header lines, the section names, and the two
# fingerprint values. This script prints those values and compares them; it
# never creates or edits a memo, so a memo stays evidence and never becomes a
# write target for a tool.
set -euo pipefail

# shellcheck disable=SC2016  # the backticks in the usage text are literal
HM_USAGE='Usage: bash handoff-memo.sh fingerprint [--repo <dir>]
       bash handoff-memo.sh check --memo <path>
       bash handoff-memo.sh compare --memo <path> [--repo <dir>]
       bash handoff-memo.sh list [--repo <dir>]
       bash handoff-memo.sh --self-test
       bash handoff-memo.sh --help

fingerprint  print two lines. `HEAD: <short sha> (<branch>)`, or
             `HEAD: none (no commits)` in a repository without a commit, or
             `HEAD: none (not a git repository)`. `Dirty: clean`, or
             `Dirty: <n> file(s): <porcelain paths>` up to 20 entries, or
             `Dirty: <n> files, digest <sha256 of git status --porcelain>` past
             that; outside a repository both lines say `none (not a git
             repository)`.
check        validate the memo header and its required sections, then print
             `Format: hyper-handoff/1`, or `Format: legacy` for a memo written
             before the format line existed; a legacy memo is read, not rejected.
compare      compare the memo `HEAD:` and `Dirty:` lines with the fingerprint of
             the repository and exit 1 naming each field that differs. A memo
             sha and the live sha count as equal when one is a prefix of the
             other, so a memo holding the full 40-character sha still matches
             the short fingerprint; a different commit still differs.
list         print the slug of every open memo under .hyper/handoff/*/memo.md.

The fingerprint is taken with git rev-parse, git symbolic-ref, and git status
--porcelain in the repository named by --repo (the current directory by
default). The script is read-only. Exit codes: 0 fine; 1 the memo is missing a
required part or has drifted from the repository; 2 usage, unreadable input, or
a git failure that prevents a decision.'

HM_REQUIRED_HEADERS='Slug
Revision
Status
Written
Written by
HEAD:
Dirty:
Resumed:
Check:'

HM_REQUIRED_SECTIONS='## Original request
## Corrections
## Now
## Done
## Next
## Plan and done-when
## Where
## Decisions and dead ends
## Open questions and risks'

hm_usage_fail() { # <message>
  printf 'handoff-memo: %s\n' "$1" >&2
  printf '%s\n' "$HM_USAGE" >&2
  exit 2
}

hm_input_fail() { # <message>
  printf 'handoff-memo: %s\n' "$1" >&2
  exit 2
}

hm_sha256_stream() { # stdin
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | cut -d' ' -f1
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum | cut -d' ' -f1
  else
    printf 'handoff-memo: shasum or sha256sum is required\n' >&2
    return 2
  fi
}

# hm_field <file> <key> prints the first header value for the key, accepting
# both the `- Key: value` bullet form the template uses and a bare `Key: value`.
# The scan stops at the first `## ` heading, so a body line that looks like a
# header never stands in for a missing header.
hm_field() { # <file> <key>
  local key=$2
  case $key in
    *:) : ;;
    *) key=$key: ;;
  esac
  awk -v k="$key" '
    {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^## /) exit
      if (line ~ /^- /) line = substr(line, 3)
      if (index(line, k) == 1) {
        v = substr(line, length(k) + 1)
        sub(/^[ \t]+/, "", v)
        sub(/[ \t]+$/, "", v)
        print v
        exit
      }
    }
  ' "$1"
}

# hm_fingerprint <dir> prints the two fingerprint lines. Read-only.
hm_fingerprint() { # <dir>
  local dir=$1 status count paths digest branch sha
  [ -d "$dir" ] || hm_input_fail "not a directory: $dir"
  if ! git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
    printf 'HEAD: none (not a git repository)\n'
    printf 'Dirty: none (not a git repository)\n'
    return 0
  fi
  # Take the status before printing anything: a bare repository fails here, and
  # a fingerprint that printed its first line before the failure would read as a
  # partial verdict on stdout. --no-optional-locks keeps the command from
  # refreshing .git/index, so a memo written after it still compares clean.
  status=$(git --no-optional-locks -C "$dir" status --porcelain 2>/dev/null) ||
    hm_input_fail "git status failed in $dir"
  sha=$(git -C "$dir" rev-parse --verify --short HEAD 2>/dev/null || true)
  branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  if [ -z "$sha" ]; then
    printf 'HEAD: none (no commits)\n'
  elif [ -n "$branch" ]; then
    printf 'HEAD: %s (%s)\n' "$sha" "$branch"
  else
    printf 'HEAD: %s (detached)\n' "$sha"
  fi
  if [ -z "$status" ]; then
    printf 'Dirty: clean\n'
    return 0
  fi
  count=$(printf '%s\n' "$status" | awk '{ n++ } END { print n + 0 }')
  paths=$(printf '%s\n' "$status" | awk '{
    p = substr($0, 4)
    sub(/^[ \t]+/, "", p)
    sub(/[ \t]+$/, "", p)
    printf "%s%s", sep, p
    sep = ", "
  }')
  if [ "$count" -gt 20 ]; then
    digest=$(printf '%s\n' "$status" | hm_sha256_stream)
    [ -n "$digest" ] || hm_input_fail 'cannot digest the working tree state'
    printf 'Dirty: %s files, digest %s\n' "$count" "$digest"
  elif [ "$count" -eq 1 ]; then
    printf 'Dirty: 1 file: %s\n' "$paths"
  else
    printf 'Dirty: %s files: %s\n' "$count" "$paths"
  fi
  return 0
}

# hm_valid_status <value> accepts `open` or `closed (<YYYY-MM-DD>: <reason>)`.
hm_valid_status() { # <value>
  case $1 in
    open) return 0 ;;
    'closed ('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]': '*')') return 0 ;;
  esac
  return 1
}

# hm_check <memo> validates the header lines and the required section headings.
hm_check() { # <memo>
  local memo=$1 rc=0 key section status format value
  [ -f "$memo" ] || hm_input_fail "memo not found: $memo"
  [ -r "$memo" ] || hm_input_fail "memo is not readable: $memo"
  while IFS= read -r key; do
    [ -n "$key" ] || continue
    value=$(hm_field "$memo" "$key")
    if [ -z "$value" ]; then
      printf 'check: missing header: %s\n' "$key" >&2
      rc=1
    fi
  done < <(printf '%s\n' "$HM_REQUIRED_HEADERS")
  while IFS= read -r section; do
    [ -n "$section" ] || continue
    if ! awk -v s="$section" '{
      line = $0
      sub(/\r$/, "", line)
      sub(/[ \t]+$/, "", line)
      if (line == s) found = 1
    } END { exit(found ? 0 : 1) }' "$memo"; then
      printf 'check: missing section: %s\n' "$section" >&2
      rc=1
    fi
  done < <(printf '%s\n' "$HM_REQUIRED_SECTIONS")
  status=$(hm_field "$memo" 'Status')
  if [ -n "$status" ] && ! hm_valid_status "$status"; then
    printf 'check: bad Status: %s (expected open or closed (<date>: <reason>))\n' "$status" >&2
    rc=1
  fi
  format=$(hm_field "$memo" 'Format')
  case $format in
    '') format_message='Format: legacy' ;;
    hyper-handoff/1) format_message='Format: hyper-handoff/1' ;;
    *)
      printf 'check: unsupported Format: %s (expected hyper-handoff/1)\n' "$format" >&2
      format_message=''
      rc=1
      ;;
  esac
  [ "$rc" -eq 0 ] || return 1
  printf '%s\n' "$format_message"
  return 0
}

# hm_compare <memo> <dir> compares the memo fingerprint with the live one.
hm_compare() { # <memo> <dir>
  local memo=$1 dir=$2 rc=0 memo_head memo_dirty live live_head live_dirty
  local memo_sha live_sha memo_tail live_tail head_match
  [ -f "$memo" ] || hm_input_fail "memo not found: $memo"
  [ -r "$memo" ] || hm_input_fail "memo is not readable: $memo"
  memo_head=$(hm_field "$memo" 'HEAD:')
  memo_dirty=$(hm_field "$memo" 'Dirty:')
  if [ -z "$memo_head" ]; then
    printf 'compare: missing header: HEAD:\n' >&2
    rc=1
  fi
  if [ -z "$memo_dirty" ]; then
    printf 'compare: missing header: Dirty:\n' >&2
    rc=1
  fi
  live=$(hm_fingerprint "$dir") || exit 2
  live_head=${live%%$'\n'*}
  live_head=${live_head#HEAD: }
  live_dirty=${live#*$'\n'}
  live_dirty=${live_dirty#Dirty: }
  if [ -n "$memo_head" ] && [ "$memo_head" != "$live_head" ]; then
    # The line is `<sha> (<branch>)`. Compare the sha part as equal when one is
    # a prefix of the other (min length 7) because the memo may carry the full
    # 40-character sha while the live fingerprint is shortened.
    memo_sha=${memo_head%% *}
    live_sha=${live_head%% *}
    memo_tail=''
    live_tail=''
    case $memo_head in
      *' '*) memo_tail=${memo_head#* } ;;
    esac
    case $live_head in
      *' '*) live_tail=${live_head#* } ;;
    esac
    head_match=0
    if [ "$memo_tail" = "$live_tail" ] &&
      [ "${#memo_sha}" -ge 7 ] && [ "${#live_sha}" -ge 7 ]; then
      case "$memo_sha" in
        "$live_sha"*) head_match=1 ;;
      esac
      case "$live_sha" in
        "$memo_sha"*) head_match=1 ;;
      esac
    fi
    if [ "$head_match" -eq 0 ]; then
      printf 'compare: HEAD mismatch\n  memo: %s\n  live: %s\n' "$memo_head" "$live_head" >&2
      rc=1
    fi
  fi
  if [ -n "$memo_dirty" ] && [ "$memo_dirty" != "$live_dirty" ]; then
    printf 'compare: Dirty mismatch\n  memo: %s\n  live: %s\n' "$memo_dirty" "$live_dirty" >&2
    rc=1
  fi
  [ "$rc" -eq 0 ] || return 1
  printf 'compare: ok\n'
  return 0
}

# hm_list <dir> prints the slug of every open memo, sorted.
hm_list() { # <dir>
  local dir=$1 root memo slug status
  [ -d "$dir" ] || hm_input_fail "not a directory: $dir"
  root=$dir/.hyper/handoff
  [ -d "$root" ] || return 0
  for memo in "$root"/*/memo.md; do
    [ -f "$memo" ] || continue
    slug=${memo%/memo.md}
    slug=${slug##*/}
    status=$(hm_field "$memo" 'Status')
    case $status in
      open) printf '%s\n' "$slug" ;;
    esac
  done | LC_ALL=C sort
  return 0
}

HM_SELFTEST_DIR=''
HM_SELFTEST_FAILED=0
HM_SELFTEST_CASES=0

hm_self_cleanup() {
  if [ -n "$HM_SELFTEST_DIR" ] && [ -d "$HM_SELFTEST_DIR" ]; then
    rm -rf "$HM_SELFTEST_DIR"
  fi
}

hm_self_expect() { # <id> <expected> <actual>
  HM_SELFTEST_CASES=$((HM_SELFTEST_CASES + 1))
  if [ "$2" = "$3" ]; then
    return 0
  fi
  HM_SELFTEST_FAILED=$((HM_SELFTEST_FAILED + 1))
  printf 'SELF-TEST FAIL %s\n  expected: %s\n  actual:   %s\n' "$1" "$2" "$3" >&2
  return 0
}

hm_self_expect_contains() { # <id> <needle> <haystack>
  HM_SELFTEST_CASES=$((HM_SELFTEST_CASES + 1))
  case $3 in
    *"$2"*) return 0 ;;
  esac
  HM_SELFTEST_FAILED=$((HM_SELFTEST_FAILED + 1))
  printf 'SELF-TEST FAIL %s\n  wanted substring: %s\n  actual: %s\n' "$1" "$2" "$3" >&2
  return 0
}

# hm_self_memo <path> <sha> <branch> <dirty> writes a complete memo fixture.
hm_self_memo() { # <path> <sha> <branch> <dirty>
  cat >"$1" <<MEMO
- Format: hyper-handoff/1
- Slug: demo
- Revision: 1
- Status: open
- Written: 2026-11-10 10:00 KST
- Written by: omp on test-machine
- HEAD: $2 ($3)
- Dirty: $4
- Resumed: none
- Check: pass

## Original request

> Do the demo task.

## Corrections

- none

## Now

Writing the demo memo so the next session can resume it.

## Done

- none

## Next

1. Run the demo command.

## Plan and done-when

- Plan: none
- Done when: the demo command exits 0.

## Where

- Repository: none
- Branch: none

## Decisions and dead ends

- none

## Open questions and risks

- none
MEMO
}

hm_self_git_repo() { # <dir>
  git init -q "$1" >/dev/null 2>&1
  printf 'one\n' >"$1/base.txt"
  git -C "$1" add base.txt
  git -C "$1" -c user.name=handoff -c user.email=handoff@example.invalid \
    commit -q -m 'selftest: base'
}

hm_self_test() {
  command -v git >/dev/null 2>&1 || hm_input_fail 'git is required for --self-test'
  command -v shasum >/dev/null 2>&1 ||
    command -v sha256sum >/dev/null 2>&1 ||
    hm_input_fail 'shasum or sha256sum is required for --self-test'

  local self tmp repo spaced sha branch out err rc before_hash after_hash
  local full_sha other_sha
  local expected digest
  self=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)/$(basename -- "$0")
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/handoff-memo.XXXXXX") ||
    hm_input_fail 'cannot create a temporary directory'
  HM_SELFTEST_DIR=$tmp
  trap hm_self_cleanup EXIT

  repo=$tmp/repo
  mkdir -p "$repo"
  hm_self_git_repo "$repo"
  sha=$(git -C "$repo" rev-parse --verify --short HEAD)
  branch=$(git -C "$repo" symbolic-ref --quiet --short HEAD)

  rc=0
  out=$(bash "$self" fingerprint --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect fingerprint-clean-exit 0 "$rc"
  hm_self_expect fingerprint-clean-head "$(printf 'HEAD: %s (%s)' "$sha" "$branch")" \
    "${out%%$'\n'*}"
  hm_self_expect fingerprint-clean-dirty 'Dirty: clean' "${out#*$'\n'}"

  printf 'changed\n' >"$repo/base.txt"
  rc=0
  out=$(bash "$self" fingerprint --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect fingerprint-one-dirty-exit 0 "$rc"
  hm_self_expect fingerprint-one-dirty 'Dirty: 1 file: base.txt' "${out#*$'\n'}"
  git -C "$repo" checkout -q -- base.txt

  local i name
  i=1
  while [ "$i" -le 20 ]; do
    name=$(printf 'dirty-%02d.txt' "$i")
    printf '%s\n' "$i" >"$repo/$name"
    i=$((i + 1))
  done
  rc=0
  out=$(bash "$self" fingerprint --repo "$repo" 2>"$tmp/err") || rc=$?
  expected='Dirty: 20 files:'
  i=1
  while [ "$i" -le 20 ]; do
    name=$(printf 'dirty-%02d.txt' "$i")
    expected="$expected $name,"
    i=$((i + 1))
  done
  expected=${expected%,}
  hm_self_expect fingerprint-twenty-dirty "$expected" "${out#*$'\n'}"
  printf '21\n' >"$repo/dirty-21.txt"
  rc=0
  out=$(bash "$self" fingerprint --repo "$repo" 2>"$tmp/err") || rc=$?
  digest=$(git --no-optional-locks -C "$repo" status --porcelain | hm_sha256_stream)
  hm_self_expect fingerprint-past-twenty-dirty "Dirty: 21 files, digest $digest" \
    "${out#*$'\n'}"
  rm -f "$repo"/dirty-*.txt

  mkdir -p "$tmp/nested/plain"
  rc=0
  out=$(bash "$self" fingerprint --repo "$tmp/nested/plain" 2>"$tmp/err") || rc=$?
  hm_self_expect fingerprint-not-repo-exit 0 "$rc"
  hm_self_expect fingerprint-not-repo-head 'HEAD: none (not a git repository)' \
    "${out%%$'\n'*}"
  hm_self_expect fingerprint-not-repo-dirty 'Dirty: none (not a git repository)' \
    "${out#*$'\n'}"

  spaced="$tmp/repo with space"
  mkdir -p "$spaced"
  hm_self_git_repo "$spaced"
  sha=$(git -C "$spaced" rev-parse --verify --short HEAD)
  branch=$(git -C "$spaced" symbolic-ref --quiet --short HEAD)
  rc=0
  out=$(bash "$self" fingerprint --repo "$spaced" 2>"$tmp/err") || rc=$?
  hm_self_expect fingerprint-space-path 0 "$rc"
  hm_self_expect fingerprint-space-head "$(printf 'HEAD: %s (%s)' "$sha" "$branch")" \
    "${out%%$'\n'*}"

  rm -rf "$spaced"
  # The spaced repository is gone; take the fingerprint from the repository the
  # remaining cases compare against.
  sha=$(git -C "$repo" rev-parse --verify --short HEAD)
  branch=$(git -C "$repo" symbolic-ref --quiet --short HEAD)
  hm_self_memo "$tmp/memo.md" "$sha" "$branch" clean
  rc=0
  out=$(bash "$self" check --memo "$tmp/memo.md" 2>"$tmp/err") || rc=$?
  hm_self_expect check-format-exit 0 "$rc"
  hm_self_expect check-format 'Format: hyper-handoff/1' "$out"

  grep -v '^- Format:' "$tmp/memo.md" >"$tmp/legacy.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/legacy.md" 2>"$tmp/err") || rc=$?
  hm_self_expect check-legacy-exit 0 "$rc"
  hm_self_expect check-legacy 'Format: legacy' "$out"

  awk '!/^## Next$/' "$tmp/memo.md" >"$tmp/no-next.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/no-next.md" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect check-missing-section-exit 1 "$rc"
  hm_self_expect_contains check-missing-section '## Next' "$err"

  sed 's/^- Status: open$/- Status: pending/' "$tmp/memo.md" >"$tmp/bad-status.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/bad-status.md" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect check-bad-status-exit 1 "$rc"
  hm_self_expect_contains check-bad-status 'Status' "$err"

  grep -v '^- Dirty:' "$tmp/memo.md" >"$tmp/no-dirty.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/no-dirty.md" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect check-missing-header-exit 1 "$rc"
  hm_self_expect_contains check-missing-header 'Dirty:' "$err"

  hm_self_memo "$tmp/memo.md" "$sha" "$branch" clean
  rc=0
  out=$(bash "$self" compare --memo "$tmp/memo.md" --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect compare-clean-exit 0 "$rc"
  hm_self_expect compare-clean 'compare: ok' "$out"

  # Full 40-character sha from the memo must match the short live fingerprint.
  full_sha=$(git -C "$repo" rev-parse --verify HEAD)
  hm_self_memo "$tmp/full.md" "$full_sha" "$branch" clean
  rc=0
  out=$(bash "$self" compare --memo "$tmp/full.md" --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect compare-full-sha-exit 0 "$rc"
  hm_self_expect compare-full-sha 'compare: ok' "$out"

  # A different commit's full sha must still fail.
  other_sha='deadbeefdeadbeefdeadbeefdeadbeefdeadbeef'
  hm_self_memo "$tmp/other-full.md" "$other_sha" "$branch" clean
  rc=0
  out=$(bash "$self" compare --memo "$tmp/other-full.md" --repo "$repo" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect compare-different-full-sha-exit 1 "$rc"
  hm_self_expect_contains compare-different-full-sha 'HEAD' "$err"

  # Body `- Format:` must not override a missing header Format line.
  hm_self_memo "$tmp/body-format.md" "$sha" "$branch" clean
  grep -v '^- Format:' "$tmp/body-format.md" >"$tmp/body-format.tmp"
  awk '
    /^## Now$/ && !done { print; print ""; print "- Format: JSON chosen by the user"; done = 1; next }
    { print }
  ' "$tmp/body-format.tmp" >"$tmp/body-format.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/body-format.md" 2>"$tmp/err") || rc=$?
  hm_self_expect check-body-format-exit 0 "$rc"
  hm_self_expect check-body-format 'Format: legacy' "$out"

  # A body `- Check:` must not hide a missing header Check line.
  hm_self_memo "$tmp/body-check.md" "$sha" "$branch" clean
  grep -v '^- Check:' "$tmp/body-check.md" >"$tmp/body-check.tmp"
  awk '
    /^## Now$/ && !done { print; print ""; print "- Check: pass"; done = 1; next }
    { print }
  ' "$tmp/body-check.tmp" >"$tmp/body-check.md"
  rc=0
  out=$(bash "$self" check --memo "$tmp/body-check.md" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect check-body-check-exit 1 "$rc"
  hm_self_expect_contains check-body-check 'Check' "$err"

  printf 'second\n' >"$repo/second.txt"
  git -C "$repo" add second.txt
  git -C "$repo" -c user.name=handoff -c user.email=handoff@example.invalid \
    commit -q -m 'selftest: second'
  rc=0
  out=$(bash "$self" compare --memo "$tmp/memo.md" --repo "$repo" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect compare-head-exit 1 "$rc"
  hm_self_expect_contains compare-head 'HEAD' "$err"

  sha=$(git -C "$repo" rev-parse --verify --short HEAD)
  hm_self_memo "$tmp/memo.md" "$sha" "$branch" clean
  printf 'untracked\n' >"$repo/untracked.txt"
  rc=0
  out=$(bash "$self" compare --memo "$tmp/memo.md" --repo "$repo" 2>"$tmp/err") || rc=$?
  err=$(cat "$tmp/err")
  hm_self_expect compare-dirty-exit 1 "$rc"
  hm_self_expect_contains compare-dirty 'Dirty' "$err"
  rm -f "$repo/untracked.txt"

  mkdir -p "$repo/.hyper/handoff/alpha" "$repo/.hyper/handoff/beta"
  hm_self_memo "$repo/.hyper/handoff/alpha/memo.md" "$sha" "$branch" clean
  hm_self_memo "$repo/.hyper/handoff/beta/memo.md" "$sha" "$branch" clean
  sed 's/^- Status: open$/- Status: closed (2026-11-10: done)/' \
    "$repo/.hyper/handoff/beta/memo.md" >"$repo/.hyper/handoff/beta/memo.tmp"
  mv "$repo/.hyper/handoff/beta/memo.tmp" "$repo/.hyper/handoff/beta/memo.md"
  rc=0
  out=$(bash "$self" list --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect list-open-exit 0 "$rc"
  hm_self_expect list-open alpha "$out"

  rm -rf "$repo/.hyper"
  rc=0
  out=$(bash "$self" list --repo "$repo" 2>"$tmp/err") || rc=$?
  hm_self_expect list-empty-exit 0 "$rc"
  hm_self_expect list-empty '' "$out"

  hm_self_memo "$tmp/memo.md" "$sha" "$branch" clean
  before_hash=$(hm_sha256_stream <"$tmp/memo.md")
  bash "$self" check --memo "$tmp/memo.md" >/dev/null 2>&1 || true
  bash "$self" compare --memo "$tmp/memo.md" --repo "$repo" >/dev/null 2>&1 || true
  bash "$self" fingerprint --repo "$repo" >/dev/null 2>&1 || true
  bash "$self" list --repo "$repo" >/dev/null 2>&1 || true
  after_hash=$(hm_sha256_stream <"$tmp/memo.md")
  hm_self_expect read-only-memo "$before_hash" "$after_hash"

  rc=0
  out=$(bash "$self" nonsense 2>"$tmp/err") || rc=$?
  hm_self_expect usage-error-exit 2 "$rc"

  if [ "$HM_SELFTEST_FAILED" -ne 0 ]; then
    printf '{"ok":false,"failed":%s,"cases":%s}\n' \
      "$HM_SELFTEST_FAILED" "$HM_SELFTEST_CASES"
    return 1
  fi
  printf '{"ok":true,"cases":%s}\n' "$HM_SELFTEST_CASES"
  return 0
}

hm_main() {
  local subcommand memo='' repo='.' seen_memo=0 seen_repo=0 flag value
  [ "$#" -gt 0 ] || hm_usage_fail 'a subcommand is required'
  case $1 in
    --help | -h)
      printf '%s\n' "$HM_USAGE"
      return 0
      ;;
    --self-test)
      hm_self_test || return $?
      return 0
      ;;
  esac
  subcommand=$1
  shift
  case $subcommand in
    fingerprint | check | compare | list) : ;;
    *) hm_usage_fail "unknown subcommand: $subcommand" ;;
  esac
  while [ "$#" -gt 0 ]; do
    flag=$1
    case $flag in
      --memo | --repo)
        [ "$#" -ge 2 ] || hm_usage_fail "$flag requires a path"
        value=$2
        case $value in
          '' | --*) hm_usage_fail "$flag requires a path" ;;
        esac
        if [ "$flag" = '--memo' ]; then
          memo=$value
          seen_memo=1
        else
          repo=$value
          seen_repo=1
        fi
        shift 2
        ;;
      *)
        hm_usage_fail "unknown argument: $flag"
        ;;
    esac
  done
  case $subcommand in
    fingerprint | list)
      [ "$seen_memo" -eq 0 ] || hm_usage_fail "$subcommand accepts only --repo <dir>"
      ;;
    check)
      [ "$seen_repo" -eq 0 ] || hm_usage_fail 'check accepts only --memo <path>'
      [ "$seen_memo" -eq 1 ] || hm_usage_fail 'check requires --memo <path>'
      ;;
    compare)
      [ "$seen_memo" -eq 1 ] || hm_usage_fail 'compare requires --memo <path>'
      ;;
  esac
  case $subcommand in
    fingerprint) hm_fingerprint "$repo" || return $? ;;
    check) hm_check "$memo" || return $? ;;
    compare) hm_compare "$memo" "$repo" || return $? ;;
    list) hm_list "$repo" || return $? ;;
  esac
  return 0
}

hm_main "$@"
