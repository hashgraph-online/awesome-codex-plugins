#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: validate_security_audit.sh <output_dir> (--sbom|--no-sbom)" >&2
  exit 2
fi

OUTDIR="$1"
SBOM_FLAG="${2:-}"

SEC="$OUTDIR/security"
if [[ ! -d "$SEC" ]]; then
  echo "FAIL: missing security dir: $SEC" >&2
  exit 1
fi

req=(
  "$SEC/threat-model.md"
  "$SEC/attack-surface.md"
  "$SEC/dataflow.md"
  "$SEC/crypto-review.md"
  "$SEC/authn-authz.md"
  "$SEC/findings.md"
  "$SEC/reproducibility.md"
  "$SEC/validate-security-audit.sh"
)

fail=0
for f in "${req[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "FAIL: missing required file: $f" >&2
    fail=1
  fi
done
if [[ $fail -ne 0 ]]; then
  exit 1
fi

# Findings gate: each finding must have Evidence + Fix sections (simple heuristic).
if ! rg -n -S '^## ' "$SEC/findings.md" >/dev/null 2>&1; then
  echo "FAIL: findings.md has no findings headers (expected '## ...')" >&2
  exit 1
fi

if ! rg -n -S '(?i)^Evidence:' "$SEC/findings.md" >/dev/null 2>&1; then
  echo "FAIL: findings.md missing Evidence: lines" >&2
  exit 1
fi
if ! rg -n -S '(?i)^(Fix|Remediation):' "$SEC/findings.md" >/dev/null 2>&1; then
  echo "FAIL: findings.md missing Fix:/Remediation: lines" >&2
  exit 1
fi

# Secret scan gate over outputs.
SCANDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="$SCANDIR/scan_secrets.sh"
if [[ ! -x "$SCANNER" ]]; then
  SCANNER="$SCANDIR/scan-secrets.sh"
fi
"$SCANNER" "$OUTDIR"

if [[ "$SBOM_FLAG" == "--sbom" ]]; then
  if [[ ! -f "$SEC/sbom.spdx.json" && ! -f "$SEC/sbom.NOOP.md" ]]; then
    echo "FAIL: --sbom set but no sbom.spdx.json (or sbom.NOOP.md) found in $SEC" >&2
    exit 1
  fi
  if [[ ! -f "$SEC/dep-risk-report.md" ]]; then
    echo "FAIL: --sbom set but missing dep-risk-report.md in $SEC" >&2
    exit 1
  fi
fi

echo "OK: security audit validated ($OUTDIR)"
