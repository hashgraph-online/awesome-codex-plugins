#!/usr/bin/env bash
# git-fast.sh - fast inspect/push helper for the hyper-git commit mode
# Usage:
#   git-fast.sh inspect [start_dir] [--jobs N]
#   git-fast.sh push [--force] [repo...]
#
# Inspect gathers repository state with pruned discovery and bounded parallel per-repo status
# while keeping the emitted blocks in repository order. Linked git worktrees are treated as
# first-class checkout roots; never assume .git is a directory. Push accepts explicit repo paths so
# the commit mode can reuse inspect results instead of rediscovering them.

set -euo pipefail

# The original implementation collected repository state through runtime APIs; the bash port uses
# POSIX tools, so add the standard locations when a caller passes a minimal PATH.
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
tmp_base=${TMPDIR:-/tmp}
tmp_base=${tmp_base%/}
TMP_ROOT=$(mktemp -d "$tmp_base/git-fast.XXXXXX")
GIT_TMP=$TMP_ROOT
GIT_EXIT=0
GIT_STDOUT=""
GIT_STDERR=""
GIT_ERR_FILE="$TMP_ROOT/err"
GIT_PROMPT_OFF=0
CURRENT_PID=""
RECEIVED_SIGNAL=""
REPOS=()
ACTIVE_PIDS=()

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

# Parent-side signal handling: forward the signal to the active workers. The pool then unwinds
# through the normal failure path and the process re-raises the signal when it exits, matching the
# original runner's stop() plus settle().
# Invoked from the INT/TERM traps below.
# shellcheck disable=SC2329
handle_signal() {
  local signal=$1
  local pid
  RECEIVED_SIGNAL=$signal
  for pid in "${ACTIVE_PIDS[@]+"${ACTIVE_PIDS[@]}"}"; do
    kill -s "$signal" "$pid" 2>/dev/null || true
  done
}
trap 'handle_signal INT' INT
trap 'handle_signal TERM' TERM

# Worker-side signal handling: forward the signal to the git child the worker is waiting on. The
# worker then finishes its normal failure path so its stderr carries the git error message.
# Invoked from the worker traps in status_worker.
# shellcheck disable=SC2329
worker_signal() {
  local signal=$1
  RECEIVED_SIGNAL=$signal
  if [ -n "$CURRENT_PID" ]; then
    kill -s "$signal" "$CURRENT_PID" 2>/dev/null || true
  fi
}

# Run git in cwd, capturing both streams. Sets GIT_EXIT, GIT_STDOUT (trimmed), GIT_STDERR (trimmed).
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

