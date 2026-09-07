#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"

[[ -s "$SKILL" ]]
grep -q '^name: scaffold$' "$SKILL"
grep -q '^## Contract$' "$SKILL"
grep -q '^## Evidence$' "$SKILL"
grep -Fq 'The caller owns version control, revision, and delivery.' "$SKILL"
if grep -Eiq 'AUTO-REDO|ONE-HELPER|HELPER-ESCALATE|ao land|next_action' "$SKILL"; then
  echo 'scaffold contract contains retired lifecycle vocabulary' >&2
  exit 1
fi

# References must not re-grant the Git-mutation or continuation authority the
# contract denies ("does not schedule RPI, create work ownership, mutate Git,
# or decide what happens next"). This sweep covers references/** because a grant
# hidden in a template file passes unseen when only SKILL.md is scanned.
#
# The pattern covers the deleted grants (Step 5 "Initial Commit", the summary
# "Commit:" line, the "Git init fails" row) and equivalent forms. Bare `push` is
# matched only when it is a verb (followed by space, period, or end-of-line), so
# the legitimate CI-trigger key `push:` and the word `pushd` do NOT false-fire.
FORBIDDEN='initial commit|create a commit|git commit|git add|git init|git push|commit:|next step|\bpush([[:space:]]|[.]|$)'
if [[ -d "$SKILL_DIR/references" ]] \
  && grep -rEiq "$FORBIDDEN" "$SKILL_DIR/references"; then
  echo 'scaffold references confer Git-commit or continuation authority the contract denies' >&2
  exit 1
fi

echo "scaffold contract: PASS"
