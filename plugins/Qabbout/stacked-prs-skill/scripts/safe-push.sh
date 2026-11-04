#!/usr/bin/env bash
# Push the current branch to its remote branch: only as a fast-forward, and
# only after the user has approved that exact push.
#
# Usage:
#   safe-push.sh [-r remote] [-P glob]... <branch>
#       Dry run (the default). Checks everything, prints what would be pushed
#       and the exact command to push it, then exits 3. Nothing is pushed.
#   safe-push.sh [-r remote] [-P glob]... -A <head-sha> -T <remote-tip-sha|none> -K <key> <branch>
#       Pushes, but only if HEAD is still <head-sha>, the remote branch is
#       still <remote-tip-sha> (or still doesn't exist, for "none"), and <key>
#       matches this exact push URL, remote, branch, head and tip. Copy the command the
#       dry run printed; run it only after the user approved that plan in chat.
#
#   -r remote  remote to push to (default: origin)
#   -P glob    another protected branch pattern; repeatable. Patterns are also
#              read from `git config --get-all stacked-prs.protect` (set the
#              reference branch there once). origin/ or refs/heads/ is ignored.
#
# Refuses: main, master, develop, release/* and every protected pattern (any
# letter case); a name starting with refs/ or <remote>/; a detached HEAD; a
# current branch that is not <branch> itself, or a work/* branch tracking
# <remote>/<branch>; a dirty working tree; commits whose subject starts with
# WIP, fixup! or squash!; a remote branch with commits HEAD doesn't contain;
# approval values that aren't full commit IDs; mirror or multiple push URLs.
# Disables automatic tag and submodule pushes. Never force-pushes. The final
# preflight is not an atomic lock: a concurrent fast-forward may still land.
#
# Exit codes: 0 pushed (or nothing to push), 1 refused or failed, 2 usage,
# 3 dry run finished: approval needed.
set -euo pipefail

usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; exit 2; }
refuse() { echo "refusing: $*" >&2; exit 1; }
lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

remote=origin
approved_head=""
approved_tip=""
approved_key=""
protected=("main" "master" "develop" "release/*")
extra_p=()
while getopts "r:P:A:T:K:h" opt; do
  case "$opt" in
    r) remote=$OPTARG ;;
    P) extra_p+=("$OPTARG") ;;
    A) approved_head=$OPTARG ;;
    T) approved_tip=$OPTARG ;;
    K) approved_key=$OPTARG ;;
    *) usage ;;
  esac
