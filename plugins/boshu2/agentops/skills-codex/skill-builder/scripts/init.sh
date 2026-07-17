#!/usr/bin/env bash
# Create one metadata-complete canonical skill source package.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SKILL_BUILDER_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

usage() {
  echo "usage: init.sh --scratch|--template|--external <slug> [--like <slug>|--from <path>]" >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
mode="$1"
slug="$2"
shift 2

[[ "$slug" =~ ^[a-z][a-z0-9-]*$ ]] || {
  echo "init.sh: slug must be lowercase-hyphen: $slug" >&2
  exit 2
}

source_hint=""
case "$mode" in
  --scratch)
    [[ $# -eq 0 ]] || usage
    ;;
  --template)
    [[ $# -eq 2 && "$1" == "--like" ]] || usage
    source_hint="$2"
    [[ -f "$REPO_ROOT/skills/$source_hint/SKILL.md" ]] || {
      echo "init.sh: unknown template skill: $source_hint" >&2
      exit 2
    }
    ;;
  --external)
    [[ $# -eq 2 && "$1" == "--from" ]] || usage
    source_hint="$2"
    [[ -f "$source_hint" ]] || {
      echo "init.sh: external source does not exist: $source_hint" >&2
      exit 2
    }
    ;;
  *) usage ;;
esac

target="$REPO_ROOT/skills/$slug"
[[ ! -e "$target" ]] || {
  echo "init.sh: target already exists: $target" >&2
  exit 1
}

tier="${SKILL_TIER:-execution}"
dependencies="${SKILL_DEPENDENCIES:-[]}"
capabilities="${SKILL_CAPABILITIES:-[\"${slug//-/_}\"]}"
effects="${SKILL_EFFECTS:-[]}"

python3 - "$dependencies" "$capabilities" "$effects" <<'PY'
import json
import sys
for value in sys.argv[1:]:
    parsed = json.loads(value)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise SystemExit("skill metadata lists must be JSON arrays of strings")
PY

mkdir -p "$target/scripts"

# The <!-- craft:... --> stubs mirror the 12 craft elements enumerated in
# references/skill-template.md section 7. The craft scorer strips HTML
# comments, so a fresh scaffold scores low until the author replaces stubs
# with real prose.
cat >"$target/SKILL.md" <<EOF
---
name: $slug
description: 'TODO: state the behavior and concrete trigger phrases for $slug.'
practices: []
skill_api_version: 1
hexagonal_role: supporting
consumes: []
produces: []
context_rel: []
user-invocable: true
metadata:
  tier: $tier
  dependencies: $dependencies
  capabilities: $capabilities
  effects: $effects
  canonical_status: canonical
  disposition: keep_specialist
  stability: experimental
---

# /$slug

TODO: Explain the bounded behavior this skill provides.

<!-- craft:trigger-rich-description Put Triggers:/Use when phrases callers actually say in the frontmatter description. -->
<!-- craft:causal-insight-line State the one causal insight (Insight:/Why:/a-because-clause) that makes this skill work. -->
<!-- craft:named-failure-mode Name the concrete failure mode this skill exists to prevent. -->
<!-- craft:router-shape Map trigger phrases to modes/entry points in a routing table when the skill has modes. -->

## Inputs

TODO: List required inputs and explicit non-goals.

<!-- craft:negative-space State what this skill is NOT for (non-goals / not-for / do-not-use-when). -->

## Procedure

1. TODO: Perform one bounded operation.
2. TODO: Check the output against the stated contract.
3. Report the result and stop.

<!-- craft:named-loop-stop-condition If any step iterates, name the loop and give a checkable stop condition in the same section. -->
<!-- craft:quantified-rules Quantify at least one rule with a number and unit. -->
<!-- craft:anti-pattern-with-corrective Pair each anti-pattern with its corrective in the same section. -->
<!-- craft:frozen-prompts Provide any reusable prompt as a fenced block marked copy-paste-only. -->
<!-- craft:runnable-commands Include at least one fenced block with runnable commands. -->

## Output

TODO: Define the artifact or response shape and how a caller checks it.

<!-- craft:measurable-done Give a machine-checkable done signal (done-when phrase, exit 0, validator command). -->

## Checks

- The output satisfies the declared behavior.
- No undeclared side effect occurred.

<!-- craft:provenance-citation Cite at least one resolvable repo path or .agents/ao verdict/intent digest grounding this skill. -->

## Failure behavior

Report the concrete failure and stop. The caller owns any revision.
EOF

cat >"$target/scripts/validate.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
exec bash "$REPO_ROOT/skills/skill-builder/scripts/heal.sh" --check --strict "$SKILL_DIR"
EOF
chmod +x "$target/scripts/validate.sh"

mkdir -p "$REPO_ROOT/.agents/audits"
report="$REPO_ROOT/.agents/audits/${slug}-build.json"
python3 - "$report" "$mode" "$slug" "$source_hint" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
mode = {"--scratch": "from-scratch", "--template": "from-template", "--external": "absorb-external"}[sys.argv[2]]
payload = {
    "mode": mode,
    "skill_name": sys.argv[3],
    "files_created": [f"skills/{sys.argv[3]}/SKILL.md", f"skills/{sys.argv[3]}/scripts/validate.sh"],
    "structure_check_pass": False,
}
if sys.argv[4]:
    payload["source_hint"] = sys.argv[4]
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

echo "init.sh: created $target"
