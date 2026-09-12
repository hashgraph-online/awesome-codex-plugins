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

HELP="$(python3 "$SKILL/scripts/reverse_engineer.py" --help)"
grep -Fq '.agents/scratch/reverse-engineer/<product>/' <<<"$HELP"
grep -Fq '.agents/research/<product>/ path remains' <<<"$HELP"
grep -Fq 'are never moved automatically.' <<<"$HELP"
grep -Fq -- "- '.agents/scratch/reverse-engineer/*/'" "$SKILL/SKILL.md"
echo "OK: output-path migration contract is visible in --help"

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

VALIDATE_OUTPUT="$SKILL/scripts/validate-output.sh"
"$VALIDATE_OUTPUT" --output-dir "$OUT1" --phase teardown \
  --security-audit 0 --sbom 0 --upstream-ref-set 0
if "$VALIDATE_OUTPUT" --output-dir "$OUT1" --phase complete \
  --security-audit 0 --sbom 0 --upstream-ref-set 0 >/dev/null 2>&1; then
  echo "FAIL: complete validator accepted a missing steal-map.md" >&2
  exit 1
fi
cat >"$OUT1/steal-map.md" <<'EOF'
# Steal map: demo

| Their capability | Our surface today | Verdict |
|---|---|---|
| Embedded archive inventory (`feature-registry.yaml`) | `skills/reverse-engineer/` | **have** |
EOF
"$VALIDATE_OUTPUT" --output-dir "$OUT1" --phase complete \
  --security-audit 0 --sbom 0 --upstream-ref-set 0
cp "$OUT1/steal-map.md" "$OUT1/steal-map.valid"
printf '# malformed map\n' >"$OUT1/steal-map.md"
if "$VALIDATE_OUTPUT" --output-dir "$OUT1" --phase complete \
  --security-audit 0 --sbom 0 --upstream-ref-set 0 >/dev/null 2>&1; then
  echo "FAIL: complete validator accepted a malformed steal-map.md" >&2
  exit 1
fi
mv "$OUT1/steal-map.valid" "$OUT1/steal-map.md"
echo "OK: exact output validator distinguishes teardown from complete decision output"

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

# The freshly generated audit is a scaffold whose files carry _TBD
# placeholders; the gate must now REFUSE to certify it (fail-closed).
if "$OUT2/security/validate-security-audit.sh" "$OUT2" --sbom >/dev/null 2>&1; then
  echo "FAIL: security gate certified an unfilled _TBD scaffold (should fail-closed)" >&2
  exit 1
fi
echo "OK: security gate rejects the unfilled _TBD scaffold"

# Fill EVERY required narrative file (no placeholders). The other files just
# need real content; findings.md additionally needs the Evidence/Fix shape.
for name in threat-model attack-surface dataflow crypto-review authn-authz reproducibility; do
  printf '# %s\n\nReviewed for the demo binary; no items of concern.\n' "$name" > "$OUT2/security/$name.md"
done
cat >"$OUT2/security/findings.md" <<'EOF'
# Findings: demo

- Date: self-test

## Finding F-001: Embedded demo prompt present in binary

Severity: Low
Impact: Informational; the embedded demo prompt is not a secret.
Likelihood: Low

Evidence: payload.zip/agent/SYSTEM_PROMPT.txt embedded via go:embed (see binary-embedded-archives.md).
Fix: None required for the demo; production binaries should not embed plaintext prompts.
Validation: Re-ran the secret scan over outputs; no credentials present.
EOF

"$OUT2/security/validate-security-audit.sh" "$OUT2" --sbom
echo "OK: security gate certifies a completed audit"

# Prove the _TBD gate scans BEYOND findings.md: seed a placeholder into a
# different required file and the gate must fail-closed again.
printf '# threat-model\n\n- _TBD_\n' > "$OUT2/security/threat-model.md"
if "$OUT2/security/validate-security-audit.sh" "$OUT2" --sbom >/dev/null 2>&1; then
  echo "FAIL: security gate certified an audit with _TBD in threat-model.md (should fail-closed)" >&2
  exit 1
fi
echo "OK: security gate rejects _TBD in a non-findings required file"

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

echo "--- existing-checkout ref mismatch test ---"
WRONG_REPO="$TMP/local-wrong-ref"
WRONG_OUT="$TMP/out-wrong-ref"
mkdir -p "$WRONG_REPO"
git -C "$WRONG_REPO" init -q
git -C "$WRONG_REPO" config user.name reverse-self-test
git -C "$WRONG_REPO" config user.email reverse-self-test@example.invalid
printf 'one\n' >"$WRONG_REPO/unique.txt"
git -C "$WRONG_REPO" add unique.txt
git -C "$WRONG_REPO" commit -qm one
first_commit="$(git -C "$WRONG_REPO" rev-parse HEAD)"
printf 'two\n' >"$WRONG_REPO/unique.txt"
git -C "$WRONG_REPO" commit -qam two
second_commit="$(git -C "$WRONG_REPO" rev-parse HEAD)"
git -C "$WRONG_REPO" checkout -q --detach "$first_commit"
if python3 "$SKILL/scripts/reverse_engineer.py" wrong-ref \
  --mode=repo --local-clone-dir="$WRONG_REPO" \
  --upstream-ref="$second_commit" --output-dir="$WRONG_OUT" >/dev/null 2>&1; then
  echo "FAIL: existing checkout at the wrong commit was analyzed" >&2
  exit 1
fi
if [ -e "$WRONG_OUT/feature-registry.yaml" ]; then
  echo "FAIL: ref mismatch wrote trusted teardown artifacts" >&2
  exit 1
