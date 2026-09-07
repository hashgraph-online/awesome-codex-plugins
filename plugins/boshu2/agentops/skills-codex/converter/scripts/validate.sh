#!/usr/bin/env bash
# Behavioral self-test for the converter. Replaces the prior vacuous check
# ("SKILL.md exists" only, which passed while the pipeline could delete its own
# source) with real proofs (CV-2):
#   1. a happy-path conversion writes the expected target + passthrough files;
#   2. the destructive clean-write path is CLOSED in BOTH directions — an output
#      dir equal to, an ancestor of, a descendant of, or a symlink into the
#      source package is refused; and an output that is or contains the repo
#      root is refused (CV-1). Each refusal is proven to happen BEFORE any
#      deletion: the source content digest is unchanged AND the exit is nonzero.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONVERT="$SKILL_DIR/scripts/convert.sh"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd -P)"
FAIL=0
pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAIL=$((FAIL + 1)); }

# Content + structure digest of a directory tree (path-relative, order-stable).
dir_digest() {
  ( cd "$1" && find . -type f -exec shasum -a 256 {} + | LC_ALL=C sort ) \
    | shasum -a 256 | awk '{print $1}'
}

# assert_refused DESC OUTPUT — the conversion must exit nonzero AND leave the
# source content digest unchanged (refusal before any deletion).
assert_refused() {
  local desc="$1" out="$2"
  if bash "$CONVERT" "$FIX" codex "$out" >/dev/null 2>&1; then
    fail "$desc: expected refusal, got success"
    return
  fi
  if [[ "$(dir_digest "$FIX")" == "$SRC_DIGEST" ]]; then
    pass "$desc: refused before any deletion; source content intact"
  else
    fail "$desc: source content changed — refusal came too late"
  fi
}

if [[ -f "$SKILL_DIR/SKILL.md" ]]; then pass "SKILL.md exists"; else fail "SKILL.md exists"; fi
if [[ -f "$CONVERT" ]]; then pass "convert.sh exists"; else fail "convert.sh exists"; fi

# Disposable fixture, left in place on exit (no rm -rf): the guard under test
# must never be handed a destructive cleanup to imitate.
WORK="$(mktemp -d "${TMPDIR:-/tmp}/converter-selftest.XXXXXX")"
FIX="$WORK/fixture-skill"
mkdir -p "$FIX/references" "$FIX/scripts"
printf -- '---\nname: fixture-skill\ndescription: converter self-test fixture\n---\n# Body\n' > "$FIX/SKILL.md"
printf 'reference payload\n' > "$FIX/references/note.md"
printf 'echo fixture\n' > "$FIX/scripts/tool.sh"
SRC_DIGEST="$(dir_digest "$FIX")"

# 1. Happy path: a distinct output dir converts, writes the target files, and
# does not touch the source.
out="$WORK/out"
if bash "$CONVERT" "$FIX" codex "$out" >/dev/null 2>&1 \
  && [[ -f "$out/SKILL.md" && -f "$out/prompt.md" && -f "$out/references/note.md" && -f "$out/scripts/tool.sh" ]] \
  && [[ "$(dir_digest "$FIX")" == "$SRC_DIGEST" ]]; then
  pass "happy-path conversion writes target + passthrough files; source intact"
else
  fail "happy-path conversion writes target + passthrough files; source intact"
fi

# 2. Bidirectional + repo containment refusals.
assert_refused "output == source"                 "$FIX"
assert_refused "output is an ancestor of source"  "$WORK"
assert_refused "output is a descendant of source" "$FIX/references"
assert_refused "output is an ancestor of the repo root" "$(dirname "$REPO_ROOT")"

# Symlink resolving into the source must be canonicalized and refused.
ln -s "$FIX/references" "$WORK/link-into-src"
assert_refused "output is a symlink into the source" "$WORK/link-into-src"

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "converter self-test: PASS"
  exit 0
fi
echo "converter self-test: FAIL ($FAIL failed)" >&2
exit 1
