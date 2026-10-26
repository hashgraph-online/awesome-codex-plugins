#!/usr/bin/env bash
# shellcheck disable=SC2059 # the printf formats below are this script's own literals
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_validator="$skill_dir/scripts/validate-output.sh"

grep -q '^name: premortem$' "$skill_dir/SKILL.md"
test -f "$skill_dir/schemas/premortem-plan-review.v1.schema.json"
test -x "$output_validator"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo|next[_ -]action' \
  "$skill_dir/SKILL.md"; then
  echo 'premortem contract contains forbidden lifecycle authority' >&2
  exit 1
fi

# The output validator accepts a well-formed review and rejects malformed ones
# with its own message, never a Python traceback.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
review='{"schema_version":"premortem-plan-review.v1","intent_digest":%s,"author_context_id":"%s","judge_context_id":"%s","findings":[{"id":"F1","statement":"s","evidence":["e"]}],"checked":[],"not_checked":[]}'
digest="\"$(printf 'a%.0s' {1..64})\""
printf "$review" "$digest" caller judge >"$tmp/valid.json"
"$output_validator" "$tmp/valid.json" >/dev/null
printf '7' >"$tmp/top-level-number.json"
printf "$review" 5 caller judge >"$tmp/digest-not-string.json"
printf "$review" "$digest" same same >"$tmp/same-ids.json"
for seeded in top-level-number digest-not-string same-ids; do
  if err="$("$output_validator" "$tmp/$seeded.json" 2>&1)" || [[ "$err" == *Traceback* ]]; then
    echo "premortem output validator mishandled seeded case: $seeded" >&2
    exit 1
  fi
done

echo 'premortem skill contract: PASS'
