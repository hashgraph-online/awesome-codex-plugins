#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill="$skill_dir/SKILL.md"

# Structural checks for the current documentation modes and authority boundary.
# Links/build checks validate documents; this script does not judge prose quality.
grep -q '^name: doc$' "$skill"
grep -q '^## Missing-document setup$' "$skill"
grep -q '^## Session handoff$' "$skill"
grep -Fq 'Existing authorization to revise' "$skill"
tr '\n' ' ' < "$skill" | grep -Fq 'Setup does not install tools'
grep -Fq 'a collision is skipped' "$skill"
grep -Fq 'Writing a handoff changes no tracker, Git, runtime or verdict state' "$skill"
grep -Fq 'existing authorization is sufficient' "$skill_dir/references/oss-pack.md"
grep -Fq 'Then it updates the authorized files without asking again' "$skill_dir/references/oss-docs.feature"
grep -Fq 'Then it leaves existing files unchanged' "$skill_dir/references/oss-docs.feature"

# Preserve every linked local resource, including the migrated setup examples.
python3 - "$skill" <<'CHECK_LINKS'
from pathlib import Path
import re
import sys
skill = Path(sys.argv[1])
for target in re.findall(r'\]\(([^)]+)\)', skill.read_text()):
    target = target.split('#', 1)[0]
    if not target or '://' in target:
        continue
    if not (skill.parent / target).is_file():
        raise SystemExit(f'doc link does not resolve: {target}')
CHECK_LINKS

echo 'doc structure and resource boundaries: PASS'
