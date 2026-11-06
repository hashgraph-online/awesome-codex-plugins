#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: scan_secrets.sh <dir>" >&2
  exit 2
fi

ROOT="$1"
if [[ ! -d "$ROOT" ]]; then
  echo "error: not a directory: $ROOT" >&2
  exit 2
fi

# Conservative patterns. This will produce false positives; treat as a gate to review and redact.
# POSIX ERE so ripgrep and the grep fallback read them the same way.
PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  # Every PEM private-key header: PKCS#8, ENCRYPTED, RSA, EC, DSA, OPENSSH, PGP ... BLOCK.
  '-----BEGIN ([A-Z0-9]+ )*PRIVATE KEY( BLOCK)?-----'
  'xox[baprs]-[0-9A-Za-z-]{10,}'
  'ghp_[0-9A-Za-z]{20,}'
  'github_pat_[0-9A-Za-z_]{20,}'
  'sk-[0-9A-Za-z]{20,}'
  'AIza[0-9A-Za-z_-]{20,}'
)
# Matched case-insensitively. The optional quote catches JSON keys ("api_key": "...").
ICASE_PATTERNS=(
  "client_secret[\"']?[[:space:]]*[:=][[:space:]]*[^[:space:]]+"
  "api[_-]?key[\"']?[[:space:]]*[:=][[:space:]]*[^[:space:]]+"
  'authorization[[:space:]]*:[[:space:]]*bearer[[:space:]]+[^[:space:]]+'
)

TMP="$(mktemp -t re_rpi_secrets.XXXXXX)"
trap 'rm -f "$TMP"' EXIT

# Search once; exit 0 = hit, 1 = clean, anything else = the search itself failed.
# Avoid self-matches: the copied security scripts embed the patterns they look for.
search() {
  local case_flag="$1" pat="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -n --no-heading "$case_flag" --hidden --no-ignore \
      --glob '!.git/**' \
      --glob '!**/security/scan-secrets.sh' \
      --glob '!**/security/scan_secrets.sh' \
      --glob '!**/security/validate-security-audit.sh' \
      --glob '!**/security/generate-sbom.sh' \
      -- "$pat" "$ROOT"
  else
    local grep_case=-I
    [[ "$case_flag" == "-i" ]] && grep_case=-iI
    grep -RnE "$grep_case" \
      --exclude-dir=.git \
      --exclude=scan-secrets.sh --exclude=scan_secrets.sh \
      --exclude=validate-security-audit.sh --exclude=generate-sbom.sh \
      -- "$pat" "$ROOT"
  fi
}

FAIL=0
run_patterns() {
  local case_flag="$1"
  shift
  local pat rc
  for pat in "$@"; do
    rc=0
    search "$case_flag" "$pat" >>"$TMP" || rc=$?
    case "$rc" in
      0) FAIL=1 ;;
      1) ;;
      *)
        echo "error: secret scan could not search $ROOT (exit $rc); treating as failed" >&2
        exit 2
        ;;
    esac
  done
}
run_patterns -s "${PATTERNS[@]}"
run_patterns -i "${ICASE_PATTERNS[@]}"

if [[ $FAIL -ne 0 ]]; then
  echo "FAIL: potential secrets detected in $ROOT; review and redact these lines, then re-run:" >&2
  # Print file:line only, so the matched value is not copied into logs.
  cut -d: -f1-2 "$TMP" | sort -u | head -50 >&2
  exit 1
fi

echo "OK: secret scan passed ($ROOT)"
