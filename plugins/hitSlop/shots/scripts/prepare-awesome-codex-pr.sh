#!/usr/bin/env bash
set -euo pipefail

target_dir="${1:-$(mktemp -d "${TMPDIR:-/tmp}/awesome-codex-shots.XXXXXX")}"
repo_url="${AWESOME_CODEX_REPO:-https://github.com/hashgraph-online/awesome-codex-plugins.git}"
branch="${AWESOME_CODEX_BRANCH:-add-shots-plugin}"
entry="- [Shots](https://github.com/hitSlop/shots) - Agent-native App Store screenshot, app icon, ASO, and localization workflows through the hosted Shots MCP server."

mkdir -p "$target_dir"
git clone "$repo_url" "$target_dir/awesome-codex-plugins"
cd "$target_dir/awesome-codex-plugins"
git checkout -b "$branch"

python3 - "$entry" <<'PY'
from pathlib import Path
import re
import sys

entry = sys.argv[1]
readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
if entry in text:
    raise SystemExit("Shots entry already exists in README.md")

start = text.index("## Tools & Integrations")
try:
    end = text.index("\n## ", start + 1)
except ValueError:
    end = len(text)

section = text[start:end]
lines = section.splitlines()
insert_at = None
entries = []
for index, line in enumerate(lines):
    if line.startswith("- "):
        match = re.match(r"- \[([^\]]+)\]\(", line)
        if match:
            entries.append((index, line, match.group(1).casefold()))

for index, _line, title in entries:
    if "shots" < title:
        insert_at = index
        break

if insert_at is None:
    insert_at = entries[-1][0] + 1 if entries else len(lines)

lines.insert(insert_at, entry)
updated = "\n".join(lines)
readme.write_text(text[:start] + updated + text[end:], encoding="utf-8")
PY

git diff -- README.md

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI or run gh auth login before opening the draft PR."
  echo "Prepared checkout: $target_dir/awesome-codex-plugins"
  exit 0
fi

gh repo fork --remote --remote-name fork
git push -u fork "$branch"
github_user="$(gh api user --jq .login)"

gh pr create \
  --repo hashgraph-online/awesome-codex-plugins \
  --base main \
  --head "${github_user}:${branch}" \
  --draft \
  --title "Add Shots plugin" \
  --body "Adds Shots to Tools & Integrations.\n\nPlugin repo: https://github.com/hitSlop/shots\nScanner evidence: paste the passing HOL scanner run URL or score before marking ready for review."
