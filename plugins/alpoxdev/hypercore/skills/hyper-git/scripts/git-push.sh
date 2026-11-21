#!/usr/bin/env bash
# git-push.sh - discover repositories and push unpushed commits safely
# Usage: scripts/git-push.sh [--force] [repo...]
#
# Discovers the current git repository or descendant repositories, or uses the repositories named
# on the command line, then pushes the ones that have unpushed commits.

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
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/git-push.XXXXXX")
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

# The original interpolated the captured stderr verbatim after the prefix, so a trailing newline
# from git leaves a blank line; the silent-git fallback stays a single line.
print_git_error_prefix() {
  if [ -s "$GIT_ERR_FILE" ]; then
    printf '%s' "$1" >&2
    cat "$GIT_ERR_FILE" >&2
    printf '\n' >&2
  else
    printf '%s%s\n' "$1" "$2" >&2
  fi
}

# Copy a captured git invocation to our own streams, the way the original "output" flag did.
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

# Sets REPO_ROOT, REPO_ROOT_OK (0 = root, 1 = git error, 2 = not a repository) and REPO_ERROR.
repo_root() {
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

collect_git_paths() {
  find "$1" -mindepth 1 \
    \( -name .git \( -type d -o -type f \) -print -prune \) -o \
    \( -type d \( \
      -name node_modules -o -name dist -o -name build -o -name .next -o \
      -name .turbo -o -name .cache -o -name coverage -o -name vendor \
    \) -prune \) 2>/dev/null
}

# Print discovered repository roots, one per line. Returns non-zero when git fails.
discover_repos() {
  local start_dir=$1
  if [ ! -d "$start_dir" ]; then
    return 0
  fi
  local cwd
  cwd=$(cd "$start_dir" && pwd)
  repo_root "$cwd"
  if [ "$REPO_ROOT_OK" -eq 0 ]; then
    if [ -n "$REPO_ROOT" ]; then
      printf '%s\n' "$REPO_ROOT"
    fi
    return 0
  fi
  if [ "$REPO_ROOT_OK" -eq 1 ]; then
    print_git_error_prefix "Error: " "$REPO_ERROR"
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
    repo_root "$dir"
    if [ "$REPO_ROOT_OK" -eq 0 ]; then
      printf '%s\n' "$REPO_ROOT" >>"$roots_file"
    elif [ "$REPO_ROOT_OK" -eq 1 ]; then
      print_git_error_prefix "Error: " "$REPO_ERROR"
      return 1
    fi
  done < <(collect_git_paths "$cwd" | LC_ALL=C sort)

  LC_ALL=C sort -u "$roots_file"
  return 0
}

# Returns 0 when the trimmed git count is numerically zero.
ahead_is_zero() {
  local value=$1
  case "$value" in
    "") return 0 ;;
    *[!0-9]*) return 1 ;;
  esac
  if [ "$((10#$value))" -eq 0 ]; then
    return 0
  fi
  return 1
}

# Returns 0 (pushed), 2 (skipped) or another status (failed).
push_one_repo() {
  local repo=$1
  local force=$2
  local root branch upstream ahead

  repo_root "$repo"
  if [ "$REPO_ROOT_OK" -eq 1 ]; then
    print_git_error_prefix "[$repo] Failed: " "$REPO_ERROR"
    return 1
  fi
  if [ "$REPO_ROOT_OK" -ne 0 ] || [ -z "$REPO_ROOT" ]; then
    printf '[%s] Failed: not a git work tree\n' "$repo" >&2
    return 1
  fi
  root=$REPO_ROOT

  git_run "$root" branch --show-current
  if [ "$GIT_EXIT" -ne 0 ]; then
    REPO_ERROR=$(git_error_message branch --show-current)
    print_git_error_prefix "[$repo] Failed: " "$REPO_ERROR"
    return 1
  fi
  branch=$GIT_STDOUT
  if [ -z "$branch" ]; then
    printf '[%s] Skipped: detached HEAD\n' "$root" >&2
    return 2
  fi

  if [ "$force" -eq 1 ] && { [ "$branch" = "main" ] || [ "$branch" = "master" ]; }; then
    printf '[%s] Skipped: cannot force push to protected branch %s\n' "$root" "$branch" >&2
    return 2
  fi

  git_run "$root" for-each-ref --format='%(upstream:short)' "refs/heads/$branch"
  if [ "$GIT_EXIT" -ne 0 ]; then
    REPO_ERROR=$(git_error_message for-each-ref '--format=%(upstream:short)' "refs/heads/$branch")
    print_git_error_prefix "[$repo] Failed: " "$REPO_ERROR"
    return 1
  fi
  upstream=$GIT_STDOUT

  if [ -n "$upstream" ]; then
    git_run "$root" rev-list --count '@{upstream}..HEAD'
    if [ "$GIT_EXIT" -ne 0 ]; then
      REPO_ERROR=$(git_error_message rev-list --count '@{upstream}..HEAD')
      print_git_error_prefix "[$repo] Failed: " "$REPO_ERROR"
      return 1
    fi
    ahead=$GIT_STDOUT
    if ahead_is_zero "$ahead"; then
      printf '[%s] Already up to date on %s\n' "$root" "$branch"
      return 2
    fi
    printf '[%s] Pushing %s commit(s) on %s...\n' "$root" "$ahead" "$branch"
    GIT_PROMPT_OFF=1
    if [ "$force" -eq 1 ]; then
      git_run "$root" push --force-with-lease
    else
      git_run "$root" push
    fi
    emit_git_output
    GIT_PROMPT_OFF=0
    return "$GIT_EXIT"
  fi

  printf '[%s] No upstream. Pushing %s to origin...\n' "$root" "$branch"
  GIT_PROMPT_OFF=1
  if [ "$force" -eq 1 ]; then
    git_run "$root" push -u origin "$branch" --force-with-lease
  else
    git_run "$root" push -u origin "$branch"
  fi
  emit_git_output
  GIT_PROMPT_OFF=0
  return "$GIT_EXIT"
}

main() {
  local force=0
  local -a repos=()
  local arg
  for arg in "$@"; do
    if [ "$arg" = "--force" ]; then
      force=1
    elif [ "$arg" = "-h" ] || [ "$arg" = "--help" ]; then
      printf 'Usage: %s [--force] [repo...]\n' "$0" >&2
      return 0
    elif [[ "$arg" == -* ]]; then
      printf 'Usage: %s [--force] [repo...]\n' "$0" >&2
      return 1
    else
      repos[${#repos[@]}]=$arg
    fi
  done

  if [ "${#repos[@]}" -eq 0 ]; then
    local discovered=""
    if ! discovered=$(discover_repos .); then
      return 1
    fi
    local line
    while IFS= read -r line; do
      if [ -n "$line" ]; then
        repos[${#repos[@]}]=$line
      fi
    done <<<"$discovered"
  fi

  if [ "${#repos[@]}" -eq 0 ]; then
    printf 'Error: No git repository found\n' >&2
    return 1
  fi

  local pushed=0 skipped=0 errors=0 rc repo
  for repo in "${repos[@]}"; do
    rc=0
    push_one_repo "$repo" "$force" || rc=$?
    if [ "$rc" -eq 0 ]; then
      pushed=$((pushed + 1))
    elif [ "$rc" -eq 2 ]; then
      skipped=$((skipped + 1))
    else
      errors=$((errors + 1))
    fi
  done

  printf '\n'
  printf 'Done: %s pushed, %s skipped, %s failed\n' "$pushed" "$skipped" "$errors"
  if [ "$errors" -eq 0 ]; then
    return 0
  fi
  return 1
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
