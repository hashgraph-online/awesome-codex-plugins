#!/usr/bin/env bash
# docflow doctor — read-only repo scan. Prints a token-light setup diagnosis.
#
# Usage:
#   scripts/docflow-doctor.sh --target <repo> [--docs-root docs]
#
# Normal repo states always exit 0. Invalid CLI usage exits non-zero.

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

count_md() {
  dir="$1"
  [ -d "$dir" ] || { printf '0'; return; }
  find "$dir" -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' '
}

placeholder_count() {
  dir="$1"
  [ -d "$dir" ] || { printf '0'; return; }
  grep -RIlE '<(PROJECT|YYYY-MM-DD|Month YEAR|topic|item|description|title|name|scope|owner|status|hash|feature|module)>' "$dir" 2>/dev/null \
    | grep -vE '/references/|/NAMING\.md$' \
    | awk 'END { print NR }'
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

if ! cd "$TARGET" 2>/dev/null; then
  echo "Status"
  echo "- target: $TARGET"
  echo "- error: cannot enter target"
  echo
  echo "Recommended next command"
  echo "- Fix target path, then run: bash scripts/docflow-doctor.sh --target <repo>"
  exit 0
fi

TARGET="$PWD"
CFG="$TARGET/docflow.json"
ROOT="$(detect_docs_root)"
DR=""
[ -n "$ROOT" ] && DR="$TARGET/$ROOT"

docflow_config="$(exists_mark "$CFG")"
docs_root_exists="no"
[ -n "$DR" ] && [ -d "$DR" ] && docs_root_exists="yes"

readme_docs_link="no"
if [ -f "$TARGET/README.md" ] && grep -qiE 'docs/README\.md|documentation/README\.md|## Documentation' "$TARGET/README.md" 2>/dev/null; then
  readme_docs_link="yes"
fi

agents="$(exists_mark "$TARGET/AGENTS.md")"
gemini="$(exists_mark "$TARGET/GEMINI.md")"
cursor="$(exists_mark "$TARGET/.cursorrules")"
helper_map="$(exists_mark "$TARGET/scripts/docflow-map.sh")"
helper_links="$(exists_mark "$TARGET/scripts/check-links.sh")"
helper_validate="$(exists_mark "$TARGET/scripts/docflow-validate.sh")"

existing_docs="no"
if [ -n "$ROOT" ] || [ -f "$TARGET/README.md" ] || [ -f "$TARGET/CHANGELOG.md" ] || [ -d "$TARGET/adr" ] || [ -d "$TARGET/docs" ] || [ -d "$TARGET/documentation" ]; then
  existing_docs="yes"
fi

md_count="0"
placeholder_files="0"
changelog_months="0"
broken_links="not checked"
validation_status="not checked"
if [ "$docs_root_exists" = "yes" ]; then
  md_count="$(count_md "$DR")"
  placeholder_files="$(placeholder_count "$DR")"
  if [ -d "$DR/changelog" ]; then
    changelog_months="$(find "$DR/changelog" -type f -name '(*-[0-9][0-9]).md' 2>/dev/null | wc -l | tr -d ' ')"
  fi
  if [ -f "$SCRIPT_DIR/check-links.sh" ]; then
    link_output="$(bash "$SCRIPT_DIR/check-links.sh" "$DR" 2>/dev/null)"
    if [ -n "$link_output" ]; then
      broken_links="$(printf '%s\n' "$link_output" | wc -l | tr -d ' ')"
    else
      broken_links="0"
    fi
  fi
  if [ -f "$SCRIPT_DIR/docflow-validate.sh" ]; then
    validation_output="$(bash "$SCRIPT_DIR/docflow-validate.sh" --target "$TARGET" --docs-root "$ROOT" 2>/dev/null)"
    validation_exit="$?"
    validation_summary="$(printf '%s\n' "$validation_output" | grep -E '^- errors: |^- warnings: ' | paste -sd ' ' -)"
    if [ "$validation_exit" = "0" ]; then
      validation_status="pass ${validation_summary:-}"
    else
      validation_status="fail ${validation_summary:-}"
    fi
  fi
fi

if [ "$docflow_config" = "yes" ] && [ "$docs_root_exists" = "yes" ]; then
  recommendation="docflow-repair"
elif [ "$existing_docs" = "yes" ]; then
  recommendation="docflow-adopt"
else
  recommendation="docflow-init"
fi

echo "Status"
echo "- target: $TARGET"
echo "- docflow config: $docflow_config"
echo "- docs root: ${ROOT:-none} ($docs_root_exists)"
echo "- recommendation: $recommendation"
echo

echo "Detected"
echo "- markdown files in docs root: $md_count"
echo "- changelog month files: $changelog_months"
echo "- README documentation link: $readme_docs_link"
echo "- agent guidance: AGENTS=$agents GEMINI=$gemini Cursor=$cursor"
echo "- helper scripts: map=$helper_map links=$helper_links validate=$helper_validate"
echo "- validation: $validation_status"
echo

echo "Missing"
[ "$docflow_config" = "yes" ] || echo "- docflow.json"
[ "$docs_root_exists" = "yes" ] || echo "- docs root"
[ "$readme_docs_link" = "yes" ] || echo "- README Documentation link"
[ "$agents" = "yes" ] || echo "- AGENTS.md"
[ "$gemini" = "yes" ] || echo "- GEMINI.md"
[ "$cursor" = "yes" ] || echo "- .cursorrules"
[ "$helper_map" = "yes" ] || echo "- scripts/docflow-map.sh"
[ "$helper_links" = "yes" ] || echo "- scripts/check-links.sh"
[ "$helper_validate" = "yes" ] || echo "- scripts/docflow-validate.sh"
if [ "$docflow_config$docs_root_exists$readme_docs_link$agents$gemini$cursor$helper_map$helper_links$helper_validate" = "yesyesyesyesyesyesyesyesyes" ]; then
  echo "- none"
fi
echo

echo "Risks"
[ "$placeholder_files" = "0" ] || echo "- placeholder docs: $placeholder_files file(s)"
[ "$broken_links" = "0" ] || [ "$broken_links" = "not checked" ] || echo "- broken links: $broken_links"
[ "$broken_links" = "not checked" ] && echo "- links not checked"
if [ "$placeholder_files" = "0" ] && { [ "$broken_links" = "0" ] || [ "$broken_links" = "not checked" ]; }; then
  echo "- none detected"
fi
echo

echo "Recommended next command"
case "$recommendation" in
  docflow-init)
    echo "- /docflow:init"
    echo "- or: bash scripts/scaffold.sh --target \"$TARGET\" --docs-root docs --project \"$(basename "$TARGET")\""
    ;;
  docflow-adopt)
    echo "- /docflow:adopt"
    echo "- or: bash scripts/docflow-adopt.sh --target \"$TARGET\" --docs-root ${ROOT:-docs} --project \"$(basename "$TARGET")\""
    ;;
  *)
    echo "- /docflow:repair"
    echo "- or: bash scripts/docflow-repair.sh --target \"$TARGET\" --docs-root ${ROOT:-docs}"
    ;;
esac

exit 0
