#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"

# Structural contract checks. Bare greps run under `set -e`, so a missing
# section fails the script — unlike the prior prose-word greps, which passed
# even after the load-bearing sections were deleted.
[[ -s "$SKILL" ]]
head -1 "$SKILL" | grep -q '^---$'
grep -q '^name: test$' "$SKILL"

# Load-bearing doctrine sections. Deleting any one must turn this validator red.
grep -q '^## Critical Constraints$' "$SKILL"
grep -q '^## Oracle-strength hierarchy$' "$SKILL"
grep -q '^## Mutation-kill proof$' "$SKILL"
grep -q '^## Harness health floors$' "$SKILL"
grep -q '^## Workflow$' "$SKILL"
grep -q '^## Output Specification$' "$SKILL"

# The mode table must enumerate the four real modes.
for mode in generate coverage tdd strategy; do
  grep -Eq "^\| \`${mode}\`" "$SKILL"
done

# Every referenced local doc must resolve on disk.
while IFS= read -r ref; do
  [[ -f "$SKILL_DIR/$ref" ]] || { echo "test contract: dangling reference $ref" >&2; exit 1; }
done < <(grep -oE 'references/[A-Za-z0-9._-]+' "$SKILL" | sort -u)

echo "test contract: PASS"
