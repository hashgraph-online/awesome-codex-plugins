#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

for path in \
  SKILL.md \
  scripts/build.sh \
  scripts/init.sh \
  scripts/heal.sh \
  scripts/audit.sh \
  scripts/audit-legacy.sh \
  scripts/score_agentops_skill.py \
  schemas/build-report.json \
  schemas/audit-report.json \
  schemas/audit-report-legacy.json \
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

# A root without scripts/generate-skill-mesh.py, like a plugin install, must be
# refused with exit 2 before anything is written; the target itself is valid.
probe_root="$(cd "$(mktemp -d)" && pwd -P)"
trap 'rm -rf "$probe_root"' EXIT
mkdir -p "$probe_root/skills/heal-probe"
printf -- "---\nname: heal-probe\ndescription: 'Inspect Git changes in a selected repository.'\npractices: []\nskill_api_version: 1\nhexagonal_role: supporting\nconsumes: []\nproduces: []\ncontext_rel: []\nuser-invocable: true\nmetadata:\n  tier: execution\n  dependencies: []\n  capabilities: [heal_probe]\n  effects: []\n  canonical_status: canonical\n  disposition: keep_specialist\n  stability: experimental\n---\nRun git status --short in the selected repository, report paths inline and stop on error.\n" \
  > "$probe_root/skills/heal-probe/SKILL.md"
set +e
SKILL_BUILDER_REPO_ROOT="$probe_root" bash "$SKILL_DIR/scripts/build.sh" from-scratch build-probe >/dev/null 2>"$probe_root/build.err"
build_rc=$?
HEAL_REPO_ROOT="$probe_root" bash "$SKILL_DIR/scripts/heal.sh" --fix "$probe_root/skills/heal-probe" >/dev/null 2>"$probe_root/heal.err"
heal_rc=$?
set -e
if [[ $build_rc -ne 2 || $heal_rc -ne 2 || -e "$probe_root/skills/build-probe" ]] \
  || ! grep -q 'not an AgentOps source checkout' "$probe_root/build.err" \
  || ! grep -q 'needs an AgentOps source checkout' "$probe_root/heal.err"; then
  echo "skill-builder validate: non-checkout root not refused (build=$build_rc heal=$heal_rc)" >&2
  exit 1
fi

# A projection failure after a clean source check exits 3, not the generator's code.
mkdir -p "$probe_root/scripts"
printf 'import sys\nsys.exit(1)\n' > "$probe_root/scripts/generate-skill-mesh.py"
set +e
HEAL_REPO_ROOT="$probe_root" bash "$SKILL_DIR/scripts/heal.sh" --fix "$probe_root/skills/heal-probe" >/dev/null 2>&1
heal_rc=$?
set -e
[[ $heal_rc -eq 3 ]] || {
  echo "skill-builder validate: failed projection exited $heal_rc, want 3" >&2
  exit 1
}

echo "skill-builder validate: PASS"
