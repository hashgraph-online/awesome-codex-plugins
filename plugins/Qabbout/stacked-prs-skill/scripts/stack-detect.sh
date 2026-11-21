#!/usr/bin/env bash
# Find what already exists for a ticket's stack before splitting or resuming.
#
# Usage: stack-detect.sh [-r remote] [-b base] [-n] <TICKET>
#   -r remote  remote to look at (default: origin)
#   -b base    base branch (default: develop; pass -b main for main-based repos)
#   -n         skip `git fetch`
#
# Matches branch names that contain the exact ticket, in any letter case
# (ABC-12 does not match ABC-123) and lists: slice branches (<TICKET>-NN-), the stack-base, other
# branches (reference candidates), where each one exists (local, remote, or
# both, and whether they differ; a local branch whose remote copy is gone is
# reported as pushed before), whether it's already merged into <base>,
# and worktrees for the ticket (detached ones too). Read-only. It can't see
# PRs: check those on the host before creating any.
set -euo pipefail

usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; exit 2; }

remote=origin
base=develop
fetch=1
while getopts "r:b:nh" opt; do
  case "$opt" in
    r) remote=$OPTARG ;;
    b) base=$OPTARG ;;
    n) fetch=0 ;;
    *) usage ;;
  esac
done
shift $((OPTIND - 1))
[ $# -eq 1 ] || usage
ticket=$1
[ -n "$ticket" ] || { echo "error: the ticket is empty" >&2; exit 2; }

git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not inside a git repository" >&2; exit 1; }
[ "$fetch" -eq 1 ] && git fetch -q --prune "$remote"
base_ref=$(git rev-parse -q --verify "refs/remotes/$remote/$base" || git rev-parse -q --verify "refs/heads/$base" || true)
[ -n "$base_ref" ] || { echo "error: no base branch '$base' (pass -b)" >&2; exit 1; }

esc=$(printf '%s' "$ticket" | sed 's/[][\.*^$+?(){}|/]/\\&/g')
match="(^|[^A-Za-z0-9])${esc}([^A-Za-z0-9]|$)"

names=$({
  git for-each-ref --format='%(refname:lstrip=2)' refs/heads
  git for-each-ref --format='%(refname:lstrip=3)' "refs/remotes/$remote"
} | grep -iE -- "$match" | grep -v '^HEAD$' | sort -u || true)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

where() {
  local b=$1 l r
  l=$(git rev-parse -q --verify "refs/heads/$b" || true)
  r=$(git rev-parse -q --verify "refs/remotes/$remote/$b" || true)
  if [ -n "$l" ] && [ -n "$r" ]; then
    if [ "$l" = "$r" ]; then echo "local+remote, same ($(git rev-parse --short "$r"))"
    elif git merge-base --is-ancestor "$l" "$r"; then echo "local+remote, local behind"
    elif git merge-base --is-ancestor "$r" "$l"; then echo "local+remote, local ahead (unpushed)"
    else echo "local+remote, DIVERGED"; fi
  elif [ -n "$r" ]; then echo "remote only ($(git rev-parse --short "$r"))"
  elif [ "$(git for-each-ref --format='%(upstream:track)' "refs/heads/$b")" = "[gone]" ]; then
    echo "local only: WAS PUSHED, its remote branch is gone (merged and deleted?) ($(git rev-parse --short "$l")); never re-cut it"
  else echo "local only, push history unknown ($(git rev-parse --short "$l")); verify before re-cutting"; fi
}

in_base() {
  local tip
  tip=$(git rev-parse -q --verify "refs/remotes/$remote/$1" || git rev-parse -q --verify "refs/heads/$1")
  git merge-base --is-ancestor "$tip" "$base_ref" || return 0
  [ -s "$tmp/first-parent" ] || git rev-list --first-parent "$base_ref" > "$tmp/first-parent"
  if grep -qx "$tip" "$tmp/first-parent"; then
    echo ", no commits of its own yet (points at a $base commit)"
  else
    echo ", merged into $base"
  fi
}

print_group() {
  local title=$1 list=$2
  [ -n "$list" ] || return 0
  echo "$title"
  while IFS= read -r b; do printf '  %-60s %s%s\n' "$b" "$(where "$b")" "$(in_base "$b")"; done <<< "$list"
}

slices=$(grep -iE -- "(^|/)${esc}-[0-9]{2}-" <<< "$names" || true)
bases=$(grep -iE -- "(^|/)${esc}-stack-base$" <<< "$names" || true)
others=$(grep -viE -- "(^|/)${esc}-[0-9]{2}-" <<< "$names" | grep -viE -- "(^|/)${esc}-stack-base$" || true)

re_lower=$(printf '%s' "$match" | tr '[:upper:]' '[:lower:]')
trees=$(git worktree list --porcelain | awk -v re="$re_lower" '
  function show() { if (path != "" && (tolower(b) ~ re || tolower(path) ~ re)) print "  " path "  [" b "]" }
  /^worktree / { show(); path = substr($0, 10); b = "" }
  /^branch / { b = substr($0, 8); sub("refs/heads/", "", b) }
  /^detached/ { b = "detached" }
  END { show() }')

if [ -z "$names" ] && [ -z "$trees" ]; then
  echo "nothing found for $ticket: no local or $remote branches or worktrees match it"
  echo "-> no stack yet; start with phase A (split)"
  exit 0
fi

print_group "slice branches:" "$slices"
print_group "stack-base:" "$bases"
print_group "other branches (reference candidates):" "$others"
if [ -n "$trees" ]; then echo "worktrees:"; echo "$trees"; fi

echo
if [ -n "$slices" ]; then
  echo "-> a stack already exists: map it (phase B0) and resume; don't re-split"
else
  echo "-> no slice branches yet: phase A, with one of the branches above as the reference"
fi
echo "-> check the host for open, merged and declined PRs from these branches before creating any"
