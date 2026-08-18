#!/usr/bin/env bash
# test-authoring-mutations.sh — proves the advisory authoring scanner detects
# prose degradation (references/authoring-doctrine.md failure modes).
#
# Baseline: a doctrine-clean fixture yields zero authoring findings. Each
# mutation introduces exactly one failure mode and MUST surface the
# corresponding named finding.
#
# Single documented command:
#   bash skills/skill-builder/scripts/test-authoring-mutations.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTHORING_PY="$SCRIPT_DIR/authoring_scan.py"
FIX="$(cd "$(mktemp -d)" && pwd -P)"
trap 'rm -rf "$FIX"' EXIT

fail() { echo "test-authoring-mutations: FAIL — $1" >&2; exit 1; }

count_of() { # count_of <dir> <finding-id>
  python3 "$AUTHORING_PY" "$1" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['counts']['$2'])"
}

total_of() {
  python3 "$AUTHORING_PY" "$1" \
    | python3 -c "import json,sys; print(len(json.load(sys.stdin)['findings']))"
}

# --- Baseline fixture: doctrine-clean ---------------------------------------
BASE="$FIX/base"
mkdir -p "$BASE"
cat >"$BASE/SKILL.md" <<'EOF'
---
name: base
description: 'Refine a draft. Triggers: "refine draft".'
---
# base

Read every reference file before editing. Edit the source and regenerate;
never edit generated files directly.

## Workflow

### Gather

Collect the inputs. Done when every input path resolves.

### Apply

Make the edits. Done when the checker exits 0.
EOF

(( $(total_of "$BASE") == 0 )) \
  || fail "baseline fixture unexpectedly has authoring findings"

# --- Mutation 1: introduce a no-op phrase -----------------------------------
MUT1="$FIX/mut1"
mkdir -p "$MUT1"
sed 's/Read every reference file before editing\./Be thorough when editing./' \
  "$BASE/SKILL.md" >"$MUT1/SKILL.md"
(( $(count_of "$MUT1" noop-phrase) >= 1 )) \
  || fail "no-op phrase mutation not surfaced as noop-phrase"

# --- Mutation 2: strip the positive counterpart from a prohibition ----------
MUT2="$FIX/mut2"
mkdir -p "$MUT2"
python3 - "$BASE/SKILL.md" "$MUT2/SKILL.md" <<'PY'
import sys
text = open(sys.argv[1]).read()
text = text.replace(
    "Read every reference file before editing. Edit the source and regenerate;\nnever edit generated files directly.",
    "Never edit generated files.",
)
open(sys.argv[2], "w").write(text)
PY
(( $(count_of "$MUT2" negation-without-positive) >= 1 )) \
  || fail "bare prohibition mutation not surfaced as negation-without-positive"

# --- Mutation 3: strip a done condition from a workflow subphase ------------
MUT3="$FIX/mut3"
mkdir -p "$MUT3"
sed 's/Collect the inputs\. Done when every input path resolves\./Collect the inputs./' \
  "$BASE/SKILL.md" >"$MUT3/SKILL.md"
(( $(count_of "$MUT3" step-missing-done-condition) == 1 )) \
  || fail "stripped done condition not surfaced as step-missing-done-condition"

# --- Clearing direction: adding the done condition back clears the finding --
MUT4="$FIX/mut4"
mkdir -p "$MUT4"
sed 's/Collect the inputs\./Collect the inputs. Done when every input path resolves./' \
  "$MUT3/SKILL.md" >"$MUT4/SKILL.md"
(( $(count_of "$MUT4" step-missing-done-condition) == 0 )) \
  || fail "restored done condition did not clear the finding"

echo "authoring mutation detection: PASS (baseline 0 findings; noop, negation, done-condition mutations each surfaced; restore clears)"
