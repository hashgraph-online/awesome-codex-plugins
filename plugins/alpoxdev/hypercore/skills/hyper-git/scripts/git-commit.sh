#!/usr/bin/env bash
# git-commit.sh - commit staged or selected files in one repository
# Usage: scripts/git-commit.sh [--repo path] "commit message" [files...]
#
# With explicit files the commit is limited to those paths: the index is checked before staging so
# a failed targeted request never rewrites unrelated staged changes.

set -euo pipefail

# The original implementation used runtime filesystem APIs; the bash port shells out to POSIX
# tools, so add the standard locations when a caller passes a minimal PATH.
harden_path() {
  local dir
  for dir in /usr/bin /bin /usr/local/bin; do
    case ":$PATH:" in
      *":$dir:"*) ;;
      *) PATH="$PATH:$dir" ;;
    esac
  done
}
harden_path

ORIG_PWD=$(pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/git-commit.XXXXXX")
GIT_TMP=$TMP_ROOT
GIT_EXIT=0
GIT_STDOUT=""
GIT_STDERR=""
GIT_ERR_FILE="$TMP_ROOT/err"
GIT_PROMPT_OFF=0
CURRENT_PID=""
RECEIVED_SIGNAL=""

# Invoked from the EXIT trap below.
# shellcheck disable=SC2329
cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

trim_end() {
  local value=$1
  while [ -n "$value" ] && [[ "$value" == *[[:space:]] ]]; do
    value=${value%?}
  done
  printf '%s' "$value"
}

# Record the signal and forward it to the running git child. The main flow still finishes (later
# git calls report "Interrupted by signal") and the process re-raises the signal at the end,
# matching the original runner's settle().
# Invoked from the INT/TERM traps below.
# shellcheck disable=SC2329
handle_signal() {
  local signal=$1
  RECEIVED_SIGNAL=$signal
  if [ -n "$CURRENT_PID" ]; then
    kill -s "$signal" "$CURRENT_PID" 2>/dev/null || true
  fi
}
trap 'handle_signal INT' INT
trap 'handle_signal TERM' TERM

# Run git in cwd, capturing both streams. Sets GIT_EXIT, GIT_STDOUT, GIT_STDERR.
git_run() {
  local cwd=$1
  shift
  GIT_EXIT=0
  GIT_STDOUT=""
  GIT_STDERR=""
  GIT_ERR_FILE="$GIT_TMP/err"
  local out_file="$GIT_TMP/out"
  : >"$out_file"
  : >"$GIT_ERR_FILE"
  if [ -n "$RECEIVED_SIGNAL" ]; then
    GIT_EXIT=130
    GIT_STDERR="Interrupted by signal"
    printf '%s' "$GIT_STDERR" >"$GIT_ERR_FILE"
    return 0
  fi
  cd "$ORIG_PWD" || true
  if [ ! -d "$cwd" ]; then
    GIT_EXIT=1
    GIT_STDERR="ENOENT: no such file or directory, chdir '$cwd'"
    printf '%s' "$GIT_STDERR" >"$GIT_ERR_FILE"
    return 0
  fi
  cd "$cwd" || {
    GIT_EXIT=1
    GIT_STDERR="ENOENT: no such file or directory, chdir '$cwd'"
    printf '%s' "$GIT_STDERR" >"$GIT_ERR_FILE"
    return 0
  }
  # Job control is enabled only around the fork: a non-interactive shell marks plain background
  # children as SIGINT-ignored, and an ignored signal cannot be trapped, so a forwarded interrupt
  # would never reach git.
  set -m
  if [ "$GIT_PROMPT_OFF" -eq 1 ]; then
    GIT_TERMINAL_PROMPT=0 git "$@" >"$out_file" 2>"$GIT_ERR_FILE" &
  else
    git "$@" >"$out_file" 2>"$GIT_ERR_FILE" &
  fi
  CURRENT_PID=$!
  set +m
  local rc=0
  wait "$CURRENT_PID" || rc=$?
  if [ -n "$RECEIVED_SIGNAL" ]; then
    # A trapped signal interrupts wait without reaping the child; this call reaps it.
    wait "$CURRENT_PID" 2>/dev/null || true
  fi
  CURRENT_PID=""
  GIT_EXIT=$rc
  GIT_STDOUT=$(trim_end "$(cat "$out_file")")
  GIT_STDERR=$(trim_end "$(cat "$GIT_ERR_FILE")")
  return 0
}

git_error_message() {
  if [ -n "$GIT_STDERR" ]; then
    printf '%s' "$GIT_STDERR"
  else
    printf 'git %s failed with exit code %s' "$*" "$GIT_EXIT"
  fi
}

# The original dropped the captured stderr verbatim into "Error: <message>", so a trailing newline
# from git produces the same blank line; only the silent-git fallback is a single line.
print_latest_git_error() {
  if [ -s "$GIT_ERR_FILE" ]; then
    printf 'Error: ' >&2
    cat "$GIT_ERR_FILE" >&2
    printf '\n' >&2
  else
    printf 'Error: %s\n' "$LAST_GIT_ERROR" >&2
  fi
}

emit_git_output() {
  if [ -s "$GIT_TMP/out" ]; then
    cat "$GIT_TMP/out"
  fi
  if [ -s "$GIT_TMP/err" ]; then
    cat "$GIT_TMP/err" >&2
  fi
}

is_not_git_repository() {
  local had_case=0 rc=1
  if shopt -q nocasematch; then had_case=1; fi
  shopt -s nocasematch
  case "$GIT_STDERR" in
    *"not a git repository"*) rc=0 ;;
  esac
  if [ "$had_case" -eq 0 ]; then shopt -u nocasematch; fi
  return "$rc"
}

