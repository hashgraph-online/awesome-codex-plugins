#!/usr/bin/env bash
set -Eeuo pipefail

selftest_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$selftest_dir/../.." && pwd)"
source_skill="$skill_dir/SKILL.md"
source_metadata="$skill_dir/agents/openai.yaml"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT

check_skill() {
  local candidate="$1"
  python3 - "$candidate/SKILL.md" "$candidate/agents/openai.yaml" <<'PY'
import pathlib
import re
import sys
skill_text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.match(r"^---\n(.*?)\n---", skill_text, re.DOTALL)
if not match:
    raise SystemExit("frontmatter delimiters are invalid")
frontmatter = match.group(1)
metadata = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
if not re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE):
    raise SystemExit("frontmatter name is invalid")
if not re.search(r"^description:\s*.*MANUAL-ONLY", frontmatter, re.MULTILINE):
    raise SystemExit("frontmatter description lacks MANUAL-ONLY")
if not all(re.search(rf"^  {key}:\s*\S+", metadata, re.MULTILINE) for key in ("display_name", "short_description", "default_prompt")):
    raise SystemExit("metadata interface is invalid")
if not re.search(r"^  allow_implicit_invocation:\s*false\s*$", metadata, re.MULTILINE):
    raise SystemExit("metadata must set allow_implicit_invocation to false")
PY
}

expect_rejection() {
  local label="$1"
  shift
  if "$@"; then
    printf 'FAIL: %s was accepted\n' "$label" >&2
    exit 1
  fi
  printf 'PASS: %s rejected\n' "$label"
}

[[ -f "$source_skill" ]] || { printf 'missing source skill: %s\n' "$source_skill" >&2; exit 1; }
[[ -f "$source_metadata" ]] || { printf 'missing source metadata: %s\n' "$source_metadata" >&2; exit 1; }
valid_copy="$temporary/valid"
/bin/cp -R "$skill_dir" "$valid_copy"
check_skill "$valid_copy"
printf 'PASS: source skill is MANUAL-ONLY with valid frontmatter and explicit implicit-invocation denial\n'

missing_marker="$temporary/missing-manual-marker"
/bin/cp -R "$valid_copy" "$missing_marker"
python3 - "$missing_marker/SKILL.md" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(path.read_text(encoding="utf-8").replace("MANUAL-ONLY:", "", 1), encoding="utf-8")
PY
expect_rejection "temporary copy without MANUAL-ONLY" check_skill "$missing_marker"

implicit_enabled="$temporary/implicit-invocation-enabled"
/bin/cp -R "$valid_copy" "$implicit_enabled"
python3 - "$implicit_enabled/agents/openai.yaml" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(
    path.read_text(encoding="utf-8").replace(
        "allow_implicit_invocation: false", "allow_implicit_invocation: true", 1
    ),
    encoding="utf-8",
)
PY
expect_rejection "temporary copy with implicit invocation enabled" check_skill "$implicit_enabled"

printf 'verify-manual-only passed\n'