fi
echo "OK: existing checkout must match the requested ref"

echo "--- explicit non-Git root test ---"
EXPLICIT_TREE="$TMP/explicit-nongit"
EXPLICIT_OUT="$TMP/out-explicit-nongit"
mkdir -p "$EXPLICIT_TREE"
printf 'only-in-explicit-tree\n' >"$EXPLICIT_TREE/unique-source.txt"
python3 "$SKILL/scripts/reverse_engineer.py" explicit-nongit \
  --mode=repo --local-clone-dir="$EXPLICIT_TREE" --output-dir="$EXPLICIT_OUT"
if ! grep -Fqx "$EXPLICIT_TREE" "$EXPLICIT_OUT/analysis-root-path.txt"; then
  echo "FAIL: explicit non-Git tree was replaced by the caller checkout" >&2
  exit 1
fi
echo "OK: explicit non-Git analysis root wins"

echo "--- output symlink refusal tests ---"
SYMLINK_CASE="$TMP/symlink-case"
SYMLINK_OUTSIDE="$TMP/symlink-outside"
mkdir -p "$SYMLINK_CASE/.agents" "$SYMLINK_OUTSIDE" "$SYMLINK_CASE/local"
printf 'outside sentinel\n' >"$SYMLINK_OUTSIDE/sentinel"
ln -s "$SYMLINK_OUTSIDE" "$SYMLINK_CASE/.agents/scratch"
if (
  cd "$SYMLINK_CASE"
  python3 "$SKILL/scripts/reverse_engineer.py" escaped \
    --mode=repo --local-clone-dir="$SYMLINK_CASE/local" >/dev/null 2>&1
); then
  echo "FAIL: default output followed a symlinked scratch parent" >&2
  exit 1
fi
if ! grep -Fqx 'outside sentinel' "$SYMLINK_OUTSIDE/sentinel" \
  || [ -e "$SYMLINK_OUTSIDE/reverse-engineer" ]; then
  echo "FAIL: symlinked parent allowed an outside write" >&2
  exit 1
fi

MANAGED_OUT="$TMP/out-managed-link"
MANAGED_OUTSIDE="$TMP/managed-outside.yaml"
mkdir -p "$MANAGED_OUT"
printf 'outside registry\n' >"$MANAGED_OUTSIDE"
ln -s "$MANAGED_OUTSIDE" "$MANAGED_OUT/feature-registry.yaml"
if python3 "$SKILL/scripts/reverse_engineer.py" managed-link \
  --mode=repo --local-clone-dir="$EXPLICIT_TREE" \
  --output-dir="$MANAGED_OUT" >/dev/null 2>&1; then
  echo "FAIL: managed artifact symlink was followed" >&2
  exit 1
fi
if ! grep -Fqx 'outside registry' "$MANAGED_OUTSIDE"; then
  echo "FAIL: managed artifact symlink changed the outside target" >&2
  exit 1
fi
echo "OK: output parent and managed-file symlinks fail closed"

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

echo "--- default output-path parity test ---"
DEFAULT_OUT="$TMP/.agents/scratch/reverse-engineer/default-demo"
(
  cd "$TMP"
  python3 "$SKILL/scripts/reverse_engineer.py" default-demo \
    --mode=repo \
    --local-clone-dir="$TMP/local-noncli" \
    --docs-sitemap-url="file://$SITEMAP"
)
if [ ! -s "$DEFAULT_OUT/feature-registry.yaml" ] \
  || [ ! -s "$DEFAULT_OUT/contracts/repo-contract.json" ] \
  || [ ! -s "$DEFAULT_OUT/reports/$(date +%F)-vibe-default-demo.md" ] \
  || [ ! -s "$DEFAULT_OUT/docs-features.txt" ] \
  || [ ! -s "$DEFAULT_OUT/validate-feature-registry.py" ]; then
  echo "FAIL: executable default did not emit the declared product output directory" >&2
  exit 1
fi
echo "OK: frontmatter output directory matches the executable default"

echo "--- earlier output-path compatibility test ---"
LEGACY_OUT="$TMP/.agents/research/legacy-demo"
LEGACY_EXPECTED="$TMP/legacy-sentinel.expected"
LEGACY_DEFAULT="$TMP/.agents/scratch/reverse-engineer/legacy-demo"
mkdir -p "$LEGACY_OUT"
printf 'caller-owned sentinel\n\n' > "$LEGACY_OUT/caller-sentinel.txt"
cp "$LEGACY_OUT/caller-sentinel.txt" "$LEGACY_EXPECTED"
(
  cd "$TMP"
  python3 "$SKILL/scripts/reverse_engineer.py" legacy-demo \
    --mode=repo \
    --local-clone-dir="$TMP/local-noncli" \
    --output-dir="$LEGACY_OUT" \
    --docs-sitemap-url="file://$SITEMAP"
)
if [ ! -s "$LEGACY_OUT/feature-registry.yaml" ]; then
  echo "FAIL: explicit earlier-default output directory was not honored" >&2
  exit 1
fi
if ! cmp -s "$LEGACY_EXPECTED" "$LEGACY_OUT/caller-sentinel.txt"; then
  echo "FAIL: explicit earlier-default invocation changed a pre-existing artifact" >&2
  exit 1
fi
if [ -e "$LEGACY_DEFAULT" ]; then
  echo "FAIL: explicit earlier-default invocation also wrote to the scratch default" >&2
  exit 1
fi
echo "OK: explicit earlier-default output directory remains supported"

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
