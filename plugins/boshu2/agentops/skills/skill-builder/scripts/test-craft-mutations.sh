#!/usr/bin/env bash
# test-craft-mutations.sh — proves the advisory craft scorer detects degradation.
#
# Baseline: a craft-rich fixture scores N/12. Mutations that strip a stop
# condition or an anti-pattern corrective MUST drop the score and name the
# lost element as a gap. Runs independently of test-mutation-boundaries.sh
# (which has a known pre-existing failure at its first assertion, tracked
# separately; do not conflate the two).
#
# Single documented command:
#   bash skills/skill-builder/scripts/test-craft-mutations.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CRAFT_PY="$SCRIPT_DIR/craft_score.py"
FIX="$(cd "$(mktemp -d)" && pwd -P)"
trap 'rm -rf "$FIX"' EXIT

fail() { echo "test-craft-mutations: FAIL — $1" >&2; exit 1; }

score_of() {
  python3 "$CRAFT_PY" "$1" --repo-root "$REPO_ROOT" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["score"])'
}

missing_of() {
  python3 "$CRAFT_PY" "$1" --repo-root "$REPO_ROOT" \
    | python3 -c 'import json,sys; print(",".join(json.load(sys.stdin)["missing"]))'
}

# --- Baseline fixture: rich in the two elements under mutation -------------
BASE="$FIX/base"
mkdir -p "$BASE"
cat >"$BASE/SKILL.md" <<'EOF'
---
name: base
description: 'Refine a draft. Triggers: "refine draft", "polish draft".'
---
# base

Insight: drafts converge because each pass removes one named defect.

## Refinement loop

Repeat the review pass. Stop after at most 3 passes or when the checker
exits 0, whichever comes first.

Avoid rewriting the whole draft in one pass; instead change one section
per pass.

## Failure behavior

Fails when the checker never reaches exit 0 within the pass budget.
EOF

baseline="$(score_of "$BASE")"
baseline_missing="$(missing_of "$BASE")"
[[ "$baseline_missing" != *"named-loop-stop-condition"* ]] \
  || fail "baseline unexpectedly missing named-loop-stop-condition"
[[ "$baseline_missing" != *"anti-pattern-with-corrective"* ]] \
  || fail "baseline unexpectedly missing anti-pattern-with-corrective"

# --- Mutation 1: strip the stop condition ----------------------------------
MUT1="$FIX/mut1"
mkdir -p "$MUT1"
sed -e 's/Stop after at most 3 passes or when the checker/Keep going until it feels done./' \
    -e '/^exits 0, whichever comes first\.$/d' \
    "$BASE/SKILL.md" >"$MUT1/SKILL.md"
mut1="$(score_of "$MUT1")"
(( mut1 < baseline )) \
  || fail "stripping the stop condition did not drop the score (baseline=$baseline mutated=$mut1)"
[[ "$(missing_of "$MUT1")" == *"named-loop-stop-condition"* ]] \
  || fail "stop-condition mutation not named as a gap"

# --- Mutation 2: strip the anti-pattern corrective --------------------------
MUT2="$FIX/mut2"
mkdir -p "$MUT2"
sed -e '/^Avoid rewriting the whole draft in one pass; instead change one section$/d' \
    -e '/^per pass\.$/d' \
    "$BASE/SKILL.md" >"$MUT2/SKILL.md"
mut2="$(score_of "$MUT2")"
(( mut2 < baseline )) \
  || fail "stripping the anti-pattern corrective did not drop the score (baseline=$baseline mutated=$mut2)"
[[ "$(missing_of "$MUT2")" == *"anti-pattern-with-corrective"* ]] \
  || fail "anti-pattern mutation not named as a gap"

echo "craft mutation detection: PASS (baseline $baseline/12; stop-condition strip -> $mut1/12; anti-pattern strip -> $mut2/12)"
