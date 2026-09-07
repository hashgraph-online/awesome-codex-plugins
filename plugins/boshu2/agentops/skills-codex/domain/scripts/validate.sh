#!/usr/bin/env bash
# Domain skill contract validator.
#
# Domain is a read-only lookup: it returns the exact definition of an AgentOps
# term from the two cited contract files and stops. The failure this guards is
# a citation that has silently decayed — a contract path that moved, or a term
# the skill promises to resolve that is no longer present in its cited source.
# Both are the "floating citation" failure the skill's own prose warns about,
# made checkable. This is the entry point audit.sh looks for.
set -euo pipefail

# pwd -P: this skill is invoked through a symlink (~/.claude/skills/domain ->
# the checkout); a logical pwd would resolve ../.. against the symlink's parent
# (.claude) and false-report the cited contracts as missing.
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
repo_root="$(cd "$skill_dir/../.." && pwd -P)"

lang="$repo_root/docs/contracts/ubiquitous-language.md"
contexts="$repo_root/docs/contracts/bounded-contexts.yaml"

fail=0

for path in "$lang" "$contexts"; do
  if [[ ! -f "$path" ]]; then
    echo "domain: cited contract path missing: ${path#"$repo_root"/}" >&2
    fail=1
  fi
done

# The skill's failure-mode example turns on "verdict" keeping its exact meaning;
# assert that term still resolves inside the cited definition source.
if [[ -f "$lang" ]] && grep -Fq '| Verdict |' "$lang"; then
  :
else
  echo "domain: term 'Verdict' no longer resolves in ubiquitous-language.md" >&2
  fail=1
fi

# The Judgment bounded context (BC2) owns Verdict; assert it still resolves so
# the ownership half of a lookup cannot drift out from under the skill.
if [[ -f "$contexts" ]] && grep -Fq 'name: Judgment' "$contexts"; then
  :
else
  echo "domain: bounded context 'Judgment' no longer resolves in bounded-contexts.yaml" >&2
  fail=1
fi

# The SKILL.md contract itself must still forbid smuggling caller-lifecycle
# words in as synonyms — the whole reason the lookup is authoritative.
if grep -Fq 'synonym smuggling' "$skill_dir/SKILL.md"; then
  :
else
  echo "domain: SKILL.md dropped the synonym-smuggling failure mode" >&2
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo 'domain skill contract: FAIL' >&2
  exit 1
fi

echo 'domain skill contract: PASS'
