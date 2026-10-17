#!/usr/bin/env bash
# repo_fixture_test.sh — Golden fixture self-test for cc-sdd repo-mode analysis.
#
# Pins to cc-sdd v2.1.0 (commit 6e972c064ac4723bc8ad0181871d07e199af6a9f) and
# runs repo-mode analysis, then compares key contracts against stored fixtures.
#
# Usage:
#   bash skills/reverse-engineer/scripts/repo_fixture_test.sh
#
# Exit codes:
#   0  All fixture contracts match.
#   1  One or more contracts drifted (diff output printed to stderr).
#   2  Prerequisite missing or unexpected error.
#
# Requirements:
#   - Network access (to clone github.com/gotalab/cc-sdd at v2.1.0)
#   - git, python3

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# ROOT = git repo root (trunks/), two levels up from the skill dir
# (reverse-engineer -> skills -> trunks)
ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
FIXTURES_DIR="$SKILL_DIR/fixtures/cc-sdd-v2.1.0"

PINNED_REF="v2.1.0"
PINNED_COMMIT="6e972c064ac4723bc8ad0181871d07e199af6a9f"
UPSTREAM_REPO="https://github.com/gotalab/cc-sdd.git"

TMP="$ROOT/.tmp/repo-fixture-test-cc-sdd"
OUT="$TMP/out"
CLONE_DIR="$TMP/local-clone"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
FAILURES=0

_fail() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

_ok() {
  echo "OK: $1"
}

_check_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command not found: $1" >&2
    exit 2
  fi
}

# Normalize a YAML/text file: strip generated_at/clone_date/analysis_root lines
# (which are volatile) so diff is stable across run dates.
_normalize() {
  local f="$1"
  grep -v '^generated_at:' "$f" \
    | grep -v '^  "clone_date":' \
    | grep -v '^  "analysis_root":' \
    | grep -v '^  "node_package_dir":' \
    | grep -v '^analysis_root:' \
    | sed 's|^- Date: .*|- Date: <DATE>|' \
    | sed 's|^- Analysis root: .*|- Analysis root: <ROOT>|' \
    | sed "s|$(echo "$ROOT" | sed 's|/|\\/|g')|<ROOT>|g"
}

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
_check_cmd git
_check_cmd python3

if [ ! -d "$FIXTURES_DIR" ]; then
  echo "error: fixtures directory not found: $FIXTURES_DIR" >&2
  echo "       Run with UPDATE_FIXTURES=1 to create it, or check the skill directory." >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# UPDATE_FIXTURES mode: regenerate and overwrite golden fixtures.
# ---------------------------------------------------------------------------
if [ "${UPDATE_FIXTURES:-0}" = "1" ]; then
  echo "=== UPDATE_FIXTURES=1: regenerating golden fixtures ==="
  rm -rf "$TMP"
  mkdir -p "$OUT" "$CLONE_DIR" "$FIXTURES_DIR"

  python3 "$SKILL_DIR/scripts/reverse_engineer.py" cc-sdd \
    --mode=repo \
    --upstream-repo="$UPSTREAM_REPO" \
    --upstream-ref="$PINNED_REF" \
    --local-clone-dir="$CLONE_DIR" \
    --output-dir="$OUT"

  # Verify resolved commit matches pin.
  ACTUAL_COMMIT="$(python3 -c "import json; d=json.load(open('$OUT/clone-metadata.json')); print(d['resolved_commit'])")"
  if [ "$ACTUAL_COMMIT" != "$PINNED_COMMIT" ]; then
    echo "WARNING: resolved commit $ACTUAL_COMMIT does not match expected pin $PINNED_COMMIT" >&2
    echo "         Update PINNED_COMMIT in this script if the tag was force-pushed." >&2
  fi

  # docs-features.txt — stable (content from repo tree).
  cp "$OUT/docs-features.txt" "$FIXTURES_DIR/docs-features.txt"

  # feature-registry.yaml — strip generated_at before storing.
  grep -v '^generated_at:' "$OUT/feature-registry.yaml" > "$FIXTURES_DIR/feature-registry.yaml"

  # clone-metadata.json — strip clone_date (volatile).
  python3 - "$OUT/clone-metadata.json" "$FIXTURES_DIR/clone-metadata.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
