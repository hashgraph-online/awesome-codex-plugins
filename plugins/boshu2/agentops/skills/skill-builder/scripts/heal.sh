#!/usr/bin/env bash
# One-pass structural audit for source skill packages.
set -euo pipefail

MODE=check
STRICT=0
TARGETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE=check ;;
    --fix) MODE=fix ;;
    --strict) STRICT=1 ;;
    -h|--help)
      echo "usage: heal.sh [--check|--fix] [--strict] [skills/<slug> ...]"
      exit 0
      ;;
    *) TARGETS+=("$1") ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${HEAL_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

if [[ "$MODE" == fix && ${#TARGETS[@]} -eq 0 ]]; then
  echo "heal.sh: --fix requires explicit source targets" >&2
  exit 2
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  for path in "$REPO_ROOT/skills"/*; do
    [[ -d "$path" && -f "$path/SKILL.md" ]] && TARGETS+=("$path")
  done
fi

# Go validates raw target spellings before normalization and reads source only.
set +e
bash "$SCRIPT_DIR/run-ao.sh" skills check-source --repo "$REPO_ROOT" --strict "${TARGETS[@]}"
rc=$?
set -e
[[ $rc -ne 2 ]] || exit 2
# 126/127 mean ao could not run at all; that is not an advisory finding.
if [[ $rc -eq 126 || $rc -eq 127 ]]; then
  echo "heal.sh: could not run 'ao skills check-source'; install ao 3.9 or later, or run from a source checkout with Go" >&2
  exit 2
fi

if [[ "$MODE" == fix && $rc -eq 0 ]]; then
  # Source behavior remains human-authored. Repair only owned projections.
  # A plugin install has skills/ but no scripts/; refuse instead of writing there.
  if [[ ! -f "$REPO_ROOT/scripts/generate-skill-mesh.py" ]]; then
    echo "heal.sh: --fix needs an AgentOps source checkout; $REPO_ROOT has no scripts/generate-skill-mesh.py (set HEAL_REPO_ROOT)" >&2
    exit 2
  fi
  # Exit 3, not the generator's own status, so a failed projection never reads
  # as a finding (1) or an invalid target (2).
  if ! python3 "$REPO_ROOT/scripts/generate-skill-mesh.py"; then
    echo "heal.sh: projection failed after a clean source check; source unchanged, projections may be partial" >&2
    exit 3
  fi
fi

if [[ $rc -ne 0 && ( $STRICT -eq 1 || "$MODE" == fix ) ]]; then
  exit 1
fi
exit 0
