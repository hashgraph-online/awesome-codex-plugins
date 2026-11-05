#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$SKILL_DIR/SKILL.md"

# Structural contract checks. Bare greps run under `set -e`, so a missing
# section fails the script — unlike the prior prose-word greps, which passed
# even after the load-bearing sections were deleted.
[[ -s "$SKILL" ]]
head -1 "$SKILL" | grep -q '^---$'
grep -q '^name: test$' "$SKILL"

# Load-bearing doctrine sections. Deleting any one must turn this validator red.
grep -q '^## Critical Constraints$' "$SKILL"
grep -q '^## Oracle-strength hierarchy$' "$SKILL"
grep -q '^## Mutation-kill proof$' "$SKILL"
grep -q '^## Harness health floors$' "$SKILL"
grep -q '^## Workflow$' "$SKILL"
grep -q '^## Output Specification$' "$SKILL"

# The mode table must enumerate the four real modes.
for mode in generate coverage tdd strategy; do
  grep -Eq "^\| \`${mode}\`" "$SKILL"
done

# GitHub-style heading anchor: lowercase, drop punctuation but - and _, spaces to hyphens.
slugify() { printf '%s\n' "$1" | tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -E 's/[^a-z0-9 _-]//g; s/ /-/g'; }

# The anchors a Markdown file defines: one per heading outside fenced code.
anchors_of() {
  local heading
  awk '/^```/ { fence = !fence; next } !fence && /^#+ / { sub(/^#+ +/, ""); sub(/ +#+ *$/, ""); print }' "$1" |
    while IFS= read -r heading; do slugify "$heading"; done
}

# Every relative link in SKILL.md and references/*.md must resolve to a file,
# and every #anchor to a heading in that file. Prints each failure; returns 1 on any.
check_links() {
  local dir="$1" doc link path anchor target anchors rc=0
  for doc in "$dir/SKILL.md" "$dir"/references/*.md; do
    [[ -f "$doc" ]] || continue
    while IFS= read -r link; do
      case "$link" in *://*|mailto:*) continue ;; esac
      path="${link%%#*}"
      anchor=""
      [[ "$link" != *"#"* ]] || anchor="${link#*#}"
      target="$doc"
      [[ -z "$path" ]] || target="$(dirname "$doc")/$path"
      if [[ ! -f "$target" ]]; then
        echo "test contract: dangling reference $link in ${doc#"$dir"/}" >&2
        rc=1
        continue
      fi
      [[ -n "$anchor" ]] || continue
      anchors="$(anchors_of "$target")"
      if ! grep -qxF -- "$anchor" <<<"$anchors"; then
        echo "test contract: no heading for #$anchor in $link (${doc#"$dir"/})" >&2
        rc=1
      fi
    done < <(grep -oE '\]\([^) ]+' "$doc" | cut -c3- | sort -u)
  done
  return "$rc"
}

check_links "$SKILL_DIR"

# Negative control: the link check must fail on a seeded broken anchor, or a
# checker that resolves nothing would still report PASS.
seed="$(mktemp -d)"
trap 'rm -rf "$seed"' EXIT
mkdir "$seed/references"
printf '# Seed\n\n[x](references/r.md#absent)\n' >"$seed/SKILL.md"
printf '# R\n\n## Present heading\n' >"$seed/references/r.md"
if check_links "$seed" 2>/dev/null; then
  echo "test contract: anchor check missed a seeded broken anchor" >&2
  exit 1
fi

echo "test contract: PASS"
