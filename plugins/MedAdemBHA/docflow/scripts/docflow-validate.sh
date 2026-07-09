#!/usr/bin/env bash
# docflow validate — deterministic documentation readiness gate.
#
# Usage:
#   scripts/docflow-validate.sh --target <repo> [--docs-root docs]
#
# Exits non-zero when blocking documentation issues are found. Warnings are
# printed for legacy/adoption gaps that should be cleaned up but should not
# block an existing repo on the first validation pass.

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

errors=()
warnings=()

error() {
  errors+=("$1")
}

warn() {
  warnings+=("$1")
}

has_section() {
  file="$1"
  pattern="$2"
  grep -qiE "^##[[:space:]]+$pattern([[:space:]]*$|[[:space:]])" "$file" 2>/dev/null
}

has_h1() {
  grep -qE '^#[^#]' "$1" 2>/dev/null
}

has_docflow_metadata() {
  grep -qE '^<!--[[:space:]]*docflow:' "$1" 2>/dev/null
}

has_update_log() {
  file="$1"
  grep -qiE '^##[[:space:]]+(Update Log|Feature log|What Changed)' "$file" 2>/dev/null
}

is_known_template_placeholder_path() {
  rel="$1"
  case "$rel" in
    INDEX.md|README.md|product-spec/00-overview.md|product-spec/NN-topic.md|specs/'(mmm-yy)'-topic.md|plans/features/'(mmm-yy)'-feature-name.md|plans/hygiene/'(mmm-yy)'-topic.md|plans/upcoming/README.md|plans/upcoming/critical.md|plans/upcoming/now.md|plans/upcoming/next.md|plans/upcoming/later.md|decisions/README.md|decisions/0001-title.md|changelog/README.md|changelog/'(mmm-yy)'.md|reviews/README.md|reviews/bugs/open.md|reviews/bugs/fixed.md)
      return 0
      ;;
    *'<PROJECT>'*|*'<topic>'*|*'<feature>'*|*'<title>'*|*'NN-'*|*'(mmm-yy)'*)
      return 0
      ;;
  esac
  return 1
}

has_placeholder_tokens() {
  grep -qE '<(PROJECT|YYYY-MM-DD|Month YEAR|topic|item|description|title|name|scope|owner|status|hash|feature|module|code path|route or entrypoint|SPA / service / CLI|one-line highlight|one line|what changed|why it matters|module)>' "$1" 2>/dev/null
}

validate_category_path() {
  rel="$1"

  case "$rel" in
    README.md|NAMING.md|INDEX.md)
      return
      ;;
    product-spec/00-overview.md|product-spec/[0-9][0-9]-*.md|product-spec/NN-topic.md)
      return
      ;;
    specs/'(mmm-yy)'-topic.md|specs/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md)
      return
      ;;
    references/*.md)
      return
      ;;
    decisions/README.md|decisions/[0-9][0-9][0-9][0-9]-*.md)
      return
      ;;
    plans/upcoming/README.md|plans/upcoming/critical.md|plans/upcoming/now.md|plans/upcoming/next.md|plans/upcoming/later.md)
      return
      ;;
    plans/features/'(mmm-yy)'-feature-name.md|plans/features/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md)
      return
      ;;
    plans/hygiene/'(mmm-yy)'-topic.md|plans/hygiene/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md)
      return
      ;;
    reviews/README.md|reviews/bugs/open.md|reviews/bugs/fixed.md|reviews/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md|reviews/active/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md|reviews/archive/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md)
      return
      ;;
    changelog/README.md|changelog/'(mmm-yy)'.md|changelog/'('[a-z][a-z][a-z]-[0-9][0-9]')'.md)
      return
      ;;
  esac

  case "$rel" in
    product-spec/*|specs/*|decisions/*|plans/*|reviews/*|changelog/*)
      error "$rel: unsupported docflow category path"
      ;;
    *)
      warn "$rel: outside docflow taxonomy; treated as legacy doc"
      ;;
  esac
}

validate_required_sections() {
  rel="$1"
  file="$2"

  case "$rel" in
    product-spec/00-overview.md)
      has_section "$file" 'What' || error "$rel: missing required section ## What..."
      has_section "$file" 'Core [Mm]odules' || error "$rel: missing required section ## Core modules"
      ;;
    product-spec/[0-9][0-9]-*.md|product-spec/NN-topic.md)
      has_section "$file" 'Purpose' || error "$rel: missing required section ## Purpose"
      has_section "$file" 'Key [Aa]ctions' || error "$rel: missing required section ## Key actions"
      has_section "$file" 'Links' || error "$rel: missing required section ## Links"
      ;;
    specs/*.md)
      has_section "$file" 'Architecture' || error "$rel: missing required section ## Architecture"
      has_section "$file" 'Data' || error "$rel: missing required section ## Data"
      has_section "$file" 'API' || error "$rel: missing required section ## API"
      has_section "$file" 'Flow' || error "$rel: missing required section ## Flow"
      has_section "$file" 'Risks' || error "$rel: missing required section ## Risks"
      grep -qiE '^Related:' "$file" 2>/dev/null || error "$rel: missing Related block"
      ;;
    plans/features/*.md)
      has_section "$file" 'In flight' || error "$rel: missing required section ## In flight"
      has_section "$file" 'Feature log' || error "$rel: missing required section ## Feature log"
      has_section "$file" 'Next' || error "$rel: missing required section ## Next"
      ;;
  esac
}

validate_index_freshness() {
  dr="$1"
  rel_root="$2"
  index="$dr/INDEX.md"

  if [ ! -f "$index" ]; then
    error "INDEX.md: missing generated docs map"
    return
  fi

  tmp="$(mktemp)"
  {
    echo "# Docs map — $(basename "$dr")/"
    echo "<!-- AUTO-GENERATED by docflow-map.sh. Lines = path — purpose. Open the exact doc. -->"
    echo
    find "$dr" -type f -name '*.md' ! -name 'INDEX.md' | LC_ALL=C sort | while IFS= read -r f; do
      rel="${f#"$dr"/}"
      desc="$(grep -m1 -E '^#[^#]' "$f" 2>/dev/null | sed -E 's/^#+[[:space:]]*//; s/<!--.*-->//')"
      [ -z "$desc" ] && desc="—"
      printf '%s — %s\n' "$rel" "$desc"
    done
  } > "$tmp"

  if ! cmp -s "$tmp" "$index"; then
    error "$rel_root/INDEX.md: stale generated map; run scripts/docflow-map.sh"
  fi
  rm -f "$tmp"
}

