#!/usr/bin/env bash
# audit.sh — two-pass skill audit (heal-skill deep audit mode; absorbed from /skill-auditor)
# Pass 1 gates through heal.sh --check --strict; Pass 2 adds 8 NEW content-discipline checks.
# Canonical SKILL.md template: skills/skill-builder/references/skill-template.md
#
# Usage:
#   audit.sh [--strict] [--json <path>] <skills/path>
#
# Exit codes:
#   0  — PASS or WARN (success)
#   1  — FAIL (or WARN under --strict)
#   2  — usage error or missing target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HEAL_SH="$SCRIPT_DIR/heal.sh"
SCORE_PY="$SCRIPT_DIR/score_agentops_skill.py"
PROFILE_TOOL="$REPO_ROOT/skills/skill-builder/scripts/conformance_profile.py"

STRICT=0
JSON_OUT=""
TARGET=""

usage() {
  echo "Usage: $0 [--strict] [--json <path>] <skills/path>" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict) STRICT=1; shift ;;
    --json)   JSON_OUT="${2:-}"; shift 2 ;;
    --help|-h) usage ;;
    --*)      echo "Unknown flag: $1" >&2; usage ;;
    *)        TARGET="$1"; shift ;;
  esac
done

[[ -n "$TARGET" ]] || usage
[[ -d "$TARGET" ]] || { echo "audit.sh: target $TARGET is not a directory" >&2; exit 2; }

SKILL_MD="$TARGET/SKILL.md"
[[ -f "$SKILL_MD" ]] || { echo "audit.sh: no SKILL.md at $SKILL_MD" >&2; exit 2; }

