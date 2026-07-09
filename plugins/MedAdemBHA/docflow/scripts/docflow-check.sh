#!/usr/bin/env bash
# docflow check — friendly one-screen readiness summary.
#
# Usage:
#   scripts/docflow-check.sh --target <repo> [--docs-root docs]
#
# Exits 0 only when the repo is ready. Setup, adoption, repair, and validation
# blockers exit 1 so this command can be used as a simple completion gate.

set -u

TARGET="$PWD"
DOCS_ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      [ $# -ge 2 ] || { echo "missing value for --target" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --docs-root)
      [ $# -ge 2 ] || { echo "missing value for --docs-root" >&2; exit 2; }
      DOCS_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

json_val() {
  key="$1"
  cfg="$2"
  grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$cfg" 2>/dev/null \
    | head -1 | sed -E "s/.*:[[:space:]]*\"([^\"]*)\".*/\1/"
}

exists_mark() {
  [ -e "$1" ] && printf 'yes' || printf 'no'
}

detect_docs_root() {
  if [ -n "$DOCS_ROOT" ]; then
    printf '%s' "$DOCS_ROOT"
    return
  fi

  cfg="$TARGET/docflow.json"
  if [ -f "$cfg" ]; then
    configured="$(json_val docsRoot "$cfg")"
    if [ -n "$configured" ]; then
      printf '%s' "$configured"
      return
    fi
  fi

  for cand in docs documentation .docs doc; do
    if [ -d "$TARGET/$cand" ]; then
      printf '%s' "$cand"
      return
    fi
  done
}

first_h1() {
  file="$1"
  grep -m1 -E '^#[^#]' "$file" 2>/dev/null | sed -E 's/^#+[[:space:]]*//'
}

if ! cd "$TARGET" 2>/dev/null; then
  echo "DocFlow Check"
  echo "- status: Blocked"
  echo "- target: $TARGET"
  echo "- reason: cannot enter target"
  echo "- next: fix target path, then run docflow-check again"
  exit 2
fi

TARGET="$PWD"
CFG="$TARGET/docflow.json"
ROOT="$(detect_docs_root)"
DR=""
[ -n "$ROOT" ] && DR="$TARGET/$ROOT"

docflow_config="$(exists_mark "$CFG")"
docs_root_exists="no"
[ -n "$DR" ] && [ -d "$DR" ] && docs_root_exists="yes"

existing_docs="no"
if [ -n "$ROOT" ] || [ -f "$TARGET/README.md" ] || [ -f "$TARGET/CHANGELOG.md" ] || [ -d "$TARGET/adr" ] || [ -d "$TARGET/docs" ] || [ -d "$TARGET/documentation" ]; then
  existing_docs="yes"
fi

project="$(basename "$TARGET")"
if [ -f "$TARGET/README.md" ]; then
  title="$(first_h1 "$TARGET/README.md")"
  [ -n "$title" ] && project="$title"
fi

readme_docs_link="no"
if [ -f "$TARGET/README.md" ] && grep -qiE 'docs/README\.md|documentation/README\.md|## Documentation' "$TARGET/README.md" 2>/dev/null; then
  readme_docs_link="yes"
fi

missing=()
notes=()
[ "$docflow_config" = "yes" ] || missing+=("docflow.json")
[ "$docs_root_exists" = "yes" ] || missing+=("docs root")
[ "$readme_docs_link" = "yes" ] || notes+=("README Documentation link is optional but recommended")
[ -e "$TARGET/AGENTS.md" ] || missing+=("AGENTS.md")
[ -e "$TARGET/GEMINI.md" ] || missing+=("GEMINI.md")
[ -e "$TARGET/.cursorrules" ] || missing+=(".cursorrules")
[ -e "$TARGET/scripts/docflow-map.sh" ] || missing+=("scripts/docflow-map.sh")
[ -e "$TARGET/scripts/check-links.sh" ] || missing+=("scripts/check-links.sh")
[ -e "$TARGET/scripts/docflow-validate.sh" ] || missing+=("scripts/docflow-validate.sh")
[ -e "$TARGET/scripts/docflow-check.sh" ] || missing+=("scripts/docflow-check.sh")

validation_output=""
validation_exit=1
errors="not checked"
warnings="not checked"
if [ "$docs_root_exists" = "yes" ] && [ -f "$SCRIPT_DIR/docflow-validate.sh" ]; then
  validation_output="$(bash "$SCRIPT_DIR/docflow-validate.sh" --target "$TARGET" --docs-root "$ROOT" 2>/dev/null)"
  validation_exit="$?"
  errors="$(printf '%s\n' "$validation_output" | sed -n 's/^- errors: //p' | head -1)"
  warnings="$(printf '%s\n' "$validation_output" | sed -n 's/^- warnings: //p' | head -1)"
  [ -n "$errors" ] || errors="unknown"
  [ -n "$warnings" ] || warnings="unknown"
fi

status="Ready"
next="No action needed."
details="Docs are installed and validation is clean."
exit_code=0

if [ "$docflow_config" != "yes" ] && [ "$existing_docs" != "yes" ]; then
  status="Needs setup"
  next="/docflow:init"
  details="No meaningful docs or docflow config detected."
  exit_code=1
elif [ "$docflow_config" != "yes" ] || [ "$docs_root_exists" != "yes" ]; then
  status="Needs adoption"
  next="/docflow:adopt"
  details="Existing docs need docflow infrastructure."
  exit_code=1
elif [ "${#missing[@]}" -gt 0 ]; then
  status="Needs repair"
  next="/docflow:repair"
  details="Docflow exists, but generated helpers or guidance are missing."
  exit_code=1
elif [ "$validation_exit" != "0" ]; then
  status="Blocked"
  next="/docflow:validate"
  details="Validation found blocking documentation errors."
  exit_code=1
fi

echo "DocFlow Check"
echo "- status: $status"
echo "- target: $TARGET"
echo "- docs root: ${ROOT:-none} ($docs_root_exists)"
echo "- validation: errors=$errors warnings=$warnings"
echo "- reason: $details"
echo "- next: $next"

if [ "${#missing[@]}" -gt 0 ]; then
  echo
  echo "Missing"
  for item in "${missing[@]}"; do
    echo "- $item"
  done
fi

if [ "${#notes[@]}" -gt 0 ]; then
  echo
  echo "Notes"
  for item in "${notes[@]}"; do
    echo "- $item"
  done
fi

if [ "$validation_exit" != "0" ] && [ -n "$validation_output" ]; then
  echo
  echo "Top validation errors"
  printf '%s\n' "$validation_output" \
    | awk '
      /^Errors$/ { in_errors=1; next }
      /^Warnings$/ { in_errors=0 }
      in_errors && /^- / && $0 != "- none" { print; count++ }
      count == 6 { exit }
    '
fi

case "$status" in
  "Needs setup")
    echo
    echo "Equivalent script"
    echo "- bash scripts/scaffold.sh --target \"$TARGET\" --docs-root docs --project \"$project\""
    ;;
  "Needs adoption")
    echo
    echo "Equivalent script"
    echo "- bash scripts/docflow-adopt.sh --target \"$TARGET\" --docs-root ${ROOT:-docs} --project \"$project\""
    ;;
  "Needs repair")
    echo
    echo "Equivalent script"
    echo "- bash scripts/docflow-repair.sh --target \"$TARGET\" --docs-root ${ROOT:-docs}"
    ;;
  "Blocked")
    echo
    echo "Equivalent script"
    echo "- bash scripts/docflow-validate.sh --target \"$TARGET\" --docs-root ${ROOT:-docs}"
    ;;
esac

exit "$exit_code"