d.pop("clone_date", None)
open(sys.argv[2], "w").write(json.dumps({k: d[k] for k in ("upstream_repo", "upstream_ref", "resolved_commit")}, indent=2) + "\n")
PYEOF

  # cli-surface-contracts.txt — extract key contract lines from spec-cli-surface.md.
  python3 - "$OUT/spec-cli-surface.md" "$FIXTURES_DIR/cli-surface-contracts.txt" <<'PYEOF'
import sys, re

text = open(sys.argv[1]).read()
out_lines = [
    "# CLI surface contract assertions for cc-sdd v2.1.0",
    "# Each line below must appear verbatim in the generated spec-cli-surface.md",
    "# (after stripping leading/trailing whitespace).",
    "# Lines starting with # are comments.",
    "",
]

# Entrypoints section.
out_lines.append("# Package identity")
for pat in [r"- Node package: `.+`", r"- package name: `.+`", r"- version: `.+`"]:
    m = re.search(pat, text)
    if m:
        out_lines.append(m.group(0))

out_lines.append("")
out_lines.append("# Binary entrypoint")
m = re.search(r"- `cc-sdd` -> `.+`", text)
if m:
    out_lines.append(m.group(0))

out_lines.append("")
out_lines.append("# Source entry heuristic")
m = re.search(r"- `tools/cc-sdd/src/cli\.ts`.+", text)
if m:
    out_lines.append(m.group(0))

# Help text flags (extract lines from the code block).
in_block = False
flags = []
for line in text.splitlines():
    if line.strip().startswith("```"):
        in_block = not in_block
        continue
    if in_block and (line.startswith("  -") or line.startswith("-")):
        flags.append(line.rstrip())
if flags:
    out_lines.append("")
    out_lines.append("# Key CLI flags present in help text")
    out_lines.extend(flags)

# Config surface.
out_lines.append("")
out_lines.append("# Config surface")
for pat in [r"- User config file: `.+`", r"- Environment variables: `.+`"]:
    m = re.search(pat, text)
    if m:
        out_lines.append(m.group(0))

open(sys.argv[2], "w").write("\n".join(out_lines) + "\n")
print(f"Written {len(out_lines)} lines to {sys.argv[2]}")
PYEOF

  echo "=== Fixtures updated in $FIXTURES_DIR ==="
  exit 0
fi

# ---------------------------------------------------------------------------
# Normal mode: run analysis and compare against golden fixtures.
# ---------------------------------------------------------------------------
echo "=== repo_fixture_test.sh: cc-sdd v2.1.0 golden fixture test ==="
echo "    Pinned commit: $PINNED_COMMIT"
echo "    Fixtures:      $FIXTURES_DIR"
echo ""

# Clean output dir for reproducible run. The clone dir is preserved across runs
# to avoid re-downloading (a shallow clone is ~5-10 MB and slow on first run).
# However, we always delete the clone dir if the resolved SHA does not match the
# pinned commit (guards against a force-pushed tag).
if [ -d "$CLONE_DIR/.git" ]; then
  EXISTING_SHA="$(git -C "$CLONE_DIR" rev-parse HEAD 2>/dev/null || true)"
  if [ "$EXISTING_SHA" != "$PINNED_COMMIT" ]; then
    echo "--- Existing clone SHA ($EXISTING_SHA) != pin ($PINNED_COMMIT); re-cloning ---"
    rm -rf "$CLONE_DIR"
  else
    echo "--- Reusing cached clone at $PINNED_COMMIT ---"
  fi
fi

rm -rf "$OUT"
mkdir -p "$OUT"

if [ ! -d "$CLONE_DIR/.git" ]; then
  echo "--- Cloning cc-sdd at $PINNED_REF (network required) ---"
  mkdir -p "$CLONE_DIR"
fi

