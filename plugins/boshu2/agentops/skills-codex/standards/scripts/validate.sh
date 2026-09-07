#!/usr/bin/env bash
# Standards skill contract validator.
#
# Standards is a read-only reference library: it loads the smallest set of
# reference files justified by a change and reports cited findings. Its one
# machine-checkable invariant is that every reference it advertises actually
# resolves — a dead link here silently drops a whole language or checklist from
# the corpus a reviewer thinks they consulted. This gate resolves every
# reference link in SKILL.md and every language file named in the canonical
# owners table, and guards against the dead-anchor regression the audit found.
set -euo pipefail

# pwd -P so resolution follows the symlinked skills estate to the real checkout.
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
skill_md="$skill_dir/SKILL.md"
common="$skill_dir/references/common-standards.md"

fail=0

# 1. Every references/*.md link in SKILL.md must resolve.
found_links=0
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  found_links=$((found_links + 1))
  if [[ ! -f "$skill_dir/$rel" ]]; then
    echo "standards: unresolved reference link in SKILL.md: $rel" >&2
    fail=1
  fi
done < <(grep -oE 'references/[A-Za-z0-9._-]+\.md' "$skill_md" | sort -u)

if [[ "$found_links" -eq 0 ]]; then
  echo "standards: SKILL.md declares no reference links (References section lost?)" >&2
  fail=1
fi

# 2. Every language file named in the Canonical Language Owners table must
#    resolve — this is what keeps the owners table honest (javascript.md was
#    missing from it while the file existed and was linked).
while IFS= read -r name; do
  [[ -n "$name" ]] || continue
  bare="${name//\`/}"
  if [[ ! -f "$skill_dir/references/$bare" ]]; then
    echo "standards: owners table names a missing language file: $bare" >&2
    fail=1
  fi
done < <(grep -oE '`[a-z]+\.md`' "$common" | sort -u)

# 2b. Reverse direction: every language reference file that declares itself a
#     "<Lang> Standards (Tier N)" catalog must have a row in the owners table.
#     The table->file check above only shrinks, so without this a deleted row
#     (e.g. the JavaScript row) would stay green. This compares the table
#     against the actual language files, so a missing row fails.
bt='`'
while IFS= read -r ref; do
  [[ -n "$ref" ]] || continue
  if head -1 "$ref" | grep -Eq 'Standards \(Tier'; then
    base="$(basename "$ref")"
    # Match only a table row (line starting with |), not a prose mention.
    if grep -Eq "^\|.*${bt}${base//./\\.}${bt}" "$common"; then
      :
    else
      echo "standards: language file $base has no row in the Canonical Language Owners table" >&2
      fail=1
    fi
  fi
done < <(find "$skill_dir/references" -maxdepth 1 -name '*.md' | sort)

# 3. Regression guard: the dead #dedup-manifest TOC anchor must stay gone.
if grep -Fq 'dedup-manifest' "$common"; then
  echo "standards: dead #dedup-manifest TOC anchor is back in common-standards.md" >&2
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo 'standards skill contract: FAIL' >&2
  exit 1
fi

echo "standards skill contract: PASS (${found_links} reference links resolve)"
