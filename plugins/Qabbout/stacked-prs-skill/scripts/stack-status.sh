#!/usr/bin/env bash
# Show how each stack branch stands against the branch its PR targets.
#
# Usage: stack-status.sh [-r remote] [-b base] [-n] [-c commit]... <branch>:<target> [<branch>:<target> ...]
#   -r remote  remote to compare against (default: origin)
#   -b base    the stack's base (default: develop). Being behind the base is
#              normal: merge it in only for conflicts or CI. Pass -b main
#              for main-based repos.
#   -n         skip `git fetch`
#   -c commit  also report whether this commit (or a cherry-pick of it) is in
#              each branch; repeatable
# Options may come before or after the pairs.
#
# Give every branch with its PR's real target, e.g.
#   feature/X-02-api:develop feature/X-04-layer:feature/X-stack-base
# Remote refs are compared; when a local branch differs from its remote,
# that's reported too, and -c is answered for both. Read-only.
set -euo pipefail

usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; exit 2; }

remote=origin
base=develop
fetch=1
commits=()
pairs=()
while [ $# -gt 0 ]; do
  case "$1" in
    -r) [ $# -ge 2 ] || usage; remote=$2; shift 2 ;;
    -b) [ $# -ge 2 ] || usage; base=$2; shift 2 ;;
    -c) [ $# -ge 2 ] || usage; commits+=("$2"); shift 2 ;;
    -n) fetch=0; shift ;;
    -h | --help) usage ;;
    -*) echo "error: unknown option $1" >&2; usage ;;
    ?*:?*) pairs+=("$1"); shift ;;
    *) echo "error: '$1' isn't <branch>:<target>" >&2; usage ;;
  esac
done
[ ${#pairs[@]} -ge 1 ] || usage

git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not inside a git repository" >&2; exit 1; }
[ "$fetch" -eq 1 ] && git fetch -q "$remote"

for c in ${commits[@]+"${commits[@]}"}; do
  git rev-parse -q --verify "$c^{commit}" >/dev/null || { echo "error: -c $c isn't a commit here" >&2; exit 1; }
done

resolve() {
  if git rev-parse -q --verify "refs/remotes/$remote/$1" >/dev/null; then
    echo "$remote/$1"
  elif git rev-parse -q --verify "refs/heads/$1" >/dev/null; then
    echo "$1"
  else
    echo "error: no branch '$1' locally or on $remote" >&2
    exit 1
  fi
}

# yes / yes (cherry-picked) / probably (same subject) / no
contains() {
  local commit=$1 ref=$2 target=$3 subject
  if git merge-base --is-ancestor "$commit" "$ref" 2>/dev/null; then
    echo "yes"
  elif git cherry "$ref" "$commit" "$commit^" 2>/dev/null | grep -q '^-'; then
    echo "yes (cherry-picked)"
  else
    subject=$(git log -1 --format=%s "$commit")
    if git log --format=%s "$target..$ref" 2>/dev/null | grep -qxF -- "$subject"; then
      echo "probably: a commit with the same subject is there (cherry-picked with changes?); check it"
    else
      echo "no"
    fi
  fi
}

local_state() {
  local b=$1 l r
  l=$(git rev-parse -q --verify "refs/heads/$b" || true)
  r=$(git rev-parse -q --verify "refs/remotes/$remote/$b" || true)
  [ -n "$l" ] && [ -n "$r" ] && [ "$l" != "$r" ] || return 0
  if git merge-base --is-ancestor "$l" "$r"; then echo "local copy is $(git rev-list --count "$l..$r") behind $remote"
  elif git merge-base --is-ancestor "$r" "$l"; then echo "local copy is $(git rev-list --count "$r..$l") ahead of $remote (unpushed)"
  else echo "local copy DIVERGED from $remote"; fi
}

printf '%-55s %-10s %s\n' "branch -> target" "tip" "state"
for pair in "${pairs[@]}"; do
  b=${pair%%:*}
  t=${pair#*:}
  ref=$(resolve "$b")
  tref=$(resolve "$t")
  behind=$(git rev-list --count "$ref..$tref")
  ahead=$(git rev-list --count "$tref..$ref")
  if [ "$behind" -eq 0 ]; then
    state="up to date with its target, $ahead own commit(s)"
  elif [ "$t" = "$base" ]; then
    state="$behind behind $base, $ahead own commit(s): normal; merge $base in only for conflicts or CI"
  else
    state="NEEDS UPDATE: $behind commit(s) behind its target, $ahead ahead"
  fi
  printf '%-55s %-10s %s\n' "$b -> $t" "$(git rev-parse --short "$ref")" "$state"
  ls=$(local_state "$b")
  [ -n "$ls" ] && printf '%-55s %-10s %s\n' "" "" "$ls"
  for c in ${commits[@]+"${commits[@]}"}; do
    printf '%-55s %-10s contains %s: %s\n' "" "" "$(git rev-parse --short "$c")" "$(contains "$c" "$ref" "$tref")"
    if [ -n "$ls" ] && [ "$ref" != "$b" ]; then
      printf '%-55s %-10s   local copy: %s\n' "" "" "$(contains "$c" "refs/heads/$b" "$tref")"
    fi
  done
done
