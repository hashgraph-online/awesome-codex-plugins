#!/usr/bin/env bash
# Domain skill contract validator.
#
# Domain's AgentOps lookup returns definitions from the two cited contract
# files. This check covers that lookup's source integrity, not the semantic
# quality of caller-domain modeling. It detects a moved contract path or a
# definition that no longer resolves. tests/skills/run-all.sh runs it.
set -euo pipefail

# The contracts live in the AgentOps checkout, not in the skill. Resolve that
# checkout through git from the skill's real location (pwd -P follows a linked
# skill dir), so skills/domain and a projected plugin/skills/domain both find
# it. A copy outside any AgentOps checkout (a plugin install) has no contracts
# to check, so it skips. A hook-injected GIT_DIR would point git elsewhere.
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
repo_root="$(env -u GIT_DIR -u GIT_WORK_TREE git -C "$skill_dir" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" || ! -f "$repo_root/skills/domain/SKILL.md" ]]; then
  echo 'domain skill contract: SKIP (not inside an AgentOps checkout)'
  exit 0
fi

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