# Mirrors requiredGit: LAST_GIT_ERROR carries the message used when git wrote nothing to stderr.
required_git() {
  local cwd=$1
  shift
  git_run "$cwd" "$@"
  if [ "$GIT_EXIT" -eq 0 ]; then
    return 0
  fi
  LAST_GIT_ERROR=$(git_error_message "$@")
  return 1
}

# Mirrors diffHasChanges: DIFF_CHANGED is 1 on exit code 1, 0 on exit code 0, and any other exit
# code is an error reported through LAST_GIT_ERROR.
diff_has_changes() {
  local cwd=$1
  shift
  git_run "$cwd" "$@"
  if [ "$GIT_EXIT" -eq 0 ]; then
    DIFF_CHANGED=0
    return 0
  fi
  if [ "$GIT_EXIT" -eq 1 ]; then
    DIFF_CHANGED=1
    return 0
  fi
  LAST_GIT_ERROR=$(git_error_message "$@")
  return 1
}

matches_requested_target() {
  local staged_file=$1
  shift
  local target
  for target in "$@"; do
    if [ "$staged_file" = "$target" ] || [[ "$staged_file" == "$target"/* ]]; then
      return 0
    fi
  done
  return 1
}

usage() {
  printf 'Usage: %s [--repo path] "commit message" [files...]\n' "$0" >&2
}

main() {
  local repo="."
  if [ "$#" -gt 0 ] && [ "$1" = "--repo" ]; then
    if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
      usage
      return 1
    fi
    repo=$2
    shift 2
  fi

  if [ "$#" -gt 0 ] && [[ "$1" == --* ]]; then
    usage
    return 1
  fi

  if [ "$#" -eq 0 ]; then
    usage
    return 1
  fi
  local message=$1
  shift
  if [ -z "$message" ]; then
    usage
    return 1
  fi

  if [[ ! "$message" =~ [^[:space:]] ]]; then
    printf 'Error: Commit message cannot be empty\n' >&2
    return 1
  fi

  if [ ! -d "$repo" ]; then
    printf 'Error: Directory not found: %s\n' "$repo" >&2
    return 1
  fi

  local cwd
  cwd=$(cd "$repo" && pwd)

  git_run "$cwd" rev-parse --git-dir
  if [ "$GIT_EXIT" -ne 0 ]; then
    if is_not_git_repository; then
      printf 'Error: Not a git repository: %s\n' "$repo" >&2
    else
      LAST_GIT_ERROR=$(git_error_message rev-parse --git-dir)
      print_latest_git_error
    fi
    return 1
  fi

  local -a requested=("$@")
  local file
  for file in "${requested[@]+"${requested[@]}"}"; do
    if [[ "$file" == --* ]]; then
      usage
      return 1
    fi
  done

  if [ "${#requested[@]}" -gt 0 ]; then
    if ! required_git "$cwd" diff --cached --name-only; then
      print_latest_git_error
      return 1
    fi
    local -a extra=()
    while IFS= read -r file; do
      if [ -n "$file" ]; then
        if ! matches_requested_target "$file" "${requested[@]}"; then
          extra[${#extra[@]}]=$file
        fi
      fi
    done <<<"$GIT_STDOUT"
    if [ "${#extra[@]}" -gt 0 ]; then
      printf 'Error: Additional staged changes exist outside the requested files:\n' >&2
      local staged
      for staged in "${extra[@]}"; do
        printf '  %s\n' "$staged" >&2
      done
      printf 'Tip: Unstage unrelated files or commit them separately before retrying.\n' >&2
      return 1
    fi

    # Preflight before staging prevents a failed targeted request from altering the index.
    local changed=0
    if ! diff_has_changes "$cwd" diff --quiet -- "${requested[@]}"; then
      print_latest_git_error
      return 1
    fi
    if [ "$DIFF_CHANGED" -eq 1 ]; then
      changed=1
    else
      if ! diff_has_changes "$cwd" diff --cached --quiet -- "${requested[@]}"; then
        print_latest_git_error
        return 1
      fi
      changed=$DIFF_CHANGED
    fi

    if ! required_git "$cwd" ls-files --others --exclude-standard -- "${requested[@]}"; then
      print_latest_git_error
      return 1
    fi
    local untracked=$GIT_STDOUT
    if [ "$changed" -eq 0 ] && [ -z "$untracked" ]; then
      printf 'Error: No changes found in the requested files\n' >&2
      return 1
    fi

    git_run "$cwd" add -- "${requested[@]}"
    emit_git_output
    if [ "$GIT_EXIT" -ne 0 ]; then
      return 1
    fi

    if ! required_git "$cwd" diff --cached --name-only; then
      print_latest_git_error
      return 1
    fi
    local -a appeared=()
    while IFS= read -r file; do
      if [ -n "$file" ]; then
        if ! matches_requested_target "$file" "${requested[@]}"; then
          appeared[${#appeared[@]}]=$file
        fi
      fi
    done <<<"$GIT_STDOUT"
    if [ "${#appeared[@]}" -gt 0 ]; then
      printf 'Error: Additional staged changes appeared while staging:\n' >&2
      local staged
      for staged in "${appeared[@]}"; do
        printf '  %s\n' "$staged" >&2
      done
      return 1
    fi
  fi

  if ! diff_has_changes "$cwd" diff --cached --quiet; then
    print_latest_git_error
    return 1
  fi
  if [ "$DIFF_CHANGED" -eq 0 ]; then
    printf 'Error: No staged changes to commit\n' >&2
    return 1
  fi

  git_run "$cwd" commit -m "$message"
  emit_git_output
  if [ "$GIT_EXIT" -ne 0 ]; then
    return 1
  fi

  if ! required_git "$cwd" rev-parse --show-toplevel; then
    print_latest_git_error
    return 1
  fi
  printf 'Committed successfully in %s\n' "$GIT_STDOUT"
  return 0
}

status=0
main "$@" || status=$?
if [ -n "$RECEIVED_SIGNAL" ]; then
  trap - INT TERM
  kill -s "$RECEIVED_SIGNAL" $$ 2>/dev/null || true
  if [ "$RECEIVED_SIGNAL" = "INT" ]; then
    exit 130
  fi
  exit 143
fi
exit "$status"
