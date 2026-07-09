#!/usr/bin/env bash
# init.sh — materialize a new skill from the canonical template
# Invoked by build.sh; not typically called directly.
#
# Usage:
#   init.sh --interactive <skill-name>
#   init.sh --like-flag-mode <skill-name> --like <source-skill>
#   init.sh --absorb <skill-name> --from <path-to-external-SKILL.md>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# SKILL_BUILDER_REPO_ROOT overrides root discovery for fixture-driven tests
# (tests/integration/test_skill_builder.bats scaffolds into a scratch repo copy
# so no in-repo surface — skills/, the dispositions ledger, the codex catalog —
# is ever mutated by a test run). Mirrors HEAL_REPO_ROOT in heal.sh. Production
# derives the root from the script location.
REPO_ROOT="${SKILL_BUILDER_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
TEMPLATE_REF="$REPO_ROOT/skills/skill-builder/references/skill-template.md"

[[ -f "$TEMPLATE_REF" ]] || { echo "init.sh: missing $TEMPLATE_REF" >&2; exit 1; }

MODE="${1:?usage: init.sh --interactive|--like-flag-mode|--absorb <name> [opts]}"
shift

SKILL_NAME="${1:?missing <skill-name>}"
shift

# Validate slug
[[ "$SKILL_NAME" =~ ^[a-z][a-z0-9-]*$ ]] || {
  echo "init.sh: skill name '$SKILL_NAME' must be lowercase-hyphen (e.g. my-skill)" >&2
  exit 1
}

NEW_DIR="$REPO_ROOT/skills/$SKILL_NAME"
NEW_SKILL_MD="$NEW_DIR/SKILL.md"
[[ -e "$NEW_DIR" ]] && { echo "init.sh: $NEW_DIR already exists; aborting" >&2; exit 1; }

mkdir -p "$NEW_DIR/scripts"

# --- Per-mode population --------------------------------------------------
case "$MODE" in
  --interactive)
    # Minimal non-blocking defaults; skip prompts in CI by reading env vars
    TIER="${SKILL_TIER:-execution}"
    DEPS="${SKILL_DEPS:-[]}"
    INTENT_MODE="${SKILL_INTENT_MODE:-task}"
    ;;

  --like-flag-mode)
    LIKE_FLAG="${1:-}"; SOURCE_SKILL="${2:-}"
    [[ "$LIKE_FLAG" == "--like" && -n "$SOURCE_SKILL" ]] || {
      echo "init.sh --like-flag-mode requires '--like <source-skill>'" >&2
      exit 1
    }
    SOURCE_DIR="$REPO_ROOT/skills/$SOURCE_SKILL"
    [[ -f "$SOURCE_DIR/SKILL.md" ]] || {
      echo "init.sh: source skill $SOURCE_DIR/SKILL.md not found" >&2
      exit 1
    }
    # Extract frontmatter values from source for sane defaults
    TIER="$(awk '/^---$/{n++;next} n==1 && /^[ ]+tier:/{print $2; exit}' "$SOURCE_DIR/SKILL.md")"
    TIER="${TIER:-execution}"
    DEPS="[]"
    INTENT_MODE="$(awk '/^---$/{n++;next} n==1 && /^[ ]+mode:/{print $2; exit}' "$SOURCE_DIR/SKILL.md")"
    INTENT_MODE="${INTENT_MODE:-task}"
    ;;

  --absorb)
    FROM_FLAG="${1:-}"; SOURCE_PATH="${2:-}"
    [[ "$FROM_FLAG" == "--from" && -n "$SOURCE_PATH" ]] || {
      echo "init.sh --absorb requires '--from <path-to-external-SKILL.md>'" >&2
      exit 1
    }
    [[ -f "$SOURCE_PATH" ]] || { echo "init.sh: external SKILL.md not found at $SOURCE_PATH" >&2; exit 1; }
    TIER="${SKILL_TIER:-execution}"
    DEPS="[]"
    INTENT_MODE="task"
    ;;

  *)
    echo "init.sh: unknown mode '$MODE'" >&2
    exit 2
    ;;
