#!/usr/bin/env bash
# repo-status.sh - summarize git state for one repository
# Usage: scripts/repo-status.sh [repo]

set -euo pipefail

# The original implementation reached the filesystem through runtime APIs; the bash port shells
# out to POSIX tools, so make sure the standard locations stay reachable when a caller passes a
# deliberately minimal PATH (for example a fixture directory holding only a fake git).
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
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/repo-status.XXXXXX")
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

# Trailing whitespace is stripped the same way String.prototype.trimEnd does it; the trailing
# newlines from command substitution are already gone by the time this runs.
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

# Mirrors requiredGit in the original: on failure the captured stderr (or a status line when git
# was silent) is copied to stderr and a non-zero status is returned.
required_git() {
  local cwd=$1
  shift
  git_run "$cwd" "$@"
  if [ "$GIT_EXIT" -eq 0 ]; then
    return 0
  fi
  if [ -s "$GIT_ERR_FILE" ]; then
    cat "$GIT_ERR_FILE" >&2
  else
    printf 'Error: git %s failed with exit code %s\n' "$*" "$GIT_EXIT" >&2
  fi
  return 1
}

main() {
  if [ "$#" -gt 1 ] || [[ "${1:-}" == -* ]]; then
    printf 'Usage: %s [repo]\n' "$0" >&2
    return 1
  fi
  local repo=${1:-.}
  if [ ! -d "$repo" ]; then
    printf 'Error: Directory not found: %s\n' "$repo" >&2
    return 1
  fi
  local cwd
  cwd=$(cd "$repo" && pwd)

  if ! required_git "$cwd" rev-parse --git-dir; then
    return 1
  fi

  local root status_short staged_stat unstaged_stat
  if ! required_git "$cwd" rev-parse --show-toplevel; then
    return 1
  fi
  root=$GIT_STDOUT
  if ! required_git "$cwd" status --short --no-renames; then
    return 1
  fi
  status_short=$GIT_STDOUT
  if ! required_git "$cwd" diff --staged --stat; then
    return 1
  fi
  staged_stat=$GIT_STDOUT
  if ! required_git "$cwd" diff --stat; then
    return 1
  fi
  unstaged_stat=$GIT_STDOUT

  local -a untracked=()
  local line
  if [ -n "$status_short" ]; then
    while IFS= read -r line; do
      case "$line" in
        "?? "*) untracked[${#untracked[@]}]=${line#???} ;;
      esac
    done <<<"$status_short"
  fi

  printf 'repo|%s\n' "$root"
  printf 'status|begin\n'
  if [ -n "$status_short" ]; then
    printf '%s\n' "$status_short"
  fi
  printf 'status|end\n'
  printf 'staged|begin\n'
  printf '%s\n' "${staged_stat:-(no staged changes)}"
  printf 'staged|end\n'
  printf 'unstaged|begin\n'
  if [ -z "$unstaged_stat" ] && [ "${#untracked[@]}" -eq 0 ]; then
    printf '(no unstaged changes)\n'
  else
    if [ -n "$unstaged_stat" ]; then
      printf '%s\n' "$unstaged_stat"
    fi
    local file
    for file in "${untracked[@]+"${untracked[@]}"}"; do
      if [ -n "$file" ]; then
        printf 'untracked: %s\n' "$file"
      fi
    done
  fi
  printf 'unstaged|end\n'
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