# Report a failed git call the way a thrown gitError message reads before the caller prefixes it.
git_failure() {
  printf '%s\n' "$(git_error_message "$@")" >&2
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

collect_git_paths() {
  find "$1" -mindepth 1 \
    \( -name .git \( -type d -o -type f \) -print -prune \) -o \
    \( -type d \( \
      -name node_modules -o -name dist -o -name build -o -name .next -o \
      -name .turbo -o -name .cache -o -name coverage -o -name vendor \
    \) -prune \) 2>/dev/null
}

# Print repository roots, one per line. Errors are reported directly on stderr.
discover_repos() {
  local start_dir=$1
  if [ ! -d "$start_dir" ]; then
    printf 'Error: Directory not found: %s\n' "$start_dir" >&2
    return 1
  fi
  cd "$ORIG_PWD" || true
  local cwd
  cwd=$(cd "$start_dir" && pwd)

  git_run "$cwd" rev-parse --show-toplevel
  if [ "$GIT_EXIT" -eq 0 ]; then
    if [ -n "$GIT_STDOUT" ]; then
      printf '%s\n' "$GIT_STDOUT"
    fi
    return 0
  fi
  if ! is_not_git_repository; then
    printf 'Error: %s\n' "$(git_error_message rev-parse --show-toplevel)" >&2
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
    git_run "$dir" rev-parse --show-toplevel
    if [ "$GIT_EXIT" -ne 0 ]; then
      printf 'Error: %s\n' "$(git_error_message rev-parse --show-toplevel)" >&2
      return 1
    fi
    if [ -n "$GIT_STDOUT" ]; then
      printf '%s\n' "$GIT_STDOUT" >>"$roots_file"
    fi
  done < <(collect_git_paths "$cwd" | LC_ALL=C sort)

  LC_ALL=C sort -u "$roots_file"
  return 0
}

# Emit the per-repository status block for one repository on stdout; errors go to stderr.
status_one_repo() {
  local repo=$1
  local root git_dir common_dir branch upstream ahead="" status_text line code file worktree

  git_run "$repo" rev-parse --is-inside-work-tree
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure rev-parse --is-inside-work-tree
    return 1
  fi
  if [ "$GIT_STDOUT" != "true" ]; then
    printf '[%s] not a git work tree\n' "$repo" >&2
    return 1
  fi

  git_run "$repo" rev-parse --show-toplevel
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure rev-parse --show-toplevel
    return 1
  fi
  root=$GIT_STDOUT
  if [ -z "$root" ]; then
    printf '[%s] not a git work tree\n' "$repo" >&2
    return 1
  fi

  git_run "$root" rev-parse --git-dir
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure rev-parse --git-dir
    return 1
  fi
  git_dir=$GIT_STDOUT

  git_run "$root" rev-parse --git-common-dir
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure rev-parse --git-common-dir
    return 1
  fi
  common_dir=$GIT_STDOUT

  git_run "$root" branch --show-current
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure branch --show-current
    return 1
  fi
  branch=$GIT_STDOUT

  git_run "$root" status --short --no-renames
  if [ "$GIT_EXIT" -ne 0 ]; then
    git_failure status --short --no-renames
    return 1
  fi
  status_text=$GIT_STDOUT

  upstream=""
  if [ -n "$branch" ]; then
    git_run "$root" for-each-ref --format='%(upstream:short)' "refs/heads/$branch"
    if [ "$GIT_EXIT" -ne 0 ]; then
      git_failure for-each-ref '--format=%(upstream:short)' "refs/heads/$branch"
      return 1
    fi
    upstream=$GIT_STDOUT
  fi

  ahead="0"
  if [ -n "$upstream" ]; then
    git_run "$root" rev-list --count '@{upstream}..HEAD'
    if [ "$GIT_EXIT" -ne 0 ]; then
      git_failure rev-list --count '@{upstream}..HEAD'
      return 1
    fi
    ahead=$GIT_STDOUT
    if [ -z "$ahead" ]; then
      ahead="0"
    fi
  fi

  worktree="primary"
  if [ -n "$git_dir" ] && [ -n "$common_dir" ] && [ "$git_dir" != "$common_dir" ]; then
    worktree="linked"
  fi

  printf 'repo|%s\n' "$root"
  printf 'worktree|%s\n' "$worktree"
  printf 'git-dir|%s\n' "$git_dir"
  printf 'git-common-dir|%s\n' "$common_dir"
  printf 'branch|%s\n' "${branch:-DETACHED}"
  printf 'upstream|%s\n' "${upstream:-none}"
  printf 'ahead|%s\n' "$ahead"
  printf 'status|begin\n'
  if [ -n "$status_text" ]; then
    printf '%s\n' "$status_text"
  fi
  printf 'status|end\n'
  printf 'files|begin\n'
  if [ -n "$status_text" ]; then
    while IFS= read -r line; do
      code=${line:0:2}
      file=${line:3}
      if [ "$code" = "??" ]; then
        printf 'untracked|%s\n' "$file"
      else
        if [ "${code:0:1}" != " " ]; then
          printf 'staged|%s\n' "$file"
        fi
        if [ "${code:1:1}" != " " ]; then
          printf 'unstaged|%s\n' "$file"
        fi
      fi
    done <<<"$status_text"
  fi
  printf 'files|end\n'
  return 0
}

# One parallel slot: runs in its own subshell with a private scratch directory and owns the signal
# forwarding for the git child it waits on.
status_worker() {
  local index=$1
  local repo=$2
  local out_file=$3
  local err_file=$4
  local rc=0
  CURRENT_PID=""
  trap 'worker_signal INT' INT
  trap 'worker_signal TERM' TERM
  GIT_TMP=$(mktemp -d "$TMP_ROOT/job.XXXXXX")
  status_one_repo "$repo" >"$out_file" 2>"$err_file" || rc=$?
  exit "$rc"
}

# Terminate the workers that are still running and reap them.
stop_active() {
  local pid
  for pid in "${ACTIVE_PIDS[@]+"${ACTIVE_PIDS[@]}"}"; do
    kill -s TERM "$pid" 2>/dev/null || true
  done
  for pid in "${ACTIVE_PIDS[@]+"${ACTIVE_PIDS[@]}"}"; do
    wait "$pid" 2>/dev/null || true
  done
  ACTIVE_PIDS=()
}

# Run status_one_repo for every repository with at most $1 concurrent workers. Blocks are written
# to per-repository files so the caller can emit them in repository order. Returns non-zero on the
# first worker failure, after stopping the work that has not started yet.
run_status_pool() {
  local jobs=$1
  local total=${#REPOS[@]}
  local next=0 rc=0 pid index
  local -a pids=()
  local -a indices=()

  while [ "$next" -lt "$total" ] || [ "${#pids[@]}" -gt 0 ]; do
    while [ "${#pids[@]}" -lt "$jobs" ] && [ "$next" -lt "$total" ]; do
      # Same reason as in git_run: only a job-control fork keeps the worker's SIGINT disposition
      # at default so worker_signal can forward the interrupt to its git child.
      set -m
      status_worker "$next" "${REPOS[$next]}" "$TMP_ROOT/status.$next.out" "$TMP_ROOT/status.$next.err" &
      pids[${#pids[@]}]=$!
      set +m
      indices[${#indices[@]}]=$next
      ACTIVE_PIDS=(${pids[@]+"${pids[@]}"})
      next=$((next + 1))
    done

    pid=${pids[0]}
    index=${indices[0]}
    rc=0
    wait "$pid" || rc=$?
    if [ -n "$RECEIVED_SIGNAL" ]; then
      # The interrupted wait did not reap the worker; the second call blocks until it exits.
      wait "$pid" 2>/dev/null || true
    fi
    if [ "${#pids[@]}" -gt 1 ]; then
      pids=("${pids[@]:1}")
      indices=("${indices[@]:1}")
    else
      pids=()
      indices=()
    fi
    ACTIVE_PIDS=(${pids[@]+"${pids[@]}"})

    if [ "$rc" -ne 0 ]; then
      stop_active
      printf 'Error: %s\n' "$(trim_end "$(cat "$TMP_ROOT/status.$index.err")")" >&2
      return 1
    fi
  done
  return 0
}

# Values that are not a positive integer fall back to 4, matching the original validation.
normalize_jobs() {
  local value=$1
  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    printf '4'
    return 0
  fi
  value=${value#"${value%%[!0]*}"}
  if [ -z "$value" ]; then
    printf '4'
    return 0
  fi
  if [ "${#value}" -gt 9 ]; then
    value=999999999
  fi
  printf '%s' "$value"
}

inspect_command() {
  local start_dir="."
  local jobs=${HYPER_GIT_JOBS:-4}
  local seen_start=0
  local arg line

  while [ "$#" -gt 0 ]; do
    arg=$1
    shift
    if [ "$arg" = "--jobs" ]; then
      if [ "$#" -eq 0 ]; then
        printf 'Error: --jobs requires a value\n' >&2
        return 1
      fi
      jobs=$1
      shift
      if [ -z "$jobs" ]; then
        printf 'Error: --jobs requires a value\n' >&2
        return 1
      fi
    elif [[ "$arg" == --jobs=* ]]; then
      jobs=${arg#--jobs=}
    elif [ "$arg" = "-h" ] || [ "$arg" = "--help" ]; then
      usage
      return 0
    elif [[ "$arg" == -* ]] || [ "$seen_start" -eq 1 ]; then
      usage
      return 1
    else
      start_dir=$arg
      seen_start=1
    fi
  done

  jobs=$(normalize_jobs "$jobs")

  if ! discover_repos "$start_dir" >"$TMP_ROOT/repos"; then
    return 1
  fi

  REPOS=()
  if [ -s "$TMP_ROOT/repos" ]; then
    while IFS= read -r line; do
      if [ -n "$line" ]; then
        REPOS[${#REPOS[@]}]=$line
      fi
    done <"$TMP_ROOT/repos"
  fi

  if [ "${#REPOS[@]}" -eq 0 ]; then
    printf 'Error: No git repository found from %s\n' "$start_dir" >&2
    return 1
  fi

  printf 'repos|begin\n'
  local repo
  for repo in "${REPOS[@]}"; do
    printf '%s\n' "$repo"
  done
  printf 'repos|end\n'

  if ! run_status_pool "$jobs"; then
    return 1
  fi

  local i
  for ((i = 0; i < ${#REPOS[@]}; i++)); do
    printf 'repo-status|begin\n'
    cat "$TMP_ROOT/status.$i.out"
    printf 'repo-status|end\n'
  done
  return 0
}

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

# Returns 0 (pushed), 2 (skipped) or the git push status (failed). Errors while inspecting the
# repository are fatal, matching an error that escapes the original push command.
push_one_repo() {
  local repo=$1
  local force=$2
  local root branch upstream ahead

  git_run "$repo" rev-parse --show-toplevel
  if [ "$GIT_EXIT" -ne 0 ]; then
    printf 'Error: %s\n' "$(git_error_message rev-parse --show-toplevel)" >&2
    exit 1
  fi
  root=$GIT_STDOUT
  if [ -z "$root" ]; then
    printf '[%s] Failed: not a git work tree\n' "$repo" >&2
    exit 1
  fi

  git_run "$root" branch --show-current
  if [ "$GIT_EXIT" -ne 0 ]; then
    printf 'Error: %s\n' "$(git_error_message branch --show-current)" >&2
    exit 1
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
    printf 'Error: %s\n' "$(git_error_message for-each-ref '--format=%(upstream:short)' "refs/heads/$branch")" >&2
    exit 1
  fi
  upstream=$GIT_STDOUT

  GIT_PROMPT_OFF=1
  if [ -n "$upstream" ]; then
    git_run "$root" rev-list --count '@{upstream}..HEAD'
    if [ "$GIT_EXIT" -ne 0 ]; then
      printf 'Error: %s\n' "$(git_error_message rev-list --count '@{upstream}..HEAD')" >&2
      exit 1
    fi
    ahead=$GIT_STDOUT
    if [ -z "$ahead" ]; then
      ahead="0"
    fi
    if ahead_is_zero "$ahead"; then
      printf '[%s] Already up to date on %s\n' "$root" "$branch"
      GIT_PROMPT_OFF=0
      return 2
    fi
    printf '[%s] Pushing %s commit(s) on %s...\n' "$root" "$ahead" "$branch"
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
  if [ "$force" -eq 1 ]; then
    git_run "$root" push -u origin "$branch" --force-with-lease
  else
    git_run "$root" push -u origin "$branch"
  fi
  emit_git_output
  GIT_PROMPT_OFF=0
  return "$GIT_EXIT"
}

push_command() {
  local force=0
  local -a repos=()
  local arg line repo

  for arg in "$@"; do
    if [ "$arg" = "--force" ]; then
      force=1
    elif [ "$arg" = "-h" ] || [ "$arg" = "--help" ]; then
      usage
      return 0
    elif [[ "$arg" == -* ]]; then
      usage
      return 1
    else
      repos[${#repos[@]}]=$arg
    fi
  done

  if [ "${#repos[@]}" -eq 0 ]; then
    if ! discover_repos "." >"$TMP_ROOT/repos"; then
      return 1
    fi
    if [ -s "$TMP_ROOT/repos" ]; then
      while IFS= read -r line; do
        if [ -n "$line" ]; then
          repos[${#repos[@]}]=$line
        fi
      done <"$TMP_ROOT/repos"
    fi
  fi

  if [ "${#repos[@]}" -eq 0 ]; then
    printf 'Error: No git repository found\n' >&2
    return 1
  fi

  local pushed=0 skipped=0 errors=0 rc
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

usage() {
  printf 'Usage:\n  git-fast.sh inspect [start_dir] [--jobs N]\n  git-fast.sh push [--force] [repo...]\n' >&2
}

main() {
  local command=""
  if [ "$#" -gt 0 ]; then
    command=$1
    shift
  fi
  local rc=0
  case "$command" in
    inspect)
      inspect_command "$@" || rc=$?
      return "$rc"
      ;;
    push)
      push_command "$@" || rc=$?
      return "$rc"
      ;;
    -h | --help)
      usage
      return 0
      ;;
  esac
  usage
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
