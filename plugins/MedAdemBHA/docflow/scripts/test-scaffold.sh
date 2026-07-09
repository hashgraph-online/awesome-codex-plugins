#!/usr/bin/env bash
# Smoke tests for the docflow scaffold and context hook.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

checksum_tree() {
  find "$1" -type f | LC_ALL=C sort | while IFS= read -r file; do
    cksum "$file"
    printf ' %s\n' "${file#"$1"/}"
  done
}

for script in "$ROOT"/scripts/*.sh "$ROOT"/hooks/*.sh; do
  bash -n "$script"
done

target="$TMP/repo"
mkdir -p "$target"

cat > "$target/AGENTS.md" <<'EOF'
# Existing Agent Guide
<DOCS_ROOT>
<PROJECT>
EOF
cp "$target/AGENTS.md" "$TMP/expected-agents.md"

project='Fish & Chips / "Docs"'
bash "$ROOT/scripts/scaffold.sh" \
  --target "$target" \
  --docs-root docs \
  --project "$project" >/dev/null

[ -f "$target/docflow.json" ] || fail "docflow.json was not created"
[ -f "$target/docs/INDEX.md" ] || fail "docs/INDEX.md was not created"
[ -f "$target/docs/product-spec/00-overview.md" ] || fail "product overview was not created"

cmp "$TMP/expected-agents.md" "$target/AGENTS.md" >/dev/null \
  || fail "existing AGENTS.md was modified"

grep -F "$project" "$target/docs/README.md" >/dev/null \
  || fail "project name was not substituted in docs README"
grep -F "$project" "$target/docs/product-spec/00-overview.md" >/dev/null \
  || fail "project name was not substituted in product overview"

python3 -m json.tool "$target/docflow.json" >/dev/null \
  || fail "docflow.json is invalid JSON"

bash "$ROOT/scripts/check-links.sh" "$target/docs" \
  || fail "fresh scaffold has broken non-placeholder links"

# helper scripts the docs reference must be installed in the target repo
[ -x "$target/scripts/check-links.sh" ] || fail "check-links.sh was not scaffolded"
[ -x "$target/scripts/docflow-map.sh" ] || fail "docflow-map.sh was not scaffolded"
[ -x "$target/scripts/docflow-check.sh" ] || fail "docflow-check.sh was not scaffolded"
[ -x "$target/scripts/docflow-doctor.sh" ] || fail "docflow-doctor.sh was not scaffolded"
[ -x "$target/scripts/docflow-repair.sh" ] || fail "docflow-repair.sh was not scaffolded"
[ -x "$target/scripts/docflow-validate.sh" ] || fail "docflow-validate.sh was not scaffolded"
( cd "$target" && bash scripts/check-links.sh docs ) \
  || fail "scaffolded check-links.sh did not run from target repo root"
( cd "$target" && bash scripts/docflow-validate.sh --target . >/dev/null ) \
  || fail "scaffolded docflow-validate.sh did not run from target repo root"
( cd "$target" && bash scripts/docflow-check.sh --target . >/dev/null ) \
  || fail "scaffolded docflow-check.sh did not run from target repo root"

before="$(checksum_tree "$target")"
bash "$ROOT/scripts/scaffold.sh" \
  --target "$target" \
  --docs-root docs \
  --project "$project" >/dev/null
after="$(checksum_tree "$target")"

[ "$before" = "$after" ] || fail "second scaffold run changed files"

context="$(CLAUDE_PROJECT_DIR="$target" bash "$ROOT/hooks/docflow-context.sh")"
printf '%s\n' "$context" | grep -F 'docs map' >/dev/null \
  || fail "context hook did not print docs map"
if printf '%s\n' "$context" | grep -F -- '--- newest changelog' >/dev/null; then
  fail "context hook printed template changelog as recent history"
fi

doctor="$(bash "$ROOT/scripts/docflow-doctor.sh" --target "$target")"
printf '%s\n' "$doctor" | grep -F 'recommendation: docflow-repair' >/dev/null \
  || fail "doctor did not recognize scaffolded repo"

echo "PASS: scaffold smoke tests"