esac

# --- Render frontmatter + skeleton ---------------------------------------
cat > "$NEW_SKILL_MD" <<EOF
---
name: $SKILL_NAME
description: |
  <one-line: verb + object + domain>

  **Use when:**
  - <Trigger 1>
  - <Trigger 2>

  **Triggers:** "<trigger phrase 1>", "<trigger phrase 2>"

  **Not ideal for:**
  - <Anti-scenario 1>
skill_api_version: 1
context:
  window: fork
  intent:
    mode: $INTENT_MODE
  sections:
    exclude: [HISTORY]
  intel_scope: topic
metadata:
  tier: $TIER
  dependencies: $DEPS
  stability: experimental
output_contract: "TODO: path to schema or output description"
---

# /$SKILL_NAME — <Title matching slug>

<1-2 sentence purpose paragraph>

## Overview

<What this skill does, why it matters, and when to use it>

## ⚠️ Critical Constraints

- **Rule 1:** <constraint>. **Why:** <rationale>

## Workflow

### Phase 1: <name>

<instructions>

**Checkpoint:** <what to confirm before next phase>

## Output Specification

**Format:** <markdown | json | excel | etc.>
**Filename:** <naming convention>
**Structure:** <key sections / fields>

## Quality Rubric

- [ ] <Check 1>
- [ ] <Check 2>
- [ ] <Check 3>

## Examples

