#!/usr/bin/env bash
# Hermetic checks for the reverse-engineer scripts: no Go, no network, all
# writes under one temporary directory. self_test.sh covers binary mode (Go).
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RE="$SKILL_DIR/scripts/reverse_engineer.py"
VALIDATE_OUTPUT="$SKILL_DIR/scripts/validate-output.sh"
SCAN="$SKILL_DIR/scripts/security/scan_secrets.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

# Syntax-check the shipped Python without writing __pycache__/*.pyc into the
# package (py_compile writes the default cfile even with cfile=None); ast.parse
# validates syntax and writes nothing.
python3 - \
  "$RE" \
  "$SKILL_DIR/scripts/fetch_url.py" \
  "$SKILL_DIR/scripts/generate_feature_inventory_md.py" \
  "$SKILL_DIR/scripts/scaffold_feature_registry.py" \
  "$SKILL_DIR/scripts/generate_feature_catalog_md.py" \
  "$SKILL_DIR/scripts/validate_feature_registry.py" \
  "$SKILL_DIR/scripts/binary/list_embedded_archives.py" \
  "$SKILL_DIR/scripts/binary/extract_embedded_archives.py" <<'PY'
import ast
import sys
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        ast.parse(fh.read(), filename=path)
PY

tmp="$(mktemp -d "${TMPDIR:-/tmp}/re-validate.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
# Physical path: the script refuses symlinked components (macOS /var -> /private/var).
tmp="$(cd "$tmp" && pwd -P)"

# The security-audit gate must fail closed on an unfilled findings scaffold
# (the _TBD check trips before the secret scan).
sec="$tmp/audit/security"
mkdir -p "$sec"
for name in threat-model attack-surface dataflow crypto-review authn-authz reproducibility; do
  printf '# %s\n' "$name" >"$sec/$name.md"
done
cp "$SKILL_DIR/scripts/security/validate_security_audit.sh" "$sec/validate-security-audit.sh"
chmod +x "$sec/validate-security-audit.sh"
printf '## Finding F-1: scaffold\nEvidence: _TBD_\nFix: _TBD_\n' >"$sec/findings.md"
if bash "$sec/validate-security-audit.sh" "$tmp/audit" --no-sbom >/dev/null 2>&1; then
  fail "security-audit gate certified an unfilled _TBD scaffold"
fi

# Secret scan: key = value, JSON key, Bearer, dash-bearing AIza secrets and
# PEM private-key headers (generic PKCS#8 and ENCRYPTED, not only RSA/EC/OPENSSH)
# must fail. Seeds are assembled at run time so this file holds no secret-shaped text.
seeds=(
  "api""_key = x"
  "\"api""_key\": \"x\""
  "client""_secret: x"
  "Authorization: ""Bearer x"
  "key=AI""zaSyA-bcdefghijklmnopqrstu"
  "-----BEGIN PRIVATE"" KEY-----"
  "-----BEGIN ENCRYPTED PRIVATE"" KEY-----"
)
i=0
for seed in "${seeds[@]}"; do
  i=$((i + 1))
  mkdir -p "$tmp/seed-$i"
  printf '%s\n' "$seed" >"$tmp/seed-$i/config.txt"
  if bash "$SCAN" "$tmp/seed-$i" >/dev/null 2>&1; then
    fail "secret scan passed seeded case $i"
  fi
done
mkdir -p "$tmp/clean"
printf 'no secrets here\n' >"$tmp/clean/notes.txt"
bash "$SCAN" "$tmp/clean" >/dev/null || fail "secret scan rejected a clean directory"

# Repo-mode teardown of a small non-Git tree, run from an unrelated cwd.
tree="$tmp/target"
out="$tmp/out"
cwd="$tmp/cwd"
mkdir -p "$tree/docs/features/alpha" "$cwd"
printf '# Alpha\n' >"$tree/docs/features/alpha/overview.md"
(cd "$cwd" && python3 "$RE" demo --mode=repo --local-clone-dir="$tree" --output-dir="$out" >/dev/null) \
  || fail "repo-mode teardown did not pass its own validator"