# Load profile identity, rule order/severities, and shared evaluations before
# emitting any verdict. Missing or malformed configuration fails closed.
TARGET_ABS="$(cd "$TARGET" && pwd)"
CANONICAL_TARGET=0
case "$TARGET_ABS" in
  "$REPO_ROOT"/skills/*|"$REPO_ROOT"/skills-codex/*) CANONICAL_TARGET=1 ;;
esac
SELECTED_PROFILE="${SKILL_CONFORMANCE_PROFILE_ID:-}"
if [[ -z "$SELECTED_PROFILE" && "$CANONICAL_TARGET" -eq 0 ]] \
  && ! grep -q '^skill_api_version:' "$SKILL_MD"; then
  SELECTED_PROFILE="external-observation"
fi
profile_args=(--repo-root "$REPO_ROOT" --audit-tsv "$SKILL_MD")
if [[ -n "$SELECTED_PROFILE" ]]; then
  profile_args+=(--profile-id "$SELECTED_PROFILE")
fi
if [[ ! -f "$PROFILE_TOOL" ]]; then
  echo "profile configuration missing: $PROFILE_TOOL" >&2
  exit 2
fi
if ! PROFILE_DATA="$(python3 "$PROFILE_TOOL" "${profile_args[@]}")"; then
  exit 2
fi

PROFILE_ID=""
KERNEL_MAX_LINES=""
PROFILE_LINE_COUNT=""
TRIGGER_FORMS=""
OUTPUT_COMPLETE="false"
RULE_IDS=()
declare -A CHECK_SEVERITY=()
declare -A PROFILE_RULE_FORMS=()
while IFS=$'\t' read -r kind value extra forms; do
  case "$kind" in
    profile_id) PROFILE_ID="$value" ;;
    kernel_max_lines) KERNEL_MAX_LINES="$value" ;;
    line_count) PROFILE_LINE_COUNT="$value" ;;
    trigger_forms) TRIGGER_FORMS="$value" ;;
    output_complete) OUTPUT_COMPLETE="$value" ;;
    rule)
      RULE_IDS+=("$value")
      CHECK_SEVERITY[$value]="$extra"
      PROFILE_RULE_FORMS[$value]="$forms"
      ;;
  esac
done <<<"$PROFILE_DATA"

if [[ -z "$PROFILE_ID" || -z "$KERNEL_MAX_LINES" || ${#RULE_IDS[@]} -eq 0 ]]; then
  echo "profile configuration error: incomplete evaluated profile data" >&2
  exit 2
fi

# --- Pass 1: heal-skill structural ---------------------------------------
PASS1_OUT=""
PASS1_FINDINGS_JSON="[]"
PASS1_AUTOFIXABLE=0
PASS1_STATUS="pass"
PASS1_EXIT_CODE=0
PASS1_FINDING_COUNT=0

if [[ -x "$HEAL_SH" ]]; then
  if PASS1_OUT="$(bash "$HEAL_SH" --check --strict "$TARGET" 2>&1)"; then
    PASS1_STATUS="pass"
    PASS1_EXIT_CODE=0
  else
    PASS1_EXIT_CODE=$?
    PASS1_STATUS="fail"
  fi
  # Parse [CODE] path: msg lines into JSON. Use Python here because BSD awk
  # lacks gawk's match(..., array) extension.
  PASS1_FINDINGS_JSON=$(PASS1_OUT="$PASS1_OUT" python3 - <<'PY'
import json
import os
import re

findings = []
pattern = re.compile(r"^\[([A-Z_]+)\] ([^:]+): (.*)$")
for line in os.environ.get("PASS1_OUT", "").splitlines():
    match = pattern.match(line)
    if match:
        code, path, msg = match.groups()
        findings.append({"code": code, "path": path, "msg": msg})
print(json.dumps(findings))
PY
)
  # Count the complete heal.sh auto-fix allowlist.
  PASS1_AUTOFIXABLE=$(echo "$PASS1_OUT" | grep -cE '^\[(MISSING_NAME|MISSING_DESC|NAME_MISMATCH|UNLINKED_REF|EMPTY_DIR|MISSING_API_VERSION)\]' || true)
else
  PASS1_STATUS="fail"
  PASS1_EXIT_CODE=2
  PASS1_OUT="heal-skill delegate missing or not executable: $HEAL_SH"
  PASS1_FINDINGS_JSON='[{"code":"HEAL_SKILL_MISSING","path":"skills/heal-skill/scripts/heal.sh","msg":"heal-skill delegate missing or not executable"}]'
fi
PASS1_FINDING_COUNT=$(PASS1_FINDINGS_JSON="$PASS1_FINDINGS_JSON" python3 - <<'PY'
import json
import os

try:
    print(len(json.loads(os.environ.get("PASS1_FINDINGS_JSON", "[]"))))
except Exception:
    print(0)
PY
)

# --- Pass 2: 8 NEW checks ------------------------------------------------

# Check 1: description-has-triggers (WARN on miss; run_check registers severity)
check_description_has_triggers() {
  profile_rule_has_form description-has-triggers
}

profile_rule_has_form() {
  local rule_id="$1" accepted form
  accepted=",${PROFILE_RULE_FORMS[$rule_id]},"
  IFS=',' read -r -a found_forms <<<"$TRIGGER_FORMS"
  for form in "${found_forms[@]}"; do
    [[ -n "$form" && "$accepted" == *",$form,"* ]] && return 0
  done
  return 1
}

# Check 2: constraints-frontloaded (WARN on miss)
check_constraints_frontloaded() {
  local skill_md="$1"
  if (( PROFILE_LINE_COUNT <= 100 )); then return 0; fi
  awk '
    BEGIN{n=0; i=0; found=0}
    /^---$/{n++; next}
    n==2 {
      i++
      if (i > 80) { exit 1 }
      if (/^## .*[Cc]onstraints/ || /^## .*⚠️/) { found=1; exit 0 }
    }
    END{ exit (found ? 0 : 1) }
  ' "$skill_md"
}

# Check 3: rationale-present (WARN on miss)
check_rationale_present() {
  local skill_md="$1"
  awk '
    function flush_bullet() {
      if (!bullet_open) return
      bullets++
      if (bullet_text ~ /[Ww][Hh][Yy]|[Bb]ecause|[Tt]his matters|[Tt]o prevent|[Rr]ationale:|[Mm]otivation:/) with_why++
      bullet_open=0
      bullet_text=""
    }
    BEGIN{in_constraints=0; bullets=0; with_why=0; bullet_open=0}
    /^## .*([Cc]onstraints|⚠️)/{in_constraints=1; next}
    in_constraints && /^## /{flush_bullet(); exit}
    in_constraints && /^[ ]*[-*] /{
      flush_bullet()
      bullet_open=1
      bullet_text=$0
      next
    }
    in_constraints && bullet_open{bullet_text=bullet_text " " $0}
    END{
      flush_bullet()
      if (bullets == 0) exit 0
      exit (with_why * 2 >= bullets ? 0 : 1)
    }
  ' "$skill_md"
}

# Check 4: verification-checkpoints (WARN on miss, conditional)
check_verification_checkpoints() {
  local skill_md="$1"
  local phases checkpoints
  phases=$(awk '/^## (Workflow|Methodology|Process|Execution)/{in_w=1; next} in_w && /^## /{exit} in_w && /^### /{n++} END{print n+0}' "$skill_md")
  if (( phases < 2 )); then return 0; fi
  checkpoints=$(grep -cE '\*\*Checkpoint:|confirm before|Wait for|verify before' "$skill_md" 2>/dev/null || echo 0)
  (( checkpoints >= 1 ))
}

# Check 5: output-spec-explicit (FAIL on miss)
check_output_spec_explicit() {
  [[ "$OUTPUT_COMPLETE" == "true" ]]
}

# Check 6: quality-rubric (WARN on miss)
check_quality_rubric() {
  local skill_md="$1"
  if (( PROFILE_LINE_COUNT <= 100 )); then return 0; fi
  awk '
    BEGIN{in_q=0; bullets=0}
    /^## (Quality|Checks|Checklist|Rubric|Best Practices|Acceptance)/{in_q=1; next}
    in_q && /^## /{exit}
    in_q && /^[ ]*[-*] /{bullets++}
    END{exit (bullets >= 3 ? 0 : 1)}
  ' "$skill_md"
}

# Check 7: references-modularization (WARN on miss, conditional)
check_references_modularization() {
  (( PROFILE_LINE_COUNT <= KERNEL_MAX_LINES ))
}

# Check 8: trigger-clarity (WARN on miss; run_check registers severity)
check_trigger_clarity() {
  profile_rule_has_form trigger-clarity
}

# --- Run all 8 checks ----------------------------------------------------
declare -A CHECK_STATUS=()
declare -A CHECK_EVIDENCE=()

run_check() {
  local id="$1"
  local fn="$2"
  local severity="${CHECK_SEVERITY[$id]}"
  if "$fn" "$SKILL_MD"; then
    CHECK_STATUS[$id]="pass"
    CHECK_EVIDENCE[$id]="check passed"
  else
    CHECK_STATUS[$id]="${severity,,}"
    CHECK_EVIDENCE[$id]="check failed"
  fi
}

run_check description-has-triggers   check_description_has_triggers
run_check constraints-frontloaded    check_constraints_frontloaded
run_check rationale-present          check_rationale_present
run_check verification-checkpoints   check_verification_checkpoints
run_check output-spec-explicit       check_output_spec_explicit
run_check quality-rubric             check_quality_rubric
run_check references-modularization  check_references_modularization
run_check trigger-clarity            check_trigger_clarity

# --- Advisory density report ---------------------------------------------
# This is deliberately not part of the PASS/WARN/FAIL verdict. Packet-boundary
# enforcement belongs to the execution-packet schema; this block helps reviewers
# find low-signal skill prose before fresh-context dispatch.
declare -A DENSITY_PRESENT=()
declare -A DENSITY_EVIDENCE=()

check_density_field() {
  local id="$1"
  local pattern="$2"
  if grep -Eiq -- "$pattern" "$SKILL_MD"; then
    DENSITY_PRESENT[$id]="true"
    DENSITY_EVIDENCE[$id]="matched advisory pattern"
  else
    DENSITY_PRESENT[$id]="false"
    DENSITY_EVIDENCE[$id]="missing advisory pattern"
  fi
}

check_density_field intent 'intent|goal|behavior|capability'
check_density_field boundary 'boundary|bounded context|write scope|non-goal|non-goals'
check_density_field evidence 'evidence|test|tests|verdict|validation|acceptance'
check_density_field decision 'decision|rationale|why|because|chosen'
check_density_field constraint 'constraint|constraints|guardrail|guardrails|limit|limits|scope'
check_density_field next_action 'next_action|next action|next steps|completion marker|report completion'

density_present_count=0
for id in intent boundary evidence decision constraint next_action; do
  if [[ "${DENSITY_PRESENT[$id]}" == "true" ]]; then
    density_present_count=$((density_present_count + 1))
  fi
done
if (( density_present_count == 6 )); then
  DENSITY_STATUS="pass"
else
  DENSITY_STATUS="warn"
fi

# --- Pass 3: rubric scoring (advisory) -----------------------------------
# Folds the 10-category Skill Quality Rubric (docs/reference/skill-quality-rubric.md)
# into the report via score_agentops_skill.py --audit-block. Each category gets a
# deterministic 0-3 score plus an explainable reason; total is 0-30 with a C/B/A/S
# rating band. Advisory-only: it never changes the PASS/WARN/FAIL verdict — the
# rubric measures market-facing maturity, not template conformance (which Pass 1+2
# already gate). Reason: a low rubric score on a structurally-clean skill is a
# productization backlog signal, not a ship blocker.
RUBRIC_JSON="null"
RUBRIC_SUMMARY=""
RUBRIC_SCORE="n/a"
RUBRIC_RATING="?"
if [[ -f "$SCORE_PY" ]] && command -v python3 >/dev/null 2>&1; then
  if rubric_out="$(python3 "$SCORE_PY" "$TARGET" --audit-block 2>/dev/null)"; then
    RUBRIC_JSON="$rubric_out"
    RUBRIC_SCORE="$(printf '%s' "$rubric_out" | awk -F': ' '/"total_score"/{gsub(/[, ]/,"",$2); print $2; exit}')"
    RUBRIC_RATING="$(printf '%s' "$rubric_out" | awk -F'"' '/"rating"/{print $4; exit}')"
    RUBRIC_SUMMARY=" Rubric: ${RUBRIC_SCORE}/30 (${RUBRIC_RATING}) [advisory]."
  fi
fi

# --- Aggregate verdict ---------------------------------------------------
fails=0
warns=0
for id in "${RULE_IDS[@]}"; do
  case "${CHECK_STATUS[$id]}" in
    fail) fails=$((fails+1)) ;;
    warn) warns=$((warns+1)) ;;
  esac
done

if [[ "$PASS1_STATUS" == "fail" && "$CANONICAL_TARGET" -eq 1 ]]; then
  VERDICT="FAIL"
elif (( fails > 0 )); then
  VERDICT="FAIL"
elif (( warns > 0 )); then
  VERDICT="WARN"
else
  VERDICT="PASS"
fi

# --- Emit report ---------------------------------------------------------
emit_json() {
  printf '{\n'
  printf '  "target": "%s",\n' "$TARGET"
  printf '  "profile_id": "%s",\n' "$PROFILE_ID"
  printf '  "verdict": "%s",\n' "$VERDICT"
  printf '  "pass1": {\n'
  printf '    "status": "%s",\n' "$PASS1_STATUS"
  printf '    "exit_code": %s,\n' "$PASS1_EXIT_CODE"
  printf '    "strict": true,\n'
  printf '    "findings": %s,\n' "$PASS1_FINDINGS_JSON"
  printf '    "autofixable": %s\n' "$PASS1_AUTOFIXABLE"
  printf '  },\n'
  printf '  "pass2": {\n'
  printf '    "checks": [\n'
  local first=1
  for id in "${RULE_IDS[@]}"; do
    if (( ! first )); then printf ',\n'; fi
    first=0
  printf '      {"id":"%s","status":"%s","severity":"%s","evidence":"%s"' \
    "$id" "${CHECK_STATUS[$id]}" "${CHECK_SEVERITY[$id]}" "${CHECK_EVIDENCE[$id]}"
  if [[ "$id" == "description-has-triggers" || "$id" == "trigger-clarity" ]]; then
    forms_json="$(python3 - "$TRIGGER_FORMS" <<'PY'
import json
import sys

print(json.dumps([item for item in sys.argv[1].split(",") if item]))
PY
)"
    printf ',"forms":%s' "$forms_json"
  fi
  printf '}'
  done
  printf '\n    ]\n'
  printf '  },\n'
  printf '  "density": {\n'
  printf '    "status": "%s",\n' "$DENSITY_STATUS"
  printf '    "advisory": true,\n'
  printf '    "fields": [\n'
  first=1
  for id in intent boundary evidence decision constraint next_action; do
    if (( ! first )); then printf ',\n'; fi
    first=0
    printf '      {"id":"%s","present":%s,"evidence":"%s"}' "$id" "${DENSITY_PRESENT[$id]}" "${DENSITY_EVIDENCE[$id]}"
  done
  printf '\n    ],\n'
  printf '    "summary": "%d/6 density signals present; advisory-only and not execution-packet enforcement."\n' "$density_present_count"
  printf '  },\n'
  printf '  "rubric": %s,\n' "$RUBRIC_JSON"
  printf '  "summary": "Pass1: %s via heal --strict (exit %d, %d findings, %d autofixable). Pass2: %d fails, %d warns.%s Verdict: %s."\n' \
    "$PASS1_STATUS" "$PASS1_EXIT_CODE" "$PASS1_FINDING_COUNT" "$PASS1_AUTOFIXABLE" "$fails" "$warns" "$RUBRIC_SUMMARY" "$VERDICT"
  printf '}\n'
}

if [[ -n "$JSON_OUT" ]]; then
  emit_json > "$JSON_OUT"
fi

# Always print human-readable summary to stderr
{
  echo "=== Skill Audit: $TARGET ==="
  echo "Profile: $PROFILE_ID"
  echo "Pass 1 (heal-skill --strict): $PASS1_STATUS (exit $PASS1_EXIT_CODE), $PASS1_FINDING_COUNT findings ($PASS1_AUTOFIXABLE autofixable)"
  echo "Pass 2 (8 NEW checks):"
  for id in "${RULE_IDS[@]}"; do
    printf "  [%-4s] %s\n" "${CHECK_STATUS[$id]}" "$id"
  done
  echo "Density advisory: $density_present_count/6 fields present ($DENSITY_STATUS)"
  echo "Pass 3 rubric (advisory): ${RUBRIC_SCORE}/30 (${RUBRIC_RATING})"
  echo "VERDICT: $VERDICT"
} >&2

# Always print JSON to stdout (unless --json file was supplied)
if [[ -z "$JSON_OUT" ]]; then
  emit_json
fi

# --- Exit code -----------------------------------------------------------
case "$VERDICT" in
  PASS) exit 0 ;;
  WARN) [[ "$STRICT" -eq 1 ]] && exit 1 || exit 0 ;;
  FAIL) exit 1 ;;
esac
