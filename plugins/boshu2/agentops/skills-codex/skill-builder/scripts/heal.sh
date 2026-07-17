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

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  for path in "$REPO_ROOT/skills"/*; do
    [[ -d "$path" && -f "$path/SKILL.md" ]] && TARGETS+=("$path")
  done
fi

normalized=()
for target in "${TARGETS[@]}"; do
  [[ "$target" = /* ]] || target="$REPO_ROOT/$target"
  [[ -d "$target" ]] || { echo "heal.sh: target does not exist: $target" >&2; exit 2; }
  [[ ! -L "$target" ]] || { echo "heal.sh: symlink targets are not accepted: $target" >&2; exit 2; }
  resolved="$(cd "$target" && pwd -P)"
  case "$(dirname "$resolved")" in
    "$REPO_ROOT/skills") ;;
    *) echo "heal.sh: target is not a direct skill package: $target" >&2; exit 2 ;;
  esac
  normalized+=("$resolved")
done

set +e
python3 - "$REPO_ROOT" "${normalized[@]}" <<'PY'
from pathlib import Path
import re
import sys
import yaml

repo = Path(sys.argv[1])
findings = []
for root in map(Path, sys.argv[2:]):
    skill = root / "SKILL.md"
    rel = root.relative_to(repo).as_posix()
    if not skill.is_file():
        findings.append(("MISSING_SKILL", rel, "SKILL.md is missing"))
        continue
    text = skill.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        findings.append(("INVALID_FRONTMATTER", rel, "leading YAML frontmatter is missing"))
        continue
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        findings.append(("INVALID_FRONTMATTER", rel, str(exc).splitlines()[0]))
        continue
    slug = root.name
    if data.get("name") != slug:
        findings.append(("NAME_MISMATCH", rel, f"name must be {slug!r}"))
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        findings.append(("MISSING_DESC", rel, "description must be nonempty"))
    if data.get("skill_api_version") != 1:
        findings.append(("MISSING_API_VERSION", rel, "skill_api_version must be 1"))
    metadata = data.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("disposition"), str) or not metadata["disposition"]:
        findings.append(("MISSING_DISPOSITION", rel, "metadata.disposition must be nonempty"))
    body = parts[2]
    for match in re.finditer(r"\]\((references|scripts)/([^\s)#?]+)", body):
        linked = root / match.group(1) / match.group(2)
        if not linked.exists():
            findings.append(("DEAD_REF", rel, f"missing {linked.relative_to(root)}"))

for code, path, message in findings:
    print(f"[{code}] {path}: {message}")
sys.exit(1 if findings else 0)
PY
rc=$?
set -e

if [[ "$MODE" == fix ]]; then
  # Source behavior remains human-authored. Repair only owned projections.
  python3 "$REPO_ROOT/scripts/generate-skill-mesh.py"
  names="$(printf '%s\n' "${normalized[@]}" | sed 's#.*/##' | sort -u | paste -sd, -)"
  bash "$REPO_ROOT/scripts/codex-sync.sh" --force --only "$names"
fi

if [[ $rc -ne 0 && ( $STRICT -eq 1 || "$MODE" == fix ) ]]; then
  exit 1
fi
exit 0
