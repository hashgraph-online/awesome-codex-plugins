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
  # Count autofixable codes (per heal.sh: MISSING_NAME, MISSING_DESC, NAME_MISMATCH, UNLINKED_REF, EMPTY_DIR)
  PASS1_AUTOFIXABLE=$(echo "$PASS1_OUT" | grep -cE '^\[(MISSING_NAME|MISSING_DESC|NAME_MISMATCH|UNLINKED_REF|EMPTY_DIR)\]' || true)
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

# Check 1: description-has-triggers (FAIL on miss)
check_description_has_triggers() {
  local skill_md="$1"
  # Form (a): YAML | block scalar in description
  if awk 'BEGIN{n=0; found=0} /^---$/{n++; next} n==1 && /^description: \|/{found=1; exit} n==2{exit} END{exit (found ? 0 : 1)}' "$skill_md" 2>/dev/null; then
    return 0
  fi
  # Form (b): explicit markers in body or in description block
  if grep -qE '(\*\*Use when:|\*\*Triggers:|\*\*Perfect for:|^Triggers:|^Use when:)' "$skill_md"; then
    return 0
  fi
  # Form (c): metadata.triggers array with 3+ items
  if awk '
    BEGIN{n=0; in_arr=0; count=0}
    /^---$/{n++; next}
    n==1 && /^[ ]+triggers:/{in_arr=1; next}
    n==1 && in_arr && /^[ ]+- /{count++; next}
    n==1 && in_arr && /^[a-z_-]+:/{exit}
    END{exit (count >= 3 ? 0 : 1)}
  ' "$skill_md" 2>/dev/null; then
    return 0
  fi
  return 1
}

# Check 2: constraints-frontloaded (WARN on miss)
check_constraints_frontloaded() {
  local skill_md="$1"
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
  # NOTE: case-insensitivity is spelled out per-character because gawk's
  # IGNORECASE=1 is silently ignored by mawk and BSD awk (portability).
  awk '
    BEGIN{in_constraints=0; bullets=0; with_why=0}
    /^## .*([Cc]onstraints|⚠️)/{in_constraints=1; next}
    in_constraints && /^## /{exit}
    in_constraints && /^[ ]*[-*] /{
      bullets++
      if (/[Ww][Hh][Yy]|[Bb]ecause|[Tt]his matters|[Tt]o prevent|[Rr]ationale:|[Mm]otivation:/) with_why++
    }
    END{
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
  local skill_md="$1"
  awk '
    BEGIN{in_out=0; has_format=0; has_path=0}
    /^## (Output|Deliverables|Returns|Output Specification|Output Format)/{in_out=1; next}
    in_out && /^## /{exit}
    in_out {
      if (/markdown|json|yaml|excel|stdout|file|director|\.md|\.json|\.yaml/) has_format=1
      if (/Filename:|Path:|naming|file path|written to|written at|\/.*\.(md|json|yaml|sh)|\.agents\//) has_path=1
    }
    END{exit (has_format && has_path ? 0 : 1)}
  ' "$skill_md"
}

# Check 6: quality-rubric (WARN on miss)
check_quality_rubric() {
  local skill_md="$1"
  awk '
    BEGIN{in_q=0; bullets=0}
    /^## (Quality|Checklist|Rubric|Best Practices|Acceptance)/{in_q=1; next}
    in_q && /^## /{exit}
    in_q && /^[ ]*[-*] /{bullets++}
    END{exit (bullets >= 3 ? 0 : 1)}
  ' "$skill_md"
}

# Check 7: references-modularization (WARN on miss, conditional)
check_references_modularization() {
  local skill_md="$1"
  local skill_dir
  skill_dir="$(dirname "$skill_md")"
  local lines
  lines=$(wc -l < "$skill_md")
  if (( lines <= 400 )); then return 0; fi
  [[ -d "$skill_dir/references" ]] || return 1
  local count
  count=$(find "$skill_dir/references" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  (( count > 0 ))
}

# Check 8: trigger-clarity (FAIL on miss)
check_trigger_clarity() {
  local skill_md="$1"
  awk '
    BEGIN{n=0; in_desc=0; out=""}
    /^---$/{n++; if (n==2) exit; next}
    n==1 && /^description:/{in_desc=1; out=out $0 "\n"; next}
    n==1 && in_desc && /^[a-z_-]+:/{in_desc=0}
    n==1 && in_desc {out=out $0 "\n"}
    END{print out}
  ' "$skill_md" | grep -qE '(Use when:|Triggers:|Perfect for:)'
}

# --- Run all 8 checks ----------------------------------------------------
declare -A CHECK_STATUS=()
declare -A CHECK_EVIDENCE=()

run_check() {
  local id="$1"
  local sev="$2"
  local fn="$3"
  if "$fn" "$SKILL_MD"; then
    CHECK_STATUS[$id]="pass"
    CHECK_EVIDENCE[$id]="check passed"
  else
    CHECK_STATUS[$id]="$sev"
    CHECK_EVIDENCE[$id]="check failed"
  fi
}

run_check description-has-triggers   warn check_description_has_triggers
run_check constraints-frontloaded    warn check_constraints_frontloaded
run_check rationale-present          warn check_rationale_present
run_check verification-checkpoints   warn check_verification_checkpoints
run_check output-spec-explicit       fail check_output_spec_explicit
run_check quality-rubric             warn check_quality_rubric
run_check references-modularization  warn check_references_modularization
run_check trigger-clarity            warn check_trigger_clarity

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
for id in description-has-triggers constraints-frontloaded rationale-present verification-checkpoints output-spec-explicit quality-rubric references-modularization trigger-clarity; do
  case "${CHECK_STATUS[$id]}" in
    fail) fails=$((fails+1)) ;;
    warn) warns=$((warns+1)) ;;
  esac
done

if [[ "$PASS1_STATUS" == "fail" ]]; then
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
  for id in description-has-triggers constraints-frontloaded rationale-present verification-checkpoints output-spec-explicit quality-rubric references-modularization trigger-clarity; do
    if (( ! first )); then printf ',\n'; fi
    first=0
  printf '      {"id":"%s","status":"%s","evidence":"%s"}' "$id" "${CHECK_STATUS[$id]}" "${CHECK_EVIDENCE[$id]}"
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
  echo "Pass 1 (heal-skill --strict): $PASS1_STATUS (exit $PASS1_EXIT_CODE), $PASS1_FINDING_COUNT findings ($PASS1_AUTOFIXABLE autofixable)"
  echo "Pass 2 (8 NEW checks):"
  for id in description-has-triggers constraints-frontloaded rationale-present verification-checkpoints output-spec-explicit quality-rubric references-modularization trigger-clarity; do
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
