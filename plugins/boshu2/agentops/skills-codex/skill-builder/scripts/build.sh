#!/usr/bin/env bash
# Create, structurally check, and project one skill exactly once.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SKILL_BUILDER_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

usage() {
  cat >&2 <<EOF
usage:
  build.sh from-scratch <slug>
  build.sh from-template <slug> --like <existing-slug>
  build.sh absorb-external <slug> --from <path>
EOF
  exit 2
}

[[ $# -ge 2 ]] || usage
mode="$1"
slug="$2"
shift 2

case "$mode" in
  from-scratch) init_mode=--scratch ;;
  from-template) init_mode=--template ;;
  absorb-external) init_mode=--external ;;
  *) usage ;;
esac

bash "$SCRIPT_DIR/init.sh" "$init_mode" "$slug" "$@"

report="$REPO_ROOT/.agents/audits/${slug}-build.json"
if ! HEAL_REPO_ROOT="$REPO_ROOT" bash "$REPO_ROOT/skills/skill-builder/scripts/heal.sh" \
  --check --strict "$REPO_ROOT/skills/$slug"; then
  echo "skill-builder: structural check failed" >&2
  exit 1
fi

python3 "$REPO_ROOT/scripts/generate-skill-mesh.py"
bash "$REPO_ROOT/scripts/codex-sync.sh" --only "$slug"
bash "$REPO_ROOT/scripts/regen-codex-hashes.sh" --only "$slug"

python3 - "$report" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["structure_check_pass"] = True
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

echo "skill-builder: created and projected $slug"
