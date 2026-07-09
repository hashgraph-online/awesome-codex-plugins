#!/usr/bin/env bash
# validate.sh — self-check for the agy-native skill (AUTHORING-STANDARD §6/§8).
# Checks: frontmatter completeness, the required section spine + order, the Form-A
# line budget, the mandatory line-start Triggers: marker, companion artifacts
# (skill.spec.json), local references/ resolution, and the no-`claude -p`-for-workers
# invariant this skill is built to enforce. Exit 0 on pass, 1 on any failure.
set -euo pipefail

# Resolve the skill root regardless of cwd (portable, no hardcoded home).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL="$ROOT/SKILL.md"
SPEC="$ROOT/skill.spec.json"

fail=0
err() { printf 'FAIL: %s\n' "$1" >&2; fail=1; }
ok()  { printf 'ok: %s\n' "$1"; }

# --- 0. SKILL.md exists -------------------------------------------------------
[ -f "$SKILL" ] || { err "SKILL.md missing at $SKILL"; exit 1; }

# --- 1. Frontmatter present + required keys ------------------------------------
fm="$(awk 'NR==1 && $0!="---"{exit 1} NR>1 && $0=="---"{exit 0} {print}' "$SKILL" 2>/dev/null || true)"
[ -n "$fm" ] || err "frontmatter block (--- ... ---) not found at top of SKILL.md"
for key in "name:" "description:" "skill_api_version:" "metadata:" "output_contract:"; do
  printf '%s\n' "$fm" | grep -q "^$key" || err "frontmatter missing required key: $key"
done
# name must equal the directory name (lowercase-hyphen rule).
dir_name="$(basename "$ROOT")"
fm_name="$(printf '%s\n' "$fm" | awk -F': *' '/^name:/{print $2; exit}')"
[ "$fm_name" = "$dir_name" ] || err "frontmatter name ($fm_name) != directory ($dir_name)"

# --- 2. Triggers: marker (FAIL-severity) --------------------------------------
# Must be a real line-start "Triggers:" marker inside the description block.
grep -qE '^[[:space:]]*Triggers:' "$SKILL" || err "no line-start 'Triggers:' marker in description"

# --- 3. Required section spine, in order --------------------------------------
spine=(
  "# agy-native"
  "## Overview / When to Use"
  "## ⚠️ Critical Constraints"
  "## Workflow / Methodology"
  "## Output Specification"
  "## Quality Rubric"
  "## Examples"
  "## Troubleshooting"
  "## See Also / References"
)
last=0
for sec in "${spine[@]}"; do
  ln="$(grep -nF -m1 "$sec" "$SKILL" | cut -d: -f1 || true)"
  if [ -z "$ln" ]; then
    err "required section missing: $sec"
  elif [ "$ln" -lt "$last" ]; then
    err "section out of order: $sec (line $ln before previous $last)"
  else
    last="$ln"
  fi
done

# --- 4. Form-A line budget (<= 250) -------------------------------------------
lines="$(wc -l < "$SKILL" | tr -d ' ')"
if [ "$lines" -le 250 ]; then ok "line budget $lines/250 (Form A)"; else err "Form-A budget exceeded: $lines > 250"; fi

# --- 5. References resolve (one level deep) -----------------------------------
# Every SKILL-LOCAL references/<file>.md must exist on disk. Absolute paths
# (e.g. ~/.agents/...) are external and intentionally skipped.
while IFS= read -r relpath; do
  [ -z "$relpath" ] && continue
  if [ -f "$ROOT/$relpath" ]; then ok "ref resolves: $relpath"; else err "dead reference: $relpath"; fi
done < <(grep -oE '(^|[^/A-Za-z0-9_-])references/[A-Za-z0-9_-]+\.md' "$SKILL" \
           | grep -oE 'references/[A-Za-z0-9_-]+\.md' | sort -u)

# --- 6. Companion artifacts ---------------------------------------------------
[ -f "$SPEC" ] || err "skill.spec.json missing"
if [ -f "$SPEC" ] && command -v python3 >/dev/null 2>&1; then
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SPEC" \
    && ok "skill.spec.json is valid JSON" || err "skill.spec.json is not valid JSON"
fi

# --- 7. No banned worker-dispatch pattern presented as a directive -----------
# Core invariant (Rule 1): never `claude -p` for workers. Every mention in this
# skill must sit in a ban/negation context. Flag a 'claude -p' line ONLY when it
# carries no negation token (i.e. it would read as an instruction to use it).
bad=0
while IFS= read -r line; do
  printf '%s\n' "$line" | grep -qiE '\b(no|not|never|ban|banned|forbid|forbidden|avoid|do not|don.t|instead of|rather than|purge|NOT)\b' && continue
  bad=1
done < <(grep -iE 'claude (-p|--print)' "$SKILL" || true)
if [ "$bad" -eq 1 ]; then
  err "a 'claude -p' mention with no ban context appears in SKILL.md (workers must be agy --print / Codex / NTM panes)"
else
  ok "every 'claude -p' mention sits in a ban context"
fi

if [ "$fail" -eq 0 ]; then
  printf '\nPASS: agy-native SKILL.md meets the authoring standard.\n'
  exit 0
else
  printf '\nFAILED: fix the issues above.\n' >&2
  exit 1
fi