done
shift $((OPTIND - 1))
[ $# -eq 1 ] || usage
branch=$1
if [ -n "$approved_head$approved_tip$approved_key" ] && { [ -z "$approved_head" ] || [ -z "$approved_tip" ] || [ -z "$approved_key" ]; }; then
  echo "error: -A, -T and -K go together; copy the command the dry run printed" >&2
  exit 2
fi
if [ -n "$approved_head" ]; then
  [[ "$approved_head" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || refuse "-A must be the full commit ID the dry run printed"
  [ "$approved_tip" = "none" ] || [[ "$approved_tip" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || refuse "-T must be the full commit ID (or none) the dry run printed"
fi

git rev-parse --git-dir >/dev/null 2>&1 || refuse "not inside a git repository"
git check-ref-format "refs/heads/$branch" >/dev/null || refuse "invalid branch name"
case "$remote" in -*) refuse "invalid remote name" ;; esac
[ "$(git config --bool --get "remote.$remote.mirror" || true)" != true ] || refuse "mirror remotes are not supported"
push_urls=$(git remote get-url --push --all "$remote") || refuse "no push URL for $remote"
[ "$(printf '%s\n' "$push_urls" | wc -l | tr -d ' ')" -eq 1 ] || refuse "multiple push URLs are not supported"
push_url=$push_urls
[ -n "$push_url" ] || refuse "empty push URL"

# protected patterns: built-in, -P, and git config stacked-prs.protect
config_p=$(git config --get-all stacked-prs.protect 2>/dev/null || true)
while IFS= read -r p; do [ -n "$p" ] && extra_p+=("$p"); done <<< "$config_p"
for p in ${extra_p[@]+"${extra_p[@]}"}; do
  p=${p#refs/heads/}; p=${p#refs/remotes/$remote/}; p=${p#$remote/}
  protected+=("$p")
done

case "$branch" in
  refs/* | "$remote"/*) refuse "give the plain branch name, without refs/ or $remote/" ;;
esac
for p in "${protected[@]}"; do
  # shellcheck disable=SC2254
  case "$(lower "$branch")" in
    $(lower "$p")) refuse "$branch is protected ($p); it only changes through a reviewed PR" ;;
  esac
done

current=$(git symbolic-ref -q --short HEAD) || refuse "HEAD is detached; check out the branch first"
if [ "$current" != "$branch" ]; then
  upstream=$(git rev-parse -q --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
  case "$current" in
    work/*) [ "$upstream" = "$remote/$branch" ] || refuse "HEAD is on '$current', which tracks '${upstream:-nothing}', not '$remote/$branch'" ;;
    *) refuse "HEAD is on '$current', not '$branch' (only a work/* branch tracking $remote/$branch may push to it)" ;;
  esac
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "refusing: the working tree has uncommitted changes:" >&2
  git status --short >&2
  exit 1
fi

if ! listing=$(git ls-remote --heads -- "$push_url" "refs/heads/$branch" 2>&1); then
  echo "error: can't read push destination for $remote: $listing" >&2
  exit 1
fi
listing=$(printf '%s\n' "$listing" | awk -v r="refs/heads/$branch" '$2 == r { print; exit }')

head=$(git rev-parse HEAD)
if [ -n "$listing" ]; then
  remote_tip=${listing%%[[:space:]]*}
  git fetch -q --no-tags -- "$push_url" "refs/heads/$branch" || { echo "error: can't fetch push destination for $remote/$branch" >&2; exit 1; }
  if ! git merge-base --is-ancestor "$remote_tip" HEAD; then
    echo "refusing: $remote/$branch has commits HEAD doesn't contain:" >&2
    git log --oneline "HEAD..$remote_tip" >&2
    echo "merge or cherry-pick onto $remote/$branch, check again, then retry" >&2
    exit 1
  fi
  if [ "$remote_tip" = "$head" ]; then
    echo "$remote/$branch is already at HEAD ($(git rev-parse --short HEAD)); nothing to push"
    exit 0
  fi
  range=("$remote_tip..HEAD")
  action="fast-forward $remote/$branch $(git rev-parse --short "$remote_tip")..$(git rev-parse --short HEAD)"
else
  remote_tip=none
  range=(HEAD --not "--remotes=$remote")
  action="create $remote/$branch at $(git rev-parse --short HEAD)"
fi

unfinished='^([Ww][Ii][Pp]([: ]|$)|fixup! |squash! )'
subjects=$(git log --format='%s' "${range[@]}")
if grep -qE "$unfinished" <<< "$subjects"; then
  echo "refusing: these commits look unfinished:" >&2
  git log --format='%h%x09%s' "${range[@]}" | awk -F'\t' -v re="$unfinished" '$2 ~ re { print $1 " " $2 }' >&2
  exit 1
fi

count=$(git log --oneline "${range[@]}" | wc -l | tr -d ' ')
echo "push plan: $action ($count commit(s))"
display_url=$push_url
if [[ "$display_url" == *://*@* ]]; then
  display_url="${display_url%%://*}://<redacted>@${display_url#*@}"
fi
display_url=${display_url%%\?*}
echo "destination: $display_url"
git log -30 --oneline "${range[@]}"
[ "$count" -gt 30 ] && echo "… and $((count - 30)) more"

key=$(printf '%s\0' "$remote" "$push_url" "$branch" "$head" "$remote_tip" | git hash-object --stdin | cut -c1-16)

if [ -z "$approved_head" ]; then
  command=("$0" -r "$remote")
  for p in ${extra_p[@]+"${extra_p[@]}"}; do command+=(-P "$p"); done
  command+=(-A "$head" -T "$remote_tip" -K "$key" "$branch")
  echo
  echo "APPROVAL NEEDED: nothing was pushed. Show this plan to the user. Only after"
  echo "they approve this exact push in the chat, run:"
  printf '  '; printf '%q ' "${command[@]}"; printf '\n'
  exit 3
fi

if [ "$(git rev-parse -q --verify "$approved_head^{commit}" || true)" != "$head" ]; then
  refuse "HEAD changed since the approved plan (approved $approved_head); run the dry run again and get a new approval"
fi
if [ "$approved_tip" = "none" ]; then
  [ "$remote_tip" = "none" ] || refuse "$remote/$branch now exists ($remote_tip); run the dry run again and get a new approval"
elif [ "$remote_tip" = "none" ] || [ "$(git rev-parse -q --verify "$approved_tip^{commit}" || true)" != "$remote_tip" ]; then
  refuse "$remote/$branch moved since the approved plan; run the dry run again and get a new approval"
fi

[ "$approved_key" = "$key" ] || refuse "this approval was for a different push (remote, branch, head or tip differ); run the dry run again and get a new approval"

git -c push.followTags=false -c push.recurseSubmodules=no push --no-follow-tags --recurse-submodules=no -- "$push_url" "$approved_head:refs/heads/$branch"
