#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() { if bash -c "$2"; then echo "PASS: $1"; PASS=$((PASS + 1)); else echo "FAIL: $1"; FAIL=$((FAIL + 1)); fi; }

check "SKILL.md exists" "[ -f '$SKILL_DIR/SKILL.md' ]"
check "SKILL.md has YAML frontmatter" "head -1 '$SKILL_DIR/SKILL.md' | grep -q '^---$'"
check "Codex parity reference exists" "[ -f '$SKILL_DIR/references/codex-parity.md' ]"
check "SKILL.md links Codex parity reference" "grep -q 'references/codex-parity.md' '$SKILL_DIR/SKILL.md'"

# --- Deep audit mode (absorbed from /skill-auditor) ---
for f in scripts/audit.sh scripts/score_agentops_skill.py references/audit-checks.md references/context-density-checks.md schemas/audit-report.json; do
  check "audit artifact $f exists" "[ -f '$SKILL_DIR/$f' ]"
done

# audit.sh must contain all 8 Pass-2 check function names
for fn in check_description_has_triggers check_constraints_frontloaded check_rationale_present check_verification_checkpoints check_output_spec_explicit check_quality_rubric check_references_modularization check_trigger_clarity; do
  check "audit.sh has $fn" "grep -q '^${fn}()' '$SKILL_DIR/scripts/audit.sh'"
done

# Advisory density block: function + all six fields, outside the Pass-2 verdict loop
check "audit.sh has density function" "grep -q '^check_density_field()' '$SKILL_DIR/scripts/audit.sh'"
for field in intent boundary evidence decision constraint next_action; do
  check "audit.sh has density field $field" "grep -q '$field' '$SKILL_DIR/scripts/audit.sh'"
done

# Pass 1 must delegate to heal.sh --check --strict and gate on exit code
check "audit.sh delegates via --check --strict" "grep -q -- '--check --strict' '$SKILL_DIR/scripts/audit.sh'"
check "audit.sh gates Pass 1 on exit code" "grep -q 'PASS1_EXIT_CODE' '$SKILL_DIR/scripts/audit.sh'"
check "audit report includes Pass-1 exit_code" "grep -q '\"exit_code\": %s' '$SKILL_DIR/scripts/audit.sh'"

# Stale check name must be gone (pre-mortem F1)
check "audit.sh has no stale check_description_multiline" "! grep -q 'check_description_multiline' '$SKILL_DIR/scripts/audit.sh'"

# Pass 3 rubric wiring (advisory): scorer invoked, rubric block emitted, --audit-block supported
check "audit.sh invokes rubric scorer" "grep -q 'score_agentops_skill.py' '$SKILL_DIR/scripts/audit.sh'"
check "audit.sh emits rubric block" "grep -q '\"rubric\": %s' '$SKILL_DIR/scripts/audit.sh'"
check "scorer supports --audit-block" "grep -q -- '--audit-block' '$SKILL_DIR/scripts/score_agentops_skill.py'"

echo ""; echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
