#!/usr/bin/env bash
# repo-discover.sh - detect the current or descendant git repositories from a start directory
# Usage: scripts/repo-discover.sh [start_dir]

set -euo pipefail

# The original implementation walked directories through runtime APIs; the bash port uses POSIX
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
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/repo-discover.XXXXXX")
GIT_TMP=$TMP_ROOT
GIT_EXIT=0
GIT_STDOUT=""
GIT_STDERR=""
GIT_ERR_FILE="$TMP_ROOT/err"
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
  git "$@" >"$out_file" 2>"$GIT_ERR_FILE" &
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

# The original interpolated the captured stderr verbatim, so a trailing newline from git leaves a
# blank line after the message; the silent-git fallback stays a single line.
print_repo_error() {
  if [ -s "$GIT_ERR_FILE" ]; then
    printf 'Error: ' >&2
    cat "$GIT_ERR_FILE" >&2
    printf '\n' >&2
  else
    printf 'Error: %s\n' "$REPO_ERROR" >&2
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

# Resolve the work-tree root for path without failing on "not a git repository".
# Sets REPO_ROOT, REPO_ROOT_OK (0 = root, 1 = git error, 2 = not a repository) and REPO_ERROR.
repo_root_allow() {
  REPO_ROOT=""
  REPO_ROOT_OK=2
  REPO_ERROR=""
  git_run "$1" rev-parse --show-toplevel
  if [ "$GIT_EXIT" -eq 0 ]; then
    REPO_ROOT=$GIT_STDOUT
    REPO_ROOT_OK=0
  elif is_not_git_repository; then
    REPO_ROOT_OK=2
  else
    REPO_ERROR=$(git_error_message rev-parse --show-toplevel)
    REPO_ROOT_OK=1
  fi
  return 0
}

# Emit every .git entry (directory or linked-worktree file) below directory while pruning
# generated trees. The walk never descends into .git itself, matching the original collector.
collect_git_paths() {
  find "$1" -mindepth 1 \
    \( -name .git \( -type d -o -type f \) -print -prune \) -o \
    \( -type d \( \
      -name node_modules -o -name dist -o -name build -o -name .next -o \
      -name .turbo -o -name .cache -o -name coverage -o -name vendor \
    \) -prune \) 2>/dev/null
}

main() {
  if [ "$#" -gt 1 ] || [[ "${1:-}" == -* ]]; then
    printf 'Usage: %s [start_dir]\n' "$0" >&2
    return 1
  fi
  local start_dir=${1:-.}
  if [ ! -d "$start_dir" ]; then
    printf 'Error: Directory not found: %s\n' "$start_dir" >&2
    return 1
  fi
  local cwd
  cwd=$(cd "$start_dir" && pwd)

  repo_root_allow "$cwd"
  if [ "$REPO_ROOT_OK" -eq 0 ] && [ -n "$REPO_ROOT" ]; then
    printf 'current|%s\n' "$REPO_ROOT"
    return 0
  fi
  if [ "$REPO_ROOT_OK" -eq 1 ]; then
    print_repo_error
    return 1
  fi

  local roots_file="$TMP_ROOT/roots"
  : >"$roots_file"
  local git_path dir
  while IFS= read -r git_path; do
    if [ -z "$git_path" ]; then
      continue
    fi
    dir=${git_path%/*}
    if [ -z "$dir" ]; then
      dir=/
    fi
    repo_root_allow "$dir"
    if [ "$REPO_ROOT_OK" -eq 0 ]; then
      printf '%s\n' "$REPO_ROOT" >>"$roots_file"
    elif [ "$REPO_ROOT_OK" -eq 1 ]; then
      print_repo_error
      return 1
    fi
  done < <(collect_git_paths "$cwd" | LC_ALL=C sort)

  local found=0 root
  while IFS= read -r root; do
    if [ -n "$root" ]; then
      printf 'descendant|%s\n' "$root"
      found=1
    fi
  done < <(LC_ALL=C sort -u "$roots_file")

  if [ "$found" -eq 0 ]; then
    printf 'Error: No git repository found from %s\n' "$start_dir" >&2
    return 1
  fi
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
