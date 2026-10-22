#!/usr/bin/env bash
set -euo pipefail

# pwd -P: this skill is invoked through a symlink (~/.claude/skills/security ->
# the checkout); a logical pwd would resolve ../.. against the symlink's parent
# (.claude), so the repo-surface probe below would silently miss AGENTS.md and
# skip the behavioral redteam instead of running it.
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SKILL="$SKILL_DIR/SKILL.md"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd -P)"

[[ -s "$SKILL" ]]
grep -q '^name: security$' "$SKILL"

# effects must be DECLARED, not the copied-default empty array. This gate used
# to pin `effects: []`; that pin mechanically enforced a false contract (the
# skill writes scan artifacts). The check is now inverted: an empty effects
# array fails.
if grep -q '^  effects: \[\]$' "$SKILL"; then
  echo 'security effects must be declared (the skill writes scan artifacts); effects: [] is a false contract' >&2
  exit 1
fi

[[ "$(awk '/^---$/{n++;next} n==2 && /^## /{print;exit}' "$SKILL")" == "## Critical Constraints" ]]
grep -Fq '**Artifact directory:**' "$SKILL"
grep -Fq '**Validator command:**' "$SKILL"
grep -Fq 'report stops after evidence' "$SKILL"
if grep -Eiq 'AUTO-REDO|ONE-HELPER|HELPER-ESCALATE|ao (pawl|land)|next_action' "$SKILL"; then
  echo 'security contract contains retired lifecycle vocabulary' >&2
  exit 1
fi

# The skill-local security-gate.sh duplicate was unrunnable: its REPO_ROOT
# resolved to skills/security, so it looked for a nonexistent skill-local
# toolchain-validate.sh and exited 1. The canonical gate is the repo-root
# scripts/security-gate.sh (documented in SKILL.md). Guard against the
# duplicate coming back.
if [[ -e "$SKILL_DIR/scripts/security-gate.sh" ]]; then
  echo 'skill-local scripts/security-gate.sh duplicate is back — it is unrunnable; use the repo-root gate' >&2
  exit 1
fi

[[ -s "$SKILL_DIR/references/policy-example.json" ]]
[[ -s "$SKILL_DIR/references/agentops-redteam-pack.json" ]]
[[ -s "$SKILL_DIR/references/security-suite-runbook.md" ]]

# Syntax-check the shipped Python without writing __pycache__/*.pyc into the
# package (py_compile writes the default cfile even with cfile=None); ast.parse
# validates syntax and writes nothing.
python3 - "$SKILL_DIR/scripts/security_suite.py" "$SKILL_DIR/scripts/prompt_redteam.py" <<'PY'
import ast
import sys
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        ast.parse(fh.read(), filename=path)
PY
python3 -c 'import json, pathlib, sys; root=pathlib.Path(sys.argv[1]); [json.loads((root/name).read_text()) for name in ("policy-example.json", "agentops-redteam-pack.json")]' "$SKILL_DIR/references"

# Behavioral redteam: run the attack pack against the live repo surfaces and
# require verdict PASS. This is what keeps the pack honest — a stale target glob
# or pattern (the "fails against its own tree" defect) turns this red. It is
# only meaningful when the governance surfaces the pack targets are present, so
# it is gated on the real repo; an isolated skill copy or standalone install
# (which lacks AGENTS.md and docs/) skips it with a disclosed note rather than
# failing on absent, unscannable surfaces.
if [[ -f "$REPO_ROOT/AGENTS.md" && -f "$REPO_ROOT/docs/CI-CD.md" ]]; then
  redteam_out="$(mktemp -d "${TMPDIR:-/tmp}/security-redteam.XXXXXX")"
  trap 'rm -rf "$redteam_out"' EXIT
  if python3 "$SKILL_DIR/scripts/prompt_redteam.py" scan \
      --repo-root "$REPO_ROOT" \
      --pack-file "$SKILL_DIR/references/agentops-redteam-pack.json" \
      --out-dir "$redteam_out" >/dev/null 2>&1; then
    echo "security redteam: PASS (attack pack holds against the live tree)"
  else
    echo 'security redteam FAILED against the live tree — a target glob or pattern is stale, or a control regressed' >&2
    jq -r '.failed_cases[]?' "$redteam_out/redteam/redteam-results.json" 2>/dev/null \
      | sed 's/^/  failed case: /' >&2 || true
    exit 1
  fi
else
  echo "security redteam: SKIP (repo governance surfaces absent; not the AgentOps repo)"
fi

echo "security contract: PASS"