\`\`\`bash
/$SKILL_NAME <example-args>
\`\`\`

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|

## See Also

- [heal-skill](../heal-skill/SKILL.md) — deep audit (audit.sh) this skill before declaring stable
EOF

# --- Mode-specific content injection -------------------------------------
if [[ "$MODE" == "--absorb" ]]; then
  # Append a "Source" reference section pointing at the absorbed external doc
  cat >> "$NEW_SKILL_MD" <<EOF

## References

- Source absorbed from: \`$SOURCE_PATH\`
EOF
fi

# --- Companion files -----------------------------------------------------
cat > "$NEW_DIR/scripts/validate.sh" <<'EOF'
#!/usr/bin/env bash
# validate.sh — minimal self-validation
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
exec bash "$REPO_ROOT/skills/heal-skill/scripts/audit.sh" "$SKILL_DIR"
EOF
chmod +x "$NEW_DIR/scripts/validate.sh"
chmod +x "$NEW_DIR" 2>/dev/null || true

# --- Codex parity (slim frontmatter + prompt.md) -------------------------
CODEX_DIR="$REPO_ROOT/skills-codex/$SKILL_NAME"
mkdir -p "$CODEX_DIR"

# Try /converter if present, otherwise hand-build
CONVERTER="$REPO_ROOT/skills/converter/scripts/convert.sh"
if [[ -x "$CONVERTER" ]]; then
  bash "$CONVERTER" "skills/$SKILL_NAME" codex 2>/dev/null || {
    echo "init.sh: converter failed; falling back to hand-built codex artifacts" >&2
  }
fi

# Hand-build codex SKILL.md (slim frontmatter — NO skill_api_version per learning 2026-05-03)
if [[ ! -f "$CODEX_DIR/SKILL.md" ]]; then
  cat > "$CODEX_DIR/SKILL.md" <<EOF
---
name: $SKILL_NAME
description: <copy from skills/$SKILL_NAME/SKILL.md description>
---

# /$SKILL_NAME

See \`skills/$SKILL_NAME/SKILL.md\` for the canonical specification.

## Codex Execution Profile

See \`prompt.md\` in this directory.
EOF
fi

# Always trim skill_api_version from codex SKILL.md if present
if grep -q "^skill_api_version:" "$CODEX_DIR/SKILL.md"; then
  sed -i.bak '/^skill_api_version:/d' "$CODEX_DIR/SKILL.md" && rm -f "$CODEX_DIR/SKILL.md.bak"
fi

# Hand-build prompt.md
if [[ ! -f "$CODEX_DIR/prompt.md" ]]; then
  cat > "$CODEX_DIR/prompt.md" <<EOF
# Execution Profile: $SKILL_NAME

You are running /$SKILL_NAME.

See \`SKILL.md\` in this directory for full specification, OR
read \`skills/$SKILL_NAME/SKILL.md\` in the host repo for the canonical document.

Workflow:
1. Read the user's request
2. Apply the skill's Workflow section
3. Produce output per the Output Specification
4. Self-check against the Quality Rubric
EOF
fi

# --- Build report --------------------------------------------------------
BUILD_REPORT="$REPO_ROOT/.agents/audits/${SKILL_NAME}-build.json"
mkdir -p "$(dirname "$BUILD_REPORT")"
cat > "$BUILD_REPORT" <<EOF
{
  "mode": "${MODE#--}",
  "skill_name": "$SKILL_NAME",
  "files_created": [
    "skills/$SKILL_NAME/SKILL.md",
    "skills/$SKILL_NAME/scripts/validate.sh",
    "skills-codex/$SKILL_NAME/SKILL.md",
    "skills-codex/$SKILL_NAME/prompt.md"
  ],
  "audit_pass": null,
  "warnings": ["v1 skeleton — manual content fill required for description, constraints, workflow"]
}
EOF

# --- New-skill plumbing (ag-cw2y): make the scaffold one-shot-green ----------
# The local/CI gates that silently tripped /burndown #600 are pre-empted here:
# 1. Dispositions row — else heal.sh Check 12 (MISSING_DISPOSITION).
if [[ -f "$REPO_ROOT/scripts/append-skill-disposition.sh" ]]; then
  bash "$REPO_ROOT/scripts/append-skill-disposition.sh" "$SKILL_NAME" "$REPO_ROOT" \
    || echo "init.sh: WARN could not append dispositions row — add one manually" >&2
fi
# 2. Narrative skill counts — --fix-counts bumps the "N checked-in skills" tokens
#    in the domain-map + bdd Gherkin so the new skill doesn't trip registry-drift.
if [[ -x "$REPO_ROOT/scripts/check-registry-drift.sh" ]]; then
  bash "$REPO_ROOT/scripts/check-registry-drift.sh" --fix-counts >/dev/null 2>&1 \
    || echo "init.sh: WARN registry-drift --fix-counts could not run — bump counts manually" >&2
fi
# 3. Codex override catalog entry — else validate-codex-override-coverage fails
#    ("source skill missing from Codex catalog"). Default parity_only (derived).
if [[ -f "$REPO_ROOT/scripts/append-codex-override-entry.sh" ]]; then
  bash "$REPO_ROOT/scripts/append-codex-override-entry.sh" "$SKILL_NAME" "$REPO_ROOT" \
    || echo "init.sh: WARN could not add codex override catalog entry — add one manually" >&2
fi
# 4. registry.json SKU catalog — else contracts-sync + correctness(ubuntu) BOTH
#    fail ("registry.json is stale" / "SKU_CATALOG: DRIFT"). This is the 5th
#    one-shot-green surface ag-cw2y missed; it cost /burndown #600 a 2nd
#    fix-and-repush (ag-ekyq). MUST run last — it scans the whole skills/ tree,
#    so the new skeleton must already exist on disk.
if [[ -f "$REPO_ROOT/scripts/generate-registry.sh" ]]; then
  bash "$REPO_ROOT/scripts/generate-registry.sh" >/dev/null 2>&1 \
    || echo "init.sh: WARN could not regen registry.json — run scripts/generate-registry.sh manually" >&2
fi

echo "init.sh: created skill skeleton at $NEW_DIR"
echo "init.sh: codex parity at $CODEX_DIR"
echo "init.sh: build report at $BUILD_REPORT"
echo "init.sh: dispositions row + narrative counts scaffolded (refine the placeholder row)"
