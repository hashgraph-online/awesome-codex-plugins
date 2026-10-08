#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Syntax-check the shipped Python without writing __pycache__/*.pyc into the
# package (py_compile writes the default cfile even with cfile=None); ast.parse
# validates syntax and writes nothing.
python3 - \
  "$SKILL_DIR/scripts/reverse_engineer.py" \
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

# Hermetic behavioral witness: the security-audit gate must fail-closed on an
# unfilled findings scaffold. The shipped template supplies Evidence/Fix as
# literal _TBD markers; a presence-only grep used to certify them green. Build a
# minimal security dir whose findings.md still carries _TBD and assert the gate
# refuses it. (No go, network, or scanners needed — the _TBD check trips before
# the secret scan.)
tmp="$(mktemp -d "${TMPDIR:-/tmp}/re-validate.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT
sec="$tmp/security"
mkdir -p "$sec"
for name in threat-model attack-surface dataflow crypto-review authn-authz reproducibility; do
  printf '# %s\n' "$name" > "$sec/$name.md"
done
cp "$SKILL_DIR/scripts/security/validate_security_audit.sh" "$sec/validate-security-audit.sh"
chmod +x "$sec/validate-security-audit.sh"
printf '## Finding F-1: scaffold\nEvidence: _TBD_\nFix: _TBD_\n' > "$sec/findings.md"

if bash "$sec/validate-security-audit.sh" "$tmp" --no-sbom >/dev/null 2>&1; then
  echo "FAIL: security-audit gate certified an unfilled _TBD scaffold (should fail-closed)" >&2
  exit 1
fi

echo "OK: reverse-engineer validate.sh passed (syntax + security gate rejects _TBD scaffold)"