grep -Fqx "$tree" "$out/analysis-root-path.txt" || fail "explicit non-Git tree was not the analysis root"
grep -Fq 'impl: unclassified' "$out/feature-registry.yaml" || fail "registry groups must start unclassified"
[[ -d "$out/scratch" ]] || fail "scratch is not under the output dir"
[[ ! -e "$cwd/.tmp" && ! -e "$out/reports" ]] || fail "teardown wrote outside its output dir or canned reports"

# The teardown validator scans outputs for secrets in every mode.
printf '%s\n' "${seeds[0]}" >"$out/scratch/leak.txt"
if bash "$VALIDATE_OUTPUT" --output-dir "$out" --phase teardown >/dev/null 2>&1; then
  fail "teardown validator passed an output holding a secret"
fi
rm -f "$out/scratch/leak.txt"

# Complete phase: the steal-map table is checked row by row.
complete() { bash "$VALIDATE_OUTPUT" --output-dir "$out" --phase complete >/dev/null 2>&1; }
map() {
  printf '# Steal map: demo\n\n| Their capability | Our surface today | Verdict |\n|---|---|---|\n%s\n' "$1" >"$out/steal-map.md"
}
if complete; then fail "complete validator accepted a missing steal-map.md"; fi
map '| Alpha sync (code: `src/sync.go:12`) | none: `rg -n sync cli/` found nothing | **steal** |
| Team dashboard (hosted) | none | **park** |'
complete || fail "complete validator rejected a valid steal-map"
for row in \
  '| Alpha sync (docs) | none | **steal** |' \
  '| Alpha sync | none | **gap** |' \
  '| Alpha sync (code: `src/sync.go:12`) | none | **adopt** |' \
  '| Alpha sync (code: `src/sync.go:12`) |  | **have** |'; do
  map "$row"
  if complete; then fail "complete validator accepted: $row"; fi
done
printf '# malformed map\n' >"$out/steal-map.md"
if complete; then fail "complete validator accepted a malformed steal-map.md"; fi

# An existing checkout at the wrong commit is refused before anything is written.
repo="$tmp/wrong-ref"
mkdir -p "$repo"
git -C "$repo" init -q
git -C "$repo" config user.name reverse-validate
git -C "$repo" config user.email reverse-validate@example.invalid
printf 'one\n' >"$repo/unique.txt"
git -C "$repo" add unique.txt
git -C "$repo" commit -qm one
first="$(git -C "$repo" rev-parse HEAD)"
printf 'two\n' >"$repo/unique.txt"
git -C "$repo" commit -qam two
second="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" checkout -q --detach "$first"
if python3 "$RE" wrong-ref --mode=repo --local-clone-dir="$repo" \
  --upstream-ref="$second" --output-dir="$tmp/out-wrong" >/dev/null 2>&1; then
  fail "an existing checkout at the wrong commit was analyzed"
fi
[[ ! -e "$tmp/out-wrong/feature-registry.yaml" ]] || fail "ref mismatch wrote teardown artifacts"

# Output parents and managed files that are symlinks fail closed.
link_case="$tmp/link-case"
outside="$tmp/outside"
mkdir -p "$link_case/.agents" "$outside"
printf 'outside sentinel\n' >"$outside/sentinel"
ln -s "$outside" "$link_case/.agents/scratch"
if (cd "$link_case" && python3 "$RE" escaped --mode=repo --local-clone-dir="$tree" >/dev/null 2>&1); then
  fail "default output followed a symlinked scratch parent"
fi
[[ ! -e "$outside/reverse-engineer" ]] || fail "symlinked parent allowed an outside write"
managed="$tmp/out-managed"
mkdir -p "$managed"
printf 'outside registry\n' >"$tmp/outside.yaml"
ln -s "$tmp/outside.yaml" "$managed/feature-registry.yaml"
if python3 "$RE" managed --mode=repo --local-clone-dir="$tree" --output-dir="$managed" >/dev/null 2>&1; then
  fail "a managed artifact symlink was followed"
fi
grep -Fqx 'outside registry' "$tmp/outside.yaml" || fail "a managed artifact symlink changed its target"

echo "OK: reverse-engineer validate.sh passed (syntax, security gate, secret scan, teardown, steal-map, ref and symlink refusals)"
