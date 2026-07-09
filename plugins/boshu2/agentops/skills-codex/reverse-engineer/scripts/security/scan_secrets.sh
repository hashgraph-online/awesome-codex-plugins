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
PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  '-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'
  'xox[baprs]-[0-9A-Za-z-]{10,}'
  'ghp_[0-9A-Za-z]{20,}'
  'github_pat_[0-9A-Za-z_]{20,}'
  'sk-[0-9A-Za-z]{20,}'
  'AIza[0-9A-Za-z\\-_]{20,}'
  '-----BEGIN PGP PRIVATE KEY BLOCK-----'
  '(?i)client_secret\\s*[:=]\\s*[^\\s]+'
  '(?i)api[_-]?key\\s*[:=]\\s*[^\\s]+'
  '(?i)authorization\\s*:\\s*bearer\\s+[^\\s]+'
)

TMP="$(mktemp -t re_rpi_secrets.XXXXXX)"
trap 'rm -f "$TMP"' EXIT

FAIL=0
for pat in "${PATTERNS[@]}"; do
  # ripgrep is faster and supports PCRE2 with -P.
  if command -v rg >/dev/null 2>&1; then
    # Use '--' so patterns beginning with '-' are not treated as flags.
    # Avoid self-matches: this validator embeds some of the patterns it is looking for.
    if rg -n -S -P --hidden --no-ignore \
      --glob '!.git/**' \
      --glob '!.tmp/**' \
      --glob '!**/security/scan-secrets.sh' \
      --glob '!**/security/scan_secrets.sh' \
      --glob '!**/security/validate-security-audit.sh' \
      --glob '!**/security/generate-sbom.sh' \
      -- "$pat" "$ROOT" >>"$TMP"; then
      FAIL=1
    fi
  else
    if grep -RInE -- "$pat" "$ROOT" >>"$TMP" 2>/dev/null; then
      FAIL=1
    fi
  fi
done

if [[ $FAIL -ne 0 ]]; then
  echo "FAIL: potential secrets detected in $ROOT" >&2
  # Print limited output to avoid copying secrets into logs.
  head -50 "$TMP" >&2
  echo "..." >&2
  exit 1
fi

echo "OK: secret scan passed ($ROOT)"