echo "--- Running repo-mode analysis ---"
python3 "$SKILL_DIR/scripts/reverse_engineer.py" cc-sdd \
  --mode=repo \
  --upstream-repo="$UPSTREAM_REPO" \
  --upstream-ref="$PINNED_REF" \
  --local-clone-dir="$CLONE_DIR" \
  --output-dir="$OUT"

# clone-metadata.json is only written by reverse_engineer.py during the initial
# clone. When reusing a cached clone, write it ourselves so downstream checks work.
if [ ! -f "$OUT/clone-metadata.json" ]; then
  RESOLVED_SHA="$(git -C "$CLONE_DIR" rev-parse HEAD 2>/dev/null || echo "")"
  python3 - "$OUT/clone-metadata.json" "$UPSTREAM_REPO" "$PINNED_REF" "$RESOLVED_SHA" <<'PYEOF'
import json, sys
out_path, repo, ref, sha = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = {"upstream_repo": repo, "upstream_ref": ref, "resolved_commit": sha, "clone_date": "cached"}
open(out_path, "w").write(json.dumps(data, indent=2) + "\n")
PYEOF
fi

echo ""
echo "--- Verifying pinned commit SHA ---"
ACTUAL_COMMIT="$(python3 -c "import json; d=json.load(open('$OUT/clone-metadata.json')); print(d['resolved_commit'])")"
if [ "$ACTUAL_COMMIT" != "$PINNED_COMMIT" ]; then
  _fail "resolved commit mismatch: got $ACTUAL_COMMIT, expected $PINNED_COMMIT"
  echo "      This means the tag was force-pushed or the fixture pin is stale." >&2
else
  _ok "resolved commit matches pin ($PINNED_COMMIT)"
fi

# ---------------------------------------------------------------------------
# Contract 1: docs-features.txt (exact match)
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 1: docs-features.txt ---"
GOLDEN="$FIXTURES_DIR/docs-features.txt"
ACTUAL="$OUT/docs-features.txt"

if [ ! -f "$ACTUAL" ]; then
  _fail "docs-features.txt not generated"
else
  DIFF_OUT="$(diff --unified=3 "$GOLDEN" "$ACTUAL" 2>&1 || true)"
  if [ -n "$DIFF_OUT" ]; then
    _fail "docs-features.txt drifted from golden fixture"
    echo "--- diff (golden vs actual) ---" >&2
    echo "$DIFF_OUT" >&2
    echo "---" >&2
  else
    _ok "docs-features.txt matches golden fixture"
  fi
fi

# ---------------------------------------------------------------------------
# Contract 2: feature-registry.yaml (normalized, strip generated_at)
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 2: feature-registry.yaml (normalized) ---"
GOLDEN="$FIXTURES_DIR/feature-registry.yaml"
ACTUAL="$OUT/feature-registry.yaml"

if [ ! -f "$ACTUAL" ]; then
  _fail "feature-registry.yaml not generated"
else
  GOLDEN_NORM="$(mktemp)"
  ACTUAL_NORM="$(mktemp)"
  grep -v '^generated_at:' "$GOLDEN" > "$GOLDEN_NORM"
  grep -v '^generated_at:' "$ACTUAL" > "$ACTUAL_NORM"
  DIFF_OUT="$(diff --unified=3 "$GOLDEN_NORM" "$ACTUAL_NORM" 2>&1 || true)"
  rm -f "$GOLDEN_NORM" "$ACTUAL_NORM"
  if [ -n "$DIFF_OUT" ]; then
    _fail "feature-registry.yaml drifted from golden fixture"
    echo "--- diff (golden vs actual, generated_at stripped) ---" >&2
    echo "$DIFF_OUT" >&2
    echo "---" >&2
  else
    _ok "feature-registry.yaml matches golden fixture (normalized)"
  fi
fi

# ---------------------------------------------------------------------------
# Contract 3: cli-surface-contracts.txt (line-presence check in spec-cli-surface.md)
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 3: spec-cli-surface.md contract lines ---"
CLI_SURFACE="$OUT/spec-cli-surface.md"
CONTRACTS="$FIXTURES_DIR/cli-surface-contracts.txt"

