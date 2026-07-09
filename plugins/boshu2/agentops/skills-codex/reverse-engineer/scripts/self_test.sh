#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SKILL="$ROOT/skills/reverse-engineer"

if ! command -v go >/dev/null 2>&1; then
  echo "error: go is required for the demo fixture build" >&2
  exit 2
fi

TMP="$ROOT/.tmp/reverse-engineer-self-test"
OUT1="$TMP/out-core"
OUT2="$TMP/out-sec"
SRC="$TMP/fixture-src"
BIN="$TMP/demo_bin"
SITEMAP="$TMP/sitemap.xml"

rm -rf "$TMP"
mkdir -p "$SRC" "$OUT1" "$OUT2"

python3 - "$SRC" <<'PY'
import sys, zipfile
from pathlib import Path

src = Path(sys.argv[1])
(src / "payload.zip").parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(src / "payload.zip", "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("agent/main.py", "print('hello from demo agent')\n")
    zf.writestr("agent/README.md", "# Demo Agent\n")
    zf.writestr("agent/SYSTEM_PROMPT.txt", "DEMO PROMPT (do not dump in reports)\n")
PY

cat >"$SRC/main.go" <<'EOF'
package main

import _ "embed"
import "fmt"

//go:embed payload.zip
var payload []byte

func main() {
	// Ensure the bytes are referenced so the ZIP signature is present in the binary.
	fmt.Printf("demo binary; embedded payload bytes=%d\n", len(payload))
}
EOF

(cat >"$SRC/go.mod" <<'EOF'
module demo_embedded_zip

go 1.22
EOF
)

(cd "$SRC" && go build -o "$BIN" .)

cat >"$SITEMAP" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.test/docs/features/alpha/overview</loc></url>
  <url><loc>https://example.test/docs/features/alpha/howto</loc></url>
  <url><loc>https://example.test/docs/features/beta/overview</loc></url>
</urlset>
EOF

python3 "$SKILL/scripts/reverse_engineer.py" demo \
  --authorized \
  --mode=binary \
  --binary-path="$BIN" \
  --docs-sitemap-url="file://$SITEMAP" \
  --materialize-archives \
  --local-clone-dir="$TMP/local-demo" \
  --output-dir="$OUT1"

python3 "$OUT1/validate-feature-registry.py"

# --- Binary mode capability assertions ---

echo "--- binary mode capability checks ---"

# 1. Help capture output exists (may be empty if binary doesn't support --help)
if [ ! -f "$OUT1/cli-commands.txt" ]; then
  echo "FAIL: cli-commands.txt not created by binary mode" >&2
  exit 1
fi
echo "OK: cli-commands.txt exists"

# 2. CLI surface spec exists (generated from --help tree or binary strings fallback)
if [ ! -f "$OUT1/spec-cli-surface.md" ]; then
  echo "FAIL: spec-cli-surface.md not created by binary mode" >&2
  exit 1
fi
echo "OK: spec-cli-surface.md exists"

# 3. binary-symbols.txt exists
if [ ! -f "$OUT1/binary-symbols.txt" ]; then
  echo "FAIL: binary-symbols.txt not created by binary mode" >&2
  exit 1
fi
echo "OK: binary-symbols.txt exists"

# 4. Registry enrichment: if cli-commands.txt has content, groups should have impl: client
if [ -s "$OUT1/cli-commands.txt" ]; then
  if ! grep -q 'impl: client' "$OUT1/feature-registry.yaml"; then
    echo "FAIL: feature-registry.yaml should contain 'impl: client' when CLI commands are found" >&2
    exit 1
  fi
  echo "OK: feature-registry.yaml enriched with impl: client"
else
  echo "OK: cli-commands.txt empty (demo binary has no subcommands); skipping impl: client check"
fi

python3 "$SKILL/scripts/reverse_engineer.py" demo \
  --authorized \
  --mode=binary \
  --binary-path="$BIN" \
  --docs-sitemap-url="file://$SITEMAP" \
  --output-dir="$OUT2" \
  --materialize-archives \
  --local-clone-dir="$TMP/local-demo" \
  --security-audit \
  --sbom

"$OUT2/security/validate-security-audit.sh" "$OUT2" --sbom

# --- Negative tests ---

# Test: invalid --mode should fail
echo "--- negative test: invalid --mode ---"
if python3 "$SKILL/scripts/reverse_engineer.py" demo --mode=invalid --output-dir="$TMP/out-neg" 2>/dev/null; then
  echo "FAIL: expected non-zero exit for --mode=invalid" >&2
  exit 1
fi
echo "OK: invalid --mode correctly rejected"

# --- Upstream ref pinning test ---

echo "--- upstream-ref pinning test ---"
OUT_REF="$TMP/out-ref"
mkdir -p "$OUT_REF"
# Use file:// protocol on the current repo to avoid network dependency.
REPO_URL="file://$ROOT"
python3 "$SKILL/scripts/reverse_engineer.py" self-ref-test \
  --mode=repo \
  --upstream-repo="$REPO_URL" \
  --upstream-ref=HEAD \
  --local-clone-dir="$TMP/local-ref" \
  --output-dir="$OUT_REF"

if [ ! -f "$OUT_REF/clone-metadata.json" ]; then
  echo "FAIL: clone-metadata.json not created with --upstream-ref" >&2
  exit 1
fi
echo "OK: clone-metadata.json created with --upstream-ref"

# --- Multi-language CLI graceful degradation test ---

echo "--- multi-language CLI degradation test ---"
OUT_NONCLI="$TMP/out-noncli"
mkdir -p "$OUT_NONCLI" "$TMP/local-noncli"
# Create a minimal repo with no CLI markers.
mkdir -p "$TMP/local-noncli/.git"
touch "$TMP/local-noncli/README.md"
python3 "$SKILL/scripts/reverse_engineer.py" no-cli-demo \
  --mode=repo \
  --local-clone-dir="$TMP/local-noncli" \
  --output-dir="$OUT_NONCLI" \
  --docs-sitemap-url="file://$SITEMAP"

# spec-cli-surface.md should NOT exist (no CLI detected), and the note should be in spec-code-map.md
if [ -f "$OUT_NONCLI/spec-cli-surface.md" ]; then
  echo "FAIL: spec-cli-surface.md should not exist for non-CLI repo" >&2
  exit 1
fi
if ! grep -q "no CLI surface detected" "$OUT_NONCLI/spec-code-map.md" 2>/dev/null; then
  echo "FAIL: spec-code-map.md should note that no CLI surface was detected" >&2
  exit 1
fi
echo "OK: multi-language CLI graceful degradation works"

echo "--- generated-tree hygiene regression test ---"
HYGIENE_REPO="$TMP/local-hygiene"
HYGIENE_OUT="$TMP/out-hygiene"
mkdir -p "$HYGIENE_REPO/.tmp/compound-engineer" "$HYGIENE_OUT"
(cd "$HYGIENE_REPO" && git init >/dev/null 2>&1)
cat >"$HYGIENE_REPO/package.json" <<'EOF'
{
  "name": "agentops",
  "version": "0.0.1",
  "bin": {
    "agentops": "bin/agentops.js"
  }
}
EOF
cat >"$HYGIENE_REPO/.tmp/compound-engineer/package.json" <<'EOF'
{
  "name": "@every-env/compound-plugin",
  "version": "9.9.9",
  "bin": {
    "compound-plugin": "bin/index.js"
  }
}
EOF
python3 "$SKILL/scripts/reverse_engineer.py" agentops \
  --mode=repo \
  --local-clone-dir="$HYGIENE_REPO" \
  --output-dir="$HYGIENE_OUT"
if grep -q "\.tmp/compound-engineer" "$HYGIENE_OUT/spec-cli-surface.md"; then
  echo "FAIL: generated-tree package leaked into CLI surface spec" >&2
  exit 1
fi
if ! grep -q "package name: \`agentops\`" "$HYGIENE_OUT/spec-cli-surface.md"; then
  echo "FAIL: root package did not win CLI surface detection" >&2
  exit 1
fi
echo "OK: generated-tree hygiene regression holds"

echo "OK: self-test passed (all positive + negative tests)"
