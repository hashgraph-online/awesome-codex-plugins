#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

for path in \
  SKILL.md \
  scripts/build.sh \
  scripts/init.sh \
  scripts/heal.sh \
  scripts/audit.sh \
  scripts/score_agentops_skill.py \
  schemas/build-report.json \
  schemas/audit-report.json \
  references/audit-checks.md \
  references/codex-parity.md; do
  [[ -f "$SKILL_DIR/$path" ]] || {
    echo "skill-builder validate: missing $path" >&2
    exit 1
  }
done

for script in scripts/build.sh scripts/init.sh; do
  [[ -x "$SKILL_DIR/$script" ]] || {
    echo "skill-builder validate: not executable: $script" >&2
    exit 1
  }
done

bash -n "$SKILL_DIR/scripts/heal.sh" "$SKILL_DIR/scripts/audit.sh"
bash "$SKILL_DIR/scripts/heal.sh" --check --strict "$SKILL_DIR"

before="$(find "$SKILL_DIR" -type f -exec shasum -a 256 {} + | sort | shasum -a 256 | awk '{print $1}')"
bash "$SKILL_DIR/scripts/heal.sh" --check "$SKILL_DIR" >/dev/null
after="$(find "$SKILL_DIR" -type f -exec shasum -a 256 {} + | sort | shasum -a 256 | awk '{print $1}')"
[[ "$before" == "$after" ]] || {
  echo "skill-builder validate: check mode mutated its target" >&2
  exit 1
}

if rg -n 'from-pattern|flywheel close-loop|append-skill-disposition' "$SKILL_DIR/SKILL.md" \
  || rg -n 'git (status|commit|push)|ao land|retry|queue|lease' \
    "$SKILL_DIR/scripts/build.sh" "$SKILL_DIR/scripts/init.sh"; then
  echo "skill-builder validate: obsolete lifecycle behavior remains" >&2
  exit 1
fi

if rg -n 'ao land|git (commit|push)|append-skill-disposition|flywheel close-loop' \
  "$SKILL_DIR/scripts/heal.sh" "$SKILL_DIR/scripts/audit.sh" \
  "$SKILL_DIR/scripts/score_agentops_skill.py"; then
  echo "skill-builder validate: lifecycle authority remains" >&2
  exit 1
fi

echo "skill-builder validate: PASS"