validate_links() {
  dr="$1"
  if [ ! -f "$SCRIPT_DIR/check-links.sh" ]; then
    warn "links: check-links.sh not available"
    return
  fi

  link_output="$(bash "$SCRIPT_DIR/check-links.sh" "$dr" 2>/dev/null)"
  if [ -n "$link_output" ]; then
    while IFS= read -r line; do
      [ -n "$line" ] && error "links: $line"
    done <<EOF
$link_output
EOF
  fi
}

if ! cd "$TARGET" 2>/dev/null; then
  echo "Status"
  echo "- target: $TARGET"
  echo "- error: cannot enter target"
  exit 2
fi

TARGET="$PWD"
ROOT="$(detect_docs_root)"
if [ -z "$ROOT" ]; then
  echo "Status"
  echo "- target: $TARGET"
  echo "- docs root: none"
  echo
  echo "Errors"
  echo "- docs root not found"
  exit 1
fi

DR="$TARGET/$ROOT"
if [ ! -d "$DR" ]; then
  echo "Status"
  echo "- target: $TARGET"
  echo "- docs root: $ROOT (missing)"
  echo
  echo "Errors"
  echo "- docs root does not exist: $ROOT"
  exit 1
fi

validate_index_freshness "$DR" "$ROOT"
validate_links "$DR"

while IFS= read -r -d '' file; do
  rel="${file#"$DR"/}"

  validate_category_path "$rel"

  if ! has_h1 "$file"; then
    error "$rel: missing first-level H1"
  fi

  case "$rel" in
    INDEX.md|README.md|NAMING.md|*/README.md)
      ;;
    *)
      if ! has_docflow_metadata "$file"; then
        warn "$rel: missing docflow metadata comment"
      fi
      ;;
  esac

  case "$rel" in
    references/*.md|NAMING.md)
      ;;
    *)
      if has_placeholder_tokens "$file"; then
        if is_known_template_placeholder_path "$rel"; then
          warn "$rel: unfilled template placeholders remain"
        else
          error "$rel: placeholder tokens remain"
        fi
      fi
      ;;
  esac

  case "$rel" in
    product-spec/*.md|specs/*.md|decisions/[0-9][0-9][0-9][0-9]-*.md|plans/features/*.md|plans/hygiene/*.md|reviews/'('[a-z][a-z][a-z]-[0-9][0-9]')'-*.md|reviews/active/*.md|reviews/archive/*.md)
      if ! has_update_log "$file"; then
        warn "$rel: missing document update log"
      fi
      ;;
  esac

  validate_required_sections "$rel" "$file"
done < <(find "$DR" -type f -name '*.md' -print0)

echo "Status"
echo "- target: $TARGET"
echo "- docs root: $ROOT"
echo "- markdown files: $(find "$DR" -type f -name '*.md' | wc -l | tr -d ' ')"
echo "- errors: ${#errors[@]}"
echo "- warnings: ${#warnings[@]}"
echo

echo "Errors"
if [ "${#errors[@]}" -eq 0 ]; then
  echo "- none"
else
  for item in "${errors[@]}"; do
    echo "- $item"
  done
fi
echo

echo "Warnings"
if [ "${#warnings[@]}" -eq 0 ]; then
  echo "- none"
else
  for item in "${warnings[@]}"; do
    echo "- $item"
  done
fi

[ "${#errors[@]}" -eq 0 ] || exit 1
exit 0