if [ ! -f "$CLI_SURFACE" ]; then
  _fail "spec-cli-surface.md not generated"
elif [ ! -f "$CONTRACTS" ]; then
  echo "SKIP: cli-surface-contracts.txt fixture not found (non-fatal)"
else
  CONTRACT_FAILURES=0
  while IFS= read -r line; do
    # Skip blank lines and comments.
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Check verbatim line presence (fixed-string, -- prevents lines starting with
    # '-' being misinterpreted as grep flags).
    if ! grep -qF -- "$line" "$CLI_SURFACE" 2>/dev/null; then
      _fail "contract line not found in spec-cli-surface.md: $line"
      CONTRACT_FAILURES=$((CONTRACT_FAILURES + 1))
    fi
  done < "$CONTRACTS"
  if [ "$CONTRACT_FAILURES" -eq 0 ]; then
    _ok "all spec-cli-surface.md contract lines present"
  fi
fi

# ---------------------------------------------------------------------------
# Contract 4: clone-metadata.json (key fields)
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 4: clone-metadata.json key fields ---"
GOLDEN="$FIXTURES_DIR/clone-metadata.json"
ACTUAL="$OUT/clone-metadata.json"

if [ ! -f "$ACTUAL" ]; then
  _fail "clone-metadata.json not generated"
elif [ ! -f "$GOLDEN" ]; then
  echo "SKIP: clone-metadata.json fixture not found (non-fatal)"
else
  # Compare only the stable fields (upstream_repo, upstream_ref, resolved_commit).
  GOLDEN_STABLE="$(mktemp)"
  ACTUAL_STABLE="$(mktemp)"
  python3 - "$GOLDEN" "$GOLDEN_STABLE" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
out = {k: d[k] for k in ("upstream_repo", "upstream_ref", "resolved_commit") if k in d}
open(sys.argv[2], "w").write(json.dumps(out, indent=2, sort_keys=True) + "\n")
PYEOF
  python3 - "$ACTUAL" "$ACTUAL_STABLE" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
out = {k: d[k] for k in ("upstream_repo", "upstream_ref", "resolved_commit") if k in d}
open(sys.argv[2], "w").write(json.dumps(out, indent=2, sort_keys=True) + "\n")
PYEOF
  DIFF_OUT="$(diff --unified=3 "$GOLDEN_STABLE" "$ACTUAL_STABLE" 2>&1 || true)"
  rm -f "$GOLDEN_STABLE" "$ACTUAL_STABLE"
  if [ -n "$DIFF_OUT" ]; then
    _fail "clone-metadata.json stable fields drifted from golden fixture"
    echo "--- diff (golden vs actual, stable fields only) ---" >&2
    echo "$DIFF_OUT" >&2
    echo "---" >&2
  else
    _ok "clone-metadata.json stable fields match golden fixture"
  fi
fi

# ---------------------------------------------------------------------------
# Contract 5: required output files exist
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 5: required output files exist ---"
REQUIRED_FILES=(
  feature-inventory.md
  feature-registry.yaml
  feature-catalog.md
  spec-architecture.md
  spec-code-map.md
  spec-clone-vs-use.md
  spec-clone-mvp.md
  spec-cli-surface.md
  spec-artifact-surface.md
  artifact-registry.json
  clone-metadata.json
  docs-features.txt
  validate-feature-registry.py
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$OUT/$f" ]; then
    _fail "required output file missing: $f"
  else
    _ok "exists: $f"
  fi
done

# ---------------------------------------------------------------------------
# Contract 6: feature registry validator passes
# ---------------------------------------------------------------------------
echo ""
echo "--- Contract 6: feature registry validator ---"
if python3 "$OUT/validate-feature-registry.py" 2>&1; then
  _ok "validate-feature-registry.py exit 0"
else
  _fail "validate-feature-registry.py exited non-zero"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
if [ "$FAILURES" -gt 0 ]; then
  echo "RESULT: FAIL — $FAILURES contract(s) drifted. See diff output above." >&2
  exit 1
else
  echo "RESULT: PASS — all golden fixture contracts match."
  exit 0
fi
