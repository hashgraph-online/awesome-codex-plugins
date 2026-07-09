#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: generate_sbom.sh <analysis_root_dir> <security_out_dir>" >&2
  exit 2
fi

ROOT="$1"
OUT="$2"
mkdir -p "$OUT"

report="$OUT/dep-risk-report.md"

if command -v syft >/dev/null 2>&1; then
  # Best-effort. Avoid failing the whole workflow if syft has issues.
  if syft "dir:${ROOT}" -o spdx-json >"$OUT/sbom.spdx.json" 2>"$OUT/syft.stderr"; then
    cat >"$report" <<EOF
# Dependency Risk Report (Best-Effort)

- Generator: syft
- Input: \`${ROOT}\`
- Notes: This report is a stub. Pair SBOM output with a vuln scanner (e.g., grype) in an authorized environment.
EOF
    exit 0
  fi
fi

# Language-aware no-op outputs (still produces deterministic artifacts).
if [[ -f "$ROOT/go.mod" ]]; then
  if command -v go >/dev/null 2>&1; then
    (cd "$ROOT" && go list -m -json all) >"$OUT/sbom.go-mod.modules.json" 2>"$OUT/go-list.stderr" || true
  fi
fi

cat >"$OUT/sbom.NOOP.md" <<EOF
# SBOM (No-Op)

No supported SBOM generator was available (or it failed).

Input: \`${ROOT}\`
Created: $(date +%F)
EOF

cat >"$report" <<EOF
# Dependency Risk Report (No-Op)

No dependency risk scan was performed (offline / tool unavailable).

Recommended (authorized environments only):
- Generate a real SBOM with syft
- Run a vuln scan with grype / osv-scanner / etc.
EOF

