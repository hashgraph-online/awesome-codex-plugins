#!/usr/bin/env bash
set -euo pipefail
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
grep -q '^name: plan$' "$skill_dir/SKILL.md"
# Static contract regression checks, not proof of a live planner's behavior.
# test_no_model_authored_packet
grep -Fq "Prefer the caller's tracker, if any" "$skill_dir/SKILL.md"
grep -Fq 'Planning produces no AgentOps packet' "$skill_dir/SKILL.md"
if grep -Fq 'plan-packet.v1' "$skill_dir/SKILL.md"; then
  echo 'plan contract references a model-authored plan packet' >&2
  exit 1
fi
# Selective method links must ship their source owners.
for reference in ground-truth-routing.md challenge.md; do
  grep -Fq "references/$reference" "$skill_dir/SKILL.md"
  test -s "$skill_dir/references/$reference"
done
# test_optional_discovery_methods: reject the original mandatory-control rule.
if grep -Eiq 'Every plan needs a ground truth|run the stock control|mandatory deviation ledger' \
  "$skill_dir/references/ground-truth-routing.md"; then
  echo 'plan routing restores a mandatory control or ledger' >&2
  exit 1
fi
# test_native_handoff_boundary: factual native references are legal. The old
# blanket prohibition would prevent recovery; it was not a lifecycle guard.
if grep -Eq 'contains no owner, ready, claim, priority, attempt, wave, queue, lease, admission, next action' \
  "$skill_dir/references/plan.feature"; then
  echo 'plan scenarios forbid factual native handoff recovery' >&2
  exit 1
fi
echo 'plan static contract checks: PASS (live behavior not evaluated)'
