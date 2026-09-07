#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HEAL="$SCRIPT_DIR/heal.sh"
AUDIT="$SCRIPT_DIR/audit.sh"
FIX="$(cd "$(mktemp -d)" && pwd -P)"
trap 'rm -rf "$FIX"' EXIT

digest_tree() {
  find "$1" -type f -exec shasum -a 256 {} + | LC_ALL=C sort | shasum -a 256 | awk '{print $1}'
}

write_fixture_skill() {
  local path="$1" name="$2"
  mkdir -p "$path"
  printf '%s\n' '---' "name: $name" "description: Fixture $name." '---' "# $name" >"$path/SKILL.md"
}

expect_check_accepts() {
  local spelling="$1" rc
  set +e
  HEAL_REPO_ROOT="$FIX" bash "$HEAL" --check "$spelling" >/dev/null 2>&1
  rc=$?
  set -e
  [[ "$rc" -eq 0 ]]
}

expect_rejected_unchanged() {
  local spelling="$1" before after rc
  before="$(digest_tree "$FIX")"
  set +e
  HEAL_REPO_ROOT="$FIX" bash "$HEAL" --fix "$spelling" >/dev/null 2>&1
  rc=$?
  set -e
  after="$(digest_tree "$FIX")"
  [[ "$rc" -eq 2 && "$before" == "$after" ]]
}

mkdir -p "$FIX/skills"
write_fixture_skill "$FIX/skills/target" target
write_fixture_skill "$FIX/skills/sibling" sibling

sibling_before="$(shasum -a 256 "$FIX/skills/sibling/SKILL.md" | awk '{print $1}')"
set +e
HEAL_REPO_ROOT="$FIX" bash "$HEAL" --fix skills/target >/dev/null 2>&1
fix_rc=$?
set -e
[[ "$fix_rc" -eq 1 ]]
grep -q '^skill_api_version: 1$' "$FIX/skills/target/SKILL.md"
if grep -q '^skill_api_version:' "$FIX/skills/sibling/SKILL.md"; then exit 1; fi
[[ "$(shasum -a 256 "$FIX/skills/sibling/SKILL.md" | awk '{print $1}')" == "$sibling_before" ]]

expect_check_accepts skills/target
expect_check_accepts ./skills/target
expect_check_accepts "$FIX/skills/target"

write_fixture_skill "$FIX/outside" outside
ln -s "$FIX/skills/target" "$FIX/skills/target-alias"
ln -s "$FIX/outside" "$FIX/skills/outside-alias"
ln -s "$FIX" "$FIX/repo-alias"
expect_rejected_unchanged skills/target/../../outside
expect_rejected_unchanged "$FIX/outside"
expect_rejected_unchanged skills/target-alias
expect_rejected_unchanged skills/outside-alias
expect_rejected_unchanged "$FIX/repo-alias/skills/target"
expect_rejected_unchanged skills/missing

check_before="$(digest_tree "$FIX")"
HEAL_REPO_ROOT="$FIX" bash "$HEAL" --check skills/sibling >/dev/null
[[ "$(digest_tree "$FIX")" == "$check_before" ]]

audit_before="$(digest_tree "$REPO_ROOT/skills")"
bash "$AUDIT" "$REPO_ROOT/skills/skill-builder" >/dev/null 2>&1
[[ "$(digest_tree "$REPO_ROOT/skills")" == "$audit_before" ]]

echo "heal mutation boundaries: PASS"
