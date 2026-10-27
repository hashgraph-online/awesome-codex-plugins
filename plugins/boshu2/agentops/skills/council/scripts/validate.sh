#!/usr/bin/env bash
# Council contract check: the report validator accepts a report written from
# SKILL.md (from a file and from stdin) and rejects the shapes SKILL.md forbids.
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="$skill_dir/scripts/validate-output.sh"

grep -q '^name: council$' "$skill_dir/SKILL.md"
test -f "$skill_dir/schemas/council-report.v1.schema.json"
test -x "$validator"

if grep -Eiq 'ao (pawl|land)|git (commit|push)|br (close|update)|auto-redo' \
  "$skill_dir/SKILL.md"; then
  echo 'council contract contains forbidden lifecycle authority' >&2
  exit 1
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cat > "$work/valid.json" <<'JSON'
{
  "schema_version": "council-report.v1",
  "question": "Which redelivery design should Jobs use?",
  "subject_digest": "d8b2a162067e029106522c91d75916b13abc28438e19b45de8c2447866c7aa9b",
  "recommendation": "Outbox; a lease would also serve if peak write volume stays low.",
  "diversity_unsatisfied": ["model-c"],
  "judges": [
    {"context_id": "ctx-1", "methodology": "static reading", "model_identity": "model-a",
     "judgment": "round 0, independent: outbox survives a broker restart",
     "evidence": ["docs/design.md:12"]},
    {"context_id": "ctx-2", "methodology": "executing the subject", "model_identity": "model-b",
     "judgment": "round 0, independent: outbox; the lease loses jobs under clock skew",
     "evidence": ["redelivery test run"], "omissions": ["did not read the billing service"]}
  ],
  "synthesis": {
    "consensus": [{"claim": "Outbox survives a broker restart",
      "methodologies": ["static reading", "executing the subject"], "models": ["model-a", "model-b"]}],
    "divergence": [],
    "minority": ["ctx-2: the lease loses jobs under clock skew"],
    "unresolved": ["Peak write volume is unmeasured"],
    "notes": ["roster model-a, model-b, model-c; model-c had no authorized adapter"],
    "caller_challenge": [{"caller_stated": "Billing stays inside the core service",
      "judges_recommend": "ctx-1 and ctx-2, independently: a billing service", "judge_count": 2,
      "reasoning": "Billing deploys on its own cadence",
      "context_possibly_missing": "Neither judge saw the billing team's staffing",
      "cost_if_wrong": "A second deploy pipeline for one small team",
      "disagreement_kind": "preference"}]
  }
}
JSON

"$validator" "$work/valid.json" >/dev/null
"$validator" - < "$work/valid.json" >/dev/null

accept() {
  jq "$2" "$work/valid.json" > "$work/$1.json"
  "$validator" "$work/$1.json" >/dev/null || {
    echo "council validator rejected a valid report: $1" >&2
    exit 1
  }
}

reject() {
  local rc=0
  jq "$2" "$work/valid.json" > "$work/$1.json"
  "$validator" "$work/$1.json" >/dev/null 2>&1 || rc=$?
  if [[ $rc -ne 1 ]]; then
    echo "council validator did not reject (exit $rc): $1" >&2
    exit 1
  fi
}

accept marked-single-method '.synthesis.consensus[0] += {methodologies: ["static reading"], weighs_as_one: true}'
accept boolean-diversity '.diversity_unsatisfied = true'
reject verdict-field '. + {verdict: "PASS"}'
reject verdict-judgment '.judges[0].judgment = "pass"'
reject verdict-recommendation '.recommendation = "NOT_PROVEN"'
reject unmarked-single-method '.synthesis.consensus[0].methodologies = ["static reading"]'
reject duplicate-methodology '.synthesis.consensus[0].methodologies = ["static reading", "static reading"]'
reject methodology-no-judge-used '.synthesis.consensus[0].methodologies = ["static reading", "tracing history"]'
reject unmarked-single-model '.synthesis.consensus[0].models = ["model-a"]'
reject model-no-judge-used '.synthesis.consensus[0].models = ["model-a", "model-z"]'
reject challenge-without-missing-context 'del(.synthesis.caller_challenge[0].context_possibly_missing)'
reject evidence-free-judge '.judges[1].evidence = []'

echo 'council skill contract: PASS'
