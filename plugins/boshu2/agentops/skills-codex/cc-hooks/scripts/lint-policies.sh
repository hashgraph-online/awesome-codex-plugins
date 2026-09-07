#!/usr/bin/env bash
# lint-policies.sh — mechanical enforcement of the hooks-manifest.v2 contract
# (age-bhsz). jq + grep only (no jsonschema dependency), so the discipline is
# checkable in bats, pre-commit, and CI alike.
#
# Checks, in order:
#   1. registry parses as JSON and declares schema hooks-manifest.v2
#   2. every policy has id / predicate_class / mode / matchers / route_message /
#      rationale / value_proof
#   3. id matches domain.object:token and is unique
#   4. mode is deny|route|audit; predicate_class is pure|lookup|stateful
#   5. PREDICATE DISCIPLINE: predicate_class != pure  =>  mode == audit
#      (the #511 anti-lesson — stateful guards are barred from blocking
#      until promoted from audit with reviewed fires)
#   6. matcher tools are Bash|Edit|Write; field is command|file_path
#   7. every pattern compiles under grep -E on this host
#
# Usage: lint-policies.sh [registry.json]   (default: ../policies/policies.json)
set -uo pipefail

# shellcheck disable=SC1007  # CDPATH= scopes an empty CDPATH to the cd, intentionally
script_dir="$(CDPATH= cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
registry="${1:-${script_dir}/../policies/policies.json}"

fail() { printf 'lint-policies: FAIL: %s\n' "$1" >&2; exit 1; }

command -v jq >/dev/null 2>&1 || fail "jq is required"
[ -f "$registry" ] || fail "registry not found: ${registry}"

jq empty "$registry" 2>/dev/null || fail "not valid JSON: ${registry}"

schema="$(jq -r '.schema // ""' "$registry")"
[ "$schema" = "hooks-manifest.v2" ] || fail "schema must be hooks-manifest.v2, got: '${schema}'"

count="$(jq '.policies | length' "$registry")"
[ "$count" -ge 1 ] || fail "policies array is empty"

# Required fields present and non-empty on every policy.
missing="$(jq -r '
  .policies[]
  | . as $p
  | ["id","predicate_class","mode","matchers","route_message","rationale","value_proof"][]
  | select(($p[.] // "") == "" or ($p[.] == null))
  | ($p.id // "<no-id>") + " missing " + .
' "$registry")"
[ -z "$missing" ] || fail "$missing"

# id format + uniqueness.
bad_id="$(jq -r '.policies[].id | select(test("^[a-z][a-z0-9-]*\\.[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$") | not)' "$registry")"
[ -z "$bad_id" ] || fail "id not domain.object:token: ${bad_id}"
dup_id="$(jq -r '[.policies[].id] | group_by(.) | map(select(length > 1) | .[0]) | .[]' "$registry")"
[ -z "$dup_id" ] || fail "duplicate policy id: ${dup_id}"

# Enums.
bad_mode="$(jq -r '.policies[] | select(.mode | IN("deny","route","audit") | not) | .id' "$registry")"
[ -z "$bad_mode" ] || fail "invalid mode on: ${bad_mode}"
bad_class="$(jq -r '.policies[] | select(.predicate_class | IN("pure","lookup","stateful") | not) | .id' "$registry")"
[ -z "$bad_class" ] || fail "invalid predicate_class on: ${bad_class}"

# THE DISCIPLINE RULE: non-pure predicates may only audit.
undisciplined="$(jq -r '.policies[] | select(.predicate_class != "pure" and .mode != "audit") | .id' "$registry")"
[ -z "$undisciplined" ] || fail "predicate discipline violation (non-pure predicate in blocking mode): ${undisciplined}"

# Matcher shape.
bad_tool="$(jq -r '.policies[] | .id as $id | .matchers[].tools[] | select(IN("Bash","Edit","Write") | not) | $id + " tool " + .' "$registry")"
[ -z "$bad_tool" ] || fail "invalid matcher tool: ${bad_tool}"
bad_field="$(jq -r '.policies[] | .id as $id | .matchers[] | select(.field | IN("command","file_path") | not) | $id' "$registry")"
[ -z "$bad_field" ] || fail "invalid matcher field on: ${bad_field}"

# Every pattern must compile under grep -E on this host.
# join(), not @tsv: TSV escaping mangles backslashes inside patterns.
while IFS=$'\x1f' read -r pid pattern; do
  [ -n "$pid" ] || continue
  if ! printf '' | grep -qE "$pattern" 2>/dev/null; then
    # grep exits 1 on no-match with a VALID pattern; only exit >1 is a compile error.
    rc=$?
    [ "$rc" -le 1 ] || fail "pattern does not compile (grep -E rc=${rc}) on ${pid}: ${pattern}"
  fi
done < <(jq -r '.policies[] | .id as $id | .matchers[] | [$id, .pattern] | join("")' "$registry")

printf 'lint-policies: OK (%s policies)\n' "$count"
